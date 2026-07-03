from __future__ import annotations

from dataclasses import dataclass, field

LEVEL_RANK: dict[str, int] = {
    "low": 0,
    "gradual": 1,
    "low_to_medium": 1,
    "medium": 2,
    "medium_to_high": 3,
    "high": 4,
    "very_high": 5,
}

PACING_RANK: dict[str, int] = {
    "slow": 0,
    "moderate": 1,
    "brisk": 2,
}

LEVEL_STEPS: tuple[str, ...] = (
    "low",
    "gradual",
    "low_to_medium",
    "medium",
    "medium_to_high",
    "high",
    "very_high",
)

SAFETY_PATTERN_IDS = frozenset(
    {
        "safety_concern_signal",
        "fear_of_bad_trip",
        "psychedelic_anxiety",
    }
)

DEFAULT_SUGGESTED_DURATION = 50
SHORTER_SUGGESTED_DURATION = 40
EMPTY_PROFILE_SUGGESTED_DURATION = 45


@dataclass(frozen=True)
class InterventionStrategy:
    pacing: str
    emotional_intensity: str
    metaphor_level: str
    directness: str
    repetition_level: str
    grounding_priority: str
    exploration_priority: str
    integration_priority: str
    body_focus: str
    relationship_focus: str
    self_focus: str
    spirituality_focus: str
    cognitive_load: str
    suggested_duration: int
    strategy_notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, str | int | tuple[str, ...]]:
        return {
            "pacing": self.pacing,
            "emotional_intensity": self.emotional_intensity,
            "metaphor_level": self.metaphor_level,
            "directness": self.directness,
            "repetition_level": self.repetition_level,
            "grounding_priority": self.grounding_priority,
            "exploration_priority": self.exploration_priority,
            "integration_priority": self.integration_priority,
            "body_focus": self.body_focus,
            "relationship_focus": self.relationship_focus,
            "self_focus": self.self_focus,
            "spirituality_focus": self.spirituality_focus,
            "cognitive_load": self.cognitive_load,
            "suggested_duration": self.suggested_duration,
            "strategy_notes": self.strategy_notes,
        }


DEFAULT_STRATEGY = InterventionStrategy(
    pacing="moderate",
    emotional_intensity="medium",
    metaphor_level="medium",
    directness="medium",
    repetition_level="medium",
    grounding_priority="medium",
    exploration_priority="medium",
    integration_priority="medium",
    body_focus="low",
    relationship_focus="low",
    self_focus="medium",
    spirituality_focus="low",
    cognitive_load="medium",
    suggested_duration=DEFAULT_SUGGESTED_DURATION,
)

EMPTY_PROFILE_STRATEGY = InterventionStrategy(
    pacing="slow",
    emotional_intensity="low",
    metaphor_level="low",
    directness="medium",
    repetition_level="medium",
    grounding_priority="high",
    exploration_priority="low",
    integration_priority="medium",
    body_focus="low",
    relationship_focus="low",
    self_focus="medium",
    spirituality_focus="low",
    cognitive_load="low",
    suggested_duration=EMPTY_PROFILE_SUGGESTED_DURATION,
    strategy_notes=(
        "Limited profile evidence: use a grounding-first, low-stimulation session frame.",
    ),
)

PatternAdjustment = dict[str, str | int]

