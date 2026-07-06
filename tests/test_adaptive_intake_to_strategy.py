"""End-to-end test from adaptive intake session to strategy and explanation."""

from __future__ import annotations

from niros.intake_session_state import (
    add_user_turn,
    build_person_fit_profile_from_intake,
    create_intake_session,
)
from niros.pattern_person_fit_contracts import PersonFitProfile
from niros.pattern_person_fit_report import build_pattern_fit_report
from niros.strategy_candidate_builder import StrategyCandidate, build_strategy_candidate
from niros.strategy_explanation import StrategyExplanation, build_strategy_explanation
from niros_tle.universal_pattern import UniversalPattern
from niros_tle.universal_pattern_library import build_universal_pattern_library

PATTERN_SELF_COMPASSION = "pattern_self_compassion"
PATTERN_ACCEPTANCE = "pattern_acceptance"
PATTERN_STABILIZATION = "pattern_stabilization"
PATTERN_DEEP_EXPOSURE = "pattern_deep_exposure"
PATTERN_VALUES = "pattern_values"
PATTERN_DEFUSION = "pattern_defusion"


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


def intake_to_strategy_pattern_library() -> tuple[UniversalPattern, ...]:
    """Mini UniversalPattern library for intake-to-strategy regression."""
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
            pattern_id=PATTERN_DEEP_EXPOSURE,
            canonical_name="deep emotional exposure",
            confidence=0.90,
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
            expected_effects=("emotional_tolerance",),
            contraindication_signals=("overwhelm_risk",),
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
            pattern_id=PATTERN_DEFUSION,
            canonical_name="cognitive defusion",
            confidence=0.86,
            target_signals=("rumination", "catastrophizing"),
            fit_domains=("cognitive",),
            expected_effects=("cognitive_distance",),
        ),
    )


def _run_adaptive_intake(session_id: str = "intake_to_strategy_001"):
    session = create_intake_session(session_id)
    session = add_user_turn(
        session,
        "I feel ashamed and I avoid strong emotions.",
        detected_signals=("shame_sensitivity", "emotional_avoidance"),
    )
    session = add_user_turn(
        session,
        "When this happens, I criticize myself very harshly.",
        detected_signals=("harsh_self_criticism",),
    )
    session = add_user_turn(
        session,
        "I need self-compassion and emotional tolerance.",
        detected_needs=("self_compassion", "emotional_tolerance"),
    )
    session = add_user_turn(
        session,
        "If we go too deep too fast, I might get overwhelmed.",
        detected_signals=("overwhelm_risk",),
        detected_risk_signals=("overwhelm_risk",),
    )
    return session


def _run_intake_to_strategy_pipeline(session_id: str = "intake_to_strategy_001") -> tuple[
    PersonFitProfile,
    StrategyCandidate,
    StrategyExplanation,
]:
    session = _run_adaptive_intake(session_id)
    profile = build_person_fit_profile_from_intake(session)
    library = build_universal_pattern_library(intake_to_strategy_pattern_library())
    fit_report = build_pattern_fit_report(profile, library)
    strategy = build_strategy_candidate(fit_report, max_patterns=3)
    explanation = build_strategy_explanation(strategy)
    return profile, strategy, explanation


def _selected_ids(strategy: StrategyCandidate) -> set[str]:
    return {pattern.pattern_id for pattern in strategy.selected_patterns}


def _caution_ids(strategy: StrategyCandidate) -> set[str]:
    return {pattern.pattern_id for pattern in strategy.caution_patterns}


def test_adaptive_intake_to_strategy_shame_case() -> None:
    session = _run_adaptive_intake("intake_to_strategy_001")
    assert session.is_ready_for_strategy is True

    profile = build_person_fit_profile_from_intake(session)
    library = build_universal_pattern_library(intake_to_strategy_pattern_library())
    fit_report = build_pattern_fit_report(profile, library)
    strategy = build_strategy_candidate(fit_report, max_patterns=3)
    explanation = build_strategy_explanation(strategy)

    selected = _selected_ids(strategy)
    caution = _caution_ids(strategy)

    assert PATTERN_SELF_COMPASSION in selected
    assert PATTERN_ACCEPTANCE in selected
    assert PATTERN_DEEP_EXPOSURE not in selected
    assert PATTERN_DEEP_EXPOSURE in caution
    assert PATTERN_VALUES not in selected
    assert explanation.explanation_items
    assert explanation.profile_id == profile.profile_id
    assert strategy.profile_id == profile.profile_id


def test_adaptive_intake_to_strategy_deterministic() -> None:
    first_profile, first_strategy, first_explanation = _run_intake_to_strategy_pipeline(
        "intake_to_strategy_deterministic"
    )
    second_profile, second_strategy, second_explanation = _run_intake_to_strategy_pipeline(
        "intake_to_strategy_deterministic"
    )

    assert first_profile == second_profile
    assert _selected_ids(first_strategy) == _selected_ids(second_strategy)
    assert _caution_ids(first_strategy) == _caution_ids(second_strategy)
    assert first_explanation.summary == second_explanation.summary
