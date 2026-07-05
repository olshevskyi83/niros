"""Tests for OpenAI-assisted Meaning Unit extraction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from niros_tle.chunk_builder import KnowledgeChunk
from niros_tle.meaning_unit_extractor import (
    MeaningUnitExtractor,
    generate_meaning_unit_id,
)


@dataclass
class _MockLLMClient:
    response: str

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        return self.response


def _chunk(**overrides: object) -> KnowledgeChunk:
    payload = {
        "chunk_id": "act_sample_txt_0001",
        "document_id": "act_sample_txt",
        "source_family": "act",
        "language": "en",
        "chunk_type": "paragraph",
        "title": "Sample Chunk",
        "text": (
            "You do not need to fight every thought that arrives. "
            "Notice it, allow it, and choose what matters next."
        ),
        "page_start": 3,
        "page_end": 3,
        "section_path": ("Chapter 1",),
        "sequence_number": 1,
        "metadata": {"source_document": "act_sample_txt"},
    }
    payload.update(overrides)
    return KnowledgeChunk(**payload)


def _response_payload(units: list[dict]) -> str:
    return json.dumps({"meaning_units": units})


def test_multiple_meaning_units():
    chunk = _chunk()
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Invite acceptance of passing thoughts without struggle.",
                    "original_span": {"start_char": 0, "end_char": 44},
                    "psychological_functions": ["acceptance", "defusion"],
                    "language_patterns": ["permission_based", "reframing"],
                    "confidence": "high",
                },
                {
                    "summary": "Encourage values-linked choice after noticing thoughts.",
                    "original_span": {"start_char": 45, "end_char": 95},
                    "psychological_functions": ["values_clarification", "agency_restoration"],
                    "language_patterns": ["future_orientation", "choice_language"],
                    "confidence": "medium",
                },
            ]
        )
    )
    units = MeaningUnitExtractor(client=client).extract(chunk)
    assert len(units) == 2
    assert units[0].meaning_unit_id == "act_sample_txt_0001_mu_001"
    assert units[1].meaning_unit_id == "act_sample_txt_0001_mu_002"


def test_single_meaning_unit():
    chunk = _chunk()
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Offer permission to allow thoughts without fighting them.",
                    "original_span": {"start_char": 0, "end_char": 44},
                    "psychological_functions": ["permission"],
                    "language_patterns": ["permission_based"],
                    "confidence": "high",
                }
            ]
        )
    )
    units = MeaningUnitExtractor(client=client).extract(chunk)
    assert len(units) == 1


def test_empty_chunk():
    chunk = _chunk(text="   ")
    client = _MockLLMClient(response=_response_payload([]))
    units = MeaningUnitExtractor(client=client).extract(chunk)
    assert units == ()


def test_deterministic_ids():
    chunk = _chunk()
    assert generate_meaning_unit_id(chunk.chunk_id, 1) == "act_sample_txt_0001_mu_001"
    assert generate_meaning_unit_id(chunk.chunk_id, 2) == "act_sample_txt_0001_mu_002"


def test_confidence_preserved():
    chunk = _chunk()
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Use a safety cue before exploring difficult material.",
                    "original_span": {"start_char": 0, "end_char": 20},
                    "psychological_functions": ["safety_cue"],
                    "language_patterns": ["grounding_language"],
                    "confidence": "low",
                }
            ]
        )
    )
    units = MeaningUnitExtractor(client=client).extract(chunk)
    assert units[0].confidence == "low"


def test_psychological_functions_present():
    chunk = _chunk()
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Support compassionate self-relating in difficult moments.",
                    "original_span": {"start_char": 0, "end_char": 20},
                    "psychological_functions": ["compassion_invitation"],
                    "language_patterns": ["gentle_framing"],
                    "confidence": "medium",
                }
            ]
        )
    )
    units = MeaningUnitExtractor(client=client).extract(chunk)
    assert units[0].psychological_functions == ("compassion_invitation",)


def test_language_mechanisms_present():
    chunk = _chunk()
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Reframe the struggle with thoughts as optional.",
                    "original_span": {"start_char": 0, "end_char": 20},
                    "psychological_functions": ["perspective_shift"],
                    "language_patterns": ["narrative_reframing", "permission_based"],
                    "confidence": "medium",
                }
            ]
        )
    )
    units = MeaningUnitExtractor(client=client).extract(chunk)
    assert units[0].language_patterns == ("narrative_reframing", "permission_based")


def test_original_span_references_preserved():
    chunk = _chunk()
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Highlight future-oriented choice after noticing thoughts.",
                    "original_span": {"start_char": 45, "end_char": 95},
                    "psychological_functions": ["future_orientation"],
                    "language_patterns": ["future_orientation"],
                    "confidence": "medium",
                }
            ]
        )
    )
    units = MeaningUnitExtractor(client=client).extract(chunk)
    assert units[0].original_span == {"start_char": 45, "end_char": 95}


def test_no_copyrighted_text_copied():
    chunk = _chunk()
    copied_summary = chunk.text[:60]
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": copied_summary,
                    "original_span": {"start_char": 0, "end_char": 44},
                    "psychological_functions": ["acceptance"],
                    "language_patterns": ["permission_based"],
                    "confidence": "medium",
                }
            ]
        )
    )
    with pytest.raises(ValueError, match="copy source text"):
        MeaningUnitExtractor(client=client).extract(chunk)

    valid_client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Invite allowing thoughts without immediate struggle.",
                    "original_span": {"start_char": 0, "end_char": 44},
                    "psychological_functions": ["acceptance"],
                    "language_patterns": ["permission_based"],
                    "confidence": "medium",
                }
            ]
        )
    )
    units = MeaningUnitExtractor(client=valid_client).extract(chunk)
    serialized = json.dumps(units[0].to_dict())
    assert chunk.text not in serialized


def test_output_written_to_processed_meaning_units(tmp_path: Path):
    chunk = _chunk()
    client = _MockLLMClient(
        response=_response_payload(
            [
                {
                    "summary": "Offer permission to allow thoughts without fighting them.",
                    "original_span": {"start_char": 0, "end_char": 44},
                    "psychological_functions": ["permission"],
                    "language_patterns": ["permission_based"],
                    "confidence": "high",
                }
            ]
        )
    )
    extractor = MeaningUnitExtractor(client=client, repo_root=tmp_path)
    units = extractor.extract_and_save(chunk)
    output_path = (
        tmp_path
        / "niros_tle"
        / "corpus"
        / "act"
        / "processed"
        / "meaning_units"
        / f"{chunk.chunk_id}.meaning_units.json"
    )
    assert output_path.is_file()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["meaning_unit_count"] == len(units)


def test_no_niros_core_meaning_unit_integration():
    repo_root = Path(__file__).resolve().parents[2]
    niros_dir = repo_root / "niros"
    matches = []
    for path in niros_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "meaning_unit_extractor" in text or "MeaningUnitExtractor" in text:
            matches.append(str(path.relative_to(repo_root)))
    assert matches == []
