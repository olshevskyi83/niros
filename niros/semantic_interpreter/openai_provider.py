# This provider will later:
# Input: natural human response
# Output: SemanticInterpretationResult
#
# The provider MUST ONLY produce semantic facts.
# It MUST NEVER:
# - classify patterns
# - infer diagnoses
# - create hypotheses
# - access interview state

from __future__ import annotations

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from niros.semantic_interpreter.base import (
    SemanticInterpretationResult,
    SemanticInterpreter,
)
from niros.semantic_interpreter.parser import (
    parse_semantic_extraction_response,
    payload_to_semantic_result,
)
from niros.semantic_interpreter.prompts import (
    build_semantic_extraction_system_prompt,
    build_semantic_extraction_user_prompt,
)
from niros.semantic_interpreter.schema import SemanticExtractionPayload

_RETRYABLE_WARNINGS = frozenset(
    {
        "invalid_json",
        "schema_validation_failed",
        "empty_response",
    }
)


class OpenAISemanticInterpreter(SemanticInterpreter):
    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.0,
        api_key: str | None = None,
        client=None,
        max_retries: int = 1,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.max_retries = 0 if max_retries < 0 else max_retries
        if client is not None:
            self.client = client
        elif OpenAI is not None and api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    def _build_messages(self, text: str) -> list[dict[str, str]]:
        system_prompt = build_semantic_extraction_system_prompt()
        user_prompt = build_semantic_extraction_user_prompt(text)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _call_openai(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    def _result_from_payload(
        self,
        text: str,
        payload: SemanticExtractionPayload,
    ) -> SemanticInterpretationResult:
        result = payload_to_semantic_result(payload)
        return SemanticInterpretationResult(
            raw_text=text,
            canonical_statements=[],
            facts=result.facts,
            provider=self.provider_name,
            detected_language=result.detected_language,
            confidence=result.confidence,
            warnings=result.warnings,
        )

    def _should_retry(self, payload: SemanticExtractionPayload) -> bool:
        if payload.facts:
            return False
        return any(warning in _RETRYABLE_WARNINGS for warning in payload.warnings)

    def interpret(self, text: str) -> SemanticInterpretationResult:
        if not text.strip():
            return SemanticInterpretationResult(
                raw_text=text,
                canonical_statements=[],
                facts=[],
                provider=self.provider_name,
                warnings=["empty_input"],
            )

        if self.client is None:
            return SemanticInterpretationResult(
                raw_text=text,
                canonical_statements=[],
                facts=[],
                provider=self.provider_name,
                warnings=["openai_client_unavailable"],
            )

        messages = self._build_messages(text)
        attempt_count = self.max_retries + 1
        last_payload: SemanticExtractionPayload | None = None

        for attempt in range(attempt_count):
            try:
                raw_content = self._call_openai(messages)
                last_payload = parse_semantic_extraction_response(raw_content)
                if not self._should_retry(last_payload):
                    return self._result_from_payload(text, last_payload)
            except Exception:
                if attempt == attempt_count - 1:
                    return SemanticInterpretationResult(
                        raw_text=text,
                        canonical_statements=[],
                        facts=[],
                        provider=self.provider_name,
                        warnings=["openai_provider_error"],
                    )

        if last_payload is not None:
            return self._result_from_payload(text, last_payload)

        return SemanticInterpretationResult(
            raw_text=text,
            canonical_statements=[],
            facts=[],
            provider=self.provider_name,
            warnings=["openai_provider_error"],
        )

    def interpret_result(self, raw_text: str) -> SemanticInterpretationResult:
        return self.interpret(raw_text)
