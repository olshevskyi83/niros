"""Pattern–Person Fit report — build grouped fit report for one profile and library."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PatternFitReport,
    PersonFitProfile,
)
from niros.pattern_person_fit_ranking import rank_patterns_for_profile
from niros_tle.universal_pattern_library import UniversalPatternLibrary


def build_pattern_fit_report(
    profile: PersonFitProfile,
    library: UniversalPatternLibrary,
) -> PatternFitReport:
    """Build a deterministic fit report from one profile and universal pattern library."""
    ranked_matches = rank_patterns_for_profile(profile, library)
    recommended_patterns = tuple(
        score for score in ranked_matches if score.recommendation_status == RECOMMENDED
    )
    caution_patterns = tuple(
        score for score in ranked_matches if score.recommendation_status == USE_WITH_CAUTION
    )
    excluded_patterns = tuple(
        score for score in ranked_matches if score.recommendation_status == NOT_RECOMMENDED
    )
    return PatternFitReport(
        profile_id=profile.profile_id,
        ranked_matches=ranked_matches,
        recommended_patterns=recommended_patterns,
        caution_patterns=caution_patterns,
        excluded_patterns=excluded_patterns,
    )
