from __future__ import annotations

from dataclasses import dataclass, field

from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_GOOD,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    COVERAGE_REPORT_DOMAIN_ORDER,
    FingerprintCoverageReport,
    PROFILE_DOMAIN_DISPLAY_LABELS,
)

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

STRATEGY_CONFIDENCE_HIGH = "high"
STRATEGY_CONFIDENCE_MEDIUM = "medium"
STRATEGY_CONFIDENCE_LOW = "low"

STRATEGY_CONFIDENCE_RANK: dict[str, int] = {
    STRATEGY_CONFIDENCE_LOW: 0,
    STRATEGY_CONFIDENCE_MEDIUM: 1,
    STRATEGY_CONFIDENCE_HIGH: 2,
}

STRATEGY_FOCUS_AREAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("presenting context", ("presenting_problem", "patterns")),
    ("personality / pacing", ("big_five",)),
    ("self-worth / self-criticism", ("self_domain", "cognitive_patterns_domain")),
    ("emotion regulation", ("emotion_regulation_domain",)),
    ("relationships", ("relationships_domain",)),
    ("meaning / purpose", ("meaning", "values_identity_domain")),
    ("spirituality / worldview", ("spirituality_worldview", "meaning")),
    ("emotional flexibility", ("emotional_flexibility_domain",)),
)


@dataclass(frozen=True)
class StrategyFocusConfidence:
    focus_area: str
    confidence: str
    based_on_domains: tuple[str, ...] = field(default_factory=tuple)
    uncertainty_notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, str | tuple[str, ...]]:
        return {
            "focus_area": self.focus_area,
            "confidence": self.confidence,
            "based_on_domains": self.based_on_domains,
            "uncertainty_notes": self.uncertainty_notes,
        }


@dataclass(frozen=True)
class StrategyCoverageSummary:
    high_confidence: tuple[str, ...] = field(default_factory=tuple)
    medium_confidence: tuple[str, ...] = field(default_factory=tuple)
    low_confidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "high_confidence": self.high_confidence,
            "medium_confidence": self.medium_confidence,
            "low_confidence": self.low_confidence,
        }


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
    focus_confidence: tuple[StrategyFocusConfidence, ...] = field(default_factory=tuple)
    coverage_summary: StrategyCoverageSummary | None = None

    def to_dict(self) -> dict[str, str | int | tuple[str, ...] | dict[str, tuple[str, ...]] | list[dict[str, str | tuple[str, ...]]] | None]:
        payload: dict[str, str | int | tuple[str, ...] | dict[str, tuple[str, ...]] | list[dict[str, str | tuple[str, ...]]] | None] = {
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
            "focus_confidence": [item.to_dict() for item in self.focus_confidence],
            "coverage_summary": self.coverage_summary.to_dict() if self.coverage_summary else None,
        }
        return payload


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


def build_intervention_strategy(
    fingerprint_or_profile: dict,
    *,
    fingerprint_coverage_report: FingerprintCoverageReport | None = None,
) -> InterventionStrategy:
    coverage_report = fingerprint_coverage_report or _extract_coverage_report(fingerprint_or_profile)
    pattern_ids = _extract_pattern_ids(fingerprint_or_profile)
    if not pattern_ids and not _extract_assessment_results(fingerprint_or_profile):
        strategy = EMPTY_PROFILE_STRATEGY
        if coverage_report is not None:
            return _attach_coverage_context(strategy, coverage_report)
        return strategy

    merged, notes = _merge_pattern_adjustments(pattern_ids)
    merged, notes = _apply_assessment_adjustments(
        merged,
        notes,
        _extract_assessment_results(fingerprint_or_profile),
        pattern_ids,
    )
    if coverage_report is not None:
        merged, notes = _apply_coverage_adjustments(merged, notes, coverage_report)
    merged, notes = _apply_worldview_profile_notes(fingerprint_or_profile, merged, notes)
    duration = _compute_duration(
        pattern_ids,
        use_shorter=bool(merged.pop("use_shorter_duration", False)),
    )
    strategy = _build_strategy_from_merged(merged, duration, notes)
    if coverage_report is not None:
        return _attach_coverage_context(strategy, coverage_report)
    return strategy


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
    ]
    if strategy.coverage_summary is not None:
        lines.extend(_render_strategy_confidence_summary(strategy))
    if strategy.focus_confidence:
        lines.append("Focus area confidence:")
        for item in strategy.focus_confidence:
            lines.append(f"- {item.focus_area}: {item.confidence}")
            if item.based_on_domains:
                lines.append(f"  Domains: {', '.join(item.based_on_domains)}")
            for note in item.uncertainty_notes:
                lines.append(f"  - {note}")
    lines.append("Notes:")
    if strategy.strategy_notes:
        lines.extend(f"- {note}" for note in strategy.strategy_notes)
    else:
        lines.append("- None noted.")
    return "\n".join(lines)


def is_high_grounding(value: str) -> bool:
    return value in {"high", "very_high"}


