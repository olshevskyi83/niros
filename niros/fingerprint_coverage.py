from __future__ import annotations

from dataclasses import dataclass, field

from niros.assessment import AssessmentResult
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact

COVERAGE_LEVEL_UNKNOWN = "unknown"
COVERAGE_LEVEL_PARTIAL = "partial"
COVERAGE_LEVEL_GOOD = "good"
COVERAGE_LEVEL_COMPLETE = "complete"

COVERAGE_LEVELS: tuple[str, ...] = (
    COVERAGE_LEVEL_UNKNOWN,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_GOOD,
    COVERAGE_LEVEL_COMPLETE,
)

INTAKE_FIELDS: tuple[str, ...] = (
    "main_problem",
    "duration",
    "perceived_causes",
    "current_impact",
    "previous_attempts",
    "desired_outcome",
)

FINGERPRINT_DOMAIN_IDS: tuple[str, ...] = (
    "presenting_problem",
    "patterns",
    "big_five",
    "self_domain",
    "emotion_regulation_domain",
    "relationships_domain",
    "meaning",
    "values_identity_domain",
    "cognitive_patterns_domain",
    "emotional_flexibility_domain",
    "sleep_nightmares",
    "grief_loss_bereavement",
    "trauma_stress_signals",
    "anxiety_fear_panic",
    "low_mood_depression_signals",
    "substance_use_patterns",
    "chronic_pain_fibromyalgia_fatigue",
    "speech_stuttering_expression",
    "psychedelic_session_concerns",
)

DOMAIN_DISPLAY_LABELS: dict[str, str] = {
    "presenting_problem": "Presenting Problem",
    "patterns": "Patterns",
    "big_five": "Big Five",
    "self_domain": "Self",
    "emotion_regulation_domain": "Emotion Regulation",
    "relationships_domain": "Relationships",
    "meaning": "Meaning",
    "values_identity_domain": "Values",
    "cognitive_patterns_domain": "Cognitive",
    "emotional_flexibility_domain": "Flexibility",
    "sleep_nightmares": "Sleep / Nightmares",
    "grief_loss_bereavement": "Grief / Loss",
    "trauma_stress_signals": "Trauma / Stress",
    "anxiety_fear_panic": "Anxiety / Fear",
    "low_mood_depression_signals": "Low Mood Signals",
    "substance_use_patterns": "Substance Use",
    "chronic_pain_fibromyalgia_fatigue": "Pain / Fatigue",
    "speech_stuttering_expression": "Speech / Expression",
    "psychedelic_session_concerns": "Psychedelic Concerns",
}

COVERAGE_REPORT_DOMAIN_ORDER: tuple[str, ...] = (
    "presenting_problem",
    "patterns",
    "big_five",
    "self_domain",
    "emotion_regulation_domain",
    "relationships_domain",
    "meaning",
    "values_identity_domain",
    "cognitive_patterns_domain",
    "emotional_flexibility_domain",
)

MODULE_DOMAIN_COVERAGE: dict[str, tuple[str, ...]] = {
    "big-five-short": ("big_five",),
    "self-domain-short": ("self_domain",),
    "emotion-regulation-domain-short": ("emotion_regulation_domain",),
    "relationships-domain-short": ("relationships_domain",),
    "values-identity-domain-short": ("values_identity_domain", "meaning"),
    "cognitive-patterns-domain-short": ("cognitive_patterns_domain",),
    "emotional-flexibility-domain-short": ("emotional_flexibility_domain",),
    "meaning-purpose-short": ("meaning", "values_identity_domain"),
    "low-mood-short": ("low_mood_depression_signals",),
    "anxiety-short": ("anxiety_fear_panic",),
    "sleep-short": ("sleep_nightmares",),
    "trauma-stress-short": ("trauma_stress_signals",),
    "grief-loss-short": ("grief_loss_bereavement", "meaning"),
    "substance-use-short": ("substance_use_patterns",),
    "behavioral-addiction-short": ("substance_use_patterns", "cognitive_patterns_domain"),
    "pain-fatigue-short": ("chronic_pain_fibromyalgia_fatigue",),
    "speech-anxiety-short": ("speech_stuttering_expression", "relationships_domain"),
    "psychedelic-concern-short": ("psychedelic_session_concerns", "anxiety_fear_panic"),
}

