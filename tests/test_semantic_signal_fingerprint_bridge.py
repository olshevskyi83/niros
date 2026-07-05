"""Tests for Semantic Signal Graph -> Fingerprint update proposal bridge."""

from __future__ import annotations

import re

from niros.semantic_signal_fingerprint_bridge import (
    ACCEPT_CONFIDENCE_THRESHOLD,
    FORBIDDEN_BRIDGE_PHRASES,
    SemanticSignalFingerprintBridge,
    propose_fingerprint_updates,
    render_fingerprint_update_proposal,
)
from niros.semantic_signal_graph import (
    SemanticEvidence,
    SemanticOpenQuestion,
    SemanticSignalGraph,
    SemanticSignalNode,
    build_semantic_signal_graph,
)

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(?:is|e|ed|ing)|disorder|patholog(?:y|ical)|clinical disorder)\b",
    re.IGNORECASE,
)


def _bridge() -> SemanticSignalFingerprintBridge:
    return SemanticSignalFingerprintBridge()


def _accepted_signals(proposal) -> set[str]:
    return {item.signal for item in proposal.accepted_signals}


def _candidate_signals(proposal) -> set[str]:
    return {item.signal for item in proposal.candidate_signals}


def _blocked_signals(proposal) -> set[str]:
    return {item.signal for item in proposal.blocked_updates}


def test_high_confidence_confirmed_signal_becomes_accepted_proposal():
    graph = build_semantic_signal_graph(
        text="I do not believe in God and religious language makes me uncomfortable.",
    )
    proposal = _bridge().propose(graph)

    assert {"secular_worldview", "religion_averse", "symbolic_constraint"}.issubset(
        _accepted_signals(proposal)
    )
    accepted = next(item for item in proposal.accepted_signals if item.signal == "religion_averse")
    assert accepted.confidence >= ACCEPT_CONFIDENCE_THRESHOLD
    assert accepted.domain == "spirituality_worldview"
    assert accepted.recommended_fingerprint_field.startswith("spirituality_worldview.")


def test_medium_confidence_confirmed_signal_becomes_candidate_and_open_question():
    graph = build_semantic_signal_graph(
        text="I constantly criticize myself even when I do well.",
    )
    proposal = _bridge().propose(graph)

    assert "self_criticism" in _candidate_signals(proposal)
    assert "self_criticism" not in _accepted_signals(proposal)
    assert any(
        question.target_signal == "self_criticism" for question in proposal.open_questions
    )


def test_low_confidence_signal_is_blocked():
    graph = build_semantic_signal_graph(
        text="I lost someone and since then everything feels empty.",
    )
    proposal = _bridge().propose(graph)

    assert "social_withdrawal" in _blocked_signals(proposal)
    assert "social_withdrawal" not in _accepted_signals(proposal)


def test_interpretation_candidate_requiring_clarification_is_not_accepted():
    graph = build_semantic_signal_graph(
        text="I feel like I am living someone else's life.",
    )
    proposal = _bridge().propose(graph)

    assert not proposal.accepted_signals
    assert "identity_dissonance" in _candidate_signals(proposal)
    assert "identity_dissonance" in _blocked_signals(proposal)


def test_ambiguous_competing_interpretations_require_clarification():
    graph = build_semantic_signal_graph(
        text="I feel like I am living someone else's life.",
    )
    proposal = _bridge().propose(graph)

    assert not proposal.accepted_signals
    assert proposal.candidate_signals
    assert proposal.open_questions
    assert all(item.requires_clarification for item in proposal.candidate_signals)
    assert any(
        "someone else's life" in item.reason.lower()
        for item in proposal.candidate_signals
    )


def test_evidence_is_preserved_in_accepted_proposals():
    text = "I do not believe in God and religious language makes me uncomfortable."
    graph = build_semantic_signal_graph(text=text)
    proposal = _bridge().propose(graph)

    accepted = next(item for item in proposal.accepted_signals if item.signal == "secular_worldview")
    assert text in accepted.evidence


def test_domain_mapping_works():
    graph = build_semantic_signal_graph(
        text="I constantly criticize myself even when I do well.",
    )
    proposal = _bridge().propose(graph)

    by_signal = {item.signal: item for item in proposal.candidate_signals}
    assert by_signal["self_criticism"].domain == "self"
    assert by_signal["low_self_worth"].domain == "self"
    assert by_signal["shame_sensitivity"].domain == "self"


def test_spirituality_worldview_signals_map_correctly():
    graph = build_semantic_signal_graph(
        text="I do not believe in God and religious language makes me uncomfortable.",
    )
    proposal = _bridge().propose(graph)

    for signal in ("secular_worldview", "religion_averse", "symbolic_constraint"):
        accepted = next(item for item in proposal.accepted_signals if item.signal == signal)
        assert accepted.domain == "spirituality_worldview"
        assert accepted.recommended_fingerprint_field.startswith("spirituality_worldview.")


def test_no_diagnostic_language():
    examples = [
        "I feel like I am living someone else's life.",
        "I constantly criticize myself even when I do well.",
        "I lost someone and since then everything feels empty.",
        "I do not believe in God and religious language makes me uncomfortable.",
    ]
    combined = "\n".join(
        render_fingerprint_update_proposal(
            propose_fingerprint_updates(build_semantic_signal_graph(text=text))
        )
        for text in examples
    )
    lowered = combined.lower()

    assert DIAGNOSIS_PATTERN.search(combined) is None
    for phrase in FORBIDDEN_BRIDGE_PHRASES:
        assert phrase not in lowered


def test_output_is_deterministic():
    text = "I lost someone and since then everything feels empty."
    first = _bridge().propose(build_semantic_signal_graph(text=text))
    second = _bridge().propose(build_semantic_signal_graph(text=text))

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_signal_without_evidence_is_blocked():
    graph = SemanticSignalGraph(
        language="en",
        original_text="Detached signal.",
        nodes=(
            SemanticSignalNode(
                id="self_criticism",
                signal_type="self_criticism",
                label="self criticism",
                domain="self",
                confidence=0.91,
                evidence_ids=(),
                needs_clarification=False,
                interpretation_status="confirmed",
            ),
        ),
        edges=(),
        evidence=(),
        open_questions=(),
    )
    proposal = _bridge().propose(graph)

    assert proposal.accepted_signals == ()
    assert "self_criticism" in _blocked_signals(proposal)
    assert any(item.reason == "No supporting evidence" for item in proposal.blocked_updates)


def test_graph_open_questions_are_carried_forward():
    graph = SemanticSignalGraph(
        language="en",
        original_text="I feel like I am living someone else's life.",
        nodes=(
            SemanticSignalNode(
                id="identity_dissonance",
                signal_type="identity_dissonance",
                label="identity dissonance",
                domain="identity",
                confidence=0.46,
                evidence_ids=("ev_001",),
                needs_clarification=True,
                interpretation_status="ambiguous",
            ),
        ),
        edges=(),
        evidence=(
            SemanticEvidence(
                id="ev_001",
                text="I feel like I am living someone else's life.",
                source_span="I feel like I am living someone else's life.",
                language="en",
                confidence=1.0,
            ),
        ),
        open_questions=(
            SemanticOpenQuestion(
                id="oq_01",
                question=(
                    "When you say you are living someone else's life, do you mean your work, "
                    "your relationships, your values, or something else?"
                ),
                target_signal="identity_dissonance",
                reason="Ambiguous",
                priority="high",
            ),
        ),
        interpretation_candidates=(),
    )
    proposal = _bridge().propose(graph)

    assert any(
        "work" in question.question and question.priority == "high"
        for question in proposal.open_questions
    )
