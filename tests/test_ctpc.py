"""Tests for Canonical Therapeutic Pattern Corpus contracts."""

from __future__ import annotations

from niros.ctpc import (
    CTPCLibrary,
    CanonicalTherapeuticPattern,
    build_ctpc_library,
    find_patterns_by_function,
    find_patterns_for_functions,
    get_ctpc_pattern,
    validate_ctpc_pattern,
)


def _pattern(
    *,
    pattern_id: str,
    therapeutic_function: str,
    confidence: float = 0.80,
    name: str | None = None,
) -> CanonicalTherapeuticPattern:
    return CanonicalTherapeuticPattern(
        pattern_id=pattern_id,
        name=name or f"Pattern {pattern_id}",
        source_family="cft",
        therapeutic_function=therapeutic_function,
        generation_rules=("Use gentle second-person phrasing.",),
        voice_rules=("Keep tempo slow and supportive.",),
        confidence=confidence,
    )


def test_default_pattern_values() -> None:
    pattern = CanonicalTherapeuticPattern(
        pattern_id="ctpc_001",
        name="Self-compassion vocal pattern",
        source_family="cft",
        therapeutic_function="self_compassion",
    )
    assert pattern.source_reference == ""
    assert pattern.psychological_function == ""
    assert pattern.candidate_targets == ()
    assert pattern.generation_rules == ()
    assert pattern.voice_rules == ()
    assert pattern.repetition_rules == ()
    assert pattern.pause_rules == ()
    assert pattern.symbolic_elements == ()
    assert pattern.contraindications == ()
    assert pattern.evidence_level == "low"
    assert pattern.confidence == 0.0
    assert pattern.review_status == "draft"


def test_library_defaults_empty() -> None:
    library = CTPCLibrary()
    assert library.patterns == ()


def test_build_ctpc_library_sorts_by_pattern_id() -> None:
    patterns = (
        _pattern(pattern_id="ctpc_b", therapeutic_function="acceptance"),
        _pattern(pattern_id="ctpc_a", therapeutic_function="self_compassion"),
    )
    library = build_ctpc_library(patterns)
    assert [pattern.pattern_id for pattern in library.patterns] == ["ctpc_a", "ctpc_b"]


def test_get_ctpc_pattern_returns_pattern() -> None:
    pattern = _pattern(pattern_id="ctpc_a", therapeutic_function="self_compassion")
    library = build_ctpc_library((pattern,))
    assert get_ctpc_pattern(library, "ctpc_a") == pattern


def test_get_ctpc_pattern_missing_returns_none() -> None:
    library = build_ctpc_library((_pattern(pattern_id="ctpc_a", therapeutic_function="self_compassion"),))
    assert get_ctpc_pattern(library, "missing") is None


def test_find_patterns_by_function_returns_matching_function() -> None:
    library = build_ctpc_library(
        (
            _pattern(pattern_id="ctpc_a", therapeutic_function="self_compassion"),
            _pattern(pattern_id="ctpc_b", therapeutic_function="acceptance"),
        )
    )
    matches = find_patterns_by_function(library, "self_compassion")
    assert len(matches) == 1
    assert matches[0].pattern_id == "ctpc_a"


def test_find_patterns_by_function_sorts_confidence_descending() -> None:
    library = build_ctpc_library(
        (
            _pattern(pattern_id="ctpc_a", therapeutic_function="self_compassion", confidence=0.70),
            _pattern(pattern_id="ctpc_b", therapeutic_function="self_compassion", confidence=0.90),
        )
    )
    matches = find_patterns_by_function(library, "self_compassion")
    assert [pattern.pattern_id for pattern in matches] == ["ctpc_b", "ctpc_a"]


def test_find_patterns_for_functions_preserves_function_priority() -> None:
    library = build_ctpc_library(
        (
            _pattern(pattern_id="ctpc_acceptance", therapeutic_function="acceptance", confidence=0.95),
            _pattern(pattern_id="ctpc_self_compassion", therapeutic_function="self_compassion", confidence=0.80),
        )
    )
    matches = find_patterns_for_functions(library, ("self_compassion", "acceptance"))
    assert [pattern.pattern_id for pattern in matches] == ["ctpc_self_compassion", "ctpc_acceptance"]


def test_find_patterns_for_functions_removes_duplicates() -> None:
    library = build_ctpc_library(
        (
            _pattern(pattern_id="ctpc_shared", therapeutic_function="self_compassion", confidence=0.90),
            _pattern(pattern_id="ctpc_acceptance", therapeutic_function="acceptance", confidence=0.85),
        )
    )
    matches = find_patterns_for_functions(library, ("self_compassion", "acceptance", "self_compassion"))
    assert [pattern.pattern_id for pattern in matches] == ["ctpc_shared", "ctpc_acceptance"]


def test_validate_valid_pattern_returns_empty_tuple() -> None:
    pattern = _pattern(pattern_id="ctpc_a", therapeutic_function="self_compassion", confidence=0.75)
    assert validate_ctpc_pattern(pattern) == ()


def test_validate_missing_required_fields_returns_issues() -> None:
    pattern = CanonicalTherapeuticPattern(
        pattern_id="",
        name="",
        source_family="",
        therapeutic_function="",
    )
    issues = validate_ctpc_pattern(pattern)
    assert "pattern_id must not be empty" in issues
    assert "name must not be empty" in issues
    assert "source_family must not be empty" in issues
    assert "therapeutic_function must not be empty" in issues
    assert "generation_rules must not be empty" in issues
    assert "voice_rules must not be empty" in issues


def test_validate_confidence_bounds() -> None:
    low = _pattern(pattern_id="ctpc_low", therapeutic_function="self_compassion", confidence=-0.1)
    high = _pattern(pattern_id="ctpc_high", therapeutic_function="self_compassion", confidence=1.1)
    assert "confidence must be between 0.0 and 1.0" in validate_ctpc_pattern(low)
    assert "confidence must be between 0.0 and 1.0" in validate_ctpc_pattern(high)


def test_output_deterministic() -> None:
    patterns = (
        _pattern(pattern_id="ctpc_b", therapeutic_function="acceptance", confidence=0.85),
        _pattern(pattern_id="ctpc_a", therapeutic_function="self_compassion", confidence=0.90),
        _pattern(pattern_id="ctpc_c", therapeutic_function="acceptance", confidence=0.95),
    )
    first_library = build_ctpc_library(patterns)
    second_library = build_ctpc_library(patterns)
    assert first_library == second_library
    assert find_patterns_for_functions(first_library, ("acceptance", "self_compassion")) == find_patterns_for_functions(
        second_library,
        ("acceptance", "self_compassion"),
    )
