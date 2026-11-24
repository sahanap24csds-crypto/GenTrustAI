"""Scoring: turns verdicts, consistency and citation checks into one score."""

VERDICT_WEIGHTS = {
    "supported": 1.0,
    "unverifiable": 0.5,   # not wrong, but not backed by evidence either
    "contradicted": 0.0,
}

CITATION_WEIGHTS = {
    "Verified": 1.0,
    "Accessible": 0.8,
    "Possible Match": 0.6,
    "Restricted": 0.5,
    "Mismatch": 0.25,
    "Not Accessible": 0.0,
    "Not Found": 0.0,
}

# Share of the overall score contributed by each check
OVERALL_WEIGHTS = {"factual": 0.60, "consistency": 0.25, "citations": 0.15}


def calculate_trust_score(results):
    """Factual score from claim verdicts. Errors are excluded from scoring."""

    counts = {"supported": 0, "contradicted": 0, "unverifiable": 0, "error": 0}

    for result in results or []:
        verdict = str(result.get("verdict", "")).lower()
        counts[verdict if verdict in counts else "error"] += 1

    scored = counts["supported"] + counts["contradicted"] + counts["unverifiable"]

    if scored == 0:
        score = None
    else:
        points = sum(VERDICT_WEIGHTS[v] * counts[v] for v in VERDICT_WEIGHTS)
        score = round(points / scored * 100)

    return {
        "score": score,
        "supported": counts["supported"],
        "contradicted": counts["contradicted"],
        "unverifiable": counts["unverifiable"],
        "errors": counts["error"],
        "total": len(results or []),
    }


def calculate_citation_score(citation_results):
    """Citation score, or None when there is nothing scoreable."""

    weights = [
        CITATION_WEIGHTS[r["status"]]
        for r in citation_results or []
        if r.get("status") in CITATION_WEIGHTS
    ]
    if not weights:
        return None
    return round(sum(weights) / len(weights) * 100)


def combine_scores(factual, consistency, citations):
    """Weighted overall score over whichever checks produced a result."""

    parts = {"factual": factual, "consistency": consistency, "citations": citations}
    available = {k: v for k, v in parts.items() if v is not None}

    if not available:
        return None

    total_weight = sum(OVERALL_WEIGHTS[k] for k in available)
    return round(sum(OVERALL_WEIGHTS[k] * v for k, v in available.items()) / total_weight)


def risk_level(score, contradicted=0):
    """Human-friendly interpretation of the overall score."""

    if score is None:
        return {
            "label": "Not enough data",
            "tone": "muted",
            "message": "No checks could be completed, so a reliability score is not available.",
        }

    if score >= 85:
        level = {"label": "High reliability", "tone": "good",
                 "message": "Most details are backed by evidence and the model answers consistently."}
    elif score >= 70:
        level = {"label": "Generally reliable", "tone": "good",
                 "message": "The answer holds up well, with a few details worth double-checking."}
    elif score >= 50:
        level = {"label": "Use with caution", "tone": "warn",
                 "message": "Several details are unconfirmed or inconsistent. Verify before relying on it."}
    else:
        level = {"label": "Low reliability", "tone": "bad",
                 "message": "Significant problems were found. Do not rely on this answer without checking."}

    if contradicted and level["tone"] == "good":
        level = {"label": "Use with caution", "tone": "warn",
                 "message": "The score is decent, but at least one claim was contradicted by evidence."}

    return level
