from __future__ import annotations

from dataclasses import dataclass, field

from niros.knowledge import PatternLoader

RELATIONSHIPS_DOMAIN = "relationships"

VULNERABILITY_PATTERN_IDS = frozenset(
    {
        "self_worth_instability",
        "rumination",
        "emotional_suppression",
        "perfectionism",
        "harsh_self_criticism",
        "shame_sensitivity",
        "emotional_overwhelm",
        "anxiety_reactivity",
        "emotional_avoidance",
        "identity_uncertainty",
        "low_self_efficacy",
        "existential_fear",
        "emotional_distress_signal",
        "nightmare_disturbance",
        "chronic_stress_signal",
    }
)

PATTERN_EXPLORATION_SPECS: dict[str, dict[str, object]] = {
    "self_worth_instability": {
        "objective": "Support self-compassion and stabilize reactive self-worth.",
        "target_emotions": ["shame", "self-criticism", "insecurity"],
        "estimated_duration": 12,
        "priority": 2,
    },
    "rumination": {
        "objective": "Introduce acceptance and release from repetitive worry cycles.",
        "target_emotions": ["worry", "mental looping", "tension"],
        "estimated_duration": 10,
        "priority": 3,
    },
    "emotional_suppression": {
        "objective": "Create space for safe emotional expression and naming.",
        "target_emotions": ["numbness", "suppressed affect", "constriction"],
        "estimated_duration": 12,
        "priority": 2,
    },
    "perfectionism": {
        "objective": "Practice flexibility and reduce performance-linked pressure.",
        "target_emotions": ["pressure", "rigidity", "fear of failure"],
        "estimated_duration": 10,
        "priority": 3,
    },
    "existential_fear": {
        "objective": "Explore reported fear about life and continuing with paced safety.",
        "target_emotions": ["fear", "dread", "uncertainty"],
        "estimated_duration": 12,
        "priority": 2,
    },
    "emotional_distress_signal": {
        "objective": "Understand reported distress and what helps the person feel safer.",
        "target_emotions": ["distress", "fear", "overwhelm"],
        "estimated_duration": 10,
        "priority": 2,
    },
    "nightmare_disturbance": {
        "objective": "Explore sleep-related distress and nightmare themes gently.",
        "target_emotions": ["fear", "sleep distress", "fatigue"],
        "estimated_duration": 10,
        "priority": 3,
    },
    "chronic_stress_signal": {
        "objective": "Explore persistent stress patterns and regulation needs.",
        "target_emotions": ["stress", "tension", "exhaustion"],
        "estimated_duration": 10,
        "priority": 3,
    },
}

RELATIONSHIP_EXPLORATION_SPEC = {
    "objective": "Explore relationship patterns and attachment themes in a contained way.",
    "target_emotions": ["anxiety", "loneliness", "trust"],
    "estimated_duration": 14,
    "priority": 1,
}

DEFAULT_OPENING_OBJECTIVE = (
    "Establish safety, consent, and a clear frame for the session."
)
STRENGTHS_FIRST_OPENING_OBJECTIVE = (
    "Begin with strengths recognition and existing resources before deeper work."
)
DEFAULT_STABILIZATION_OBJECTIVE = (
    "Support nervous-system stabilization and present-moment grounding."
)
STRENGTHS_FIRST_STABILIZATION_OBJECTIVE = (
    "Anchor attention on existing strengths, support, and bodily steadiness."
)
DEFAULT_INTEGRATION_OBJECTIVE = (
    "Consolidate session insights and identify one carry-forward intention."
)
DEFAULT_CLOSING_OBJECTIVE = (
    "Close the session with orientation, safety check, and next-step clarity."
)
EMPTY_PROFILE_OPENING_OBJECTIVE = (
    "Establish safety and a gentle entry when profile evidence is still limited."
)
EMPTY_PROFILE_STABILIZATION_OBJECTIVE = (
    "Provide simple grounding while remaining open to emerging themes."
)


@dataclass(frozen=True)
class ScenarioPhase:
    objective: str
    target_patterns: list[str] = field(default_factory=list)
    target_emotions: list[str] = field(default_factory=list)
    estimated_duration: int = 0
    priority: int = 0


@dataclass(frozen=True)
class ScenarioBlueprint:
    opening_phase: ScenarioPhase
    stabilization_phase: ScenarioPhase
    exploration_phases: list[ScenarioPhase]
    integration_phase: ScenarioPhase
    closing_phase: ScenarioPhase


