"""Tolerant JSON extraction from LLM output, shared by generator and diagnostician."""

import json
from typing import Any


def extract_json_object(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Pull the first JSON object out of a model response.

    Tolerates markdown fences and stray prose around the object — models drift
    even when told not to, and rejecting salvageable output just wastes budget.
    Returns (object, None) or (None, error message).
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None, "response contained no JSON object"
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        return None, f"response was not valid JSON: {exc}"
    if not isinstance(parsed, dict):
        return None, "response JSON was not an object"
    return parsed, None
