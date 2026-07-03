from __future__ import annotations

from niros.semantic_interpreter.factory import get_semantic_interpreter

SUPPORTED_MODES = frozenset({"passthrough", "mock_llm"})


def normalize_user_input(
    raw_text: str,
    mode: str = "passthrough",
    provider: str = "mock",
) -> str:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported normalizer mode: {mode}")

    stripped = raw_text.strip()
    if mode == "passthrough":
        return stripped

    statements = get_semantic_interpreter(provider).interpret_result(stripped).canonical_statements
    if not statements:
        return ""
    return " ".join(statements)
