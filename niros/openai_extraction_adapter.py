"""OpenAI Therapeutic Extraction Adapter — contract-only LLM extraction boundary."""

from __future__ import annotations

from dataclasses import dataclass

from niros.raw_source import RawSource, RawSourceSegment
from niros.therapeutic_extraction import TherapeuticFunctionExtraction

DEFAULT_EXTRACTION_PROMPT_VERSION = "v1"
DEFAULT_ADAPTER_VERSION = "contract_v1"


@dataclass(frozen=True)
class ExtractionRequest:
    source_id: str
    segment_id: str
    raw_text: str
    language: str
    source_family: str
    extraction_prompt_version: str = DEFAULT_EXTRACTION_PROMPT_VERSION


@dataclass(frozen=True)
class ExtractionResponse:
    request: ExtractionRequest
    extraction: TherapeuticFunctionExtraction
    raw_llm_output: str = ""
    adapter_version: str = DEFAULT_ADAPTER_VERSION


def build_extraction_request(
    raw_source_segment: RawSourceSegment,
    raw_source: RawSource,
) -> ExtractionRequest:
    """Map a raw source segment and parent source into an extraction request."""
    return ExtractionRequest(
        source_id=raw_source.source_id,
        segment_id=raw_source_segment.segment_id,
        raw_text=raw_source_segment.raw_text,
        language=raw_source.language,
        source_family=raw_source.source_family,
    )


def build_extraction_response(
    request: ExtractionRequest,
    extraction: TherapeuticFunctionExtraction,
) -> ExtractionResponse:
    """Build a deterministic extraction response envelope."""
    return ExtractionResponse(
        request=request,
        extraction=extraction,
    )


def validate_extraction_response(response: ExtractionResponse) -> tuple[str, ...]:
    """Return validation issue strings for one extraction response."""
    issues: list[str] = []

    if response.request is None:
        issues.append("request must exist")
    if response.extraction is None:
        issues.append("extraction must exist")

    if response.request is not None and response.extraction is not None:
        if response.extraction.source_id != response.request.source_id:
            issues.append("extraction source_id must match request source_id")
        if response.extraction.segment_id != response.request.segment_id:
            issues.append("extraction segment_id must match request segment_id")

    return tuple(issues)
