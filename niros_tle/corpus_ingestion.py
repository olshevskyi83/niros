"""Corpus ingestion guardrails — metadata registration only, no content parsing."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent / "metadata" / "document_registry.json"
)
DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent / "metadata" / "corpus_manifest.json"
)

ALLOWED_FILE_TYPES: tuple[str, ...] = ("pdf", "txt", "md", "epub")
REQUIRED_FIELDS: tuple[str, ...] = ("title", "source_family", "language", "file_type")


class CorpusIngestionError(ValueError):
    """Raised when corpus registry operations fail unexpectedly."""


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    title: str
    author: str
    source_family: str
    language: str
    file_path: str
    file_type: str
    copyright_status: str = ""
    license: str = ""
    publication_year: str = ""
    edition: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, str]:
        payload = {
            "document_id": self.document_id,
            "title": self.title,
            "author": self.author,
            "source_family": self.source_family,
            "language": self.language,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "copyright_status": self.copyright_status,
            "license": self.license,
            "publication_year": self.publication_year,
            "edition": self.edition,
            "notes": self.notes,
        }
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SourceDocument:
        return cls(
            document_id=str(payload["document_id"]).strip(),
            title=str(payload["title"]).strip(),
            author=str(payload.get("author", "")).strip(),
            source_family=str(payload["source_family"]).strip(),
            language=str(payload["language"]).strip(),
            file_path=str(payload.get("file_path", "")).strip(),
            file_type=str(payload["file_type"]).strip(),
            copyright_status=str(payload.get("copyright_status", "")).strip(),
            license=str(payload.get("license", "")).strip(),
            publication_year=str(payload.get("publication_year", "")).strip(),
            edition=str(payload.get("edition", "")).strip(),
            notes=str(payload.get("notes", "")).strip(),
        )


@dataclass(frozen=True)
class DocumentRegistrationResult:
    accepted: bool
    reason: str
    warnings: tuple[str, ...] = field(default_factory=tuple)
    normalized_metadata: dict[str, str] = field(default_factory=dict)


class CorpusRegistry:
    """Register source document metadata before any ingestion pipeline exists."""

    def __init__(
        self,
        registry_path: Path | str | None = None,
        manifest_path: Path | str | None = None,
    ) -> None:
        self._registry_path = Path(registry_path or DEFAULT_REGISTRY_PATH)
        self._manifest_path = Path(manifest_path or DEFAULT_MANIFEST_PATH)
        self._allowed_source_families = _load_source_families(self._manifest_path)
        self._documents: dict[str, SourceDocument] = {}
        self._load()

    def register_document(
        self,
        document: SourceDocument,
        *,
        persist: bool = True,
    ) -> DocumentRegistrationResult:
        result = self.validate_document(document)
        if not result.accepted:
            return result

        normalized = SourceDocument.from_dict(result.normalized_metadata)
        self._documents[normalized.document_id] = normalized
        if persist:
            self._save()
        return DocumentRegistrationResult(
            accepted=True,
            reason="Document registered.",
            warnings=result.warnings,
            normalized_metadata=result.normalized_metadata,
        )

    def save(self) -> None:
        self._save()

    def has_document(self, document_id: str) -> bool:
        return document_id.strip() in self._documents

    def list_documents(
        self,
        *,
        source_family: str | None = None,
    ) -> tuple[SourceDocument, ...]:
        documents = sorted(self._documents.values(), key=lambda item: item.document_id)
        if source_family is None:
            return tuple(documents)
        normalized_family = source_family.strip().lower()
        return tuple(
            document
            for document in documents
            if document.source_family.lower() == normalized_family
        )

    def validate_document(self, document: SourceDocument) -> DocumentRegistrationResult:
        warnings: list[str] = []
        normalized = _normalize_document_metadata(document.to_dict())

        missing = [
            field_name
            for field_name in REQUIRED_FIELDS
            if not normalized.get(field_name, "").strip()
        ]
        if missing:
            return DocumentRegistrationResult(
                accepted=False,
                reason=f"Missing required metadata: {', '.join(missing)}",
                warnings=tuple(warnings),
            )

        if not normalized["document_id"]:
            return DocumentRegistrationResult(
                accepted=False,
                reason="Missing required metadata: document_id",
                warnings=tuple(warnings),
            )

        file_type = normalized["file_type"]
        if file_type not in ALLOWED_FILE_TYPES:
            return DocumentRegistrationResult(
                accepted=False,
                reason=f"Unsupported file type '{file_type}'.",
                warnings=tuple(warnings),
            )

        source_family = normalized["source_family"]
        if source_family not in self._allowed_source_families:
            return DocumentRegistrationResult(
                accepted=False,
                reason=f"Unknown source_family '{source_family}'.",
                warnings=tuple(warnings),
            )

        if normalized["document_id"] in self._documents:
            return DocumentRegistrationResult(
                accepted=False,
                reason=f"Duplicate document_id '{normalized['document_id']}'.",
                warnings=tuple(warnings),
            )

        file_path = normalized.get("file_path", "")
        if file_path:
            extension = Path(file_path).suffix.lower().lstrip(".")
            if extension and extension != file_type:
                return DocumentRegistrationResult(
                    accepted=False,
                    reason=(
                        f"File extension '.{extension}' does not match file_type '{file_type}'."
                    ),
                    warnings=tuple(warnings),
                )
            if not Path(file_path).exists():
                warnings.append(f"file_path does not exist yet: {file_path}")
        else:
            warnings.append("file_path not provided; metadata-only registration.")

        if not normalized.get("author"):
            warnings.append("author not provided.")
        if not normalized.get("copyright_status"):
            warnings.append("copyright_status not provided.")

        return DocumentRegistrationResult(
            accepted=True,
            reason="Document metadata validated.",
            warnings=tuple(warnings),
            normalized_metadata=normalized,
        )

    def _load(self) -> None:
        if not self._registry_path.exists():
            self._documents = {}
            return

        payloads = json.loads(self._registry_path.read_text(encoding="utf-8"))
        if not isinstance(payloads, list):
            raise CorpusIngestionError("Document registry must be a JSON list.")

        documents: dict[str, SourceDocument] = {}
        for payload in payloads:
            document = SourceDocument.from_dict(payload)
            if document.document_id in documents:
                raise CorpusIngestionError(
                    f"Duplicate document_id in registry: {document.document_id}"
                )
            documents[document.document_id] = document
        self._documents = documents

    def _save(self) -> None:
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        payloads = [document.to_dict() for document in self.list_documents()]
        self._registry_path.write_text(
            json.dumps(payloads, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def generate_document_id(document: SourceDocument) -> str:
    """Build a deterministic document id from normalized metadata."""
    normalized = _normalize_document_metadata(document.to_dict())
    slug = _slugify(normalized["title"])
    return f"{normalized['source_family']}_{slug}_{normalized['file_type']}"


def _normalize_document_metadata(payload: dict[str, Any]) -> dict[str, str]:
    normalized = {key: str(value).strip() for key, value in payload.items()}
    normalized["file_type"] = normalized.get("file_type", "").lower().lstrip(".")
    normalized["source_family"] = normalized.get("source_family", "").lower()
    normalized["language"] = normalized.get("language", "").lower()
    return normalized


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "untitled"


def _load_source_families(manifest_path: Path) -> frozenset[str]:
    if not manifest_path.exists():
        raise CorpusIngestionError(f"Corpus manifest not found: {manifest_path}")

    payloads = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payloads, list):
        raise CorpusIngestionError("Corpus manifest must be a JSON list.")

    families = {
        str(entry["source_family"]).strip().lower()
        for entry in payloads
        if entry.get("source_family")
    }
    if not families:
        raise CorpusIngestionError("Corpus manifest contains no source families.")
    return frozenset(families)
