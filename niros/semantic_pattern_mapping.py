from __future__ import annotations

from dataclasses import dataclass

from niros.semantic_interpreter.facts import SemanticFact

FactPatternRule = tuple[str, str, frozenset[str], tuple[str, ...]]

PRESENT_VALUES = frozenset({"present", "elevated", "reduced", "avoidant", "seeking"})

DEPRESSED_MOOD_SUPPORTING_FACTS: tuple[tuple[str, str], ...] = (
    ("body", "appetite_loss"),
    ("social", "social_withdrawal"),
    ("sleep", "insomnia"),
    ("sleep", "sleep_disruption"),
    ("sleep", "nightmares"),
    ("self", "perceived_helplessness"),
)


@dataclass(frozen=True)
class SemanticPatternMatch:
    canonical_id: str
    matched_text: str
    confidence: float
    fact_index: int


FACT_PATTERN_RULES: tuple[FactPatternRule, ...] = (
    (
        "emotion",
        "reported_distress",
        frozenset({"present", "elevated"}),
        ("emotional_distress_signal",),
    ),
    (
        "emotion",
        "reported_fear",
        frozenset({"present", "elevated"}),
        ("generalized_fear", "emotional_distress_signal"),
    ),
    (
        "emotion",
        "chronic_stress",
        frozenset({"present", "elevated"}),
        ("chronic_stress_signal", "emotional_distress_signal"),
    ),
    (
        "emotion",
        "reported_low_mood",
        frozenset({"present", "elevated"}),
        ("low_mood_signal",),
    ),
    (
        "self",
        "clinical_label_self_report",
        frozenset({"depression"}),
        ("self_reported_depression_concern",),
    ),
    (
        "self",
        "unworthiness",
        frozenset({"present", "elevated"}),
        ("unworthiness_signal", "self_worth_instability"),
    ),
    (
        "self",
        "self_worth",
        frozenset({"low", "unstable", "reduced", "weak"}),
        ("self_worth_instability", "unworthiness_signal"),
    ),
    (
        "social",
        "belonging",
        frozenset({"low", "reduced", "weak", "absent"}),
        ("social_disconnection_signal",),
    ),
    (
        "social",
        "feeling_unwanted",
        frozenset({"present", "elevated"}),
        ("social_disconnection_signal", "rejection_sensitivity"),
    ),
    (
        "treatment",
        "medication_history",
        frozenset({"present", "elevated"}),
        ("medication_history",),
    ),
    (
        "treatment",
        "negative_medication_experience",
        frozenset({"present", "elevated"}),
        ("negative_medication_experience",),
    ),
    (
        "treatment",
        "low_response",
        frozenset({"present", "elevated"}),
        ("low_treatment_response_signal",),
    ),
    (
        "body",
        "pain_burden",
        frozenset({"present", "elevated"}),
        ("chronic_pain_burden",),
    ),
    (
        "body",
        "reported_pain",
        frozenset({"present", "elevated"}),
        ("chronic_pain_burden",),
    ),
    (
        "body",
        "reported_fatigue",
        frozenset({"present", "elevated"}),
        ("fatigue_burden",),
    ),
    (
        "body",
        "reported_distress",
        frozenset({"present", "elevated"}),
        ("fatigue_burden", "emotional_distress_signal"),
    ),
    (
        "sleep",
        "nightmares",
        frozenset({"present", "elevated"}),
        ("nightmare_disturbance", "sleep_disruption"),
    ),
    (
        "speech",
        "stuttering",
        frozenset({"present", "elevated"}),
        ("speech_anxiety", "communication_avoidance"),
    ),
    (
        "speech",
        "speech_comfort",
        frozenset({"reduced", "blocked", "low"}),
        ("speech_anxiety", "communication_avoidance"),
    ),
    (
        "session",
        "fear_of_bad_trip",
        frozenset({"present", "elevated"}),
        ("fear_of_bad_trip", "psychedelic_anxiety"),
    ),
    (
        "psychedelic",
        "fear_of_bad_trip",
        frozenset({"present", "elevated"}),
        ("fear_of_bad_trip", "psychedelic_anxiety"),
    ),
    (
        "self",
        "perceived_helplessness",
        frozenset({"present", "elevated"}),
        ("hopelessness_signal", "emotional_distress_signal"),
    ),
    (
        "trauma",
        "trauma_stress",
        frozenset({"present", "elevated"}),
        ("chronic_stress_signal", "emotional_distress_signal"),
    ),
    (
        "life_event",
        "bereavement",
        frozenset({"present", "elevated"}),
        ("bereavement_context", "loss_related_distress"),
    ),
    (
        "life_event",
        "loss",
        frozenset({"present", "elevated"}),
        ("loss_related_distress", "grief_signal"),
    ),
    (
        "relationship",
        "breakup",
        frozenset({"present", "elevated"}),
        ("relationship_breakup_context",),
    ),
    (
        "relationship",
        "separation",
        frozenset({"present", "elevated"}),
        ("attachment_loss_signal", "separation_distress"),
    ),
    (
        "relationship",
        "abandonment",
        frozenset({"present", "elevated"}),
        ("abandonment_wound_signal",),
    ),
    (
        "emotion",
        "separation_distress",
        frozenset({"present", "elevated"}),
        ("separation_distress",),
    ),
    (
        "emotion",
        "grief",
        frozenset({"present", "elevated"}),
        ("grief_signal", "loss_related_distress"),
    ),
    (
        "emotion",
        "loss_related_distress",
        frozenset({"present", "elevated"}),
        ("loss_related_distress", "grief_signal"),
    ),
    (
        "substance",
        "substance_use",
        frozenset({"present", "elevated"}),
        ("substance_use_pattern", "drug_use_concern"),
    ),
    (
        "substance",
        "drug_use_concern",
        frozenset({"present", "elevated"}),
        ("drug_use_concern", "substance_use_pattern"),
    ),
    (
        "substance",
        "addiction_concern",
        frozenset({"present", "elevated"}),
        ("addiction_concern_signal", "loss_of_control_over_use"),
    ),
    (
        "substance",
        "compulsive_use",
        frozenset({"present", "elevated"}),
        ("compulsive_use_signal", "substance_preoccupation"),
    ),
    (
        "substance",
        "loss_of_control_use",
        frozenset({"present", "elevated"}),
        ("loss_of_control_over_use", "addiction_concern_signal"),
    ),
    (
        "substance",
        "substance_preoccupation",
        frozenset({"present", "elevated"}),
        ("substance_preoccupation", "compulsive_use_signal"),
    ),
    (
        "agency",
        "recovery_goal",
        frozenset({"seeking", "present"}),
        ("recovery_goal_signal", "desire_for_change"),
    ),
    (
        "life_event",
        "accident",
        frozenset({"present", "elevated"}),
        ("accident_context", "trauma_context_signal", "post_event_distress"),
    ),
    (
        "life_event",
        "traumatic_event",
        frozenset({"present", "elevated"}),
        ("trauma_context_signal", "post_event_distress", "accident_context"),
    ),
    (
        "sleep",
        "insomnia",
        frozenset({"present", "elevated"}),
        ("insomnia_signal", "sleep_disruption"),
    ),
    (
        "sleep",
        "sleep_disruption",
        frozenset({"present", "elevated"}),
        ("sleep_disruption", "insomnia_signal"),
    ),
    (
        "body",
        "appetite_loss",
        frozenset({"present", "elevated", "reduced"}),
        ("appetite_loss_signal", "depressed_mood_signal"),
    ),
    (
        "social",
        "social_withdrawal",
        frozenset({"present", "elevated", "avoidant"}),
        ("social_withdrawal", "communication_avoidance", "depressed_mood_signal"),
    ),
)


