"""Report rendering (tabs) for a finished analysis."""

import re

import streamlit as st

from modules import ui
from modules.report import to_json, to_markdown

VERDICTS = {
    "supported": ("Supported", "good"),
    "contradicted": ("Contradicted", "bad"),
    "unverifiable": ("Unverifiable", "warn"),
    "error": ("Not checked", "muted"),
}

CITATION_TONES = {
    "Verified": "good",
    "Accessible": "good",
    "Possible Match": "warn",
    "Restricted": "warn",
    "Mismatch": "warn",
    "Not Found": "bad",
    "Not Accessible": "bad",
    "Error": "muted",
}


def _safe_link(title, url):
    title = re.sub(r"[\[\]]", "", title)
    url = url.replace(" ", "%20").replace(")", "%29").replace("(", "%28")
    return f"[{title}]({url})"


# ------------------------------------------------------------------
# Overview
# ------------------------------------------------------------------

def _overview(analysis):
    risk = analysis["risk"]
    scores = analysis["scores"]
    trust = analysis["trust"]
    tone = risk["tone"]

    left, right = st.columns([1, 1.45], gap="large")

    with left:
        ui.render(
            f'<div class="gt-card"><div class="gt-gauge-wrap">'
            f'{ui.gauge(analysis["overall"], tone, "Overall trust")}'
            f'<div class="gt-verdict-label" style="color:{ui.color(tone)}">{ui.esc(risk["label"])}</div>'
            f'<div class="gt-verdict-msg">{ui.esc(risk["message"])}</div>'
            f'</div></div>'
        )

    with right:
        ui.render('<div class="gt-section-title" style="margin-top:0">What we found</div>')
        if analysis["findings"]:
            for item in analysis["findings"]:
                ui.render(ui.finding(item["text"], item["tone"]))
        else:
            st.info("No findings to report.")

    st.write("")
    c1, c2, c3 = st.columns(3, gap="medium")

    factual = scores["factual"]
    c1.markdown(
        ui.stat_card(
            "Factual accuracy",
            "–" if factual is None else f"{factual}%",
            f"{trust['supported']} supported · {trust['contradicted']} contradicted · "
            f"{trust['unverifiable']} unverified" if trust else "Not available",
            factual,
        ),
        unsafe_allow_html=True,
    )

    consistency = scores["consistency"]
    c2.markdown(
        ui.stat_card(
            "Consistency",
            "–" if consistency is None else f"{consistency}%",
            "How stable the model's answers are" if consistency is not None else "Not run or unavailable",
            consistency,
        ),
        unsafe_allow_html=True,
    )

    citation = scores["citations"]
    n_cit = len(analysis["citations"])
    c3.markdown(
        ui.stat_card(
            "Citations",
            "–" if citation is None else f"{citation}%",
            f"{n_cit} reference{'s' if n_cit != 1 else ''} checked" if n_cit else "No citations detected",
            citation,
        ),
        unsafe_allow_html=True,
    )

    ui.render(
        '<div class="gt-note"><strong>How to read this.</strong> The score estimates how well '
        'the answer is backed by evidence. It is not the probability that every statement is true. '
        'A citation that exists does not prove it supports a claim, and "unverifiable" means '
        'no clear evidence was found, not that the claim is false.</div>'
    )

    with st.expander("View the analysed text"):
        st.write(analysis["answer"])


# ------------------------------------------------------------------
# Claims
# ------------------------------------------------------------------

def _claims(analysis):
    results = analysis["verification"]
    if not results:
        st.info("No factual claims were checked for this text.")
        return

    ui.section_title("Claim-by-claim verification", "Every verdict is based only on the web evidence shown.")

    options = ["All", "Contradicted", "Unverifiable", "Supported"]
    choice = st.radio("Filter claims", options, horizontal=True, label_visibility="collapsed")
    wanted = None if choice == "All" else choice.lower()

    shown = 0
    for index, item in enumerate(results, 1):
        if wanted and item["verdict"] != wanted:
            continue
        shown += 1

        label, tone = VERDICTS.get(item["verdict"], VERDICTS["error"])

        with st.container(border=True):
            ui.render(
                f'<div class="gt-claim-head"><div>'
                f'<div class="gt-claim-num">Claim {index}</div>'
                f'<div class="gt-claim-text">{ui.esc(item["claim"])}</div></div>'
                f'{ui.chip(label, tone)}</div>'
                f'<div class="gt-reason">{ui.esc(item["reason"])}</div>'
                f'<div class="gt-meta">Confidence: {ui.esc(item.get("confidence", "medium")).capitalize()}</div>'
            )

            sources = item.get("sources") or []
            if sources:
                with st.expander(f"Evidence ({len(sources)} source{'s' if len(sources) != 1 else ''})"):
                    for source in sources:
                        st.markdown(f"**{_safe_link(source['title'], source['url'])}**")
                        st.caption(source["snippet"])

    if shown == 0:
        st.info(f"No {choice.lower()} claims.")


