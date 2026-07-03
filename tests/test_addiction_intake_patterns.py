import pytest

from niros.evidence import statement_to_evidence
from niros.models import SupportedLanguage
from niros.patterns import PatternTagger
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_pattern_mapping import patterns_for_semantic_fact, semantic_fact_pattern_matches
from niros.statements import Statement


def _detect(raw_text: str, language: SupportedLanguage) -> set[str]:
    statement = Statement(
        session_id="session-addiction-001",
        text=raw_text,
        sequence=0,
        language=language,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def test_uk_drug_problem_detects_substance_patterns():
    detected = _detect("у мене проблема з наркотиками", SupportedLanguage.UKRAINIAN)

    assert detected.intersection({"drug_use_concern", "substance_use_pattern"})


def test_uk_preoccupation_detects_compulsive_or_preoccupation_patterns():
    detected = _detect(
        "мене не цікавить нічого крім наркотиків",
        SupportedLanguage.UKRAINIAN,
    )

    assert detected.intersection({"substance_preoccupation", "compulsive_use_signal"})


def test_uk_cannot_overcome_addiction_detects_control_patterns():
    detected = _detect("я не можу побороти залежність", SupportedLanguage.UKRAINIAN)

    assert detected.intersection(
        {"addiction_concern_signal", "loss_of_control_over_use"}
    )


def test_uk_wants_to_quit_habit_detects_recovery_or_change_patterns():
    detected = _detect("я хочу позбутись цієї звички", SupportedLanguage.UKRAINIAN)

    assert detected.intersection({"recovery_goal_signal", "desire_for_change"})


@pytest.mark.parametrize(
    ("text", "language", "expected_any"),
    [
        ("I have a problem with drugs", SupportedLanguage.ENGLISH, {"drug_use_concern", "substance_use_pattern"}),
        ("nothing interests me except drugs", SupportedLanguage.ENGLISH, {"substance_preoccupation", "compulsive_use_signal"}),
        ("I cannot beat this addiction", SupportedLanguage.ENGLISH, {"addiction_concern_signal", "loss_of_control_over_use"}),
        ("I want to get rid of this habit", SupportedLanguage.ENGLISH, {"recovery_goal_signal", "desire_for_change"}),
        ("у меня проблема с наркотиками", SupportedLanguage.RUSSIAN, {"drug_use_concern", "substance_use_pattern"}),
        ("меня не интересует ничего кроме наркотиков", SupportedLanguage.RUSSIAN, {"substance_preoccupation", "compulsive_use_signal"}),
        ("я не могу побороть зависимость", SupportedLanguage.RUSSIAN, {"addiction_concern_signal", "loss_of_control_over_use"}),
        ("я хочу избавиться от этой привычки", SupportedLanguage.RUSSIAN, {"recovery_goal_signal", "desire_for_change"}),
        ("tengo un problema con las drogas", SupportedLanguage.SPANISH, {"drug_use_concern", "substance_use_pattern"}),
        ("no me interesa nada excepto las drogas", SupportedLanguage.SPANISH, {"substance_preoccupation", "compulsive_use_signal"}),
        ("no puedo vencer esta adicción", SupportedLanguage.SPANISH, {"addiction_concern_signal", "loss_of_control_over_use"}),
        ("quiero deshacerme de este hábito", SupportedLanguage.SPANISH, {"recovery_goal_signal", "desire_for_change"}),
    ],
)
def test_multilingual_addiction_examples(text, language, expected_any):
    detected = _detect(text, language)
    assert detected.intersection(expected_any)


def test_neutral_sentence_does_not_false_positive():
    neutral_cases = [
        ("I like coffee in the morning.", SupportedLanguage.ENGLISH),
        ("Сьогодні я працюю над проектом.", SupportedLanguage.UKRAINIAN),
        ("Me gusta caminar por la mañana.", SupportedLanguage.SPANISH),
        ("Сегодня хорошая погода.", SupportedLanguage.RUSSIAN),
    ]
    addiction_patterns = {
        "substance_use_pattern",
        "drug_use_concern",
        "addiction_concern_signal",
        "compulsive_use_signal",
        "loss_of_control_over_use",
        "substance_preoccupation",
        "recovery_goal_signal",
    }

    for text, language in neutral_cases:
        detected = _detect(text, language)
        assert not detected.intersection(addiction_patterns)


def test_semantic_substance_facts_map_to_patterns():
    fact = SemanticFact(
        category="substance",
        attribute="drug_use_concern",
        value="present",
        evidence="problem with drugs",
        confidence=0.9,
    )

    assert "drug_use_concern" in patterns_for_semantic_fact(fact)
    matches = semantic_fact_pattern_matches([fact])
    assert {match.canonical_id for match in matches}.intersection({"drug_use_concern", "substance_use_pattern"})
