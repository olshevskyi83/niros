"""Pattern–Person Fit contracts — stable types for fingerprint-to-library matching."""

from __future__ import annotations

from dataclasses import dataclass, field

RECOMMENDED = "recommended"
USE_WITH_CAUTION = "use_with_caution"
NOT_RECOMMENDED = "not_recommended"

UNSPECIFIED_SESSION_PHASE = "unspecified"


@dataclass(frozen=True)
class PersonFitProfile:
    profile_id: str
    active_signals: tuple[str, ...] = field(default_factory=tuple)
    dominant_domains: tuple[str, ...] = field(default_factory=tuple)
    risk_signals: tuple[str, ...] = field(default_factory=tuple)
    needs: tuple[str, ...] = field(default_factory=tuple)
    session_phase: str = UNSPECIFIED_SESSION_PHASE


@dataclass(frozen=True)
class PatternFitScore:
    pattern_id: str
    canonical_name: str
    fit_score: float
    confidence: float
    matched_signals: tuple[str, ...] = field(default_factory=tuple)
    matched_domains: tuple[str, ...] = field(default_factory=tuple)
    matched_needs: tuple[str, ...] = field(default_factory=tuple)
    contraindication_hits: tuple[str, ...] = field(default_factory=tuple)
    recommendation_status: str = NOT_RECOMMENDED
    reason: str = ""


@dataclass(frozen=True)
class PatternFitReport:
    profile_id: str
    ranked_matches: tuple[PatternFitScore, ...] = field(default_factory=tuple)
    recommended_patterns: tuple[PatternFitScore, ...] = field(default_factory=tuple)
    caution_patterns: tuple[PatternFitScore, ...] = field(default_factory=tuple)
    excluded_patterns: tuple[PatternFitScore, ...] = field(default_factory=tuple)
