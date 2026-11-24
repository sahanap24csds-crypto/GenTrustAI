"""Step 3: self-consistency test.

The model is asked the same factual questions several times. Real knowledge
tends to be stable; hallucinated details tend to change from run to run.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.llm import LLMError, chat, chat_json

ANSWERS_PER_QUESTION = 3


# --------------------------------------------------
# Question generation
# --------------------------------------------------

def generate_consistency_questions(client, answer, model, max_questions=3):

    prompt = f"""
Read the AI-generated answer and create up to {max_questions} different
factual questions covering its most important, specific topics.

RULES:
1. Cover different factual topics; do not focus on only one.
2. Include important names, dates, events and numbers.
3. Avoid duplicate or nearly identical questions.
4. Each question must be clear and answerable on its own, without
   referring to "the answer" or "the text".
5. Do not answer the questions.

AI-GENERATED ANSWER:
{answer}

Return ONLY valid JSON:

{{
    "questions": [
        "First factual question?",
        "Second factual question?"
    ]
}}
"""

    data = chat_json(
        client,
        model,
        [
            {
                "role": "system",
                "content": "Generate diverse, self-contained factual questions. Return valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=800,
    )

    questions = data.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError("Invalid question generation format.")

    cleaned, seen = [], set()
    for question in questions:
        if isinstance(question, str):
            question = question.strip()
            if question and question.lower() not in seen:
                seen.add(question.lower())
                cleaned.append(question)

    if not cleaned:
        raise ValueError("No valid questions were generated.")

    return cleaned[:max_questions]


# --------------------------------------------------
# One question: answer 3 times, then compare
# --------------------------------------------------

def _check_question(client, question, model):

    responses = []
    for _ in range(ANSWERS_PER_QUESTION):
        text = chat(
            client,
            model,
            [
                {
                    "role": "system",
                    "content": (
                        "You are a factual assistant. Answer clearly in 3 to 5 "
                        "sentences in plain text. Do not invent facts."
                    ),
                },
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=700,
        )
        responses.append(text.strip())

    numbered = "\n\n".join(
        f"ANSWER {i}:\n{text}" for i, text in enumerate(responses, 1)
    )

    prompt = f"""
You are an AI response consistency evaluator.

Compare the following answers to the SAME question.

QUESTION:
{question}

{numbered}

TASKS:
1. Identify factual claims that differ between the answers.
2. Look for contradictions in dates, names, numbers, events and explanations.
3. Different wording with the same meaning is NOT an inconsistency.
4. Different details that do not conflict are NOT contradictions.
5. Give a consistency score from 0 to 100.

SCORING:
100 = no factual contradictions. Lower scores = more factual disagreement.

You are checking agreement between the answers, NOT whether they are true.

Return ONLY valid JSON:

{{
    "consistency_score": 80,
    "summary": "Short explanation",
    "inconsistencies": [
        {{"topic": "Example topic", "details": "Explain the disagreement"}}
    ]
}}
"""

    result = chat_json(
        client,
        model,
        [
            {
                "role": "system",
                "content": "You evaluate factual consistency carefully and objectively. Return valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
    )

    score = result.get("consistency_score", 0)
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        score = 0
    score = max(0, min(100, round(score)))

    raw_issues = result.get("inconsistencies", [])
    issues = []
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if isinstance(item, dict):
                issues.append({
                    "topic": str(item.get("topic", "Difference")),
                    "details": str(item.get("details", "No details provided.")),
                })

    summary = result.get("summary", "")
    if not isinstance(summary, str) or not summary.strip():
        summary = "Comparison completed."

    return {
        "question": question,
        "responses": responses,
        "consistency_score": score,
        "summary": summary.strip(),
        "inconsistencies": issues,
    }


# --------------------------------------------------
# All questions
# --------------------------------------------------

def check_consistency(client, questions, model, on_item=None, workers=3):

    if isinstance(questions, str):
        questions = [questions]

    questions = [q.strip() for q in questions if isinstance(q, str) and q.strip()]
    questions = list(dict.fromkeys(questions))[:5]

    if not questions:
        raise ValueError("No valid consistency questions were provided.")

    slots = [None] * len(questions)
    failures = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_check_question, client, q, model): i
            for i, q in enumerate(questions)
        }

        for done, future in enumerate(as_completed(futures), 1):
            index = futures[future]
            try:
                slots[index] = future.result()
            except (LLMError, ValueError) as exc:
                failures.append(f"Question {index + 1}: {exc}")

            if on_item:
                on_item(done, len(questions))

    question_results = [item for item in slots if item]

    if not question_results:
        raise ValueError(
            "Consistency testing failed for every question. "
            + (failures[0] if failures else "")
        )

    overall = round(
        sum(item["consistency_score"] for item in question_results)
        / len(question_results)
    )

    all_issues = [
        {"question": item["question"], **issue}
        for item in question_results
        for issue in item["inconsistencies"]
    ]

    return {
        "consistency_score": overall,
        "question_results": question_results,
        "inconsistencies": all_issues,
        "failures": failures,
        "summary": (
            f"Asked {len(question_results)} factual question(s), "
            f"{ANSWERS_PER_QUESTION} times each, and compared the answers."
        ),
    }
