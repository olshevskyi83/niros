"""CTPC — Canonical Therapeutic Pattern Corpus contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_EVIDENCE_LEVEL = "low"
DEFAULT_REVIEW_STATUS = "draft"
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0


@dataclass(frozen=True)
class CanonicalTherapeuticPattern:
    pattern_id: str
    name: str
    source_family: str
    therapeutic_function: str
    source_reference: str = ""
    psychological_function: str = ""
    candidate_targets: tuple[str, ...] = field(default_factory=tuple)
    generation_rules: tuple[str, ...] = field(default_factory=tuple)
    voice_rules: tuple[str, ...] = field(default_factory=tuple)
    repetition_rules: tuple[str, ...] = field(default_factory=tuple)
    pause_rules: tuple[str, ...] = field(default_factory=tuple)
    symbolic_elements: tuple[str, ...] = field(default_factory=tuple)
    contraindications: tuple[str, ...] = field(default_factory=tuple)
    evidence_level: str = DEFAULT_EVIDENCE_LEVEL
    confidence: float = 0.0
    review_status: str = DEFAULT_REVIEW_STATUS
    knowledge_domain: str = ""


@dataclass(frozen=True)
class CTPCLibrary:
    patterns: tuple[CanonicalTherapeuticPattern, ...] = field(default_factory=tuple)


def build_ctpc_library(
    patterns: tuple[CanonicalTherapeuticPattern, ...] | list[CanonicalTherapeuticPattern],
) -> CTPCLibrary:
    """Build a CTPC library with patterns sorted by pattern_id."""
    return CTPCLibrary(patterns=tuple(sorted(patterns, key=lambda pattern: pattern.pattern_id)))


def get_ctpc_pattern(library: CTPCLibrary, pattern_id: str) -> CanonicalTherapeuticPattern | None:
    """Return a CTPC pattern by ID, or None if not found."""
    for pattern in library.patterns:
        if pattern.pattern_id == pattern_id:
            return pattern
    return None


def _sort_patterns(patterns: tuple[CanonicalTherapeuticPattern, ...]) -> tuple[CanonicalTherapeuticPattern, ...]:
    return tuple(
        sorted(
            patterns,
            key=lambda pattern: (-pattern.confidence, pattern.pattern_id),
        )
    )


def find_patterns_by_function(
    library: CTPCLibrary,
    therapeutic_function: str,
) -> tuple[CanonicalTherapeuticPattern, ...]:
    """Return patterns matching one therapeutic function."""
    matches = tuple(
        pattern
        for pattern in library.patterns
        if pattern.therapeutic_function == therapeutic_function
    )
    return _sort_patterns(matches)


def find_patterns_for_functions(
    library: CTPCLibrary,
    therapeutic_functions: tuple[str, ...] | list[str],
) -> tuple[CanonicalTherapeuticPattern, ...]:
    """Return patterns for requested therapeutic functions in priority order."""
    selected: list[CanonicalTherapeuticPattern] = []
    seen_pattern_ids: set[str] = set()

    for therapeutic_function in therapeutic_functions:
        for pattern in find_patterns_by_function(library, therapeutic_function):
            if pattern.pattern_id in seen_pattern_ids:
                continue
            selected.append(pattern)
            seen_pattern_ids.add(pattern.pattern_id)

    return tuple(selected)


def validate_ctpc_pattern(pattern: CanonicalTherapeuticPattern) -> tuple[str, ...]:
    """Return validation issue strings for one CTPC pattern."""
    issues: list[str] = []

    if not pattern.pattern_id.strip():
        issues.append("pattern_id must not be empty")
    if not pattern.name.strip():
        issues.append("name must not be empty")
    if not pattern.source_family.strip():
        issues.append("source_family must not be empty")
    if not pattern.therapeutic_function.strip():
        issues.append("therapeutic_function must not be empty")
    if not pattern.generation_rules:
        issues.append("generation_rules must not be empty")
    if not pattern.voice_rules:
        issues.append("voice_rules must not be empty")
    if pattern.confidence < MIN_CONFIDENCE or pattern.confidence > MAX_CONFIDENCE:
        issues.append("confidence must be between 0.0 and 1.0")

    return tuple(issues)
