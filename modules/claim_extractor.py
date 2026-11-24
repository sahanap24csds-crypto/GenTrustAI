"""Step 1: break an AI answer into individually checkable factual claims."""

import re

from modules.llm import chat_json


def extract_claims(client, answer, model, max_claims=10):

    if not answer or not answer.strip():
        return []

    prompt = f"""
You are an expert factual claim extraction system.

Extract accurate, independent, checkable factual claims from the
AI-generated answer below.

RULES:
1. Extract only factual statements that can be checked.
2. Ignore opinions, advice, greetings and personal preferences.
3. Separate independent facts into individual claims.
4. Do not split one fact into unnecessary smaller claims.
5. Remove duplicate or repeated claims.
6. Preserve names, dates, numbers, units and locations.
7. Make every claim understandable on its own (no pronouns like "he"
   or "it" without naming the subject).
8. Do not change the original meaning or add new information.
9. Do not verify claims or decide whether they are true.
10. Ignore reference lists, URLs and DOIs; they are checked separately.
11. Return at most {max_claims} claims. If there are more, keep the most
    specific and important ones (names, dates, numbers, events).

EXAMPLE:

Input:
Albert Einstein was born in Germany in 1879. He developed the theory of
relativity. Einstein won the Nobel Prize in Physics in 1921.

Output:
{{
    "claims": [
        {{"claim": "Albert Einstein was born in Germany in 1879."}},
        {{"claim": "Albert Einstein developed the theory of relativity."}},
        {{"claim": "Albert Einstein won the Nobel Prize in Physics in 1921."}}
    ]
}}

Return ONLY valid JSON in this exact format:

{{
    "claims": [
        {{"claim": "First factual claim"}},
        {{"claim": "Second factual claim"}}
    ]
}}

AI-GENERATED ANSWER:
{answer}
"""

    data = chat_json(
        client,
        model,
        [
            {
                "role": "system",
                "content": (
                    "You are a precise factual claim extractor. "
                    "Extract only facts from the supplied text. "
                    "Do not invent, verify or duplicate claims. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1800,
    )

    claims = data.get("claims", [])
    if not isinstance(claims, list):
        raise ValueError("Invalid claim extraction format returned by the AI.")

    cleaned, seen = [], set()

    for item in claims:
        text = item.get("claim", "") if isinstance(item, dict) else item
        if not isinstance(text, str):
            continue

        text = text.strip()
        if not text:
            continue

        normalized = " ".join(re.sub(r"[^\w\s]", "", text.lower()).split())
        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned.append({"claim": text})

    return cleaned[:max_claims]