def coverage_level_to_strategy_confidence(level: str) -> str:
    if level in {COVERAGE_LEVEL_COMPLETE, COVERAGE_LEVEL_GOOD}:
        return STRATEGY_CONFIDENCE_HIGH
    if level == COVERAGE_LEVEL_PARTIAL:
        return STRATEGY_CONFIDENCE_MEDIUM
    return STRATEGY_CONFIDENCE_LOW


def _extract_coverage_report(fingerprint_or_profile: dict) -> FingerprintCoverageReport | None:
    report = fingerprint_or_profile.get("fingerprint_coverage_report")
    if isinstance(report, FingerprintCoverageReport):
        return report
    return None


def _domain_display_label(domain_id: str) -> str:
    return PROFILE_DOMAIN_DISPLAY_LABELS.get(
        domain_id,
        domain_id.replace("_", " ").title(),
    )


def _build_strategy_coverage_summary(
    coverage_report: FingerprintCoverageReport,
) -> StrategyCoverageSummary:
    high: list[str] = []
    medium: list[str] = []
    low: list[str] = []

    for domain_id in COVERAGE_REPORT_DOMAIN_ORDER:
        level = coverage_report.domains[domain_id].level
        label = _domain_display_label(domain_id)
        confidence = coverage_level_to_strategy_confidence(level)
        if confidence == STRATEGY_CONFIDENCE_HIGH:
            high.append(label)
        elif confidence == STRATEGY_CONFIDENCE_MEDIUM:
            medium.append(label)
        else:
            low.append(label)

    return StrategyCoverageSummary(
        high_confidence=tuple(high),
        medium_confidence=tuple(medium),
        low_confidence=tuple(low),
    )


def _build_focus_confidence(
    coverage_report: FingerprintCoverageReport,
) -> tuple[StrategyFocusConfidence, ...]:
    items: list[StrategyFocusConfidence] = []

    for focus_area, domain_ids in STRATEGY_FOCUS_AREAS:
        domain_labels = tuple(_domain_display_label(domain_id) for domain_id in domain_ids)
        domain_levels = [coverage_report.domains[domain_id].level for domain_id in domain_ids]
        confidence = min(
            (coverage_level_to_strategy_confidence(level) for level in domain_levels),
            key=lambda value: STRATEGY_CONFIDENCE_RANK[value],
        )
        uncertainty_notes = _uncertainty_notes_for_domains(
            focus_area=focus_area,
            domain_ids=domain_ids,
            coverage_report=coverage_report,
            confidence=confidence,
        )
        items.append(
            StrategyFocusConfidence(
                focus_area=focus_area,
                confidence=confidence,
                based_on_domains=domain_labels,
                uncertainty_notes=uncertainty_notes,
            )
        )

    return tuple(items)


def _uncertainty_notes_for_domains(
    *,
    focus_area: str,
    domain_ids: tuple[str, ...],
    coverage_report: FingerprintCoverageReport,
    confidence: str,
) -> tuple[str, ...]:
    notes: list[str] = []

    for domain_id in domain_ids:
        domain = coverage_report.domains[domain_id]
        label = _domain_display_label(domain_id)
        if domain.level == COVERAGE_LEVEL_PARTIAL:
            notes.append(f"{label} domain coverage is partial")
        elif domain.level == COVERAGE_LEVEL_UNKNOWN:
            notes.append(f"{label} domain coverage is unknown")

    if focus_area == "self-worth / self-criticism" and confidence != STRATEGY_CONFIDENCE_HIGH:
        notes.append(
            "Further clarification is recommended before strong self-focused framing"
        )
    if focus_area == "emotion regulation" and confidence == STRATEGY_CONFIDENCE_LOW:
        notes.append(
            "Do not assume regulation capacity is known; prioritize stabilization first"
        )
    if focus_area == "personality / pacing" and confidence == STRATEGY_CONFIDENCE_HIGH:
        notes.append("Big Five coverage supports confident tone and pacing choices")
    if focus_area == "spirituality / worldview" and confidence != STRATEGY_CONFIDENCE_HIGH:
        notes.append(
            "Use conservative symbolic language until worldview orientation is clearer"
        )

    return tuple(dict.fromkeys(notes))


