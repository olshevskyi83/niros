import os

import pytest

from niros.env_loader import load_project_env
from niros.runtime_config import (
    REAL_PROVIDER,
    build_runtime_settings,
    describe_openai_startup,
    has_openai_api_key,
    resolve_semantic_provider,
)


def test_load_project_env_reads_openai_api_key_from_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('OPENAI_API_KEY=dotenv-secret-key\n', encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    loaded = load_project_env(env_path=env_file)

    assert loaded is True
    assert os.getenv("OPENAI_API_KEY") == "dotenv-secret-key"


def test_load_project_env_does_not_override_existing_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('OPENAI_API_KEY=from-dotenv\n', encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "from-shell")

    load_project_env(env_path=env_file)

    assert os.getenv("OPENAI_API_KEY") == "from-shell"


def test_load_project_env_returns_false_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    loaded = load_project_env(env_path=tmp_path / "missing.env")

    assert loaded is False


def test_describe_openai_startup_available(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "configured-key")

    status = describe_openai_startup()

    assert status.available is True
    assert status.lines == ("OpenAI semantic extraction: available.",)


def test_describe_openai_startup_unavailable_explains_setup(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    status = describe_openai_startup()

    assert status.available is False
    assert "unavailable" in status.lines[0]
    assert ".env" in status.lines[1]
    assert "RUN_REAL_INTERVIEW.md" in status.lines[1]


def test_explicit_openai_without_key_reports_unavailability(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider, message = resolve_semantic_provider(explicit_provider=REAL_PROVIDER)

    assert provider == REAL_PROVIDER
    assert message is not None
    assert "no API key is configured" in message


def test_build_runtime_settings_uses_dotenv_key(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('OPENAI_API_KEY=dotenv-runtime-key\n', encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    load_project_env(env_path=env_file)

    settings = build_runtime_settings()

    assert has_openai_api_key() is True
    assert settings.provider == REAL_PROVIDER
