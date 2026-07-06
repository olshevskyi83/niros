"""Tests for Therapeutic Vocal Engine / Icaro profile contracts."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import RECOMMENDED, PatternFitScore
from niros.strategy_candidate_builder import DEFAULT_STRATEGY_ID, StrategyCandidate
from niros.therapeutic_vocal_engine import (
    CONSTRAINT_AVOID_DEEP_EXPOSURE,
    DEFAULT_EMOTIONAL_TONE,
    DEFAULT_ICARO_ID,
    DEFAULT_PAUSE_DENSITY,
    DEFAULT_REPETITION_LEVEL,
    DEFAULT_SAFETY_LEVEL,
    DEFAULT_TEMPO,
    IcaroProfile,
    build_icaro_profile_from_strategy,
)


def _score(
    *,
    pattern_id: str,
    canonical_name: str,
) -> PatternFitScore:
    return PatternFitScore(
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        fit_score=0.95,
        confidence=0.90,
        recommendation_status=RECOMMENDED,
    )


def _strategy(
    *,
    selected: tuple[PatternFitScore, ...] = (),
    caution: tuple[PatternFitScore, ...] = (),
    profile_id: str = "profile_001",
) -> StrategyCandidate:
    return StrategyCandidate(
        strategy_id=DEFAULT_STRATEGY_ID,
        profile_id=profile_id,
        selected_patterns=selected,
        caution_patterns=caution,
    )


def test_default_icaro_profile_values() -> None:
    profile = IcaroProfile()
    assert profile.icaro_id == DEFAULT_ICARO_ID
    assert profile.therapeutic_functions == ()
    assert profile.selected_pattern_ids == ()
    assert profile.vocal_style == "gentle_vocal"
    assert profile.tempo == DEFAULT_TEMPO
    assert profile.repetition_level == DEFAULT_REPETITION_LEVEL
    assert profile.pause_density == DEFAULT_PAUSE_DENSITY
    assert profile.emotional_tone == DEFAULT_EMOTIONAL_TONE
    assert profile.safety_level == DEFAULT_SAFETY_LEVEL
    assert profile.session_phase == "preparation"
    assert profile.constraints == ()


def test_strategy_id_is_preserved() -> None:
    strategy = _strategy(selected=(_score(pattern_id="p1", canonical_name="values clarification"),))
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.strategy_id == DEFAULT_STRATEGY_ID


def test_profile_id_is_preserved() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="values clarification"),),
        profile_id="patient_profile_001",
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.profile_id == "patient_profile_001"


def test_selected_pattern_ids_are_preserved() -> None:
    strategy = _strategy(
        selected=(
            _score(pattern_id="pattern_self_compassion", canonical_name="self compassion for shame"),
            _score(pattern_id="pattern_acceptance", canonical_name="acceptance of difficult emotions"),
        )
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.selected_pattern_ids == ("pattern_self_compassion", "pattern_acceptance")


def test_self_compassion_function_inferred() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="self compassion for shame"),)
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.therapeutic_functions == ("self_compassion",)


def test_acceptance_function_inferred() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="acceptance of difficult emotions"),)
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.therapeutic_functions == ("acceptance",)


def test_stabilization_function_inferred() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="stabilization before deep work"),)
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.therapeutic_functions == ("stabilization",)


def test_duplicates_removed() -> None:
    strategy = _strategy(
        selected=(
            _score(pattern_id="p1", canonical_name="self compassion for shame"),
            _score(pattern_id="p2", canonical_name="guided self compassion practice"),
        )
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.therapeutic_functions == ("self_compassion",)


def test_caution_pattern_sets_cautious_safety() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="acceptance of difficult emotions"),),
        caution=(_score(pattern_id="p2", canonical_name="deep emotional exposure"),),
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.safety_level == "cautious"


def test_caution_pattern_adds_avoid_deep_exposure_constraint() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="acceptance of difficult emotions"),),
        caution=(_score(pattern_id="p2", canonical_name="deep emotional exposure"),),
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert CONSTRAINT_AVOID_DEEP_EXPOSURE in profile.constraints


def test_stabilization_adjusts_tempo_and_pauses() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="stabilization before deep work"),)
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.tempo == "very_slow"
    assert profile.pause_density == "very_high"
    assert profile.emotional_tone == "grounding"


def test_self_compassion_adjusts_emotional_tone() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="self compassion for shame"),)
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.emotional_tone == "warm_supportive"


def test_acceptance_adjusts_repetition_level() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="acceptance of difficult emotions"),)
    )
    profile = build_icaro_profile_from_strategy(strategy)
    assert profile.repetition_level == "high"


def test_session_phase_is_preserved() -> None:
    strategy = _strategy(
        selected=(_score(pattern_id="p1", canonical_name="acceptance of difficult emotions"),)
    )
    profile = build_icaro_profile_from_strategy(strategy, session_phase="integration")
    assert profile.session_phase == "integration"


def test_output_deterministic() -> None:
    strategy = _strategy(
        selected=(
            _score(pattern_id="pattern_self_compassion", canonical_name="self compassion for shame"),
            _score(pattern_id="pattern_acceptance", canonical_name="acceptance of difficult emotions"),
        ),
        caution=(_score(pattern_id="pattern_deep_exposure", canonical_name="deep emotional exposure"),),
    )
    first = build_icaro_profile_from_strategy(strategy, session_phase="preparation")
    second = build_icaro_profile_from_strategy(strategy, session_phase="preparation")
    assert first == second
    assert isinstance(first, IcaroProfile)
