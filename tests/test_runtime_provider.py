import io
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from demo_interview import run_demo
from niros.runtime_config import (
    REAL_PROVIDER,
    RUNTIME_MODE_REAL,
    RUNTIME_MODE_TEST,
    TEST_PROVIDER,
    build_runtime_settings,
    has_openai_api_key,
    resolve_semantic_provider,
)
from run_niros import run_niros


def test_automatic_provider_selects_openai_when_api_key_exists(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-value")

    provider, message = resolve_semantic_provider()

    assert provider == REAL_PROVIDER
    assert message is not None
    assert "OPENAI_API_KEY detected" in message


def test_automatic_provider_falls_back_to_mock_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider, message = resolve_semantic_provider()

    assert provider == TEST_PROVIDER
    assert message is not None
    assert "OPENAI_API_KEY not set" in message


def test_run_niros_startup_reports_openai_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = io.StringIO()

    run_niros(
        "I worry people will stop liking me.",
        turns=1,
        provider="mock",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "OpenAI semantic extraction: unavailable." in rendered
    assert ".env" in rendered


def test_run_niros_startup_reports_openai_available_with_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "configured-key")
    output = io.StringIO()

    run_niros(
        "I worry people will stop liking me.",
        turns=1,
        provider="mock",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "OpenAI semantic extraction: available." in rendered


def test_explicit_openai_provider_without_key_shows_setup_hint(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = io.StringIO()

    run_niros(
        "I worry people will stop liking me.",
        turns=1,
        provider="openai",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "Semantic provider: openai" in rendered
    assert "no API key is configured" in rendered
    assert ".env" in rendered


def test_runtime_mode_test_forces_mock():
    provider, message = resolve_semantic_provider(explicit_runtime_mode=RUNTIME_MODE_TEST)

    assert provider == TEST_PROVIDER
    assert "TEST" in message


def test_runtime_mode_real_without_key_falls_back_to_mock(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider, message = resolve_semantic_provider(explicit_runtime_mode=RUNTIME_MODE_REAL)

    assert provider == TEST_PROVIDER
    assert "falling back to mock" in message


def test_build_runtime_settings_real_mode_with_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-value")

    settings = build_runtime_settings(explicit_runtime_mode=RUNTIME_MODE_REAL)

    assert settings.runtime_mode == RUNTIME_MODE_REAL
    assert settings.provider == REAL_PROVIDER


def test_no_api_key_leakage_in_run_niros_output(monkeypatch):
    secret = "super-secret-openai-key"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    output = io.StringIO()

    run_niros(
        "I worry people will stop liking me.",
        turns=1,
        provider="openai",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert secret not in rendered
    assert "OPENAI_API_KEY" not in rendered


def test_no_api_key_leakage_in_run_demo_output(monkeypatch):
    secret = "super-secret-openai-key"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    output = io.StringIO()

    run_demo(
        "I worry people will stop liking me.",
        provider="openai",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert secret not in rendered
    assert "OPENAI_API_KEY" not in rendered


def test_run_niros_debug_mode_prints_pipeline_sections():
    output = io.StringIO()

    run_niros(
        "I worry people will stop liking me.",
        turns=1,
        provider="mock",
        debug=True,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "=== Debug Pipeline ===" in rendered
    assert "Raw transcript:" in rendered
    assert "Semantic Facts:" in rendered
    assert "Detected Patterns:" in rendered
    assert "Human Digital Fingerprint:" in rendered


def test_run_niros_explicit_mock_provider_for_tests():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-value")
    output = io.StringIO()

    run_niros(
        "I stay quiet even when I disagree.",
        turns=1,
        provider="mock",
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "Semantic provider: mock" in rendered
    monkeypatch.undo()


def test_has_openai_api_key_helper():
    assert has_openai_api_key() is bool(os.getenv("OPENAI_API_KEY"))
