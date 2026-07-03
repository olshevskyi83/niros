import io
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from run_niros import COMPLETION_MESSAGE, WELCOME_BANNER, run_niros


def test_runner_exists():
    assert (SCRIPTS_DIR / "run_niros.py").is_file()


def test_runner_completes_with_mock_provider():
    output = io.StringIO()

    exit_code = run_niros(
        user_inputs=[
            "I worry people will stop liking me.",
            "I try to make everyone happy.",
            "I push my feelings down so I can keep going.",
        ],
        turns=3,
        provider="mock",
        output_stream=output,
    )

    assert exit_code == 0
    assert output.getvalue()


def test_mock_provider_is_reported():
    output = io.StringIO()

    run_niros(
        "I stay quiet even when I disagree.",
        turns=1,
        provider="mock",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "Semantic provider: mock" in rendered
    assert "Provider selection:" in rendered


def test_runner_output_contains_mvp_sections():
    output = io.StringIO()

    run_niros(
        user_inputs=[
            "I feel anxious when people become distant.",
            "I try to make everyone happy.",
            "My mind gets stuck on the same worries.",
        ],
        turns=3,
        provider="mock",
        output_stream=output,
    )

    rendered = output.getvalue()

    assert WELCOME_BANNER in rendered
    assert "Human Profile Summary" in rendered
    assert "Human Profile" in rendered
    assert "=== Human Profile Report ===" in rendered
    assert "Human Profile Report" in rendered
    assert "Scenario Blueprint" in rendered
    assert "Session Timeline" in rendered
    assert "=== NIROS Session Timeline ===" in rendered
    assert COMPLETION_MESSAGE in rendered


def test_runner_openai_provider_does_not_crash_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = io.StringIO()

    exit_code = run_niros(
        "I worry people will stop liking me.",
        turns=1,
        provider="openai",
        output_stream=output,
    )

    assert exit_code == 0
    assert "Semantic provider: openai" in output.getvalue()


def test_runner_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported semantic interpreter provider"):
        run_niros(
            "I worry people will stop liking me.",
            provider="anthropic",
            output_stream=io.StringIO(),
        )


def test_runner_main_runs_as_subprocess():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "run_niros.py"), "--turns", "1"],
        input="I worry people will stop liking me.\n",
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0
    assert "Scenario Blueprint" in result.stdout
    assert "Session Timeline" in result.stdout
