from __future__ import annotations

from niros.semantic_interpreter.fact_vocabulary import (
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)

_REQUIRED_JSON_SHAPE = """{
  "facts": [
    {
      "category": "...",
      "attribute": "...",
      "value": "...",
      "confidence": 0.0,
      "evidence": "..."
    }
  ],
  "detected_language": "...",
  "confidence": 0.0,
  "warnings": []
}"""


def build_semantic_extraction_system_prompt() -> str:
    return """You are a semantic fact extractor for NIROS.

You are not a psychologist.
You do not diagnose.
You do not infer hidden motives.
You do not detect NIROS patterns.

You only extract explicit semantic facts from the user text.

Rules:
- Output must be valid JSON only.
- Use only the provided NIROS vocabulary.
- If unsure, omit the fact.
- Evidence must be a short phrase from the user input.
- Confidence must be between 0.0 and 1.0.
- No markdown.
- No explanations.
- No extra keys."""


def _format_vocabulary(values: frozenset[str]) -> str:
    return ", ".join(sorted(values))


def build_semantic_extraction_user_prompt(text: str) -> str:
    return f"""Extract semantic facts from this user text:

{text}

Allowed categories:
{_format_vocabulary(VALID_CATEGORIES)}

Allowed attributes:
{_format_vocabulary(VALID_ATTRIBUTES)}

Allowed values:
{_format_vocabulary(VALID_VALUES)}

Return JSON with exactly this shape:
{_REQUIRED_JSON_SHAPE}"""
