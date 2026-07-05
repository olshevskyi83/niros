"""Icaros readiness gate — evaluates whether NIROS understands a person well enough
to safely personalize therapeutic language. Does not generate an Icaro."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from niros.assessment import AssessmentResult
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_GOOD,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageReport,
)
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    STRATEGY_CONFIDENCE_MEDIUM,
    InterventionStrategy,
)
from niros.scenario_blueprint import ScenarioBlueprint
from niros.semantic_interpreter.facts import SemanticFact
from niros.spirituality_worldview import (
    COMFORT_ALLOWED,
    COMFORT_AVOID,
    COMFORT_PREFERRED,
    ORIENTATION_AGNOSTIC,
    ORIENTATION_ATHEIST,
    ORIENTATION_CHRISTIAN,
    ORIENTATION_NATURE_SPIRITUAL,
    ORIENTATION_RELIGION_AVERSE,
    ORIENTATION_SECULAR_HUMANIST,
    ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
    ORIENTATION_UNKNOWN,
    SPIRITUALITY_WORLDVIEW_DOMAIN,
    SpiritualityWorldviewProfile,
    build_spirituality_worldview_profile,
)

READINESS_NOT_READY = "Not Ready"
READINESS_PARTIALLY_READY = "Partially Ready"
READINESS_READY_WITH_LIMITATIONS = "Ready with limitations"
READINESS_READY = "Ready"

CONFIDENCE_LOW = "low"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_HIGH = "high"

SELF_DOMAIN = "self_domain"
EMOTION_REGULATION_DOMAIN = "emotion_regulation_domain"
VALUES_IDENTITY_DOMAIN = "values_identity_domain"
MEANING_DOMAIN = "meaning"

CRITICAL_BLOCKING_DOMAINS = (
    SELF_DOMAIN,
    EMOTION_REGULATION_DOMAIN,
)

LIMITATION_DOMAINS = (
    VALUES_IDENTITY_DOMAIN,
    MEANING_DOMAIN,
    SPIRITUALITY_WORLDVIEW_DOMAIN,
)

SPIRITUAL_PATTERN_IDS = frozenset(
    {
        "spiritual_openness",
        "spiritual_resistance",
        "meaning_seeking",
        "mystical_expectation",
        "desire_for_change",
        "search_for_self_understanding",
    }
)

LEVEL_SCORES: dict[str, int] = {
    COVERAGE_LEVEL_UNKNOWN: 0,
    COVERAGE_LEVEL_PARTIAL: 55,
    COVERAGE_LEVEL_GOOD: 80,
    COVERAGE_LEVEL_COMPLETE: 100,
}

CONFIDENCE_SCORES: dict[str, int] = {
    STRATEGY_CONFIDENCE_LOW: 35,
    STRATEGY_CONFIDENCE_MEDIUM: 65,
    STRATEGY_CONFIDENCE_HIGH: 90,
}

SPIRITUAL_ORIENTATION_ATHEIST = "atheist"
SPIRITUAL_ORIENTATION_CHRISTIAN = "christian"
SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS = "spiritual_but_not_religious"
SPIRITUAL_ORIENTATION_AGNOSTIC = "agnostic"
SPIRITUAL_ORIENTATION_RELIGION_AVERSE = "religion_averse"
SPIRITUAL_ORIENTATION_UNKNOWN = "unknown"

SYMBOL_PREFERENCE_PREFERRED = "preferred"
SYMBOL_PREFERENCE_NEUTRAL = "neutral"
SYMBOL_PREFERENCE_AVOID = "avoid"

LANGUAGE_STYLE_KEYS = (
    "directness",
    "metaphor",
    "repetition",
    "rhythm",
    "affirmation",
    "identity_language",
)


@dataclass(frozen=True)
class IcarosReadinessResult:
    ready: bool
    overall_readiness: int
    confidence: str
    readiness_level: str
    missing_information: tuple[str, ...] = field(default_factory=tuple)
    blocking_domains: tuple[str, ...] = field(default_factory=tuple)
    recommended_next_steps: tuple[str, ...] = field(default_factory=tuple)
    recommended_language_style: dict[str, str] = field(default_factory=dict)
    recommended_symbolic_style: dict[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    spiritual_orientation: str = SPIRITUAL_ORIENTATION_UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "overall_readiness": self.overall_readiness,
            "confidence": self.confidence,
            "readiness_level": self.readiness_level,
            "missing_information": list(self.missing_information),
            "blocking_domains": list(self.blocking_domains),
            "recommended_next_steps": list(self.recommended_next_steps),
            "recommended_language_style": dict(self.recommended_language_style),
            "recommended_symbolic_style": dict(self.recommended_symbolic_style),
            "warnings": list(self.warnings),
            "spiritual_orientation": self.spiritual_orientation,
        }


class IcarosReadinessEvaluator:
    """Deterministic readiness audit before any future Icaro generation."""

    def evaluate(
        self,
        *,
        fingerprint: dict,
        coverage_report: FingerprintCoverageReport,
        strategy: InterventionStrategy,
        scenario_blueprint: ScenarioBlueprint | None = None,
        completed_assessments: dict[str, list[AssessmentResult]] | None = None,
    ) -> IcarosReadinessResult:
        detected_patterns = _detected_pattern_ids(fingerprint)
        semantic_facts = _semantic_facts(fingerprint)
        completed = completed_assessments or _completed_from_fingerprint(fingerprint)

        coverage_score = _coverage_component_score(coverage_report, completed)
        pattern_score = _pattern_component_score(detected_patterns, coverage_report)
        strategy_score = _strategy_component_score(strategy, coverage_report)
        scenario_score = _scenario_component_score(scenario_blueprint)
        profile_score = _profile_confidence_score(
            fingerprint,
            coverage_report,
            strategy,
            detected_patterns,
        )

        overall = round(
            coverage_score * 0.30
            + pattern_score * 0.15
            + strategy_score * 0.20
            + scenario_score * 0.15
            + profile_score * 0.20
        )

        spiritual_orientation = _orientation_for_readiness(
            _worldview_profile_from_fingerprint(
                fingerprint,
                detected_patterns,
                semantic_facts,
                completed,
            )
        )
        spiritual_understood = _spiritual_orientation_understood(
            coverage_report,
            _worldview_profile_from_fingerprint(
                fingerprint,
                detected_patterns,
                semantic_facts,
                completed,
            ),
            detected_patterns,
            semantic_facts,
        )

        missing_information = _missing_information(
            coverage_report,
            spiritual_understood,
            detected_patterns,
            completed,
        )
        blocking_domains: list[str] = []
        warnings: list[str] = []
        next_steps: list[str] = []

        self_level = _domain_level(coverage_report, SELF_DOMAIN)
        emotion_level = _domain_level(coverage_report, EMOTION_REGULATION_DOMAIN)
        values_level = _domain_level(coverage_report, VALUES_IDENTITY_DOMAIN)

        if self_level == COVERAGE_LEVEL_UNKNOWN:
            blocking_domains.append(SELF_DOMAIN)
            overall = min(overall, 39)
            warnings.append("Self domain requires more confidence.")
            next_steps.append("Gather more evidence about self-worth, shame, and self-criticism.")

        if profile_score < 45:
            blocking_domains.append("human_profile")
            overall = min(overall, 39)
            warnings.append("Human profile confidence is too low for personalized therapeutic language.")
            next_steps.append("Complete more interview turns and targeted assessments before personalization.")

        critical_unknown = sum(
            1
            for domain_id in CRITICAL_BLOCKING_DOMAINS + (VALUES_IDENTITY_DOMAIN,)
            if _domain_level(coverage_report, domain_id) == COVERAGE_LEVEL_UNKNOWN
        )
        if critical_unknown >= 2:
            if "multiple_critical_domains" not in blocking_domains:
                blocking_domains.append("multiple_critical_domains")
            overall = min(overall, 39)
            warnings.append("Multiple critical psychological domains remain unknown.")
            next_steps.append("Prioritize assessments for the least understood core domains.")

        if emotion_level == COVERAGE_LEVEL_UNKNOWN:
            missing_information.append("emotion_regulation_domain")
            next_steps.append("Explore emotion regulation patterns and coping responses.")

        if not spiritual_understood:
            overall = min(overall, 84)
            missing_information.append("spiritual_orientation")
            warnings.append(
                "Spiritual / worldview orientation is unknown; "
                "symbolic language should remain conservative."
            )
            next_steps.append(
                "Ask about spiritual openness, meaning, and symbolic language comfort."
            )
        else:
            worldview_profile = _worldview_profile_from_fingerprint(
                fingerprint,
                detected_patterns,
                semantic_facts,
                completed,
            )
            _apply_worldview_readiness_notes(
                worldview_profile,
                warnings,
                next_steps,
            )

        if values_level == COVERAGE_LEVEL_UNKNOWN:
            overall = min(overall, 84)
            missing_information.append(VALUES_IDENTITY_DOMAIN)
            warnings.append("Identity domain still uncertain.")
            next_steps.append("Clarify values, identity, and what feels authentically meaningful.")

        if self_level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}:
            warnings.append("Self domain requires more confidence.")

        language_style = _recommend_language_style(strategy, coverage_report)
        symbolic_style = _recommend_symbolic_style(
            strategy,
            spiritual_orientation,
            spiritual_understood,
            _worldview_profile_from_fingerprint(
                fingerprint,
                detected_patterns,
                semantic_facts,
                completed,
            ),
        )

        overall = max(0, min(100, overall))
        readiness_level = _readiness_level_label(overall)
        confidence = _confidence_label(overall, blocking_domains)
        ready = overall >= 85 and not blocking_domains

        return IcarosReadinessResult(
            ready=ready,
            overall_readiness=overall,
            confidence=confidence,
            readiness_level=readiness_level,
            missing_information=tuple(dict.fromkeys(missing_information)),
            blocking_domains=tuple(dict.fromkeys(blocking_domains)),
            recommended_next_steps=tuple(dict.fromkeys(next_steps)),
            recommended_language_style=language_style,
            recommended_symbolic_style=symbolic_style,
            warnings=tuple(dict.fromkeys(warnings)),
            spiritual_orientation=spiritual_orientation,
        )


def render_icaros_readiness_section(result: IcarosReadinessResult) -> str:
    lines = [
        "===== ICAROS READINESS =====",
        f"Overall readiness: {result.overall_readiness}%",
        f"Readiness level: {result.readiness_level}",
        f"Confidence: {result.confidence.title()}",
        f"Ready for personalized language: {'Yes' if result.ready else 'No'}",
        f"Spiritual orientation (inferred): {result.spiritual_orientation.replace('_', ' ')}",
        "",
        "Blocking domains:",
    ]
    if result.blocking_domains:
        lines.extend(f"- {domain.replace('_', ' ')}" for domain in result.blocking_domains)
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Warnings:")
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Missing information:")
    if result.missing_information:
        lines.extend(f"- {item.replace('_', ' ')}" for item in result.missing_information)
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Recommended next steps:")
    if result.recommended_next_steps:
        lines.extend(f"- {step}" for step in result.recommended_next_steps)
    else:
        lines.append("- Continue with the current session strategy; no major gaps flagged.")

    lines.append("")
    lines.append("Language recommendation:")
    for key in LANGUAGE_STYLE_KEYS:
        value = result.recommended_language_style.get(key, "neutral")
        lines.append(f"- {key.replace('_', ' ')}: {value}")

    lines.append("")
    lines.append("Symbol recommendation:")
    for key, value in sorted(result.recommended_symbolic_style.items()):
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


def _detected_pattern_ids(fingerprint: dict) -> set[str]:
    patterns = fingerprint.get("patterns", {})
    counts = patterns.get("pattern_counts", {})
    if counts:
        return set(counts.keys())
    primary = patterns.get("primary_pattern")
    if primary:
        ids = {primary["canonical_id"]}
        for secondary in patterns.get("secondary_patterns", []):
            ids.add(secondary["canonical_id"])
        return ids
    return set()


def _semantic_facts(fingerprint: dict) -> list[SemanticFact]:
    facts: list[SemanticFact] = []
    for item in fingerprint.get("semantic_facts", []):
        if isinstance(item, SemanticFact):
            facts.append(item)
            continue
        if isinstance(item, dict):
            confidence_raw = item.get("confidence", 1.0)
            facts.append(
                SemanticFact(
                    category=str(item.get("category", "")),
                    attribute=str(item.get("attribute", "")),
                    value=str(item.get("value", "")),
                    evidence=str(item.get("evidence", "")),
                    confidence=float(confidence_raw if confidence_raw is not None else 1.0),
                )
            )
    return facts


def _completed_from_fingerprint(fingerprint: dict) -> dict[str, list[AssessmentResult]]:
    grouped: dict[str, list[AssessmentResult]] = {}
    for item in fingerprint.get("assessment_results", []):
        if not isinstance(item, dict):
            continue
        module_id = str(item.get("module_id", ""))
        if not module_id:
            continue
        grouped.setdefault(module_id, []).append(
            AssessmentResult(
                domain_id=str(item.get("domain_id", module_id)),
                score=float(item.get("score", 0.0)),
                normalized_score=float(item.get("normalized_score", 0.0)),
                interpretation=str(item.get("interpretation", "")),
                fingerprint_dimension=str(item.get("fingerprint_dimension", "patterns")),
            )
        )
    return grouped


def _domain_level(coverage_report: FingerprintCoverageReport, domain_id: str) -> str:
    domain = coverage_report.domains.get(domain_id)
    if domain is None:
        return COVERAGE_LEVEL_UNKNOWN
    return domain.level


def _level_score(level: str) -> int:
    return LEVEL_SCORES.get(level, 0)


def _coverage_component_score(
    coverage_report: FingerprintCoverageReport,
    completed_assessments: dict[str, list[AssessmentResult]],
) -> int:
    weighted_domains = (
        (SELF_DOMAIN, 0.22),
        (EMOTION_REGULATION_DOMAIN, 0.18),
        (VALUES_IDENTITY_DOMAIN, 0.14),
        (MEANING_DOMAIN, 0.14),
        (SPIRITUALITY_WORLDVIEW_DOMAIN, 0.10),
        ("presenting_problem", 0.11),
        ("patterns", 0.11),
    )
    total = 0.0
    for domain_id, weight in weighted_domains:
        score = _level_score(_domain_level(coverage_report, domain_id))
        if completed_assessments and domain_id in {
            VALUES_IDENTITY_DOMAIN,
            MEANING_DOMAIN,
            EMOTION_REGULATION_DOMAIN,
            SELF_DOMAIN,
            SPIRITUALITY_WORLDVIEW_DOMAIN,
        }:
            score = min(100, score + 8)
        total += score * weight
    return round(total)


def _pattern_component_score(
    detected_patterns: set[str],
    coverage_report: FingerprintCoverageReport,
) -> int:
    if not detected_patterns:
        return 0
    base = _level_score(_domain_level(coverage_report, "patterns"))
    if len(detected_patterns) >= 3:
        base = min(100, base + 10)
    if detected_patterns & SPIRITUAL_PATTERN_IDS:
        base = min(100, base + 5)
    return base


def _strategy_component_score(
    strategy: InterventionStrategy,
    coverage_report: FingerprintCoverageReport | None = None,
) -> int:
    if not strategy.focus_confidence:
        base = 45
    else:
        scores = [
            CONFIDENCE_SCORES.get(item.confidence, 50)
            for item in strategy.focus_confidence
        ]
        base = round(sum(scores) / len(scores))

        if strategy.coverage_summary is not None:
            low_count = len(strategy.coverage_summary.low_confidence)
            high_count = len(strategy.coverage_summary.high_confidence)
            if high_count >= 2:
                base = min(100, base + 8)
            if low_count >= 3:
                base = max(0, base - 12)

        self_confidence = _focus_confidence(strategy, "self-worth / self-criticism")
        emotion_confidence = _focus_confidence(strategy, "emotion regulation")
        if self_confidence == STRATEGY_CONFIDENCE_LOW:
            base = max(0, base - 10)
        if emotion_confidence == STRATEGY_CONFIDENCE_HIGH:
            base = min(100, base + 5)

    if coverage_report is not None:
        critical_levels = [
            _level_score(_domain_level(coverage_report, domain_id))
            for domain_id in (
                SELF_DOMAIN,
                EMOTION_REGULATION_DOMAIN,
                VALUES_IDENTITY_DOMAIN,
                MEANING_DOMAIN,
            )
        ]
        coverage_blend = round(sum(critical_levels) / len(critical_levels))
        base = round((base + coverage_blend) / 2)

    return base


def _scenario_component_score(scenario_blueprint: ScenarioBlueprint | None) -> int:
    if scenario_blueprint is None:
        return 50
    if not scenario_blueprint.confidence_phases:
        return 55

    phase_scores = [
        CONFIDENCE_SCORES.get(phase.confidence, 50)
        for phase in scenario_blueprint.confidence_phases
    ]
    base = round(sum(phase_scores) / len(phase_scores))

    if scenario_blueprint.confidence_summary is not None:
        summary = scenario_blueprint.confidence_summary
        if summary.direct_personalization:
            base = min(100, base + 8)
        if len(summary.exploratory_only) >= 3:
            base = max(0, base - 10)
    return base


def _profile_confidence_score(
    fingerprint: dict,
    coverage_report: FingerprintCoverageReport,
    strategy: InterventionStrategy,
    detected_patterns: set[str],
) -> int:
    if not detected_patterns:
        return 10

    scores = [
        _level_score(_domain_level(coverage_report, "presenting_problem")),
        _level_score(_domain_level(coverage_report, "patterns")),
    ]

    if strategy.coverage_summary is not None:
        low = len(strategy.coverage_summary.low_confidence)
        high = len(strategy.coverage_summary.high_confidence)
        if high >= 2:
            scores.append(85)
        elif low >= 3:
            scores.append(25)
        else:
            scores.append(60)
    else:
        scores.append(50)

    overview = str(fingerprint.get("summary_text", "")).strip()
    if overview and "not enough evidence" not in overview.lower():
        scores.append(75)
    else:
        scores.append(30)

    return round(sum(scores) / len(scores))


def _focus_confidence(strategy: InterventionStrategy, focus_area: str) -> str | None:
    for item in strategy.focus_confidence:
        if item.focus_area == focus_area:
            return item.confidence
    return None


def _worldview_profile_from_fingerprint(
    fingerprint: dict,
    detected_patterns: set[str],
    semantic_facts: list[SemanticFact],
    completed_assessments: dict[str, list[AssessmentResult]],
) -> SpiritualityWorldviewProfile:
    payload = fingerprint.get("spirituality_worldview")
    if payload:
        return SpiritualityWorldviewProfile.from_dict(payload)

    assessment_results = [
        result
        for module_results in completed_assessments.values()
        for result in module_results
    ]
    if not assessment_results:
        for item in fingerprint.get("assessment_results", []):
            if not isinstance(item, dict):
                continue
            assessment_results.append(
                AssessmentResult(
                    domain_id=str(item.get("domain_id", "")),
                    score=float(item.get("score", 0.0)),
                    normalized_score=float(item.get("normalized_score", 0.0)),
                    interpretation=str(item.get("interpretation", "")),
                    fingerprint_dimension=str(item.get("fingerprint_dimension", "patterns")),
                )
            )

    return build_spirituality_worldview_profile(
        presenting_problem=fingerprint.get("presenting_problem"),
        pattern_ids=detected_patterns,
        semantic_facts=semantic_facts,
        assessment_results=assessment_results,
    )


def _orientation_for_readiness(profile: SpiritualityWorldviewProfile) -> str:
    mapping = {
        ORIENTATION_ATHEIST: SPIRITUAL_ORIENTATION_ATHEIST,
        ORIENTATION_SECULAR_HUMANIST: SPIRITUAL_ORIENTATION_ATHEIST,
        ORIENTATION_AGNOSTIC: SPIRITUAL_ORIENTATION_AGNOSTIC,
        ORIENTATION_SPIRITUAL_NOT_RELIGIOUS: SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
        ORIENTATION_CHRISTIAN: SPIRITUAL_ORIENTATION_CHRISTIAN,
        ORIENTATION_RELIGION_AVERSE: SPIRITUAL_ORIENTATION_RELIGION_AVERSE,
        ORIENTATION_NATURE_SPIRITUAL: SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
        "symbolic_open": SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
        "skeptical_open": SPIRITUAL_ORIENTATION_AGNOSTIC,
        "religious_other": SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
    }
    return mapping.get(profile.worldview_orientation, SPIRITUAL_ORIENTATION_UNKNOWN)


def _apply_worldview_readiness_notes(
    profile: SpiritualityWorldviewProfile,
    warnings: list[str],
    next_steps: list[str],
) -> None:
    if profile.worldview_orientation == ORIENTATION_RELIGION_AVERSE:
        if profile.avoided_symbolic_language:
            next_steps.append(
                "Respect explicit avoided symbolic language before using personalized framing."
            )
        else:
            warnings.append(
                "Religion-averse orientation noted; confirm avoided language explicitly."
            )
    elif profile.worldview_orientation == ORIENTATION_CHRISTIAN:
        if profile.religious_language_comfort in {COMFORT_ALLOWED, COMFORT_PREFERRED}:
            next_steps.append(
                "Christian-compatible symbolic language is allowed when explicitly accepted."
            )
        else:
            warnings.append(
                "Christian orientation noted without explicit religious language comfort."
            )
    elif profile.worldview_orientation in {ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST}:
        if profile.icaros_language_constraints:
            next_steps.append(
                "Secular symbolic constraints are clear; avoid religious framing."
            )


def _spiritual_orientation_understood(
    coverage_report: FingerprintCoverageReport,
    profile: SpiritualityWorldviewProfile,
    detected_patterns: set[str],
    semantic_facts: list[SemanticFact],
) -> bool:
    worldview_level = _domain_level(coverage_report, SPIRITUALITY_WORLDVIEW_DOMAIN)
    if worldview_level in {COVERAGE_LEVEL_GOOD, COVERAGE_LEVEL_COMPLETE}:
        return True
    if profile.worldview_orientation != ORIENTATION_UNKNOWN:
        return True
    if profile.religious_language_comfort != "unknown":
        return True
    if detected_patterns & SPIRITUAL_PATTERN_IDS:
        return True
    if _domain_level(coverage_report, MEANING_DOMAIN) in {
        COVERAGE_LEVEL_GOOD,
        COVERAGE_LEVEL_COMPLETE,
    }:
        return True
    for fact in semantic_facts:
        if fact.attribute in {
            "session_openness",
            "meaning_sense",
            "change_desire",
            "worldview_orientation",
            "religious_language_comfort",
        }:
            return True
    return False


def _infer_spiritual_orientation(
    detected_patterns: set[str],
    semantic_facts: list[SemanticFact],
    coverage_report: FingerprintCoverageReport,
) -> str:
    profile = build_spirituality_worldview_profile(
        pattern_ids=detected_patterns,
        semantic_facts=semantic_facts,
    )
    return _orientation_for_readiness(profile)


def _missing_information(
    coverage_report: FingerprintCoverageReport,
    spiritual_understood: bool,
    detected_patterns: set[str],
    completed_assessments: dict[str, list[AssessmentResult]],
) -> list[str]:
    missing: list[str] = []
    for domain_id in (
        SELF_DOMAIN,
        EMOTION_REGULATION_DOMAIN,
        VALUES_IDENTITY_DOMAIN,
        MEANING_DOMAIN,
        "big_five",
    ):
        if _domain_level(coverage_report, domain_id) in {
            COVERAGE_LEVEL_UNKNOWN,
            COVERAGE_LEVEL_PARTIAL,
        }:
            missing.append(domain_id)

    if not spiritual_understood:
        missing.append("spiritual_orientation")

    if not detected_patterns:
        missing.append("observed_patterns")

    if not completed_assessments:
        missing.append("completed_assessments")

    return missing


def _recommend_language_style(
    strategy: InterventionStrategy,
    coverage_report: FingerprintCoverageReport,
) -> dict[str, str]:
    self_level = _domain_level(coverage_report, SELF_DOMAIN)
    identity_language = "allowed"
    if self_level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}:
        identity_language = "cautious"

    affirmation = "gentle"
    if strategy.emotional_intensity in {"low", "low_to_medium"}:
        affirmation = "gentle"
    elif strategy.emotional_intensity in {"medium_to_high", "high", "very_high"}:
        affirmation = "steady"

    return {
        "directness": strategy.directness,
        "metaphor": strategy.metaphor_level,
        "repetition": strategy.repetition_level,
        "rhythm": strategy.pacing,
        "affirmation": affirmation,
        "identity_language": identity_language,
    }


def _recommend_symbolic_style(
    strategy: InterventionStrategy,
    spiritual_orientation: str,
    spiritual_understood: bool,
    worldview_profile: SpiritualityWorldviewProfile | None = None,
) -> dict[str, str]:
    style = {
        "nature": SYMBOL_PREFERENCE_NEUTRAL,
        "religious": SYMBOL_PREFERENCE_NEUTRAL,
        "ancestral": SYMBOL_PREFERENCE_NEUTRAL,
        "light": SYMBOL_PREFERENCE_NEUTRAL,
        "body": _body_focus_level(strategy.body_focus),
    }

    if worldview_profile is not None:
        for symbol in worldview_profile.avoided_symbolic_language:
            if symbol in {"god", "christ", "prayer", "religion"}:
                style["religious"] = SYMBOL_PREFERENCE_AVOID
            if symbol == "ancestors":
                style["ancestral"] = SYMBOL_PREFERENCE_AVOID
        for symbol in worldview_profile.symbolic_language_preferences:
            if symbol == "nature":
                style["nature"] = SYMBOL_PREFERENCE_PREFERRED
            if symbol in {"god", "christ", "prayer", "holy_spirit"}:
                style["religious"] = SYMBOL_PREFERENCE_PREFERRED
            if symbol == "light":
                style["light"] = SYMBOL_PREFERENCE_PREFERRED
            if symbol == "ancestors":
                style["ancestral"] = SYMBOL_PREFERENCE_PREFERRED

    if not spiritual_understood:
        style["religious"] = SYMBOL_PREFERENCE_AVOID
        style["light"] = SYMBOL_PREFERENCE_NEUTRAL
        return style

    if spiritual_orientation == SPIRITUAL_ORIENTATION_ATHEIST:
        style["religious"] = SYMBOL_PREFERENCE_AVOID
        style["nature"] = SYMBOL_PREFERENCE_PREFERRED
        style["light"] = SYMBOL_PREFERENCE_NEUTRAL
    elif spiritual_orientation == SPIRITUAL_ORIENTATION_CHRISTIAN:
        if (
            worldview_profile is not None
            and worldview_profile.religious_language_comfort
            in {COMFORT_ALLOWED, COMFORT_PREFERRED}
        ):
            style["religious"] = SYMBOL_PREFERENCE_PREFERRED
            style["light"] = SYMBOL_PREFERENCE_PREFERRED
        else:
            style["religious"] = SYMBOL_PREFERENCE_NEUTRAL
    elif spiritual_orientation == SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS:
        style["nature"] = SYMBOL_PREFERENCE_PREFERRED
        style["light"] = SYMBOL_PREFERENCE_PREFERRED
        style["religious"] = SYMBOL_PREFERENCE_AVOID
    elif spiritual_orientation == SPIRITUAL_ORIENTATION_AGNOSTIC:
        style["religious"] = SYMBOL_PREFERENCE_AVOID
        style["nature"] = SYMBOL_PREFERENCE_NEUTRAL
    elif spiritual_orientation == SPIRITUAL_ORIENTATION_RELIGION_AVERSE:
        style["religious"] = SYMBOL_PREFERENCE_AVOID

    if strategy.spirituality_focus in {"medium_to_high", "high", "very_high"}:
        style["light"] = SYMBOL_PREFERENCE_PREFERRED

    return style


def _body_focus_level(body_focus: str) -> str:
    if body_focus in {"high", "very_high"}:
        return "high"
    if body_focus in {"medium", "medium_to_high"}:
        return "medium"
    return "low"


def _readiness_level_label(score: int) -> str:
    if score < 40:
        return READINESS_NOT_READY
    if score < 70:
        return READINESS_PARTIALLY_READY
    if score < 85:
        return READINESS_READY_WITH_LIMITATIONS
    return READINESS_READY


def _confidence_label(score: int, blocking_domains: list[str]) -> str:
    if blocking_domains or score < 40:
        return CONFIDENCE_LOW
    if score < 85:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_HIGH
