"""Tests for TLE corpus document registry guardrails."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from niros_tle.corpus_ingestion import (
    CorpusRegistry,
    SourceDocument,
    generate_document_id,
)

TLE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = TLE_ROOT.parent
MANIFEST_PATH = TLE_ROOT / "metadata" / "corpus_manifest.json"


def _valid_document(**overrides: str) -> SourceDocument:
    payload = {
        "document_id": "act_getting_unstuck_pdf",
        "title": "Getting Unstuck in ACT",
        "author": "Example Author",
        "source_family": "act",
        "language": "en",
        "file_path": "niros_tle/corpus/act/raw/getting_unstuck.pdf",
        "file_type": "pdf",
        "copyright_status": "licensed_reference",
        "license": "publisher_license",
        "publication_year": "2019",
        "edition": "1",
        "notes": "Metadata-only registration test fixture.",
    }
    payload.update(overrides)
    return SourceDocument.from_dict(payload)


@pytest.fixture
def registry(tmp_path: Path) -> CorpusRegistry:
    registry_path = tmp_path / "document_registry.json"
    return CorpusRegistry(registry_path=registry_path, manifest_path=MANIFEST_PATH)


def test_register_valid_document(registry: CorpusRegistry):
    document = _valid_document()
    result = registry.register_document(document)

    assert result.accepted is True
    assert result.reason == "Document registered."
    listed = registry.list_documents()
    assert len(listed) == 1
    assert listed[0].document_id == "act_getting_unstuck_pdf"
    assert listed[0].title == "Getting Unstuck in ACT"


def test_reject_duplicates(registry: CorpusRegistry):
    document = _valid_document()
    first = registry.register_document(document)
    second = registry.register_document(document)

    assert first.accepted is True
    assert second.accepted is False
    assert "Duplicate document_id" in second.reason
    assert len(registry.list_documents()) == 1


def test_reject_missing_metadata(registry: CorpusRegistry):
    document = _valid_document(title="")
    result = registry.validate_document(document)

    assert result.accepted is False
    assert "Missing required metadata" in result.reason
    assert "title" in result.reason


def test_reject_unsupported_extension(registry: CorpusRegistry):
    document = _valid_document(file_type="docx")
    result = registry.validate_document(document)

    assert result.accepted is False
    assert "Unsupported file type" in result.reason


def test_reject_extension_mismatch(registry: CorpusRegistry):
    document = _valid_document(
        file_type="pdf",
        file_path="niros_tle/corpus/act/raw/getting_unstuck.txt",
    )
    result = registry.validate_document(document)

    assert result.accepted is False
    assert "does not match file_type" in result.reason


def test_registry_persists(tmp_path: Path):
    registry_path = tmp_path / "document_registry.json"
    registry = CorpusRegistry(registry_path=registry_path, manifest_path=MANIFEST_PATH)
    document = _valid_document()
    registry.register_document(document)

    reloaded = CorpusRegistry(registry_path=registry_path, manifest_path=MANIFEST_PATH)
    listed = reloaded.list_documents()
    assert len(listed) == 1
    assert listed[0].document_id == document.document_id

    saved = json.loads(registry_path.read_text(encoding="utf-8"))
    assert saved[0]["title"] == document.title


def test_deterministic_ids():
    document = _valid_document()
    first = generate_document_id(document)
    second = generate_document_id(document)
    assert first == second
    assert first == "act_getting_unstuck_in_act_pdf"


def test_listing_works(registry: CorpusRegistry):
    act_doc = _valid_document(
        document_id="act_one_pdf",
        title="ACT One",
    )
    ifs_doc = _valid_document(
        document_id="ifs_intro_pdf",
        title="IFS Intro",
        source_family="ifs",
        file_path="niros_tle/corpus/ifs/raw/intro.pdf",
    )
    registry.register_document(act_doc)
    registry.register_document(ifs_doc)

    all_docs = registry.list_documents()
    act_docs = registry.list_documents(source_family="act")

    assert [doc.document_id for doc in all_docs] == ["act_one_pdf", "ifs_intro_pdf"]
    assert [doc.document_id for doc in act_docs] == ["act_one_pdf"]


def test_no_file_parsing_occurs(registry: CorpusRegistry, tmp_path: Path):
    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"%PDF-1.4")
    document = _valid_document(file_path=str(file_path))

    original_read_text = Path.read_text
    read_paths: list[Path] = []

    def tracking_read_text(self: Path, *args: object, **kwargs: object) -> str:
        read_paths.append(self)
        return original_read_text(self, *args, **kwargs)

    with patch.object(Path, "read_text", tracking_read_text):
        result = registry.register_document(document)

    assert result.accepted is True
    assert file_path not in read_paths


def test_no_niros_core_corpus_registry_integration():
    niros_dir = REPO_ROOT / "niros"
    matches = []
    for path in niros_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "corpus_ingestion" in text or "document_registry" in text:
            matches.append(str(path.relative_to(REPO_ROOT)))
    assert matches == []
