from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_interpreter.factory import get_semantic_interpreter


def test_semantic_fact_creation():
    fact = SemanticFact(
        category="self",
        attribute="identity",
        value="unclear",
        confidence=1.0,
        evidence="I do not really know who I am.",
    )

    assert fact.category == "self"
    assert fact.attribute == "identity"
    assert fact.value == "unclear"
    assert fact.confidence == 1.0
    assert fact.evidence == "I do not really know who I am."


def test_semantic_interpretation_result_contains_facts():
    result = SemanticInterpretationResult(
        raw_text="example",
        canonical_statements=["I do not really know who I am."],
        facts=[
            SemanticFact(
                category="self",
                attribute="identity",
                value="unclear",
            )
        ],
    )

    assert len(result.facts) == 1
    assert result.facts[0].attribute == "identity"


def test_mock_semantic_interpreter_populates_identity_fact():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("я не розумію себе")

    assert result.canonical_statements == ["I do not really know who I am."]
    assert len(result.facts) == 1
    assert result.facts[0] == SemanticFact(
        category="self",
        attribute="identity",
        value="unclear",
        confidence=1.0,
        evidence="I do not really know who I am.",
    )
    assert result.facts[0].is_valid() is True


def test_mock_semantic_interpreter_populates_agency_fact():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("я думаю що нічого не зможу")

    assert result.canonical_statements == ["I probably cannot do this."]
    assert result.facts[0] == SemanticFact(
        category="agency",
        attribute="self_efficacy",
        value="low",
        confidence=1.0,
        evidence="I probably cannot do this.",
    )


def test_mock_semantic_interpreter_unmapped_input_has_no_facts():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("unmapped phrase")

    assert result.canonical_statements == ["unmapped phrase"]
    assert result.facts == []