def _apply_coverage_adjustments(
    merged: dict[str, str | bool],
    notes: tuple[str, ...],
    coverage_report: FingerprintCoverageReport,
) -> tuple[dict[str, str | bool], tuple[str, ...]]:
    note_list = list(notes)
    domains = coverage_report.domains

    self_level = domains["self_domain"].level
    if self_level == COVERAGE_LEVEL_UNKNOWN:
        merged["self_focus"] = _merge_lowest(str(merged["self_focus"]), "low")
        merged["exploration_priority"] = _merge_lowest(str(merged["exploration_priority"]), "gradual")
        note = (
            "Self domain coverage is limited: keep self-focused work exploratory "
            "and avoid overly confident self-worth framing."
        )
        if note not in note_list:
            note_list.append(note)
    elif self_level == COVERAGE_LEVEL_PARTIAL:
        merged["self_focus"] = _merge_lowest(str(merged["self_focus"]), "medium")
        note = "Self domain coverage is partial: phrase self-related recommendations carefully."
        if note not in note_list:
            note_list.append(note)

    emotion_level = domains["emotion_regulation_domain"].level
    if emotion_level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}:
        merged["grounding_priority"] = _merge_highest(str(merged["grounding_priority"]), "high")
        note = (
            "Emotion Regulation coverage is limited: emphasize grounding and stabilization "
            "before assuming regulation capacity."
        )
        if note not in note_list:
            note_list.append(note)

    relationships_level = domains["relationships_domain"].level
    if relationships_level == COVERAGE_LEVEL_UNKNOWN:
        merged["relationship_focus"] = _merge_lowest(str(merged["relationship_focus"]), "low")

    big_five_level = domains["big_five"].level
    if big_five_level in {COVERAGE_LEVEL_COMPLETE, COVERAGE_LEVEL_GOOD}:
        note = "Big Five coverage is strong: personality-informed pacing may be used confidently."
        if note not in note_list:
            note_list.append(note)

    worldview_level = domains["spirituality_worldview"].level
    if worldview_level == COVERAGE_LEVEL_UNKNOWN:
        merged["spirituality_focus"] = _merge_lowest(str(merged["spirituality_focus"]), "low")
        merged["metaphor_level"] = _merge_lowest(str(merged["metaphor_level"]), "low")
        note = (
            "Spirituality / Worldview is unknown: keep symbolic language conservative "
            "and avoid religious framing."
        )
        if note not in note_list:
            note_list.append(note)
    elif worldview_level == COVERAGE_LEVEL_PARTIAL:
        note = (
            "Spirituality / Worldview is partial: use cautious symbolic language "
            "until preferences are clearer."
        )
        if note not in note_list:
            note_list.append(note)

    return merged, tuple(note_list)


def _apply_worldview_profile_notes(
    fingerprint_or_profile: dict,
    merged: dict[str, str | bool],
    notes: tuple[str, ...],
) -> tuple[dict[str, str | bool], tuple[str, ...]]:
    from niros.spirituality_worldview import (
        COMFORT_AVOID,
        ORIENTATION_UNKNOWN,
        SpiritualityWorldviewProfile,
    )

    payload = fingerprint_or_profile.get("spirituality_worldview")
    if not payload:
        return merged, notes

    profile = SpiritualityWorldviewProfile.from_dict(payload)
    if profile.worldview_orientation == ORIENTATION_UNKNOWN:
        if not profile.symbolic_language_preferences and not profile.avoided_symbolic_language:
            return merged, notes

    note_list = list(notes)

    if profile.worldview_orientation != ORIENTATION_UNKNOWN:
        note_list.append(
            f"Worldview framing: {profile.worldview_orientation.replace('_', ' ')}"
        )
    if profile.symbolic_language_preferences:
        note_list.append(
            "Allowed symbolic language: "
            + ", ".join(profile.symbolic_language_preferences)
        )
    if profile.avoided_symbolic_language:
        note_list.append(
            "Avoided symbolic language: "
            + ", ".join(profile.avoided_symbolic_language)
        )
    if profile.icaros_language_constraints:
        note_list.append(
            "Future Icaro language constraints: "
            + "; ".join(profile.icaros_language_constraints)
        )
    if profile.religious_language_comfort == COMFORT_AVOID:
        merged["spirituality_focus"] = _merge_lowest(str(merged["spirituality_focus"]), "low")

    return merged, tuple(dict.fromkeys(note_list))


def _attach_coverage_context(
    strategy: InterventionStrategy,
    coverage_report: FingerprintCoverageReport,
) -> InterventionStrategy:
    return InterventionStrategy(
        pacing=strategy.pacing,
        emotional_intensity=strategy.emotional_intensity,
        metaphor_level=strategy.metaphor_level,
        directness=strategy.directness,
        repetition_level=strategy.repetition_level,
        grounding_priority=strategy.grounding_priority,
        exploration_priority=strategy.exploration_priority,
        integration_priority=strategy.integration_priority,
        body_focus=strategy.body_focus,
        relationship_focus=strategy.relationship_focus,
        self_focus=strategy.self_focus,
        spirituality_focus=strategy.spirituality_focus,
        cognitive_load=strategy.cognitive_load,
        suggested_duration=strategy.suggested_duration,
        strategy_notes=strategy.strategy_notes,
        focus_confidence=_build_focus_confidence(coverage_report),
        coverage_summary=_build_strategy_coverage_summary(coverage_report),
    )


def _render_strategy_confidence_summary(strategy: InterventionStrategy) -> list[str]:
    summary = strategy.coverage_summary
    if summary is None:
        return []

    lines = ["Strategy Confidence Summary"]
    lines.append("High confidence:")
    if summary.high_confidence:
        lines.extend(f"- {label}" for label in summary.high_confidence)
    else:
        lines.append("- (none)")

    lines.append("Medium confidence:")
    if summary.medium_confidence:
        lines.extend(f"- {label}" for label in summary.medium_confidence)
    else:
        lines.append("- (none)")

    lines.append("Low confidence / exploratory:")
    if summary.low_confidence:
        lines.extend(f"- {label}" for label in summary.low_confidence)
    else:
        lines.append("- (none)")

    return lines


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
