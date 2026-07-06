"""Source Registry — registered therapeutic knowledge sources for the compiler pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

DEFAULT_PROCESSING_STATUS = "registered"


@dataclass(frozen=True)
class KnowledgeSourceRecord:
    source_id: str
    source_family: str
    title: str
    source_type: str
    language: str
    author: str = ""
    year: int | None = None
    storage_path: str = ""
    processing_status: str = DEFAULT_PROCESSING_STATUS
    notes: str = ""


@dataclass(frozen=True)
class KnowledgeSourceRegistry:
    sources: tuple[KnowledgeSourceRecord, ...] = field(default_factory=tuple)


def build_source_registry(
    sources: tuple[KnowledgeSourceRecord, ...] | list[KnowledgeSourceRecord],
) -> KnowledgeSourceRegistry:
    """Build a source registry with sources sorted by source_id."""
    return KnowledgeSourceRegistry(
        sources=tuple(sorted(sources, key=lambda source: source.source_id))
    )


def get_source_record(
    registry: KnowledgeSourceRegistry,
    source_id: str,
) -> KnowledgeSourceRecord | None:
    """Return a registered source by ID, or None if not found."""
    for source in registry.sources:
        if source.source_id == source_id:
            return source
    return None


def list_sources_by_family(
    registry: KnowledgeSourceRegistry,
    source_family: str,
) -> tuple[KnowledgeSourceRecord, ...]:
    """Return registered sources for one source family."""
    matches = tuple(
        source for source in registry.sources if source.source_family == source_family
    )
    return tuple(sorted(matches, key=lambda source: source.source_id))


def list_sources_by_status(
    registry: KnowledgeSourceRegistry,
    processing_status: str,
) -> tuple[KnowledgeSourceRecord, ...]:
    """Return registered sources with one processing status."""
    matches = tuple(
        source
        for source in registry.sources
        if source.processing_status == processing_status
    )
    return tuple(sorted(matches, key=lambda source: source.source_id))


def mark_source_status(
    registry: KnowledgeSourceRegistry,
    source_id: str,
    processing_status: str,
) -> KnowledgeSourceRegistry:
    """Return an updated registry with one source's processing status changed."""
    updated_sources: list[KnowledgeSourceRecord] = []
    found = False

    for source in registry.sources:
        if source.source_id == source_id:
            updated_sources.append(replace(source, processing_status=processing_status))
            found = True
        else:
            updated_sources.append(source)

    if not found:
        return registry

    return build_source_registry(updated_sources)


def validate_source_record(record: KnowledgeSourceRecord) -> tuple[str, ...]:
    """Return validation issue strings for one knowledge source record."""
    issues: list[str] = []

    if not record.source_id.strip():
        issues.append("source_id must not be empty")
    if not record.source_family.strip():
        issues.append("source_family must not be empty")
    if not record.title.strip():
        issues.append("title must not be empty")
    if not record.source_type.strip():
        issues.append("source_type must not be empty")
    if not record.language.strip():
        issues.append("language must not be empty")
    if not record.processing_status.strip():
        issues.append("processing_status must not be empty")

    return tuple(issues)