PATTERN_STRATEGY_ADJUSTMENTS: dict[str, PatternAdjustment] = {
    "existential_fear": {
        "pacing": "slow",
        "emotional_intensity": "low_to_medium",
        "metaphor_level": "medium",
        "directness": "low",
        "grounding_priority": "high",
        "cognitive_load": "low",
        "note": "Ground before exploring existential themes.",
    },
    "safety_concern_signal": {
        "grounding_priority": "very_high",
        "exploration_priority": "low",
        "emotional_intensity": "low",
        "directness": "low",
        "note": "Safety and steadiness take precedence over exploration.",
    },
    "emotional_distress_signal": {
        "grounding_priority": "high",
        "integration_priority": "medium",
        "emotional_intensity": "low_to_medium",
        "note": "Support reported distress with paced grounding and integration space.",
    },
    "chronic_stress_signal": {
        "pacing": "slow",
        "repetition_level": "high",
        "body_focus": "medium",
        "cognitive_load": "low",
        "note": "Use steady repetition and body-aware pacing for chronic stress.",
    },
    "nightmare_disturbance": {
        "pacing": "slow",
        "grounding_priority": "high",
        "emotional_intensity": "low",
        "integration_priority": "medium",
        "note": "Keep nightmare-related work gentle and grounding-led.",
    },
    "sleep_disruption": {
        "pacing": "slow",
        "grounding_priority": "high",
        "emotional_intensity": "low",
        "integration_priority": "medium",
        "note": "Prioritize regulation before sleep-related exploration.",
    },
    "fibromyalgia_signal": {
        "pacing": "slow",
        "body_focus": "high",
        "emotional_intensity": "low",
        "cognitive_load": "low",
        "duration_modifier": "shorter",
        "note": "Body-centered pacing with reduced stimulation.",
    },
    "chronic_pain_burden": {
        "pacing": "slow",
        "body_focus": "high",
        "emotional_intensity": "low",
        "cognitive_load": "low",
        "duration_modifier": "shorter",
        "note": "Body-centered pacing with reduced stimulation.",
    },
    "fatigue_burden": {
        "pacing": "slow",
        "emotional_intensity": "low",
        "cognitive_load": "low",
        "duration_modifier": "shorter",
        "note": "Keep session load low when fatigue burden is reported.",
    },
    "speech_anxiety": {
        "directness": "low",
        "repetition_level": "high",
        "emotional_intensity": "low",
        "self_focus": "medium",
        "note": "Use gentle repetition and low directness around speech themes.",
    },
    "stuttering_signal": {
        "directness": "low",
        "repetition_level": "high",
        "emotional_intensity": "low",
        "self_focus": "medium",
        "note": "Use gentle repetition and low directness around speech themes.",
    },
    "fear_of_speaking": {
        "directness": "low",
        "repetition_level": "high",
        "emotional_intensity": "low",
        "self_focus": "medium",
    },
    "psychedelic_anxiety": {
        "grounding_priority": "very_high",
        "exploration_priority": "low_to_medium",
        "directness": "low",
        "metaphor_level": "low_to_medium",
        "note": "Ground first; allow only gradual exploration.",
    },
    "fear_of_bad_trip": {
        "grounding_priority": "very_high",
        "exploration_priority": "low_to_medium",
        "directness": "low",
        "metaphor_level": "low_to_medium",
        "note": "Ground first; allow only gradual exploration.",
    },
    "surrender_difficulty": {
        "pacing": "slow",
        "repetition_level": "high",
        "metaphor_level": "medium",
        "directness": "low",
        "exploration_priority": "gradual",
        "note": "Build trust through repetition before inviting surrender.",
    },
    "control_resistance": {
        "pacing": "slow",
        "repetition_level": "high",
        "metaphor_level": "medium",
        "directness": "low",
        "exploration_priority": "gradual",
        "note": "Build trust through repetition before inviting surrender.",
    },
    "meaning_seeking": {
        "spirituality_focus": "medium_to_high",
        "metaphor_level": "medium_to_high",
        "integration_priority": "high",
        "note": "Support meaning and integration without prescribing beliefs.",
    },
    "loss_of_meaning": {
        "spirituality_focus": "medium_to_high",
        "metaphor_level": "medium_to_high",
        "integration_priority": "high",
        "note": "Support meaning and integration without prescribing beliefs.",
    },
    "desire_for_change": {
        "exploration_priority": "medium",
        "integration_priority": "high",
        "note": "Link exploration to practical integration of desired change.",
    },
}

MERGE_HIGHEST = frozenset(
    {
        "grounding_priority",
        "integration_priority",
        "body_focus",
        "relationship_focus",
        "self_focus",
        "spirituality_focus",
        "repetition_level",
    }
)

MERGE_LOWEST = frozenset(
    {
        "emotional_intensity",
        "cognitive_load",
        "directness",
        "exploration_priority",
    }
)


def build_intervention_strategy(fingerprint_or_profile: dict) -> InterventionStrategy:
    pattern_ids = _extract_pattern_ids(fingerprint_or_profile)
    if not pattern_ids and not _extract_assessment_results(fingerprint_or_profile):
        return EMPTY_PROFILE_STRATEGY

    merged, notes = _merge_pattern_adjustments(pattern_ids)
    merged, notes = _apply_assessment_adjustments(
        merged,
        notes,
        _extract_assessment_results(fingerprint_or_profile),
        pattern_ids,
    )
    duration = _compute_duration(
        pattern_ids,
        use_shorter=bool(merged.pop("use_shorter_duration", False)),
    )
    return _build_strategy_from_merged(merged, duration, notes)


