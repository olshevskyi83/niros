"""Tests for therapeutic knowledge source registry."""

from __future__ import annotations

from niros.source_registry import (
    DEFAULT_PROCESSING_STATUS,
    KnowledgeSourceRecord,
    KnowledgeSourceRegistry,
    build_source_registry,
    get_source_record,
    list_sources_by_family,
    list_sources_by_status,
    mark_source_status,
    validate_source_record,
)


def _record(**overrides) -> KnowledgeSourceRecord:
    base = {
        "source_id": "source_001",
        "source_family": "mazatec_tradition",
        "title": "Chant collection",
        "source_type": "chant",
        "language": "mazatec",
        "author": "Anonymous",
        "year": 1956,
        "storage_path": "data/sources/source_001.txt",
    }
    base.update(overrides)
    return KnowledgeSourceRecord(**base)


def test_default_registry_empty() -> None:
    registry = KnowledgeSourceRegistry()
    assert registry.sources == ()


def test_build_source_registry_sorts_sources() -> None:
    registry = build_source_registry(
        (
            _record(source_id="source_b"),
            _record(source_id="source_a", title="A"),
        )
    )
    assert [source.source_id for source in registry.sources] == ["source_a", "source_b"]


def test_get_source_record_returns_record() -> None:
    record = _record()
    registry = build_source_registry((record,))
    assert get_source_record(registry, "source_001") == record


def test_missing_source_returns_none() -> None:
    registry = build_source_registry((_record(),))
    assert get_source_record(registry, "missing") is None


def test_list_sources_by_family() -> None:
    registry = build_source_registry(
        (
            _record(source_id="source_b", source_family="meditation"),
            _record(source_id="source_a", source_family="mazatec_tradition"),
            _record(source_id="source_c", source_family="mazatec_tradition"),
        )
    )
    matches = list_sources_by_family(registry, "mazatec_tradition")
    assert [source.source_id for source in matches] == ["source_a", "source_c"]


def test_list_sources_by_status() -> None:
    registry = build_source_registry(
        (
            _record(source_id="source_a", processing_status="registered"),
            _record(source_id="source_b", processing_status="extracted"),
            _record(source_id="source_c", processing_status="registered"),
        )
    )
    matches = list_sources_by_status(registry, "registered")
    assert [source.source_id for source in matches] == ["source_a", "source_c"]


def test_mark_source_status_updates_existing_source() -> None:
    registry = build_source_registry((_record(processing_status="registered"),))
    updated = mark_source_status(registry, "source_001", "extracted")
    record = get_source_record(updated, "source_001")
    assert record is not None
    assert record.processing_status == "extracted"


def test_mark_source_status_missing_source_unchanged() -> None:
    registry = build_source_registry((_record(),))
    updated = mark_source_status(registry, "missing", "extracted")
    assert updated == registry


def test_validate_valid_source_empty_issues() -> None:
    assert validate_source_record(_record()) == ()


def test_validate_missing_required_fields() -> None:
    issues = validate_source_record(
        KnowledgeSourceRecord(
            source_id="",
            source_family="",
            title="",
            source_type="",
            language="",
            processing_status="",
        )
    )
    assert "source_id must not be empty" in issues
    assert "source_family must not be empty" in issues
    assert "title must not be empty" in issues
    assert "source_type must not be empty" in issues
    assert "language must not be empty" in issues
    assert "processing_status must not be empty" in issues


def test_output_deterministic() -> None:
    sources = (_record(source_id="source_b"), _record(source_id="source_a", title="A"))
    first = build_source_registry(sources)
    second = build_source_registry(sources)
    assert first == second
    assert list_sources_by_family(first, "mazatec_tradition") == list_sources_by_family(
        second,
        "mazatec_tradition",
    )
    assert mark_source_status(first, "source_a", "reviewed") == mark_source_status(
        second,
        "source_a",
        "reviewed",
    )
    assert DEFAULT_PROCESSING_STATUS == "registered"
