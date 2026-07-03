import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demo_interview import DEFAULT_SEMANTIC_PROVIDER, FIRST_QUESTION, run_demo, run_pipeline


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
        "I stay quiet even when I disagree. I am afraid of disappointing people.",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert "NIROS Human Understanding Engine" in rendered
    assert FIRST_QUESTION in rendered
    assert "Detected Patterns" in rendered
    assert "Current Hypothesis" in rendered
    assert "NIROS Interview Summary" in rendered
    assert "Human Profile Summary" in rendered
    assert "=== Human Profile Report ===" in rendered
    assert "Overview" in rendered
    assert "Total turns: 1" in rendered
    assert rendered.count("⸻") >= 4


def test_run_demo_multi_turn_summary():
    output = io.StringIO()

    exit_code = run_demo(
        user_inputs=[
            "I worry people will stop liking me.",
            "I try to make everyone happy.",
            "I stay quiet even when I disagree.",
        ],
        turns=3,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert "Question 1:" in rendered
    assert "Question 2:" in rendered
    assert "Question 3:" in rendered
    assert "NIROS Interview Summary" in rendered
    assert "Total turns: 3" in rendered
    assert "Unique detected patterns:" in rendered
    assert "Strongest pattern:" in rendered
    assert "Questions asked:" in rendered


def test_run_demo_default_semantic_provider_is_mock():
    output = io.StringIO()

    run_demo(
        "I worry people will stop liking me.",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert f"Semantic provider: {DEFAULT_SEMANTIC_PROVIDER}" in rendered
    assert "Semantic provider: mock" in rendered


def test_run_demo_openai_provider_is_printed_without_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-key-value")
    output = io.StringIO()

    run_demo(
        "I worry people will stop liking me.",
        provider="openai",
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
        "I worry people will stop liking me.",
        provider="openai",
        mode="mock_llm",
        output_stream=output,
    )

    assert exit_code == 0
    assert "Semantic provider: openai" in output.getvalue()


def test_run_demo_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported semantic interpreter provider"):
        run_demo(
            "I worry people will stop liking me.",
            provider="anthropic",
            output_stream=io.StringIO(),
        )