def render_intervention_strategy(strategy: InterventionStrategy) -> str:
    lines = [
        "=== NIROS Intervention Strategy ===",
        f"Pacing: {strategy.pacing}",
        f"Emotional intensity: {strategy.emotional_intensity}",
        f"Metaphor level: {strategy.metaphor_level}",
        f"Directness: {strategy.directness}",
        f"Repetition: {strategy.repetition_level}",
        f"Grounding priority: {strategy.grounding_priority}",
        f"Exploration priority: {strategy.exploration_priority}",
        f"Integration priority: {strategy.integration_priority}",
        f"Body focus: {strategy.body_focus}",
        f"Relationship focus: {strategy.relationship_focus}",
        f"Self focus: {strategy.self_focus}",
        f"Spirituality focus: {strategy.spirituality_focus}",
        f"Cognitive load: {strategy.cognitive_load}",
        f"Suggested duration: {strategy.suggested_duration} minutes",
        "Notes:",
    ]
    if strategy.strategy_notes:
        lines.extend(f"- {note}" for note in strategy.strategy_notes)
    else:
        lines.append("- None noted.")
    return "\n".join(lines)


def is_high_grounding(value: str) -> bool:
    return value in {"high", "very_high"}


def _extract_pattern_ids(fingerprint_or_profile: dict) -> list[str]:
    profile_data = fingerprint_or_profile
    if "patterns" in fingerprint_or_profile and isinstance(fingerprint_or_profile["patterns"], dict):
        profile_data = fingerprint_or_profile["patterns"]

    pattern_counts = profile_data.get("pattern_counts") or {}
    if pattern_counts:
        return sorted(
            pattern_counts,
            key=lambda pattern_id: (-pattern_counts[pattern_id], pattern_id),
        )

    ranked: list[str] = []
    primary = profile_data.get("primary_pattern")
    if primary is not None:
        ranked.append(primary["canonical_id"])

    for pattern in profile_data.get("secondary_patterns") or []:
        canonical_id = pattern["canonical_id"]
        if canonical_id not in ranked:
            ranked.append(canonical_id)

    return ranked


def _merge_pattern_adjustments(pattern_ids: list[str]) -> tuple[dict[str, str | bool], tuple[str, ...]]:
    merged: dict[str, str | bool] = {
        "pacing": DEFAULT_STRATEGY.pacing,
        "emotional_intensity": DEFAULT_STRATEGY.emotional_intensity,
        "metaphor_level": DEFAULT_STRATEGY.metaphor_level,
        "directness": DEFAULT_STRATEGY.directness,
        "repetition_level": DEFAULT_STRATEGY.repetition_level,
        "grounding_priority": DEFAULT_STRATEGY.grounding_priority,
        "exploration_priority": DEFAULT_STRATEGY.exploration_priority,
        "integration_priority": DEFAULT_STRATEGY.integration_priority,
        "body_focus": DEFAULT_STRATEGY.body_focus,
        "relationship_focus": DEFAULT_STRATEGY.relationship_focus,
        "self_focus": DEFAULT_STRATEGY.self_focus,
        "spirituality_focus": DEFAULT_STRATEGY.spirituality_focus,
        "cognitive_load": DEFAULT_STRATEGY.cognitive_load,
        "use_shorter_duration": False,
    }
    notes: list[str] = []

    for pattern_id in sorted(pattern_ids):
        adjustment = PATTERN_STRATEGY_ADJUSTMENTS.get(pattern_id)
        if adjustment is None:
            continue
        for field, value in adjustment.items():
            if field == "note":
                note = str(value)
                if note not in notes:
                    notes.append(note)
                continue
            if field == "duration_modifier" and value == "shorter":
                merged["use_shorter_duration"] = True
                continue
            if field == "pacing":
                merged["pacing"] = _merge_pacing(str(merged["pacing"]), str(value))
                continue
            if field == "metaphor_level":
                merged["metaphor_level"] = _merge_metaphor(str(merged["metaphor_level"]), str(value))
                continue
            if field in MERGE_HIGHEST:
                merged[field] = _merge_highest(str(merged[field]), str(value))
            elif field in MERGE_LOWEST:
                merged[field] = _merge_lowest(str(merged[field]), str(value))
            else:
                merged[field] = str(value)

    return merged, tuple(notes)


