from niros.models import SupportedLanguage
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_pattern_mapping import patterns_for_semantic_fact, semantic_fact_pattern_matches


def test_patterns_for_reported_distress_fact():
    fact = SemanticFact(
        category="emotion",
        attribute="reported_distress",
        value="elevated",
        evidence="я завжди у стресі",
    )

    assert "emotional_distress_signal" in patterns_for_semantic_fact(fact)


def test_patterns_for_sleep_nightmares_fact():
    fact = SemanticFact(
        category="sleep",
        attribute="nightmares",
        value="present",
        evidence="мені сняться погані сни",
    )

    patterns = patterns_for_semantic_fact(fact)
    assert "nightmare_disturbance" in patterns
    assert "sleep_disruption" in patterns


def test_semantic_fact_pattern_matches_creates_unique_patterns():
    facts = [
        SemanticFact(
            category="self",
            attribute="perceived_helplessness",
            value="present",
            confidence=0.88,
            evidence="мені не допомагає нічого",
        )
    ]

    matches = semantic_fact_pattern_matches(facts)

    assert len(matches) == 2
    assert {match.canonical_id for match in matches} == {
        "hopelessness_signal",
        "emotional_distress_signal",
    }
    assert matches[0].matched_text == "мені не допомагає нічого"
