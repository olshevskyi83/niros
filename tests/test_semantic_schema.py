import pytest
from pydantic import ValidationError

from niros.semantic_interpreter.fact_vocabulary import (
    IDENTITY,
    SELF,
    UNCLEAR,
)
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_interpreter.schema import SemanticExtractionPayload, SemanticFactPayload


def test_valid_payload_parses():
    payload = SemanticExtractionPayload(
        facts=[
            SemanticFactPayload(
                category="self",
                attribute="identity",
                value="unclear",
                confidence=0.95,
                evidence="I do not really know who I am.",
            )
        ],
        detected_language="en",
        confidence=0.95,
        warnings=[],
    )

    assert len(payload.facts) == 1
    assert payload.facts[0].category == "self"
    assert payload.detected_language == "en"
    assert payload.confidence == 0.95
    assert payload.warnings == []


def test_invalid_category_fails():
    with pytest.raises(ValidationError):
        SemanticFactPayload(
            category="experience",
            attribute="identity",
            value="unclear",
        )


def test_invalid_attribute_fails():
    with pytest.raises(ValidationError):
        SemanticFactPayload(
            category="self",
            attribute="sleep_distress",
            value="unclear",
        )


def test_invalid_value_fails():
    with pytest.raises(ValidationError):
        SemanticFactPayload(
            category="self",
            attribute="identity",
            value="severe",
        )


def test_invalid_confidence_below_zero_fails():
    with pytest.raises(ValidationError):
        SemanticFactPayload(
            category="self",
            attribute="identity",
            value="unclear",
            confidence=-0.1,
        )


def test_invalid_confidence_above_one_fails():
    with pytest.raises(ValidationError):
        SemanticFactPayload(
            category="self",
            attribute="identity",
            value="unclear",
            confidence=1.1,
        )


def test_conversion_to_semantic_fact_works():
    payload = SemanticFactPayload(
        category=SELF,
        attribute=IDENTITY,
        value=UNCLEAR,
        confidence=0.95,
        evidence="I do not really know who I am.",
    )

    fact = payload.to_semantic_fact()

    assert fact == SemanticFact(
        category=SELF,
        attribute=IDENTITY,
        value=UNCLEAR,
        confidence=0.95,
        evidence="I do not really know who I am.",
    )
    assert fact.is_valid() is True
