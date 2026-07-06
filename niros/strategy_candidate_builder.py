"""Strategy Candidate Builder — bridge from Pattern–Person Fit to Strategy Engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from niros.pattern_person_fit_contracts import PatternFitReport, PatternFitScore

DEFAULT_STRATEGY_ID = "strategy_candidate_001"
DRAFT_STRATEGY_STATUS = "draft"


@dataclass(frozen=True)
class StrategyCandidate:
    strategy_id: str = DEFAULT_STRATEGY_ID
    profile_id: str = ""
    selected_patterns: tuple[PatternFitScore, ...] = field(default_factory=tuple)
    caution_patterns: tuple[PatternFitScore, ...] = field(default_factory=tuple)
    excluded_patterns: tuple[PatternFitScore, ...] = field(default_factory=tuple)
    strategy_status: str = DRAFT_STRATEGY_STATUS
    rationale: str = ""


def build_strategy_candidate(
    fit_report: PatternFitReport,
    *,
    max_patterns: int = 5,
) -> StrategyCandidate:
    """Build a draft strategy candidate from a pattern fit report."""
    selected_patterns = fit_report.recommended_patterns[:max(0, max_patterns)]
    rationale = _build_rationale(
        selected_count=len(selected_patterns),
        caution_count=len(fit_report.caution_patterns),
        excluded_count=len(fit_report.excluded_patterns),
    )
    return StrategyCandidate(
        strategy_id=DEFAULT_STRATEGY_ID,
        profile_id=fit_report.profile_id,
        selected_patterns=selected_patterns,
        caution_patterns=fit_report.caution_patterns,
        excluded_patterns=fit_report.excluded_patterns,
        strategy_status=DRAFT_STRATEGY_STATUS,
        rationale=rationale,
    )


def _build_rationale(
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
