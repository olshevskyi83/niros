from __future__ import annotations

import json

from pydantic import ValidationError

from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.schema import SemanticExtractionPayload


def _empty_payload(warning: str) -> SemanticExtractionPayload:
    return SemanticExtractionPayload(facts=[], warnings=[warning])


def parse_semantic_extraction_response(raw_text: str) -> SemanticExtractionPayload:
    if not raw_text.strip():
        return _empty_payload("empty_response")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return _empty_payload("invalid_json")

    if not isinstance(data, dict):
        return _empty_payload("schema_validation_failed")

    try:
        return SemanticExtractionPayload.model_validate(data)
    except ValidationError:
        return _empty_payload("schema_validation_failed")


def payload_to_semantic_result(payload: SemanticExtractionPayload) -> SemanticInterpretationResult:
    return SemanticInterpretationResult(
        raw_text="",
        canonical_statements=[],
        facts=[fact.to_semantic_fact() for fact in payload.facts],
        detected_language=payload.detected_language,
        confidence=payload.confidence,
        warnings=list(payload.warnings),
    )
