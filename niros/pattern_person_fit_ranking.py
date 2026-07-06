"""Pattern–Person Fit ranking — rank universal pattern library for one profile."""

from __future__ import annotations

from typing import Iterable

from niros.pattern_person_fit_contracts import PatternFitScore, PersonFitProfile
from niros.pattern_person_fit_scoring import score_pattern_fit
from niros_tle.universal_pattern_library import UniversalPatternLibrary


def rank_patterns_for_profile(
    profile: PersonFitProfile,
    library: UniversalPatternLibrary,
) -> tuple[PatternFitScore, ...]:
    """Score and rank all patterns in a universal pattern library for one profile."""
    scored = [score_pattern_fit(profile, pattern) for pattern in library.patterns]
    return sort_pattern_fit_scores(scored)


def sort_pattern_fit_scores(
    scores: Iterable[PatternFitScore],
) -> tuple[PatternFitScore, ...]:
    """Sort fit scores by fit_score, confidence, then pattern_id."""
    return tuple(
        sorted(
            scores,
            key=lambda item: (-item.fit_score, -item.confidence, item.pattern_id),
        )
    )
