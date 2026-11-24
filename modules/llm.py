"""Shared helpers for talking to Groq: retries, JSON parsing, friendly errors."""

import json
import re
import time

DEFAULT_MODEL = "llama-3.3-70b-versatile"

MODEL_CHOICES = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant",
]


class LLMError(RuntimeError):
    """An error whose message is safe and helpful to show to the user.

    fatal=True means retrying other steps is pointless (bad key, missing
    model, exhausted rate limit), so the whole analysis should stop.
    """

    def __init__(self, message, fatal=False):
        super().__init__(message)
        self.fatal = fatal


def make_client(api_key):
    from groq import Groq

    return Groq(api_key=api_key, timeout=60.0, max_retries=0)


# ------------------------------------------------------------------
# Text helpers
# ------------------------------------------------------------------

def strip_think(text):
    """Remove <think>...</think> blocks emitted by reasoning models."""
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    if "</think>" in text.lower():
        text = re.split(r"</think>", text, flags=re.IGNORECASE)[-1]
    return text.strip()


def extract_json(text):
    """Parse a JSON object from model output, tolerating fences and chatter."""
    cleaned = strip_think(text)
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned.strip(), flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("The model did not return valid JSON.")


# ------------------------------------------------------------------
# Error classification
# ------------------------------------------------------------------

def _retry_delay(message, attempt):
    match = re.search(r"try again in (?:(\d+)m)?\s*([\d.]+)s", message)
    if match:
        minutes = int(match.group(1) or 0)
        return minutes * 60 + float(match.group(2)) + 0.5
    return min(2 ** attempt, 10)


def _model_extras(model):
    name = model.lower()
    if "qwen3" in name:
        return {"reasoning_format": "hidden"}
    if "gpt-oss" in name:
        return {"reasoning_effort": "low"}
    return None


# ------------------------------------------------------------------
# Core call
# ------------------------------------------------------------------

def chat(client, model, messages, json_mode=False, temperature=0.1,
         max_tokens=1200, retries=4):
    """Call the chat API with retries and return the cleaned text."""

    extras = _model_extras(model)
    if extras:
        max_tokens = max(max_tokens * 3, 4000)

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }
    if extras:
        kwargs["extra_body"] = extras
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    attempt = 0
    last_problem = "unknown error"

    while attempt <= retries:
        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            text = strip_think(choice.message.content or "")
            if text:
                return text
            last_problem = f"empty response (finish reason: {choice.finish_reason})"
            attempt += 1
            continue

        except Exception as exc:  # noqa: BLE001 - classify below
            message = str(exc).lower()
            last_problem = str(exc)

            if "response_format" in kwargs and any(
                key in message
                for key in ("json_validate_failed", "response_format", "failed to generate json")
            ):
                kwargs.pop("response_format")
                continue

            if "extra_body" in kwargs and "reasoning" in message:
                kwargs.pop("extra_body")
                continue

            if any(k in message for k in ("invalid api key", "invalid_api_key", "401", "unauthorized")):
                raise LLMError(
                    "Your Groq API key was rejected. Please check the key in your .env file.",
                    fatal=True,
                ) from exc

            if ("model" in message and any(
                    k in message for k in ("not found", "does not exist", "decommissioned", "no access"))):
                raise LLMError(
                    f"The model '{model}' is not available on your Groq account. "
                    "Choose another model in the sidebar.",
                    fatal=True,
                ) from exc

            retryable = any(
                k in message
                for k in ("429", "rate limit", "rate_limit", "500", "502", "503",
                          "504", "timeout", "timed out", "connection", "overloaded")
            )
            if not retryable:
                raise LLMError(f"Groq request failed: {exc}") from exc

            delay = _retry_delay(message, attempt)
            if delay > 45:
                raise LLMError(
                    "The Groq rate limit has been reached. Please wait a little "
                    "while (or switch to a different model) and try again.",
                    fatal=True,
                ) from exc

            time.sleep(delay)
            attempt += 1

    raise LLMError(f"Groq did not return a usable answer ({last_problem}).")


def chat_json(client, model, messages, temperature=0.1, max_tokens=1200):
    """Like chat(), but returns a parsed JSON object (retries once on bad JSON)."""
    last_error = None
    for attempt in range(2):
        text = chat(
            client, model, messages, json_mode=True,
            temperature=0.0 if attempt else temperature,
            max_tokens=max_tokens,
        )
        try:
            return extract_json(text)
        except ValueError as exc:
            last_error = exc
    raise LLMError(str(last_error))