PATTERN_DOMAIN_HINTS: dict[str, tuple[tuple[str, float], ...]] = {
    "unworthiness_signal": (("self_domain", 0.30),),
    "self_worth_instability": (("self_domain", 0.25),),
    "shame_sensitivity": (("self_domain", 0.25),),
    "harsh_self_criticism": (("self_domain", 0.20),),
    "social_disconnection_signal": (("self_domain", 0.15), ("relationships_domain", 0.25)),
    "rejection_sensitivity": (("relationships_domain", 0.25), ("self_domain", 0.10)),
    "social_withdrawal": (
        ("relationships_domain", 0.20),
        ("emotion_regulation_domain", 0.15),
        ("self_domain", 0.18),
    ),
    "communication_avoidance": (("relationships_domain", 0.15), ("emotion_regulation_domain", 0.10)),
    "attachment_anxiety": (("relationships_domain", 0.25),),
    "abandonment_wound_signal": (("relationships_domain", 0.30), ("grief_loss_bereavement", 0.15)),
    "emotional_suppression": (("emotion_regulation_domain", 0.25),),
    "emotional_overwhelm": (("emotion_regulation_domain", 0.25),),
    "emotional_avoidance": (("emotion_regulation_domain", 0.25), ("emotional_flexibility_domain", 0.15)),
    "rumination": (("cognitive_patterns_domain", 0.25),),
    "obsessive_thinking_loop": (("cognitive_patterns_domain", 0.20),),
    "mental_overcontrol": (("cognitive_patterns_domain", 0.20),),
    "hopelessness_signal": (("cognitive_patterns_domain", 0.20), ("low_mood_depression_signals", 0.20)),
    "loss_of_meaning": (("meaning", 0.30),),
    "meaning_seeking": (("meaning", 0.20), ("values_identity_domain", 0.15)),
    "identity_confusion": (("values_identity_domain", 0.25),),
    "identity_uncertainty": (("values_identity_domain", 0.20),),
    "control_resistance": (("emotional_flexibility_domain", 0.20),),
    "surrender_difficulty": (("emotional_flexibility_domain", 0.20),),
    "grief_signal": (("grief_loss_bereavement", 0.30), ("meaning", 0.15)),
    "bereavement_context": (("grief_loss_bereavement", 0.35),),
    "loss_related_distress": (("grief_loss_bereavement", 0.25), ("meaning", 0.10)),
    "relationship_breakup_context": (("grief_loss_bereavement", 0.20), ("relationships_domain", 0.20)),
    "sleep_disruption": (("sleep_nightmares", 0.30),),
    "insomnia_signal": (("sleep_nightmares", 0.30),),
    "nightmare_disturbance": (("sleep_nightmares", 0.35),),
    "generalized_fear": (("anxiety_fear_panic", 0.25),),
    "panic_reactivity": (("anxiety_fear_panic", 0.25),),
    "accident_context": (("trauma_stress_signals", 0.30),),
    "trauma_context_signal": (("trauma_stress_signals", 0.30),),
    "post_event_distress": (("trauma_stress_signals", 0.25),),
    "depressed_mood_signal": (("low_mood_depression_signals", 0.30),),
    "low_mood_signal": (("low_mood_depression_signals", 0.25),),
    "self_reported_depression_concern": (("low_mood_depression_signals", 0.25),),
    "drug_use_concern": (("substance_use_patterns", 0.30),),
    "substance_use_pattern": (("substance_use_patterns", 0.30),),
    "chronic_pain_burden": (("chronic_pain_fibromyalgia_fatigue", 0.30),),
    "fibromyalgia_signal": (("chronic_pain_fibromyalgia_fatigue", 0.30),),
    "fatigue_burden": (("chronic_pain_fibromyalgia_fatigue", 0.20),),
    "stuttering_signal": (("speech_stuttering_expression", 0.30),),
    "speech_anxiety": (("speech_stuttering_expression", 0.25),),
    "psychedelic_anxiety": (("psychedelic_session_concerns", 0.30),),
    "fear_of_bad_trip": (("psychedelic_session_concerns", 0.30),),
}

