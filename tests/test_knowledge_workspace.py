"""Tests for knowledge workspace layout."""

from __future__ import annotations

from pathlib import Path

import pytest

from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    KnowledgeWorkspacePaths,
    build_knowledge_workspace_paths,
    ensure_knowledge_workspace,
    knowledge_artifact_path,
)


def test_default_paths_deterministic() -> None:
    first = build_knowledge_workspace_paths()
    second = build_knowledge_workspace_paths()
    assert first == second
    assert first.root == DEFAULT_KNOWLEDGE_ROOT
    assert first.incoming_dir == "knowledge_factory/incoming"
    assert first.registry_dir == "knowledge_factory/registry"
    assert first.raw_corpus_dir == "knowledge_factory/raw_corpus"
    assert first.extractions_dir == "knowledge_factory/extractions"
    assert first.review_dir == "knowledge_factory/review"
    assert first.ctpc_dir == "knowledge_factory/ctpc"
    assert first.audio_dir == "knowledge_factory/audio"
    assert first.logs_dir == "knowledge_factory/logs"


def test_custom_root_paths_deterministic() -> None:
    paths = build_knowledge_workspace_paths("custom_factory")
    assert paths.root == "custom_factory"
    assert paths.ctpc_dir == "custom_factory/ctpc"
    assert isinstance(paths, KnowledgeWorkspacePaths)


def test_ensure_creates_directories_using_tmp_path(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    assert Path(paths.root).is_dir()
    assert Path(paths.incoming_dir).is_dir()
    assert Path(paths.registry_dir).is_dir()
    assert Path(paths.raw_corpus_dir).is_dir()
    assert Path(paths.extractions_dir).is_dir()
    assert Path(paths.review_dir).is_dir()
    assert Path(paths.ctpc_dir).is_dir()
    assert Path(paths.audio_dir).is_dir()
    assert Path(paths.logs_dir).is_dir()


@pytest.mark.parametrize(
    ("artifact_type", "expected_dir"),
    [
        ("incoming", "incoming"),
        ("registry", "registry"),
        ("raw_corpus", "raw_corpus"),
        ("extractions", "extractions"),
        ("review", "review"),
        ("ctpc", "ctpc"),
        ("audio", "audio"),
        ("logs", "logs"),
    ],
)
def test_artifact_path_by_type(artifact_type: str, expected_dir: str) -> None:
    paths = build_knowledge_workspace_paths("knowledge_factory")
    artifact_path = knowledge_artifact_path(paths, artifact_type, "example.json")
    assert artifact_path == f"knowledge_factory/{expected_dir}/example.json"


def test_unknown_artifact_type_raises_value_error() -> None:
    paths = build_knowledge_workspace_paths()
    with pytest.raises(ValueError, match="Unknown artifact_type"):
        knowledge_artifact_path(paths, "unknown", "example.json")