def build_scenario_blueprint(human_profile: dict) -> ScenarioBlueprint:
    pattern_ids = _ranked_pattern_ids(human_profile)
    relationship_patterns = _relationship_patterns(pattern_ids)
    is_empty = not pattern_ids
    is_healthy = not is_empty and not _has_vulnerability_patterns(pattern_ids)

    opening = _build_opening_phase(is_empty=is_empty, is_healthy=is_healthy)
    stabilization = _build_stabilization_phase(is_empty=is_empty, is_healthy=is_healthy)
    exploration_phases = _build_exploration_phases(
        pattern_ids,
        relationship_patterns,
    )
    integration = _build_integration_phase(pattern_ids)
    closing = _build_closing_phase()

    return ScenarioBlueprint(
        opening_phase=opening,
        stabilization_phase=stabilization,
        exploration_phases=exploration_phases,
        integration_phase=integration,
        closing_phase=closing,
    )


def _ranked_pattern_ids(human_profile: dict) -> list[str]:
    pattern_counts: dict[str, int] = human_profile.get("pattern_counts", {})
    if not pattern_counts:
        return []

    return sorted(
        pattern_counts,
        key=lambda pattern_id: (-pattern_counts[pattern_id], pattern_id),
    )


def _has_vulnerability_patterns(pattern_ids: list[str]) -> bool:
    return any(pattern_id in VULNERABILITY_PATTERN_IDS for pattern_id in pattern_ids)


def _relationship_patterns(pattern_ids: list[str]) -> list[str]:
    loader = PatternLoader()
    relationship_patterns: list[str] = []
    for pattern_id in pattern_ids:
        pattern = loader.load(pattern_id)
        if pattern.domain == RELATIONSHIPS_DOMAIN:
            relationship_patterns.append(pattern_id)
    return relationship_patterns


def _build_opening_phase(*, is_empty: bool, is_healthy: bool) -> ScenarioPhase:
    if is_empty:
        objective = EMPTY_PROFILE_OPENING_OBJECTIVE
    elif is_healthy:
        objective = STRENGTHS_FIRST_OPENING_OBJECTIVE
    else:
        objective = DEFAULT_OPENING_OBJECTIVE

    return ScenarioPhase(
        objective=objective,
        target_patterns=[],
        target_emotions=["safety", "orientation"],
        estimated_duration=8,
        priority=1,
    )


def _build_stabilization_phase(*, is_empty: bool, is_healthy: bool) -> ScenarioPhase:
    if is_empty:
        objective = EMPTY_PROFILE_STABILIZATION_OBJECTIVE
    elif is_healthy:
        objective = STRENGTHS_FIRST_STABILIZATION_OBJECTIVE
    else:
        objective = DEFAULT_STABILIZATION_OBJECTIVE

    return ScenarioPhase(
        objective=objective,
        target_patterns=[],
        target_emotions=["grounding", "regulation"],
        estimated_duration=10,
        priority=1,
    )


def _build_exploration_phases(
    pattern_ids: list[str],
    relationship_patterns: list[str],
) -> list[ScenarioPhase]:
    phases: list[ScenarioPhase] = []

    if relationship_patterns:
        phases.append(
            ScenarioPhase(
                objective=str(RELATIONSHIP_EXPLORATION_SPEC["objective"]),
                target_patterns=list(relationship_patterns),
                target_emotions=list(RELATIONSHIP_EXPLORATION_SPEC["target_emotions"]),
                estimated_duration=int(RELATIONSHIP_EXPLORATION_SPEC["estimated_duration"]),
                priority=int(RELATIONSHIP_EXPLORATION_SPEC["priority"]),
            )
        )

    for pattern_id in pattern_ids:
        spec = PATTERN_EXPLORATION_SPECS.get(pattern_id)
        if spec is None:
            continue
        phases.append(
            ScenarioPhase(
                objective=str(spec["objective"]),
                target_patterns=[pattern_id],
                target_emotions=list(spec["target_emotions"]),
                estimated_duration=int(spec["estimated_duration"]),
                priority=int(spec["priority"]),
            )
        )

    return sorted(
        phases,
        key=lambda phase: (phase.priority, phase.objective, tuple(phase.target_patterns)),
    )


def _build_integration_phase(pattern_ids: list[str]) -> ScenarioPhase:
    return ScenarioPhase(
        objective=DEFAULT_INTEGRATION_OBJECTIVE,
        target_patterns=list(pattern_ids),
        target_emotions=["reflection", "meaning"],
        estimated_duration=8,
        priority=2,
    )


def _build_closing_phase() -> ScenarioPhase:
    return ScenarioPhase(
        objective=DEFAULT_CLOSING_OBJECTIVE,
        target_patterns=[],
        target_emotions=["closure", "safety"],
        estimated_duration=5,
        priority=1,
    )