SEMANTIC_FACT_DOMAIN_HINTS: dict[tuple[str, str], tuple[tuple[str, float], ...]] = {
    ("self", "unworthiness"): (("self_domain", 0.25),),
    ("self", "self_worth"): (("self_domain", 0.20),),
    ("social", "belonging"): (("self_domain", 0.15), ("relationships_domain", 0.15)),
    ("social", "feeling_unwanted"): (("self_domain", 0.15), ("relationships_domain", 0.15)),
    ("social", "social_withdrawal"): (("relationships_domain", 0.15), ("emotion_regulation_domain", 0.10)),
    ("emotion", "grief"): (("grief_loss_bereavement", 0.20),),
    ("emotion", "loss_related_distress"): (("grief_loss_bereavement", 0.15),),
    ("emotion", "separation_distress"): (("relationships_domain", 0.15), ("emotion_regulation_domain", 0.10)),
    ("life_event", "bereavement"): (("grief_loss_bereavement", 0.25),),
    ("life_event", "loss"): (("grief_loss_bereavement", 0.15),),
    ("relationship", "breakup"): (("relationships_domain", 0.20), ("grief_loss_bereavement", 0.10)),
    ("relationship", "abandonment"): (("relationships_domain", 0.25),),
    ("sleep", "insomnia"): (("sleep_nightmares", 0.25),),
    ("sleep", "nightmares"): (("sleep_nightmares", 0.25),),
    ("sleep", "sleep_disruption"): (("sleep_nightmares", 0.20),),
    ("meaning", "meaning_sense"): (("meaning", 0.20), ("values_identity_domain", 0.10)),
    ("agency", "recovery_goal"): (("values_identity_domain", 0.10), ("self_domain", 0.10)),
}

INTAKE_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sleep_nightmares": ("sleep", "insomnia", "сон", "спати", "nightmare", "кошмар", "sueño"),
    "grief_loss_bereavement": ("grief", "loss", "bereavement", "втрат", "смерт", "duelo", "горе"),
    "trauma_stress_signals": ("accident", "trauma", "авар", "травм", "stress", "стрес"),
    "anxiety_fear_panic": ("anxiety", "fear", "panic", "тривог", "страх", "pánico"),
    "low_mood_depression_signals": ("depress", "депрес", "low mood", "настр", "пригнічен"),
    "substance_use_patterns": ("substance", "drug", "addiction", "наркот", "залеж", "alcohol"),
    "chronic_pain_fibromyalgia_fatigue": ("pain", "fatigue", "біль", "втом", "fibromyalgia"),
    "speech_stuttering_expression": ("stutter", "speech", "заїк", "говор"),
    "psychedelic_session_concerns": ("psychedelic", "bad trip", "тріп", "psilocybin"),
    "meaning": ("meaning", "purpose", "сенс", "зміст", "empty", "порожн"),
    "self_domain": ("worthless", "unwanted", "непотрібн", "belong", "не маю значення"),
    "relationships_domain": ("alone", "lonely", "relationship", "partner", "стосунк"),
}

