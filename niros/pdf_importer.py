"""PDF Importer — deterministic text-based PDF ingestion into RawSourceCorpus."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency should be installed
    PdfReader = None

from niros.raw_source import (
    RawSource,
    RawSourceCorpus,
    RawSourceSegment,
    build_raw_source_corpus,
)

DEFAULT_SOURCE_TYPE = "document"
DEFAULT_LANGUAGE = "unknown"
DEFAULT_SOURCE_FAMILY = "unspecified"
IMPORTED_VIA = "pdf_importer"
PDF_FILE_TYPE = "pdf"
SUPPORTED_PDF_SUFFIXES = (".pdf",)


class PDFImporterError(Exception):
    """Base error for PDF importer failures."""


class PDFFileNotFoundError(PDFImporterError):
    """Raised when the PDF file path does not exist."""


class PDFUnsupportedFileError(PDFImporterError):
    """Raised when the file extension is not a supported PDF type."""


class PDFNoExtractableTextError(PDFImporterError):
    """Raised when a PDF contains no extractable text."""


class PDFExtractionError(PDFImporterError):
    """Raised when PDF text extraction fails."""


def _normalize_page_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _validate_pdf_path(pdf_path: Path) -> None:
    if not pdf_path.exists():
        raise PDFFileNotFoundError(f"PDF file not found: {pdf_path}")
    if pdf_path.suffix.lower() not in SUPPORTED_PDF_SUFFIXES:
        raise PDFUnsupportedFileError(
            f"Unsupported file extension for PDF import: {pdf_path.suffix}"
        )


def _read_pdf(pdf_path: Path) -> tuple[int, tuple[tuple[int, str], ...]]:
    """Read a PDF and return total page count plus non-empty page text."""
    _validate_pdf_path(pdf_path)

    if PdfReader is None:
        raise PDFExtractionError("pypdf is not installed.")

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise PDFExtractionError(f"Failed to read PDF: {pdf_path}") from exc

    page_count = len(reader.pages)
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            raw_text = page.extract_text() or ""
        except Exception as exc:
            raise PDFExtractionError(
                f"Failed to extract text from page {index} in {pdf_path}"
            ) from exc
        normalized = _normalize_page_text(raw_text)
        if normalized:
            pages.append((index, normalized))

    return page_count, tuple(pages)


def extract_pdf_page_texts(pdf_path: str | Path) -> tuple[tuple[int, str], ...]:
    """Extract non-empty page text as ``(page_number, text)`` tuples."""
    _, page_texts = _read_pdf(Path(pdf_path))
    return page_texts


def _build_segment_notes(page_number: int) -> str:
    return f"page_number={page_number}; source_page_label=Page {page_number}"


def build_segments_from_pdf_pages(
    source_id: str,
    page_texts: tuple[tuple[int, str], ...],
) -> tuple[RawSourceSegment, ...]:
    """Build deterministic raw source segments from extracted PDF pages."""
    segments: list[RawSourceSegment] = []
    for sequence_index, (page_number, raw_text) in enumerate(page_texts, start=1):
        segments.append(
            RawSourceSegment(
                segment_id=f"{source_id}_page_{page_number:03d}",
                source_id=source_id,
                sequence_index=sequence_index,
                raw_text=raw_text,
                notes=_build_segment_notes(page_number),
            )
        )
    return tuple(segments)


def import_pdf(
    pdf_path: str | Path,
    source_id: str,
    source_title: str,
    source_family: str | None = None,
    metadata: dict[str, Any] | None = None,
    *,
    language: str = DEFAULT_LANGUAGE,
    source_type: str = DEFAULT_SOURCE_TYPE,
) -> RawSourceCorpus:
    """Import a text-based PDF into a RawSourceCorpus."""
    path = Path(pdf_path)
    page_count, page_texts = _read_pdf(path)
    if not page_texts:
        raise PDFNoExtractableTextError(
            f"PDF contains no extractable text: {path}"
        )

    source_metadata: dict[str, Any] = {
        "original_file_name": path.name,
        "file_type": PDF_FILE_TYPE,
        "page_count": page_count,
        "imported_via": IMPORTED_VIA,
    }
    if metadata:
        source_metadata.update(metadata)

    source = RawSource(
        source_id=source_id,
        source_family=source_family or DEFAULT_SOURCE_FAMILY,
        title=source_title,
        language=language,
        source_type=source_type,
        metadata=source_metadata,
    )
    segments = build_segments_from_pdf_pages(source_id, page_texts)
    return build_raw_source_corpus(source, segments)


class PDFImporter:
    """Import text-based PDF files into RawSourceCorpus artifacts."""

    def import_pdf(
        self,
        pdf_path: str | Path,
        source_id: str,
        source_title: str,
        source_family: str | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        language: str = DEFAULT_LANGUAGE,
        source_type: str = DEFAULT_SOURCE_TYPE,
    ) -> RawSourceCorpus:
        """Import one PDF file into a raw source corpus."""
        return import_pdf(
            pdf_path,
            source_id,
            source_title,
            source_family=source_family,
            metadata=metadata,
            language=language,
            source_type=source_type,
        )