def _build_strategy_from_merged(
    merged: dict[str, str | bool],
    duration: int,
    notes: tuple[str, ...],
) -> InterventionStrategy:
    return InterventionStrategy(
        pacing=str(merged["pacing"]),
        emotional_intensity=str(merged["emotional_intensity"]),
        metaphor_level=str(merged["metaphor_level"]),
        directness=str(merged["directness"]),
        repetition_level=str(merged["repetition_level"]),
        grounding_priority=str(merged["grounding_priority"]),
        exploration_priority=str(merged["exploration_priority"]),
        integration_priority=str(merged["integration_priority"]),
        body_focus=str(merged["body_focus"]),
        relationship_focus=str(merged["relationship_focus"]),
        self_focus=str(merged["self_focus"]),
        spirituality_focus=str(merged["spirituality_focus"]),
        cognitive_load=str(merged["cognitive_load"]),
        suggested_duration=duration,
        strategy_notes=notes,
    )


def _compute_duration(pattern_ids: list[str], *, use_shorter: bool) -> int:
    if use_shorter:
        duration = SHORTER_SUGGESTED_DURATION
    else:
        duration = DEFAULT_SUGGESTED_DURATION
    if len(pattern_ids) >= 4:
        duration += 5
    return max(30, min(duration, 90))


def _merge_highest(current: str, incoming: str) -> str:
    if LEVEL_RANK[incoming] >= LEVEL_RANK[current]:
        return incoming
    return current


def _merge_lowest(current: str, incoming: str) -> str:
    if LEVEL_RANK[incoming] <= LEVEL_RANK[current]:
        return incoming
    return current


def _merge_pacing(current: str, incoming: str) -> str:
    if PACING_RANK[incoming] <= PACING_RANK[current]:
        return incoming
    return current


def _merge_metaphor(current: str, incoming: str) -> str:
    if LEVEL_RANK[incoming] < LEVEL_RANK[current]:
        return incoming
    return _merge_highest(current, incoming)


def _extract_assessment_results(fingerprint_or_profile: dict) -> list[dict[str, str | float]]:
    results = fingerprint_or_profile.get("assessment_results")
    if isinstance(results, list):
        return [result for result in results if isinstance(result, dict)]
    return []


def _assessment_level(
    assessment_results: list[dict[str, str | float]],
    domain_id: str,
) -> str | None:
    for result in assessment_results:
        if result.get("domain_id") == domain_id:
            return str(result.get("interpretation"))
    return None


def _apply_assessment_adjustments(
    merged: dict[str, str | bool],
    notes: tuple[str, ...],
    assessment_results: list[dict[str, str | float]],
    pattern_ids: list[str],
) -> tuple[dict[str, str | bool], tuple[str, ...]]:
    if not assessment_results:
        return merged, notes

    note_list = list(notes)

    if _assessment_level(assessment_results, "neuroticism") == "elevated":
        merged["grounding_priority"] = _bump_level(str(merged["grounding_priority"]), 1)
        merged["emotional_intensity"] = _merge_lowest(
            str(merged["emotional_intensity"]),
            "medium_to_high",
        )
        merged["cognitive_load"] = _merge_lowest(str(merged["cognitive_load"]), "low")
        note = "Elevated self-reported neuroticism: keep grounding high and cognitive load low."
        if note not in note_list:
            note_list.append(note)

    if (
        _assessment_level(assessment_results, "openness") == "elevated"
        and not _safety_patterns_high(pattern_ids, merged)
    ):
        merged["metaphor_level"] = _bump_level(str(merged["metaphor_level"]), 1)
        note = "Elevated self-reported openness: metaphor may increase when safety is steady."
        if note not in note_list:
            note_list.append(note)

    if (
        _assessment_level(assessment_results, "conscientiousness") == "elevated"
        and "control_resistance" in pattern_ids
    ):
        merged["directness"] = _merge_lowest(str(merged["directness"]), "low")
        merged["pacing"] = _merge_pacing(str(merged["pacing"]), "slow")
        merged["repetition_level"] = _merge_highest(str(merged["repetition_level"]), "high")
        note = "Elevated conscientiousness with control resistance: use slow, repetitive pacing."
        if note not in note_list:
            note_list.append(note)

    return merged, tuple(note_list)


def _safety_patterns_high(pattern_ids: list[str], merged: dict[str, str | bool]) -> bool:
    if any(pattern_id in SAFETY_PATTERN_IDS for pattern_id in pattern_ids):
        return True
    return is_high_grounding(str(merged.get("grounding_priority", "medium")))


def _bump_level(current: str, steps: int = 1) -> str:
    if current not in LEVEL_STEPS:
        return current
    index = LEVEL_STEPS.index(current)
    return LEVEL_STEPS[min(index + steps, len(LEVEL_STEPS) - 1)]
