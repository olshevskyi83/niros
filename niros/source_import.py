"""Source Import — deterministic import manifests for knowledge sources."""

from __future__ import annotations

from dataclasses import dataclass

from niros.source_registry import KnowledgeSourceRecord

DEFAULT_IMPORT_STATUS = "imported"


@dataclass(frozen=True)
class SourceImportManifest:
    import_id: str
    source_id: str
    source_family: str
    title: str
    original_filename: str
    file_extension: str
    language: str
    import_timestamp: str = ""
    workspace_path: str = ""
    checksum: str = ""
    status: str = DEFAULT_IMPORT_STATUS


def build_import_manifest(
    source_record: KnowledgeSourceRecord,
    original_filename: str,
    file_extension: str,
    workspace_path: str,
    checksum: str = "",
) -> SourceImportManifest:
    """Build a deterministic import manifest from a registered source record."""
    return SourceImportManifest(
        import_id=f"import_{source_record.source_id}",
        source_id=source_record.source_id,
        source_family=source_record.source_family,
        title=source_record.title,
        original_filename=original_filename,
        file_extension=file_extension,
        language=source_record.language,
        workspace_path=workspace_path,
        checksum=checksum,
    )


def validate_import_manifest(manifest: SourceImportManifest) -> tuple[str, ...]:
    """Return validation issue strings for one source import manifest."""
    issues: list[str] = []

    if not manifest.source_id.strip():
        issues.append("source_id must not be empty")
    if not manifest.source_family.strip():
        issues.append("source_family must not be empty")
    if not manifest.title.strip():
        issues.append("title must not be empty")
    if not manifest.original_filename.strip():
        issues.append("original_filename must not be empty")
    if not manifest.file_extension.strip():
        issues.append("file_extension must not be empty")
    if not manifest.status.strip():
        issues.append("status must not be empty")

    return tuple(issues)
