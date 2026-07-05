"""Universal Therapeutic Pattern schema — structured language patterns for future TLE.

Descriptive metadata only. Does not contain generated therapeutic text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

REQUIRED_FIELDS: tuple[str, ...] = (
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
)

OPTIONAL_FIELDS: tuple[str, ...] = (
    "source_family",
    "delivery_formats",
    "contraindications",
    "example_use_case",
)

DEFAULT_SEED_LIBRARY_PATH = (
    Path(__file__).resolve().parent.parent / "knowledge" / "therapeutic_patterns" / "seed_library.json"
)


class TherapeuticPatternValidationError(ValueError):
    """Raised when a therapeutic pattern payload is invalid."""


@dataclass(frozen=True)
class TherapeuticPattern:
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
    source_family: tuple[str, ...] = field(default_factory=tuple)
    delivery_formats: tuple[str, ...] = field(default_factory=tuple)
    contraindications: tuple[str, ...] = field(default_factory=tuple)
    example_use_case: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TherapeuticPattern:
        _validate_required_fields(payload)
        return cls(
            id=str(payload["id"]).strip(),
            name=str(payload["name"]).strip(),
            psychological_function=_tuple_field(payload, "psychological_function"),
            good_for=_tuple_field(payload, "good_for"),
            avoid_if=_tuple_field(payload, "avoid_if"),
            language_style=_tuple_field(payload, "language_style"),
            rhythm=str(payload["rhythm"]).strip(),
            semantic_cluster=_tuple_field(payload, "semantic_cluster"),
            spiritual_compatibility=_tuple_field(payload, "spiritual_compatibility"),
            requires_symbols=_tuple_field(payload, "requires_symbols"),
            forbidden_symbols=_tuple_field(payload, "forbidden_symbols"),
            intensity=str(payload["intensity"]).strip(),
            directness=str(payload["directness"]).strip(),
            repetition_level=str(payload["repetition_level"]).strip(),
            safety_notes=_tuple_field(payload, "safety_notes"),
            source_family=_tuple_field(payload, "source_family"),
            delivery_formats=_tuple_field(payload, "delivery_formats"),
            contraindications=_tuple_field(payload, "contraindications"),
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
        }
        if self.source_family:
            payload["source_family"] = list(self.source_family)
        if self.delivery_formats:
            payload["delivery_formats"] = list(self.delivery_formats)
        if self.contraindications:
            payload["contraindications"] = list(self.contraindications)
        if self.example_use_case:
            payload["example_use_case"] = self.example_use_case
        return payload

    def to_fit_candidate(self) -> "CandidateTherapeuticPattern":
        from niros.pattern_person_fit import CandidateTherapeuticPattern

        return CandidateTherapeuticPattern(
            id=self.id,
            name=self.name,
            psychological_function=self.psychological_function,
            good_for=self.good_for,
            avoid_if=self.avoid_if,
            language_style=self.language_style,
            rhythm=self.rhythm,
            semantic_cluster=self.semantic_cluster,
            spiritual_compatibility=self.spiritual_compatibility,
            requires_symbols=self.requires_symbols,
            forbidden_symbols=self.forbidden_symbols,
            intensity=self.intensity,
            directness=self.directness,
            repetition_level=self.repetition_level,
            safety_notes=self.safety_notes,
        )


@dataclass(frozen=True)
class TherapeuticPatternLibrary:
    patterns: tuple[TherapeuticPattern, ...]

    @classmethod
    def from_dicts(cls, payloads: Iterable[dict[str, Any]]) -> TherapeuticPatternLibrary:
        patterns = tuple(TherapeuticPattern.from_dict(payload) for payload in payloads)
        _validate_unique_ids(patterns)
        return cls(patterns=patterns)

    @classmethod
    def load_json(cls, path: Path | str) -> TherapeuticPatternLibrary:
        library_path = Path(path)
        payloads = json.loads(library_path.read_text(encoding="utf-8"))
        if not isinstance(payloads, list):
            raise TherapeuticPatternValidationError("Therapeutic pattern library must be a JSON list.")
        return cls.from_dicts(payloads)

    @classmethod
    def load_seed(cls, path: Path | str | None = None) -> TherapeuticPatternLibrary:
        return cls.load_json(path or DEFAULT_SEED_LIBRARY_PATH)

    def by_id(self, pattern_id: str) -> TherapeuticPattern | None:
        for pattern in self.patterns:
            if pattern.id == pattern_id:
                return pattern
        return None

    def ids(self) -> tuple[str, ...]:
        return tuple(pattern.id for pattern in self.patterns)

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {"patterns": [pattern.to_dict() for pattern in self.patterns]}


def _tuple_field(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key, ())
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise TherapeuticPatternValidationError(f"Field '{key}' must be a list.")
    return tuple(str(item).strip() for item in value if str(item).strip())


def _validate_required_fields(payload: dict[str, Any]) -> None:
    missing = [field_name for field_name in REQUIRED_FIELDS if field_name not in payload]
    if missing:
        raise TherapeuticPatternValidationError(
            f"Missing required therapeutic pattern fields: {', '.join(missing)}"
        )

    for field_name in ("id", "name", "rhythm", "intensity", "directness", "repetition_level"):
        if not str(payload[field_name]).strip():
            raise TherapeuticPatternValidationError(f"Field '{field_name}' must not be empty.")

    for field_name in (
        "psychological_function",
        "good_for",
        "avoid_if",
        "language_style",
        "semantic_cluster",
        "spiritual_compatibility",
        "safety_notes",
    ):
        if not _tuple_field(payload, field_name):
            raise TherapeuticPatternValidationError(f"Field '{field_name}' must not be empty.")

    for field_name in ("requires_symbols", "forbidden_symbols"):
        if field_name not in payload:
            raise TherapeuticPatternValidationError(f"Missing required therapeutic pattern fields: {field_name}")


def _validate_unique_ids(patterns: tuple[TherapeuticPattern, ...]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for pattern in patterns:
        if pattern.id in seen:
            duplicates.append(pattern.id)
        seen.add(pattern.id)
    if duplicates:
        raise TherapeuticPatternValidationError(
            f"Duplicate therapeutic pattern IDs: {', '.join(sorted(set(duplicates)))}"
        )
