"""OpenAI-assisted Meaning Unit extraction from a single Knowledge Chunk."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from niros_tle.chunk_builder import KnowledgeChunk

TLE_ROOT = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = TLE_ROOT.parent

CONFIDENCE_VALUES: tuple[str, ...] = ("low", "medium", "high")

ALLOWED_PSYCHOLOGICAL_FUNCTIONS: frozenset[str] = frozenset(
    {
        "acceptance",
        "perspective_shift",
        "identity_reconstruction",
        "compassion_invitation",
        "agency_restoration",
        "values_clarification",
        "narrative_reframing",
        "hope_induction",
        "permission",
        "safety_cue",
        "future_orientation",
        "defusion",
        "grounding",
        "curiosity",
        "grief_processing",
        "meaning_making",
    }
)

MAX_SUMMARY_CHARS = 320
MAX_ORIGINAL_SPAN_LENGTH = 240
MIN_PARAPHRASE_OVERLAP_RATIO = 0.85


class MeaningUnitExtractionError(ValueError):
    """Raised when meaning unit extraction or validation fails."""


@dataclass(frozen=True)
class MeaningUnit:
    meaning_unit_id: str
    chunk_id: str
    summary: str
    original_span: dict[str, int]
    psychological_functions: tuple[str, ...]
    language_patterns: tuple[str, ...]
    confidence: str
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meaning_unit_id": self.meaning_unit_id,
            "chunk_id": self.chunk_id,
            "summary": self.summary,
            "original_span": dict(self.original_span),
            "psychological_functions": list(self.psychological_functions),
            "language_patterns": list(self.language_patterns),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


class MeaningUnitLLMClient(Protocol):
    def complete(self, *, system_prompt: str, user_prompt: str) -> str: ...


class OpenAIMeaningUnitClient:
    """Thin OpenAI wrapper for one-chunk Meaning Unit extraction."""

    def __init__(
        self,
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.0,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        if client is not None:
            self._client = client
            return

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise MeaningUnitExtractionError(
                "OpenAI package is not installed."
            ) from exc

        self._client = OpenAI(api_key=api_key) if api_key else OpenAI()

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""


@dataclass(frozen=True)
class MeaningUnitExtractor:
    model: str = "gpt-4.1-mini"
    temperature: float = 0.0
    client: MeaningUnitLLMClient | None = None
    repo_root: Path = field(default_factory=lambda: DEFAULT_REPO_ROOT)

    def extract(self, chunk: KnowledgeChunk) -> tuple[MeaningUnit, ...]:
        if not chunk.text.strip():
            return ()

        if self.client is None:
            raise MeaningUnitExtractionError(
                "OpenAI client unavailable. Provide a client to extract meaning units."
            )

        raw_response = self.client.complete(
            system_prompt=build_meaning_unit_system_prompt(),
            user_prompt=build_meaning_unit_user_prompt(chunk),
        )
        payloads = parse_meaning_unit_response(raw_response)
        return tuple(
            _payload_to_meaning_unit(chunk, payload, index)
            for index, payload in enumerate(payloads, start=1)
        )

    def save_meaning_units(
        self,
        chunk: KnowledgeChunk,
        meaning_units: tuple[MeaningUnit, ...],
    ) -> Path:
        output_path = meaning_units_output_path(chunk, repo_root=self.repo_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "source_family": chunk.source_family,
            "meaning_unit_count": len(meaning_units),
            "meaning_units": [unit.to_dict() for unit in meaning_units],
        }
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return output_path

    def extract_and_save(self, chunk: KnowledgeChunk) -> tuple[MeaningUnit, ...]:
        meaning_units = self.extract(chunk)
        self.save_meaning_units(chunk, meaning_units)
        return meaning_units


def build_meaning_unit_system_prompt() -> str:
    functions = ", ".join(sorted(ALLOWED_PSYCHOLOGICAL_FUNCTIONS))
    return f"""You identify minimal self-contained therapeutic Meaning Units in ONE source chunk.

You are not a psychologist.
You do not diagnose.
You do not summarize the whole document.
You do not create therapeutic patterns.
You work on exactly one chunk.

Rules:
- Output valid JSON only.
- Identify 1-5 Meaning Units when present.
- Each summary must be a short paraphrase in your own words.
- Never copy long phrases from the source chunk.
- original_span must contain only start_char and end_char integer offsets into the chunk text.
- Do not include source text in the JSON.
- psychological_functions must use only this vocabulary when possible: {functions}
- language_patterns must name language mechanisms such as permission_based, metaphor, reframing, future_orientation, safety_cue.
- confidence must be one of: low, medium, high.
- No markdown. No extra keys.

