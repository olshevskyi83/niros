"""Semantic Extraction Prompt — ontology-guided OpenAI prompt generation for raw segments."""

from __future__ import annotations

from niros.ontology_context import OntologyContext, load_ontology_context
from niros.raw_source import RawSource, RawSourceSegment
from niros.semantic_knowledge_extraction import (
    REQUIRED_SEMANTIC_KNOWLEDGE_FIELDS,
    SUPPORTED_ONTOLOGY_STATUSES,
    format_ontology_mechanism_catalog,
)
from niros.semantic_therapeutic_gate import (
    KNOWLEDGE_KIND_BIBLIOGRAPHY,
    KNOWLEDGE_KIND_CASE_EXAMPLE,
    KNOWLEDGE_KIND_CLINICAL_CONTRAINDICATION,
    KNOWLEDGE_KIND_EXERCISE_OR_PRACTICE,
    KNOWLEDGE_KIND_FRONT_MATTER,
    KNOWLEDGE_KIND_INTERVENTION_PRINCIPLE,
    KNOWLEDGE_KIND_MARKETING,
    KNOWLEDGE_KIND_STATISTICS_ONLY,
    KNOWLEDGE_KIND_THEORETICAL_BACKGROUND,
    KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
    KNOWLEDGE_KIND_UNKNOWN,
)

REQUIRED_EXTRACTION_FIELDS: tuple[str, ...] = (
    "mechanism_name",
    "mechanism_description",
    "why_this_is_a_mechanism",
    "causal_process",
    "evidence",
    "ontology_status",
    "confidence",
    "therapeutic_function",
    "psychological_function",
    "symbolic_elements",
    "candidate_targets",
    "generation_rules",
    "voice_rules",
    "repetition_rules",
    "pause_rules",
    "contraindications",
)

REQUIRED_RELEVANCE_FIELDS: tuple[str, ...] = (
    "is_relevant",
    "relevance_score",
    "knowledge_kind",
    "reasoning",
    "evidence_span",
    "skip_reason",
    "suggested_mechanisms",
    "should_extract",
)

KNOWLEDGE_KIND_OPTIONS: tuple[str, ...] = (
    KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
    KNOWLEDGE_KIND_INTERVENTION_PRINCIPLE,
    KNOWLEDGE_KIND_EXERCISE_OR_PRACTICE,
    KNOWLEDGE_KIND_CLINICAL_CONTRAINDICATION,
    KNOWLEDGE_KIND_CASE_EXAMPLE,
    KNOWLEDGE_KIND_THEORETICAL_BACKGROUND,
    KNOWLEDGE_KIND_FRONT_MATTER,
    KNOWLEDGE_KIND_MARKETING,
    KNOWLEDGE_KIND_STATISTICS_ONLY,
    KNOWLEDGE_KIND_BIBLIOGRAPHY,
    KNOWLEDGE_KIND_UNKNOWN,
)

_PROMPT_RULES: tuple[str, ...] = (
    "Behave as an experienced psychotherapy researcher, not a text summarizer.",
    "Ask: what new reusable therapeutic knowledge does this passage contribute?",
    "Extract only psychological mechanisms, causal processes, or intervention principles that teach a therapist something reusable.",
    "Require an explained change process: what maintains suffering, what changes, why, and how.",
    "Do not extract merely because the segment mentions ACT, acceptance, values, defusion, mindfulness, pain, anxiety, or suffering.",
    "Never extract definitions, terminology lists, marketing copy, introductions, chapter summaries, or generic examples without mechanism logic.",
    "Never extract isolated therapeutic phrases such as 'Acceptance is important.' without causal explanation.",
    "Skip front matter, bibliographies, statistics-only passages, and keyword-only mentions.",
    "If the passage strengthens an existing ontology mechanism with new evidence or nuance, say so explicitly.",
    "If the passage introduces a mechanism not in the ontology, set ontology_status to potential_new_mechanism. Do not reject it.",
    "Never summarize, rewrite, or improve the source text.",
    "Do not invent mechanisms unsupported by the segment.",
    "If uncertain, reflect uncertainty in confidence.",
)

_FORBIDDEN_EXTRACTIONS: tuple[str, ...] = (
    "definitions without causal process",
    "terminology or glossary entries",
    "marketing or promotional copy",
    "book or chapter introductions",
    "chapter summaries",
    "generic examples without explained mechanism",
    "isolated therapeutic slogans",
)

