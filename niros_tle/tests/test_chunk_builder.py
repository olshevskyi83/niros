"""Tests for deterministic Knowledge Chunk Builder."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from niros_tle.chunk_builder import ChunkBuilder
from niros_tle.corpus_ingestion import SourceDocument


def _document(
    *,
    document_id: str = "act_sample_txt",
    source_family: str = "act",
    language: str = "en",
    file_path: str = "niros_tle/corpus/act/raw/sample.txt",
    file_type: str = "txt",
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title="Sample Document",
        author="unknown",
        source_family=source_family,
        language=language,
        file_path=file_path,
        file_type=file_type,
        copyright_status="unknown",
        license="unknown",
        notes="Test fixture.",
    )


@pytest.fixture
def repo_with_text(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    raw_dir = repo / "niros_tle" / "corpus" / "act" / "raw"
    raw_dir.mkdir(parents=True)
    return repo


def _write_text(repo: Path, relative_path: str, content: str) -> None:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_paragraph_split(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "First meaningful paragraph with enough words to remain standalone.\n\n"
        "Second meaningful paragraph with enough words to remain standalone.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    document = _document()
    chunks = builder.build_chunks(document)
    assert len(chunks) == 2
    assert all(chunk.chunk_type == "paragraph" for chunk in chunks)


def test_exercise_preserved(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "Exercise: Values Clarification\n"
        "1. Notice what matters.\n"
        "2. Write one value down.\n\n"
        "Short note.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    chunks = builder.build_chunks(_document())
    exercise = next(chunk for chunk in chunks if chunk.chunk_type == "exercise")
    assert "1. Notice what matters." in exercise.text
    assert "2. Write one value down." in exercise.text


def test_chant_preserved(tmp_path: Path):
    repo = tmp_path / "repo"
    raw_path = "niros_tle/corpus/maria_sabina/raw/chants.txt"
    _write_text(
        repo,
        raw_path,
        "ICARO:\n"
        "Water light river\n"
        "Soft path open\n\n\n"
        "ICARO:\n"
        "Moon thread singing\n"
        "Green door breathing\n",
    )
    builder = ChunkBuilder(repo_root=repo)
    document = _document(
        document_id="maria_sabina_chants_txt",
        source_family="maria_sabina",
        file_path=raw_path,
    )
    chunks = builder.build_chunks(document)
    chants = [chunk for chunk in chunks if chunk.chunk_type == "chant"]
    assert len(chants) == 2
    assert chants[0].text != chants[1].text


def test_story_preserved(tmp_path: Path):
    repo = tmp_path / "repo"
    raw_path = "niros_tle/corpus/erickson/raw/story.txt"
    _write_text(
        repo,
        raw_path,
        "Once upon a time there was a patient who feared elevators.\n\n"
        "He told me he could not enter the building.\n\n"
        "Chapter 2\n\n"
        "Another topic begins here with enough words to stand alone.",
    )
    builder = ChunkBuilder(repo_root=repo)
    document = _document(
        document_id="erickson_story_txt",
        source_family="erickson",
        file_path=raw_path,
    )
    chunks = builder.build_chunks(document)
    story = next(chunk for chunk in chunks if chunk.chunk_type == "story")
    assert "Once upon a time" in story.text
    assert "He told me he could not enter the building." in story.text


def test_page_numbers_preserved(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "[page 3]\n\n"
        "Paragraph on page three with enough words to remain a standalone chunk.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    chunks = builder.build_chunks(_document())
    assert chunks[0].page_start == 3
    assert chunks[0].page_end == 3


def test_section_hierarchy(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "Chapter 1\n\n"
        "Intro paragraph with enough words to remain a standalone chunk here.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    chunks = builder.build_chunks(_document())
    assert chunks[0].section_path == ("Chapter 1",)
    assert chunks[0].metadata["section_hierarchy"] == "Chapter 1"


def test_deterministic_ids(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "Stable paragraph with enough words to remain a standalone chunk.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    document = _document()
    first = builder.build_chunks(document)
    second = builder.build_chunks(document)
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert first[0].chunk_id == "act_sample_txt_0001"


def test_ordering_preserved(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "Alpha paragraph with enough words to remain a standalone chunk.\n\n"
        "Beta paragraph with enough words to remain a standalone chunk.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    chunks = builder.build_chunks(_document())
    assert [chunk.sequence_number for chunk in chunks] == [1, 2]
    assert chunks[0].text.startswith("Alpha")
    assert chunks[1].text.startswith("Beta")


def test_empty_documents(repo_with_text: Path):
    _write_text(repo_with_text, "niros_tle/corpus/act/raw/sample.txt", "   \n\n  ")
    builder = ChunkBuilder(repo_root=repo_with_text)
    chunks = builder.build_chunks(_document())
    assert chunks == ()


def test_multiple_languages(tmp_path: Path):
    repo = tmp_path / "repo"
    raw_path = "niros_tle/corpus/maria_sabina/raw/spanish.txt"
    _write_text(
        repo,
        raw_path,
        "Párrafo significativo con suficientes palabras para permanecer como unidad propia.",
    )
    builder = ChunkBuilder(repo_root=repo)
    document = _document(
        document_id="maria_sabina_spanish_txt",
        source_family="maria_sabina",
        language="es",
        file_path=raw_path,
    )
    chunks = builder.build_chunks(document)
    assert chunks[0].language == "es"


def test_output_written_to_processed(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "Processed output paragraph with enough words to remain standalone.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    document = _document()
    output_path = builder.save_chunks(document, builder.build_chunks(document))
    assert output_path.name == "act_sample_txt.chunks.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["document_id"] == document.document_id
    assert payload["chunk_count"] == 1


def test_no_openai_or_embeddings_usage(repo_with_text: Path):
    _write_text(
        repo_with_text,
        "niros_tle/corpus/act/raw/sample.txt",
        "Simple paragraph with enough words to remain a standalone chunk.",
    )
    builder = ChunkBuilder(repo_root=repo_with_text)
    with patch("builtins.open", wraps=open) as mock_open:
        chunks = builder.build_chunks(_document())
    assert len(chunks) == 1
    opened_modules = {str(call.args[0]) for call in mock_open.call_args_list if call.args}
    assert not any("openai" in item.lower() for item in opened_modules)


def test_no_niros_core_chunk_builder_integration():
    repo_root = Path(__file__).resolve().parents[2]
    niros_dir = repo_root / "niros"
    matches = []
    for path in niros_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "chunk_builder" in text or "KnowledgeChunk" in text:
            matches.append(str(path.relative_to(repo_root)))
    assert matches == []
