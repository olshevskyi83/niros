"""Canonical clean-TXT knowledge library storage for NIROS."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_KNOWLEDGE_LIBRARY_ROOT = "knowledge_library"
KNOWLEDGE_LIBRARY_REGISTRY_DIR = "registry"
KNOWLEDGE_LIBRARY_REGISTRY_FILENAME = "source_registry.json"
KNOWLEDGE_SOURCE_TYPE_TEXT = "text"
KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT = "audio_extract"
AUDIO_EXTRACT_FILENAME_SUFFIX = ".audio_extract.json"
COMPILE_STATUS_NEVER_COMPILED = "never_compiled"
COMPILE_STATUS_PENDING_REVIEW = "pending_review"
COMPILE_STATUS_COMPILED = "compiled"
COMPILE_STATUS_UNSUPPORTED = "unsupported"
COMPILE_STATUS_FAILED = "failed"

PSYCHOTHERAPY_DOMAIN_DIR = "psychotherapy"
VOCAL_ICARO_DOMAIN_DIR = "vocal_icaro"
MUSIC_SESSION_DOMAIN_DIR = "music_session"
PHYSIOLOGY_DOMAIN_DIR = "physiology"

KNOWLEDGE_LIBRARY_FAMILIES: dict[str, tuple[str, ...]] = {
    PSYCHOTHERAPY_DOMAIN_DIR: (
        "act",
        "cft",
        "ifs",
        "erickson",
        "narrative",
        "motivational_interviewing",
        "schema",
        "dbt",
        "cbt",
    ),
    VOCAL_ICARO_DOMAIN_DIR: ("maria_sabina", "shipibo", "quechua", "other"),
    MUSIC_SESSION_DOMAIN_DIR: (
        "johns_hopkins",
        "imperial",
        "maps",
        "mendel_kaelen",
        "music_psychology",
        "psychoacoustics",
        "rhythm",
        "vocal_research",
    ),
    PHYSIOLOGY_DOMAIN_DIR: ("eeg", "hrv", "gsr", "respiration"),
}


@dataclass(frozen=True)
class KnowledgeLibrarySourceRecord:
    source_id: str
    title: str
    domain: str
    family: str
    relative_path: str
    filename: str
    checksum: str
    source_type: str = KNOWLEDGE_SOURCE_TYPE_TEXT
    file_size: int = 0
    extension: str = ".txt"
    indexed_at: str = ""
    compile_status: str = COMPILE_STATUS_NEVER_COMPILED
    author: str = ""
    imported_at: str = ""


def _normalize_source_id_part(value: str) -> str:
    normalized = (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace(".", "_")
    )
    normalized = re.sub(r"[^a-z0-9_]+", "", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "source"


def build_deterministic_source_id(
    *,
    domain: str,
    family: str,
    filename: str,
) -> str:
    """Build a deterministic source_id from canonical library path parts."""
    stem = _source_title_from_filename(filename)
    return "source_" + "_".join(
        (
            _normalize_source_id_part(domain),
            _normalize_source_id_part(family),
            _normalize_source_id_part(stem),
        )
    )


def source_type_for_knowledge_library_path(path: str | Path) -> str | None:
    """Return the supported source type for a library path, if any."""
    resolved = Path(path)
    if resolved.suffix.lower() == ".txt":
        return KNOWLEDGE_SOURCE_TYPE_TEXT
    if resolved.name.endswith(AUDIO_EXTRACT_FILENAME_SUFFIX):
        return KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT
    return None


def _source_title_from_filename(filename: str) -> str:
    if filename.endswith(AUDIO_EXTRACT_FILENAME_SUFFIX):
        return filename.removesuffix(AUDIO_EXTRACT_FILENAME_SUFFIX)
    return Path(filename).stem


def knowledge_library_registry_path(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> Path:
    """Return the canonical knowledge library registry JSON path."""
    return (
        Path(library_root)
        / KNOWLEDGE_LIBRARY_REGISTRY_DIR
        / KNOWLEDGE_LIBRARY_REGISTRY_FILENAME
    )


def ensure_knowledge_library(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> Path:
    """Create the canonical clean-TXT knowledge library folder structure."""
    root = Path(library_root)
    root.mkdir(parents=True, exist_ok=True)
    for domain, families in KNOWLEDGE_LIBRARY_FAMILIES.items():
        for family in families:
            (root / domain / family).mkdir(parents=True, exist_ok=True)
    registry_dir = root / KNOWLEDGE_LIBRARY_REGISTRY_DIR
    registry_dir.mkdir(parents=True, exist_ok=True)
    registry_path = registry_dir / KNOWLEDGE_LIBRARY_REGISTRY_FILENAME
    if not registry_path.exists():
        registry_path.write_text("[]\n", encoding="utf-8")
    return root


def iter_knowledge_library_txt_files(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[Path, ...]:
    """Return clean TXT files from the canonical knowledge library."""
    root = Path(library_root)
    if not root.exists():
        return ()
    return tuple(
        sorted(
            path
            for path in root.rglob("*.txt")
            if path.is_file()
            and KNOWLEDGE_LIBRARY_REGISTRY_DIR not in path.parts
            and path.name not in {".DS_Store", ".gitkeep", "tree.txt"}
        )
    )


def iter_knowledge_library_source_files(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[Path, ...]:
    """Return supported source files from the canonical knowledge library."""
    root = Path(library_root)
    if not root.exists():
        return ()
    return tuple(
        sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and KNOWLEDGE_LIBRARY_REGISTRY_DIR not in path.parts
            and path.name not in {".DS_Store", ".gitkeep", "tree.txt"}
            and source_type_for_knowledge_library_path(path) is not None
        )
    )


def relative_knowledge_library_txt_paths(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[str, ...]:
    """Return clean TXT paths relative to the knowledge library root."""
    root = Path(library_root)
    return tuple(
        path.relative_to(root).as_posix()
        for path in iter_knowledge_library_txt_files(library_root)
    )


def resolve_knowledge_library_txt_path(
    path_input: str,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> Path:
    """Resolve a clean TXT path inside the canonical knowledge library."""
    cleaned = path_input.strip()
    if not cleaned:
        raise ValueError("TXT path must not be empty")

    root = Path(library_root)
    candidate = root / cleaned
    if candidate.is_file() and candidate.suffix.lower() == ".txt":
        return candidate.resolve()

    matches = [
        path
        for path in iter_knowledge_library_txt_files(library_root)
        if path.name == cleaned
    ]
    if len(matches) == 1:
        return matches[0].resolve()
    if len(matches) > 1:
        raise ValueError(
            f"TXT filename is ambiguous in knowledge_library: {cleaned}. "
            "Use a domain/family relative path."
        )
    raise FileNotFoundError(f"TXT file not found in knowledge_library: {cleaned}")


def classify_knowledge_library_path(
    path: str | Path,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[str, str] | None:
    """Return ``(domain, family)`` for any supported path inside the canonical library."""
    root = Path(library_root).resolve()
    resolved = Path(path).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) < 2 or parts[0] == KNOWLEDGE_LIBRARY_REGISTRY_DIR:
        return None
    if resolved.name == "tree.txt" or source_type_for_knowledge_library_path(resolved) is None:
        return None

    domain = parts[0]
    family = "general" if len(parts) == 2 else "/".join(parts[1:-1])
    return domain, family


def infer_domain_and_family_from_path(
    path: str | Path,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[str, str]:
    """Infer canonical ``(domain, family)`` from a knowledge_library path."""
    result = classify_knowledge_library_path(path, library_root)
    if result is None:
        raise ValueError(f"Path is not inside a supported knowledge_library family: {path}")
    return result


def checksum_file(path: str | Path) -> str:
    """Return the SHA-256 checksum for one source TXT file."""
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_knowledge_library_source_record(
    txt_path: str | Path,
    *,
    source_id: str,
    title: str,
    domain: str,
    family: str,
    author: str = "",
    imported_at: str | None = None,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    source_type: str = KNOWLEDGE_SOURCE_TYPE_TEXT,
) -> KnowledgeLibrarySourceRecord:
    """Build a canonical source registry record for one supported source document."""
    path = Path(txt_path)
    detected_source_type = source_type_for_knowledge_library_path(path)
    if detected_source_type is None:
        raise ValueError(
            "Knowledge library sources must be clean TXT files or audio extract JSON files: "
            f"{path}"
        )
    if source_type != detected_source_type:
        raise ValueError(
            f"Knowledge library source_type {source_type!r} does not match path: {path}"
        )
    timestamp = imported_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    root = Path(library_root)
    try:
        relative_path = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        relative_path = path.name
    return KnowledgeLibrarySourceRecord(
        source_id=source_id,
        title=title,
        author=author,
        domain=domain,
        family=family,
        relative_path=relative_path,
        filename=path.name,
        checksum=checksum_file(path),
        source_type=source_type,
        file_size=path.stat().st_size,
        extension=AUDIO_EXTRACT_FILENAME_SUFFIX
        if source_type == KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT
        else path.suffix.lower(),
        indexed_at=timestamp,
        imported_at=timestamp,
    )


def build_source_record_from_library_path(
    path: str | Path,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    *,
    indexed_at: str | None = None,
) -> KnowledgeLibrarySourceRecord:
    """Build one registry record directly from a canonical library source path."""
    resolved = Path(path)
    domain, family = infer_domain_and_family_from_path(resolved, library_root)
    source_type = source_type_for_knowledge_library_path(resolved)
    if source_type is None:
        raise ValueError(f"Unsupported Knowledge Library source file: {resolved}")
    source_id = build_deterministic_source_id(
        domain=domain,
        family=family,
        filename=resolved.name,
    )
    return build_knowledge_library_source_record(
        resolved,
        source_id=source_id,
        title=_source_title_from_filename(resolved.name),
        domain=domain,
        family=family,
        source_type=source_type,
        imported_at=indexed_at,
        library_root=library_root,
    )


def list_knowledge_sources(
    root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[KnowledgeLibrarySourceRecord, ...]:
    """Discover supported source documents in the canonical knowledge library."""
    existing = {
        record.source_id: record
        for record in load_knowledge_library_registry(root)
    }
    records: list[KnowledgeLibrarySourceRecord] = []
    for path in iter_knowledge_library_source_files(root):
        try:
            record = build_source_record_from_library_path(path, root)
            previous = existing.get(record.source_id)
            if previous is not None and previous.checksum == record.checksum:
                record = replace(record, compile_status=previous.compile_status)
            records.append(record)
        except ValueError:
            continue
    return tuple(sorted(records, key=lambda record: record.source_id))


def get_source_by_id(
    source_id: str,
    root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> KnowledgeLibrarySourceRecord | None:
    """Return one discovered source by source_id, or None."""
    for source in list_knowledge_sources(root):
        if source.source_id == source_id:
            return source
    return None


def index_knowledge_library_sources(
    root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    *,
    indexed_at: str | None = None,
) -> Path:
    """Write the canonical registry JSON from discovered source files."""
    existing = {
        record.source_id: record
        for record in load_knowledge_library_registry(root)
    }
    records: list[KnowledgeLibrarySourceRecord] = []
    for path in iter_knowledge_library_source_files(root):
        if classify_knowledge_library_path(path, root) is None:
            continue
        record = build_source_record_from_library_path(path, root, indexed_at=indexed_at)
        previous = existing.get(record.source_id)
        if previous is not None and previous.checksum == record.checksum:
            record = replace(record, compile_status=previous.compile_status)
        records.append(record)
    return save_knowledge_library_registry(records, root)


def set_knowledge_library_source_compile_status(
    source_id: str,
    compile_status: str,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> Path:
    """Update compile status for one indexed source record if it exists."""
    records = tuple(
        replace(record, compile_status=compile_status)
        if record.source_id == source_id
        else record
        for record in load_knowledge_library_registry(library_root)
    )
    return save_knowledge_library_registry(records, library_root)


def load_knowledge_library_registry(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[KnowledgeLibrarySourceRecord, ...]:
    """Load canonical source registry records."""
    registry_path = knowledge_library_registry_path(library_root)
    if not registry_path.exists():
        return ()
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return tuple(KnowledgeLibrarySourceRecord(**item) for item in data)


def save_knowledge_library_registry(
    records: tuple[KnowledgeLibrarySourceRecord, ...] | list[KnowledgeLibrarySourceRecord],
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> Path:
    """Persist canonical source registry records sorted by source_id."""
    ensure_knowledge_library(library_root)
    registry_path = knowledge_library_registry_path(library_root)
    sorted_records = sorted(records, key=lambda record: record.source_id)
    payload: list[dict[str, Any]] = [asdict(record) for record in sorted_records]
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return registry_path


def upsert_knowledge_library_source_record(
    record: KnowledgeLibrarySourceRecord,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> Path:
    """Insert or replace one canonical source registry record."""
    existing = {
        current.source_id: current
        for current in load_knowledge_library_registry(library_root)
    }
    existing[record.source_id] = record
    return save_knowledge_library_registry(tuple(existing.values()), library_root)
