"""Human-case regression tests for Pattern–Person Fit through Strategy Explanation."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import PatternFitReport, PersonFitProfile
from niros.pattern_person_fit_report import build_pattern_fit_report
from niros.strategy_candidate_builder import StrategyCandidate, build_strategy_candidate
from niros.strategy_explanation import StrategyExplanation, build_strategy_explanation
from niros_tle.universal_pattern import UniversalPattern
from niros_tle.universal_pattern_library import build_universal_pattern_library

PATTERN_SELF_COMPASSION = "pattern_self_compassion"
PATTERN_ACCEPTANCE = "pattern_acceptance"
PATTERN_STABILIZATION = "pattern_stabilization"
PATTERN_VALUES = "pattern_values"
PATTERN_MEANING = "pattern_meaning"
PATTERN_IDENTITY = "pattern_identity"
PATTERN_DEFUSION = "pattern_defusion"
PATTERN_DEEP_EXPOSURE = "pattern_deep_exposure"


def _universal_pattern(
    *,
    pattern_id: str,
    canonical_name: str,
    confidence: float,
    target_signals: tuple[str, ...],
    fit_domains: tuple[str, ...],
    expected_effects: tuple[str, ...],
    contraindication_signals: tuple[str, ...] = (),
    source_family: str = "act",
) -> UniversalPattern:
    return UniversalPattern(
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        source_families=(source_family,),
        member_pattern_ids=(f"{pattern_id}_member",),
        confidence=confidence,
        target_signals=target_signals,
        contraindication_signals=contraindication_signals,
        fit_domains=fit_domains,
        expected_effects=expected_effects,
    )


def human_case_pattern_library() -> tuple[UniversalPattern, ...]:
    """Shared mini library for human-case regression tests."""
    return (
        _universal_pattern(
            pattern_id=PATTERN_SELF_COMPASSION,
            canonical_name="self compassion for shame",
            confidence=0.90,
            target_signals=("shame_sensitivity", "harsh_self_criticism"),
            fit_domains=("self",),
            expected_effects=("self_compassion",),
            source_family="cft",
        ),
        _universal_pattern(
            pattern_id=PATTERN_ACCEPTANCE,
            canonical_name="acceptance of difficult emotions",
            confidence=0.85,
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
            expected_effects=("emotional_tolerance",),
        ),
        _universal_pattern(
            pattern_id=PATTERN_STABILIZATION,
            canonical_name="stabilization before deep work",
            confidence=0.88,
            target_signals=("overwhelm_risk", "emotional_instability"),
            fit_domains=("emotion_regulation",),
            expected_effects=("stabilization",),
        ),
        _universal_pattern(
            pattern_id=PATTERN_VALUES,
            canonical_name="values clarification",
            confidence=0.84,
            target_signals=("values_confusion", "low_direction"),
            fit_domains=("values", "meaning"),
            expected_effects=("values_alignment",),
        ),
        _universal_pattern(
            pattern_id=PATTERN_MEANING,
            canonical_name="meaning reconstruction",
            confidence=0.82,
            target_signals=("existential_emptiness", "loss_of_meaning"),
            fit_domains=("meaning",),
            expected_effects=("meaning_making",),
        ),
        _universal_pattern(
            pattern_id=PATTERN_IDENTITY,
            canonical_name="identity reinforcement",
            confidence=0.80,
            target_signals=("identity_diffusion", "low_self_coherence"),
            fit_domains=("self", "meaning"),
            expected_effects=("identity_coherence",),
        ),
        _universal_pattern(
            pattern_id=PATTERN_DEFUSION,
            canonical_name="cognitive defusion",
            confidence=0.86,
            target_signals=("rumination", "catastrophizing"),
            fit_domains=("cognitive",),
            expected_effects=("cognitive_distance",),
        ),
        _universal_pattern(
            pattern_id=PATTERN_DEEP_EXPOSURE,
            canonical_name="deep emotional exposure",
            confidence=0.90,
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
            expected_effects=("emotional_tolerance",),
            contraindication_signals=("overwhelm_risk",),
        ),
    )


def run_case(
    profile: PersonFitProfile,
    patterns: tuple[UniversalPattern, ...] | None = None,
    *,
    max_patterns: int = 3,
) -> tuple[PatternFitReport, StrategyCandidate, StrategyExplanation]:
    """Run the Pattern–Person Fit pipeline for one human case."""
    library = build_universal_pattern_library(patterns or human_case_pattern_library())
    fit_report = build_pattern_fit_report(profile, library)
    strategy = build_strategy_candidate(fit_report, max_patterns=max_patterns)
    explanation = build_strategy_explanation(strategy)
    return fit_report, strategy, explanation


def _selected_ids(strategy: StrategyCandidate) -> set[str]:
    return {pattern.pattern_id for pattern in strategy.selected_patterns}


def _caution_ids(strategy: StrategyCandidate) -> set[str]:
    return {pattern.pattern_id for pattern in strategy.caution_patterns}


def _rank_index(fit_report: PatternFitReport, pattern_id: str) -> int:
    return next(
        index
        for index, score in enumerate(fit_report.ranked_matches)
        if score.pattern_id == pattern_id
    )


def test_case_shame_self_criticism_and_emotional_avoidance():
    profile = PersonFitProfile(
        profile_id="case_shame_self_criticism",
        active_signals=("shame_sensitivity", "harsh_self_criticism", "emotional_avoidance"),
        dominant_domains=("self", "emotion_regulation"),
        risk_signals=("overwhelm_risk",),
        needs=("self_compassion", "emotional_tolerance"),
        session_phase="preparation",
    )
    fit_report, strategy, explanation = run_case(profile)

    selected = _selected_ids(strategy)
    caution = _caution_ids(strategy)
    assert PATTERN_SELF_COMPASSION in selected
    assert PATTERN_ACCEPTANCE in selected
    assert PATTERN_VALUES not in selected
    assert PATTERN_DEEP_EXPOSURE not in selected
    assert PATTERN_DEEP_EXPOSURE in caution

    top_selected = strategy.selected_patterns[0].pattern_id
    assert top_selected in {PATTERN_SELF_COMPASSION, PATTERN_ACCEPTANCE}

    assert explanation.explanation_items
    assert explanation.profile_id == profile.profile_id


def test_case_overwhelm_stabilization():
    profile = PersonFitProfile(
        profile_id="case_overwhelm_stabilization",
        active_signals=("overwhelm_risk", "emotional_instability", "emotional_avoidance"),
        dominant_domains=("emotion_regulation",),
        risk_signals=("overwhelm_risk",),
        needs=("stabilization", "emotional_tolerance"),
        session_phase="preparation",
    )
    fit_report, strategy, explanation = run_case(profile)

    selected = _selected_ids(strategy)
    caution = _caution_ids(strategy)

    assert PATTERN_STABILIZATION in selected
    assert PATTERN_DEEP_EXPOSURE in caution
    assert PATTERN_DEEP_EXPOSURE not in selected
    assert PATTERN_ACCEPTANCE in selected
    assert explanation.summary == "selected=2; caution=1; excluded=5"


def test_case_values_confusion():
    profile = PersonFitProfile(
        profile_id="case_values_confusion",
        active_signals=("values_confusion", "low_direction"),
        dominant_domains=("values", "meaning"),
        needs=("values_alignment",),
        session_phase="preparation",
    )
    fit_report, strategy, explanation = run_case(profile)

    selected = _selected_ids(strategy)
    assert PATTERN_VALUES in selected
    assert PATTERN_SELF_COMPASSION not in selected
    assert PATTERN_ACCEPTANCE not in selected
    assert strategy.selected_patterns[0].pattern_id == PATTERN_VALUES
    assert explanation.explanation_items


def test_case_meaning_and_identity():
    profile = PersonFitProfile(
        profile_id="case_meaning_identity",
        active_signals=("existential_emptiness", "loss_of_meaning", "identity_diffusion"),
        dominant_domains=("meaning", "self"),
        needs=("meaning_making", "identity_coherence"),
        session_phase="preparation",
    )
    fit_report, strategy, explanation = run_case(profile)

    selected = _selected_ids(strategy)
    assert PATTERN_MEANING in selected
    assert PATTERN_IDENTITY in selected

    meaning_rank = _rank_index(fit_report, PATTERN_MEANING)
    identity_rank = _rank_index(fit_report, PATTERN_IDENTITY)
    values_rank = _rank_index(fit_report, PATTERN_VALUES)
    assert values_rank > meaning_rank
    assert values_rank > identity_rank
    assert explanation.explanation_items


def test_case_rumination_and_catastrophizing():
    profile = PersonFitProfile(
        profile_id="case_rumination_catastrophizing",
        active_signals=("rumination", "catastrophizing"),
        dominant_domains=("cognitive",),
        needs=("cognitive_distance",),
        session_phase="preparation",
    )
    fit_report, strategy, explanation = run_case(profile)

    selected = _selected_ids(strategy)
    assert PATTERN_DEFUSION in selected
    assert PATTERN_SELF_COMPASSION not in selected
    assert PATTERN_VALUES not in selected
    assert strategy.selected_patterns[0].pattern_id == PATTERN_DEFUSION
    assert explanation.explanation_items


def test_case_shame_and_overwhelm_mixed():
    profile = PersonFitProfile(
        profile_id="case_shame_overwhelm",
        active_signals=(
            "shame_sensitivity",
            "harsh_self_criticism",
            "emotional_avoidance",
            "overwhelm_risk",
        ),
        dominant_domains=("self", "emotion_regulation"),
        risk_signals=("overwhelm_risk",),
        needs=("self_compassion", "stabilization", "emotional_tolerance"),
        session_phase="preparation",
    )
    fit_report, strategy, explanation = run_case(profile)

    selected = _selected_ids(strategy)
    caution = _caution_ids(strategy)

    assert PATTERN_SELF_COMPASSION in selected
    assert PATTERN_STABILIZATION in selected
    assert PATTERN_DEEP_EXPOSURE in caution
    assert PATTERN_DEEP_EXPOSURE not in selected
    assert PATTERN_ACCEPTANCE in selected
    assert explanation.explanation_items


def test_human_case_pipeline_is_deterministic():
    profile = PersonFitProfile(
        profile_id="case_shame_self_criticism",
        active_signals=("shame_sensitivity", "harsh_self_criticism", "emotional_avoidance"),
        dominant_domains=("self", "emotion_regulation"),
        needs=("self_compassion", "emotional_tolerance"),
        session_phase="preparation",
    )
    first = run_case(profile)
    second = run_case(profile)
    assert first[0] == second[0]
    assert first[1] == second[1]
    assert first[2] == second[2]
