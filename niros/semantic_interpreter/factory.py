from __future__ import annotations

import os

from niros.semantic_interpreter.base import SemanticInterpreter
from niros.semantic_interpreter.mock import MockSemanticInterpreter
from niros.semantic_interpreter.openai_provider import OpenAISemanticInterpreter

SUPPORTED_PROVIDERS = frozenset({"mock", "openai"})


def get_semantic_interpreter(provider: str = "mock") -> SemanticInterpreter:
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported semantic interpreter provider: {provider}")

    if provider == "mock":
        return MockSemanticInterpreter()

    if provider == "openai":
        return OpenAISemanticInterpreter(api_key=os.getenv("OPENAI_API_KEY"))

    raise ValueError(f"Unsupported semantic interpreter provider: {provider}")
