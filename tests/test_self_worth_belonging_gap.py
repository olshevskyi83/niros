from niros.adaptive_assessment_selector import (
    SELF_DOMAIN_SHORT,
    select_assessment_modules,
)
from niros.assessment_domain_map import build_assessment_domain_map
from niros.evidence import statement_to_evidence
from niros.models import SupportedLanguage
from niros.patterns import PatternTagger
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_pattern_mapping import patterns_for_semantic_fact
from niros.statements import Statement


def _detect(raw_text: str, language: SupportedLanguage = SupportedLanguage.UKRAINIAN) -> set[str]:
    statement = Statement(
        session_id="session-self-worth-gap",
        text=raw_text,
        sequence=0,
        language=language,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def _fact(category: str, attribute: str, value: str, evidence: str) -> SemanticFact:
    return SemanticFact(
        category=category,
        attribute=attribute,
        value=value,
        confidence=0.9,
        evidence=evidence,
    )


def test_uk_unworthiness_phrase_detects_core_patterns():
    detected = _detect("я відчуваю себе непотрібним")

    assert "unworthiness_signal" in detected
    assert "self_worth_instability" in detected


def test_uk_nobody_needs_me_detects_social_disconnection():
    detected = _detect("я нікому не потрібен")

    assert "social_disconnection_signal" in detected


def test_uk_nobody_values_me_detects_rejection_sensitivity():
    detected = _detect("мене ніхто не цінує")

    assert detected.intersection({"social_disconnection_signal", "rejection_sensitivity"})


def test_en_i_feel_useless_detects_unworthiness():
    detected = _detect("I feel useless", SupportedLanguage.ENGLISH)

    assert "unworthiness_signal" in detected


def test_en_nobody_needs_me_detects_social_disconnection():
    detected = _detect("nobody needs me", SupportedLanguage.ENGLISH)

    assert "social_disconnection_signal" in detected


def test_en_people_do_not_value_me_detects_rejection_sensitivity():
    detected = _detect("people do not value me", SupportedLanguage.ENGLISH)

    assert detected.intersection({"social_disconnection_signal", "rejection_sensitivity"})


def test_ru_feel_unnecessary_detects_unworthiness():
    detected = _detect("я чувствую себя ненужным", SupportedLanguage.RUSSIAN)

    assert "unworthiness_signal" in detected
    assert "self_worth_instability" in detected


def test_ru_nobody_needs_me_detects_social_disconnection():
    detected = _detect("я никому не нужен", SupportedLanguage.RUSSIAN)

    assert "social_disconnection_signal" in detected


def test_es_feel_useless_detects_unworthiness():
    detected = _detect("me siento inútil", SupportedLanguage.SPANISH)

    assert "unworthiness_signal" in detected


def test_es_nobody_needs_me_detects_social_disconnection():
    detected = _detect("siento que nadie me necesita", SupportedLanguage.SPANISH)

    assert "social_disconnection_signal" in detected


def test_neutral_statement_does_not_false_positive():
    detected = _detect("сьогодні я пішов у магазин за хлібом")

    assert not detected.intersection(
        {
            "unworthiness_signal",
            "self_worth_instability",
            "social_disconnection_signal",
            "rejection_sensitivity",
        }
    )


def test_semantic_facts_are_vocabulary_valid():
    facts = [
        _fact("self", "unworthiness", "present", "я відчуваю себе непотрібним"),
        _fact("self", "self_worth", "low", "я відчуваю себе непотрібним"),
        _fact("social", "belonging", "low", "я нікому не потрібен"),
        _fact("social", "feeling_unwanted", "present", "я нікому не потрібен"),
        _fact("emotion", "reported_low_mood", "present", "почуваюся зайвим"),
    ]

    for fact in facts:
        assert fact.is_valid()
        assert patterns_for_semantic_fact(fact)


def test_unworthiness_semantic_facts_map_to_expected_patterns():
    facts = [
        _fact("self", "unworthiness", "present", "I feel useless"),
        _fact("social", "feeling_unwanted", "present", "I feel unwanted"),
    ]
    detected = set()
    for fact in facts:
        detected.update(patterns_for_semantic_fact(fact))

    assert "unworthiness_signal" in detected
    assert "self_worth_instability" in detected
    assert detected.intersection({"social_disconnection_signal", "rejection_sensitivity"})


def test_reported_low_mood_with_unworthiness_can_add_low_mood_signal():
    facts = [
        _fact("self", "unworthiness", "present", "I feel worthless"),
        _fact("emotion", "reported_low_mood", "present", "I feel worthless"),
    ]
    from niros.semantic_pattern_mapping import semantic_fact_pattern_matches

    detected = {match.canonical_id for match in semantic_fact_pattern_matches(facts)}

    assert "low_mood_signal" in detected
    assert "unworthiness_signal" in detected


def test_adaptive_selector_chooses_self_domain_for_unworthiness_intake():
    from niros.adaptive_assessment_selector import SELF_DOMAIN_SHORT, select_assessment_modules

    selection = select_assessment_modules(
        presenting_problem={"main_problem": "я відчуваю себе непотрібним"},
        detected_patterns=["unworthiness_signal", "self_worth_instability"],
        assessment_domain_map=build_assessment_domain_map(),
    )

    assert SELF_DOMAIN_SHORT in selection.selected_modules
