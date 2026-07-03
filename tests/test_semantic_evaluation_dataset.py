from pathlib import Path

import yaml

from niros.semantic_interpreter.fact_vocabulary import (
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)
from niros.semantic_interpreter.facts import SemanticFact

DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "evaluation" / "semantic_cases" / "semantic_cases_v1.yaml"
)
SUPPORTED_LANGUAGES = frozenset({"en", "uk", "ru", "es"})
REQUIRED_CASE_FIELDS = frozenset({"id", "language", "input", "expected_facts"})
REQUIRED_FACT_FIELDS = frozenset({"category", "attribute", "value"})


def load_semantic_evaluation_dataset() -> dict:
    with DATASET_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_dataset_file_exists_and_is_valid_yaml():
    dataset = load_semantic_evaluation_dataset()

    assert isinstance(dataset, dict)
    assert dataset["version"] == 1
    assert isinstance(dataset["cases"], list)


def test_dataset_has_forty_cases():
    dataset = load_semantic_evaluation_dataset()

    assert len(dataset["cases"]) == 40


def test_case_ids_are_unique():
    dataset = load_semantic_evaluation_dataset()
    case_ids = [case["id"] for case in dataset["cases"]]

    assert len(case_ids) == len(set(case_ids))


def test_each_language_has_ten_cases():
    dataset = load_semantic_evaluation_dataset()
    counts = {language: 0 for language in SUPPORTED_LANGUAGES}

    for case in dataset["cases"]:
        counts[case["language"]] += 1

    assert counts == {"en": 10, "uk": 10, "ru": 10, "es": 10}


def test_supported_languages_only():
    dataset = load_semantic_evaluation_dataset()

    for case in dataset["cases"]:
        assert case["language"] in SUPPORTED_LANGUAGES


def test_cases_have_required_fields():
    dataset = load_semantic_evaluation_dataset()

    for case in dataset["cases"]:
        assert REQUIRED_CASE_FIELDS.issubset(case)
        assert case["input"].strip()
        assert case["expected_facts"]


def test_expected_facts_use_valid_vocabulary():
    dataset = load_semantic_evaluation_dataset()

    for case in dataset["cases"]:
        for expected in case["expected_facts"]:
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


def test_dataset_covers_required_domains():
    dataset = load_semantic_evaluation_dataset()
    attributes = {
        expected["attribute"]
        for case in dataset["cases"]
        for expected in case["expected_facts"]
    }

    assert "conflict" in attributes
    assert "fear_of_rejection" in attributes
    assert "identity" in attributes
    assert "self_worth" in attributes
    assert "trust" in attributes
    assert "boundary_setting" in attributes
    assert "reaction_to_criticism" in attributes
    assert "self_efficacy" in attributes
    assert "attachment" in attributes
