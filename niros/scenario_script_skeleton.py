from __future__ import annotations

from dataclasses import dataclass, field

from niros.scenario_blueprint import ScenarioBlueprint, ScenarioPhase

OPENING_PHASE_NAME = "opening"
STABILIZATION_PHASE_NAME = "stabilization"
EXPLORATION_PHASE_NAME = "exploration"
INTEGRATION_PHASE_NAME = "integration"
CLOSING_PHASE_NAME = "closing"

RELATIONSHIP_PATTERN_IDS = frozenset(
    {
        "attachment_anxiety",
        "boundary_difficulty",
        "conflict_avoidance",
        "fear_of_disappointing_others",
        "fear_of_rejection",
        "people_pleasing",
        "trust_difficulty",
    }
)

SELF_WORTH_PATTERN_IDS = frozenset(
    {
        "self_worth_instability",
        "shame_sensitivity",
        "harsh_self_criticism",
    }
)

PATTERN_MUSICAL_DIRECTIONS: dict[str, str] = {
    "rumination": "spacious / repetitive / releasing",
    "emotional_suppression": "expressive / rising",
    "perfectionism": "flexible / fluid",
}

DEFAULT_EXPLORATION_MUSICAL_DIRECTION = "spacious / neutral"
RELATIONSHIP_MUSICAL_DIRECTION = "holding / relational"
SELF_WORTH_MUSICAL_DIRECTION = "compassionate / warm"

HIGH_PRIORITY_THRESHOLD = 1
MEDIUM_PRIORITY_THRESHOLD = 2


@dataclass(frozen=True)
class ScenarioSegment:
    phase_name: str
    objective: str
    target_patterns: list[str] = field(default_factory=list)
    target_emotions: list[str] = field(default_factory=list)
    estimated_duration: int = 0
    intensity: str = ""
    musical_direction: str = ""
    vocal_direction: str = ""
    silence_ratio: str = ""
    transition_notes: str = ""


@dataclass(frozen=True)
class ScenarioScriptSkeleton:
    title: str
    total_estimated_duration: int
    segments: list[ScenarioSegment]


def build_scenario_script_skeleton(blueprint: ScenarioBlueprint) -> ScenarioScriptSkeleton:
    segments: list[ScenarioSegment] = []

    ordered_phases: list[tuple[str, ScenarioPhase]] = [
        (OPENING_PHASE_NAME, blueprint.opening_phase),
        (STABILIZATION_PHASE_NAME, blueprint.stabilization_phase),
    ]
    for index, phase in enumerate(blueprint.exploration_phases, start=1):
        phase_name = EXPLORATION_PHASE_NAME
        if len(blueprint.exploration_phases) > 1:
            phase_name = f"{EXPLORATION_PHASE_NAME}_{index}"
        ordered_phases.append((phase_name, phase))
    ordered_phases.extend(
        [
            (INTEGRATION_PHASE_NAME, blueprint.integration_phase),
            (CLOSING_PHASE_NAME, blueprint.closing_phase),
        ]
    )

    for index, (phase_name, phase) in enumerate(ordered_phases):
        next_phase_name = (
            ordered_phases[index + 1][0] if index + 1 < len(ordered_phases) else None
        )
        segments.append(
            _segment_from_phase(
                phase_name=phase_name,
                phase=phase,
                next_phase_name=next_phase_name,
            )
        )

    total_duration = sum(segment.estimated_duration for segment in segments)
    return ScenarioScriptSkeleton(
        title=_build_title(blueprint),
        total_estimated_duration=total_duration,
        segments=segments,
    )


