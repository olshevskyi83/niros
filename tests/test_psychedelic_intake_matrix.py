from pathlib import Path

import yaml

from niros.knowledge import PatternLoader
from niros.semantic_interpreter.fact_vocabulary import (
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)
from niros.semantic_interpreter.facts import SemanticFact

MATRIX_PATH = Path(__file__).resolve().parent.parent / "evaluation" / "psychedelic_intake_matrix.yaml"
SUPPORTED_LANGUAGES = frozenset({"en", "uk", "ru", "es"})
MIN_CASES_PER_LANGUAGE = 20
MIN_CASES_WITH_NEGATIVE_PATTERNS = 20

REQUIRED_CASE_FIELDS = frozenset(
    {
        "id",
        "language",
        "input",
        "expected_semantic_facts",
        "expected_patterns",
        "negative_expected_patterns",
    }
)
REQUIRED_FACT_FIELDS = frozenset({"category", "attribute", "value"})

DOMAIN_PATTERNS = frozenset(
    {
        "low_mood_signal",
        "depressed_mood_signal",
        "anhedonia_signal",
        "hopelessness_signal",
        "emotional_heaviness",
        "loss_of_meaning",
        "generalized_fear",
        "panic_reactivity",
        "fear_of_losing_control",
        "fear_of_death",
        "chronic_stress_signal",
        "somatic_anxiety",
        "hypervigilance",
        "intrusive_memories",
        "avoidance_of_triggers",
        "emotional_numbing",
        "startle_sensitivity",
        "dissociation_signal",
        "shame_sensitivity",
        "harsh_self_criticism",
        "self_worth_instability",
        "guilt_burden",
        "unworthiness_signal",
        "rumination",
        "obsessive_thinking_loop",
        "mental_overcontrol",
        "inability_to_let_go",
        "chronic_pain_burden",
        "fibromyalgia_signal",
        "fatigue_burden",
        "body_sensitivity",
        "pain_fear_cycle",
        "symptom_unpredictability",
        "sleep_disruption",
        "stuttering_signal",
        "speech_anxiety",
        "fear_of_speaking",
        "communication_avoidance",
        "shame_about_speech",
        "self_expression_block",
        "psychedelic_anxiety",
        "fear_of_bad_trip",
        "surrender_difficulty",
        "control_resistance",
        "fear_of_body_sensations",
        "trust_in_facilitator_difficulty",
        "integration_need",
        "spiritual_openness",
        "spiritual_resistance",
        "meaning_seeking",
        "mystical_expectation",
        "existential_fear",
    }
)


def load_matrix() -> dict:
    with MATRIX_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_known_pattern_ids() -> frozenset[str]:
    loader = PatternLoader()
    return frozenset(pattern.canonical_id for pattern in loader.load_all())


def test_matrix_file_exists_and_is_valid_yaml():
    matrix = load_matrix()

    assert isinstance(matrix, dict)
    assert matrix["version"] == 1
    assert isinstance(matrix["cases"], list)
    assert matrix["cases"]


def test_case_ids_are_unique():
    matrix = load_matrix()
    case_ids = [case["id"] for case in matrix["cases"]]

    assert len(case_ids) == len(set(case_ids))


def test_each_language_has_at_least_twenty_cases():
    matrix = load_matrix()
    counts = {language: 0 for language in SUPPORTED_LANGUAGES}

    for case in matrix["cases"]:
        counts[case["language"]] += 1

    for language, count in counts.items():
        assert count >= MIN_CASES_PER_LANGUAGE, f"{language} has {count} cases"


def test_supported_languages_only():
    matrix = load_matrix()

    for case in matrix["cases"]:
        assert case["language"] in SUPPORTED_LANGUAGES


def test_cases_have_required_fields():
    matrix = load_matrix()

    for case in matrix["cases"]:
        assert REQUIRED_CASE_FIELDS.issubset(case)
        assert case["input"].strip()
        assert case["expected_semantic_facts"]
        assert case["expected_patterns"]
        assert isinstance(case["negative_expected_patterns"], list)


def test_expected_semantic_facts_use_valid_vocabulary():
    matrix = load_matrix()

    for case in matrix["cases"]:
        for expected in case["expected_semantic_facts"]:
            assert REQUIRED_FACT_FIELDS.issubset(expected)
            fact = SemanticFact(
                category=expected["category"],
                attribute=expected["attribute"],
                value=expected["value"],
            )
            assert fact.is_valid() is True
            assert expected["category"] in VALID_CATEGORIES
            assert expected["attribute"] in VALID_ATTRIBUTES
            assert expected["value"] in VALID_VALUES


def test_expected_patterns_exist_in_knowledge_base():
    matrix = load_matrix()
    known_patterns = load_known_pattern_ids()

    for case in matrix["cases"]:
        for pattern_id in case["expected_patterns"]:
            assert pattern_id in known_patterns, f"unknown expected pattern: {pattern_id}"
        for pattern_id in case["negative_expected_patterns"]:
            assert pattern_id in known_patterns, f"unknown negative pattern: {pattern_id}"


def test_at_least_twenty_cases_have_negative_expected_patterns():
    matrix = load_matrix()
    with_negatives = [
        case for case in matrix["cases"] if case["negative_expected_patterns"]
    ]

    assert len(with_negatives) >= MIN_CASES_WITH_NEGATIVE_PATTERNS


def test_domain_patterns_are_represented():
    matrix = load_matrix()
    represented = {
        pattern_id
        for case in matrix["cases"]
        for pattern_id in case["expected_patterns"]
    }

    missing = DOMAIN_PATTERNS - represented
    assert not missing, f"missing domain patterns: {sorted(missing)}"
