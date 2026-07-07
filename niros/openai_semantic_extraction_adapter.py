"""OpenAI Semantic Extraction Adapter — LLM-backed therapeutic extraction for raw segments."""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from niros.raw_source import RawSource, RawSourceCorpus, RawSourceSegment
from niros.semantic_extraction_prompt import build_semantic_extraction_prompt
from niros.therapeutic_extraction import (
    TherapeuticFunctionExtraction,
    build_extraction_id,
    validate_extraction,
)

DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"
OPENAI_MODEL_ENV_VAR = "OPENAI_MODEL"
DEFAULT_EXTRACTOR_NAME = "openai"


class SemanticExtractionAdapterError(Exception):
    """Base error for OpenAI semantic extraction adapter failures."""


class SemanticExtractionMissingApiKeyError(SemanticExtractionAdapterError):
    """Raised when a real OpenAI client is requested without an API key."""


class SemanticExtractionApiError(SemanticExtractionAdapterError):
    """Raised when the OpenAI API call fails."""


class SemanticExtractionEmptyResponseError(SemanticExtractionAdapterError):
    """Raised when OpenAI returns an empty response."""


class SemanticExtractionInvalidJsonError(SemanticExtractionAdapterError):
    """Raised when OpenAI response is not valid JSON."""


class SemanticExtractionValidationError(SemanticExtractionAdapterError):
    """Raised when parsed JSON does not validate as TherapeuticFunctionExtraction."""


class ChatCompletionClient(Protocol):
    """Minimal injectable client boundary for chat completion calls."""

    def complete(self, *, model: str, messages: list[dict[str, str]]) -> str:
        """Return the assistant message content for one chat completion request."""


class OpenAIChatCompletionClient:
    """Runtime OpenAI chat completion client."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_OPENAI_MODEL,
        temperature: float = 0.0,
        client: Any | None = None,
    ) -> None:
        if client is not None:
            self._client = client
        elif OpenAI is not None:
            self._client = OpenAI(api_key=api_key)
        else:
            raise SemanticExtractionMissingApiKeyError(
                "OpenAI package is not installed; inject a fake client for tests."
            )
        self.model = model
        self.temperature = temperature

    def complete(self, *, model: str, messages: list[dict[str, str]]) -> str:
        response = self._client.chat.completions.create(
            model=model,
            temperature=self.temperature,
            messages=messages,
        )
        return response.choices[0].message.content or ""


def resolve_openai_model(model: str | None = None) -> str:
    """Resolve the OpenAI model from argument or environment."""
    if model is not None and model.strip():
        return model.strip()
    env_model = os.getenv(OPENAI_MODEL_ENV_VAR, "").strip()
    if env_model:
        return env_model
    return DEFAULT_OPENAI_MODEL


def _strip_json_fence(raw_text: str) -> str:
    stripped = raw_text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def parse_therapeutic_extraction_json(
    raw_text: str,
    *,
    source_id: str,
    segment_id: str,
    evidence_text: str,
) -> TherapeuticFunctionExtraction:
    """Parse LLM JSON output into a TherapeuticFunctionExtraction."""
    cleaned = _strip_json_fence(raw_text)
    if not cleaned.strip():
        raise SemanticExtractionEmptyResponseError("OpenAI returned an empty response.")

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise SemanticExtractionInvalidJsonError(
            "OpenAI response is not valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise SemanticExtractionInvalidJsonError(
            "OpenAI response JSON must be an object."
        )

    therapeutic_function = str(data.get("therapeutic_function", "")).strip()
    psychological_function = str(data.get("psychological_function", "")).strip()
    extraction = TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id(
            source_id,
            segment_id,
            therapeutic_function,
            psychological_function,
        ),
        source_id=source_id,
        segment_id=segment_id,
        therapeutic_function=therapeutic_function,
        psychological_function=psychological_function,
        evidence_text=evidence_text.strip(),
        symbolic_elements=_as_string_tuple(data.get("symbolic_elements")),
        candidate_targets=_as_string_tuple(data.get("candidate_targets")),
        generation_rules=_as_string_tuple(data.get("generation_rules")),
        voice_rules=_as_string_tuple(data.get("voice_rules")),
        repetition_rules=_as_string_tuple(data.get("repetition_rules")),
        pause_rules=_as_string_tuple(data.get("pause_rules")),
        contraindications=_as_string_tuple(data.get("contraindications")),
        confidence=float(data.get("confidence", 0.0)),
        extractor=DEFAULT_EXTRACTOR_NAME,
    )

    issues = validate_extraction(extraction)
    if issues:
        joined = "; ".join(issues)
        raise SemanticExtractionValidationError(
            f"OpenAI extraction JSON failed validation: {joined}"
        )

    return extraction


class OpenAISemanticExtractionAdapter:
    """Extract therapeutic mechanisms from raw source segments via OpenAI."""

    def __init__(
        self,
        *,
        client: ChatCompletionClient | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = resolve_openai_model(model)
        if client is not None:
            self._client = client
            return

        resolved_api_key = api_key if api_key is not None else os.getenv(OPENAI_API_KEY_ENV_VAR)
        if not resolved_api_key:
            raise SemanticExtractionMissingApiKeyError(
                f"{OPENAI_API_KEY_ENV_VAR} is required to create a real OpenAI client."
            )
        self._client = OpenAIChatCompletionClient(
            api_key=resolved_api_key,
            model=self.model,
        )

    def build_prompt(
        self,
        raw_source: RawSource,
        raw_segment: RawSourceSegment,
    ) -> str:
        """Build the semantic extraction prompt for one segment."""
        return build_semantic_extraction_prompt(raw_source, raw_segment)

    def extract_from_prompt(
        self,
        prompt: str,
        raw_source: RawSource,
        raw_segment: RawSourceSegment,
    ) -> TherapeuticFunctionExtraction:
        """Call OpenAI with a prepared prompt and return a validated extraction."""
        messages = [{"role": "user", "content": prompt}]
        try:
            raw_output = self._client.complete(model=self.model, messages=messages)
        except SemanticExtractionAdapterError:
            raise
        except Exception as exc:
            raise SemanticExtractionApiError("OpenAI API call failed.") from exc

        return parse_therapeutic_extraction_json(
            raw_output,
            source_id=raw_source.source_id,
            segment_id=raw_segment.segment_id,
            evidence_text=raw_segment.raw_text,
        )

    def extract_segment(
        self,
        raw_source: RawSource,
        raw_segment: RawSourceSegment,
    ) -> TherapeuticFunctionExtraction:
        """Build a prompt and extract therapeutic mechanisms for one segment."""
        prompt = self.build_prompt(raw_source, raw_segment)
        return self.extract_from_prompt(prompt, raw_source, raw_segment)

    def extract_from_corpus(
        self,
        corpus: RawSourceCorpus,
        segment_id: str,
    ) -> TherapeuticFunctionExtraction:
        """Extract therapeutic mechanisms for one segment within a raw source corpus."""
        for segment in corpus.segments:
            if segment.segment_id == segment_id:
                return self.extract_segment(corpus.source, segment)
        raise ValueError(f"Segment not found in corpus: {segment_id}")