# ------------------------------------------------------------------
# Consistency
# ------------------------------------------------------------------

def _consistency(analysis):
    data = analysis["consistency"]
    if not data:
        st.info("The consistency check was turned off or could not be completed.")
        return

    score = data["consistency_score"]
    tone = ui.tone_for_score(score)

    left, right = st.columns([1, 2.2], gap="large")
    with left:
        ui.render(f'<div class="gt-card"><div class="gt-gauge-wrap">{ui.gauge(score, tone, "Consistent", small=True)}</div></div>')
    with right:
        ui.section_title("Does the AI give the same answer twice?")
        st.write(
            "Each question below was put to the model several times. Reliable knowledge "
            "stays stable between runs, while made-up details tend to change."
        )
        st.caption(data["summary"])

    for index, item in enumerate(data["question_results"], 1):
        item_tone = ui.tone_for_score(item["consistency_score"])
        with st.container(border=True):
            ui.render(
                f'<div class="gt-claim-head"><div><div class="gt-claim-num">Question {index}</div>'
                f'<div class="gt-claim-text">{ui.esc(item["question"])}</div></div>'
                f'{ui.chip(str(item["consistency_score"]) + "% consistent", item_tone)}</div>'
                f'<div class="gt-reason">{ui.esc(item["summary"])}</div>'
            )

            for issue in item["inconsistencies"]:
                ui.render(
                    f'<div class="gt-note" style="border-color:{ui.color("warn")};background:rgba(251,191,36,.08)">'
                    f'<strong>{ui.esc(issue["topic"])}</strong><br>{ui.esc(issue["details"])}</div>'
                )

            with st.expander("See the model's answers"):
                for number, response in enumerate(item["responses"], 1):
                    st.markdown(f"**Answer {number}**")
                    st.write(response)


# ------------------------------------------------------------------
# Citations
# ------------------------------------------------------------------

def _citations(analysis):
    results = analysis["citations"]

    if not results:
        ui.render(
            '<div class="gt-card"><h4>No citations detected</h4>'
            '<p>GenTrust looks for DOIs, web links, entries under a "References" heading and '
            'author-year mentions like (Smith, 2021). None were found in this text.</p></div>'
        )
        return

    ui.section_title("Citation checks", "Checks whether each reference exists. It cannot confirm that it supports the claim.")

    for index, item in enumerate(results, 1):
        tone = CITATION_TONES.get(item["status"], "muted")
        with st.container(border=True):
            ui.render(
                f'<div class="gt-claim-head"><div><div class="gt-claim-num">Citation {index}</div>'
                f'<div class="gt-claim-text" style="word-break:break-word">{ui.esc(item["citation"])}</div></div>'
                f'{ui.chip(item["status"], tone)}</div>'
                f'<div class="gt-reason">{ui.esc(item["message"])}</div>'
            )
            if item.get("title"):
                st.caption(f"Matched publication: {item['title']}")
            if item.get("url"):
                st.markdown(f"[Open source ↗]({item['url']})")


# ------------------------------------------------------------------
# Export
# ------------------------------------------------------------------

def _export(analysis):
    ui.section_title("Take your report with you")
    stamp = analysis["created"].replace(" ", "_").replace(",", "").replace(":", "-")

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇  Download as Markdown",
        to_markdown(analysis),
        file_name=f"gentrust_report_{stamp}.md",
        mime="text/markdown",
    )
    c2.download_button(
        "⬇  Download as JSON",
        to_json(analysis),
        file_name=f"gentrust_report_{stamp}.json",
        mime="application/json",
    )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def render_report(analysis):
    ui.render(
        f'<div class="gt-section-title" style="font-size:1.7rem">Reliability report</div>'
        f'<div class="gt-section-sub">Analysed with {ui.esc(analysis["model"])} · '
        f'{ui.esc(analysis["created"])} · {analysis["elapsed"]}s</div>'
    )

    n_claims = len(analysis["verification"])
    n_cit = len(analysis["citations"])

    tabs = st.tabs([
        "Overview",
        f"Claims ({n_claims})",
        "Consistency",
        f"Citations ({n_cit})",
        "Export",
    ])

    with tabs[0]:
        _overview(analysis)
    with tabs[1]:
        _claims(analysis)
    with tabs[2]:
        _consistency(analysis)
    with tabs[3]:
        _citations(analysis)
    with tabs[4]:
        _export(analysis)
