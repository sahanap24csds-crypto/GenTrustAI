"""Step 4: detect and check citations (DOIs, URLs, reference-list entries)."""

import re
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GenTrustAI/2.0; citation checker; "
        "+https://github.com/)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
}

DOI_PATTERN = r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+"
URL_PATTERN = r"https?://[^\s<>\"'\]]+"
HEADING_PATTERN = re.compile(
    r"^\s*(?:#{1,6}\s*|\*\*)?"
    r"(references?|bibliography|sources?|citations?|works cited|further reading)"
    r"\s*[:*]*\s*$",
    re.IGNORECASE,
)
AUTHOR_YEAR_PATTERN = re.compile(
    r"\(([A-Z][A-Za-z'\-]+(?:\s+et al\.?|\s+(?:and|&)\s+[A-Z][A-Za-z'\-]+)?),?\s+((?:19|20)\d{2})[a-z]?\)"
)

MAX_CITATIONS = 10


# ------------------------------------------------------------------
# Detection
# ------------------------------------------------------------------

def _clean(value):
    return value.rstrip(".,;:)]}>'\"")


def detect_citations(answer):
    """Return a de-duplicated list of citation strings found in the text."""

    citations = []
    seen_dois = set()

    for doi in re.findall(DOI_PATTERN, answer):
        doi = _clean(doi)
        if doi.lower() not in seen_dois:
            seen_dois.add(doi.lower())
            citations.append(doi)

    for url in re.findall(URL_PATTERN, answer):
        url = _clean(url)
        if any(doi in url.lower() for doi in seen_dois):
            continue  # already covered by the DOI check
        citations.append(url)

    # Entries listed under a "References" style heading
    lines = answer.splitlines()
    in_references = False
    for line in lines:
        if HEADING_PATTERN.match(line):
            in_references = True
            continue
        if not in_references:
            continue

        entry = re.sub(r"^\s*(?:[-*•]|\[\d+\]|\d+[.)])\s*", "", line).strip()
        if len(entry) < 15:
            continue
        if re.search(DOI_PATTERN, entry) or re.search(URL_PATTERN, entry):
            continue  # DOI/URL already captured above
        citations.append(entry)

    # Parenthetical author-year mentions, e.g. (Smith et al., 2021)
    for match in AUTHOR_YEAR_PATTERN.finditer(answer):
        citations.append(f"{match.group(1)}, {match.group(2)}")

    return list(dict.fromkeys(citations))[:MAX_CITATIONS]


# ------------------------------------------------------------------
# Similarity helpers
# ------------------------------------------------------------------

def normalize_title(title):
    title = re.sub(r"[^a-z0-9\s]", "", title.lower())
    return " ".join(title.split())


def title_overlap(title, text):
    """Share of the publication title's words that appear in the text (0-1)."""
    title_words = set(normalize_title(title).split())
    text_words = set(normalize_title(text).split())
    if not title_words or not text_words:
        return 0.0
    return len(title_words & text_words) / len(title_words)


def title_similarity(first, second):
    first, second = normalize_title(first), normalize_title(second)
    if not first or not second:
        return 0.0
    return SequenceMatcher(None, first, second).ratio()


def _result(status, message, title="", url="", similarity=None):
    data = {"status": status, "message": message, "title": title, "url": url}
    if similarity is not None:
        data["similarity"] = similarity
    return data


def _first_title(item):
    titles = item.get("title") or []
    return titles[0] if titles else "Untitled"


