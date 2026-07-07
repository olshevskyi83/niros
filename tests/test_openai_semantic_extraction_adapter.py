"""Tests for OpenAI semantic extraction adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.openai_semantic_extraction_adapter import (
    OpenAISemanticExtractionAdapter,
    SemanticExtractionApiError,
    SemanticExtractionEmptyResponseError,
    SemanticExtractionInvalidJsonError,
    SemanticExtractionMissingApiKeyError,
    SemanticExtractionValidationError,
    parse_therapeutic_extraction_json,
)
from niros.raw_source import RawSource, RawSourceCorpus, RawSourceSegment, build_raw_source_corpus
from niros.semantic_extraction_prompt import build_semantic_extraction_prompt


class FakeChatCompletionClient:
    def __init__(
        self,
        response: str = "",
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, object]] = []

    def complete(self, *, model: str, messages: list[dict[str, str]]) -> str:
        self.calls.append({"model": model, "messages": messages})
        if self.error is not None:
            raise self.error
        return self.response


def _source() -> RawSource:
    return RawSource(
        source_id="source_001",
        source_family="mazatec_tradition",
        title="Chant source",
        language="mazatec",
        source_type="chant",
    )


def _segment() -> RawSourceSegment:
    return RawSourceSegment(
        segment_id="source_001_segment_001",
        source_id="source_001",
        sequence_index=1,
        raw_text="May the heart be softened and fear released.",
    )


def _corpus() -> RawSourceCorpus:
    return build_raw_source_corpus(_source(), (_segment(),))


def _valid_llm_json(**overrides) -> str:
    payload = {
        "therapeutic_function": "self_compassion",
        "psychological_function": "reduce self-criticism",
        "symbolic_elements": ["heart", "water"],
        "candidate_targets": ["shame"],
        "generation_rules": ["Use gentle tone."],
        "voice_rules": ["Slow pace."],
        "repetition_rules": ["Repeat key phrase."],
        "pause_rules": ["Pause after invocation."],
        "contraindications": ["acute crisis"],
        "confidence": 0.85,
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_successful_extraction_using_fake_openai_response() -> None:
    client = FakeChatCompletionClient(response=_valid_llm_json())
    adapter = OpenAISemanticExtractionAdapter(client=client)

    extraction = adapter.extract_segment(_source(), _segment())

    assert extraction.source_id == "source_001"
    assert extraction.segment_id == "source_001_segment_001"
    assert extraction.therapeutic_function == "self_compassion"
    assert extraction.evidence_text == "May the heart be softened and fear released."
    assert extraction.extractor == "openai"
    assert extraction.confidence == 0.85


def test_adapter_builds_semantic_extraction_prompt() -> None:
    client = FakeChatCompletionClient(response=_valid_llm_json())
    adapter = OpenAISemanticExtractionAdapter(client=client)
    source = _source()
    segment = _segment()
    expected_prompt = build_semantic_extraction_prompt(source, segment)

    adapter.extract_segment(source, segment)

    assert len(client.calls) == 1
    messages = client.calls[0]["messages"]
    assert messages == [{"role": "user", "content": expected_prompt}]
    assert segment.raw_text in messages[0]["content"]


def test_invalid_json_raises_expected_error() -> None:
    client = FakeChatCompletionClient(response="not-json")
    adapter = OpenAISemanticExtractionAdapter(client=client)

    with pytest.raises(SemanticExtractionInvalidJsonError):
        adapter.extract_segment(_source(), _segment())


def test_validation_error_raises_expected_error() -> None:
    client = FakeChatCompletionClient(
        response=_valid_llm_json(therapeutic_function="", confidence=2.0)
    )
    adapter = OpenAISemanticExtractionAdapter(client=client)

    with pytest.raises(SemanticExtractionValidationError) as exc_info:
        adapter.extract_segment(_source(), _segment())

    message = str(exc_info.value)
    assert "therapeutic_function must not be empty" in message
    assert "confidence must be between 0.0 and 1.0" in message


def test_empty_response_raises_expected_error() -> None:
    client = FakeChatCompletionClient(response="   ")
    adapter = OpenAISemanticExtractionAdapter(client=client)

    with pytest.raises(SemanticExtractionEmptyResponseError):
        adapter.extract_segment(_source(), _segment())


def test_api_failure_is_wrapped_in_adapter_level_error() -> None:
    client = FakeChatCompletionClient(error=RuntimeError("network down"))
    adapter = OpenAISemanticExtractionAdapter(client=client)

    with pytest.raises(SemanticExtractionApiError) as exc_info:
        adapter.extract_segment(_source(), _segment())

    assert exc_info.value.__cause__ is not None


def test_adapter_does_not_create_ctpc_files_or_write_into_ctpc_workspace(
    tmp_path: Path,
) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    ctpc_dir = Path(paths.ctpc_dir)
    client = FakeChatCompletionClient(response=_valid_llm_json())
    adapter = OpenAISemanticExtractionAdapter(client=client)

    adapter.extract_from_corpus(_corpus(), "source_001_segment_001")

    assert ctpc_dir.exists()
    assert list(ctpc_dir.rglob("*.json")) == []


def test_extract_from_corpus_uses_source_and_segment() -> None:
    client = FakeChatCompletionClient(response=_valid_llm_json())
    adapter = OpenAISemanticExtractionAdapter(client=client)

    extraction = adapter.extract_from_corpus(_corpus(), "source_001_segment_001")

    assert extraction.segment_id == "source_001_segment_001"
    assert extraction.source_id == "source_001"


def test_missing_api_key_when_real_client_is_used(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(SemanticExtractionMissingApiKeyError):
        OpenAISemanticExtractionAdapter()


def test_parse_therapeutic_extraction_json_strips_markdown_fence() -> None:
    payload = _valid_llm_json()
    raw = f"```json\n{payload}\n```"
    extraction = parse_therapeutic_extraction_json(
        raw,
        source_id="source_001",
        segment_id="source_001_segment_001",
        evidence_text="Evidence line.",
    )
    assert extraction.therapeutic_function == "self_compassion"
