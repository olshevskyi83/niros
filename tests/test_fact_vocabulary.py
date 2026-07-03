from niros.semantic_interpreter.fact_vocabulary import (
    AGENCY,
    ATTACHMENT,
    AVOIDANT,
    EMOTION,
    FEAR_OF_REJECTION,
    IDENTITY,
    LOW,
    REACTION_TO_CRITICISM,
    RELATIONSHIP,
    SELF,
    SELF_EFFICACY,
    STRONG,
    UNCLEAR,
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)
from niros.semantic_interpreter.facts import SemanticFact


def test_known_category_in_vocabulary():
    assert SELF in VALID_CATEGORIES
    assert AGENCY in VALID_CATEGORIES
    assert EMOTION in VALID_CATEGORIES
    assert RELATIONSHIP in VALID_CATEGORIES


def test_known_attribute_in_vocabulary():
    assert IDENTITY in VALID_ATTRIBUTES
    assert SELF_EFFICACY in VALID_ATTRIBUTES
    assert FEAR_OF_REJECTION in VALID_ATTRIBUTES
    assert ATTACHMENT in VALID_ATTRIBUTES


def test_known_value_in_vocabulary():
    assert UNCLEAR in VALID_VALUES
    assert LOW in VALID_VALUES
    assert STRONG in VALID_VALUES
    assert AVOIDANT in VALID_VALUES


def test_valid_fact():
    fact = SemanticFact(
        category=SELF,
        attribute=IDENTITY,
        value=UNCLEAR,
    )

    assert fact.is_valid() is True


def test_invalid_category():
    fact = SemanticFact(
        category="experience",
        attribute=IDENTITY,
        value=UNCLEAR,
    )

    assert fact.is_valid() is False


def test_invalid_attribute():
    fact = SemanticFact(
        category=SELF,
        attribute="sleep_distress",
        value=UNCLEAR,
    )

    assert fact.is_valid() is False


def test_invalid_value():
    fact = SemanticFact(
        category=RELATIONSHIP,
        attribute=FEAR_OF_REJECTION,
        value="severe",
    )

    assert fact.is_valid() is False


def test_mock_facts_are_valid():
    fact = SemanticFact(
        category=AGENCY,
        attribute=SELF_EFFICACY,
        value=LOW,
    )

    assert fact.is_valid() is True


def test_emotion_reaction_fact_is_valid():
    fact = SemanticFact(
        category=EMOTION,
        attribute=REACTION_TO_CRITICISM,
        value=STRONG,
    )

    assert fact.is_valid() is True
