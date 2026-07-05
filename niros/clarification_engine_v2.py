"""Clarification Engine v2 — selects precise clarification questions without guessing.

Does not mutate Human Digital Fingerprint or replace Adaptive Interview logic.
Deterministic and optional.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from niros.assessment import AssessmentResult
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageReport,
)
from niros.icaros_readiness import IcarosReadinessResult, SPIRITUAL_ORIENTATION_UNKNOWN
from niros.semantic_signal_fingerprint_bridge import (
    FORBIDDEN_BRIDGE_PHRASES,
    SIGNAL_PROPOSAL_DOMAIN,
    FingerprintUpdateProposal,
)
from niros.semantic_signal_graph import SemanticOpenQuestion, SemanticSignalGraph

NEED_LOW = "low"
NEED_MEDIUM = "medium"
NEED_HIGH = "high"

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

SOURCE_PROPOSAL = "proposal"
SOURCE_GRAPH = "graph"
SOURCE_COVERAGE = "coverage"
SOURCE_WORLDVIEW = "worldview"

CRITICAL_COVERAGE_DOMAINS: tuple[tuple[str, str, int], ...] = (
    ("self", "self_domain", 400),
    ("emotion_regulation", "emotion_regulation_domain", 390),
    ("values_identity", "values_identity_domain", 380),
    ("meaning_purpose", "meaning", 370),
    ("spirituality_worldview", "spirituality_worldview", 360),
)

PROPOSAL_TO_COVERAGE_DOMAIN: dict[str, str] = {
    "self": "self_domain",
    "emotion_regulation": "emotion_regulation_domain",
    "values_identity": "values_identity_domain",
    "meaning_purpose": "meaning",
    "spirituality_worldview": "spirituality_worldview",
    "relationships": "relationships_domain",
    "grief_loss": "grief_loss_bereavement",
}

DOMAIN_FALLBACK_QUESTIONS: dict[str, tuple[str, str, str]] = {
    "self": (
        "self",
        "When you think about yourself lately, what feels most difficult or strained?",
        "Self-related understanding is still limited.",
    ),
    "emotion_regulation": (
        "emotion_regulation",
        "What usually happens inside you when strong feelings come up?",
        "Emotional regulation patterns are not yet clear.",
    ),
    "values_identity": (
        "values_identity",
        "What matters most to you right now, and what feels out of alignment?",
        "Values and identity coverage remains limited.",
    ),
    "meaning_purpose": (
        "meaning_purpose",
        "What currently gives your days a sense of meaning or direction?",
        "Meaning and purpose coverage remains limited.",
    ),
}

WORLDVIEW_CLARIFICATION_QUESTION = (
    "Are there any spiritual, religious, or symbolic words that feel meaningful or uncomfortable for you?"
)
WORLDVIEW_TARGET_SIGNAL = "symbolic_language_comfort"
WORLDVIEW_REASON = (
    "Spiritual / worldview orientation is unknown and symbolic language may affect future personalization."
)

FORBIDDEN_CLARIFICATION_PHRASES = frozenset(FORBIDDEN_BRIDGE_PHRASES) | frozenset(
    {
        "symptom severity",
        "clarify identity dissonance",
    }
)


@dataclass(frozen=True)
class ClarificationQuestion:
    id: str
    question: str
    target_signal: str
    target_domain: str
    priority: str
    reason: str
    expected_information_gain: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "target_signal": self.target_signal,
            "target_domain": self.target_domain,
            "priority": self.priority,
            "reason": self.reason,
            "expected_information_gain": self.expected_information_gain,
        }


@dataclass(frozen=True)
class SkippedQuestion:
    question: str
    target_signal: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "target_signal": self.target_signal,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ClarificationPlan:
    questions: tuple[ClarificationQuestion, ...] = field(default_factory=tuple)
    skipped_questions: tuple[SkippedQuestion, ...] = field(default_factory=tuple)
    coverage_targets: tuple[str, ...] = field(default_factory=tuple)
    overall_need_for_clarification: str = NEED_LOW

    def to_dict(self) -> dict[str, Any]:
        return {
            "questions": [item.to_dict() for item in self.questions],
            "skipped_questions": [item.to_dict() for item in self.skipped_questions],
            "coverage_targets": list(self.coverage_targets),
            "overall_need_for_clarification": self.overall_need_for_clarification,
        }


@dataclass(frozen=True)
class _QuestionCandidate:
    question: str
    target_signal: str
    target_domain: str
    priority: str
    reason: str
    source: str
    score: int
    linked_to_ambiguity: bool


class ClarificationEngineV2:
    """Select the smallest set of high-value clarification questions."""

    def plan(
        self,
        graph: SemanticSignalGraph,
        proposal: FingerprintUpdateProposal,
        *,
        fingerprint_coverage: FingerprintCoverageReport | None = None,
        completed_assessments: Iterable[AssessmentResult] | None = None,
        icaros_readiness: IcarosReadinessResult | None = None,
        max_questions: int = 3,
    ) -> ClarificationPlan:
        del completed_assessments

        signal_domains = _signal_domains(proposal)
        linked_signals = _linked_clarification_signals(proposal)
        pre_skipped: list[SkippedQuestion] = []
        candidates = _collect_candidates(
            graph=graph,
            proposal=proposal,
            fingerprint_coverage=fingerprint_coverage,
            icaros_readiness=icaros_readiness,
            linked_signals=linked_signals,
            skipped=pre_skipped,
        )

        selected: list[_QuestionCandidate] = []
        skipped: list[SkippedQuestion] = list(pre_skipped)
        seen_questions: set[str] = set()

        for candidate in sorted(
            candidates,
            key=lambda item: (-item.score, PRIORITY_RANK[item.priority], item.target_signal, item.question),
        ):
            normalized = _normalize_question(candidate.question)
            if normalized in seen_questions:
                skipped.append(
                    SkippedQuestion(
                        question=candidate.question,
                        target_signal=candidate.target_signal,
                        reason="Duplicate question",
                    )
                )
                continue

            if (
                candidate.source == SOURCE_COVERAGE
                and not candidate.linked_to_ambiguity
                and _domain_is_complete(fingerprint_coverage, candidate.target_domain)
            ):
                skipped.append(
                    SkippedQuestion(
                        question=candidate.question,
                        target_signal=candidate.target_signal,
                        reason="Domain coverage already complete",
                    )
                )
                continue

            if len(selected) >= max_questions:
                skipped.append(
                    SkippedQuestion(
                        question=candidate.question,
                        target_signal=candidate.target_signal,
                        reason="Lower priority within max_questions limit",
                    )
                )
                continue

            seen_questions.add(normalized)
            selected.append(candidate)

        questions = tuple(
            ClarificationQuestion(
                id=_question_id(item.target_signal, index),
                question=item.question,
                target_signal=item.target_signal,
                target_domain=item.target_domain,
                priority=item.priority,
                reason=item.reason,
                expected_information_gain=_expected_information_gain(
                    priority=item.priority,
                    source=item.source,
                    linked_to_ambiguity=item.linked_to_ambiguity,
                ),
            )
            for index, item in enumerate(selected, start=1)
        )

        coverage_targets = _coverage_targets(
            questions=questions,
            signal_domains=signal_domains,
            fingerprint_coverage=fingerprint_coverage,
        )
        overall_need = _overall_need(
            questions=questions,
            proposal=proposal,
            fingerprint_coverage=fingerprint_coverage,
        )

        return ClarificationPlan(
            questions=questions,
            skipped_questions=tuple(skipped),
            coverage_targets=coverage_targets,
            overall_need_for_clarification=overall_need,
        )


def build_clarification_plan(
    graph: SemanticSignalGraph,
    proposal: FingerprintUpdateProposal,
    **kwargs: Any,
) -> ClarificationPlan:
    return ClarificationEngineV2().plan(graph, proposal, **kwargs)


def render_clarification_plan(plan: ClarificationPlan) -> str:
    lines = [
        "===== CLARIFICATION PLAN =====",
        f"Overall need: {plan.overall_need_for_clarification}",
        "",
        "Questions:",
    ]
    if plan.questions:
        for item in plan.questions:
            lines.append(
                f"- [{item.priority}] {item.question} "
                f"(signal={item.target_signal}, domain={item.target_domain}, "
                f"gain={item.expected_information_gain:.2f})"
            )
    else:
        lines.append("- (none)")

    if plan.coverage_targets:
        lines.append("")
        lines.append("Coverage targets: " + ", ".join(plan.coverage_targets))

    if plan.skipped_questions:
        lines.append("")
        lines.append("Skipped:")
        for item in plan.skipped_questions:
            lines.append(f"- {item.question} ({item.reason})")

    return "\n".join(lines)


def _collect_candidates(
    *,
    graph: SemanticSignalGraph,
    proposal: FingerprintUpdateProposal,
    fingerprint_coverage: FingerprintCoverageReport | None,
    icaros_readiness: IcarosReadinessResult | None,
    linked_signals: frozenset[str],
    skipped: list[SkippedQuestion],
) -> list[_QuestionCandidate]:
    candidates: list[_QuestionCandidate] = []

    for item in proposal.open_questions:
        target_domain = _domain_for_signal(item.target_signal)
        candidates.append(
            _QuestionCandidate(
                question=item.question,
                target_signal=item.target_signal,
                target_domain=target_domain,
                priority=item.priority,
                reason=_proposal_question_reason(item, proposal),
                source=SOURCE_PROPOSAL,
                score=_score_proposal_question(item, linked_signals),
                linked_to_ambiguity=item.target_signal in linked_signals,
            )
        )

    for item in graph.open_questions:
        target_domain = _domain_for_signal(item.target_signal)
        candidates.append(
            _QuestionCandidate(
                question=item.question,
                target_signal=item.target_signal,
                target_domain=target_domain,
                priority=item.priority,
                reason=item.reason or "Open question from semantic signal graph.",
                source=SOURCE_GRAPH,
                score=_score_graph_question(item, linked_signals),
                linked_to_ambiguity=item.target_signal in linked_signals,
            )
        )

    for short_domain, coverage_domain, base_score in CRITICAL_COVERAGE_DOMAINS:
        if short_domain == "spirituality_worldview":
            continue
        target_signal, question, reason = DOMAIN_FALLBACK_QUESTIONS[short_domain]
        if _domain_is_complete(fingerprint_coverage, short_domain):
            skipped.append(
                SkippedQuestion(
                    question=question,
                    target_signal=target_signal,
                    reason="Domain coverage already complete",
                )
            )
            continue
        if not _domain_needs_coverage(fingerprint_coverage, coverage_domain):
            continue
        candidates.append(
            _QuestionCandidate(
                question=question,
                target_signal=target_signal,
                target_domain=short_domain,
                priority="medium",
                reason=reason,
                source=SOURCE_COVERAGE,
                score=base_score,
                linked_to_ambiguity=False,
            )
        )

    if _needs_worldview_clarification(fingerprint_coverage, icaros_readiness):
        priority = _worldview_question_priority(icaros_readiness)
        candidates.append(
            _QuestionCandidate(
                question=WORLDVIEW_CLARIFICATION_QUESTION,
                target_signal=WORLDVIEW_TARGET_SIGNAL,
                target_domain="spirituality_worldview",
                priority=priority,
                reason=WORLDVIEW_REASON,
                source=SOURCE_WORLDVIEW,
                score=_worldview_question_score(fingerprint_coverage, icaros_readiness),
                linked_to_ambiguity=_worldview_ambiguity(proposal, icaros_readiness),
            )
        )

    return candidates


def _score_proposal_question(
    item: Any,
    linked_signals: frozenset[str],
) -> int:
    score = 1000
    if item.target_signal in linked_signals:
        score += 120
    if item.priority == "high":
        score += 20
    return score


def _score_graph_question(item: SemanticOpenQuestion, linked_signals: frozenset[str]) -> int:
    score = 900
    if item.target_signal in linked_signals:
        score += 80
    if item.priority == "high":
        score += 15
    return score


def _proposal_question_reason(item: Any, proposal: FingerprintUpdateProposal) -> str:
    for candidate in proposal.candidate_signals:
        if candidate.signal == item.target_signal:
            return (
                "Ambiguous expression may indicate multiple psychological meanings."
                if candidate.requires_clarification
                else candidate.reason
            )
    for blocked in proposal.blocked_updates:
        if blocked.signal == item.target_signal:
            return blocked.reason
    return "Clarification needed before fingerprint promotion."


def _linked_clarification_signals(proposal: FingerprintUpdateProposal) -> frozenset[str]:
    linked = {item.signal for item in proposal.candidate_signals if item.requires_clarification}
    linked.update(item.signal for item in proposal.blocked_updates)
    return frozenset(linked)


def _signal_domains(proposal: FingerprintUpdateProposal) -> set[str]:
    domains: set[str] = set()
    for item in proposal.candidate_signals:
        domains.add(item.domain)
    for item in proposal.accepted_signals:
        domains.add(item.domain)
    return domains


def _domain_for_signal(target_signal: str) -> str:
    return SIGNAL_PROPOSAL_DOMAIN.get(target_signal, target_signal)


def _normalize_question(text: str) -> str:
    return " ".join(text.lower().split())


def _question_id(target_signal: str, index: int) -> str:
    safe_signal = target_signal.replace(" ", "_")
    return f"clarify_{safe_signal}_{index:03d}"


def _expected_information_gain(
    *,
    priority: str,
    source: str,
    linked_to_ambiguity: bool,
) -> float:
    base = {"high": 0.87, "medium": 0.72, "low": 0.55}.get(priority, 0.55)
    source_bonus = {
        SOURCE_PROPOSAL: 0.05,
        SOURCE_GRAPH: 0.03,
        SOURCE_WORLDVIEW: 0.02,
        SOURCE_COVERAGE: 0.0,
    }.get(source, 0.0)
    ambiguity_bonus = 0.03 if linked_to_ambiguity else 0.0
    return round(min(0.95, base + source_bonus + ambiguity_bonus), 2)


def _domain_is_complete(
    fingerprint_coverage: FingerprintCoverageReport | None,
    domain: str,
) -> bool:
    if fingerprint_coverage is None:
        return False
    coverage_domain = PROPOSAL_TO_COVERAGE_DOMAIN.get(domain, domain)
    entry = fingerprint_coverage.domains.get(coverage_domain)
    if entry is None:
        return False
    return entry.level == COVERAGE_LEVEL_COMPLETE


def _domain_needs_coverage(
    fingerprint_coverage: FingerprintCoverageReport | None,
    coverage_domain: str,
) -> bool:
    if fingerprint_coverage is None:
        return False
    entry = fingerprint_coverage.domains.get(coverage_domain)
    if entry is None:
        return True
    return entry.level in {
        COVERAGE_LEVEL_UNKNOWN,
        COVERAGE_LEVEL_PARTIAL,
    }


def _needs_worldview_clarification(
    fingerprint_coverage: FingerprintCoverageReport | None,
    icaros_readiness: IcarosReadinessResult | None,
) -> bool:
    if icaros_readiness is not None:
        if icaros_readiness.spiritual_orientation == SPIRITUAL_ORIENTATION_UNKNOWN:
            return True
        if _icaros_warns_about_worldview_or_symbolic_language(icaros_readiness):
            return True

    if fingerprint_coverage is None:
        return False

    if _domain_is_complete(fingerprint_coverage, "spirituality_worldview"):
        return icaros_readiness is not None and (
            icaros_readiness.spiritual_orientation == SPIRITUAL_ORIENTATION_UNKNOWN
            or _icaros_warns_about_worldview_or_symbolic_language(icaros_readiness)
        )

    entry = fingerprint_coverage.domains.get("spirituality_worldview")
    if entry is None:
        return True
    return entry.level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}


def _icaros_warns_about_worldview_or_symbolic_language(
    icaros_readiness: IcarosReadinessResult,
) -> bool:
    for warning in icaros_readiness.warnings:
        lowered = warning.lower()
        if "symbolic language" in lowered or "worldview" in lowered:
            return True
    return False


def _worldview_question_score(
    fingerprint_coverage: FingerprintCoverageReport | None,
    icaros_readiness: IcarosReadinessResult | None,
) -> int:
    score = 355
    if fingerprint_coverage is not None and _domain_needs_coverage(
        fingerprint_coverage,
        "spirituality_worldview",
    ):
        score = max(score, 900)
    if icaros_readiness is not None:
        if icaros_readiness.spiritual_orientation == SPIRITUAL_ORIENTATION_UNKNOWN:
            score = max(score, 920)
        if _icaros_warns_about_worldview_or_symbolic_language(icaros_readiness):
            score = max(score, 925)
    return score


def _worldview_question_priority(icaros_readiness: IcarosReadinessResult | None) -> str:
    if icaros_readiness is not None and (
        icaros_readiness.spiritual_orientation == SPIRITUAL_ORIENTATION_UNKNOWN
        or _icaros_warns_about_worldview_or_symbolic_language(icaros_readiness)
    ):
        return "high"
    return "medium"


def _worldview_ambiguity(
    proposal: FingerprintUpdateProposal,
    icaros_readiness: IcarosReadinessResult | None,
) -> bool:
    worldview_signals = {"secular_worldview", "religion_averse", "symbolic_constraint"}
    if any(item.signal in worldview_signals for item in proposal.candidate_signals):
        return True
    if icaros_readiness is not None and icaros_readiness.spiritual_orientation == SPIRITUAL_ORIENTATION_UNKNOWN:
        return True
    return False


def _coverage_targets(
    *,
    questions: tuple[ClarificationQuestion, ...],
    signal_domains: set[str],
    fingerprint_coverage: FingerprintCoverageReport | None,
) -> tuple[str, ...]:
    targets: list[str] = []
    seen: set[str] = set()

    for item in questions:
        if item.target_domain not in seen:
            targets.append(item.target_domain)
            seen.add(item.target_domain)

    for domain in sorted(signal_domains):
        if domain not in seen:
            targets.append(domain)
            seen.add(domain)

    if fingerprint_coverage is not None:
        for short_domain, coverage_domain, _ in CRITICAL_COVERAGE_DOMAINS:
            if short_domain in seen:
                continue
            if _domain_needs_coverage(fingerprint_coverage, coverage_domain):
                targets.append(short_domain)
                seen.add(short_domain)

    ordered = [domain for domain, _, _ in CRITICAL_COVERAGE_DOMAINS if domain in seen]
    ordered.extend(domain for domain in targets if domain not in ordered)
    return tuple(ordered)


def _overall_need(
    *,
    questions: tuple[ClarificationQuestion, ...],
    proposal: FingerprintUpdateProposal,
    fingerprint_coverage: FingerprintCoverageReport | None,
) -> str:
    if not questions:
        if proposal.candidate_signals or proposal.blocked_updates:
            return NEED_HIGH
        if fingerprint_coverage is not None and fingerprint_coverage.missing_domains:
            return NEED_MEDIUM
        return NEED_LOW

    if any(item.priority == "high" for item in questions):
        return NEED_HIGH
    if proposal.candidate_signals or proposal.blocked_updates:
        return NEED_HIGH
    return NEED_MEDIUM
