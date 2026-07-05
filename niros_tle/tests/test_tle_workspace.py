"""Validate TLE workspace structure and seed pattern schema compatibility."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from niros.therapeutic_pattern import (
    REQUIRED_FIELDS,
    TherapeuticPatternLibrary,
    TherapeuticPatternValidationError,
)

TLE_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_CORPUS_FOLDERS = (
    "erickson",
    "act",
    "ifs",
    "cft",
    "narrative",
    "motivational_interviewing",
    "maria_sabina",
    "shipibo",
    "quechua",
)


def test_niros_tle_directory_exists():
    assert TLE_ROOT.is_dir()
    assert TLE_ROOT.name == "niros_tle"


@pytest.mark.parametrize("folder", EXPECTED_CORPUS_FOLDERS)
def test_corpus_folders_exist(folder: str):
    assert (TLE_ROOT / "corpus" / folder).is_dir()


def test_corpus_sources_json_exists():
    path = TLE_ROOT / "metadata" / "corpus_sources.json"
    assert path.is_file()


def test_corpus_sources_includes_all_expected_source_ids():
    path = TLE_ROOT / "metadata" / "corpus_sources.json"
    sources = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(sources, list)

    source_ids = {entry["id"] for entry in sources}
    missing = set(EXPECTED_CORPUS_FOLDERS) - source_ids
    assert not missing, f"Missing corpus source ids: {sorted(missing)}"


def test_seed_patterns_json_exists():
    path = TLE_ROOT / "patterns" / "seed_patterns.json"
    assert path.is_file()


def test_seed_patterns_are_valid_json():
    path = TLE_ROOT / "patterns" / "seed_patterns.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payloads, list)
    assert payloads


def test_seed_pattern_ids_are_unique():
    path = TLE_ROOT / "patterns" / "seed_patterns.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    ids = [entry["id"] for entry in payloads]
    assert len(ids) == len(set(ids))


def test_seed_patterns_include_required_therapeutic_pattern_fields():
    path = TLE_ROOT / "patterns" / "seed_patterns.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))

    for payload in payloads:
        missing = [field_name for field_name in REQUIRED_FIELDS if field_name not in payload]
        assert not missing, f"Pattern {payload.get('id', '?')} missing fields: {missing}"


def test_seed_patterns_validate_against_therapeutic_pattern_schema():
    path = TLE_ROOT / "patterns" / "seed_patterns.json"
    library = TherapeuticPatternLibrary.load_json(path)
    assert len(library.patterns) >= 5


def test_seed_patterns_reject_duplicate_ids():
    path = TLE_ROOT / "patterns" / "seed_patterns.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    duplicate_payloads = list(payloads) + [payloads[0]]

    with pytest.raises(TherapeuticPatternValidationError, match="Duplicate"):
        TherapeuticPatternLibrary.from_dicts(duplicate_payloads)


def test_exports_directory_exists():
    assert (TLE_ROOT / "exports").is_dir()


def test_embeddings_directory_exists():
    assert (TLE_ROOT / "embeddings").is_dir()