SUFFICIENT_COVERAGE_THRESHOLD = 0.50
COMPLETE_COVERAGE_THRESHOLD = 0.90
EVIDENCE_COVERAGE_CAP = 0.85
EVIDENCE_DOMAIN_THRESHOLD = 0.15
EVIDENCE_MATCH_BONUS = 0.35
SYMPTOM_MODULE_BONUS = 0.55
PROJECTED_MODULE_COVERAGE = 0.92
SYMPTOM_PARTIAL_DISCOUNT = 0.35
SINGLE_DOMAIN_BONUS = 0.20
PARTIAL_SYMPTOM_THRESHOLD = 0.25

PREFERRED_MODULE_BY_SYMPTOM_DOMAIN: dict[str, str] = {
    "sleep_nightmares": "sleep-short",
    "grief_loss_bereavement": "grief-loss-short",
    "trauma_stress_signals": "trauma-stress-short",
    "anxiety_fear_panic": "anxiety-short",
    "low_mood_depression_signals": "low-mood-short",
    "substance_use_patterns": "substance-use-short",
    "chronic_pain_fibromyalgia_fatigue": "pain-fatigue-short",
    "speech_stuttering_expression": "speech-anxiety-short",
    "psychedelic_session_concerns": "psychedelic-concern-short",
    "meaning": "meaning-purpose-short",
}

PREFERRED_MODULE_BONUS = 0.45

CORE_PSYCH_FINGERPRINT_DOMAINS: frozenset[str] = frozenset(
    {
        "big_five",
        "self_domain",
        "emotion_regulation_domain",
        "relationships_domain",
        "values_identity_domain",
        "cognitive_patterns_domain",
        "emotional_flexibility_domain",
    }
)

ALWAYS_FILL_CORE_PSYCH_DOMAINS: frozenset[str] = frozenset(
    {
        "big_five",
        "self_domain",
        "emotion_regulation_domain",
        "relationships_domain",
        "cognitive_patterns_domain",
        "emotional_flexibility_domain",
    }
)

SYMPTOM_FINGERPRINT_DOMAINS: frozenset[str] = frozenset(
    {
        "sleep_nightmares",
        "grief_loss_bereavement",
        "trauma_stress_signals",
        "anxiety_fear_panic",
        "low_mood_depression_signals",
        "substance_use_patterns",
        "chronic_pain_fibromyalgia_fatigue",
        "speech_stuttering_expression",
        "psychedelic_session_concerns",
        "meaning",
    }
)


@dataclass(frozen=True)
class DomainCoverage:
    domain_id: str
    coverage: float
    confidence: float
    level: str


@dataclass
class FingerprintCoverageReport:
    domains: dict[str, DomainCoverage] = field(default_factory=dict)
    missing_domains: list[str] = field(default_factory=list)
    selected_modules: list[str] = field(default_factory=list)
    reason_by_module: dict[str, str] = field(default_factory=dict)


