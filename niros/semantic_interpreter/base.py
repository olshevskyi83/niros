# Future providers may include:
# - OpenAISemanticInterpreter
# - ClaudeSemanticInterpreter
# - GeminiSemanticInterpreter
# - LocalLLMSemanticInterpreter
#
# All providers MUST return canonical NIROS statements.
# They MUST NOT:
# - detect patterns
# - infer diagnoses
# - produce hypotheses
# - access interview state
#
# They only translate natural language into canonical NIROS statements.

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from niros.semantic_interpreter.facts import SemanticFact


@dataclass
class SemanticInterpretationResult:
    raw_text: str
    canonical_statements: list[str]
    facts: list[SemanticFact] = field(default_factory=list)
    provider: str = "mock"
    detected_language: str | None = None
    confidence: float | None = None
    warnings: list[str] = field(default_factory=list)


class SemanticInterpreter(ABC):
    @abstractmethod
    def interpret(self, raw_text: str) -> list[str]:
        """Translate natural language into canonical NIROS statements."""

    def interpret_result(self, raw_text: str) -> SemanticInterpretationResult:
        statements = self.interpret(raw_text)
        return SemanticInterpretationResult(
            raw_text=raw_text,
            canonical_statements=statements,
            provider=self.provider_name,
        )

    @property
    def provider_name(self) -> str:
        return self.__class__.__name__
