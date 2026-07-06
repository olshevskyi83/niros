"""Therapeutic Vocal Engine — Icaro profile contracts from strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass, field

from niros.strategy_candidate_builder import StrategyCandidate

DEFAULT_ICARO_ID = "icaro_profile_001"
DEFAULT_VOCAL_STYLE = "gentle_vocal"
DEFAULT_TEMPO = "slow"
DEFAULT_REPETITION_LEVEL = "moderate"
DEFAULT_PAUSE_DENSITY = "high"
DEFAULT_EMOTIONAL_TONE = "supportive"
DEFAULT_SAFETY_LEVEL = "gentle"
DEFAULT_SESSION_PHASE = "preparation"

CONSTRAINT_AVOID_DEEP_EXPOSURE = "avoid_deep_exposure"

THERAPEUTIC_FUNCTION_RULES: tuple[tuple[str, str], ...] = (
    ("self compassion", "self_compassion"),
    ("acceptance", "acceptance"),
    ("stabilization", "stabilization"),
    ("grounding", "grounding"),
    ("values", "values_clarification"),
    ("meaning", "meaning_reconstruction"),
    ("identity", "identity_reinforcement"),
    ("defusion", "cognitive_defusion"),
)


@dataclass(frozen=True)
class IcaroProfile:
    icaro_id: str = DEFAULT_ICARO_ID
    strategy_id: str = ""
    profile_id: str = ""
    therapeutic_functions: tuple[str, ...] = field(default_factory=tuple)
    selected_pattern_ids: tuple[str, ...] = field(default_factory=tuple)
    vocal_style: str = DEFAULT_VOCAL_STYLE
    tempo: str = DEFAULT_TEMPO
    repetition_level: str = DEFAULT_REPETITION_LEVEL
    pause_density: str = DEFAULT_PAUSE_DENSITY
    emotional_tone: str = DEFAULT_EMOTIONAL_TONE
    safety_level: str = DEFAULT_SAFETY_LEVEL
    session_phase: str = DEFAULT_SESSION_PHASE
    constraints: tuple[str, ...] = field(default_factory=tuple)


def _infer_therapeutic_functions(strategy_candidate: StrategyCandidate) -> tuple[str, ...]:
    functions: list[str] = []
    seen: set[str] = set()
    for pattern in strategy_candidate.selected_patterns:
        canonical_name = pattern.canonical_name.lower()
        for substring, function in THERAPEUTIC_FUNCTION_RULES:
            if substring in canonical_name and function not in seen:
                functions.append(function)
                seen.add(function)
    return tuple(functions)


def build_icaro_profile_from_strategy(
    strategy_candidate: StrategyCandidate,
    session_phase: str = DEFAULT_SESSION_PHASE,
) -> IcaroProfile:
    """Build a vocal-delivery Icaro profile from an existing strategy candidate."""
    selected_pattern_ids = tuple(
        pattern.pattern_id for pattern in strategy_candidate.selected_patterns
    )
    therapeutic_functions = _infer_therapeutic_functions(strategy_candidate)

    safety_level = DEFAULT_SAFETY_LEVEL
    constraints: list[str] = []
    tempo = DEFAULT_TEMPO
    repetition_level = DEFAULT_REPETITION_LEVEL
    pause_density = DEFAULT_PAUSE_DENSITY
    emotional_tone = DEFAULT_EMOTIONAL_TONE

    if strategy_candidate.caution_patterns:
        safety_level = "cautious"
        constraints.append(CONSTRAINT_AVOID_DEEP_EXPOSURE)

    if "stabilization" in therapeutic_functions:
        tempo = "very_slow"
        pause_density = "very_high"
        emotional_tone = "grounding"

    if "self_compassion" in therapeutic_functions:
        emotional_tone = "warm_supportive"

    if "acceptance" in therapeutic_functions:
        repetition_level = "high"

    return IcaroProfile(
        strategy_id=strategy_candidate.strategy_id,
        profile_id=strategy_candidate.profile_id,
        therapeutic_functions=therapeutic_functions,
        selected_pattern_ids=selected_pattern_ids,
        safety_level=safety_level,
        session_phase=session_phase,
        constraints=tuple(constraints),
        tempo=tempo,
        repetition_level=repetition_level,
        pause_density=pause_density,
        emotional_tone=emotional_tone,
    )
