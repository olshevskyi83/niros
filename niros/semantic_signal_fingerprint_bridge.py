"""Bridge from Semantic Signal Graph to Human Digital Fingerprint update proposals.

Produces structured proposals only — never mutates the fingerprint directly.
Uncertain interpretations become clarification questions, not fingerprint facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from niros.assessment import AssessmentResult
from niros.fingerprint_coverage import FingerprintCoverageReport
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_signal_graph import (
    COMPETING_CONFIDENCE_WINDOW,
    INTERPRETATION_AMBIGUOUS,
    INTERPRETATION_CANDIDATE,
    INTERPRETATION_CONFIRMED,
    FORBIDDEN_GRAPH_PHRASES,
    HEURISTIC_RULES,
    InterpretationCandidate,
    SemanticOpenQuestion,
    SemanticSignalGraph,
    SemanticSignalNode,
)

ACCEPT_CONFIDENCE_THRESHOLD = 0.75
CANDIDATE_CONFIDENCE_MIN = 0.50
BLOCK_CONFIDENCE_THRESHOLD = 0.50

FORBIDDEN_BRIDGE_PHRASES = frozenset(FORBIDDEN_GRAPH_PHRASES)


@dataclass(frozen=True)
class AcceptedSignalProposal:
    signal: str
    domain: str
    confidence: float
    evidence: tuple[str, ...]
    recommended_fingerprint_field: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "domain": self.domain,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "recommended_fingerprint_field": self.recommended_fingerprint_field,
        }


@dataclass(frozen=True)
class CandidateSignalProposal:
    signal: str
    domain: str
    confidence: float
    reason: str
    requires_clarification: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "domain": self.domain,
            "confidence": self.confidence,
            "reason": self.reason,
            "requires_clarification": self.requires_clarification,
        }


@dataclass(frozen=True)
class OpenQuestionProposal:
    question: str
    target_signal: str
    priority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "target_signal": self.target_signal,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class BlockedUpdate:
    signal: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FingerprintUpdateProposal:
    accepted_signals: tuple[AcceptedSignalProposal, ...] = field(default_factory=tuple)
    candidate_signals: tuple[CandidateSignalProposal, ...] = field(default_factory=tuple)
    open_questions: tuple[OpenQuestionProposal, ...] = field(default_factory=tuple)
    blocked_updates: tuple[BlockedUpdate, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted_signals": [item.to_dict() for item in self.accepted_signals],
            "candidate_signals": [item.to_dict() for item in self.candidate_signals],
            "open_questions": [item.to_dict() for item in self.open_questions],
            "blocked_updates": [item.to_dict() for item in self.blocked_updates],
        }


SIGNAL_PROPOSAL_DOMAIN: dict[str, str] = {
    "self_criticism": "self",
    "low_self_worth": "self",
    "shame_sensitivity": "self",
    "self_alienation": "self",
    "agency_reduction": "self",
    "grief_loss": "grief_loss",
    "meaning_disruption": "meaning_purpose",
    "identity_dissonance": "values_identity",
    "values_conflict": "values_identity",
    "emotional_numbness": "emotion_regulation",
    "social_withdrawal": "relationships",
    "secular_worldview": "spirituality_worldview",
    "religion_averse": "spirituality_worldview",
    "symbolic_constraint": "spirituality_worldview",
}

SIGNAL_FINGERPRINT_FIELD: dict[str, str] = {
    "self_criticism": "self_domain.self_criticism",
    "low_self_worth": "self_domain.self_worth",
    "shame_sensitivity": "self_domain.shame",
    "self_alienation": "self_domain.identity",
    "agency_reduction": "self_domain.agency",
    "grief_loss": "grief_loss_bereavement.grief",
    "meaning_disruption": "meaning.meaning_sense",
    "identity_dissonance": "values_identity_domain.authenticity",
    "values_conflict": "values_identity_domain.inner_conflict",
    "emotional_numbness": "emotion_regulation_domain.emotional_suppression",
    "social_withdrawal": "relationships_domain.attachment_avoidance",
    "secular_worldview": "spirituality_worldview.worldview_orientation",
    "religion_averse": "spirituality_worldview.worldview_orientation",
    "symbolic_constraint": "spirituality_worldview.religious_language_comfort",
}


class SemanticSignalFingerprintBridge:
    """Convert a SemanticSignalGraph into safe fingerprint update proposals."""

    def propose(
        self,
        graph: SemanticSignalGraph,
        *,
        semantic_facts: Iterable[SemanticFact] | None = None,
        patterns: Iterable[str] | Iterable[PatternTag] | None = None,
        fingerprint_coverage: FingerprintCoverageReport | None = None,
        assessment_results: Iterable[AssessmentResult] | None = None,
    ) -> FingerprintUpdateProposal:
        del semantic_facts, patterns, fingerprint_coverage, assessment_results

        evidence_by_id = {item.id: item.text for item in graph.evidence}
        clarification_required = _clarification_required_signals(graph.interpretation_candidates)
        competing_groups = _build_competing_groups(graph)

        accepted: list[AcceptedSignalProposal] = []
        candidates: list[CandidateSignalProposal] = []
        blocked: list[BlockedUpdate] = []
        open_questions: list[OpenQuestionProposal] = []

        for node in _ordered_nodes(graph.nodes):
            evidence_texts = _evidence_texts(node, evidence_by_id)
            domain = _proposal_domain(node.signal_type)
            competing_group = competing_groups.get(node.signal_type, frozenset())
            requires_clarification = _requires_clarification(
                node=node,
                nodes=graph.nodes,
                clarification_required=clarification_required,
                competing_group=competing_group,
            )

            if not evidence_texts:
                blocked.append(
                    BlockedUpdate(signal=node.signal_type, reason="No supporting evidence")
                )
                continue

            if requires_clarification:
                reason = _candidate_reason(
                    node=node,
                    graph=graph,
                    evidence_texts=evidence_texts,
                    competing_group=competing_group,
                    clarification_required=clarification_required,
                )
                candidates.append(
                    CandidateSignalProposal(
                        signal=node.signal_type,
                        domain=domain,
                        confidence=node.confidence,
                        reason=reason,
                        requires_clarification=True,
                    )
                )
                blocked.append(
                    BlockedUpdate(
                        signal=node.signal_type,
                        reason=_blocked_reason(node, competing_group),
                    )
                )
                continue

            if node.confidence < BLOCK_CONFIDENCE_THRESHOLD:
                blocked.append(
                    BlockedUpdate(
                        signal=node.signal_type,
                        reason="Confidence below promotion threshold",
                    )
                )
                continue

            if (
                node.interpretation_status == INTERPRETATION_CONFIRMED
                and node.confidence >= ACCEPT_CONFIDENCE_THRESHOLD
                and _is_clear_winner(node, graph.nodes, competing_group)
            ):
                accepted.append(
                    AcceptedSignalProposal(
                        signal=node.signal_type,
                        domain=domain,
                        confidence=node.confidence,
                        evidence=evidence_texts,
                        recommended_fingerprint_field=_fingerprint_field(node.signal_type),
                    )
                )
                continue

            if (
                node.interpretation_status == INTERPRETATION_CONFIRMED
                and CANDIDATE_CONFIDENCE_MIN <= node.confidence < ACCEPT_CONFIDENCE_THRESHOLD
            ):
                candidates.append(
                    CandidateSignalProposal(
                        signal=node.signal_type,
                        domain=domain,
                        confidence=node.confidence,
                        reason=(
                            f"Confirmed signal at medium confidence ({node.confidence:.2f}); "
                            "clarification recommended before fingerprint promotion."
                        ),
                        requires_clarification=True,
                    )
                )
                _append_medium_confidence_question(
                    open_questions,
                    node=node,
                    graph=graph,
                )
                continue

            blocked.append(
                BlockedUpdate(
                    signal=node.signal_type,
                    reason=_blocked_reason(node, competing_group),
                )
            )

        _append_graph_open_questions(open_questions, graph.open_questions)
        open_questions = _dedupe_open_questions(open_questions)

        return FingerprintUpdateProposal(
            accepted_signals=tuple(accepted),
            candidate_signals=tuple(candidates),
            open_questions=tuple(open_questions),
            blocked_updates=tuple(blocked),
        )


def propose_fingerprint_updates(
    graph: SemanticSignalGraph,
    **kwargs: Any,
) -> FingerprintUpdateProposal:
    return SemanticSignalFingerprintBridge().propose(graph, **kwargs)


def render_fingerprint_update_proposal(proposal: FingerprintUpdateProposal) -> str:
    lines = ["===== FINGERPRINT UPDATE PROPOSAL =====", ""]

    lines.append("Accepted signals:")
    if proposal.accepted_signals:
        for item in proposal.accepted_signals:
            evidence = "; ".join(item.evidence)
            lines.append(
                f"- {item.signal} ({item.domain}, confidence={item.confidence:.2f}) "
                f"-> {item.recommended_fingerprint_field} [{evidence}]"
            )
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("Candidate signals:")
    if proposal.candidate_signals:
        for item in proposal.candidate_signals:
            lines.append(
                f"- {item.signal} ({item.domain}, confidence={item.confidence:.2f}): "
                f"{item.reason}"
            )
    else:
        lines.append("- (none)")

    if proposal.open_questions:
        lines.append("")
        lines.append("Open questions:")
        for item in proposal.open_questions:
            lines.append(f"- [{item.priority}] {item.question}")

    if proposal.blocked_updates:
        lines.append("")
        lines.append("Blocked updates:")
        for item in proposal.blocked_updates:
            lines.append(f"- {item.signal}: {item.reason}")

    return "\n".join(lines)


def _ordered_nodes(nodes: tuple[SemanticSignalNode, ...]) -> tuple[SemanticSignalNode, ...]:
    return tuple(sorted(nodes, key=lambda node: (-node.confidence, node.signal_type)))


def _proposal_domain(signal_type: str) -> str:
    return SIGNAL_PROPOSAL_DOMAIN.get(signal_type, signal_type)


def _fingerprint_field(signal_type: str) -> str:
    return SIGNAL_FINGERPRINT_FIELD.get(signal_type, f"unknown.{signal_type}")


def _evidence_texts(
    node: SemanticSignalNode,
    evidence_by_id: dict[str, str],
) -> tuple[str, ...]:
    texts = tuple(
        evidence_by_id[item_id]
        for item_id in node.evidence_ids
        if item_id in evidence_by_id and evidence_by_id[item_id].strip()
    )
    return texts


def _clarification_required_signals(
    interpretation_candidates: tuple[InterpretationCandidate, ...],
) -> frozenset[str]:
    return frozenset(
        candidate.proposed_signal
        for candidate in interpretation_candidates
        if candidate.clarification_required
    )


def _build_competing_groups(graph: SemanticSignalGraph) -> dict[str, frozenset[str]]:
    groups: dict[str, frozenset[str]] = {}

    for candidate in graph.interpretation_candidates:
        if not candidate.competing_interpretations:
            continue
        group = frozenset({candidate.proposed_signal, *candidate.competing_interpretations})
        for signal in group:
            groups[signal] = frozenset(groups.get(signal, frozenset()) | group)

    ambiguous = [
        node.signal_type
        for node in graph.nodes
        if node.interpretation_status == INTERPRETATION_AMBIGUOUS
    ]
    if len(ambiguous) >= 2:
        amb_set = frozenset(ambiguous)
        for signal in ambiguous:
            groups[signal] = frozenset(groups.get(signal, frozenset()) | amb_set)

    return groups


def _requires_clarification(
    *,
    node: SemanticSignalNode,
    nodes: tuple[SemanticSignalNode, ...],
    clarification_required: frozenset[str],
    competing_group: frozenset[str],
) -> bool:
    if node.signal_type in clarification_required:
        return True
    if node.needs_clarification:
        return True
    if node.interpretation_status in {INTERPRETATION_CANDIDATE, INTERPRETATION_AMBIGUOUS}:
        return True
    if len(competing_group) >= 2:
        if node.confidence < ACCEPT_CONFIDENCE_THRESHOLD:
            return True
        if not _is_clear_winner(node, nodes, competing_group):
            return True
    return False


def _is_clear_winner(
    node: SemanticSignalNode,
    nodes: tuple[SemanticSignalNode, ...] | Iterable[SemanticSignalNode],
    competing_group: frozenset[str],
) -> bool:
    if len(competing_group) < 2:
        return True

    peers = [item for item in nodes if item.signal_type in competing_group]
    if not peers:
        return True

    ordered = sorted(peers, key=lambda item: (-item.confidence, item.signal_type))
    if ordered[0].signal_type != node.signal_type:
        return False
    if len(ordered) == 1:
        return True
    return ordered[0].confidence - ordered[1].confidence >= COMPETING_CONFIDENCE_WINDOW


def _source_phrase_from_evidence(
    graph: SemanticSignalGraph,
    evidence_texts: tuple[str, ...],
) -> str | None:
    corpus = " ".join(evidence_texts).lower() if evidence_texts else graph.original_text.lower()

    matched: list[str] = []
    for rule in HEURISTIC_RULES:
        for phrase in rule.phrases:
            if phrase in corpus:
                matched.append(phrase)

    if matched:
        return max(matched, key=len)

    if evidence_texts:
        text = evidence_texts[0].strip()
        if text:
            return text

    stripped = graph.original_text.strip()
    return stripped or None


def _candidate_reason(
    *,
    node: SemanticSignalNode,
    graph: SemanticSignalGraph,
    evidence_texts: tuple[str, ...],
    competing_group: frozenset[str],
    clarification_required: frozenset[str],
) -> str:
    source_phrase = _source_phrase_from_evidence(graph, evidence_texts)
    is_ambiguous_competing = (
        node.signal_type in clarification_required
        or (
            node.interpretation_status == INTERPRETATION_AMBIGUOUS
            and len(competing_group) >= 2
        )
    )

    if is_ambiguous_competing:
        if source_phrase:
            return f"Ambiguous expression requires clarification: {source_phrase}"
        return (
            f"Ambiguous expression: competing interpretations remain unresolved "
            f"({', '.join(sorted(competing_group))})."
        )

    if node.needs_clarification and source_phrase:
        return f"Ambiguous expression requires clarification: {source_phrase}"

    if node.needs_clarification:
        return f"Signal needs clarification before fingerprint promotion ({node.label})."

    return f"Clarification required before promotion ({node.label})."


def _blocked_reason(node: SemanticSignalNode, competing_group: frozenset[str]) -> str:
    if node.confidence < BLOCK_CONFIDENCE_THRESHOLD:
        return "Confidence below promotion threshold"
    if len(competing_group) >= 2:
        return "Competing interpretations require clarification"
    if node.needs_clarification:
        return "Clarification required before promotion"
    return "Not eligible for fingerprint promotion"


def _append_medium_confidence_question(
    open_questions: list[OpenQuestionProposal],
    *,
    node: SemanticSignalNode,
    graph: SemanticSignalGraph,
) -> None:
    open_questions.append(
        OpenQuestionProposal(
            question=(
                f"Can you say more about what you mean regarding {node.label}? "
                f'You said: "{graph.original_text}"'
            ),
            target_signal=node.signal_type,
            priority="medium",
        )
    )


def _append_graph_open_questions(
    open_questions: list[OpenQuestionProposal],
    graph_questions: tuple[SemanticOpenQuestion, ...],
) -> None:
    for item in graph_questions:
        open_questions.append(
            OpenQuestionProposal(
                question=item.question,
                target_signal=item.target_signal,
                priority=item.priority,
            )
        )


def _dedupe_open_questions(
    open_questions: list[OpenQuestionProposal],
) -> list[OpenQuestionProposal]:
    seen: set[tuple[str, str]] = set()
    deduped: list[OpenQuestionProposal] = []
    for item in open_questions:
        key = (item.target_signal, item.question)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
