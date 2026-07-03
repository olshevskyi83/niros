from __future__ import annotations

import os
from dataclasses import dataclass

from niros.semantic_interpreter.factory import SUPPORTED_PROVIDERS

RUNTIME_MODE_TEST = "test"
RUNTIME_MODE_REAL = "real"

TEST_PROVIDER = "mock"
REAL_PROVIDER = "openai"

DEFAULT_NORMALIZER_MODE_TEST = "passthrough"
DEFAULT_NORMALIZER_MODE_REAL = "passthrough"

OPENAI_KEY_ENV_VAR = "OPENAI_API_KEY"

OPENAI_SETUP_HINT = (
    "To enable OpenAI semantic extraction, add your API key to a .env file at the "
    "project root or export it in your shell before launching NIROS. "
    "See docs/RUN_REAL_INTERVIEW.md for setup steps."
)


@dataclass(frozen=True)
class OpenAIStartupStatus:
    available: bool
    lines: tuple[str, ...]


def has_openai_api_key() -> bool:
    return bool(os.getenv(OPENAI_KEY_ENV_VAR))


def describe_openai_startup() -> OpenAIStartupStatus:
    if has_openai_api_key():
        return OpenAIStartupStatus(
            available=True,
            lines=("OpenAI semantic extraction: available.",),
        )
    return OpenAIStartupStatus(
        available=False,
        lines=(
            "OpenAI semantic extraction: unavailable.",
            OPENAI_SETUP_HINT,
        ),
    )


def format_openai_startup_lines() -> list[str]:
    return list(describe_openai_startup().lines)


@dataclass(frozen=True)
class RuntimeSettings:
    runtime_mode: str
    provider: str
    normalizer_mode: str
    selection_message: str | None


def resolve_semantic_provider(
    *,
    explicit_provider: str | None = None,
    explicit_runtime_mode: str | None = None,
) -> tuple[str, str | None]:
    if explicit_runtime_mode == RUNTIME_MODE_TEST:
        return (
            TEST_PROVIDER,
            "Runtime mode TEST selected; using mock semantic provider.",
        )

    if explicit_runtime_mode == RUNTIME_MODE_REAL:
        if not has_openai_api_key():
            return (
                TEST_PROVIDER,
                "Runtime mode REAL requested but OPENAI_API_KEY is not set; "
                "falling back to mock semantic provider.",
            )
        return (
            REAL_PROVIDER,
            "Runtime mode REAL selected; using OpenAI semantic provider.",
        )

    if explicit_provider is not None:
        if explicit_provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported semantic interpreter provider: {explicit_provider}")
        if explicit_provider == REAL_PROVIDER and not has_openai_api_key():
            return (
                REAL_PROVIDER,
                "OpenAI provider selected, but no API key is configured. "
                "Semantic extraction will be unavailable until one is set. "
                f"{OPENAI_SETUP_HINT}",
            )
        if explicit_provider == REAL_PROVIDER:
            return REAL_PROVIDER, "OpenAI provider selected; semantic extraction available."
        return explicit_provider, None

    if has_openai_api_key():
        return (
            REAL_PROVIDER,
            "OPENAI_API_KEY detected; using OpenAI as the default semantic provider.",
        )

    return (
        TEST_PROVIDER,
        "OPENAI_API_KEY not set; using mock semantic provider.",
    )


def resolve_runtime_mode(provider: str) -> str:
    if provider == REAL_PROVIDER:
        return RUNTIME_MODE_REAL
    return RUNTIME_MODE_TEST


def resolve_normalizer_mode(
    *,
    runtime_mode: str,
    explicit_mode: str | None = None,
) -> str:
    if explicit_mode is not None:
        return explicit_mode
    if runtime_mode == RUNTIME_MODE_REAL:
        return DEFAULT_NORMALIZER_MODE_REAL
    return DEFAULT_NORMALIZER_MODE_TEST


def build_runtime_settings(
    *,
    explicit_provider: str | None = None,
    explicit_runtime_mode: str | None = None,
    explicit_normalizer_mode: str | None = None,
) -> RuntimeSettings:
    provider, selection_message = resolve_semantic_provider(
        explicit_provider=explicit_provider,
        explicit_runtime_mode=explicit_runtime_mode,
    )
    runtime_mode = (
        explicit_runtime_mode
        if explicit_runtime_mode is not None
        else resolve_runtime_mode(provider)
    )
    normalizer_mode = resolve_normalizer_mode(
        runtime_mode=runtime_mode,
        explicit_mode=explicit_normalizer_mode,
    )
    return RuntimeSettings(
        runtime_mode=runtime_mode,
        provider=provider,
        normalizer_mode=normalizer_mode,
        selection_message=selection_message,
    )
