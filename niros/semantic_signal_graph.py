"""Semantic Signal Graph — structured Human Language Understanding layer.

Represents rich, ambiguous meaning signals without replacing flat semantic facts.
Deterministic heuristics only; no LLM calls in this slice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from niros.patterns import PatternTag
from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.facts import SemanticFact

CLARIFICATION_THRESHOLD = 0.55
COMPETING_CONFIDENCE_WINDOW = 0.12

INTERPRETATION_CONFIRMED = "confirmed"
INTERPRETATION_CANDIDATE = "candidate"
INTERPRETATION_AMBIGUOUS = "ambiguous"

EDGE_RELATIONS = frozenset(
    {
        "suggests",
        "reinforces",
        "conflicts_with",
        "may_underlie",
        "may_lead_to",
        "needs_clarification_for",
    }
)

FORBIDDEN_GRAPH_PHRASES = frozenset(
    {
        "diagnosis",
        "diagnose",
        "disorder",
        "patholog",
        "clinical disorder",
        "mental illness",
        "psychiatric",
    }
)


@dataclass(frozen=True)
class SemanticEvidence:
    id: str
    text: str
    source_span: str
    language: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "source_span": self.source_span,
            "language": self.language,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class SemanticSignalNode:
    id: str
    signal_type: str
    label: str
    domain: str
    confidence: float
    evidence_ids: tuple[str, ...]
    needs_clarification: bool
    interpretation_status: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "signal_type": self.signal_type,
            "label": self.label,
            "domain": self.domain,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "needs_clarification": self.needs_clarification,
            "interpretation_status": self.interpretation_status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SemanticSignalEdge:
    source: str
    target: str
    relation: str
    confidence: float
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class SemanticOpenQuestion:
    id: str
    question: str
    target_signal: str
    reason: str
    priority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "target_signal": self.target_signal,
            "reason": self.reason,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class InterpretationCandidate:
    id: str
    proposed_signal: str
    confidence: float
    supporting_evidence: tuple[str, ...]
    competing_interpretations: tuple[str, ...]
    clarification_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "proposed_signal": self.proposed_signal,
            "confidence": self.confidence,
            "supporting_evidence": list(self.supporting_evidence),
            "competing_interpretations": list(self.competing_interpretations),
            "clarification_required": self.clarification_required,
        }


@dataclass(frozen=True)
class SemanticSignalGraph:
    language: str
    original_text: str
    nodes: tuple[SemanticSignalNode, ...]
    edges: tuple[SemanticSignalEdge, ...]
    evidence: tuple[SemanticEvidence, ...]
    open_questions: tuple[SemanticOpenQuestion, ...]
    interpretation_candidates: tuple[InterpretationCandidate, ...] = field(default_factory=tuple)
    overall_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "original_text": self.original_text,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "evidence": [item.to_dict() for item in self.evidence],
            "open_questions": [item.to_dict() for item in self.open_questions],
            "interpretation_candidates": [
                candidate.to_dict() for candidate in self.interpretation_candidates
            ],
            "overall_confidence": self.overall_confidence,
        }

    def confirmed_nodes(self) -> tuple[SemanticSignalNode, ...]:
        return tuple(
            node for node in self.nodes if node.interpretation_status == INTERPRETATION_CONFIRMED
        )

    def candidate_nodes(self) -> tuple[SemanticSignalNode, ...]:
        return tuple(
            node
            for node in self.nodes
            if node.interpretation_status in {INTERPRETATION_CANDIDATE, INTERPRETATION_AMBIGUOUS}
        )


@dataclass(frozen=True)
class _HeuristicSignalSpec:
    signal_type: str
    label: str
    domain: str
    confidence: float


@dataclass(frozen=True)
class _HeuristicEdgeSpec:
    source: str
    target: str
    relation: str
    confidence: float


@dataclass(frozen=True)
class _HeuristicOpenQuestionSpec:
    question: str
    target_signal: str
    reason: str
    priority: str = "medium"


@dataclass(frozen=True)
class _HeuristicRule:
    phrases: tuple[str, ...]
    signals: tuple[_HeuristicSignalSpec, ...]
    edges: tuple[_HeuristicEdgeSpec, ...] = ()
    open_questions: tuple[_HeuristicOpenQuestionSpec, ...] = ()


HEURISTIC_RULES: tuple[_HeuristicRule, ...] = (
    _HeuristicRule(
        phrases=(
            "living someone else's life",
            "living someone elses life",
            "living someone else's life.",
        ),
        signals=(
            _HeuristicSignalSpec("identity_dissonance", "identity dissonance", "identity", 0.46),
            _HeuristicSignalSpec("values_conflict", "values conflict", "values", 0.44),
            _HeuristicSignalSpec("self_alienation", "self alienation", "self", 0.42),
            _HeuristicSignalSpec("agency_reduction", "agency reduction", "agency", 0.39),
            _HeuristicSignalSpec("meaning_disruption", "meaning disruption", "meaning", 0.41),
        ),
        edges=(
            _HeuristicEdgeSpec("identity_dissonance", "meaning_disruption", "may_underlie", 0.70),
            _HeuristicEdgeSpec("values_conflict", "identity_dissonance", "reinforces", 0.68),
            _HeuristicEdgeSpec("agency_reduction", "self_alienation", "may_lead_to", 0.65),
        ),
        open_questions=(
            _HeuristicOpenQuestionSpec(
                question=(
                    "When you say you are living someone else's life, do you mean your work, "
                    "your relationships, your values, or something else?"
                ),
                target_signal="identity_dissonance",
                reason="Multiple plausible identity and values interpretations remain unresolved.",
                priority="high",
            ),
        ),
    ),
    _HeuristicRule(
        phrases=(
            "constantly criticize myself even when i do well",
            "constantly criticise myself even when i do well",
            "criticize myself even when i do well",
        ),
        signals=(
            _HeuristicSignalSpec("self_criticism", "self criticism", "self", 0.72),
            _HeuristicSignalSpec("low_self_worth", "low self-worth", "self", 0.66),
            _HeuristicSignalSpec("shame_sensitivity", "shame sensitivity", "emotion", 0.58),
        ),
        edges=(
            _HeuristicEdgeSpec("self_criticism", "low_self_worth", "reinforces", 0.74),
            _HeuristicEdgeSpec("shame_sensitivity", "self_criticism", "may_underlie", 0.62),
        ),
        open_questions=(
            _HeuristicOpenQuestionSpec(
                question="What does the critical voice usually say about you?",
                target_signal="self_criticism",
                reason="Self-critical language may reflect several self-related patterns.",
                priority="medium",
            ),
        ),
    ),
    _HeuristicRule(
        phrases=(
            "lost someone and since then everything feels empty",
            "since then everything feels empty",
            "everything feels empty",
        ),
        signals=(
            _HeuristicSignalSpec("grief_loss", "grief / loss", "grief", 0.78),
            _HeuristicSignalSpec("meaning_disruption", "meaning disruption", "meaning", 0.64),
            _HeuristicSignalSpec("emotional_numbness", "emotional numbness", "emotion", 0.58),
            _HeuristicSignalSpec("social_withdrawal", "social withdrawal", "relationships", 0.45),
        ),
        edges=(
            _HeuristicEdgeSpec("grief_loss", "meaning_disruption", "may_underlie", 0.76),
            _HeuristicEdgeSpec("grief_loss", "emotional_numbness", "may_lead_to", 0.70),
        ),
        open_questions=(
            _HeuristicOpenQuestionSpec(
                question="What feels most empty since the loss?",
                target_signal="grief_loss",
                reason="Loss-related emptiness can reflect grief, meaning, or withdrawal signals.",
                priority="high",
            ),
        ),
    ),
    _HeuristicRule(
        phrases=(
            "do not believe in god and religious language makes me uncomfortable",
            "don't believe in god and religious language makes me uncomfortable",
            "religious language makes me uncomfortable",
        ),
        signals=(
            _HeuristicSignalSpec("secular_worldview", "secular worldview", "worldview", 0.86),
            _HeuristicSignalSpec("religion_averse", "religion averse", "worldview", 0.88),
            _HeuristicSignalSpec("symbolic_constraint", "symbolic constraint", "language", 0.82),
        ),
        edges=(
            _HeuristicEdgeSpec("religion_averse", "symbolic_constraint", "reinforces", 0.84),
        ),
        open_questions=(),
    ),
)

FACT_SIGNAL_HINTS: dict[tuple[str, str], _HeuristicSignalSpec] = {
    ("meaning", "worldview_orientation"): _HeuristicSignalSpec(
        "secular_worldview", "secular worldview", "worldview", 0.80
    ),
    ("session", "religious_language_comfort"): _HeuristicSignalSpec(
        "symbolic_constraint", "symbolic constraint", "language", 0.75
    ),
    ("self", "unworthiness"): _HeuristicSignalSpec(
        "low_self_worth", "low self-worth", "self", 0.60
    ),
}

PATTERN_SIGNAL_HINTS: dict[str, _HeuristicSignalSpec] = {
    "identity_confusion": _HeuristicSignalSpec(
        "identity_dissonance", "identity dissonance", "identity", 0.52
    ),
    "identity_uncertainty": _HeuristicSignalSpec(
        "identity_dissonance", "identity dissonance", "identity", 0.50
    ),
    "harsh_self_criticism": _HeuristicSignalSpec(
        "self_criticism", "self criticism", "self", 0.68
    ),
    "shame_sensitivity": _HeuristicSignalSpec(
        "shame_sensitivity", "shame sensitivity", "emotion", 0.62
    ),
    "grief_signal": _HeuristicSignalSpec("grief_loss", "grief / loss", "grief", 0.70),
    "spiritual_resistance": _HeuristicSignalSpec(
        "religion_averse", "religion averse", "worldview", 0.72
    ),
}


class SemanticSignalGraphBuilder:
    """Deterministic heuristic builder for Semantic Signal Graphs."""

    def build(
        self,
        *,
        text: str,
        language: str = "en",
        semantic_facts: Iterable[SemanticFact] | None = None,
        patterns: Iterable[str] | Iterable[PatternTag] | None = None,
    ) -> SemanticSignalGraph:
        normalized_text = " ".join(text.strip().split())
        lowered = normalized_text.lower()

        evidence = (
            SemanticEvidence(
                id="ev_001",
                text=normalized_text,
                source_span=normalized_text,
                language=language,
                confidence=1.0,
            ),
        )
        evidence_ids = (evidence[0].id,)

        matched_rule = _match_rule(lowered)
        signal_specs: dict[str, _HeuristicSignalSpec] = {}
        edge_specs: list[_HeuristicEdgeSpec] = []
        question_specs: list[_HeuristicOpenQuestionSpec] = []

        if matched_rule is not None:
            for spec in matched_rule.signals:
                signal_specs[spec.signal_type] = spec
            edge_specs.extend(matched_rule.edges)
            question_specs.extend(matched_rule.open_questions)

        for fact in semantic_facts or ():
            if not fact.is_valid():
                continue
            hint = FACT_SIGNAL_HINTS.get((fact.category, fact.attribute))
            if hint is None:
                continue
            signal_specs[hint.signal_type] = _merge_signal_spec(signal_specs.get(hint.signal_type), hint)

        for pattern_id in _normalize_pattern_ids(patterns):
            hint = PATTERN_SIGNAL_HINTS.get(pattern_id)
            if hint is None:
                continue
            signal_specs[hint.signal_type] = _merge_signal_spec(signal_specs.get(hint.signal_type), hint)

        nodes, candidates, open_questions = _finalize_signals(
            signal_specs=signal_specs,
            evidence_ids=evidence_ids,
            question_specs=question_specs,
        )

        edges = tuple(
            SemanticSignalEdge(
                source=edge.source,
                target=edge.target,
                relation=edge.relation,
                confidence=edge.confidence,
                evidence_ids=evidence_ids,
            )
            for edge in edge_specs
            if edge.source in {node.signal_type for node in nodes}
            and edge.target in {node.signal_type for node in nodes}
        )

        overall_confidence = 0.0
        if nodes:
            overall_confidence = round(
                sum(node.confidence for node in nodes if node.interpretation_status == INTERPRETATION_CONFIRMED)
                / max(1, len([node for node in nodes if node.interpretation_status == INTERPRETATION_CONFIRMED])),
                4,
            )

        return SemanticSignalGraph(
            language=language,
            original_text=normalized_text,
            nodes=nodes,
            edges=edges,
            evidence=evidence,
            open_questions=open_questions,
            interpretation_candidates=candidates,
            overall_confidence=overall_confidence,
        )

    def build_from_interpretation_result(
        self,
        result: SemanticInterpretationResult,
        *,
        language: str | None = None,
        patterns: Iterable[str] | Iterable[PatternTag] | None = None,
    ) -> SemanticSignalGraph:
        return self.build(
            text=result.raw_text,
            language=language or result.detected_language or "en",
            semantic_facts=result.facts,
            patterns=patterns,
        )


def build_semantic_signal_graph(
    *,
    text: str,
    language: str = "en",
    semantic_facts: Iterable[SemanticFact] | None = None,
    patterns: Iterable[str] | Iterable[PatternTag] | None = None,
) -> SemanticSignalGraph:
    return SemanticSignalGraphBuilder().build(
        text=text,
        language=language,
        semantic_facts=semantic_facts,
        patterns=patterns,
    )


def render_semantic_signal_graph(graph: SemanticSignalGraph) -> str:
    lines = [
        "===== SEMANTIC SIGNAL GRAPH =====",
        f"Language: {graph.language}",
        f"Overall confidence (confirmed signals): {graph.overall_confidence:.2f}",
        "",
        "Evidence:",
    ]
    for item in graph.evidence:
        lines.append(f"- {item.id}: {item.text}")

    lines.append("")
    lines.append("Signals:")
    if graph.nodes:
        for node in graph.nodes:
            status = node.interpretation_status
            clarify = "needs clarification" if node.needs_clarification else "ready"
            lines.append(
                f"- {node.signal_type} ({node.domain}, {status}, {clarify}, "
                f"confidence={node.confidence:.2f})"
            )
    else:
        lines.append("- (none)")

    if graph.edges:
        lines.append("")
        lines.append("Relations:")
        for edge in graph.edges:
            lines.append(
                f"- {edge.source} {edge.relation} {edge.target} (confidence={edge.confidence:.2f})"
            )

    if graph.interpretation_candidates:
        lines.append("")
        lines.append("Interpretation candidates:")
        for candidate in graph.interpretation_candidates:
            competing = ", ".join(candidate.competing_interpretations) or "none"
            lines.append(
                f"- {candidate.proposed_signal} (confidence={candidate.confidence:.2f}, "
                f"competing: {competing})"
            )

    if graph.open_questions:
        lines.append("")
        lines.append("Open questions:")
        for question in graph.open_questions:
            lines.append(f"- [{question.priority}] {question.question}")

    return "\n".join(lines)


def _match_rule(lowered_text: str) -> _HeuristicRule | None:
    for rule in HEURISTIC_RULES:
        if any(phrase in lowered_text for phrase in rule.phrases):
            return rule
    return None


def _merge_signal_spec(
    existing: _HeuristicSignalSpec | None,
    incoming: _HeuristicSignalSpec,
) -> _HeuristicSignalSpec:
    if existing is None:
        return incoming
    return _HeuristicSignalSpec(
        signal_type=incoming.signal_type,
        label=existing.label,
        domain=existing.domain,
        confidence=max(existing.confidence, incoming.confidence),
    )


def _normalize_pattern_ids(
    patterns: Iterable[str] | Iterable[PatternTag] | None,
) -> set[str]:
    if not patterns:
        return set()
    pattern_ids: set[str] = set()
    for item in patterns:
        if isinstance(item, PatternTag):
            pattern_ids.add(item.canonical_id)
        else:
            pattern_ids.add(str(item))
    return pattern_ids


def _finalize_signals(
    *,
    signal_specs: dict[str, _HeuristicSignalSpec],
    evidence_ids: tuple[str, ...],
    question_specs: list[_HeuristicOpenQuestionSpec],
) -> tuple[
    tuple[SemanticSignalNode, ...],
    tuple[InterpretationCandidate, ...],
    tuple[SemanticOpenQuestion, ...],
]:
    if not signal_specs:
        return (), (), ()

    ordered_specs = sorted(signal_specs.values(), key=lambda spec: (-spec.confidence, spec.signal_type))
    confidences = [spec.confidence for spec in ordered_specs]
    max_confidence = confidences[0]
    competing_types = [
        spec.signal_type
        for spec in ordered_specs
        if max_confidence - spec.confidence <= COMPETING_CONFIDENCE_WINDOW
    ]
    ambiguous_group = (
        len(competing_types) >= 2
        and max_confidence < CLARIFICATION_THRESHOLD
    )

    nodes: list[SemanticSignalNode] = []
    candidates: list[InterpretationCandidate] = []

    for spec in ordered_specs:
        if ambiguous_group and spec.signal_type in competing_types:
            status = INTERPRETATION_AMBIGUOUS
            needs_clarification = True
        elif spec.confidence >= CLARIFICATION_THRESHOLD and not ambiguous_group:
            status = INTERPRETATION_CONFIRMED
            needs_clarification = False
        elif spec.confidence >= CLARIFICATION_THRESHOLD:
            status = INTERPRETATION_CONFIRMED
            needs_clarification = False
        else:
            status = INTERPRETATION_CANDIDATE
            needs_clarification = True

        nodes.append(
            SemanticSignalNode(
                id=spec.signal_type,
                signal_type=spec.signal_type,
                label=spec.label,
                domain=spec.domain,
                confidence=spec.confidence,
                evidence_ids=evidence_ids,
                needs_clarification=needs_clarification,
                interpretation_status=status,
                metadata=(("source", "heuristic"),),
            )
        )

        if status in {INTERPRETATION_CANDIDATE, INTERPRETATION_AMBIGUOUS}:
            competing = tuple(
                other
                for other in competing_types
                if other != spec.signal_type
            )
            candidates.append(
                InterpretationCandidate(
                    id=f"candidate_{spec.signal_type}",
                    proposed_signal=spec.signal_type,
                    confidence=spec.confidence,
                    supporting_evidence=evidence_ids,
                    competing_interpretations=competing,
                    clarification_required=True,
                )
            )

    open_questions: list[SemanticOpenQuestion] = []
    if ambiguous_group or any(node.needs_clarification for node in nodes):
        for index, spec in enumerate(question_specs, start=1):
            open_questions.append(
                SemanticOpenQuestion(
                    id=f"oq_{index:02d}",
                    question=spec.question,
                    target_signal=spec.target_signal,
                    reason=spec.reason,
                    priority=spec.priority,
                )
            )

    return tuple(nodes), tuple(candidates), tuple(open_questions)
