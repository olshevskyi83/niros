"""Tests for Human Language Understanding Pipeline orchestrator."""

from __future__ import annotations

import re

from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.human_language_understanding_pipeline import (
    FORBIDDEN_PIPELINE_PHRASES,
    HumanLanguageUnderstandingPipeline,
    run_human_language_understanding,
)
from niros.patterns import PatternTag
from niros.models import SupportedLanguage

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(?:is|e|ed|ing)|disorder|patholog(?:y|ical)|clinical disorder)\b",
    re.IGNORECASE,
)


def _pipeline() -> HumanLanguageUnderstandingPipeline:
    return HumanLanguageUnderstandingPipeline()


def _signal_types(result) -> set[str]:
    return {node.signal_type for node in result.semantic_signal_graph.nodes}


def _accepted(result) -> set[str]:
    return {item.signal for item in result.accepted_signals}


def _candidates(result) -> set[str]:
    return {item.signal for item in result.candidate_signals}


def test_pipeline_returns_all_result_sections():
    result = _pipeline().run(text="I feel like I am living someone else's life.")

    assert result.semantic_signal_graph
    assert result.fingerprint_update_proposal is not None
    assert result.clarification_plan is not None
    assert isinstance(result.interview_questions, tuple)
    assert isinstance(result.accepted_signals, tuple)
    assert isinstance(result.candidate_signals, tuple)
    assert isinstance(result.blocked_updates, tuple)
    assert isinstance(result.open_questions, tuple)
    assert isinstance(result.overall_confidence, float)
    assert isinstance(result.needs_clarification, bool)
    assert result.to_dict()


def test_ambiguous_identity_text_creates_candidate_signals_and_clarification_question():
    result = _pipeline().run(text="I feel like I am living someone else's life.")

    assert not result.accepted_signals
    assert "identity_dissonance" in _candidates(result)
    assert result.needs_clarification is True
    assert result.open_questions or result.interview_questions
    assert any(
        "someone else's life" in item.question
        for item in (*result.open_questions, *result.interview_questions)
    )


def test_self_criticism_text_creates_self_related_signals():
    result = _pipeline().run(text="I constantly criticize myself even when I do well.")

    signals = _accepted(result) | _candidates(result)
    assert {"self_criticism", "low_self_worth", "shame_sensitivity"}.issubset(signals)


def test_grief_text_creates_grief_and_meaning_signals():
    result = _pipeline().run(text="I lost someone and since then everything feels empty.")

    graph_signals = _signal_types(result)
    assert "grief_loss" in graph_signals
    assert "meaning_disruption" in graph_signals


def test_atheist_religion_averse_text_creates_worldview_signals():
    result = _pipeline().run(
        text="I do not believe in God and religious language makes me uncomfortable.",
    )

    assert {"secular_worldview", "religion_averse", "symbolic_constraint"}.issubset(_accepted(result))
    assert result.needs_clarification is False


def test_no_direct_fingerprint_mutation():
    patterns = [
        PatternTag(
            id="tag-spiritual_resistance",
            session_id="session-hlu",
            evidence_id="session-hlu:evidence:0",
            canonical_id="spiritual_resistance",
            matched_text="religious language makes me uncomfortable",
            confidence=1.0,
            language=SupportedLanguage.ENGLISH,
        )
    ]
    before = build_human_digital_fingerprint(detected_patterns=patterns)
    _pipeline().run(
        text="I do not believe in God and religious language makes me uncomfortable.",
        patterns=["spiritual_resistance"],
    )
    after = build_human_digital_fingerprint(detected_patterns=patterns)

    assert before == after


def test_evidence_is_preserved():
    text = "I lost someone and since then everything feels empty."
    result = _pipeline().run(text=text)

    assert result.semantic_signal_graph.evidence
    assert result.semantic_signal_graph.evidence[0].text == text
    for item in result.accepted_signals:
        assert item.evidence
    for item in result.candidate_signals:
        assert item.reason


def test_needs_clarification_true_for_ambiguous_text():
    result = _pipeline().run(text="I feel like I am living someone else's life.")
    assert result.needs_clarification is True


def test_needs_clarification_false_for_high_confidence_text():
    result = _pipeline().run(
        text="I do not believe in God and religious language makes me uncomfortable.",
    )
    assert result.needs_clarification is False


def test_deterministic_output():
    text = "I constantly criticize myself even when I do well."
    first = run_human_language_understanding(text)
    second = run_human_language_understanding(text)

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_no_diagnostic_language():
    examples = [
        "I feel like I am living someone else's life.",
        "I constantly criticize myself even when I do well.",
        "I lost someone and since then everything feels empty.",
        "I do not believe in God and religious language makes me uncomfortable.",
    ]
    combined = "\n".join(
        str(run_human_language_understanding(text).to_dict()) for text in examples
    ).lower()

    assert DIAGNOSIS_PATTERN.search(combined) is None
    for phrase in FORBIDDEN_PIPELINE_PHRASES:
        assert phrase not in combined
