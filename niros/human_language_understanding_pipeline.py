"""Human Language Understanding Pipeline — lightweight orchestrator for HLU modules.

Connects Semantic Signal Graph, fingerprint bridge, clarification engine, and interview adapter.
Does not mutate Human Digital Fingerprint or replace existing semantic extraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from niros.assessment import AssessmentResult
from niros.clarification_engine_v2 import (
    NEED_LOW,
    ClarificationEngineV2,
    ClarificationPlan,
    ClarificationQuestion,
)
from niros.clarification_interview_adapter import (
    ClarificationInterviewAdapter,
    ClarificationInterviewContext,
    ClarificationInterviewQuestion,
)
from niros.fingerprint_coverage import FingerprintCoverageReport
from niros.icaros_readiness import IcarosReadinessResult
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_signal_fingerprint_bridge import (
    AcceptedSignalProposal,
    BlockedUpdate,
    CandidateSignalProposal,
    FingerprintUpdateProposal,
    SemanticSignalFingerprintBridge,
)
from niros.semantic_signal_graph import SemanticSignalGraph, build_semantic_signal_graph

FORBIDDEN_PIPELINE_PHRASES = frozenset(
    {
        "diagnosis",
        "diagnose",
        "disorder",
        "patholog",
        "clinical disorder",
        "mental illness",
        "psychiatric",
        "symptom severity",
    }
)


@dataclass(frozen=True)
class HumanLanguageUnderstandingResult:
    semantic_signal_graph: SemanticSignalGraph
    fingerprint_update_proposal: FingerprintUpdateProposal
    clarification_plan: ClarificationPlan
    interview_questions: tuple[ClarificationInterviewQuestion, ...] = field(default_factory=tuple)
    accepted_signals: tuple[AcceptedSignalProposal, ...] = field(default_factory=tuple)
    candidate_signals: tuple[CandidateSignalProposal, ...] = field(default_factory=tuple)
    blocked_updates: tuple[BlockedUpdate, ...] = field(default_factory=tuple)
    open_questions: tuple[ClarificationQuestion, ...] = field(default_factory=tuple)
    overall_confidence: float = 0.0
    needs_clarification: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_signal_graph": self.semantic_signal_graph.to_dict(),
            "fingerprint_update_proposal": self.fingerprint_update_proposal.to_dict(),
            "clarification_plan": self.clarification_plan.to_dict(),
            "interview_questions": [item.to_dict() for item in self.interview_questions],
            "accepted_signals": [item.to_dict() for item in self.accepted_signals],
            "candidate_signals": [item.to_dict() for item in self.candidate_signals],
            "blocked_updates": [item.to_dict() for item in self.blocked_updates],
            "open_questions": [item.to_dict() for item in self.open_questions],
            "overall_confidence": self.overall_confidence,
            "needs_clarification": self.needs_clarification,
        }


class HumanLanguageUnderstandingPipeline:
    """Deterministic convenience layer connecting existing HLU modules."""

    def run(
        self,
        *,
        text: str,
        language: str = "en",
        semantic_facts: Iterable[SemanticFact] | None = None,
        patterns: Iterable[str] | Iterable[PatternTag] | None = None,
        fingerprint_coverage: FingerprintCoverageReport | None = None,
        completed_assessments: Iterable[AssessmentResult] | None = None,
        icaros_readiness: IcarosReadinessResult | None = None,
        max_clarification_questions: int = 3,
    ) -> HumanLanguageUnderstandingResult:
        graph = build_semantic_signal_graph(
            text=text,
            language=language,
            semantic_facts=semantic_facts,
            patterns=patterns,
        )
        proposal = SemanticSignalFingerprintBridge().propose(
            graph,
            semantic_facts=semantic_facts,
            patterns=patterns,
        )
        clarification_plan = ClarificationEngineV2().plan(
            graph,
            proposal,
            fingerprint_coverage=fingerprint_coverage,
            completed_assessments=completed_assessments,
            icaros_readiness=icaros_readiness,
            max_questions=max_clarification_questions,
        )
        interview_questions = ClarificationInterviewAdapter(
            max_clarification_questions=max_clarification_questions,
        ).adapt(
            clarification_plan,
            ClarificationInterviewContext(),
        )

        needs_clarification = _needs_clarification(
            graph=graph,
            proposal=proposal,
            clarification_plan=clarification_plan,
        )

        return HumanLanguageUnderstandingResult(
            semantic_signal_graph=graph,
            fingerprint_update_proposal=proposal,
            clarification_plan=clarification_plan,
            interview_questions=interview_questions,
            accepted_signals=proposal.accepted_signals,
            candidate_signals=proposal.candidate_signals,
            blocked_updates=proposal.blocked_updates,
            open_questions=clarification_plan.questions,
            overall_confidence=graph.overall_confidence,
            needs_clarification=needs_clarification,
        )


def run_human_language_understanding(
    text: str,
    **kwargs: Any,
) -> HumanLanguageUnderstandingResult:
    return HumanLanguageUnderstandingPipeline().run(text=text, **kwargs)


def _needs_clarification(
    *,
    graph: SemanticSignalGraph,
    proposal: FingerprintUpdateProposal,
    clarification_plan: ClarificationPlan,
) -> bool:
    if clarification_plan.overall_need_for_clarification != NEED_LOW:
        return True
    if clarification_plan.questions:
        return True
    if proposal.candidate_signals or proposal.blocked_updates or proposal.open_questions:
        return True
    if graph.interpretation_candidates or graph.candidate_nodes():
        return True
    return any(node.needs_clarification for node in graph.nodes)
