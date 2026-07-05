"""Register raw corpus files into the TLE document registry — metadata only."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from niros_tle.corpus_ingestion import (
    ALLOWED_FILE_TYPES,
    CorpusRegistry,
    SourceDocument,
    generate_document_id,
)

TLE_ROOT = Path(__file__).resolve().parent
DEFAULT_CORPUS_ROOT = TLE_ROOT / "corpus"
DEFAULT_REPO_ROOT = TLE_ROOT.parent

IGNORED_FILENAMES = frozenset({".gitkeep", ".ds_store"})
AUTO_REGISTRATION_NOTES = "Auto-registered from raw corpus."


@dataclass(frozen=True)
class CorpusRegistrationSummary:
    registered: tuple[str, ...]
    skipped_existing: tuple[str, ...]
    ignored: tuple[str, ...]
    rejected: tuple[str, ...]


def scan_raw_corpus_files(
    corpus_root: Path | str | None = None,
) -> tuple[Path, ...]:
    """Return supported raw corpus files in deterministic order."""
    root = Path(corpus_root or DEFAULT_CORPUS_ROOT)
    if not root.is_dir():
        return ()

    discovered: list[Path] = []
    for source_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        raw_dir = source_dir / "raw"
        if not raw_dir.is_dir():
            continue
        for file_path in sorted(raw_dir.iterdir()):
            if not file_path.is_file():
                continue
            if should_ignore_raw_file(file_path):
                continue
            if file_path.suffix.lower().lstrip(".") not in ALLOWED_FILE_TYPES:
                continue
            discovered.append(file_path)
    return tuple(discovered)


def should_ignore_raw_file(file_path: Path) -> bool:
    name = file_path.name
    if name.startswith("."):
        return True
    return name.lower() in IGNORED_FILENAMES


def infer_source_family(file_path: Path, corpus_root: Path) -> str:
    try:
        relative = file_path.relative_to(corpus_root)
    except ValueError as exc:
        raise ValueError(f"File is outside corpus root: {file_path}") from exc
    if len(relative.parts) < 3 or relative.parts[1] != "raw":
        raise ValueError(f"Unexpected corpus raw path: {file_path}")
    return relative.parts[0].lower()


def title_from_filename(file_path: Path) -> str:
    stem = file_path.stem
    title = re.sub(r"[_\-]+", " ", stem)
    title = re.sub(r"\s+", " ", title).strip()
    return title or "Untitled"


def build_source_document(
    file_path: Path,
    *,
    repo_root: Path,
    corpus_root: Path,
) -> SourceDocument:
    source_family = infer_source_family(file_path, corpus_root)
    file_type = file_path.suffix.lower().lstrip(".")
    title = title_from_filename(file_path)
    relative_path = file_path.relative_to(repo_root)

    draft = SourceDocument(
        document_id="",
        title=title,
        author="unknown",
        source_family=source_family,
        language="unknown",
        file_path=str(relative_path),
        file_type=file_type,
        copyright_status="unknown",
        license="unknown",
        publication_year="",
        edition="",
        notes=AUTO_REGISTRATION_NOTES,
    )
    document_id = generate_document_id(draft)
    return SourceDocument(
        document_id=document_id,
        title=title,
        author="unknown",
        source_family=source_family,
        language="unknown",
        file_path=str(relative_path),
        file_type=file_type,
        copyright_status="unknown",
        license="unknown",
        publication_year="",
        edition="",
        notes=AUTO_REGISTRATION_NOTES,
    )


def register_all_corpus_sources(
    *,
    corpus_root: Path | str | None = None,
    repo_root: Path | str | None = None,
    registry: CorpusRegistry | None = None,
) -> CorpusRegistrationSummary:
    """Scan raw corpus folders and register new documents without overwriting existing ids."""
    corpus_path = Path(corpus_root or DEFAULT_CORPUS_ROOT)
    repo_path = Path(repo_root or DEFAULT_REPO_ROOT)
    registry = registry or CorpusRegistry()

    registered: list[str] = []
    skipped_existing: list[str] = []
    ignored: list[str] = []
    rejected: list[str] = []

    if corpus_path.is_dir():
        for source_dir in sorted(path for path in corpus_path.iterdir() if path.is_dir()):
            raw_dir = source_dir / "raw"
            if not raw_dir.is_dir():
                continue
            for file_path in sorted(raw_dir.iterdir()):
                if not file_path.is_file():
                    continue
                if should_ignore_raw_file(file_path):
                    ignored.append(str(file_path.relative_to(repo_path)))
                    continue
                if file_path.suffix.lower().lstrip(".") not in ALLOWED_FILE_TYPES:
                    ignored.append(str(file_path.relative_to(repo_path)))
                    continue

                document = build_source_document(
                    file_path,
                    repo_root=repo_path,
                    corpus_root=corpus_path,
                )
                if registry.has_document(document.document_id):
                    skipped_existing.append(document.document_id)
                    continue

                result = registry.register_document(document, persist=False)
                if result.accepted:
                    registered.append(document.document_id)
                else:
                    rejected.append(f"{document.document_id}: {result.reason}")

    if registered:
        registry.save()

    return CorpusRegistrationSummary(
        registered=tuple(registered),
        skipped_existing=tuple(skipped_existing),
        ignored=tuple(ignored),
        rejected=tuple(rejected),
    )


def main() -> CorpusRegistrationSummary:
    summary = register_all_corpus_sources()
    print(f"Registered: {len(summary.registered)}")
    print(f"Skipped existing: {len(summary.skipped_existing)}")
    print(f"Ignored: {len(summary.ignored)}")
    print(f"Rejected: {len(summary.rejected)}")
    return summary


if __name__ == "__main__":
    main()
