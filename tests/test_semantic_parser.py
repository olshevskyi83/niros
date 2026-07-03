import json

from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_interpreter.parser import (
    parse_semantic_extraction_response,
    payload_to_semantic_result,
)


def test_valid_json_returns_parsed_facts():
    raw = json.dumps(
        {
            "facts": [
                {
                    "category": "self",
                    "attribute": "identity",
                    "value": "unclear",
                    "confidence": 0.95,
                    "evidence": "I do not really know who I am.",
                }
            ],
            "detected_language": "en",
            "confidence": 0.95,
            "warnings": [],
        }
    )

    payload = parse_semantic_extraction_response(raw)

    assert len(payload.facts) == 1
    assert payload.facts[0].category == "self"
    assert payload.facts[0].attribute == "identity"
    assert payload.facts[0].value == "unclear"
    assert payload.detected_language == "en"
    assert payload.confidence == 0.95
    assert payload.warnings == []


def test_invalid_json_returns_empty_facts_and_invalid_json_warning():
    payload = parse_semantic_extraction_response("{not valid json")

    assert payload.facts == []
    assert payload.warnings == ["invalid_json"]


def test_schema_invalid_json_returns_empty_facts_and_schema_validation_failed_warning():
    raw = json.dumps(
        {
            "facts": [
                {
                    "category": "experience",
                    "attribute": "identity",
                    "value": "unclear",
                }
            ],
            "detected_language": "en",
        }
    )

    payload = parse_semantic_extraction_response(raw)

    assert payload.facts == []
    assert payload.warnings == ["schema_validation_failed"]


def test_empty_response_returns_empty_facts_and_empty_response_warning():
    payload = parse_semantic_extraction_response("   ")

    assert payload.facts == []
    assert payload.warnings == ["empty_response"]


def test_valid_payload_converts_to_semantic_interpretation_result():
    raw = json.dumps(
        {
            "facts": [
                {
                    "category": "self",
                    "attribute": "identity",
                    "value": "unclear",
                    "confidence": 0.95,
                    "evidence": "I do not really know who I am.",
                }
            ],
            "detected_language": "en",
            "confidence": 0.95,
            "warnings": [],
        }
    )
    payload = parse_semantic_extraction_response(raw)

    result = payload_to_semantic_result(payload)

    assert result.facts == [
        SemanticFact(
            category="self",
            attribute="identity",
            value="unclear",
            confidence=0.95,
            evidence="I do not really know who I am.",
        )
    ]
    assert result.detected_language == "en"
    assert result.confidence == 0.95
    assert result.warnings == []


def test_canonical_statements_remains_empty_list():
    raw = json.dumps(
        {
            "facts": [
                {
                    "category": "self",
                    "attribute": "identity",
                    "value": "unclear",
                    "confidence": 0.95,
                    "evidence": "I do not really know who I am.",
                }
            ],
            "detected_language": "en",
        }
    )
    payload = parse_semantic_extraction_response(raw)

    result = payload_to_semantic_result(payload)

    assert result.canonical_statements == []
