"""Pattern-Person Fit — evaluates therapeutic language pattern compatibility.

Does not generate Icaros. Deterministic gate before future TLE pattern selection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageReport,
)
from niros.icaros_readiness import (
    READINESS_NOT_READY,
    IcarosReadinessResult,
    SELF_DOMAIN,
    EMOTION_REGULATION_DOMAIN,
    VALUES_IDENTITY_DOMAIN,
)
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    STRATEGY_CONFIDENCE_MEDIUM,
    InterventionStrategy,
)
from niros.scenario_blueprint import ScenarioBlueprint
from niros.spirituality_worldview import (
    COMFORT_ALLOWED,
    COMFORT_PREFERRED,
    ORIENTATION_AGNOSTIC,
    ORIENTATION_ATHEIST,
    ORIENTATION_CHRISTIAN,
    ORIENTATION_RELIGION_AVERSE,
    ORIENTATION_SECULAR_HUMANIST,
    ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
    ORIENTATION_SKEPTICAL_OPEN,
    ORIENTATION_SYMBOLIC_OPEN,
    ORIENTATION_NATURE_SPIRITUAL,
    SpiritualityWorldviewProfile,
)

FIT_LEVEL_POOR = "poor"
FIT_LEVEL_POSSIBLE = "possible"
FIT_LEVEL_GOOD = "good"
FIT_LEVEL_STRONG = "strong"

CONFIDENCE_LOW = "low"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_HIGH = "high"

RELIGIOUS_SYMBOLS = frozenset(
    {
        "god",
        "prayer",
        "angels",
        "salvation",
        "christ",
        "holy_spirit",
        "divine",
        "religion",
        "supernatural",
        "supernatural_claims",
    }
)

RELIGIOUS_SEMANTIC_TOKENS = frozenset(
    {"prayer", "divine", "god", "salvation", "angels", "christ", "surrender"}
)

WORLDVIEW_COMPAT_KEYS: dict[str, str] = {
    ORIENTATION_ATHEIST: "atheist",
    ORIENTATION_SECULAR_HUMANIST: "secular",
    ORIENTATION_AGNOSTIC: "agnostic",
    ORIENTATION_SPIRITUAL_NOT_RELIGIOUS: "spiritual_but_not_religious",
    ORIENTATION_CHRISTIAN: "christian",
    ORIENTATION_RELIGION_AVERSE: "religion_averse",
    ORIENTATION_NATURE_SPIRITUAL: "nature_spiritual",
    ORIENTATION_SYMBOLIC_OPEN: "symbolic_open",
    ORIENTATION_SKEPTICAL_OPEN: "skeptical_open",
}

SPIRITUAL_NOT_RELIGIOUS_CLUSTERS = frozenset({"nature", "breath", "light", "inner_wisdom"})

MIN_SELECT_SCORE = 40


@dataclass(frozen=True)
class CandidateTherapeuticPattern:
    id: str
    psychological_function: tuple[str, ...]
    good_for: tuple[str, ...]
    avoid_if: tuple[str, ...]
    language_style: tuple[str, ...]
    rhythm: str
    semantic_cluster: tuple[str, ...]
    spiritual_compatibility: tuple[str, ...]
    requires_symbols: tuple[str, ...] = ()
    forbidden_symbols: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CandidateTherapeuticPattern:
        return cls(
            id=str(payload["id"]),
            psychological_function=tuple(payload.get("psychological_function", ())),
            good_for=tuple(payload.get("good_for", ())),
            avoid_if=tuple(payload.get("avoid_if", ())),
            language_style=tuple(payload.get("language_style", ())),
            rhythm=str(payload.get("rhythm", "")),
            semantic_cluster=tuple(payload.get("semantic_cluster", ())),
            spiritual_compatibility=tuple(payload.get("spiritual_compatibility", ())),
            requires_symbols=tuple(payload.get("requires_symbols", ())),
            forbidden_symbols=tuple(payload.get("forbidden_symbols", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "psychological_function": list(self.psychological_function),
            "good_for": list(self.good_for),
            "avoid_if": list(self.avoid_if),
            "language_style": list(self.language_style),
            "rhythm": self.rhythm,
            "semantic_cluster": list(self.semantic_cluster),
            "spiritual_compatibility": list(self.spiritual_compatibility),
            "requires_symbols": list(self.requires_symbols),
            "forbidden_symbols": list(self.forbidden_symbols),
        }


@dataclass(frozen=True)
class SelectedPatternFit:
    id: str
    fit_score: int
    fit_level: str
    why_selected: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fit_score": self.fit_score,
            "fit_level": self.fit_level,
            "why_selected": list(self.why_selected),
            "constraints": list(self.constraints),
        }


@dataclass(frozen=True)
class RejectedPatternFit:
    id: str
    reason: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "reason": list(self.reason)}


@dataclass(frozen=True)
class PatternPersonFitResult:
    selected_patterns: tuple[SelectedPatternFit, ...] = field(default_factory=tuple)
    rejected_patterns: tuple[RejectedPatternFit, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    overall_fit_confidence: str = CONFIDENCE_LOW
    blocking_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_patterns": [item.to_dict() for item in self.selected_patterns],
            "rejected_patterns": [item.to_dict() for item in self.rejected_patterns],
            "warnings": list(self.warnings),
            "overall_fit_confidence": self.overall_fit_confidence,
            "blocking_reason": self.blocking_reason,
        }


class PatternPersonFitEvaluator:
    """Deterministic compatibility audit for candidate therapeutic language patterns."""

    def evaluate(
        self,
        *,
        fingerprint: dict,
        coverage_report: FingerprintCoverageReport,
        strategy: InterventionStrategy,
        scenario_blueprint: ScenarioBlueprint | None,
        icaros_readiness: IcarosReadinessResult,
        spirituality_worldview: SpiritualityWorldviewProfile,
        candidate_patterns: Iterable[CandidateTherapeuticPattern],
    ) -> PatternPersonFitResult:
        if icaros_readiness.readiness_level == READINESS_NOT_READY:
            return PatternPersonFitResult(
                blocking_reason=(
                    "Icaros readiness is Not Ready; pattern selection is blocked until "
                    "critical fingerprint gaps are resolved."
                ),
                warnings=tuple(icaros_readiness.warnings),
                overall_fit_confidence=CONFIDENCE_LOW,
            )

        detected = _detected_pattern_ids(fingerprint)
        context = _EvaluationContext(
            fingerprint=fingerprint,
            coverage_report=coverage_report,
            strategy=strategy,
            scenario_blueprint=scenario_blueprint,
            icaros_readiness=icaros_readiness,
            worldview=spirituality_worldview,
            detected_patterns=detected,
        )

        selected: list[SelectedPatternFit] = []
        rejected: list[RejectedPatternFit] = []
        warnings: list[str] = list(icaros_readiness.warnings)

        for pattern in candidate_patterns:
            reject_reasons = _hard_reject_reasons(pattern, context)
            if reject_reasons:
                rejected.append(RejectedPatternFit(id=pattern.id, reason=tuple(reject_reasons)))
                continue

            score, why, constraints = _score_pattern(pattern, context)
            if score < MIN_SELECT_SCORE:
                rejected.append(
                    RejectedPatternFit(
                        id=pattern.id,
                        reason=(f"Fit score too low ({score}); {FIT_LEVEL_POOR} compatibility.",),
                    )
                )
                continue

            selected.append(
                SelectedPatternFit(
                    id=pattern.id,
                    fit_score=score,
                    fit_level=_fit_level_label(score),
                    why_selected=tuple(why),
                    constraints=tuple(constraints),
                )
            )

        selected.sort(key=lambda item: (-item.fit_score, item.id))
        confidence = _overall_confidence(selected)

        return PatternPersonFitResult(
            selected_patterns=tuple(selected),
            rejected_patterns=tuple(rejected),
            warnings=tuple(dict.fromkeys(warnings)),
            overall_fit_confidence=confidence,
        )


@dataclass
class _EvaluationContext:
    fingerprint: dict
    coverage_report: FingerprintCoverageReport
    strategy: InterventionStrategy
    scenario_blueprint: ScenarioBlueprint | None
    icaros_readiness: IcarosReadinessResult
    worldview: SpiritualityWorldviewProfile
    detected_patterns: set[str]


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


def _hard_reject_reasons(
    pattern: CandidateTherapeuticPattern,
    context: _EvaluationContext,
) -> list[str]:
    reasons: list[str] = []

    for avoid_token in pattern.avoid_if:
        if _token_matches_detected(avoid_token, context.detected_patterns):
            reasons.append(f"Detected signal matches avoid_if: {avoid_token}")

    if _pattern_uses_religious_language(pattern):
        orientation = context.worldview.worldview_orientation
        if orientation in {ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST}:
            reasons.append("Secular or atheist worldview rejects religious language patterns")
        elif orientation == ORIENTATION_RELIGION_AVERSE:
            reasons.append("User is religion-averse; religious framing is not compatible")

    if orientation := context.worldview.worldview_orientation:
        if orientation == ORIENTATION_RELIGION_AVERSE and _pattern_is_religious(pattern):
            if "User is religion-averse" not in " ".join(reasons):
                reasons.append("User is religion-averse; religious framing is not compatible")

    if context.worldview.worldview_orientation == ORIENTATION_CHRISTIAN:
        comfort = context.worldview.religious_language_comfort
        if _pattern_is_religious(pattern) and comfort not in {COMFORT_ALLOWED, COMFORT_PREFERRED}:
            reasons.append(
                "Christian-compatible patterns require explicit religious language comfort"
            )
        elif _pattern_is_religious(pattern) and "christian" not in pattern.spiritual_compatibility:
            reasons.append("Pattern is not marked Christian-compatible")

    compat_key = WORLDVIEW_COMPAT_KEYS.get(context.worldview.worldview_orientation, "")
    if compat_key and pattern.spiritual_compatibility:
        if compat_key not in pattern.spiritual_compatibility and not reasons:
            if _pattern_is_religious(pattern) or pattern.requires_symbols:
                reasons.append(
                    f"Pattern spiritual compatibility does not include {compat_key.replace('_', ' ')} worldview"
                )

    avoided = set(context.worldview.avoided_symbolic_language)
    orientation = context.worldview.worldview_orientation
    for symbol in pattern.requires_symbols:
        if symbol in avoided:
            reasons.append(f"Required symbol '{symbol}' is avoided by this person")
        elif symbol in RELIGIOUS_SYMBOLS and orientation in {
            ORIENTATION_ATHEIST,
            ORIENTATION_SECULAR_HUMANIST,
            ORIENTATION_RELIGION_AVERSE,
        }:
            reasons.append(f"Required religious symbol '{symbol}' is incompatible with worldview")

    for symbol in pattern.semantic_cluster:
        if symbol in avoided:
            reasons.append(f"Pattern semantic cluster uses avoided symbol: {symbol}")

    if _self_confidence_low(context) and _is_intense_identity_pattern(pattern):
        reasons.append("Self domain confidence is low; intense identity reconstruction is blocked")

    if _values_identity_unknown(context) and _uses_destiny_mission_language(pattern):
        reasons.append("Values and identity are unknown; destiny or mission language is blocked")

    if context.worldview.worldview_orientation in {ORIENTATION_AGNOSTIC, ORIENTATION_SKEPTICAL_OPEN}:
        if _uses_certainty_language(pattern):
            reasons.append("Agnostic worldview avoids certainty or dogmatic language")

    return list(dict.fromkeys(reasons))


def _score_pattern(
    pattern: CandidateTherapeuticPattern,
    context: _EvaluationContext,
) -> tuple[int, list[str], list[str]]:
    score = 45
    why: list[str] = []
    constraints: list[str] = []

    good_matches = [
        token
        for token in pattern.good_for
        if _token_matches_detected(token, context.detected_patterns)
    ]
    if good_matches:
        bonus = min(30, len(good_matches) * 12)
        score += bonus
        for token in good_matches:
            why.append(f"Matches {token.replace('_', ' ')} pattern")

    if _strategy_aligns(pattern, context.strategy):
        score += 12
        why.append("Aligns with current session strategy focus")

    for item in context.strategy.focus_confidence:
        if item.focus_area == "self-worth / self-criticism" and item.confidence == STRATEGY_CONFIDENCE_HIGH:
            if "self_worth" in pattern.psychological_function or "identity" in pattern.semantic_cluster:
                score += 8
                why.append("Matches self-worth / self-criticism strategy focus")
                break

    if _worldview_supports_pattern(pattern, context.worldview):
        score += 10
        compat = context.worldview.worldview_orientation.replace("_", " ")
        why.append(f"Compatible with {compat} worldview")

    if _emotion_regulation_low(context) and _is_grounding_pattern(pattern):
        score += 15
        why.append("Grounding pattern preferred while emotion regulation coverage is limited")

    if context.worldview.worldview_orientation in {
        ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
        ORIENTATION_NATURE_SPIRITUAL,
        ORIENTATION_SYMBOLIC_OPEN,
    }:
        if SPIRITUAL_NOT_RELIGIOUS_CLUSTERS & set(pattern.semantic_cluster):
            score += 12
            why.append("Matches nature / breath / light / inner wisdom preferences")

    if context.worldview.worldview_orientation in {ORIENTATION_AGNOSTIC, ORIENTATION_SKEPTICAL_OPEN}:
        if _uses_uncertainty_language(pattern):
            score += 10
            why.append("Uses symbolic uncertainty suited to agnostic openness")

    constraints.extend(_pattern_constraints(pattern, context.worldview))
    if context.worldview.icaros_language_constraints:
        for item in context.worldview.icaros_language_constraints:
            if item not in constraints:
                constraints.append(item)

    return max(0, min(100, score)), why, constraints


def _fit_level_label(score: int) -> str:
    if score >= 85:
        return FIT_LEVEL_STRONG
    if score >= 70:
        return FIT_LEVEL_GOOD
    if score >= 40:
        return FIT_LEVEL_POSSIBLE
    return FIT_LEVEL_POOR


def _overall_confidence(selected: list[SelectedPatternFit]) -> str:
    if not selected:
        return CONFIDENCE_LOW
    best = selected[0].fit_score
    if best >= 85:
        return CONFIDENCE_HIGH
    if best >= 70:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW


def _token_matches_detected(token: str, detected: set[str]) -> bool:
    normalized = token.lower().replace("-", "_")
    for pattern_id in detected:
        pid = pattern_id.lower().replace("-", "_")
        if normalized in pid or pid in normalized:
            return True
        if normalized in pid.split("_") or any(normalized in part for part in pid.split("_")):
            return True
    return False


def _pattern_uses_religious_language(pattern: CandidateTherapeuticPattern) -> bool:
    if pattern.requires_symbols and RELIGIOUS_SYMBOLS.intersection(pattern.requires_symbols):
        return True
    if RELIGIOUS_SEMANTIC_TOKENS.intersection(pattern.semantic_cluster):
        return True
    if "prayer_language" in pattern.language_style or "faith_language" in pattern.language_style:
        return True
    return False


def _pattern_is_religious(pattern: CandidateTherapeuticPattern) -> bool:
    return _pattern_uses_religious_language(pattern)


def _is_intense_identity_pattern(pattern: CandidateTherapeuticPattern) -> bool:
    return (
        "identity_repetition" in pattern.language_style
        and "identity" in pattern.semantic_cluster
        and "power" not in pattern.semantic_cluster
    )


def _is_grounding_pattern(pattern: CandidateTherapeuticPattern) -> bool:
    return "grounding" in pattern.semantic_cluster or "grounding_language" in pattern.language_style


def _uses_destiny_mission_language(pattern: CandidateTherapeuticPattern) -> bool:
    if "mission" in pattern.semantic_cluster or "destiny" in pattern.semantic_cluster:
        return True
    return "destiny_language" in pattern.language_style or "mission_framing" in pattern.language_style


def _uses_certainty_language(pattern: CandidateTherapeuticPattern) -> bool:
    return (
        "certainty_language" in pattern.language_style
        or "dogmatic_framing" in pattern.language_style
        or "dogma" in pattern.semantic_cluster
        or "certainty" in pattern.semantic_cluster
    )


def _uses_uncertainty_language(pattern: CandidateTherapeuticPattern) -> bool:
    return (
        "uncertainty_language" in pattern.language_style
        or "symbolic_openness" in pattern.language_style
    )


def _self_confidence_low(context: _EvaluationContext) -> bool:
    domain = context.coverage_report.domains.get(SELF_DOMAIN)
    if domain is None:
        return True
    return domain.level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}


def _emotion_regulation_low(context: _EvaluationContext) -> bool:
    domain = context.coverage_report.domains.get(EMOTION_REGULATION_DOMAIN)
    if domain is None:
        return True
    return domain.level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}


def _values_identity_unknown(context: _EvaluationContext) -> bool:
    domain = context.coverage_report.domains.get(VALUES_IDENTITY_DOMAIN)
    if domain is None:
        return True
    return domain.level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}


def _worldview_supports_pattern(
    pattern: CandidateTherapeuticPattern,
    worldview: SpiritualityWorldviewProfile,
) -> bool:
    compat_key = WORLDVIEW_COMPAT_KEYS.get(worldview.worldview_orientation, "")
    if not compat_key or not pattern.spiritual_compatibility:
        return not _pattern_is_religious(pattern)
    return compat_key in pattern.spiritual_compatibility


def _strategy_aligns(pattern: CandidateTherapeuticPattern, strategy: InterventionStrategy) -> bool:
    focus_tokens: set[str] = set()
    for item in strategy.focus_confidence:
        if item.confidence in {STRATEGY_CONFIDENCE_HIGH, STRATEGY_CONFIDENCE_MEDIUM}:
            focus_tokens.update(item.focus_area.lower().replace("/", " ").split())

    cluster_and_function = set(pattern.semantic_cluster) | set(pattern.psychological_function)
    for token in focus_tokens:
        if any(token in value or value in token for value in cluster_and_function):
            return True
        if token in {"self", "worth", "criticism"} and "self_worth" in pattern.psychological_function:
            return True
        if token in {"emotion", "regulation"} and "regulation" in pattern.psychological_function:
            return True
        if token in {"meaning", "purpose"} and "meaning" in pattern.psychological_function:
            return True
    if strategy.grounding_priority in {"high", "very_high"} and _is_grounding_pattern(pattern):
        return True
    return False


def _pattern_constraints(
    pattern: CandidateTherapeuticPattern,
    worldview: SpiritualityWorldviewProfile,
) -> list[str]:
    constraints: list[str] = []
    orientation = worldview.worldview_orientation

    if orientation in {ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST}:
        constraints.append("Use secular identity language")
        constraints.append("Avoid religious symbolism")
    elif orientation == ORIENTATION_RELIGION_AVERSE:
        constraints.append("Avoid religious framing")
    elif orientation == ORIENTATION_CHRISTIAN and worldview.religious_language_comfort in {
        COMFORT_ALLOWED,
        COMFORT_PREFERRED,
    }:
        constraints.append("Christian-compatible language allowed when explicitly accepted")
    elif orientation in {ORIENTATION_AGNOSTIC, ORIENTATION_SKEPTICAL_OPEN}:
        constraints.append("Avoid certainty about metaphysical claims")
    elif orientation in {ORIENTATION_SPIRITUAL_NOT_RELIGIOUS, ORIENTATION_NATURE_SPIRITUAL}:
        constraints.append("Prefer nature, breath, or light imagery")

    if worldview.avoided_symbolic_language:
        constraints.append(
            "Avoid symbols: " + ", ".join(worldview.avoided_symbolic_language)
        )

    return list(dict.fromkeys(constraints))


def render_pattern_person_fit_section(result: PatternPersonFitResult) -> str:
    lines = ["===== PATTERN-PERSON FIT ====="]
    if result.blocking_reason:
        lines.append(f"Blocked: {result.blocking_reason}")
        return "\n".join(lines)

    lines.append(f"Overall fit confidence: {result.overall_fit_confidence}")
    lines.append("")
    lines.append("Selected patterns:")
    if result.selected_patterns:
        for item in result.selected_patterns:
            lines.append(f"- {item.id} ({item.fit_score}% — {item.fit_level})")
            for reason in item.why_selected:
                lines.append(f"  - {reason}")
            for constraint in item.constraints:
                lines.append(f"  - Constraint: {constraint}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Rejected patterns:")
    if result.rejected_patterns:
        for item in result.rejected_patterns:
            lines.append(f"- {item.id}")
            for reason in item.reason:
                lines.append(f"  - {reason}")
    else:
        lines.append("- None")

    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)

    return "\n".join(lines)
