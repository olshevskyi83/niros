"""TLE pattern import/export contract — structured metadata only, no therapeutic text."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

SOURCE_CONFIDENCE_VALUES: tuple[str, ...] = ("low", "medium", "high")

EXTRACTION_METHOD_VALUES: tuple[str, ...] = (
    "manual_seed",
    "llm_analysis_future",
    "rag_analysis_future",
)

TLE_REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "psychological_function",
    "good_for",
    "avoid_if",
    "language_style",
    "rhythm",
    "semantic_cluster",
    "spiritual_compatibility",
    "requires_symbols",
    "forbidden_symbols",
    "intensity",
    "directness",
    "repetition_level",
    "safety_notes",
    "source_family",
    "source_confidence",
    "extraction_method",
    "evidence_refs",
)

TLE_LIST_FIELDS: tuple[str, ...] = (
    "psychological_function",
    "good_for",
    "avoid_if",
    "language_style",
    "semantic_cluster",
    "spiritual_compatibility",
    "requires_symbols",
    "forbidden_symbols",
    "safety_notes",
    "source_family",
)

CORE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "delivery_formats",
    "contraindications",
    "example_use_case",
)

FORBIDDEN_CONTENT_FIELDS: frozenset[str] = frozenset(
    {
        "therapeutic_text",
        "generated_text",
        "icaro_text",
        "final_text",
        "script",
        "passage",
        "lyrics",
        "mantra",
        "mantra_text",
        "spoken_text",
        "full_text",
    }
)

EVIDENCE_REF_REQUIRED_FIELDS: tuple[str, ...] = ("source_family", "reference_type", "note")

MAX_EVIDENCE_NOTE_LENGTH = 320
MAX_COPY_PASTE_LENGTH = 500

DEFAULT_SEED_PATTERNS_PATH = (
    Path(__file__).resolve().parent / "patterns" / "seed_patterns.json"
)
DEFAULT_CORE_EXPORT_PATH = Path(__file__).resolve().parent / "exports" / "core_patterns.json"


class TLEPatternValidationError(ValueError):
    """Raised when a TLE pattern record is invalid."""


@dataclass(frozen=True)
class TLEPatternRecord:
    id: str
    name: str
    psychological_function: tuple[str, ...]
    good_for: tuple[str, ...]
    avoid_if: tuple[str, ...]
    language_style: tuple[str, ...]
    rhythm: str
    semantic_cluster: tuple[str, ...]
    spiritual_compatibility: tuple[str, ...]
    requires_symbols: tuple[str, ...]
    forbidden_symbols: tuple[str, ...]
    intensity: str
    directness: str
    repetition_level: str
    safety_notes: tuple[str, ...]
    source_family: tuple[str, ...]
    source_confidence: str
    extraction_method: str
    evidence_refs: tuple[dict[str, str], ...]
    notes: str = ""
    delivery_formats: tuple[str, ...] = field(default_factory=tuple)
    contraindications: tuple[str, ...] = field(default_factory=tuple)
    example_use_case: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TLEPatternRecord:
        validate_tle_pattern_record(payload)
        return cls(
            id=str(payload["id"]).strip(),
            name=str(payload["name"]).strip(),
            psychological_function=_required_tuple_field(payload, "psychological_function"),
            good_for=_required_tuple_field(payload, "good_for"),
            avoid_if=_required_tuple_field(payload, "avoid_if"),
            language_style=_required_tuple_field(payload, "language_style"),
            rhythm=str(payload["rhythm"]).strip(),
            semantic_cluster=_required_tuple_field(payload, "semantic_cluster"),
            spiritual_compatibility=_required_tuple_field(payload, "spiritual_compatibility"),
            requires_symbols=_required_tuple_field(payload, "requires_symbols"),
            forbidden_symbols=_required_tuple_field(payload, "forbidden_symbols"),
            intensity=str(payload["intensity"]).strip(),
            directness=str(payload["directness"]).strip(),
            repetition_level=str(payload["repetition_level"]).strip(),
            safety_notes=_required_tuple_field(payload, "safety_notes"),
            source_family=_required_tuple_field(payload, "source_family"),
            source_confidence=str(payload["source_confidence"]).strip(),
            extraction_method=str(payload["extraction_method"]).strip(),
            evidence_refs=_evidence_refs(payload.get("evidence_refs")),
            notes=str(payload.get("notes", "")).strip(),
            delivery_formats=_optional_tuple_field(payload, "delivery_formats"),
            contraindications=_optional_tuple_field(payload, "contraindications"),
            example_use_case=str(payload.get("example_use_case", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "psychological_function": list(self.psychological_function),
            "good_for": list(self.good_for),
            "avoid_if": list(self.avoid_if),
            "language_style": list(self.language_style),
            "rhythm": self.rhythm,
            "semantic_cluster": list(self.semantic_cluster),
            "spiritual_compatibility": list(self.spiritual_compatibility),
            "requires_symbols": list(self.requires_symbols),
            "forbidden_symbols": list(self.forbidden_symbols),
            "intensity": self.intensity,
            "directness": self.directness,
            "repetition_level": self.repetition_level,
            "safety_notes": list(self.safety_notes),
            "source_family": list(self.source_family),
            "source_confidence": self.source_confidence,
            "extraction_method": self.extraction_method,
            "evidence_refs": [dict(ref) for ref in self.evidence_refs],
        }
        if self.notes:
            payload["notes"] = self.notes
        if self.delivery_formats:
            payload["delivery_formats"] = list(self.delivery_formats)
        if self.contraindications:
            payload["contraindications"] = list(self.contraindications)
        if self.example_use_case:
            payload["example_use_case"] = self.example_use_case
        return payload


def validate_tle_pattern_record(record: dict[str, Any] | TLEPatternRecord) -> None:
    """Validate a TLE pattern payload or record."""
    payload = record.to_dict() if isinstance(record, TLEPatternRecord) else record
    if not isinstance(payload, dict):
        raise TLEPatternValidationError("TLE pattern record must be a mapping.")

    _reject_forbidden_content_fields(payload)
    _validate_required_fields(payload)
    _validate_list_fields(payload)
    _validate_evidence_refs(payload.get("evidence_refs"))
    _reject_long_copied_text(payload)


def to_core_therapeutic_pattern(record: TLEPatternRecord | dict[str, Any]) -> dict[str, Any]:
    """Convert a TLE record into a NIROS Core TherapeuticPattern-compatible dict."""
    if isinstance(record, dict):
        record = TLEPatternRecord.from_dict(record)

    core: dict[str, Any] = {
        "id": record.id,
        "name": record.name,
        "psychological_function": list(record.psychological_function),
        "good_for": list(record.good_for),
        "avoid_if": list(record.avoid_if),
        "language_style": list(record.language_style),
        "rhythm": record.rhythm,
        "semantic_cluster": list(record.semantic_cluster),
        "spiritual_compatibility": list(record.spiritual_compatibility),
        "requires_symbols": list(record.requires_symbols),
        "forbidden_symbols": list(record.forbidden_symbols),
        "intensity": record.intensity,
        "directness": record.directness,
        "repetition_level": record.repetition_level,
        "safety_notes": list(record.safety_notes),
    }
    if record.source_family:
        core["source_family"] = list(record.source_family)
    if record.delivery_formats:
        core["delivery_formats"] = list(record.delivery_formats)
    if record.contraindications:
        core["contraindications"] = list(record.contraindications)
    if record.example_use_case:
        core["example_use_case"] = record.example_use_case
    return core


def load_tle_patterns(path: Path | str) -> tuple[TLEPatternRecord, ...]:
    """Load and validate TLE patterns from a JSON list file."""
    pattern_path = Path(path)
    payloads = json.loads(pattern_path.read_text(encoding="utf-8"))
    if not isinstance(payloads, list):
        raise TLEPatternValidationError("TLE pattern library must be a JSON list.")

    records = tuple(TLEPatternRecord.from_dict(payload) for payload in payloads)
    _validate_unique_ids(records)
    return records


def export_core_patterns(
    records: Iterable[TLEPatternRecord],
    output_path: Path | str,
    *,
    validate_with_core_schema: bool = True,
) -> list[dict[str, Any]]:
    """Export TLE records as Core-compatible pattern dicts (deterministic order by id)."""
    record_list = sorted(records, key=lambda item: item.id)
    _validate_unique_ids(record_list)

    core_patterns = [to_core_therapeutic_pattern(record) for record in record_list]
    if validate_with_core_schema:
        _validate_core_patterns(core_patterns)

    export_path = Path(output_path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(core_patterns, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return core_patterns


def _validate_core_patterns(patterns: list[dict[str, Any]]) -> None:
    try:
        from niros.therapeutic_pattern import TherapeuticPatternLibrary
    except ImportError as exc:
        raise TLEPatternValidationError(
            "NIROS Core TherapeuticPattern schema unavailable for export validation."
        ) from exc

    TherapeuticPatternLibrary.from_dicts(patterns)


def _validate_required_fields(payload: dict[str, Any]) -> None:
    missing = [field_name for field_name in TLE_REQUIRED_FIELDS if field_name not in payload]
    if missing:
        raise TLEPatternValidationError(
            f"Missing required TLE pattern fields: {', '.join(missing)}"
        )

    if not str(payload["id"]).strip():
        raise TLEPatternValidationError("Field 'id' must not be empty.")

    for field_name in ("name", "rhythm", "intensity", "directness", "repetition_level"):
        if not str(payload[field_name]).strip():
            raise TLEPatternValidationError(f"Field '{field_name}' must not be empty.")

    confidence = str(payload["source_confidence"]).strip()
    if confidence not in SOURCE_CONFIDENCE_VALUES:
        raise TLEPatternValidationError(
            f"Invalid source_confidence '{confidence}'. "
            f"Expected one of: {', '.join(SOURCE_CONFIDENCE_VALUES)}"
        )

    method = str(payload["extraction_method"]).strip()
    if method not in EXTRACTION_METHOD_VALUES:
        raise TLEPatternValidationError(
            f"Invalid extraction_method '{method}'. "
            f"Expected one of: {', '.join(EXTRACTION_METHOD_VALUES)}"
        )


def _validate_list_fields(payload: dict[str, Any]) -> None:
    for field_name in TLE_LIST_FIELDS:
        if field_name not in payload:
            raise TLEPatternValidationError(f"Missing required TLE pattern fields: {field_name}")
        value = payload[field_name]
        if value is None:
            raise TLEPatternValidationError(f"Field '{field_name}' must be a list.")
        if not isinstance(value, list):
            raise TLEPatternValidationError(f"Field '{field_name}' must be a list.")

    for field_name in (
        "psychological_function",
        "good_for",
        "language_style",
        "semantic_cluster",
        "spiritual_compatibility",
        "safety_notes",
        "source_family",
    ):
        if not _required_tuple_field(payload, field_name):
            raise TLEPatternValidationError(f"Field '{field_name}' must not be empty.")

    for field_name in ("delivery_formats", "contraindications"):
        if field_name in payload:
            _optional_tuple_field(payload, field_name)


def _validate_evidence_refs(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise TLEPatternValidationError("Field 'evidence_refs' must be a non-empty list.")

    for index, ref in enumerate(value):
        if not isinstance(ref, dict):
            raise TLEPatternValidationError(f"evidence_refs[{index}] must be a mapping.")

        missing = [field_name for field_name in EVIDENCE_REF_REQUIRED_FIELDS if field_name not in ref]
        if missing:
            raise TLEPatternValidationError(
                f"evidence_refs[{index}] missing fields: {', '.join(missing)}"
            )

        for field_name in EVIDENCE_REF_REQUIRED_FIELDS:
            text = str(ref[field_name]).strip()
            if not text:
                raise TLEPatternValidationError(
                    f"evidence_refs[{index}].{field_name} must not be empty."
                )
            if len(text) > MAX_EVIDENCE_NOTE_LENGTH:
                raise TLEPatternValidationError(
                    f"evidence_refs[{index}].{field_name} exceeds maximum length "
                    f"({MAX_EVIDENCE_NOTE_LENGTH})."
                )


def _reject_forbidden_content_fields(payload: dict[str, Any]) -> None:
    present = sorted(field_name for field_name in FORBIDDEN_CONTENT_FIELDS if field_name in payload)
    if present:
        raise TLEPatternValidationError(
            f"Forbidden therapeutic text fields present: {', '.join(present)}"
        )


def _reject_long_copied_text(payload: dict[str, Any]) -> None:
    for path, text in _iter_string_fields(payload):
        if len(text) > MAX_COPY_PASTE_LENGTH:
            raise TLEPatternValidationError(
                f"Field '{path}' exceeds maximum allowed length ({MAX_COPY_PASTE_LENGTH}); "
                "copied passages or generated therapeutic text are not allowed."
            )


def _validate_unique_ids(records: Iterable[TLEPatternRecord]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for record in records:
        if record.id in seen:
            duplicates.append(record.id)
        seen.add(record.id)
    if duplicates:
        raise TLEPatternValidationError(
            f"Duplicate TLE pattern IDs: {', '.join(sorted(set(duplicates)))}"
        )


def _required_tuple_field(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    if key not in payload:
        raise TLEPatternValidationError(f"Missing required TLE pattern fields: {key}")
    value = payload[key]
    if value is None:
        raise TLEPatternValidationError(f"Field '{key}' must be a list.")
    if not isinstance(value, list):
        raise TLEPatternValidationError(f"Field '{key}' must be a list.")
    return tuple(str(item).strip() for item in value if str(item).strip())


def _optional_tuple_field(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    if key not in payload:
        return ()
    value = payload[key]
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    raise TLEPatternValidationError(f"Field '{key}' must be a list.")


def _evidence_refs(value: Any) -> tuple[dict[str, str], ...]:
    _validate_evidence_refs(value)
    refs: list[dict[str, str]] = []
    for ref in value:
        refs.append(
            {
                "source_family": str(ref["source_family"]).strip(),
                "reference_type": str(ref["reference_type"]).strip(),
                "note": str(ref["note"]).strip(),
            }
        )
    return tuple(refs)


def _iter_string_fields(value: Any, prefix: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        if prefix:
            yield prefix, value
        return

    if isinstance(value, dict):
        for key, nested in value.items():
            nested_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_string_fields(nested, nested_prefix)
        return

    if isinstance(value, list):
        for index, nested in enumerate(value):
            nested_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _iter_string_fields(nested, nested_prefix)
