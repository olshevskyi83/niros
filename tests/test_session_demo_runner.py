import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from run_session_demo import build_sample_profile, run_session_demo


def test_script_entrypoint_exists():
    script_path = SCRIPTS_DIR / "run_session_demo.py"

    assert script_path.is_file()


def test_run_session_demo_runs_without_crashing():
    output = io.StringIO()

    exit_code = run_session_demo(output_stream=output)

    assert exit_code == 0
    assert output.getvalue()


def test_run_session_demo_output_contains_timeline_sections():
    rendered = io.StringIO()
    run_session_demo(output_stream=rendered)
    output = rendered.getvalue()

    assert "=== NIROS Session Demo ===" in output
    assert "=== NIROS Session Timeline ===" in output
    assert "Human Profile" in output
    assert "Scenario Blueprint" in output
    assert "Scenario Script Skeleton" in output
    for state in (
        "OPENING",
        "STABILIZATION",
        "EXPLORATION",
        "INTEGRATION",
        "CLOSING",
    ):
        assert state in output


def test_sample_profile_has_detected_patterns():
    profile = build_sample_profile()

    assert profile["primary_pattern"] is not None
    assert profile["pattern_counts"]
    assert len(profile["pattern_counts"]) == 3


def test_script_main_runs_as_subprocess():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "run_session_demo.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0
    assert "=== NIROS Session Timeline ===" in result.stdout
    assert "OPENING" in result.stdout