class FingerprintCoverageAnalyzer:
    def analyze(
        self,
        *,
        presenting_problem: dict[str, str],
        patterns: list[str] | list[PatternTag],
        semantic_facts: list[SemanticFact] | None = None,
        completed_assessments: dict[str, list[AssessmentResult]] | None = None,
        max_modules: int = 4,
    ) -> FingerprintCoverageReport:
        pattern_ids, pattern_confidence = _normalize_patterns(patterns)
        coverage_values = _empty_coverage_values()
        confidence_values = _empty_coverage_values()

        _apply_intake_coverage(presenting_problem, coverage_values, confidence_values)
        _apply_pattern_coverage(pattern_ids, pattern_confidence, coverage_values, confidence_values)
        _apply_semantic_fact_coverage(semantic_facts or [], coverage_values, confidence_values)
        _apply_intake_keyword_hints(presenting_problem, coverage_values, confidence_values)
        _apply_completed_assessment_coverage(
            completed_assessments or {},
            coverage_values,
            confidence_values,
        )

        domains = {
            domain_id: DomainCoverage(
                domain_id=domain_id,
                coverage=_clamp(coverage_values[domain_id]),
                confidence=_clamp(confidence_values[domain_id]),
                level=coverage_level(coverage_values[domain_id]),
            )
            for domain_id in FINGERPRINT_DOMAIN_IDS
        }
        missing_domains = [
            domain_id
            for domain_id in COVERAGE_REPORT_DOMAIN_ORDER
            if domains[domain_id].level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}
        ]

        selected_modules, reason_by_module = self._select_modules(
            domains=domains,
            evidence_domains=_evidence_backed_domains(coverage_values),
            completed_modules=frozenset((completed_assessments or {}).keys()),
            max_modules=max_modules,
        )

        return FingerprintCoverageReport(
            domains=domains,
            missing_domains=missing_domains,
            selected_modules=selected_modules,
            reason_by_module=reason_by_module,
        )

    def _select_modules(
        self,
        *,
        domains: dict[str, DomainCoverage],
        evidence_domains: frozenset[str],
        completed_modules: frozenset[str],
        max_modules: int,
    ) -> tuple[list[str], dict[str, str]]:
        projected_coverage = {domain_id: domains[domain_id].coverage for domain_id in FINGERPRINT_DOMAIN_IDS}
        selected: list[str] = []
        reason_by_module: dict[str, str] = {}

        if (
            "big-five-short" not in completed_modules
            and projected_coverage["big_five"] < SUFFICIENT_COVERAGE_THRESHOLD
        ):
            selected.append("big-five-short")
            reason_by_module["big-five-short"] = (
                "baseline personality coverage required for Human Digital Fingerprint"
            )
            _project_module_coverage("big-five-short", projected_coverage)

        while len(selected) < max_modules:
            best: tuple[float, float, int, str, str] | None = None

            for module_id, module_domains in sorted(MODULE_DOMAIN_COVERAGE.items()):
                if module_id in completed_modules or module_id in selected:
                    continue

                relevant_gain, evidence_matches = _module_relevant_gain(
                    module_domains,
                    projected_coverage,
                    evidence_domains,
                )
                if relevant_gain <= 0.0:
                    continue

                efficiency = relevant_gain / len(module_domains)
                score = efficiency + (EVIDENCE_MATCH_BONUS * evidence_matches)
                if _module_has_symptom_evidence(module_domains, evidence_domains):
                    score += SYMPTOM_MODULE_BONUS
                if len(module_domains) == 1:
                    score += SINGLE_DOMAIN_BONUS
                score += _preferred_module_bonus(module_id, evidence_domains, projected_coverage)

                missing = [
                    DOMAIN_DISPLAY_LABELS.get(domain_id, domain_id)
                    for domain_id in module_domains
                    if _domain_counts_for_selection(domain_id, evidence_domains)
                    and projected_coverage[domain_id] < SUFFICIENT_COVERAGE_THRESHOLD
                ]
                reason = (
                    f"fills missing fingerprint coverage for {', '.join(missing)} "
                    f"(information gain {relevant_gain:.2f})"
                )
                candidate = (score, relevant_gain, -len(module_domains), module_id, reason)
                if best is None or candidate > best:
                    best = candidate

            if best is None:
                break

            _, _, _, module_id, reason = best
            selected.append(module_id)
            reason_by_module[module_id] = reason
            _project_module_coverage(module_id, projected_coverage)

        return selected, reason_by_module


def coverage_level(value: float) -> str:
    if value >= COMPLETE_COVERAGE_THRESHOLD:
        return COVERAGE_LEVEL_COMPLETE
    if value >= SUFFICIENT_COVERAGE_THRESHOLD:
        return COVERAGE_LEVEL_GOOD
    if value >= 0.25:
        return COVERAGE_LEVEL_PARTIAL
    return COVERAGE_LEVEL_UNKNOWN