def patterns_for_semantic_fact(fact: SemanticFact) -> list[str]:
    if not fact.is_valid():
        return []

    matched: list[str] = []
    for category, attribute, values, pattern_ids in FACT_PATTERN_RULES:
        if fact.category != category or fact.attribute != attribute:
            continue
        if fact.value not in values:
            continue
        matched.extend(pattern_ids)
    return matched


def semantic_fact_pattern_matches(facts: list[SemanticFact]) -> list[SemanticPatternMatch]:
    matches: list[SemanticPatternMatch] = []
    seen: set[str] = set()

    for fact_index, fact in enumerate(facts):
        for pattern_id in patterns_for_semantic_fact(fact):
            if pattern_id in seen:
                continue
            seen.add(pattern_id)
            matches.append(
                SemanticPatternMatch(
                    canonical_id=pattern_id,
                    matched_text=fact.evidence or f"{fact.category}/{fact.attribute}={fact.value}",
                    confidence=fact.confidence if fact.confidence is not None else 0.85,
                    fact_index=fact_index,
                )
            )

    if _should_emit_depressed_mood_from_low_mood(facts):
        if "depressed_mood_signal" not in seen:
            evidence = _depressed_mood_evidence(facts)
            matches.append(
                SemanticPatternMatch(
                    canonical_id="depressed_mood_signal",
                    matched_text=evidence,
                    confidence=0.85,
                    fact_index=_first_low_mood_fact_index(facts),
                )
            )

    return matches


def _should_emit_depressed_mood_from_low_mood(facts: list[SemanticFact]) -> bool:
    if not _has_low_mood_fact(facts):
        return False

    if _count_low_mood_facts(facts) >= 2:
        return True

    return _has_supporting_mood_fact(facts)


def _has_low_mood_fact(facts: list[SemanticFact]) -> bool:
    return any(
        fact.category == "emotion"
        and fact.attribute == "reported_low_mood"
        and fact.value in PRESENT_VALUES
        for fact in facts
    )


def _count_low_mood_facts(facts: list[SemanticFact]) -> int:
    return sum(
        1
        for fact in facts
        if fact.category == "emotion"
        and fact.attribute == "reported_low_mood"
        and fact.value in PRESENT_VALUES
    )


def _has_supporting_mood_fact(facts: list[SemanticFact]) -> bool:
    for category, attribute in DEPRESSED_MOOD_SUPPORTING_FACTS:
        for fact in facts:
            if fact.category != category or fact.attribute != attribute:
                continue
            if fact.value in PRESENT_VALUES:
                return True
    return False


def _first_low_mood_fact_index(facts: list[SemanticFact]) -> int:
    for index, fact in enumerate(facts):
        if fact.category == "emotion" and fact.attribute == "reported_low_mood":
            return index
    return 0


def _depressed_mood_evidence(facts: list[SemanticFact]) -> str:
    for fact in facts:
        if fact.category == "emotion" and fact.attribute == "reported_low_mood" and fact.evidence:
            return fact.evidence
    for category, attribute in DEPRESSED_MOOD_SUPPORTING_FACTS:
        for fact in facts:
            if fact.category == category and fact.attribute == attribute and fact.evidence:
                return fact.evidence
    return "emotion/reported_low_mood=present"
