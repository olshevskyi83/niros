from __future__ import annotations

from dataclasses import dataclass, field

from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    STRATEGY_CONFIDENCE_MEDIUM,
    InterventionStrategy,
    StrategyCoverageSummary,
    StrategyFocusConfidence,
)
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

FOCUS_AREA_PHASE_LABELS: dict[str, str] = {
    "presenting context": "session opening",
    "personality / pacing": "pacing and tone",
    "emotion regulation": "stabilization",
    "self-worth / self-criticism": "emotional opening",
    "relationships": "relationship exploration",
    "meaning / purpose": "integration",
    "emotional flexibility": "closing",
}

DEFAULT_SCENARIO_FRAMING: dict[str, str] = {
    STRATEGY_CONFIDENCE_HIGH: (
        "Use direct personalized framing grounded in available fingerprint evidence."
    ),
    STRATEGY_CONFIDENCE_MEDIUM: (
        "Use gentle personalized framing and avoid strong identity claims."
    ),
    STRATEGY_CONFIDENCE_LOW: (
        "Use open-ended exploratory framing and avoid strong assumptions."
    ),
}

FOCUS_AREA_SCENARIO_FRAMING: dict[str, dict[str, str]] = {
    "self-worth / self-criticism": {
        STRATEGY_CONFIDENCE_HIGH: (
            "Personalize self-worth themes with clear but non-judgmental language."
        ),
        STRATEGY_CONFIDENCE_MEDIUM: (
            "Use gentle exploratory language around self-worth instead of strong identity claims."
        ),
        STRATEGY_CONFIDENCE_LOW: (
            "Keep self-worth themes open-ended; avoid direct identity conclusions."
        ),
    },
    "emotion regulation": {
        STRATEGY_CONFIDENCE_HIGH: (
            "Personalize regulation support based on known patterns and capacity."
        ),
        STRATEGY_CONFIDENCE_MEDIUM: (
            "Offer grounding gently without assuming regulation capacity."
        ),
        STRATEGY_CONFIDENCE_LOW: (
            "Prioritize stabilization and avoid assuming regulation capacity is known."
        ),
    },
    "relationships": {
        STRATEGY_CONFIDENCE_LOW: (
            "Explore relationship themes tentatively without attachment-style labeling."
        ),
    },
    "meaning / purpose": {
        STRATEGY_CONFIDENCE_MEDIUM: (
            "Invite meaning exploration without prescribing beliefs or outcomes."
        ),
    },
}


@dataclass(frozen=True)
class ScenarioConfidencePhase:
    phase: str
    focus: str
    confidence: str
    source_domains: tuple[str, ...] = field(default_factory=tuple)
    framing: str = ""
    uncertainty_notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, str | tuple[str, ...]]:
        return {
            "phase": self.phase,
            "focus": self.focus,
            "confidence": self.confidence,
            "source_domains": self.source_domains,
            "framing": self.framing,
            "uncertainty_notes": self.uncertainty_notes,
        }


@dataclass(frozen=True)
class ScenarioConfidenceSummary:
    direct_personalization: tuple[str, ...] = field(default_factory=tuple)
    gentle_personalization: tuple[str, ...] = field(default_factory=tuple)
    exploratory_only: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "direct_personalization": self.direct_personalization,
            "gentle_personalization": self.gentle_personalization,
            "exploratory_only": self.exploratory_only,
        }


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
    confidence_phases: tuple[ScenarioConfidencePhase, ...] = field(default_factory=tuple)
    confidence_summary: ScenarioConfidenceSummary | None = None


def build_scenario_blueprint(
    human_profile: dict,
    *,
    intervention_strategy: InterventionStrategy | None = None,
) -> ScenarioBlueprint:
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

    confidence_phases: tuple[ScenarioConfidencePhase, ...] = ()
    confidence_summary: ScenarioConfidenceSummary | None = None
    if intervention_strategy is not None and intervention_strategy.focus_confidence:
        confidence_phases = _build_confidence_phases(intervention_strategy.focus_confidence)
        if intervention_strategy.coverage_summary is not None:
            confidence_summary = _build_scenario_confidence_summary(
                intervention_strategy.coverage_summary
            )

    return ScenarioBlueprint(
        opening_phase=opening,
        stabilization_phase=stabilization,
        exploration_phases=exploration_phases,
        integration_phase=integration,
        closing_phase=closing,
        confidence_phases=confidence_phases,
        confidence_summary=confidence_summary,
    )