def render_fingerprint_coverage_report(report: FingerprintCoverageReport) -> str:
    lines = ["===== Fingerprint Coverage ====="]
    for domain_id in COVERAGE_REPORT_DOMAIN_ORDER:
        domain = report.domains[domain_id]
        label = DOMAIN_DISPLAY_LABELS.get(domain_id, domain_id)
        lines.append(f"{label}\n{int(round(domain.coverage * 100))}%")

    lines.append("Selected:")
    if report.selected_modules:
        lines.extend(report.selected_modules)
    else:
        lines.append("(none)")

    return "\n".join(lines)


def _module_relevant_gain(
    module_domains: tuple[str, ...],
    coverage_values: dict[str, float],
    evidence_domains: frozenset[str],
) -> tuple[float, int]:
    gain = 0.0
    evidence_matches = 0
    for domain_id in module_domains:
        if not _domain_counts_for_selection(domain_id, evidence_domains):
            continue
        current = coverage_values[domain_id]
        if current >= SUFFICIENT_COVERAGE_THRESHOLD:
            continue
        domain_gain = 1.0 - current
        if domain_id in SYMPTOM_FINGERPRINT_DOMAINS and current >= PARTIAL_SYMPTOM_THRESHOLD:
            domain_gain *= SYMPTOM_PARTIAL_DISCOUNT
        gain += domain_gain
        if domain_id in evidence_domains:
            evidence_matches += 1
    return gain, evidence_matches


def _module_has_symptom_evidence(
    module_domains: tuple[str, ...],
    evidence_domains: frozenset[str],
) -> bool:
    return any(
        domain_id in SYMPTOM_FINGERPRINT_DOMAINS and domain_id in evidence_domains
        for domain_id in module_domains
    )


def _preferred_module_bonus(
    module_id: str,
    evidence_domains: frozenset[str],
    coverage_values: dict[str, float],
) -> float:
    for domain_id in evidence_domains:
        if PREFERRED_MODULE_BY_SYMPTOM_DOMAIN.get(domain_id) != module_id:
            continue
        if domain_id == "sleep_nightmares" and _core_psych_still_missing(coverage_values):
            return 0.0
        return PREFERRED_MODULE_BONUS
    return 0.0


def _core_psych_still_missing(coverage_values: dict[str, float]) -> bool:
    return any(
        coverage_values[domain_id] < PARTIAL_SYMPTOM_THRESHOLD
        for domain_id in ALWAYS_FILL_CORE_PSYCH_DOMAINS
        if domain_id != "big_five"
    )


def _project_module_coverage(module_id: str, coverage_values: dict[str, float]) -> None:
    for domain_id in MODULE_DOMAIN_COVERAGE.get(module_id, ()):
        coverage_values[domain_id] = max(coverage_values[domain_id], PROJECTED_MODULE_COVERAGE)


def _domain_counts_for_selection(domain_id: str, evidence_domains: frozenset[str]) -> bool:
    if domain_id in evidence_domains:
        return True
    if domain_id in ALWAYS_FILL_CORE_PSYCH_DOMAINS:
        return True
    return False


def _evidence_backed_domains(coverage_values: dict[str, float]) -> frozenset[str]:
    return frozenset(
        domain_id
        for domain_id, value in coverage_values.items()
        if domain_id not in {"presenting_problem", "patterns"}
        and value >= EVIDENCE_DOMAIN_THRESHOLD
    )


def _empty_coverage_values() -> dict[str, float]:
    return {domain_id: 0.0 for domain_id in FINGERPRINT_DOMAIN_IDS}


def _apply_intake_coverage(
    presenting_problem: dict[str, str],
    coverage_values: dict[str, float],
    confidence_values: dict[str, float],
) -> None:
    populated = sum(1 for field_name in INTAKE_FIELDS if str(presenting_problem.get(field_name, "")).strip())
    if populated == 0:
        return

    ratio = populated / len(INTAKE_FIELDS)
    coverage_values["presenting_problem"] = max(coverage_values["presenting_problem"], ratio)
    confidence_values["presenting_problem"] = max(confidence_values["presenting_problem"], min(1.0, ratio + 0.1))