def _segment_from_phase(
    *,
    phase_name: str,
    phase: ScenarioPhase,
    next_phase_name: str | None,
) -> ScenarioSegment:
    if phase_name == OPENING_PHASE_NAME:
        return ScenarioSegment(
            phase_name=phase_name,
            objective=phase.objective,
            target_patterns=list(phase.target_patterns),
            target_emotions=list(phase.target_emotions),
            estimated_duration=phase.estimated_duration,
            intensity="low",
            musical_direction="grounding",
            vocal_direction="soft / invitational",
            silence_ratio="high",
            transition_notes=_transition_note(phase_name, next_phase_name),
        )

    if phase_name == STABILIZATION_PHASE_NAME:
        return ScenarioSegment(
            phase_name=phase_name,
            objective=phase.objective,
            target_patterns=list(phase.target_patterns),
            target_emotions=list(phase.target_emotions),
            estimated_duration=phase.estimated_duration,
            intensity="low_to_medium",
            musical_direction="steady / regulating",
            vocal_direction="calm / repetitive",
            silence_ratio="medium",
            transition_notes=_transition_note(phase_name, next_phase_name),
        )

    if phase_name.startswith(EXPLORATION_PHASE_NAME):
        return ScenarioSegment(
            phase_name=phase_name,
            objective=phase.objective,
            target_patterns=list(phase.target_patterns),
            target_emotions=list(phase.target_emotions),
            estimated_duration=phase.estimated_duration,
            intensity=_exploration_intensity(phase.priority),
            musical_direction=_exploration_musical_direction(phase.target_patterns),
            vocal_direction=_exploration_vocal_direction(phase.target_patterns),
            silence_ratio="medium",
            transition_notes=_transition_note(phase_name, next_phase_name),
        )

    if phase_name == INTEGRATION_PHASE_NAME:
        return ScenarioSegment(
            phase_name=phase_name,
            objective=phase.objective,
            target_patterns=list(phase.target_patterns),
            target_emotions=list(phase.target_emotions),
            estimated_duration=phase.estimated_duration,
            intensity="medium_to_low",
            musical_direction="integrating / coherent",
            vocal_direction="reassuring / simple",
            silence_ratio="medium",
            transition_notes=_transition_note(phase_name, next_phase_name),
        )

    return ScenarioSegment(
        phase_name=phase_name,
        objective=phase.objective,
        target_patterns=list(phase.target_patterns),
        target_emotions=list(phase.target_emotions),
        estimated_duration=phase.estimated_duration,
        intensity="low",
        musical_direction="grounding / settling",
        vocal_direction="minimal",
        silence_ratio="high",
        transition_notes=_transition_note(phase_name, next_phase_name),
    )


def _exploration_intensity(priority: int) -> str:
    if priority <= HIGH_PRIORITY_THRESHOLD:
        return "medium_to_high"
    if priority <= MEDIUM_PRIORITY_THRESHOLD:
        return "medium"
    return "medium_to_low"


def _exploration_musical_direction(target_patterns: list[str]) -> str:
    for pattern_id in sorted(target_patterns):
        if pattern_id in PATTERN_MUSICAL_DIRECTIONS:
            return PATTERN_MUSICAL_DIRECTIONS[pattern_id]
        if pattern_id in SELF_WORTH_PATTERN_IDS:
            return SELF_WORTH_MUSICAL_DIRECTION
        if pattern_id in RELATIONSHIP_PATTERN_IDS:
            return RELATIONSHIP_MUSICAL_DIRECTION
    return DEFAULT_EXPLORATION_MUSICAL_DIRECTION


def _exploration_vocal_direction(target_patterns: list[str]) -> str:
    if any(pattern_id in SELF_WORTH_PATTERN_IDS for pattern_id in target_patterns):
        return "gentle / affirming"
    if any(pattern_id in RELATIONSHIP_PATTERN_IDS for pattern_id in target_patterns):
        return "steady / relational"
    if "rumination" in target_patterns:
        return "spacious / minimal"
    if "emotional_suppression" in target_patterns:
        return "inviting / expressive"
    if "perfectionism" in target_patterns:
        return "flexible / permissive"
    return "supportive / neutral"


def _transition_note(current_phase_name: str, next_phase_name: str | None) -> str:
    if next_phase_name is None:
        return "End session after closing segment."

    return (
        f"Transition from {current_phase_name} to {next_phase_name} "
        "with gradual pacing adjustment."
    )


def _build_title(blueprint: ScenarioBlueprint) -> str:
    pattern_ids: list[str] = []
    for phase in blueprint.exploration_phases:
        pattern_ids.extend(phase.target_patterns)
    unique_patterns = sorted(set(pattern_ids))

    if not unique_patterns:
        return "General Therapeutic Session Skeleton"

    if len(unique_patterns) == 1:
        label = unique_patterns[0].replace("_", " ")
        return f"Therapeutic Session Skeleton ({label})"

    return "Therapeutic Session Skeleton (multi-pattern)"