def _year_of(item):
    for key in ("issued", "published-print", "published-online", "created"):
        parts = (item.get(key) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            return str(parts[0][0])
    return ""


# ------------------------------------------------------------------
# DOI
# ------------------------------------------------------------------

def _check_doi(doi, surrounding_text):
    url = f"https://doi.org/{doi}"

    try:
        response = requests.get(
            f"https://api.crossref.org/works/{doi}", headers=HEADERS, timeout=15
        )
    except requests.RequestException:
        return _result("Error", "Could not connect to Crossref to check this DOI.", url=url)

    if response.status_code == 200:
        item = response.json().get("message", {})
        title = _first_title(item)
        year = _year_of(item)
        label = f"{title} ({year})" if year else title

        remainder = re.sub(DOI_PATTERN, " ", surrounding_text)
        remainder = re.sub(URL_PATTERN, " ", remainder)

        # A real DOI attached to a different title is a classic hallucination
        if len(remainder.split()) >= 5 and title_overlap(title, remainder) < 0.4:
            return _result(
                "Mismatch",
                "The DOI exists, but its registered title does not match the "
                "reference text. Check that the right paper is being cited.",
                title=label, url=url,
            )

        return _result("Verified", "The DOI exists in Crossref.", title=label, url=url)

    if response.status_code == 404:
        # Not every DOI is registered with Crossref (e.g. DataCite)
        try:
            resolved = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if resolved.status_code < 400:
                return _result(
                    "Verified",
                    "The DOI resolves (registered outside Crossref).",
                    url=resolved.url,
                )
        except requests.RequestException:
            pass

        return _result(
            "Not Found",
            "This DOI does not exist. It may have been invented by the AI.",
            url=url,
        )

    return _result("Error", f"Crossref returned status {response.status_code}.", url=url)


# ------------------------------------------------------------------
# URL
# ------------------------------------------------------------------

def _page_title(response):
    try:
        chunk = next(response.iter_content(65536, decode_unicode=True), "") or ""
        if isinstance(chunk, bytes):
            chunk = chunk.decode(response.encoding or "utf-8", errors="ignore")
        match = re.search(r"<title[^>]*>(.*?)</title>", chunk, re.IGNORECASE | re.DOTALL)
        return " ".join(match.group(1).split())[:200] if match else ""
    except Exception:  # noqa: BLE001
        return ""


def _check_url(url):
    try:
        response = requests.get(
            url, headers=HEADERS, timeout=12, allow_redirects=True, stream=True
        )
    except requests.exceptions.Timeout:
        return _result("Error", "The website took too long to respond.", url=url)
    except requests.exceptions.SSLError:
        return _result("Not Accessible", "The website has an invalid security certificate.", url=url)
    except requests.exceptions.ConnectionError:
        return _result(
            "Not Accessible",
            "The address could not be reached. It may be invalid or your "
            "internet may be offline.",
            url=url,
        )
    except requests.RequestException:
        return _result("Error", "Could not access the URL.", url=url)

    try:
        code = response.status_code

        if code < 400:
            return _result(
                "Accessible",
                "The page exists. This does not prove it supports the claim.",
                title=_page_title(response), url=response.url,
            )

        if code in (401, 403, 429, 999):
            return _result(
                "Restricted",
                f"The site exists but blocks automated checks (status {code}). "
                "Open it manually to confirm.",
                url=url,
            )

        return _result("Not Accessible", f"The page returned status {code}.", url=url)
    finally:
        response.close()


# ------------------------------------------------------------------
# Free-text reference / author-year
# ------------------------------------------------------------------

def _check_reference_text(citation):
    author_year = re.fullmatch(r"(.+?),\s*((?:19|20)\d{2})", citation)
    params = {"query.bibliographic": citation, "rows": 5}

    try:
        response = requests.get(
            "https://api.crossref.org/works", params=params, headers=HEADERS, timeout=15
        )
        response.raise_for_status()
        items = response.json()["message"]["items"]
    except requests.RequestException:
        return _result("Error", "Could not connect to Crossref.")
    except (KeyError, ValueError):
        return _result("Error", "Crossref returned an unexpected response.")

    if author_year:
        surname = re.split(r"\s", author_year.group(1).strip())[0].lower()
        year = author_year.group(2)

        for item in items:
            families = [a.get("family", "").lower() for a in item.get("author", [])]
            if surname in families and _year_of(item) == year:
                return _result(
                    "Possible Match",
                    "A publication by this author in that year exists, but only "
                    "the author and year were given. Confirm the title yourself.",
                    title=f"{_first_title(item)} ({year})",
                    url=item.get("URL", ""),
                )

        return _result(
            "Not Found",
            "No publication by this author in that year was found in Crossref. "
            "It may be a book or a non-indexed source, or it may be invented.",
        )

    best, best_score = None, 0.0
    for item in items:
        title = _first_title(item)
        score = max(title_overlap(title, citation), title_similarity(citation, title))
        if score > best_score:
            best, best_score = item, score

    if best and best_score >= 0.7:
        return _result(
            "Possible Match",
            "A similar publication was found. Verify its authors and details.",
            title=f"{_first_title(best)} ({_year_of(best)})".replace(" ()", ""),
            url=best.get("URL", ""),
            similarity=round(best_score * 100),
        )

    return _result(
        "Not Found",
        "No sufficiently similar publication was found in Crossref. It may "
        "not be indexed there, or it may not exist.",
    )


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def check_citation(citation):

    citation = (citation or "").strip()
    if not citation:
        return _result("Error", "No citation provided.")

    doi_match = re.search(DOI_PATTERN, citation, re.IGNORECASE)
    if doi_match:
        return _check_doi(_clean(doi_match.group(0)), citation)

    url_match = re.search(URL_PATTERN, citation)
    if url_match:
        return _check_url(_clean(url_match.group(0)))

    return _check_reference_text(citation)


def check_citations(citations, on_item=None, workers=4):
    """Check several citations in parallel, preserving order."""

    results = [None] * len(citations)

    def work(index):
        try:
            return index, check_citation(citations[index])
        except Exception as exc:  # noqa: BLE001
            return index, _result("Error", f"Check failed: {exc}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for done, (index, outcome) in enumerate(pool.map(work, range(len(citations))), 1):
            results[index] = {"citation": citations[index], **outcome}
            if on_item:
                on_item(done, len(citations))

    return results
