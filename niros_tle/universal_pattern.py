"""Universal Pattern — stable library contract for Pattern–Person Fit consumption."""

from __future__ import annotations

from dataclasses import dataclass, field

from niros_tle.approved_canonical_pattern import ApprovedCanonicalPattern

ACTIVE_LIBRARY_STATUS = "active"
UNSPECIFIED_VALUE = "unspecified"

SOURCE_TYPE_DEMO = "demo"
SOURCE_TYPE_MANUAL_SEED = "manual_seed"
SOURCE_TYPE_CTPC = "ctpc"
SOURCE_TYPE_CORPUS_DERIVED = "corpus_derived"
SOURCE_TYPE_UNSPECIFIED = "unspecified"


@dataclass(frozen=True)
class UniversalPattern:
    pattern_id: str
    canonical_name: str
    source_families: tuple[str, ...]
    member_pattern_ids: tuple[str, ...]
    confidence: float
    target_signals: tuple[str, ...] = field(default_factory=tuple)
    contraindication_signals: tuple[str, ...] = field(default_factory=tuple)
    fit_domains: tuple[str, ...] = field(default_factory=tuple)
    expected_effects: tuple[str, ...] = field(default_factory=tuple)
    intervention_style: str = UNSPECIFIED_VALUE
    session_phase: str = UNSPECIFIED_VALUE
    library_status: str = ACTIVE_LIBRARY_STATUS
    source_type: str = SOURCE_TYPE_UNSPECIFIED
    source_reference: str = ""


def build_universal_pattern(
    approved_pattern: ApprovedCanonicalPattern,
) -> UniversalPattern:
    """Build a universal pattern from an approved canonical pattern."""
    return UniversalPattern(
        pattern_id=approved_pattern.pattern_id,
        canonical_name=approved_pattern.canonical_name,
        source_families=approved_pattern.source_families,
        member_pattern_ids=approved_pattern.member_pattern_ids,
        confidence=approved_pattern.confidence,
        target_signals=(),
        contraindication_signals=(),
        fit_domains=(),
        expected_effects=(),
        intervention_style=UNSPECIFIED_VALUE,
        session_phase=UNSPECIFIED_VALUE,
        library_status=ACTIVE_LIBRARY_STATUS,
    )
