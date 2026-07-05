"""Tests for TLE pattern import/export contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from niros.therapeutic_pattern import TherapeuticPatternLibrary
from niros_tle.pattern_contract import (
    DEFAULT_SEED_PATTERNS_PATH,
    TLEPatternRecord,
    TLEPatternValidationError,
    export_core_patterns,
    load_tle_patterns,
    to_core_therapeutic_pattern,
    validate_tle_pattern_record,
)

TLE_ROOT = Path(__file__).resolve().parent.parent
NIROS_ROOT = TLE_ROOT.parent
VALID_TLE_PATTERN = {
    "id": "test_pattern_loop",
    "name": "Test Pattern Loop",
    "psychological_function": ["regulation"],
    "good_for": ["anxiety"],
    "avoid_if": ["psychosis_risk"],
    "language_style": ["gentle"],
    "rhythm": "slow",
    "semantic_cluster": ["safety"],
    "spiritual_compatibility": ["secular"],
    "requires_symbols": [],
    "forbidden_symbols": [],
    "intensity": "low",
    "directness": "low",
    "repetition_level": "low",
    "safety_notes": ["Keep language non-directive"],
    "source_family": ["act"],
    "source_confidence": "medium",
    "extraction_method": "manual_seed",
    "evidence_refs": [
        {
            "source_family": "act",
            "reference_type": "conceptual",
            "note": "Pattern derived from general ACT acceptance/process language concepts.",
        }
    ],
    "notes": "Test fixture only.",
}


def test_valid_tle_pattern_passes_validation():
    validate_tle_pattern_record(VALID_TLE_PATTERN)
    record = TLEPatternRecord.from_dict(VALID_TLE_PATTERN)
    assert record.id == "test_pattern_loop"


def test_missing_required_field_fails_validation():
    payload = dict(VALID_TLE_PATTERN)
    del payload["source_confidence"]
    with pytest.raises(TLEPatternValidationError, match="source_confidence"):
        validate_tle_pattern_record(payload)


def test_invalid_source_confidence_fails_validation():
    payload = dict(VALID_TLE_PATTERN, source_confidence="very_high")
    with pytest.raises(TLEPatternValidationError, match="source_confidence"):
        validate_tle_pattern_record(payload)


def test_invalid_extraction_method_fails_validation():
    payload = dict(VALID_TLE_PATTERN, extraction_method="openai_analysis")
    with pytest.raises(TLEPatternValidationError, match="extraction_method"):
        validate_tle_pattern_record(payload)


def test_evidence_refs_reject_long_copied_text():
    payload = dict(VALID_TLE_PATTERN)
    payload["evidence_refs"] = [
        {
            "source_family": "act",
            "reference_type": "conceptual",
            "note": "x" * 400,
        }
    ]
    with pytest.raises(TLEPatternValidationError, match="exceeds maximum length"):
        validate_tle_pattern_record(payload)


def test_final_generated_text_field_is_rejected():
    payload = dict(VALID_TLE_PATTERN, therapeutic_text="You are safe and whole.")
    with pytest.raises(TLEPatternValidationError, match="Forbidden therapeutic text fields"):
        validate_tle_pattern_record(payload)


def test_seed_patterns_json_loads():
    records = load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH)
    assert len(records) >= 5


def test_seed_patterns_validate():
    records = load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH)
    for record in records:
        validate_tle_pattern_record(record)


def test_export_creates_core_compatible_pattern_dicts(tmp_path: Path):
    records = load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH)
    output_path = tmp_path / "core_patterns.json"
    exported = export_core_patterns(records[:2], output_path)

    assert output_path.is_file()
    assert len(exported) == 2
    TherapeuticPatternLibrary.from_dicts(exported)

    for pattern in exported:
        assert "source_confidence" not in pattern
        assert "extraction_method" not in pattern
        assert "evidence_refs" not in pattern
        assert "notes" not in pattern


def test_exported_pattern_ids_remain_unique(tmp_path: Path):
    records = load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH)
    output_path = tmp_path / "core_patterns.json"
    exported = export_core_patterns(records, output_path)
    ids = [pattern["id"] for pattern in exported]
    assert len(ids) == len(set(ids))


def test_no_tle_code_mutates_niros_core(tmp_path: Path):
    core_files = {
        path: path.stat().st_mtime_ns
        for path in (NIROS_ROOT / "niros").rglob("*.py")
    }

    records = load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH)
    export_core_patterns(records, tmp_path / "core_patterns.json")

    for path, before_mtime in core_files.items():
        assert path.stat().st_mtime_ns == before_mtime


def test_deterministic_export(tmp_path: Path):
    records = load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH)
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"

    export_core_patterns(records, first_path)
    export_core_patterns(records, second_path)

    assert first_path.read_text(encoding="utf-8") == second_path.read_text(encoding="utf-8")


def test_to_core_therapeutic_pattern_strips_tle_only_fields():
    record = TLEPatternRecord.from_dict(VALID_TLE_PATTERN)
    core = to_core_therapeutic_pattern(record)

    assert core["id"] == "test_pattern_loop"
    assert "source_confidence" not in core
    assert "evidence_refs" not in core


def test_export_writes_sorted_json_list(tmp_path: Path):
    records = load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH)
    output_path = tmp_path / "core_patterns.json"
    export_core_patterns(records, output_path)

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert isinstance(loaded, list)
    assert [item["id"] for item in loaded] == sorted(record.id for record in records)
