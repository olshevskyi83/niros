"""Tests for PDF source importer."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.pdf_importer import (
    PDFExtractionError,
    PDFFileNotFoundError,
    PDFImporter,
    PDFNoExtractableTextError,
    PDFUnsupportedFileError,
    import_pdf,
)
from niros.raw_source import RawSourceCorpus


def _write_text_pdf(path: Path, page_texts: list[str]) -> None:
    """Write a minimal text PDF readable by pypdf."""
    parts: list[bytes] = []

    def add(text: str) -> None:
        parts.append(text.encode("latin-1"))

    add("%PDF-1.4\n")
    offsets: dict[int, int] = {}

    def add_obj(number: int, body: str) -> None:
        offsets[number] = sum(len(part) for part in parts)
        add(f"{number} 0 obj\n{body}\nendobj\n")

    page_count = len(page_texts)
    font_number = 2 + (2 * page_count) + 1
    kids = " ".join(f"{3 + (2 * index)} 0 R" for index in range(page_count))

    add_obj(1, "<< /Type /Catalog /Pages 2 0 R >>")
    add_obj(2, f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>")

    for index, text in enumerate(page_texts):
        page_number = 3 + (2 * index)
        content_number = page_number + 1
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 {720 - (index * 24)} Td ({escaped}) Tj ET"
        add_obj(
            page_number,
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_number} 0 R >> >> "
                f"/Contents {content_number} 0 R >>"
            ),
        )
        add_obj(
            content_number,
            f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        )

    add_obj(font_number, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    xref_offset = sum(len(part) for part in parts)
    add("xref\n")
    add(f"0 {font_number + 1}\n")
    add("0000000000 65535 f \n")
    for number in range(1, font_number + 1):
        add(f"{offsets[number]:010d} 00000 n \n")
    add(f"trailer\n<< /Size {font_number + 1} /Root 1 0 R >>\n")
    add("startxref\n")
    add(f"{xref_offset}\n")
    add("%%EOF\n")
    path.write_bytes(b"".join(parts))


def _write_blank_pdf(path: Path, page_count: int = 1) -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as handle:
        writer.write(handle)


def test_imports_simple_generated_text_pdf_into_raw_source_corpus(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_text_pdf(pdf_path, ["Page one text", "Page two text"])

    corpus = import_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Sample PDF",
        source_family="research",
    )

    assert isinstance(corpus, RawSourceCorpus)
    assert corpus.source.source_id == "source_001"
    assert corpus.source.title == "Sample PDF"
    assert len(corpus.segments) == 2


def test_creates_one_segment_per_page_with_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "three_page.pdf"
    _write_text_pdf(
        pdf_path,
        ["First page text", "Second page text", "Third page text"],
    )

    corpus = import_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Three pages",
    )

    assert [segment.raw_text for segment in corpus.segments] == [
        "First page text",
        "Second page text",
        "Third page text",
    ]
    assert [segment.notes for segment in corpus.segments] == [
        "page_number=1; source_page_label=Page 1",
        "page_number=2; source_page_label=Page 2",
        "page_number=3; source_page_label=Page 3",
    ]


def test_deterministic_source_id_and_segment_ids(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_text_pdf(pdf_path, ["Alpha page", "Beta page"])

    corpus = import_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Sample PDF",
    )

    assert [segment.segment_id for segment in corpus.segments] == [
        "source_001_page_001",
        "source_001_page_002",
    ]
    assert [segment.sequence_index for segment in corpus.segments] == [1, 2]


def test_metadata_includes_file_type_pdf_and_page_count(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_text_pdf(pdf_path, ["Page one text", "Page two text"])

    corpus = import_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Sample PDF",
        metadata={"collection": "test"},
    )

    assert corpus.source.metadata["original_file_name"] == "sample.pdf"
    assert corpus.source.metadata["file_type"] == "pdf"
    assert corpus.source.metadata["page_count"] == 2
    assert corpus.source.metadata["imported_via"] == "pdf_importer"
    assert corpus.source.metadata["collection"] == "test"


def test_missing_file_raises_expected_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.pdf"
    with pytest.raises(PDFFileNotFoundError):
        import_pdf(missing, source_id="source_001", source_title="Missing")


def test_non_pdf_file_raises_expected_error(tmp_path: Path) -> None:
    text_path = tmp_path / "sample.txt"
    text_path.write_text("Not a PDF.", encoding="utf-8")

    with pytest.raises(PDFUnsupportedFileError):
        import_pdf(text_path, source_id="source_001", source_title="Not PDF")


def test_empty_no_text_pdf_raises_expected_error(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _write_blank_pdf(pdf_path)

    with pytest.raises(PDFNoExtractableTextError):
        import_pdf(pdf_path, source_id="source_001", source_title="Blank")


def test_importer_does_not_write_to_ctpc(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    pdf_path = tmp_path / "sample.pdf"
    _write_text_pdf(pdf_path, ["Page one text"])

    PDFImporter().import_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Sample PDF",
    )

    ctpc_dir = Path(paths.ctpc_dir)
    assert ctpc_dir.exists()
    assert list(ctpc_dir.iterdir()) == []


def test_importer_does_not_call_openai() -> None:
    import niros.pdf_importer as pdf_importer_module

    source = inspect.getsource(pdf_importer_module)
    assert "openai" not in source.lower()
    assert "OpenAI" not in source


def test_pdf_importer_class_delegates_to_import_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_text_pdf(pdf_path, ["Delegated import"])

    direct = import_pdf(pdf_path, source_id="source_001", source_title="Sample")
    via_class = PDFImporter().import_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Sample",
    )
    assert direct == via_class


def test_invalid_pdf_bytes_raise_extraction_error(tmp_path: Path) -> None:
    pdf_path = tmp_path / "broken.pdf"
    pdf_path.write_bytes(b"not-a-valid-pdf")

    with pytest.raises(PDFExtractionError):
        import_pdf(pdf_path, source_id="source_001", source_title="Broken")
