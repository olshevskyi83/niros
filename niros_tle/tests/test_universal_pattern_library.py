"""Tests for Universal Pattern Library."""

from __future__ import annotations

from niros_tle.universal_pattern import UniversalPattern
from niros_tle.universal_pattern_library import (
    DEFAULT_LIBRARY_ID,
    UniversalPatternLibrary,
    build_universal_pattern_library,
    filter_patterns_by_source,
    get_pattern_by_id,
)


def _pattern(
    *,
    pattern_id: str,
    canonical_name: str,
    source_families: tuple[str, ...],
    confidence: float = 0.85,
) -> UniversalPattern:
    return UniversalPattern(
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        source_families=source_families,
        member_pattern_ids=(f"{pattern_id}_member",),
        confidence=confidence,
    )


def test_empty_input_creates_empty_active_library():
    library = build_universal_pattern_library(())
    assert isinstance(library, UniversalPatternLibrary)
    assert library.patterns == ()
    assert library.pattern_count == 0
    assert library.source_families == ()
    assert library.library_status == "active"


def test_single_pattern_creates_library_with_count_one():
    pattern = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        source_families=("act", "cft", "ifs"),
    )
    library = build_universal_pattern_library((pattern,))
    assert library.pattern_count == 1
    assert library.patterns == (pattern,)


def test_multiple_patterns_are_sorted_by_pattern_id():
    second = _pattern(
        pattern_id="canonical_pattern_002",
        canonical_name="clarify personal values",
        source_families=("act",),
    )
    first = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        source_families=("act", "cft"),
    )
    library = build_universal_pattern_library((second, first))
    assert [pattern.pattern_id for pattern in library.patterns] == [
        "canonical_pattern_001",
        "canonical_pattern_002",
    ]


def test_pattern_count_is_correct():
    patterns = (
        _pattern(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            source_families=("act",),
        ),
        _pattern(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            source_families=("act", "cbt"),
        ),
    )
    library = build_universal_pattern_library(patterns)
    assert library.pattern_count == 2


def test_source_families_are_collected_and_sorted():
    patterns = (
        _pattern(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            source_families=("ifs", "act"),
        ),
        _pattern(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            source_families=("cbt", "act"),
        ),
    )
    library = build_universal_pattern_library(patterns)
    assert library.source_families == ("act", "cbt", "ifs")


def test_get_pattern_by_id_returns_matching_pattern():
    pattern = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        source_families=("act",),
    )
    library = build_universal_pattern_library((pattern,))
    assert get_pattern_by_id(library, "canonical_pattern_001") == pattern


def test_get_pattern_by_id_returns_none_when_missing():
    library = build_universal_pattern_library(())
    assert get_pattern_by_id(library, "canonical_pattern_999") is None


def test_filter_patterns_by_source_returns_matching_patterns():
    acceptance = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        source_families=("act", "cft", "ifs"),
    )
    values = _pattern(
        pattern_id="canonical_pattern_002",
        canonical_name="clarify personal values",
        source_families=("act",),
    )
    library = build_universal_pattern_library((acceptance, values))
    filtered = filter_patterns_by_source(library, "ifs")
    assert filtered == (acceptance,)


def test_filter_patterns_by_source_returns_empty_tuple_when_no_match():
    pattern = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        source_families=("act",),
    )
    library = build_universal_pattern_library((pattern,))
    assert filter_patterns_by_source(library, "ifs") == ()


def test_output_is_deterministic():
    patterns = (
        _pattern(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            source_families=("act",),
        ),
        _pattern(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            source_families=("cft", "act"),
        ),
    )
    first = build_universal_pattern_library(patterns)
    second = build_universal_pattern_library(reversed(patterns))
    assert first == second


def test_library_status_defaults_to_active():
    library = build_universal_pattern_library(())
    assert library.library_status == "active"


def test_library_id_defaults_to_universal_pattern_library():
    library = build_universal_pattern_library(())
    assert library.library_id == DEFAULT_LIBRARY_ID
    assert library.library_id == "universal_pattern_library"
