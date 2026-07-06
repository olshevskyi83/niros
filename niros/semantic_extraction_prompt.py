"""Semantic Extraction Prompt — deterministic OpenAI prompt generation for raw segments."""

from __future__ import annotations

from niros.raw_source import RawSource, RawSourceSegment

REQUIRED_EXTRACTION_FIELDS: tuple[str, ...] = (
    "therapeutic_function",
    "psychological_function",
    "symbolic_elements",
    "candidate_targets",
    "generation_rules",
    "voice_rules",
    "repetition_rules",
    "pause_rules",
    "contraindications",
    "confidence",
)

_PROMPT_RULES: tuple[str, ...] = (
    "Never summarize the source text.",
    "Never rewrite the source text.",
    "Never improve the source text.",
    "Never generate new therapeutic content.",
    "Do not invent symbolism or mechanisms that are not supported by the segment.",
    "Only extract observable therapeutic mechanisms grounded in the provided raw text.",
    "If uncertain about any field, reflect that uncertainty in confidence.",
)

_JSON_SCHEMA_LINES: tuple[str, ...] = (
    '  "therapeutic_function": "string",',
    '  "psychological_function": "string",',
    '  "symbolic_elements": ["string"],',
    '  "candidate_targets": ["string"],',
    '  "generation_rules": ["string"],',
    '  "voice_rules": ["string"],',
    '  "repetition_rules": ["string"],',
    '  "pause_rules": ["string"],',
    '  "contraindications": ["string"],',
    '  "confidence": 0.0',
)


def _format_source_metadata(raw_source: RawSource) -> str:
    lines = [
        f"source_id: {raw_source.source_id}",
        f"source_family: {raw_source.source_family}",
        f"title: {raw_source.title}",
        f"language: {raw_source.language}",
        f"source_type: {raw_source.source_type}",
        f"author: {raw_source.author}",
        f"year: {raw_source.year if raw_source.year is not None else 'null'}",
    ]
    return "\n".join(lines)


def _format_segment_content(raw_segment: RawSourceSegment) -> str:
    lines = [
        f"segment_id: {raw_segment.segment_id}",
        f"sequence_index: {raw_segment.sequence_index}",
        "raw_text:",
        raw_segment.raw_text,
    ]
    return "\n".join(lines)


def build_semantic_extraction_prompt(
    raw_source: RawSource,
    raw_segment: RawSourceSegment,
) -> str:
    """Build a deterministic extraction prompt for one raw source segment."""
    rules = "\n".join(f"- {rule}" for rule in _PROMPT_RULES)
    required_fields = "\n".join(f"- {field}" for field in REQUIRED_EXTRACTION_FIELDS)
    json_schema = "{\n" + "\n".join(_JSON_SCHEMA_LINES) + "\n}"

    return (
        "You are a therapeutic mechanism extractor for NIROS Knowledge Factory.\n"
        "Analyze the source segment below and extract only observable therapeutic "
        "mechanisms supported by the raw text.\n\n"
        "Strict rules:\n"
        f"{rules}\n\n"
        "Required extraction fields:\n"
        f"{required_fields}\n\n"
        "Source metadata:\n"
        f"{_format_source_metadata(raw_source)}\n\n"
        "Source segment:\n"
        f"{_format_segment_content(raw_segment)}\n\n"
        "Respond with valid JSON only. Do not include markdown fences or commentary.\n"
        "Use this JSON shape:\n"
        f"{json_schema}\n"
        "confidence must be a number between 0.0 and 1.0."
    )
