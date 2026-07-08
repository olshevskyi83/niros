"""Tests for semantic therapeutic relevance gate."""

from __future__ import annotations

from niros.semantic_therapeutic_gate import (
    KNOWLEDGE_KIND_EXERCISE_OR_PRACTICE,
    KNOWLEDGE_KIND_FRONT_MATTER,
    KNOWLEDGE_KIND_MARKETING,
    KNOWLEDGE_KIND_STATISTICS_ONLY,
    KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
    SKIP_REASON_FRONT_MATTER,
    SKIP_REASON_KEYWORD_ONLY,
    SKIP_REASON_MARKETING,
    SKIP_REASON_NO_ACTIONABLE_MECHANISM,
    SKIP_REASON_STATISTICS_ONLY,
    evaluate_chunk_relevance,
)


def _decision(text: str, *, chunk_id: str = "chunk_001", source_id: str = "source_001"):
    return evaluate_chunk_relevance(
        source_id=source_id,
        chunk_id=chunk_id,
        text=text,
    )


def test_skips_copyright_front_matter() -> None:
    decision = _decision(
        "Copyright 2024 Example Publisher. ISBN 978-0-000-0000-0. All rights reserved."
    )
    assert decision.should_extract is False
    assert decision.knowledge_kind == KNOWLEDGE_KIND_FRONT_MATTER
    assert decision.skip_reason == SKIP_REASON_FRONT_MATTER


def test_skips_table_of_contents() -> None:
    decision = _decision("Table of contents\nChapter 1 Introduction\nChapter 2 Values")
    assert decision.should_extract is False
    assert decision.skip_reason == SKIP_REASON_FRONT_MATTER


def test_skips_marketing_blurb() -> None:
    decision = _decision(
        "This book helps readers overcome anxiety and depression with practical tools."
    )
    assert decision.should_extract is False
    assert decision.knowledge_kind == KNOWLEDGE_KIND_MARKETING
    assert decision.skip_reason == SKIP_REASON_MARKETING


def test_skips_statistics_only_text() -> None:
    decision = _decision(
        "Studies show that 42% of participants reported lower anxiety in the meta-analysis."
    )
    assert decision.should_extract is False
    assert decision.knowledge_kind == KNOWLEDGE_KIND_STATISTICS_ONLY
    assert decision.skip_reason == SKIP_REASON_STATISTICS_ONLY


def test_skips_keyword_only_act_sentence() -> None:
    decision = _decision("ACT uses acceptance and values.")
    assert decision.should_extract is False
    assert decision.skip_reason == SKIP_REASON_KEYWORD_ONLY


def test_accepts_experiential_avoidance_mechanism() -> None:
    decision = _decision(
        "When a client tries to control painful feelings, short-term distress drops but "
        "long-term suffering increases because experiential avoidance moves them away "
        "from valued action."
    )
    assert decision.should_extract is True
    assert decision.knowledge_kind == KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM
    assert "experiential avoidance" in decision.reasoning.lower()
    assert decision.evidence_span


def test_accepts_defusion_mechanism() -> None:
    decision = _decision(
        "Cognitive defusion helps the client see thoughts as thoughts and unhook from "
        "believing them literally because the process changes their relationship to thinking."
    )
    assert decision.should_extract is True
    assert decision.knowledge_kind == KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM
    assert "defusion" in decision.reasoning.lower()


def test_accepts_concrete_exercise_or_practice() -> None:
    decision = _decision(
        "Try this exercise: notice your breathing, observe the urge to avoid, and practice "
        "willingness to feel the emotion because the client learns contact with experience."
    )
    assert decision.should_extract is True
    assert decision.knowledge_kind == KNOWLEDGE_KIND_EXERCISE_OR_PRACTICE


def test_case_example_requires_explicit_mechanism() -> None:
    vague = _decision("For example, a client felt anxious.")
    assert vague.should_extract is False
    assert vague.skip_reason == SKIP_REASON_NO_ACTIONABLE_MECHANISM

    explicit = _decision(
        "For example, a client noticed urges to avoid painful feelings. When they practiced "
        "willingness instead of control, short-term distress rose but valued action returned "
        "because experiential avoidance had been blocking committed action."
    )
    assert explicit.should_extract is True


def test_returns_reasoning_and_evidence_span() -> None:
    decision = _decision(
        "When a client defuses from thoughts, they observe thoughts as thoughts and unhook "
        "from literal belief because the process changes behavior toward values."
    )
    assert decision.reasoning
    assert decision.evidence_span
    assert decision.relevance_score > 0.0
