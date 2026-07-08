"""OpenAI Semantic Extraction Adapter — LLM-backed therapeutic extraction for raw segments."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from niros.raw_source import RawSource, RawSourceCorpus, RawSourceSegment
from niros.semantic_extraction_prompt import build_semantic_extraction_prompt
from niros.semantic_knowledge_extraction import (
    enrich_extraction_with_ontology,
    validate_semantic_knowledge_extraction,
)
from niros.semantic_therapeutic_gate import (
    KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
    TherapeuticRelevanceDecision,
    parse_relevance_decision_json,
)
from niros.ontology_context import OntologyContext, load_ontology_context
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


class SemanticExtractionSkippedError(SemanticExtractionAdapterError):
    """Raised when the relevance gate decides not to extract from one segment."""

    def __init__(self, decision: TherapeuticRelevanceDecision) -> None:
        self.decision = decision
        super().__init__(decision.reasoning or decision.skip_reason or "Chunk skipped by relevance gate.")


@dataclass(frozen=True)
class SemanticExtractionResult:
    relevance_decision: TherapeuticRelevanceDecision
    extraction: TherapeuticFunctionExtraction | None


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


def _parse_extraction_payload(
    data: dict[str, Any],
    *,
    source_id: str,
    segment_id: str,
    evidence_text: str,
    ontology_context: OntologyContext | None = None,
) -> TherapeuticFunctionExtraction:
    mechanism_name = str(data.get("mechanism_name", "")).strip()
    mechanism_description = str(data.get("mechanism_description", "")).strip()
    why_this_is_a_mechanism = str(data.get("why_this_is_a_mechanism", "")).strip()
    causal_process = str(data.get("causal_process", "")).strip()
    ontology_status = str(data.get("ontology_status", "")).strip()
    llm_evidence = str(data.get("evidence", "")).strip()
    therapeutic_function = str(data.get("therapeutic_function", "")).strip() or mechanism_name
    psychological_function = (
        str(data.get("psychological_function", "")).strip() or mechanism_description
    )
    resolved_evidence = llm_evidence or evidence_text.strip()

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
        evidence_text=resolved_evidence,
        mechanism_name=mechanism_name,
        mechanism_description=mechanism_description,
        why_this_is_a_mechanism=why_this_is_a_mechanism,
        causal_process=causal_process,
        ontology_status=ontology_status,
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

    issues = list(validate_extraction(extraction))
    enriched = enrich_extraction_with_ontology(
        extraction,
        context=ontology_context or load_ontology_context(),
    )

    require_semantic = bool(
        mechanism_name or causal_process or why_this_is_a_mechanism or ontology_status
    )
    if require_semantic:
        issues.extend(validate_semantic_knowledge_extraction(enriched))
    if issues:
        joined = "; ".join(issues)
        raise SemanticExtractionValidationError(
            f"OpenAI extraction JSON failed validation: {joined}"
        )

    return enriched


def _legacy_relevance_decision(
    *,
    source_id: str,
    segment_id: str,
    evidence_text: str,
) -> TherapeuticRelevanceDecision:
    return TherapeuticRelevanceDecision(
        chunk_id=segment_id,
        source_id=source_id,
        is_relevant=True,
        relevance_score=1.0,
        knowledge_kind=KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
        reasoning="Legacy extraction response without explicit relevance decision.",
        evidence_span=evidence_text.strip()[:240],
        skip_reason="",
        suggested_mechanisms=(),
        should_extract=True,
    )


def parse_semantic_extraction_response_json(
    raw_text: str,
    *,
    source_id: str,
    segment_id: str,
    evidence_text: str,
    ontology_context: OntologyContext | None = None,
) -> SemanticExtractionResult:
    """Parse LLM JSON output into a relevance decision and optional extraction."""
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

    if "relevance_decision" in data:
        relevance_payload = data.get("relevance_decision")
        if not isinstance(relevance_payload, dict):
            raise SemanticExtractionInvalidJsonError(
                "relevance_decision must be an object."
            )
        decision = parse_relevance_decision_json(
            relevance_payload,
            source_id=source_id,
            chunk_id=segment_id,
            fallback_text=evidence_text,
        )
        extraction_payload = data.get("extraction")
        if not decision.should_extract:
            if extraction_payload is not None:
                raise SemanticExtractionValidationError(
                    "extraction must be null when should_extract is false."
                )
            return SemanticExtractionResult(relevance_decision=decision, extraction=None)

        if not isinstance(extraction_payload, dict):
            raise SemanticExtractionInvalidJsonError(
                "extraction must be an object when should_extract is true."
            )
        extraction = _parse_extraction_payload(
            extraction_payload,
            source_id=source_id,
            segment_id=segment_id,
            evidence_text=evidence_text,
            ontology_context=ontology_context,
        )
        return SemanticExtractionResult(relevance_decision=decision, extraction=extraction)

    decision = _legacy_relevance_decision(
        source_id=source_id,
        segment_id=segment_id,
        evidence_text=evidence_text,
    )
    extraction = _parse_extraction_payload(
        data,
        source_id=source_id,
        segment_id=segment_id,
        evidence_text=evidence_text,
        ontology_context=ontology_context,
    )
    return SemanticExtractionResult(relevance_decision=decision, extraction=extraction)


def parse_therapeutic_extraction_json(
    raw_text: str,
    *,
    source_id: str,
    segment_id: str,
    evidence_text: str,
    ontology_context: OntologyContext | None = None,
) -> TherapeuticFunctionExtraction:
    """Parse LLM JSON output into a TherapeuticFunctionExtraction."""
    result = parse_semantic_extraction_response_json(
        raw_text,
        source_id=source_id,
        segment_id=segment_id,
        evidence_text=evidence_text,
        ontology_context=ontology_context,
    )
    if result.extraction is None:
        raise SemanticExtractionSkippedError(result.relevance_decision)
    return result.extraction


class OpenAISemanticExtractionAdapter:
    """Extract therapeutic mechanisms from raw source segments via OpenAI."""

    def __init__(
        self,
        *,
        client: ChatCompletionClient | None = None,
        model: str | None = None,
        api_key: str | None = None,
        ontology_context: OntologyContext | None = None,
    ) -> None:
        self.model = resolve_openai_model(model)
        self._ontology_context = ontology_context or load_ontology_context()
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
        return build_semantic_extraction_prompt(
            raw_source,
            raw_segment,
            ontology_context=self._ontology_context,
        )

    def extract_from_prompt(
        self,
        prompt: str,
        raw_source: RawSource,
        raw_segment: RawSourceSegment,
    ) -> SemanticExtractionResult:
        """Call OpenAI with a prepared prompt and return a gated extraction result."""
        messages = [{"role": "user", "content": prompt}]
        try:
            raw_output = self._client.complete(model=self.model, messages=messages)
        except SemanticExtractionAdapterError:
            raise
        except Exception as exc:
            raise SemanticExtractionApiError("OpenAI API call failed.") from exc

        return parse_semantic_extraction_response_json(
            raw_output,
            source_id=raw_source.source_id,
            segment_id=raw_segment.segment_id,
            evidence_text=raw_segment.raw_text,
            ontology_context=self._ontology_context,
        )

    def extract_segment(
        self,
        raw_source: RawSource,
        raw_segment: RawSourceSegment,
    ) -> SemanticExtractionResult:
        """Build a prompt and extract therapeutic mechanisms for one segment."""
        prompt = self.build_prompt(raw_source, raw_segment)
        return self.extract_from_prompt(prompt, raw_source, raw_segment)

    def extract_from_corpus_gated(
        self,
        corpus: RawSourceCorpus,
        segment_id: str,
    ) -> SemanticExtractionResult:
        """Extract with relevance decision for one segment within a raw source corpus."""
        for segment in corpus.segments:
            if segment.segment_id == segment_id:
                return self.extract_segment(corpus.source, segment)
        raise ValueError(f"Segment not found in corpus: {segment_id}")

    def extract_from_corpus(
        self,
        corpus: RawSourceCorpus,
        segment_id: str,
    ) -> TherapeuticFunctionExtraction:
        """Extract therapeutic mechanisms for one segment within a raw source corpus."""
        result = self.extract_from_corpus_gated(corpus, segment_id)
        if result.extraction is None:
            raise SemanticExtractionSkippedError(result.relevance_decision)
        return result.extraction