def render_scenario_blueprint(blueprint: ScenarioBlueprint) -> str:
    lines = [
        "Scenario Blueprint",
        f"- Opening objective: {blueprint.opening_phase.objective}",
        f"- Stabilization objective: {blueprint.stabilization_phase.objective}",
        f"- Exploration phases: {len(blueprint.exploration_phases)}",
    ]
    for index, phase in enumerate(blueprint.exploration_phases, start=1):
        patterns = ", ".join(phase.target_patterns) if phase.target_patterns else "None"
        lines.append(f"  - Exploration {index} ({patterns}): {phase.objective}")
    lines.extend(
        [
            f"- Integration objective: {blueprint.integration_phase.objective}",
            f"- Closing objective: {blueprint.closing_phase.objective}",
        ]
    )

    if blueprint.confidence_summary is not None:
        lines.extend(_render_scenario_confidence_summary(blueprint.confidence_summary))

    if blueprint.confidence_phases:
        lines.append("Confidence-aware scenario themes:")
        for item in blueprint.confidence_phases:
            lines.append(f"- {item.phase}: {item.focus} ({item.confidence} confidence)")
            if item.source_domains:
                lines.append(f"  Source domains: {', '.join(item.source_domains)}")
            if item.framing:
                lines.append(f"  Framing: {item.framing}")
            for note in item.uncertainty_notes:
                lines.append(f"  - {note}")

    return "\n".join(lines)


def _build_confidence_phases(
    focus_confidence: tuple[StrategyFocusConfidence, ...],
) -> tuple[ScenarioConfidencePhase, ...]:
    phases: list[ScenarioConfidencePhase] = []
    for item in focus_confidence:
        phases.append(
            ScenarioConfidencePhase(
                phase=FOCUS_AREA_PHASE_LABELS.get(item.focus_area, item.focus_area),
                focus=item.focus_area,
                confidence=item.confidence,
                source_domains=item.based_on_domains,
                framing=_scenario_framing_for_focus(item.focus_area, item.confidence),
                uncertainty_notes=item.uncertainty_notes,
            )
        )
    return tuple(phases)


def _build_scenario_confidence_summary(
    coverage_summary: StrategyCoverageSummary,
) -> ScenarioConfidenceSummary:
    direct = list(coverage_summary.high_confidence)
    if "Big Five" in direct:
        direct = ["Big Five-based pacing", *[
            label for label in direct if label != "Big Five"
        ]]
    return ScenarioConfidenceSummary(
        direct_personalization=tuple(direct),
        gentle_personalization=coverage_summary.medium_confidence,
        exploratory_only=coverage_summary.low_confidence,
    )


def _scenario_framing_for_focus(focus_area: str, confidence: str) -> str:
    focus_framing = FOCUS_AREA_SCENARIO_FRAMING.get(focus_area, {})
    return focus_framing.get(confidence, DEFAULT_SCENARIO_FRAMING[confidence])


def _render_scenario_confidence_summary(summary: ScenarioConfidenceSummary) -> list[str]:
    lines = ["Scenario Confidence Summary"]

    lines.append("Direct personalization:")
    if summary.direct_personalization:
        lines.extend(f"- {label}" for label in summary.direct_personalization)
    else:
        lines.append("- (none)")

    lines.append("Gentle personalization:")
    if summary.gentle_personalization:
        lines.extend(f"- {label}" for label in summary.gentle_personalization)
    else:
        lines.append("- (none)")

    lines.append("Exploratory only:")
    if summary.exploratory_only:
        lines.extend(f"- {label}" for label in summary.exploratory_only)
    else:
        lines.append("- (none)")

    return lines


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
