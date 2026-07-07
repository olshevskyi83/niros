"""Knowledge Factory UI helpers — workspace summaries and review actions for Streamlit."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path

from niros.ctpc import CanonicalTherapeuticPattern
from niros.human_review_workflow import (
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_CHANGES_REQUESTED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_REJECTED,
    HumanReviewError,
    HumanReviewRecord,
    HumanReviewWorkflow,
    deserialize_human_review_record,
)
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_UNKNOWN,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
    ctpc_pattern_relative_path,
    infer_knowledge_domain,
    is_compilable_knowledge_domain,
    is_tle_runtime_eligible_domain,
    knowledge_domain_label,
    normalize_review_knowledge_domain,
)
from niros.knowledge_factory_pipeline import KnowledgeFactoryPipeline
from niros.knowledge_library import (
    DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    KNOWLEDGE_SOURCE_TYPE_TEXT,
    build_source_record_from_library_path,
    build_knowledge_library_source_record,
    classify_knowledge_library_path,
    get_source_by_id,
    index_knowledge_library_sources,
    iter_knowledge_library_txt_files,
    list_knowledge_sources,
    relative_knowledge_library_txt_paths,
    resolve_knowledge_library_txt_path,
    upsert_knowledge_library_source_record,
    KnowledgeLibrarySourceRecord,
)
from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    KnowledgeWorkspacePaths,
    build_knowledge_workspace_paths,
    ensure_knowledge_workspace,
    knowledge_artifact_path,
)
from niros.openai_semantic_extraction_adapter import SemanticExtractionAdapterError
from niros.raw_corpus_io import load_raw_corpus, save_raw_corpus
from niros.raw_source import RawSourceCorpus, RawSourceSegment, build_raw_source_corpus
from niros.source_registry import KnowledgeSourceRecord
from niros.therapeutic_extraction import TherapeuticFunctionExtraction
from niros.txt_source_importer import import_txt_as_raw_corpus

DEFAULT_UI_MAX_BATCH_CHARS = 2000
DEFAULT_SOURCE_TYPE = "text"
DEFAULT_LANGUAGE = "unknown"
MIN_MEANINGFUL_CHARS = 40
BATCH_SEPARATOR = "\n\n---\n\n"

SCANNED_PDF_GUIDANCE = (
    "Scanned PDFs are not supported. Convert scanned pages to TXT first."
)

EVIDENCE_APPROVE_MIN_LENGTH = 100
APPROVE_MIN_CONFIDENCE = 0.8
FUNCTION_PREVIEW_LENGTH = 60

VAGUE_THERAPEUTIC_FUNCTIONS = frozenset(
    {
        "general",
        "healing",
        "n/a",
        "na",
        "other",
        "support",
        "therapy",
        "unknown",
        "wellness",
    }
)


@dataclass(frozen=True)
class WorkspaceSummary:
    incoming_files: int
    raw_corpus_count: int
    pending_review_count: int
    approved_review_count: int
    rejected_review_count: int
    changes_requested_count: int
    ctpc_pattern_count: int


@dataclass(frozen=True)
class ReviewTableItem:
    review_id: str
    source_id: str
    source_title: str
    source_family: str
    segment_id: str
    status: str
    confidence: float
    function_preview: str
    suggested_action: str
    knowledge_domain: str


@dataclass(frozen=True)
class CTPCPatternSummary:
    pattern_id: str
    segment_id: str
    therapeutic_function: str
    confidence: float
    knowledge_domain: str


@dataclass(frozen=True)
class ReviewListItem:
    filename: str
    review_id: str
    status: str
    source_id: str
    segment_id: str
    confidence: float
    therapeutic_function: str
    psychological_function: str


@dataclass(frozen=True)
class ReviewDetail:
    filename: str
    review_id: str
    extraction_id: str
    source_id: str
    segment_id: str
    status: str
    confidence: float
    therapeutic_function: str
    psychological_function: str
    generation_rules: tuple[str, ...]
    voice_rules: tuple[str, ...]
    pause_rules: tuple[str, ...]
    repetition_rules: tuple[str, ...]
    symbolic_elements: tuple[str, ...]
    candidate_targets: tuple[str, ...]
    evidence_text: str
    reviewer_notes: str
    knowledge_domain: str


@dataclass(frozen=True)
class BatchGroupSummary:
    batch_segment_id: str
    included_segment_ids: tuple[str, ...]
    char_count: int


@dataclass(frozen=True)
class ImportTxtResult:
    source_id: str
    source_title: str
    source_family: str
    total_segments: int
    usable_segments: int
    batch_groups: tuple[BatchGroupSummary, ...]
    raw_corpus_path: str


@dataclass(frozen=True)
class ExtractionRunResult:
    batch_segment_id: str
    review_id: str | None
    extraction_id: str | None
    failure_message: str | None


@dataclass(frozen=True)
class KnowledgeLibrarySourceSummary:
    source_id: str
    title: str
    domain: str
    family: str
    relative_path: str
    filename: str
    checksum: str
    source_type: str
    compile_status: str
    file_size: int
    extension: str


@dataclass(frozen=True)
class LibraryExtractionResult:
    import_result: ImportTxtResult
    extraction_results: tuple[ExtractionRunResult, ...]
    knowledge_domain: str


@dataclass(frozen=True)
class ApproveReviewResult:
    review: HumanReviewRecord
    pattern: CanonicalTherapeuticPattern
    ctpc_path: str


def _normalize_source_id(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    normalized = re.sub(r"[^a-z0-9_]+", "", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "txt_source"


def default_source_id(txt_path: Path) -> str:
    return f"source_{_normalize_source_id(txt_path.stem)}"


def meaningful_char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text.strip()))


def is_obvious_heading(text: str) -> bool:
    collapsed = " ".join(text.strip().split())
    if not collapsed:
        return False
    if meaningful_char_count(collapsed) >= MIN_MEANINGFUL_CHARS:
        return False
    if collapsed.endswith((".", "!", "?")):
        return False
    word_count = len(collapsed.split())
    return collapsed.isupper() or word_count <= 6


def is_usable_segment(segment: RawSourceSegment) -> bool:
    text = segment.raw_text.strip()
    if not text:
        return False
    if meaningful_char_count(text) < MIN_MEANINGFUL_CHARS:
        return False
    if is_obvious_heading(text):
        return False
    return True


def filter_usable_segments(
    segments: tuple[RawSourceSegment, ...] | list[RawSourceSegment],
) -> tuple[RawSourceSegment, ...]:
    return tuple(segment for segment in segments if is_usable_segment(segment))


def build_batch_segment(
    source_id: str,
    batch_index: int,
    included_segments: tuple[RawSourceSegment, ...],
) -> RawSourceSegment:
    batch_id = f"{source_id}_batch_{batch_index:03d}"
    included_ids = ", ".join(segment.segment_id for segment in included_segments)
    return RawSourceSegment(
        segment_id=batch_id,
        source_id=source_id,
        sequence_index=batch_index,
        raw_text=BATCH_SEPARATOR.join(segment.raw_text.strip() for segment in included_segments),
        notes=f"included_segment_ids={included_ids}",
    )


def build_batch_groups(
    segments: tuple[RawSourceSegment, ...] | list[RawSourceSegment],
    source_id: str,
    max_batch_chars: int = DEFAULT_UI_MAX_BATCH_CHARS,
) -> tuple[tuple[RawSourceSegment, ...], ...]:
    usable_segments = filter_usable_segments(segments)
    if not usable_segments:
        return ()

    groups: list[tuple[RawSourceSegment, ...]] = []
    current_group: list[RawSourceSegment] = []
    current_chars = 0

    for segment in usable_segments:
        segment_chars = len(segment.raw_text.strip())
        added_chars = segment_chars if not current_group else len(BATCH_SEPARATOR) + segment_chars

        if current_group and current_chars + added_chars > max_batch_chars:
            groups.append(tuple(current_group))
            current_group = [segment]
            current_chars = segment_chars
            continue

        current_group.append(segment)
        current_chars += added_chars

    if current_group:
        groups.append(tuple(current_group))

    return tuple(groups)


def summarize_batch_groups(
    groups: tuple[tuple[RawSourceSegment, ...], ...],
    source_id: str,
) -> tuple[BatchGroupSummary, ...]:
    summaries: list[BatchGroupSummary] = []
    for index, group in enumerate(groups, start=1):
        batch_segment = build_batch_segment(source_id, index, group)
        summaries.append(
            BatchGroupSummary(
                batch_segment_id=batch_segment.segment_id,
                included_segment_ids=tuple(segment.segment_id for segment in group),
                char_count=len(batch_segment.raw_text),
            )
        )
    return tuple(summaries)


def parse_multiline_field(text: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def format_multiline_field(values: tuple[str, ...]) -> str:
    return "\n".join(values)


def _workflow(workspace_root: str) -> HumanReviewWorkflow:
    paths = ensure_knowledge_workspace(workspace_root)
    return HumanReviewWorkflow(paths=paths)


def _pipeline(workspace_root: str) -> KnowledgeFactoryPipeline:
    return KnowledgeFactoryPipeline.from_workspace_root(workspace_root)


def _truncate_preview(value: str, limit: int = FUNCTION_PREVIEW_LENGTH) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 3]}..."


def is_vague_therapeutic_function(value: str) -> bool:
    normalized = value.strip().lower().replace(" ", "_")
    if not normalized:
        return True
    if len(normalized) < 4:
        return True
    return normalized in VAGUE_THERAPEUTIC_FUNCTIONS


def duplicate_segment_ids(records: list[HumanReviewRecord]) -> set[str]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.segment_id] = counts.get(record.segment_id, 0) + 1
    return {segment_id for segment_id, count in counts.items() if count > 1}


def suggested_action_for_review(
    *,
    segment_id: str,
    confidence: float,
    therapeutic_function: str,
    evidence_text: str,
    duplicate_segments: set[str],
) -> str:
    evidence = evidence_text.strip()
    if not evidence or len(evidence) <= EVIDENCE_APPROVE_MIN_LENGTH:
        return "reject_candidate"
    if segment_id in duplicate_segments:
        return "duplicate_candidate"
    if (
        confidence >= APPROVE_MIN_CONFIDENCE
        and therapeutic_function.strip()
        and len(evidence) > EVIDENCE_APPROVE_MIN_LENGTH
        and not is_vague_therapeutic_function(therapeutic_function)
    ):
        return "approve_candidate"
    return "needs_edit"


def _review_dir(paths: KnowledgeWorkspacePaths) -> Path:
    return Path(paths.review_dir)


def _count_files(directory: str, pattern: str = "*") -> int:
    path = Path(directory)
    if not path.exists():
        return 0
    return sum(1 for item in path.glob(pattern) if item.is_file())


def _count_ctpc_patterns(ctpc_dir: str) -> int:
    root = Path(ctpc_dir)
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*.json") if path.is_file())


def _load_review_file(path: Path) -> HumanReviewRecord:
    data = json.loads(path.read_text(encoding="utf-8"))
    return deserialize_human_review_record(data)


def _display_extraction(record: HumanReviewRecord) -> TherapeuticFunctionExtraction:
    if record.edited_extraction is not None:
        return record.edited_extraction
    return record.original_extraction


def summarize_workspace(workspace_root: str = DEFAULT_KNOWLEDGE_ROOT) -> WorkspaceSummary:
    """Return artifact counts for the Knowledge Factory workspace."""
    paths = build_knowledge_workspace_paths(workspace_root)
    reviews = list_review_records(workspace_root)
    status_counts = {
        REVIEW_STATUS_PENDING: 0,
        REVIEW_STATUS_APPROVED: 0,
        REVIEW_STATUS_REJECTED: 0,
        REVIEW_STATUS_CHANGES_REQUESTED: 0,
    }
    for record in reviews:
        if record.status in status_counts:
            status_counts[record.status] += 1

    return WorkspaceSummary(
        incoming_files=len(
            iter_knowledge_library_txt_files(DEFAULT_KNOWLEDGE_LIBRARY_ROOT)
        ),
        raw_corpus_count=_count_files(paths.raw_corpus_dir, "*.json"),
        pending_review_count=status_counts[REVIEW_STATUS_PENDING],
        approved_review_count=status_counts[REVIEW_STATUS_APPROVED],
        rejected_review_count=status_counts[REVIEW_STATUS_REJECTED],
        changes_requested_count=status_counts[REVIEW_STATUS_CHANGES_REQUESTED],
        ctpc_pattern_count=_count_ctpc_patterns(paths.ctpc_dir),
    )


def list_incoming_txt_files(workspace_root: str = DEFAULT_KNOWLEDGE_ROOT) -> tuple[str, ...]:
    """Return clean TXT source paths from the canonical knowledge library."""
    return relative_knowledge_library_txt_paths(DEFAULT_KNOWLEDGE_LIBRARY_ROOT)


def knowledge_library_source_to_summary(
    source: KnowledgeLibrarySourceRecord,
) -> KnowledgeLibrarySourceSummary:
    """Return a UI-safe source summary."""
    return KnowledgeLibrarySourceSummary(
        source_id=source.source_id,
        title=source.title,
        domain=source.domain,
        family=source.family,
        relative_path=source.relative_path,
        filename=source.filename,
        checksum=source.checksum,
        source_type=source.source_type,
        compile_status=source.compile_status,
        file_size=source.file_size,
        extension=source.extension,
    )


def list_knowledge_library_sources_for_ui(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> tuple[KnowledgeLibrarySourceSummary, ...]:
    """Return discovered knowledge library TXT sources for UI selection."""
    index_knowledge_library_sources(library_root)
    return tuple(
        knowledge_library_source_to_summary(source)
        for source in list_knowledge_sources(library_root)
    )


def count_knowledge_library_sources_by_family(
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
) -> dict[tuple[str, str, str, str], int]:
    """Return source counts keyed by domain, family, source type, and compile status."""
    counts: dict[tuple[str, str, str, str], int] = {}
    for source in list_knowledge_sources(library_root):
        key = (source.domain, source.family, source.source_type, source.compile_status)
        counts[key] = counts.get(key, 0) + 1
    return counts


def knowledge_domain_for_library_source(
    source: KnowledgeLibrarySourceRecord,
) -> str:
    """Map canonical library source domain to a supported review knowledge_domain."""
    if source.domain in {"psychotherapy", "psychedelic_research"}:
        return KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    if source.domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO:
        return KNOWLEDGE_DOMAIN_VOCAL_ICARO
    raise ValueError(
        f"Knowledge Library domain {source.domain!r} is not supported for extraction yet."
    )


def list_review_records(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    status: str | None = None,
) -> list[HumanReviewRecord]:
    """Load all review records, optionally filtered by status."""
    paths = build_knowledge_workspace_paths(workspace_root)
    review_dir = _review_dir(paths)
    if not review_dir.exists():
        return []

    records: list[HumanReviewRecord] = []
    for path in sorted(review_dir.glob("*.json")):
        record = _load_review_file(path)
        if status is not None and record.status != status:
            continue
        records.append(record)
    return records


def list_extraction_results_for_ui(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> tuple[ReviewTableItem, ...]:
    """Return pending and changes-requested reviews for the extraction results table."""
    actionable_statuses = {REVIEW_STATUS_PENDING, REVIEW_STATUS_CHANGES_REQUESTED}
    records = [
        record
        for record in list_review_records(workspace_root)
        if record.status in actionable_statuses
    ]
    duplicates = duplicate_segment_ids(records)
    sources_by_id = {
        source.source_id: source
        for source in list_knowledge_sources(DEFAULT_KNOWLEDGE_LIBRARY_ROOT)
    }
    items: list[ReviewTableItem] = []
    for record in records:
        extraction = _display_extraction(record)
        source = sources_by_id.get(record.source_id)
        items.append(
            ReviewTableItem(
                review_id=record.review_id,
                source_id=record.source_id,
                source_title=source.title if source is not None else "",
                source_family=source.family if source is not None else "",
                segment_id=record.segment_id,
                status=record.status,
                confidence=extraction.confidence,
                function_preview=_truncate_preview(extraction.therapeutic_function),
                suggested_action=suggested_action_for_review(
                    segment_id=record.segment_id,
                    confidence=extraction.confidence,
                    therapeutic_function=extraction.therapeutic_function,
                    evidence_text=extraction.evidence_text,
                    duplicate_segments=duplicates,
                ),
                knowledge_domain=normalize_review_knowledge_domain(record.knowledge_domain),
            )
        )
    return tuple(sorted(items, key=lambda item: item.segment_id))


def list_latest_ctpc_patterns(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    limit: int = 5,
) -> tuple[CTPCPatternSummary, ...]:
    """Return the most recently modified CTPC patterns."""
    from niros.ctpc_compiler import deserialize_ctpc_pattern

    paths = build_knowledge_workspace_paths(workspace_root)
    ctpc_dir = Path(paths.ctpc_dir)
    if not ctpc_dir.exists():
        return ()

    pattern_files = sorted(
        ctpc_dir.rglob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:limit]
    summaries: list[CTPCPatternSummary] = []
    for path in pattern_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        pattern = deserialize_ctpc_pattern(data)
        summaries.append(
            CTPCPatternSummary(
                pattern_id=pattern.pattern_id,
                segment_id=pattern.source_reference,
                therapeutic_function=_truncate_preview(pattern.therapeutic_function, 80),
                confidence=pattern.confidence,
                knowledge_domain=normalize_review_knowledge_domain(
                    pattern.knowledge_domain or data.get("knowledge_domain")
                ),
            )
        )
    return tuple(summaries)


def list_tle_eligible_ctpc_patterns(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    limit: int = 50,
) -> tuple[CTPCPatternSummary, ...]:
    """Return compiled CTPC patterns eligible for future TLE runtime loading."""
    patterns = list_latest_ctpc_patterns(workspace_root, limit=limit)
    return tuple(
        pattern
        for pattern in patterns
        if is_tle_runtime_eligible_domain(pattern.knowledge_domain)
    )


def list_pending_review_items(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> tuple[ReviewListItem, ...]:
    """Return summary rows for pending reviews."""
    paths = build_knowledge_workspace_paths(workspace_root)
    review_dir = _review_dir(paths)
    items: list[ReviewListItem] = []
    for record in list_review_records(workspace_root, status=REVIEW_STATUS_PENDING):
        extraction = _display_extraction(record)
        filename = f"{record.review_id}.json"
        review_path = review_dir / filename
        if review_path.exists():
            filename = review_path.name
        items.append(
            ReviewListItem(
                filename=filename,
                review_id=record.review_id,
                status=record.status,
                source_id=record.source_id,
                segment_id=record.segment_id,
                confidence=extraction.confidence,
                therapeutic_function=extraction.therapeutic_function,
                psychological_function=extraction.psychological_function,
            )
        )
    return tuple(items)


def load_review_record(
    review_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> HumanReviewRecord:
    """Load one human review record."""
    return _workflow(workspace_root).load_review(review_id)


def base_extraction_for_review(record: HumanReviewRecord) -> TherapeuticFunctionExtraction:
    """Return the extraction currently used for display or approval."""
    if record.edited_extraction is not None:
        return record.edited_extraction
    return record.original_extraction


def load_review_for_ui(
    review_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> ReviewDetail:
    """Load one review record formatted for UI display."""
    workflow = _workflow(workspace_root)
    record = workflow.load_review(review_id)
    extraction = _display_extraction(record)
    filename = f"{record.review_id}.json"
    review_path = Path(workflow.paths.review_dir) / filename
    if review_path.exists():
        filename = review_path.name

    return ReviewDetail(
        filename=filename,
        review_id=record.review_id,
        extraction_id=record.extraction_id,
        source_id=record.source_id,
        segment_id=record.segment_id,
        status=record.status,
        confidence=extraction.confidence,
        therapeutic_function=extraction.therapeutic_function,
        psychological_function=extraction.psychological_function,
        generation_rules=extraction.generation_rules,
        voice_rules=extraction.voice_rules,
        pause_rules=extraction.pause_rules,
        repetition_rules=extraction.repetition_rules,
        symbolic_elements=extraction.symbolic_elements,
        candidate_targets=extraction.candidate_targets,
        evidence_text=extraction.evidence_text,
        reviewer_notes=record.reviewer_notes,
        knowledge_domain=normalize_review_knowledge_domain(record.knowledge_domain),
    )


def resolve_txt_input_path(
    path_input: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> Path:
    """Resolve a TXT path from knowledge_library, absolute path, or legacy incoming."""
    cleaned = path_input.strip()
    if not cleaned:
        raise ValueError("TXT path must not be empty")

    try:
        return resolve_knowledge_library_txt_path(
            cleaned,
            DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
        )
    except FileNotFoundError:
        pass

    if "/" not in cleaned and "\\" not in cleaned and cleaned.endswith(".txt"):
        library_root = Path(DEFAULT_KNOWLEDGE_LIBRARY_ROOT)
        matches = tuple(
            sorted(
                path
                for path in library_root.rglob(cleaned)
                if path.is_file() and path.name not in {".gitkeep", ".DS_Store"}
            )
        )
        if len(matches) == 1:
            return matches[0].resolve()
        if len(matches) > 1:
            raise ValueError(
                f"TXT filename is ambiguous in knowledge_library: {cleaned}. "
                "Use a domain/family relative path."
            )

    direct = Path(cleaned).expanduser()
    if direct.is_file():
        return direct.resolve()

    legacy_incoming_candidate = Path(workspace_root) / "incoming" / cleaned
    if legacy_incoming_candidate.is_file():
        return legacy_incoming_candidate.resolve()

    raise FileNotFoundError(f"TXT file not found: {cleaned}")


def import_txt_for_ui(
    txt_path: str | Path,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    source_id: str | None = None,
    source_title: str | None = None,
    source_family: str = "manual_import",
    encoding: str = "utf-8",
    max_batch_chars: int = DEFAULT_UI_MAX_BATCH_CHARS,
) -> ImportTxtResult:
    """Import one TXT file into raw corpus and return segment/batch summaries."""
    resolved_txt = Path(txt_path).expanduser().resolve()
    if not resolved_txt.is_file():
        raise FileNotFoundError(f"TXT file not found: {resolved_txt}")
    if resolved_txt.suffix.lower() != ".txt":
        raise ValueError(f"Expected a .txt file: {resolved_txt}")

    library_location = classify_knowledge_library_path(
        resolved_txt,
        DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    )
    library_record = (
        build_source_record_from_library_path(
            resolved_txt,
            DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
        )
        if library_location
        else None
    )
    paths = ensure_knowledge_workspace(workspace_root)
    resolved_source_id = (
        source_id
        or (library_record.source_id if library_record is not None else default_source_id(resolved_txt))
    )
    resolved_source_title = (
        source_title
        or (library_record.title if library_record is not None else resolved_txt.name)
    )
    library_domain = library_location[0] if library_location else ""
    resolved_source_family = (
        library_location[1] if library_location and source_family == "manual_import" else source_family
    )
    source_record = KnowledgeSourceRecord(
        source_id=resolved_source_id,
        source_family=resolved_source_family,
        title=resolved_source_title,
        source_type=DEFAULT_SOURCE_TYPE,
        language=DEFAULT_LANGUAGE,
    )
    corpus = import_txt_as_raw_corpus(resolved_txt, source_record, encoding=encoding)
    if not corpus.segments:
        raise ValueError("No text segments were found in the TXT file.")

    domain = infer_knowledge_domain(
        source_id=resolved_source_id,
        txt_path=str(resolved_txt),
    )
    registry_record = build_knowledge_library_source_record(
        resolved_txt,
        source_id=resolved_source_id,
        title=resolved_source_title,
        author="",
        domain=library_domain or domain,
        family=resolved_source_family,
        library_root=DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    )
    upsert_knowledge_library_source_record(
        registry_record,
        DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    )

    raw_corpus_path = Path(
        knowledge_artifact_path(paths, "raw_corpus", f"{resolved_source_id}.json")
    )
    save_raw_corpus(corpus, raw_corpus_path)

    usable_segments = filter_usable_segments(corpus.segments)
    batch_groups = build_batch_groups(corpus.segments, resolved_source_id, max_batch_chars)

    return ImportTxtResult(
        source_id=resolved_source_id,
        source_title=resolved_source_title,
        source_family=resolved_source_family,
        total_segments=len(corpus.segments),
        usable_segments=len(usable_segments),
        batch_groups=summarize_batch_groups(batch_groups, resolved_source_id),
        raw_corpus_path=str(raw_corpus_path),
    )


def import_knowledge_source_for_ui(
    source_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    max_batch_chars: int = DEFAULT_UI_MAX_BATCH_CHARS,
) -> ImportTxtResult:
    """Import one knowledge_library TXT source into the processing workspace."""
    source = get_source_by_id(source_id, library_root)
    if source is None:
        raise FileNotFoundError(f"Knowledge Library source not found: {source_id}")
    if source.source_type != KNOWLEDGE_SOURCE_TYPE_TEXT:
        raise ValueError("Audio extract import/preview is not implemented yet.")
    txt_path = Path(library_root) / source.relative_path
    return import_txt_for_ui(
        txt_path,
        workspace_root,
        source_id=source.source_id,
        source_title=source.title,
        source_family=source.family,
        max_batch_chars=max_batch_chars,
    )


def run_library_source_extraction_for_ui(
    source_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    max_batch_chars: int = DEFAULT_UI_MAX_BATCH_CHARS,
    process_all: bool = True,
) -> LibraryExtractionResult:
    """Import and extract one supported knowledge_library source into pending reviews."""
    if not process_all:
        raise ValueError("Single-segment extraction is not enabled for library sources.")
    source = get_source_by_id(source_id, library_root)
    if source is None:
        raise FileNotFoundError(f"Knowledge Library source not found: {source_id}")
    knowledge_domain = knowledge_domain_for_library_source(source)
    import_result = import_knowledge_source_for_ui(
        source_id,
        workspace_root,
        library_root=library_root,
        max_batch_chars=max_batch_chars,
    )
    extraction_results = run_batch_extraction_for_ui(
        import_result.source_id,
        workspace_root,
        max_batch_chars=max_batch_chars,
        knowledge_domain=knowledge_domain,
    )
    return LibraryExtractionResult(
        import_result=import_result,
        extraction_results=extraction_results,
        knowledge_domain=knowledge_domain,
    )


def load_imported_corpus(
    source_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> RawSourceCorpus:
    """Load a previously imported raw corpus JSON artifact."""
    paths = build_knowledge_workspace_paths(workspace_root)
    raw_corpus_path = Path(
        knowledge_artifact_path(paths, "raw_corpus", f"{source_id}.json")
    )
    if not raw_corpus_path.exists():
        raise FileNotFoundError(f"Raw corpus not found for source_id={source_id}")
    return load_raw_corpus(raw_corpus_path)


def run_batch_extraction_for_ui(
    source_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    max_batch_chars: int = DEFAULT_UI_MAX_BATCH_CHARS,
    knowledge_domain: str = KNOWLEDGE_DOMAIN_VOCAL_ICARO,
) -> tuple[ExtractionRunResult, ...]:
    """Run OpenAI extraction for all batch groups and create pending reviews."""
    corpus = load_imported_corpus(source_id, workspace_root)
    batch_groups = build_batch_groups(corpus.segments, source_id, max_batch_chars)
    if not batch_groups:
        raise ValueError("No usable segments were available for batch extraction.")

    pipeline = _pipeline(workspace_root)
    results: list[ExtractionRunResult] = []

    for index, included_segments in enumerate(batch_groups, start=1):
        batch_segment = build_batch_segment(source_id, index, included_segments)
        try:
            batch_corpus = build_raw_source_corpus(corpus.source, (batch_segment,))
            extraction = pipeline.extract_from_corpus(
                batch_corpus,
                batch_segment.segment_id,
            )
            pending_review = pipeline.create_pending_review(
                extraction,
                knowledge_domain=knowledge_domain,
            )
            results.append(
                ExtractionRunResult(
                    batch_segment_id=batch_segment.segment_id,
                    review_id=pending_review.review_id,
                    extraction_id=extraction.extraction_id,
                    failure_message=None,
                )
            )
        except (SemanticExtractionAdapterError, ValueError) as exc:
            results.append(
                ExtractionRunResult(
                    batch_segment_id=batch_segment.segment_id,
                    review_id=None,
                    extraction_id=None,
                    failure_message=str(exc),
                )
            )

    return tuple(results)


def build_edited_extraction(
    base: TherapeuticFunctionExtraction,
    *,
    therapeutic_function: str,
    psychological_function: str,
    generation_rules: tuple[str, ...],
    voice_rules: tuple[str, ...],
    pause_rules: tuple[str, ...],
    repetition_rules: tuple[str, ...],
    symbolic_elements: tuple[str, ...],
) -> TherapeuticFunctionExtraction:
    """Return one edited extraction preserving immutable review identity fields."""
    return replace(
        base,
        therapeutic_function=therapeutic_function.strip(),
        psychological_function=psychological_function.strip(),
        generation_rules=generation_rules,
        voice_rules=voice_rules,
        pause_rules=pause_rules,
        repetition_rules=repetition_rules,
        symbolic_elements=symbolic_elements,
    )


def edit_review_for_ui(
    review_id: str,
    edited_extraction: TherapeuticFunctionExtraction,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> HumanReviewRecord:
    """Attach an edited extraction to one pending or changes-requested review."""
    workflow = _workflow(workspace_root)
    return workflow.edit_extraction(review_id, edited_extraction)


def assign_review_domain_for_ui(
    review_id: str,
    knowledge_domain: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> HumanReviewRecord:
    """Assign psychotherapy_tle or vocal_icaro to one review."""
    workflow = _workflow(workspace_root)
    return workflow.assign_knowledge_domain(review_id, knowledge_domain)


def approve_review_for_ui(
    review_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    reviewer_id: str = "ui_reviewer",
    reviewer_notes: str = "",
    edited_extraction: TherapeuticFunctionExtraction | None = None,
) -> ApproveReviewResult:
    """Approve one review and compile CTPC. Optionally apply edits first."""
    pipeline = _pipeline(workspace_root)
    if edited_extraction is not None:
        pipeline.review_workflow.edit_extraction(review_id, edited_extraction)
    approved = pipeline.approve_review(
        review_id,
        reviewer_id=reviewer_id,
        reviewer_notes=reviewer_notes,
    )
    pattern = pipeline.compile_approved_review(approved)
    ctpc_path = knowledge_artifact_path(
        pipeline.ctpc_compiler.paths,
        "ctpc",
        ctpc_pattern_relative_path(pattern.knowledge_domain, pattern.pattern_id),
    )
    return ApproveReviewResult(
        review=approved,
        pattern=pattern,
        ctpc_path=ctpc_path,
    )


def reject_review_for_ui(
    review_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    reviewer_id: str = "ui_reviewer",
    notes: str = "",
) -> HumanReviewRecord:
    """Reject one pending or changes-requested review without compiling CTPC."""
    workflow = _workflow(workspace_root)
    return workflow.reject(review_id, notes=notes, reviewer_id=reviewer_id)


def request_changes_for_ui(
    review_id: str,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    *,
    reviewer_id: str = "ui_reviewer",
    notes: str = "",
) -> HumanReviewRecord:
    """Request changes on one pending review."""
    workflow = _workflow(workspace_root)
    return workflow.request_changes(review_id, notes=notes, reviewer_id=reviewer_id)


def review_is_actionable(status: str) -> bool:
    """Return True when a review can be approved, rejected, or edited."""
    return status in {REVIEW_STATUS_PENDING, REVIEW_STATUS_CHANGES_REQUESTED}


def review_can_be_approved(record: HumanReviewRecord) -> bool:
    """Return True when a review has an assigned compilable knowledge domain."""
    return review_is_actionable(record.status) and is_compilable_knowledge_domain(
        record.knowledge_domain
    )


def extraction_from_review_detail(detail: ReviewDetail) -> TherapeuticFunctionExtraction:
    """Rebuild a TherapeuticFunctionExtraction from one UI detail view."""
    return TherapeuticFunctionExtraction(
        extraction_id=detail.extraction_id,
        source_id=detail.source_id,
        segment_id=detail.segment_id,
        therapeutic_function=detail.therapeutic_function,
        psychological_function=detail.psychological_function,
        evidence_text=detail.evidence_text,
        generation_rules=detail.generation_rules,
        voice_rules=detail.voice_rules,
        pause_rules=detail.pause_rules,
        repetition_rules=detail.repetition_rules,
        symbolic_elements=detail.symbolic_elements,
        candidate_targets=detail.candidate_targets,
        confidence=detail.confidence,
    )