def _apply_pattern_coverage(
    pattern_ids: frozenset[str],
    pattern_confidence: dict[str, float],
    coverage_values: dict[str, float],
    confidence_values: dict[str, float],
) -> None:
    if not pattern_ids:
        return

    avg_confidence = sum(pattern_confidence.get(pattern_id, 1.0) for pattern_id in pattern_ids) / len(
        pattern_ids
    )
    pattern_coverage = min(
        1.0,
        0.30 + (0.12 * len(pattern_ids)) + (0.08 * avg_confidence),
    )
    coverage_values["patterns"] = max(coverage_values["patterns"], pattern_coverage)
    confidence_values["patterns"] = max(confidence_values["patterns"], min(1.0, pattern_coverage))

    for pattern_id in pattern_ids:
        hints = PATTERN_DOMAIN_HINTS.get(pattern_id, ())
        confidence = pattern_confidence.get(pattern_id, 1.0)
        for domain_id, hint in hints:
            boosted = min(EVIDENCE_COVERAGE_CAP, hint * confidence)
            coverage_values[domain_id] = max(coverage_values[domain_id], boosted)
            confidence_values[domain_id] = max(confidence_values[domain_id], boosted)


def _apply_semantic_fact_coverage(
    semantic_facts: list[SemanticFact],
    coverage_values: dict[str, float],
    confidence_values: dict[str, float],
) -> None:
    for fact in semantic_facts:
        if not fact.is_valid():
            continue
        hints = SEMANTIC_FACT_DOMAIN_HINTS.get((fact.category, fact.attribute), ())
        fact_confidence = fact.confidence if fact.confidence is not None else 0.85
        for domain_id, hint in hints:
            boosted = min(EVIDENCE_COVERAGE_CAP, hint * fact_confidence)
            coverage_values[domain_id] = max(coverage_values[domain_id], boosted)
            confidence_values[domain_id] = max(confidence_values[domain_id], boosted)


def _apply_intake_keyword_hints(
    presenting_problem: dict[str, str],
    coverage_values: dict[str, float],
    confidence_values: dict[str, float],
) -> None:
    combined = " ".join(
        str(presenting_problem.get(field_name, "")).lower()
        for field_name in INTAKE_FIELDS
        if presenting_problem.get(field_name)
    )
    if not combined:
        return

    for domain_id, keywords in INTAKE_DOMAIN_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            coverage_values[domain_id] = max(coverage_values[domain_id], 0.20)
            confidence_values[domain_id] = max(confidence_values[domain_id], 0.35)


def _apply_completed_assessment_coverage(
    completed_assessments: dict[str, list[AssessmentResult]],
    coverage_values: dict[str, float],
    confidence_values: dict[str, float],
) -> None:
    for module_id, results in completed_assessments.items():
        module_domains = MODULE_DOMAIN_COVERAGE.get(module_id, ())
        if not results:
            continue

        avg_normalized = sum(result.normalized_score for result in results) / len(results)
        module_coverage = min(1.0, 0.75 + (0.25 * avg_normalized))

        for domain_id in module_domains:
            coverage_values[domain_id] = max(coverage_values[domain_id], module_coverage)
            confidence_values[domain_id] = max(confidence_values[domain_id], module_coverage)


def _normalize_patterns(
    patterns: list[str] | list[PatternTag],
) -> tuple[frozenset[str], dict[str, float]]:
    if not patterns:
        return frozenset(), {}

    if isinstance(patterns[0], PatternTag):
        tags = patterns  # type: ignore[assignment]
        pattern_ids = {tag.canonical_id for tag in tags}
        confidence = {tag.canonical_id: tag.confidence for tag in tags}
        return frozenset(pattern_ids), confidence

    pattern_ids = frozenset(str(pattern_id) for pattern_id in patterns)
    return pattern_ids, {str(pattern_id): 1.0 for pattern_id in patterns}


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
