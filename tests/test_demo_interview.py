import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demo_interview import DEFAULT_SEMANTIC_PROVIDER, run_demo, run_pipeline
from niros.intake_protocol import DEFAULT_INTAKE_PROTOCOL, PRESENTING_PROBLEM_ID


def test_run_pipeline_returns_follow_up_question():
    pattern_tags, _hypotheses, next_question = run_pipeline(
        "I worry people will stop liking me. I try to make everyone happy.",
        "demo-session-test",
    )

    assert pattern_tags
    assert next_question


def test_run_demo_prints_expected_sections():
    output = io.StringIO()

    exit_code = run_demo(
        user_inputs=["I stay quiet even when I disagree. I am afraid of disappointing people."],
        intake_inputs=[
            "I feel overwhelmed at work.",
            "About six months.",
            "Stress and conflict.",
            "Sleep and focus.",
            "Talked with a friend.",
            "More clarity about myself.",
        ],
        turns=1,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert "NIROS Human Understanding Engine" in rendered
    assert "Structured Intake" in rendered
    assert DEFAULT_INTAKE_PROTOCOL.question_text(PRESENTING_PROBLEM_ID, "en") in rendered
    assert "about yourself" not in rendered.lower()
    assert "Detected Patterns" in rendered
    assert "Current Hypothesis" in rendered
    assert "NIROS Interview Summary" in rendered
    assert "Human Profile Summary" in rendered
    assert "=== Human Profile Report ===" in rendered
    assert "Presenting Problem" in rendered
    assert "Overview" in rendered
    assert rendered.count("⸻") >= 4


def test_run_demo_multi_turn_summary():
    output = io.StringIO()

    exit_code = run_demo(
        user_inputs=[
            "I worry people will stop liking me.",
            "I try to make everyone happy.",
            "I stay quiet even when I disagree.",
        ],
        intake_inputs=[
            "People-pleasing feels exhausting.",
            "Several years.",
            "Family expectations.",
            "Relationships.",
            "Journaling sometimes helps.",
            "More honest communication.",
        ],
        turns=3,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert "Intake Question 1:" in rendered
    assert "Question 1:" in rendered
    assert "NIROS Interview Summary" in rendered
    assert "Unique detected patterns:" in rendered
    assert "Strongest pattern:" in rendered
    assert "Questions asked:" in rendered


def test_run_demo_default_semantic_provider_is_mock(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = io.StringIO()

    run_demo(
        user_inputs=["I worry people will stop liking me."],
        intake_inputs=[
            "I feel anxious around people.",
            "A few months.",
            "Work pressure.",
            "Sleep.",
            "Breathing exercises.",
            "More calm.",
        ],
        turns=1,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert f"Semantic provider: {DEFAULT_SEMANTIC_PROVIDER}" in rendered
    assert "Semantic provider: mock" in rendered


def test_run_demo_openai_provider_is_printed_without_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-key-value")
    output = io.StringIO()

    run_demo(
        user_inputs=["I worry people will stop liking me."],
        turns=1,
        provider="openai",
        skip_intake=True,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "Semantic provider: openai" in rendered
    assert "super-secret-key-value" not in rendered
    assert "OPENAI_API_KEY" not in rendered


def test_run_demo_openai_without_api_key_does_not_crash(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = io.StringIO()

    exit_code = run_demo(
        user_inputs=["I worry people will stop liking me."],
        turns=1,
        provider="openai",
        mode="mock_llm",
        skip_intake=True,
        output_stream=output,
    )

    assert exit_code == 0
    assert "Semantic provider: openai" in output.getvalue()


def test_run_demo_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported semantic interpreter provider"):
        run_demo(
            user_inputs=["I worry people will stop liking me."],
            turns=1,
            provider="anthropic",
            skip_intake=True,
            output_stream=io.StringIO(),
        )
