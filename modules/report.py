"""Export helpers: Markdown and JSON versions of a report."""

import json


def _pct(value):
    return "n/a" if value is None else f"{value}%"


def to_json(analysis):
    return json.dumps(analysis, indent=2, ensure_ascii=False)


def to_markdown(analysis):
    scores = analysis["scores"]
    risk = analysis["risk"]
    lines = [
        "# GenTrust AI Reliability Report",
        "",
        f"*Generated {analysis['created']} · model `{analysis['model']}` · {analysis['elapsed']}s*",
        "",
        f"## Overall: {_pct(analysis['overall'])} - {risk['label']}",
        "",
        risk["message"],
        "",
        f"- Factual accuracy: {_pct(scores['factual'])}",
        f"- Consistency: {_pct(scores['consistency'])}",
        f"- Citations: {_pct(scores['citations'])}",
        "",
        "## Key findings",
        "",
    ]
    lines += [f"- {f['text']}" for f in analysis["findings"]] or ["- None"]

    lines += ["", "## Claim verification", ""]
    for i, item in enumerate(analysis["verification"], 1):
        lines.append(f"### {i}. {item['verdict'].upper()} - {item['claim']}")
        lines.append("")
        lines.append(item["reason"])
        for source in item.get("sources", []):
            lines.append(f"- [{source['title']}]({source['url']})")
        lines.append("")

    consistency = analysis["consistency"]
    if consistency:
        lines += ["## Consistency", "", f"Overall: {consistency['consistency_score']}%", ""]
        for item in consistency["question_results"]:
            lines.append(f"- **{item['question']}** - {item['consistency_score']}%: {item['summary']}")
            for issue in item["inconsistencies"]:
                lines.append(f"  - {issue['topic']}: {issue['details']}")
        lines.append("")

    if analysis["citations"]:
        lines += ["## Citations", ""]
        for item in analysis["citations"]:
            lines.append(f"- **{item['status']}** - {item['citation']}: {item['message']}")
        lines.append("")

    lines += [
        "---",
        "*Automated checks reduce risk but do not replace human judgement. A "
        "citation that exists does not prove it supports a claim.*",
    ]
    return "\n".join(lines)