_RELEVANCE_SCHEMA_LINES: tuple[str, ...] = (
    '    "is_relevant": true,',
    '    "relevance_score": 0.0,',
    '    "knowledge_kind": "therapeutic_mechanism",',
    '    "reasoning": "string",',
    '    "evidence_span": "string",',
    '    "skip_reason": "",',
    '    "suggested_mechanisms": ["string"],',
    '    "should_extract": true',
)

_EXTRACTION_SCHEMA_LINES: tuple[str, ...] = (
    '    "mechanism_name": "string",',
    '    "mechanism_description": "string",',
    '    "why_this_is_a_mechanism": "string",',
    '    "causal_process": "string",',
    '    "evidence": "string",',
    '    "ontology_status": "known",',
    '    "confidence": 0.0,',
    '    "therapeutic_function": "string",',
    '    "psychological_function": "string",',
    '    "symbolic_elements": ["string"],',
    '    "candidate_targets": ["string"],',
    '    "generation_rules": ["string"],',
    '    "voice_rules": ["string"],',
    '    "repetition_rules": ["string"],',
    '    "pause_rules": ["string"],',
    '    "contraindications": ["string"]',
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
    *,
    ontology_context: OntologyContext | None = None,
) -> str:
    """Build a deterministic ontology-guided extraction prompt for one raw source segment."""
    context = ontology_context or load_ontology_context()
    rules = "\n".join(f"- {rule}" for rule in _PROMPT_RULES)
    forbidden = "\n".join(f"- {item}" for item in _FORBIDDEN_EXTRACTIONS)
    required_fields = "\n".join(f"- {field}" for field in REQUIRED_EXTRACTION_FIELDS)
    semantic_fields = "\n".join(f"- {field}" for field in REQUIRED_SEMANTIC_KNOWLEDGE_FIELDS)
    relevance_fields = "\n".join(f"- {field}" for field in REQUIRED_RELEVANCE_FIELDS)
    knowledge_kinds = "\n".join(f"- {kind}" for kind in KNOWLEDGE_KIND_OPTIONS)
    ontology_statuses = "\n".join(f"- {status}" for status in sorted(SUPPORTED_ONTOLOGY_STATUSES))
    mechanism_catalog = format_ontology_mechanism_catalog(context)
    json_schema = (
        "{\n"
        '  "relevance_decision": {\n'
        + "\n".join(_RELEVANCE_SCHEMA_LINES)
        + "\n  },\n"
        '  "extraction": {\n'
        + "\n".join(_EXTRACTION_SCHEMA_LINES)
        + "\n  }\n"
        "}"
    )

    return (
        "You are a psychotherapy researcher building reusable psychological knowledge for NIROS.\n"
        "Your job is to identify therapeutic knowledge, not interesting sentences.\n\n"
        "For every segment, decide internally:\n"
        "1. Does the passage explain a psychological mechanism with maintaining logic?\n"
        "2. Does it explain a causal relationship that a therapist could reuse?\n"
        "3. Does it explain an intervention principle with a change process?\n"
        "4. Does it strengthen an existing ontology mechanism with new evidence or nuance?\n"
        "5. Does it introduce a mechanism not represented in the ontology?\n\n"
        "Strict rules:\n"
        f"{rules}\n\n"
        "Explicitly forbidden extractions:\n"
        f"{forbidden}\n\n"
        "Master ontology reference mechanisms (incomplete; unknown mechanisms are valid):\n"
        f"{mechanism_catalog or '- (no mechanisms loaded)'}\n\n"
        "Allowed ontology_status values:\n"
        f"{ontology_statuses}\n\n"
        "Relevance decision fields:\n"
        f"{relevance_fields}\n\n"
        "Allowed knowledge_kind values:\n"
        f"{knowledge_kinds}\n\n"
        "Required semantic knowledge fields (only when should_extract is true):\n"
        f"{semantic_fields}\n\n"
        "Required extraction fields (only when should_extract is true):\n"
        f"{required_fields}\n\n"
        "If should_extract is false:\n"
        "- set extraction to null\n"
        "- explain why the chunk was skipped in reasoning and skip_reason\n"
        "- include the most relevant quoted span in evidence_span when possible\n\n"
        "Source metadata:\n"
        f"{_format_source_metadata(raw_source)}\n\n"
        "Source segment:\n"
        f"{_format_segment_content(raw_segment)}\n\n"
        "Respond with valid JSON only. Do not include markdown fences or commentary.\n"
        "Use this JSON shape:\n"
        f"{json_schema}\n"
        "relevance_score and confidence must be numbers between 0.0 and 1.0."
    )
