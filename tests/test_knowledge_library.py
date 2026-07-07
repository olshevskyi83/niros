"""Tests for canonical clean-TXT knowledge library storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from niros.knowledge_library import (
    KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT,
    KNOWLEDGE_SOURCE_TYPE_TEXT,
    KNOWLEDGE_LIBRARY_FAMILIES,
    build_deterministic_source_id,
    build_knowledge_library_source_record,
    checksum_file,
    classify_knowledge_library_path,
    ensure_knowledge_library,
    get_source_by_id,
    index_knowledge_library_sources,
    infer_domain_and_family_from_path,
    knowledge_library_registry_path,
    list_knowledge_sources,
    load_knowledge_library_registry,
    relative_knowledge_library_txt_paths,
    resolve_knowledge_library_txt_path,
    upsert_knowledge_library_source_record,
)


def test_ensure_knowledge_library_creates_canonical_family_tree(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"

    ensure_knowledge_library(str(root))

    for domain, families in KNOWLEDGE_LIBRARY_FAMILIES.items():
        for family in families:
            assert Path(root, domain, family).is_dir()
    assert knowledge_library_registry_path(str(root)).is_file()


def test_relative_txt_paths_are_domain_family_separated(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    Path(root, "psychotherapy", "act", "ACT Made Simple.txt").write_text(
        "Clean text.",
        encoding="utf-8",
    )
    Path(root, "psychotherapy", "act", "ignored.pdf").write_text(
        "No PDFs here.",
        encoding="utf-8",
    )
    Path(root, "psychotherapy", "act", ".DS_Store").write_text(
        "ignore",
        encoding="utf-8",
    )
    Path(root, "psychotherapy", "act", ".gitkeep").write_text(
        "",
        encoding="utf-8",
    )

    assert relative_knowledge_library_txt_paths(str(root)) == (
        "psychotherapy/act/ACT Made Simple.txt",
    )


def test_resolve_knowledge_library_txt_path_by_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    txt_path = Path(root, "vocal_icaro", "maria_sabina", "chants.txt")
    txt_path.write_text("Clean chant text.", encoding="utf-8")

    resolved = resolve_knowledge_library_txt_path(
        "vocal_icaro/maria_sabina/chants.txt",
        str(root),
    )

    assert resolved == txt_path.resolve()
    assert classify_knowledge_library_path(txt_path, str(root)) == (
        "vocal_icaro",
        "maria_sabina",
    )
    assert infer_domain_and_family_from_path(txt_path, str(root)) == (
        "vocal_icaro",
        "maria_sabina",
    )


def test_recursive_scan_includes_arbitrary_top_level_domain(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    txt_path = Path(root, "psychedelic_research", "Psilocybin therapy.txt")
    txt_path.parent.mkdir(parents=True)
    txt_path.write_text("Clean psychedelic research text.", encoding="utf-8")

    sources = list_knowledge_sources(str(root))

    assert len(sources) == 1
    assert sources[0].domain == "psychedelic_research"
    assert sources[0].family == "general"
    assert sources[0].source_type == KNOWLEDGE_SOURCE_TYPE_TEXT
    assert sources[0].relative_path == "psychedelic_research/Psilocybin therapy.txt"


def test_nested_file_keeps_family_path(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    txt_path = Path(
        root,
        "vocal_icaro",
        "maria_sabina",
        "text",
        "selections_mariasabina.txt",
    )
    txt_path.parent.mkdir(parents=True)
    txt_path.write_text("Clean nested chant text.", encoding="utf-8")

    domain, family = infer_domain_and_family_from_path(txt_path, str(root))
    source = list_knowledge_sources(str(root))[0]

    assert (domain, family) == ("vocal_icaro", "maria_sabina/text")
    assert source.family == "maria_sabina/text"


def test_source_id_is_deterministic() -> None:
    assert (
        build_deterministic_source_id(
            domain="psychotherapy",
            family="act",
            filename="ACT Made Simple.txt",
        )
        == "source_psychotherapy_act_act_made_simple"
    )


def test_registry_record_requires_txt(tmp_path: Path) -> None:
    pdf_path = tmp_path / "book.pdf"
    pdf_path.write_bytes(b"%PDF")

    with pytest.raises(ValueError, match="clean TXT"):
        build_knowledge_library_source_record(
            pdf_path,
            source_id="source_book",
            title="Book",
            domain="psychotherapy",
            family="act",
        )


def test_registry_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    txt_path = Path(root, "psychotherapy", "act", "ACT Made Simple.txt")
    txt_path.write_text("Clean ACT text.", encoding="utf-8")
    record = build_knowledge_library_source_record(
        txt_path,
        source_id="source_act_made_simple",
        title="ACT Made Simple",
        author="Russ Harris",
        domain="psychotherapy",
        family="act",
        imported_at="2026-07-07T12:00:00+00:00",
        library_root=str(root),
    )

    upsert_knowledge_library_source_record(record, str(root))
    loaded = load_knowledge_library_registry(str(root))

    assert loaded == (record,)
    assert loaded[0].checksum == checksum_file(txt_path)
    registry_data = json.loads(knowledge_library_registry_path(str(root)).read_text())
    assert registry_data[0]["filename"] == "ACT Made Simple.txt"
    assert registry_data[0]["relative_path"] == "psychotherapy/act/ACT Made Simple.txt"


def test_list_knowledge_sources_and_get_source_by_id(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    Path(root, "psychotherapy", "act", "ACT Made Simple.txt").write_text(
        "Clean ACT text.",
        encoding="utf-8",
    )
    Path(root, "vocal_icaro", "maria_sabina", "chants.txt").write_text(
        "Clean chant text.",
        encoding="utf-8",
    )

    sources = list_knowledge_sources(str(root))
    ids = [source.source_id for source in sources]

    assert ids == [
        "source_psychotherapy_act_act_made_simple",
        "source_vocal_icaro_maria_sabina_chants",
    ]
    assert sources[0].domain == "psychotherapy"
    assert sources[0].family == "act"
    assert sources[0].source_type == KNOWLEDGE_SOURCE_TYPE_TEXT
    assert sources[0].extension == ".txt"
    assert sources[0].file_size > 0
    assert get_source_by_id(ids[1], str(root)) == sources[1]


def test_index_knowledge_library_sources_writes_registry(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    Path(root, "psychotherapy", "cft", "CFT Made Simple.txt").write_text(
        "Clean CFT text.",
        encoding="utf-8",
    )

    registry_path = index_knowledge_library_sources(
        str(root),
        indexed_at="2026-07-07T12:00:00+00:00",
    )
    payload = json.loads(registry_path.read_text(encoding="utf-8"))

    assert payload == [
        {
            "author": "",
            "checksum": checksum_file(Path(root, "psychotherapy", "cft", "CFT Made Simple.txt")),
            "compile_status": "never_compiled",
            "domain": "psychotherapy",
            "extension": ".txt",
            "family": "cft",
            "file_size": len("Clean CFT text."),
            "filename": "CFT Made Simple.txt",
            "imported_at": "2026-07-07T12:00:00+00:00",
            "indexed_at": "2026-07-07T12:00:00+00:00",
            "relative_path": "psychotherapy/cft/CFT Made Simple.txt",
            "source_type": "text",
            "source_id": "source_psychotherapy_cft_cft_made_simple",
            "title": "CFT Made Simple",
        }
    ]


def test_discovery_includes_audio_extract_json_and_ignores_arbitrary_json(
    tmp_path: Path,
) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    audio_path = Path(
        root,
        "vocal_icaro",
        "maria_sabina",
        "audio_extracts",
        "01_maria_sabina.audio_extract.json",
    )
    audio_path.parent.mkdir(parents=True)
    audio_path.write_text('{"transcript": "chant"}', encoding="utf-8")
    Path(audio_path.parent, "notes.json").write_text('{"ignored": true}', encoding="utf-8")

    sources = list_knowledge_sources(str(root))

    assert len(sources) == 1
    assert sources[0].domain == "vocal_icaro"
    assert sources[0].family == "maria_sabina/audio_extracts"
    assert sources[0].source_type == KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT
    assert sources[0].title == "01_maria_sabina"
    assert sources[0].relative_path == (
        "vocal_icaro/maria_sabina/audio_extracts/01_maria_sabina.audio_extract.json"
    )


def test_audio_extract_source_type_is_stored_in_registry(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    audio_path = Path(
        root,
        "vocal_icaro",
        "maria_sabina",
        "audio_extracts",
        "01_maria_sabina.audio_extract.json",
    )
    audio_path.parent.mkdir(parents=True)
    audio_path.write_text('{"transcript": "chant"}', encoding="utf-8")

    registry_path = index_knowledge_library_sources(
        str(root),
        indexed_at="2026-07-07T20:48:00+00:00",
    )
    payload = json.loads(registry_path.read_text(encoding="utf-8"))

    assert payload[0]["source_type"] == KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT
    assert payload[0]["compile_status"] == "never_compiled"
    assert payload[0]["family"] == "maria_sabina/audio_extracts"
    assert payload[0]["extension"] == ".audio_extract.json"


def test_registry_updates_when_file_added_and_removed(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    first = Path(root, "psychotherapy", "act", "act.txt")
    first.write_text("Clean ACT text.", encoding="utf-8")
    index_knowledge_library_sources(str(root), indexed_at="2026-07-07T12:00:00+00:00")

    second = Path(root, "psychedelic_research", "johns_hopkins", "depression", "study.txt")
    second.parent.mkdir(parents=True)
    second.write_text("Clean study text.", encoding="utf-8")
    index_knowledge_library_sources(str(root), indexed_at="2026-07-07T12:01:00+00:00")
    added = json.loads(knowledge_library_registry_path(str(root)).read_text())

    assert [item["relative_path"] for item in added] == [
        "psychedelic_research/johns_hopkins/depression/study.txt",
        "psychotherapy/act/act.txt",
    ]
    first.unlink()
    index_knowledge_library_sources(str(root), indexed_at="2026-07-07T12:02:00+00:00")
    removed = json.loads(knowledge_library_registry_path(str(root)).read_text())

    assert [item["relative_path"] for item in removed] == [
        "psychedelic_research/johns_hopkins/depression/study.txt",
    ]


def test_registry_resets_compile_status_when_checksum_changes(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    txt_path = Path(root, "psychotherapy", "act", "act.txt")
    txt_path.write_text("Clean ACT text.", encoding="utf-8")
    index_knowledge_library_sources(str(root), indexed_at="2026-07-07T12:00:00+00:00")
    registry_path = knowledge_library_registry_path(str(root))
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload[0]["compile_status"] = "pending_review"
    registry_path.write_text(json.dumps(payload), encoding="utf-8")

    txt_path.write_text("Updated clean ACT text.", encoding="utf-8")
    index_knowledge_library_sources(str(root), indexed_at="2026-07-07T12:01:00+00:00")
    updated = json.loads(registry_path.read_text(encoding="utf-8"))

    assert updated[0]["compile_status"] == "never_compiled"


def test_tree_txt_and_registry_are_ignored(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(root))
    Path(root, "tree.txt").write_text("tree", encoding="utf-8")
    Path(root, "registry", "ignored.txt").write_text("ignore", encoding="utf-8")
    Path(root, "psychotherapy", "act", "act.txt").write_text(
        "Clean ACT text.",
        encoding="utf-8",
    )

    assert relative_knowledge_library_txt_paths(str(root)) == ("psychotherapy/act/act.txt",)
