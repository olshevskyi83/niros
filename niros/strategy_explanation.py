"""Strategy Explanation — deterministic explanation for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass, field

from niros.pattern_person_fit_contracts import PatternFitScore
from niros.strategy_candidate_builder import StrategyCandidate


@dataclass(frozen=True)
class StrategyExplanationItem:
    pattern_id: str
    canonical_name: str
    fit_score: float
    recommendation_status: str
    matched_signals: tuple[str, ...]
    matched_domains: tuple[str, ...]
    matched_needs: tuple[str, ...]
    contraindication_hits: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class StrategyExplanation:
    strategy_id: str
    profile_id: str
    explanation_items: tuple[StrategyExplanationItem, ...] = field(default_factory=tuple)
    summary: str = ""


def build_strategy_explanation(strategy_candidate: StrategyCandidate) -> StrategyExplanation:
    """Build a deterministic explanation from a strategy candidate."""
    patterns = (
        strategy_candidate.selected_patterns
        + strategy_candidate.caution_patterns
        + strategy_candidate.excluded_patterns
    )
    explanation_items = tuple(_build_explanation_item(score) for score in patterns)
    summary = _build_summary(
        selected_count=len(strategy_candidate.selected_patterns),
        caution_count=len(strategy_candidate.caution_patterns),
        excluded_count=len(strategy_candidate.excluded_patterns),
    )
    return StrategyExplanation(
        strategy_id=strategy_candidate.strategy_id,
        profile_id=strategy_candidate.profile_id,
        explanation_items=explanation_items,
        summary=summary,
    )


def _build_explanation_item(score: PatternFitScore) -> StrategyExplanationItem:
    explanation = (
        f"fit={score.fit_score:.4f}; "
        f"signals={len(score.matched_signals)}; "
        f"domains={len(score.matched_domains)}; "
        f"needs={len(score.matched_needs)}; "
        f"contraindications={len(score.contraindication_hits)}"
    )
    return StrategyExplanationItem(
        pattern_id=score.pattern_id,
        canonical_name=score.canonical_name,
        fit_score=score.fit_score,
        recommendation_status=score.recommendation_status,
        matched_signals=score.matched_signals,
        matched_domains=score.matched_domains,
        matched_needs=score.matched_needs,
        contraindication_hits=score.contraindication_hits,
        explanation=explanation,
    )


def _build_summary(
    *,
    selected_count: int,
    caution_count: int,
    excluded_count: int,
) -> str:
    return (
        f"selected={selected_count}; "
        f"caution={caution_count}; "
        f"excluded={excluded_count}"
    )
