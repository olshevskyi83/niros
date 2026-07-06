"""Pattern–Person Fit scoring — deterministic single-pattern fit evaluation."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PatternFitScore,
    PersonFitProfile,
)
from niros_tle.universal_pattern import UniversalPattern

SIGNAL_WEIGHT = 0.45
DOMAIN_WEIGHT = 0.20
NEED_WEIGHT = 0.20
CONFIDENCE_WEIGHT = 0.15
CONTRAINDICATION_PENALTY = 0.30

RECOMMENDED_THRESHOLD = 0.65
CAUTION_THRESHOLD = 0.50


def score_pattern_fit(
    profile: PersonFitProfile,
    pattern: UniversalPattern,
) -> PatternFitScore:
    """Score fit between one person profile and one universal pattern."""
    matched_signals = _sorted_intersection(profile.active_signals, pattern.target_signals)
    matched_domains = _sorted_intersection(profile.dominant_domains, pattern.fit_domains)
    matched_needs = _sorted_intersection(profile.needs, pattern.expected_effects)
    contraindication_hits = _sorted_intersection(
        profile.risk_signals,
        pattern.contraindication_signals,
    )

    signal_component = _ratio_component(matched_signals, pattern.target_signals, SIGNAL_WEIGHT)
    domain_component = _ratio_component(matched_domains, pattern.fit_domains, DOMAIN_WEIGHT)
    need_component = _ratio_component(matched_needs, pattern.expected_effects, NEED_WEIGHT)
    confidence_component = pattern.confidence * CONFIDENCE_WEIGHT
    contraindication_penalty = CONTRAINDICATION_PENALTY if contraindication_hits else 0.0

    fit_score = round(
        _clamp(
            signal_component
            + domain_component
            + need_component
            + confidence_component
            - contraindication_penalty
        ),
        4,
    )
    recommendation_status = _recommendation_status(fit_score, contraindication_hits)
    reason = _build_reason(
        matched_signals=matched_signals,
        matched_domains=matched_domains,
        matched_needs=matched_needs,
        contraindication_hits=contraindication_hits,
    )

    return PatternFitScore(
        pattern_id=pattern.pattern_id,
        canonical_name=pattern.canonical_name,
        fit_score=fit_score,
        confidence=pattern.confidence,
        matched_signals=matched_signals,
        matched_domains=matched_domains,
        matched_needs=matched_needs,
        contraindication_hits=contraindication_hits,
        recommendation_status=recommendation_status,
        reason=reason,
    )


def _sorted_intersection(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(left) & set(right)))


def _ratio_component(
    matched: tuple[str, ...],
    pattern_values: tuple[str, ...],
    weight: float,
) -> float:
    if not pattern_values:
        return 0.0
    return (len(matched) / len(pattern_values)) * weight


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _recommendation_status(
    fit_score: float,
    contraindication_hits: tuple[str, ...],
) -> str:
    if fit_score >= RECOMMENDED_THRESHOLD and not contraindication_hits:
        return RECOMMENDED
    if fit_score >= CAUTION_THRESHOLD or contraindication_hits:
        return USE_WITH_CAUTION
    return NOT_RECOMMENDED


def _build_reason(
    *,
    matched_signals: tuple[str, ...],
    matched_domains: tuple[str, ...],
    matched_needs: tuple[str, ...],
    contraindication_hits: tuple[str, ...],
) -> str:
    return (
        f"signals={len(matched_signals)}; "
        f"domains={len(matched_domains)}; "
        f"needs={len(matched_needs)}; "
        f"contraindications={len(contraindication_hits)}"
    )
