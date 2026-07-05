"""Tests for Clarification Engine v2."""

from __future__ import annotations

import re

from niros.clarification_engine_v2 import (
    FORBIDDEN_CLARIFICATION_PHRASES,
    NEED_HIGH,
    NEED_LOW,
    ClarificationEngineV2,
    build_clarification_plan,
    render_clarification_plan,
)
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_UNKNOWN,
    DomainCoverage,
    FingerprintCoverageReport,
)
from niros.icaros_readiness import IcarosReadinessResult, SPIRITUAL_ORIENTATION_UNKNOWN
from niros.semantic_signal_fingerprint_bridge import (
    OpenQuestionProposal,
    SemanticSignalFingerprintBridge,
    FingerprintUpdateProposal,
)
from niros.semantic_signal_graph import (
    SemanticEvidence,
    SemanticOpenQuestion,
    SemanticSignalGraph,
    build_semantic_signal_graph,
)

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(?:is|e|ed|ing)|disorder|patholog(?:y|ical)|clinical disorder)\b",
    re.IGNORECASE,
)


def _engine() -> ClarificationEngineV2:
    return ClarificationEngineV2()


def _bridge() -> SemanticSignalFingerprintBridge:
    return SemanticSignalFingerprintBridge()


def _coverage_report(domains: dict[str, str]) -> FingerprintCoverageReport:
    return FingerprintCoverageReport(
        domains={
            domain_id: DomainCoverage(
                domain_id=domain_id,
                coverage=1.0 if level == COVERAGE_LEVEL_COMPLETE else 0.2,
                confidence=0.5,
                level=level,
            )
            for domain_id, level in domains.items()
        }
    )


def _identity_case():
    text = "I feel like I am living someone else's life."
    graph = build_semantic_signal_graph(text=text)
    proposal = _bridge().propose(graph)
    return graph, proposal


def test_ambiguous_candidate_signal_creates_high_priority_clarification():
    graph, proposal = _identity_case()
    plan = _engine().plan(graph, proposal, max_questions=3)

    assert plan.questions
    assert plan.questions[0].priority == "high"
    assert plan.questions[0].target_signal == "identity_dissonance"
    assert plan.overall_need_for_clarification == NEED_HIGH
    assert "values_identity" in plan.coverage_targets


def test_proposal_open_questions_are_prioritized():
    graph = SemanticSignalGraph(
        language="en",
        original_text="Ambiguous text.",
        nodes=(),
        edges=(),
        evidence=(),
        open_questions=(
            SemanticOpenQuestion(
                id="oq_graph",
                question="Graph-only fallback question about values?",
                target_signal="values_conflict",
                reason="Graph reason",
                priority="medium",
            ),
        ),
    )
    proposal = FingerprintUpdateProposal(
        open_questions=(
            OpenQuestionProposal(
                question="Proposal-first question about identity?",
                target_signal="identity_dissonance",
                priority="high",
            ),
        ),
        candidate_signals=(),
        blocked_updates=(),
    )

    plan = _engine().plan(graph, proposal, max_questions=1)

    assert len(plan.questions) == 1
    assert plan.questions[0].question.startswith("Proposal-first")


def test_max_questions_is_respected():
    graph, proposal = _identity_case()
    coverage = _coverage_report(
        {
            "self_domain": COVERAGE_LEVEL_UNKNOWN,
            "emotion_regulation_domain": COVERAGE_LEVEL_UNKNOWN,
            "values_identity_domain": COVERAGE_LEVEL_UNKNOWN,
            "meaning": COVERAGE_LEVEL_UNKNOWN,
            "spirituality_worldview": COVERAGE_LEVEL_UNKNOWN,
        }
    )
    plan = _engine().plan(graph, proposal, fingerprint_coverage=coverage, max_questions=2)

    assert len(plan.questions) == 2
    assert plan.skipped_questions


def test_duplicate_questions_are_removed():
    question = (
        "When you say you are living someone else's life, do you mean your work, "
        "your relationships, your values, or something else?"
    )
    graph = SemanticSignalGraph(
        language="en",
        original_text="I feel like I am living someone else's life.",
        nodes=(),
        edges=(),
        evidence=(),
        open_questions=(
            SemanticOpenQuestion(
                id="oq_graph",
                question=question,
                target_signal="identity_dissonance",
                reason="Graph",
                priority="high",
            ),
        ),
    )
    proposal = FingerprintUpdateProposal(
        open_questions=(
            OpenQuestionProposal(
                question=question,
                target_signal="identity_dissonance",
                priority="high",
            ),
        )
    )

    plan = _engine().plan(graph, proposal, max_questions=3)

    assert len(plan.questions) == 1
    assert any(item.reason == "Duplicate question" for item in plan.skipped_questions)


