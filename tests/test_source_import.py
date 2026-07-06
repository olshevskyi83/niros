"""Tests for source import manifests."""

from __future__ import annotations

from niros.source_import import (
    DEFAULT_IMPORT_STATUS,
    SourceImportManifest,
    build_import_manifest,
    validate_import_manifest,
)
from niros.source_registry import KnowledgeSourceRecord


def _source_record() -> KnowledgeSourceRecord:
    return KnowledgeSourceRecord(
        source_id="source_001",
        source_family="mazatec_tradition",
        title="Chant collection",
        source_type="chant",
        language="mazatec",
        author="Anonymous",
        year=1956,
    )


def test_defaults() -> None:
    manifest = SourceImportManifest(
        import_id="import_source_001",
        source_id="source_001",
        source_family="mazatec_tradition",
        title="Chant collection",
        original_filename="chants.txt",
        file_extension=".txt",
        language="mazatec",
    )
    assert manifest.import_timestamp == ""
    assert manifest.workspace_path == ""
    assert manifest.checksum == ""
    assert manifest.status == DEFAULT_IMPORT_STATUS


def test_manifest_mapping() -> None:
    manifest = build_import_manifest(
        _source_record(),
        original_filename="chants.txt",
        file_extension=".txt",
        workspace_path="knowledge_factory/incoming/chants.txt",
        checksum="abc123",
    )
    assert manifest.source_id == "source_001"
    assert manifest.source_family == "mazatec_tradition"
    assert manifest.title == "Chant collection"
    assert manifest.language == "mazatec"
    assert manifest.original_filename == "chants.txt"
    assert manifest.file_extension == ".txt"
    assert manifest.workspace_path == "knowledge_factory/incoming/chants.txt"
    assert manifest.checksum == "abc123"
    assert manifest.status == DEFAULT_IMPORT_STATUS


def test_deterministic_import_id() -> None:
    manifest = build_import_manifest(
        _source_record(),
        original_filename="chants.txt",
        file_extension=".txt",
        workspace_path="knowledge_factory/incoming/chants.txt",
    )
    assert manifest.import_id == "import_source_001"


def test_validation_valid() -> None:
    manifest = build_import_manifest(
        _source_record(),
        original_filename="chants.txt",
        file_extension=".txt",
        workspace_path="knowledge_factory/incoming/chants.txt",
    )
    assert validate_import_manifest(manifest) == ()


def test_missing_fields() -> None:
    manifest = SourceImportManifest(
        import_id="import_",
        source_id="",
        source_family="",
        title="",
        original_filename="",
        file_extension="",
        language="mazatec",
        status="",
    )
    issues = validate_import_manifest(manifest)
    assert "source_id must not be empty" in issues
    assert "source_family must not be empty" in issues
    assert "title must not be empty" in issues
    assert "original_filename must not be empty" in issues
    assert "file_extension must not be empty" in issues
    assert "status must not be empty" in issues


def test_deterministic_output() -> None:
    record = _source_record()
    first = build_import_manifest(
        record,
        original_filename="chants.txt",
        file_extension=".txt",
        workspace_path="knowledge_factory/incoming/chants.txt",
    )
    second = build_import_manifest(
        record,
        original_filename="chants.txt",
        file_extension=".txt",
        workspace_path="knowledge_factory/incoming/chants.txt",
    )
    assert first == second
    assert validate_import_manifest(first) == validate_import_manifest(second)
