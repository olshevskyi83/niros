"""Tests for raw corpus registration utility."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from niros_tle.corpus_ingestion import CorpusRegistry, generate_document_id
from niros_tle.corpus_registration import (
    AUTO_REGISTRATION_NOTES,
    build_source_document,
    infer_source_family,
    register_all_corpus_sources,
    scan_raw_corpus_files,
    should_ignore_raw_file,
    title_from_filename,
)

TLE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = TLE_ROOT.parent
MANIFEST_PATH = TLE_ROOT / "metadata" / "corpus_manifest.json"


@pytest.fixture
def sample_corpus(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    corpus_root = repo_root / "niros_tle" / "corpus"
    raw_dir = corpus_root / "act" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "sample_book.pdf").write_bytes(b"%PDF-1.4 sample")
    (raw_dir / "notes.txt").write_text("placeholder", encoding="utf-8")
    (raw_dir / ".gitkeep").write_text("", encoding="utf-8")
    (raw_dir / ".DS_Store").write_bytes(b"dsstore")
    (raw_dir / "unsupported.docx").write_bytes(b"docx")
    return repo_root, corpus_root


def test_scanner_finds_valid_raw_files(sample_corpus: tuple[Path, Path]):
    _, corpus_root = sample_corpus
    files = scan_raw_corpus_files(corpus_root)
    names = [path.name for path in files]
    assert names == ["notes.txt", "sample_book.pdf"]


def test_ignores_gitkeep_and_ds_store(sample_corpus: tuple[Path, Path]):
    _, corpus_root = sample_corpus
    raw_dir = corpus_root / "act" / "raw"
    assert should_ignore_raw_file(raw_dir / ".gitkeep") is True
    assert should_ignore_raw_file(raw_dir / ".DS_Store") is True
    assert should_ignore_raw_file(raw_dir / "sample_book.pdf") is False


def test_creates_deterministic_document_ids(sample_corpus: tuple[Path, Path]):
    repo_root, corpus_root = sample_corpus
    file_path = corpus_root / "act" / "raw" / "sample_book.pdf"
    first = build_source_document(file_path, repo_root=repo_root, corpus_root=corpus_root)
    second = build_source_document(file_path, repo_root=repo_root, corpus_root=corpus_root)
    assert first.document_id == second.document_id
    assert first.document_id == generate_document_id(first)


def test_source_family_inferred_from_folder(sample_corpus: tuple[Path, Path]):
    repo_root, corpus_root = sample_corpus
    file_path = corpus_root / "act" / "raw" / "sample_book.pdf"
    assert infer_source_family(file_path, corpus_root) == "act"
    document = build_source_document(file_path, repo_root=repo_root, corpus_root=corpus_root)
    assert document.source_family == "act"


def test_unsupported_files_ignored(sample_corpus: tuple[Path, Path]):
    _, corpus_root = sample_corpus
    summary = register_all_corpus_sources(
        corpus_root=corpus_root,
        repo_root=sample_corpus[0],
        registry=CorpusRegistry(
            registry_path=sample_corpus[0] / "document_registry.json",
            manifest_path=MANIFEST_PATH,
        ),
    )
    assert any(path.endswith("unsupported.docx") for path in summary.ignored)


def test_registry_persists(sample_corpus: tuple[Path, Path]):
    repo_root, corpus_root = sample_corpus
    registry_path = repo_root / "document_registry.json"
    registry = CorpusRegistry(registry_path=registry_path, manifest_path=MANIFEST_PATH)

    summary = register_all_corpus_sources(
        corpus_root=corpus_root,
        repo_root=repo_root,
        registry=registry,
    )
    assert len(summary.registered) == 2

    saved = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(saved) == 2
    assert saved[0]["notes"] == AUTO_REGISTRATION_NOTES
    assert saved[0]["author"] == "unknown"


def test_duplicate_runs_are_idempotent(sample_corpus: tuple[Path, Path]):
    repo_root, corpus_root = sample_corpus
    registry_path = repo_root / "document_registry.json"
    registry = CorpusRegistry(registry_path=registry_path, manifest_path=MANIFEST_PATH)

    first = register_all_corpus_sources(
        corpus_root=corpus_root,
        repo_root=repo_root,
        registry=registry,
    )
    second = register_all_corpus_sources(
        corpus_root=corpus_root,
        repo_root=repo_root,
        registry=registry,
    )

    assert len(first.registered) == 2
    assert first.skipped_existing == ()
    assert second.registered == ()
    assert len(second.skipped_existing) == 2


def test_no_document_content_is_parsed(sample_corpus: tuple[Path, Path]):
    repo_root, corpus_root = sample_corpus
    pdf_path = corpus_root / "act" / "raw" / "sample_book.pdf"
    registry = CorpusRegistry(
        registry_path=repo_root / "document_registry.json",
        manifest_path=MANIFEST_PATH,
    )

    original_read_text = Path.read_text
    read_paths: list[Path] = []

    def tracking_read_text(self: Path, *args: object, **kwargs: object) -> str:
        read_paths.append(self)
        return original_read_text(self, *args, **kwargs)

    with patch.object(Path, "read_text", tracking_read_text):
        register_all_corpus_sources(
            corpus_root=corpus_root,
            repo_root=repo_root,
            registry=registry,
        )

    assert pdf_path not in read_paths


def test_title_from_filename():
    assert title_from_filename(Path("The-Happiness-Trap-Harris.pdf")) == "The Happiness Trap Harris"


def test_no_niros_core_corpus_registration_integration():
    niros_dir = REPO_ROOT / "niros"
    matches = []
    for path in niros_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "corpus_registration" in text or "register_all_corpus_sources" in text:
            matches.append(str(path.relative_to(REPO_ROOT)))
    assert matches == []
