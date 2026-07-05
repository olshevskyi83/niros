"""Tests for Semantic Signal Graph — Human Language Understanding layer."""

from __future__ import annotations

import re

from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_signal_graph import (
    CLARIFICATION_THRESHOLD,
    INTERPRETATION_AMBIGUOUS,
    INTERPRETATION_CANDIDATE,
    INTERPRETATION_CONFIRMED,
    FORBIDDEN_GRAPH_PHRASES,
    SemanticSignalGraphBuilder,
    build_semantic_signal_graph,
    render_semantic_signal_graph,
)

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(?:is|e|ed|ing)|disorder|patholog(?:y|ical)|clinical disorder)\b",
    re.IGNORECASE,
)


def _signal_types(graph) -> set[str]:
    return {node.signal_type for node in graph.nodes}


def test_graph_can_be_created():
    graph = build_semantic_signal_graph(
        text="I feel like I am living someone else's life.",
        language="en",
    )

    assert graph.original_text
    assert graph.language == "en"
    assert graph.nodes
    assert graph.evidence


def test_nodes_have_required_fields():
    graph = build_semantic_signal_graph(
        text="I constantly criticize myself even when I do well.",
    )
    node = graph.nodes[0]

    assert node.id
    assert node.signal_type
    assert node.label
    assert node.domain
    assert 0.0 <= node.confidence <= 1.0
    assert node.evidence_ids
    assert isinstance(node.needs_clarification, bool)
    assert node.interpretation_status in {
        INTERPRETATION_CONFIRMED,
        INTERPRETATION_CANDIDATE,
        INTERPRETATION_AMBIGUOUS,
    }


def test_evidence_is_preserved():
    text = "I lost someone and since then everything feels empty."
    graph = build_semantic_signal_graph(text=text, language="en")

    assert len(graph.evidence) == 1
    assert graph.evidence[0].text == text
    assert graph.evidence[0].source_span == text
    assert graph.evidence[0].language == "en"
    assert graph.nodes[0].evidence_ids == (graph.evidence[0].id,)


def test_living_someone_elses_life_creates_identity_values_agency_meaning_signals():
    graph = build_semantic_signal_graph(
        text="I feel like I am living someone else's life.",
    )

    signals = _signal_types(graph)
    assert {
        "identity_dissonance",
        "values_conflict",
        "self_alienation",
        "agency_reduction",
        "meaning_disruption",
    }.issubset(signals)


def test_living_someone_elses_life_generates_open_questions_and_candidates():
    graph = build_semantic_signal_graph(
        text="I feel like I am living someone else's life.",
    )

    assert graph.open_questions
    assert graph.interpretation_candidates
    assert all(candidate.clarification_required for candidate in graph.interpretation_candidates)
    assert all(node.needs_clarification for node in graph.candidate_nodes())
    assert not graph.confirmed_nodes()
    assert any(
        "someone else's life" in question.question.lower()
        for question in graph.open_questions
    )


def test_self_criticism_text_creates_expected_signals():
    graph = build_semantic_signal_graph(
        text="I constantly criticize myself even when I do well.",
    )

    signals = _signal_types(graph)
    assert {"self_criticism", "low_self_worth", "shame_sensitivity"}.issubset(signals)


def test_grief_text_creates_grief_and_meaning_signals():
    graph = build_semantic_signal_graph(
        text="I lost someone and since then everything feels empty.",
    )

    signals = _signal_types(graph)
    assert "grief_loss" in signals
    assert "meaning_disruption" in signals
    assert "emotional_numbness" in signals


def test_atheist_religion_averse_text_creates_worldview_signals():
    graph = build_semantic_signal_graph(
        text="I do not believe in God and religious language makes me uncomfortable.",
    )

    signals = _signal_types(graph)
    assert {"secular_worldview", "religion_averse", "symbolic_constraint"}.issubset(signals)
    assert graph.confirmed_nodes()
    assert not graph.open_questions
    assert not graph.interpretation_candidates


def test_edges_are_deterministic():
    text = "I feel like I am living someone else's life."
    first = build_semantic_signal_graph(text=text)
    second = build_semantic_signal_graph(text=text)

    assert [(edge.source, edge.relation, edge.target) for edge in first.edges] == [
        (edge.source, edge.relation, edge.target) for edge in second.edges
    ]
    assert len(first.edges) >= 3


def test_output_is_deterministic():
    text = "I constantly criticize myself even when I do well."
    first = build_semantic_signal_graph(text=text, language="en")
    second = build_semantic_signal_graph(text=text, language="en")

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert render_semantic_signal_graph(first) == render_semantic_signal_graph(second)


def test_low_confidence_signals_become_candidates_not_confirmed():
    graph = build_semantic_signal_graph(
        text="I feel like I am living someone else's life.",
    )

    for node in graph.nodes:
        if node.confidence < CLARIFICATION_THRESHOLD:
            assert node.interpretation_status in {
                INTERPRETATION_CANDIDATE,
                INTERPRETATION_AMBIGUOUS,
            }
            assert node.needs_clarification is True


def test_builder_consumes_semantic_facts_and_patterns():
    graph = SemanticSignalGraphBuilder().build(
        text="I feel disconnected.",
        semantic_facts=[
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="I feel disconnected.",
            )
        ],
        patterns=["identity_confusion", "harsh_self_criticism"],
    )

    assert "identity_dissonance" in _signal_types(graph)
    assert "self_criticism" in _signal_types(graph)


def test_builder_consumes_interpretation_result():
    result = SemanticInterpretationResult(
        raw_text="I do not believe in God and religious language makes me uncomfortable.",
        canonical_statements=[],
        facts=[
            SemanticFact(
                category="meaning",
                attribute="worldview_orientation",
                value="atheist",
                evidence="I do not believe in God",
            )
        ],
        detected_language="en",
    )
    graph = SemanticSignalGraphBuilder().build_from_interpretation_result(result)

    assert "secular_worldview" in _signal_types(graph)
    assert "religion_averse" in _signal_types(graph)


def test_no_diagnostic_language_is_introduced():
    examples = [
        "I feel like I am living someone else's life.",
        "I constantly criticize myself even when I do well.",
        "I lost someone and since then everything feels empty.",
        "I do not believe in God and religious language makes me uncomfortable.",
    ]
    combined = "\n".join(render_semantic_signal_graph(build_semantic_signal_graph(text=text)) for text in examples)
    lowered = combined.lower()

    assert DIAGNOSIS_PATTERN.search(combined) is None
    for phrase in FORBIDDEN_GRAPH_PHRASES:
        assert phrase not in lowered