JSON shape:
{{
  "meaning_units": [
    {{
      "summary": "...",
      "original_span": {{"start_char": 0, "end_char": 42}},
      "psychological_functions": ["acceptance"],
      "language_patterns": ["permission_based"],
      "confidence": "medium"
    }}
  ]
}}"""


def build_meaning_unit_user_prompt(chunk: KnowledgeChunk) -> str:
    return (
        f"Extract Meaning Units from this single chunk.\n"
        f"chunk_id: {chunk.chunk_id}\n"
        f"chunk_type: {chunk.chunk_type}\n"
        f"source_family: {chunk.source_family}\n"
        f"language: {chunk.language}\n"
        f"section_path: {' > '.join(chunk.section_path) if chunk.section_path else '(none)'}\n"
        f"chunk_text:\n{chunk.text}"
    )


def parse_meaning_unit_response(raw_text: str) -> list[dict[str, Any]]:
    payload = _load_json_object(raw_text)
    units = payload.get("meaning_units")
    if not isinstance(units, list):
        raise MeaningUnitExtractionError("Response must contain a meaning_units list.")
    return [item for item in units if isinstance(item, dict)]


def meaning_units_output_path(
    chunk: KnowledgeChunk,
    *,
    repo_root: Path,
) -> Path:
    return (
        repo_root
        / "niros_tle"
        / "corpus"
        / chunk.source_family
        / "processed"
        / "meaning_units"
        / f"{chunk.chunk_id}.meaning_units.json"
    )


def generate_meaning_unit_id(chunk_id: str, index: int) -> str:
    return f"{chunk_id}_mu_{index:03d}"


def _payload_to_meaning_unit(
    chunk: KnowledgeChunk,
    payload: dict[str, Any],
    index: int,
) -> MeaningUnit:
    summary = str(payload.get("summary", "")).strip()
    if not summary:
        raise MeaningUnitExtractionError("Meaning unit summary must not be empty.")
    if len(summary) > MAX_SUMMARY_CHARS:
        raise MeaningUnitExtractionError("Meaning unit summary exceeds maximum length.")

    _validate_summary_is_paraphrase(summary, chunk.text)

    original_span = _normalize_original_span(payload.get("original_span"), chunk.text)
    psychological_functions = _normalize_string_list(payload.get("psychological_functions"))
    language_patterns = _normalize_string_list(payload.get("language_patterns"))
    if not psychological_functions:
        raise MeaningUnitExtractionError("psychological_functions must not be empty.")
    if not language_patterns:
        raise MeaningUnitExtractionError("language_patterns must not be empty.")

    confidence = str(payload.get("confidence", "")).strip().lower()
    if confidence not in CONFIDENCE_VALUES:
        raise MeaningUnitExtractionError(f"Invalid confidence '{confidence}'.")

    return MeaningUnit(
        meaning_unit_id=generate_meaning_unit_id(chunk.chunk_id, index),
        chunk_id=chunk.chunk_id,
        summary=summary,
        original_span=original_span,
        psychological_functions=psychological_functions,
        language_patterns=language_patterns,
        confidence=confidence,
        metadata={
            "source_document": chunk.document_id,
            "source_family": chunk.source_family,
            "chunk_type": chunk.chunk_type,
            "section_hierarchy": " > ".join(chunk.section_path) if chunk.section_path else "",
            "page_start": "" if chunk.page_start is None else str(chunk.page_start),
            "page_end": "" if chunk.page_end is None else str(chunk.page_end),
        },
    )


def _normalize_original_span(value: Any, chunk_text: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise MeaningUnitExtractionError("original_span must be a mapping with start_char and end_char.")
    try:
        start_char = int(value["start_char"])
        end_char = int(value["end_char"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MeaningUnitExtractionError(
            "original_span must include integer start_char and end_char."
        ) from exc

    text_length = len(chunk_text)
    if start_char < 0 or end_char < start_char or end_char > text_length:
        raise MeaningUnitExtractionError("original_span offsets are out of range.")
    if end_char - start_char > MAX_ORIGINAL_SPAN_LENGTH:
        raise MeaningUnitExtractionError("original_span range exceeds maximum allowed length.")
    return {"start_char": start_char, "end_char": end_char}


def _normalize_string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MeaningUnitExtractionError("Expected a list of strings.")
    normalized = tuple(
        _slug_token(str(item))
        for item in value
        if str(item).strip()
    )
    return normalized


def _slug_token(value: str) -> str:
    return re.sub(r"\s+", "_", value.strip().lower())


def _validate_summary_is_paraphrase(summary: str, chunk_text: str) -> None:
    normalized_summary = _normalize_for_compare(summary)
    normalized_chunk = _normalize_for_compare(chunk_text)
    if not normalized_summary:
        raise MeaningUnitExtractionError("Meaning unit summary must not be empty.")

    if normalized_summary == normalized_chunk:
        raise MeaningUnitExtractionError("Summary must not copy the full chunk text.")

    if normalized_summary in normalized_chunk and len(normalized_summary) >= 40:
        raise MeaningUnitExtractionError("Summary appears to copy source text verbatim.")

    overlap = _longest_shared_substring_length(normalized_summary, normalized_chunk)
    if len(normalized_summary) >= 40 and overlap / len(normalized_summary) >= MIN_PARAPHRASE_OVERLAP_RATIO:
        raise MeaningUnitExtractionError("Summary appears to copy source text verbatim.")


def _normalize_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _longest_shared_substring_length(left: str, right: str) -> int:
    if not left or not right:
        return 0
    best = 0
    for start in range(len(left)):
        for end in range(start + 1, len(left) + 1):
            fragment = left[start:end]
            if len(fragment) <= best:
                continue
            if fragment in right:
                best = len(fragment)
    return best


def _load_json_object(raw_text: str) -> dict[str, Any]:
    stripped = raw_text.strip()
    if not stripped:
        raise MeaningUnitExtractionError("Empty model response.")
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise MeaningUnitExtractionError("Model response must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise MeaningUnitExtractionError("Model response must be a JSON object.")
    return payload
