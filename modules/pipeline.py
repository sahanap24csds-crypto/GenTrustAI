"""Runs the complete analysis and returns one report dictionary."""

import time
from datetime import datetime

from modules.citation_checker import check_citations, detect_citations
from modules.claim_extractor import extract_claims
from modules.consistency import check_consistency, generate_consistency_questions
from modules.trust_score import (
    calculate_citation_score,
    calculate_trust_score,
    combine_scores,
    risk_level,
)
from modules.llm import LLMError
from modules.verifier import verify_claims

MAX_ANSWER_CHARS = 8000

BAD_CITATIONS = ("Not Found", "Not Accessible", "Mismatch")


def _build_findings(analysis):
    findings = []
    trust = analysis["trust"]

    if trust and trust["contradicted"]:
        n = trust["contradicted"]
        findings.append({
            "tone": "bad",
            "text": f"{n} claim{'s were' if n != 1 else ' was'} contradicted by web evidence.",
        })
    if trust and trust["unverifiable"]:
        n = trust["unverifiable"]
        findings.append({
            "tone": "warn",
            "text": f"{n} claim{'s' if n != 1 else ''} could not be confirmed or refuted.",
        })
    if trust and trust["supported"] and not trust["contradicted"]:
        findings.append({
            "tone": "good",
            "text": f"{trust['supported']} claim{'s are' if trust['supported'] != 1 else ' is'} supported by evidence.",
        })

    consistency = analysis["consistency"]
    if consistency:
        n = len(consistency["inconsistencies"])
        if n:
            findings.append({
                "tone": "warn",
                "text": f"The model gave conflicting answers on {n} point{'s' if n != 1 else ''} when re-asked.",
            })
        else:
            findings.append({"tone": "good", "text": "The model answered consistently when re-asked."})

    citations = analysis["citations"]
    if citations:
        bad = sum(1 for c in citations if c["status"] in BAD_CITATIONS)
        if bad:
            findings.append({
                "tone": "bad",
                "text": f"{bad} of {len(citations)} citation{'s' if len(citations) != 1 else ''} could not be validated.",
            })
        else:
            findings.append({"tone": "good", "text": "Detected citations check out (existence only)."})

    for message in analysis["errors"]:
        findings.append({"tone": "muted", "text": message})

    return findings


def run_analysis(client, model, answer, options, on_progress=None):
    """
    options: max_claims, num_questions, run_consistency, run_citations
    on_progress(fraction, message) is always called from the calling thread.
    """

    def progress(fraction, message):
        if on_progress:
            on_progress(min(max(fraction, 0.0), 1.0), message)

    started = time.time()
    answer = answer.strip()[:MAX_ANSWER_CHARS]

    analysis = {
        "answer": answer,
        "model": model,
        "created": datetime.now().strftime("%d %b %Y, %H:%M"),
        "options": dict(options),
        "claims": [],
        "verification": [],
        "trust": None,
        "questions": [],
        "consistency": None,
        "citations": [],
        "scores": {},
        "overall": None,
        "risk": None,
        "findings": [],
        "errors": [],
        "elapsed": 0.0,
    }

    # Share of the progress bar given to each stage
    stages = ["claims"]
    if options.get("run_consistency"):
        stages.append("consistency")
    if options.get("run_citations"):
        stages.append("citations")
    weights = {"claims": 0.6, "consistency": 0.3, "citations": 0.1}
    total = sum(weights[s] for s in stages)
    offsets, running = {}, 0.0
    for s in stages:
        offsets[s] = (running / total, weights[s] / total)
        running += weights[s]

    def stage_progress(stage, inner, message):
        start, span = offsets[stage]
        progress(start + span * inner, message)

    # ---------------- Claims ----------------
    stage_progress("claims", 0.0, "Extracting factual claims…")
    try:
        analysis["claims"] = extract_claims(
            client, answer, model, max_claims=options.get("max_claims", 8)
        )
    except LLMError as exc:
        if exc.fatal:
            raise
        analysis["errors"].append(f"Claim extraction failed: {exc}")
    except Exception as exc:  # noqa: BLE001
        analysis["errors"].append(f"Claim extraction failed: {exc}")

    if analysis["claims"]:
        count = len(analysis["claims"])
        stage_progress("claims", 0.15, f"Fact-checking {count} claims against the web…")

        def on_claim(done, total_claims):
            stage_progress(
                "claims", 0.15 + 0.85 * done / total_claims,
                f"Verified {done} of {total_claims} claims…",
            )

        try:
            analysis["verification"] = verify_claims(client, analysis["claims"], model, on_item=on_claim)
        except Exception as exc:  # noqa: BLE001
            analysis["errors"].append(f"Claim verification failed: {exc}")

        analysis["trust"] = calculate_trust_score(analysis["verification"])

        if analysis["trust"]["errors"]:
            analysis["errors"].append(
                f"{analysis['trust']['errors']} claim(s) could not be checked "
                "because of a technical problem and were left out of the score."
            )
    elif not analysis["errors"]:
        analysis["errors"].append("No checkable factual claims were found in this text.")

    # ---------------- Consistency ----------------
    if options.get("run_consistency"):
        stage_progress("consistency", 0.0, "Designing consistency questions…")
        try:
            analysis["questions"] = generate_consistency_questions(
                client, answer, model, max_questions=options.get("num_questions", 3)
            )

            def on_question(done, total_q):
                stage_progress(
                    "consistency", 0.2 + 0.8 * done / total_q,
                    f"Re-asking the model… {done} of {total_q} questions compared",
                )

            stage_progress("consistency", 0.2, "Re-asking the model several times…")
            analysis["consistency"] = check_consistency(
                client, analysis["questions"], model, on_item=on_question
            )
            for failure in analysis["consistency"].get("failures", []):
                analysis["errors"].append(f"Consistency check skipped - {failure}")
        except Exception as exc:  # noqa: BLE001
            analysis["errors"].append(f"Consistency analysis failed: {exc}")

    # ---------------- Citations ----------------
    if options.get("run_citations"):
        stage_progress("citations", 0.0, "Looking for citations…")
        try:
            found = detect_citations(answer)
            if found:
                def on_citation(done, total_c):
                    stage_progress("citations", done / total_c, f"Checked {done} of {total_c} citations…")

                analysis["citations"] = check_citations(found, on_item=on_citation)
        except Exception as exc:  # noqa: BLE001
            analysis["errors"].append(f"Citation checking failed: {exc}")

    # ---------------- Scores ----------------
    factual = analysis["trust"]["score"] if analysis["trust"] else None
    consistency_score = (
        analysis["consistency"]["consistency_score"] if analysis["consistency"] else None
    )
    citation_score = calculate_citation_score(analysis["citations"])

    analysis["scores"] = {
        "factual": factual,
        "consistency": consistency_score,
        "citations": citation_score,
    }
    analysis["overall"] = combine_scores(factual, consistency_score, citation_score)
    analysis["risk"] = risk_level(
        analysis["overall"],
        contradicted=analysis["trust"]["contradicted"] if analysis["trust"] else 0,
    )
    analysis["findings"] = _build_findings(analysis)
    analysis["elapsed"] = round(time.time() - started, 1)

    progress(1.0, "Analysis complete")
    return analysis