def test_complete_domains_are_skipped_for_fallback_questions():
    graph = build_semantic_signal_graph(text="Hello there.")
    proposal = _bridge().propose(graph)
    coverage = _coverage_report(
        {
            "self_domain": COVERAGE_LEVEL_COMPLETE,
            "emotion_regulation_domain": COVERAGE_LEVEL_COMPLETE,
            "values_identity_domain": COVERAGE_LEVEL_UNKNOWN,
            "meaning": COVERAGE_LEVEL_COMPLETE,
            "spirituality_worldview": COVERAGE_LEVEL_COMPLETE,
        }
    )

    plan = _engine().plan(graph, proposal, fingerprint_coverage=coverage, max_questions=5)

    assert all("difficult or strained" not in item.question for item in plan.questions)
    assert any(
        item.reason == "Domain coverage already complete"
        for item in plan.skipped_questions
    )


def test_low_coverage_critical_domains_can_generate_fallback_questions():
    graph = build_semantic_signal_graph(text="Hello there.")
    proposal = _bridge().propose(graph)
    coverage = _coverage_report(
        {
            "self_domain": COVERAGE_LEVEL_COMPLETE,
            "emotion_regulation_domain": COVERAGE_LEVEL_COMPLETE,
            "values_identity_domain": COVERAGE_LEVEL_UNKNOWN,
            "meaning": COVERAGE_LEVEL_COMPLETE,
            "spirituality_worldview": COVERAGE_LEVEL_COMPLETE,
        }
    )

    plan = _engine().plan(graph, proposal, fingerprint_coverage=coverage, max_questions=3)

    assert any("matters most to you" in item.question for item in plan.questions)
    assert "values_identity" in plan.coverage_targets


def test_spirituality_worldview_unknown_generates_gentle_symbolic_language_question():
    graph = build_semantic_signal_graph(text="Hello there.")
    proposal = _bridge().propose(graph)
    icaros = IcarosReadinessResult(
        ready=False,
        overall_readiness=40,
        confidence="low",
        readiness_level="Not Ready",
        spiritual_orientation=SPIRITUAL_ORIENTATION_UNKNOWN,
        warnings=(
            "Spiritual / worldview orientation is unknown; "
            "symbolic language should remain conservative.",
        ),
    )

    plan = _engine().plan(
        graph,
        proposal,
        fingerprint_coverage=_coverage_report(
            {"spirituality_worldview": COVERAGE_LEVEL_UNKNOWN}
        ),
        icaros_readiness=icaros,
        max_questions=3,
    )

    assert any(
        "spiritual, religious, or symbolic words" in item.question
        for item in plan.questions
    )
    assert "spirituality_worldview" in plan.coverage_targets


def test_no_diagnostic_language():
    graph, proposal = _identity_case()
    coverage = _coverage_report(
        {
            "self_domain": COVERAGE_LEVEL_UNKNOWN,
            "values_identity_domain": COVERAGE_LEVEL_UNKNOWN,
        }
    )
    plan = build_clarification_plan(
        graph,
        proposal,
        fingerprint_coverage=coverage,
        max_questions=3,
    )
    combined = render_clarification_plan(plan).lower()

    assert DIAGNOSIS_PATTERN.search(combined) is None
    for phrase in FORBIDDEN_CLARIFICATION_PHRASES:
        assert phrase not in combined


def test_output_is_deterministic():
    graph, proposal = _identity_case()
    first = _engine().plan(graph, proposal, max_questions=3)
    second = _engine().plan(graph, proposal, max_questions=3)

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_empty_plan_when_no_clarification_needed():
    graph = build_semantic_signal_graph(
        text="I do not believe in God and religious language makes me uncomfortable.",
    )
    proposal = _bridge().propose(graph)
    coverage = _coverage_report(
        {
            "self_domain": COVERAGE_LEVEL_COMPLETE,
            "emotion_regulation_domain": COVERAGE_LEVEL_COMPLETE,
            "values_identity_domain": COVERAGE_LEVEL_COMPLETE,
            "meaning": COVERAGE_LEVEL_COMPLETE,
            "spirituality_worldview": COVERAGE_LEVEL_COMPLETE,
        }
    )

    plan = _engine().plan(graph, proposal, fingerprint_coverage=coverage, max_questions=3)

    assert not plan.questions
    assert plan.overall_need_for_clarification == NEED_LOW


def test_evidence_linked_ambiguous_plan_includes_reason_and_gain():
    graph, proposal = _identity_case()
    plan = _engine().plan(graph, proposal, max_questions=1)

    question = plan.questions[0]
    assert question.reason
    assert question.expected_information_gain >= 0.87
    assert question.id.startswith("clarify_identity_dissonance_")
