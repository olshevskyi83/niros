"""Universal Pattern Library — stable collection for Pattern–Person Fit consumption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros_tle.universal_pattern import ACTIVE_LIBRARY_STATUS, UniversalPattern

DEFAULT_LIBRARY_ID = "universal_pattern_library"


@dataclass(frozen=True)
class UniversalPatternLibrary:
    library_id: str = DEFAULT_LIBRARY_ID
    patterns: tuple[UniversalPattern, ...] = ()
    pattern_count: int = 0
    source_families: tuple[str, ...] = ()
    library_status: str = ACTIVE_LIBRARY_STATUS


def build_universal_pattern_library(
    universal_patterns: Iterable[UniversalPattern],
) -> UniversalPatternLibrary:
    """Build a deterministic universal pattern library."""
    patterns = tuple(sorted(universal_patterns, key=lambda pattern: pattern.pattern_id))
    source_families = tuple(
        sorted(
            {
                source_family
                for pattern in patterns
                for source_family in pattern.source_families
            }
        )
    )
    return UniversalPatternLibrary(
        library_id=DEFAULT_LIBRARY_ID,
        patterns=patterns,
        pattern_count=len(patterns),
        source_families=source_families,
        library_status=ACTIVE_LIBRARY_STATUS,
    )


def get_pattern_by_id(
    library: UniversalPatternLibrary,
    pattern_id: str,
) -> UniversalPattern | None:
    """Return a library pattern by ID, or None if not found."""
    for pattern in library.patterns:
        if pattern.pattern_id == pattern_id:
            return pattern
    return None


def filter_patterns_by_source(
    library: UniversalPatternLibrary,
    source_family: str,
) -> tuple[UniversalPattern, ...]:
    """Return patterns that include the given source family."""
    return tuple(
        pattern
        for pattern in library.patterns
        if source_family in pattern.source_families
    )
