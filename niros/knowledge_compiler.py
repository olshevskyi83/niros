"""Knowledge Compiler — orchestrate library TXT sources into review artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from niros.knowledge_compiler_router import (
    AudioExtractCompiler,
    TextSemanticCompiler,
    route_knowledge_source,
)
from niros.knowledge_consolidator import (
    ConsolidationSourceContext,
    DEFAULT_REVIEW_MODE,
    KnowledgeConsolidator,
    candidate_is_auto_approvable,
)
from niros.knowledge_factory_pipeline import KnowledgeFactoryPipeline
from niros.knowledge_library import (
    COMPILE_STATUS_FAILED,
    COMPILE_STATUS_PENDING_REVIEW,
    COMPILE_STATUS_UNSUPPORTED,
    DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    KnowledgeLibrarySourceRecord,
    get_source_by_id,
    index_knowledge_library_sources,
    list_knowledge_sources,
    set_knowledge_library_source_compile_status,
)
from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    KnowledgeWorkspacePaths,
    ensure_knowledge_workspace,
)
from niros.openai_semantic_extraction_adapter import (
    OPENAI_API_KEY_ENV_VAR,
    SemanticExtractionAdapterError,
    SemanticExtractionMissingApiKeyError,
    SemanticExtractionResult,
    resolve_openai_model,
)
from niros.raw_corpus_io import save_raw_corpus
from niros.raw_source import RawSourceCorpus, RawSourceSegment, build_raw_source_corpus
from niros.semantic_therapeutic_gate import (
    RELEVANCE_HIGH,
    RELEVANCE_LOW,
    RELEVANCE_MEDIUM,
    TherapeuticRelevanceDecision,
    evaluate_chunk_relevance,
    serialize_relevance_decision,
)
from niros.source_registry import KnowledgeSourceRecord
from niros.txt_source_importer import import_txt_as_raw_corpus

COMPILER_VERSION = "knowledge_compiler_mvp_1"
COMPILE_REGISTRY_FILENAME = "compile_registry.json"
COMPILE_HISTORY_FILENAME = "compile_history.jsonl"
COMPILE_RUN_LOG_PREFIX = "compile_run"
COMPILE_LIVE_LOG_PREFIX = "compile"
DEFAULT_MAX_BATCH_CHARS = 2000
DEFAULT_MAX_BATCHES = 3
MAX_CONSECUTIVE_FAILURES = 3
MIN_MEANINGFUL_CHARS = 40
BATCH_SEPARATOR = "\n\n---\n\n"

PROGRESS_STARTED = "started"
PROGRESS_SOURCE_LOADED = "source_loaded"
PROGRESS_RAW_CORPUS_CREATED = "raw_corpus_created"
PROGRESS_BATCHES_BUILT = "batches_built"
PROGRESS_BATCH_STARTED = "batch_started"
PROGRESS_BATCH_SUCCEEDED = "batch_succeeded"
PROGRESS_BATCH_FAILED = "batch_failed"
PROGRESS_BATCH_SKIPPED = "batch_skipped"
PROGRESS_GATE_SKIPPED = "gate_skipped"
PROGRESS_REVIEW_CREATED = "review_created"
PROGRESS_CONSOLIDATING = "consolidating"
PROGRESS_CONSOLIDATED = "consolidated"
PROGRESS_SAVING_REVIEWS = "saving_reviews"
PROGRESS_COMPLETED = "completed"
PROGRESS_FAILED = "failed"
PROGRESS_STOPPED = "stopped"

@dataclass(frozen=True)
class CompileBatchError:
    batch_id: str
    error_type: str
    message: str


@dataclass(frozen=True)
class CompileProgressEvent:
    event: str
    timestamp: str
    source_id: str = ""
    batch_index: int = 0
    batch_total: int = 0
    batch_id: str = ""
    reviews_created_so_far: int = 0
    failed_batches_so_far: int = 0
    skipped_reviews_so_far: int = 0
    message: str = ""


class CompileProgressTracker:
    """Emit structured progress events and append them to a live JSONL compile log."""

    def __init__(
        self,
        *,
        source_id: str,
        live_log_path: Path,
        timestamp_fn: Callable[[], str],
        callback: Callable[[CompileProgressEvent], None] | None = None,
    ) -> None:
        self.source_id = source_id
        self.live_log_path = live_log_path
        self.timestamp_fn = timestamp_fn
        self.callback = callback
        self.events: list[CompileProgressEvent] = []
        self.live_log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        event: str,
        *,
        batch_index: int = 0,
        batch_total: int = 0,
        batch_id: str = "",
        reviews_created_so_far: int = 0,
        failed_batches_so_far: int = 0,
        skipped_reviews_so_far: int = 0,
        message: str = "",
    ) -> CompileProgressEvent:
        progress_event = CompileProgressEvent(
            event=event,
            timestamp=self.timestamp_fn(),
            source_id=self.source_id,
            batch_index=batch_index,
            batch_total=batch_total,
            batch_id=batch_id,
            reviews_created_so_far=reviews_created_so_far,
            failed_batches_so_far=failed_batches_so_far,
            skipped_reviews_so_far=skipped_reviews_so_far,
            message=message,
        )
        self.events.append(progress_event)
        with self.live_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(progress_event), sort_keys=True) + "\n")
        if self.callback is not None:
            self.callback(progress_event)
        return progress_event


@dataclass(frozen=True)
class CompileRegistryEntry:
    source_id: str
    checksum: str
    last_compiled_at: str
    compiler_version: str
    status: str
    pending_reviews: int = 0
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocumentCompileResult:
    source_id: str
    relative_path: str
    status: str
    source_type: str = ""
    domain: str = ""
    family: str = ""
    knowledge_domain: str = ""
    chunks_created: int = 0
    semantic_extractions: int = 0
    pending_reviews: int = 0
    approved_patterns: int = 0
    ctpc_generated: int = 0
    raw_corpus_path: str = ""
    segment_count: int = 0
    usable_batch_count: int = 0
    max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS
    process_all_batches: bool = True
    openai_model: str = ""
    extraction_attempted: bool = False
    reviews_created: int = 0
    raw_extractions: int = 0
    filtered_extractions: int = 0
    consolidated_candidates: int = 0
    auto_approved: int = 0
    books_processed: int = 0
    failed_batches: int = 0
    skipped_reviews: int = 0
    batches_processed: int = 0
    max_batches: int | None = None
    chunks_seen: int = 0
    chunks_skipped: int = 0
    chunks_extracted: int = 0
    skipped_by_reason: tuple[tuple[str, int], ...] = ()
    low_relevance_count: int = 0
    medium_relevance_count: int = 0
    high_relevance_count: int = 0
    log_path: str = ""
    live_log_path: str = ""
    progress_events: tuple[CompileProgressEvent, ...] = ()
    failed_batch_errors: tuple[CompileBatchError, ...] = ()
    duration_seconds: float = 0.0
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompileSummary:
    scope: str
    documents_processed: int = 0
    chunks_created: int = 0
    semantic_extractions: int = 0
    pending_reviews: int = 0
    approved_patterns: int = 0
    ctpc_generated: int = 0
    failed_documents: int = 0
    skipped_documents: int = 0
    raw_extractions: int = 0
    filtered_extractions: int = 0
    consolidated_candidates: int = 0
    auto_approved: int = 0
    books_processed: int = 0
    processing_time_seconds: float = 0.0
    chunks_seen: int = 0
    chunks_skipped: int = 0
    chunks_extracted: int = 0
    skipped_by_reason: tuple[tuple[str, int], ...] = ()
    low_relevance_count: int = 0
    medium_relevance_count: int = 0
    high_relevance_count: int = 0
    document_results: tuple[DocumentCompileResult, ...] = ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _meaningful_char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text.strip()))


def _is_obvious_heading(text: str) -> bool:
    collapsed = " ".join(text.strip().split())
    if not collapsed:
        return False
    if _meaningful_char_count(collapsed) >= MIN_MEANINGFUL_CHARS:
        return False
    if collapsed.endswith((".", "!", "?")):
        return False
    return collapsed.isupper() or len(collapsed.split()) <= 6


def _is_usable_segment(segment: RawSourceSegment) -> bool:
    text = segment.raw_text.strip()
    return (
        bool(text)
        and _meaningful_char_count(text) >= MIN_MEANINGFUL_CHARS
        and not _is_obvious_heading(text)
    )


def _is_gate_candidate(segment: RawSourceSegment) -> bool:
    """Return True when a raw segment should be evaluated by the therapeutic gate."""
    text = segment.raw_text.strip()
    return bool(text) and not _is_obvious_heading(text)


def _build_batch_segment(
    source_id: str,
    batch_index: int,
    included_segments: tuple[RawSourceSegment, ...],
) -> RawSourceSegment:
    included_ids = ", ".join(segment.segment_id for segment in included_segments)
    return RawSourceSegment(
        segment_id=f"{source_id}_batch_{batch_index:03d}",
        source_id=source_id,
        sequence_index=batch_index,
        raw_text=BATCH_SEPARATOR.join(segment.raw_text.strip() for segment in included_segments),
        notes=f"included_segment_ids={included_ids}",
    )


def _build_batch_segments(
    segments: tuple[RawSourceSegment, ...],
    source_id: str,
    max_batch_chars: int,
) -> tuple[RawSourceSegment, ...]:
    usable_segments = tuple(segment for segment in segments if _is_usable_segment(segment))
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

    return tuple(
        _build_batch_segment(source_id, index, group)
        for index, group in enumerate(groups, start=1)
    )


def _increment_skip_reason(
    skipped_by_reason: dict[str, int],
    skip_reason: str,
) -> None:
    key = skip_reason.strip() or "unknown"
    skipped_by_reason[key] = skipped_by_reason.get(key, 0) + 1


def _sorted_skip_reasons(
    skipped_by_reason: dict[str, int],
) -> tuple[tuple[str, int], ...]:
    return tuple(
        sorted(skipped_by_reason.items(), key=lambda item: (-item[1], item[0]))
    )


def _increment_relevance_band(
    *,
    decision: TherapeuticRelevanceDecision,
    low_relevance_count: int,
    medium_relevance_count: int,
    high_relevance_count: int,
) -> tuple[int, int, int]:
    band = decision.relevance_band
    if band == RELEVANCE_HIGH:
        return low_relevance_count, medium_relevance_count, high_relevance_count + 1
    if band == RELEVANCE_MEDIUM:
        return low_relevance_count, medium_relevance_count + 1, high_relevance_count
    return low_relevance_count + 1, medium_relevance_count, high_relevance_count


def _relevance_for_candidate(
    candidate: Any,
    relevance_by_segment_id: dict[str, TherapeuticRelevanceDecision],
) -> TherapeuticRelevanceDecision | None:
    for fragment in candidate.evidence_fragments:
        decision = relevance_by_segment_id.get(fragment.segment_id)
        if decision is not None:
            return decision
    return None


class KnowledgeCompiler:
    """Compile canonical Knowledge Library TXT sources into pending reviews."""

    def __init__(
        self,
        *,
        library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
        workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
        pipeline: KnowledgeFactoryPipeline | None = None,
        timestamp_fn: Callable[[], str] = _utc_now,
    ) -> None:
        self.library_root = library_root
        self.workspace_root = workspace_root
        self.paths = ensure_knowledge_workspace(workspace_root)
        self._pipeline = pipeline
        self.timestamp_fn = timestamp_fn

    @property
    def pipeline(self) -> KnowledgeFactoryPipeline:
        if self._pipeline is None:
            self._pipeline = KnowledgeFactoryPipeline.from_workspace_root(
                self.workspace_root,
                paths=self.paths,
            )
        return self._pipeline

    @property
    def compile_registry_path(self) -> Path:
        return Path(self.paths.registry_dir) / COMPILE_REGISTRY_FILENAME

    @property
    def compile_history_path(self) -> Path:
        return Path(self.paths.logs_dir) / COMPILE_HISTORY_FILENAME

    def compile_document(
        self,
        source_id_or_path: str,
        *,
        force: bool = False,
        max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
        process_all_batches: bool = True,
        max_batches: int | None = None,
        progress_callback: Callable[[CompileProgressEvent], None] | None = None,
        review_mode: str = DEFAULT_REVIEW_MODE,
        auto_approve: bool = False,
        force_allow_single_evidence_auto_approve: bool = False,
    ) -> CompileSummary:
        source = self._resolve_source(source_id_or_path)
        return self._compile_sources(
            scope=f"document:{source.source_id}",
            sources=(source,),
            force=force,
            max_batch_chars=max_batch_chars,
            process_all_batches=process_all_batches,
            max_batches=max_batches,
            progress_callback=progress_callback,
            review_mode=review_mode,
            auto_approve=auto_approve,
            force_allow_single_evidence_auto_approve=force_allow_single_evidence_auto_approve,
        )

    def compile_family(
        self,
        domain: str,
        family: str,
        *,
        force: bool = False,
        max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
        process_all_batches: bool = True,
        max_batches: int | None = None,
        progress_callback: Callable[[CompileProgressEvent], None] | None = None,
        review_mode: str = DEFAULT_REVIEW_MODE,
        auto_approve: bool = False,
        force_allow_single_evidence_auto_approve: bool = False,
    ) -> CompileSummary:
        sources = tuple(
            source
            for source in list_knowledge_sources(self.library_root)
            if source.domain == domain and source.family == family
        )
        return self._compile_sources(
            scope=f"family:{domain}/{family}",
            sources=sources,
            force=force,
            max_batch_chars=max_batch_chars,
            process_all_batches=process_all_batches,
            max_batches=max_batches,
            progress_callback=progress_callback,
            review_mode=review_mode,
            auto_approve=auto_approve,
            force_allow_single_evidence_auto_approve=force_allow_single_evidence_auto_approve,
        )

    def compile_domain(
        self,
        domain: str,
        *,
        force: bool = False,
        max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
        process_all_batches: bool = True,
        max_batches: int | None = None,
        progress_callback: Callable[[CompileProgressEvent], None] | None = None,
        review_mode: str = DEFAULT_REVIEW_MODE,
        auto_approve: bool = False,
        force_allow_single_evidence_auto_approve: bool = False,
    ) -> CompileSummary:
        sources = tuple(
            source
            for source in list_knowledge_sources(self.library_root)
            if source.domain == domain
        )
        return self._compile_sources(
            scope=f"domain:{domain}",
            sources=sources,
            force=force,
            max_batch_chars=max_batch_chars,
            process_all_batches=process_all_batches,
            max_batches=max_batches,
            progress_callback=progress_callback,
            review_mode=review_mode,
            auto_approve=auto_approve,
            force_allow_single_evidence_auto_approve=force_allow_single_evidence_auto_approve,
        )

    def compile_library(
        self,
        *,
        force: bool = False,
        max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
        process_all_batches: bool = True,
        max_batches: int | None = None,
        progress_callback: Callable[[CompileProgressEvent], None] | None = None,
        review_mode: str = DEFAULT_REVIEW_MODE,
        auto_approve: bool = False,
        force_allow_single_evidence_auto_approve: bool = False,
    ) -> CompileSummary:
        sources = list_knowledge_sources(self.library_root)
        return self._compile_sources(
            scope="library",
            sources=sources,
            force=force,
            max_batch_chars=max_batch_chars,
            process_all_batches=process_all_batches,
            max_batches=max_batches,
            progress_callback=progress_callback,
            review_mode=review_mode,
            auto_approve=auto_approve,
            force_allow_single_evidence_auto_approve=force_allow_single_evidence_auto_approve,
        )

    def _resolve_source(self, source_id_or_path: str) -> KnowledgeLibrarySourceRecord:
        index_knowledge_library_sources(self.library_root)
        by_id = get_source_by_id(source_id_or_path, self.library_root)
        if by_id is not None:
            return by_id
        normalized = source_id_or_path.strip()
        for source in list_knowledge_sources(self.library_root):
            if source.relative_path == normalized:
                return source
        raise FileNotFoundError(f"Knowledge Library source not found: {source_id_or_path}")

    def _compile_sources(
        self,
        *,
        scope: str,
        sources: tuple[KnowledgeLibrarySourceRecord, ...],
        force: bool,
        max_batch_chars: int,
        process_all_batches: bool,
        max_batches: int | None,
        progress_callback: Callable[[CompileProgressEvent], None] | None,
        review_mode: str = DEFAULT_REVIEW_MODE,
        auto_approve: bool = False,
        force_allow_single_evidence_auto_approve: bool = False,
    ) -> CompileSummary:
        start = perf_counter()
        compiled: list[tuple[DocumentCompileResult, tuple[TherapeuticFunctionExtraction, ...], KnowledgeLibrarySourceRecord, str]] = []
        for source in sources:
            result, extractions, timestamp = self._compile_source(
                source,
                force=force,
                max_batch_chars=max_batch_chars,
                process_all_batches=process_all_batches,
                max_batches=max_batches,
                progress_callback=progress_callback,
                defer_consolidation=len(sources) > 1,
                review_mode=review_mode,
                auto_approve=auto_approve,
                force_allow_single_evidence_auto_approve=force_allow_single_evidence_auto_approve,
            )
            compiled.append((result, extractions, source, timestamp))

        all_extractions = [
            extraction
            for _, extractions, _, _ in compiled
            for extraction in extractions
        ]
        scope_pending = 0
        scope_skipped = 0
        scope_candidates = 0
        scope_filtered = 0
        scope_auto_approved = 0
        if len(sources) > 1 and all_extractions:
            knowledge_domain = next(
                (
                    item[0].knowledge_domain
                    for item in compiled
                    if item[0].knowledge_domain
                ),
                "",
            )
            (
                scope_pending,
                scope_skipped,
                scope_candidates,
                scope_filtered,
                scope_auto_approved,
            ) = self._queue_consolidated_reviews(
                all_extractions,
                sources=sources,
                knowledge_domain=knowledge_domain,
                force=force,
                progress_callback=progress_callback,
                scope_label=scope,
                review_mode=review_mode,
                auto_approve=auto_approve,
                force_allow_single_evidence_auto_approve=force_allow_single_evidence_auto_approve,
            )

        final_results: list[DocumentCompileResult] = []
        for result, extractions, source, timestamp in compiled:
            updated = replace(
                result,
                raw_extractions=len(extractions),
                books_processed=1,
            )
            if len(sources) == 1:
                updated = replace(
                    updated,
                    pending_reviews=result.pending_reviews,
                    reviews_created=result.reviews_created,
                    skipped_reviews=result.skipped_reviews,
                    consolidated_candidates=result.consolidated_candidates,
                )
            final_results.append(self._record_compile_result(source, updated, timestamp))

        return self._summary_from_results(
            scope=scope,
            results=tuple(final_results),
            started_at=start,
            scope_pending_reviews=scope_pending if len(sources) > 1 else sum(
                result.pending_reviews for result in final_results
            ),
            scope_consolidated_candidates=scope_candidates if len(sources) > 1 else sum(
                result.consolidated_candidates for result in final_results
            ),
            scope_raw_extractions=len(all_extractions),
            scope_filtered_extractions=scope_filtered if len(sources) > 1 else sum(
                result.filtered_extractions for result in final_results
            ),
            scope_auto_approved=scope_auto_approved if len(sources) > 1 else sum(
                result.auto_approved for result in final_results
            ),
            scope_books_processed=len(sources),
        )

    def _compile_source(
        self,
        source: KnowledgeLibrarySourceRecord,
        *,
        force: bool,
        max_batch_chars: int,
        process_all_batches: bool,
        max_batches: int | None,
        progress_callback: Callable[[CompileProgressEvent], None] | None,
        defer_consolidation: bool = False,
        review_mode: str = DEFAULT_REVIEW_MODE,
        auto_approve: bool = False,
        force_allow_single_evidence_auto_approve: bool = False,
    ) -> tuple[DocumentCompileResult, tuple[TherapeuticFunctionExtraction, ...], str]:
        start = perf_counter()
        timestamp = self.timestamp_fn()
        live_log_path = self._compile_live_log_path(source, timestamp)
        progress = CompileProgressTracker(
            source_id=source.source_id,
            live_log_path=live_log_path,
            timestamp_fn=self.timestamp_fn,
            callback=progress_callback,
        )
        progress.emit(PROGRESS_STARTED, message="Compile started.")

        route = route_knowledge_source(source)
        progress.emit(
            PROGRESS_SOURCE_LOADED,
            message=f"Loaded source {source.relative_path}.",
        )

        if not route.supported:
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="unsupported",
                max_batch_chars=max_batch_chars,
                process_all_batches=process_all_batches,
                max_batches=max_batches,
                live_log_path=str(live_log_path),
                progress_events=tuple(progress.events),
                duration_seconds=round(perf_counter() - start, 4),
                errors=(route.unsupported_reason,),
            )
            progress.emit(PROGRESS_FAILED, message=route.unsupported_reason)
            return result, (), timestamp

        knowledge_domain = route.knowledge_domain
        if not knowledge_domain:
            message = f"Unsupported knowledge library domain: {source.domain}"
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="failed",
                max_batch_chars=max_batch_chars,
                process_all_batches=process_all_batches,
                max_batches=max_batches,
                live_log_path=str(live_log_path),
                progress_events=tuple(progress.events),
                duration_seconds=round(perf_counter() - start, 4),
                errors=(message,),
            )
            progress.emit(PROGRESS_FAILED, message=message)
            return result, (), timestamp

        registry = self._load_compile_registry()
        previous = registry.get(source.source_id)
        if (
            previous is not None
            and previous.checksum == source.checksum
            and previous.compiler_version == COMPILER_VERSION
            and not force
        ):
            message = "Skipped unchanged source; checksum matches previous compile."
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="skipped",
                knowledge_domain=knowledge_domain,
                max_batch_chars=max_batch_chars,
                process_all_batches=process_all_batches,
                max_batches=max_batches,
                live_log_path=str(live_log_path),
                progress_events=tuple(progress.events),
                duration_seconds=round(perf_counter() - start, 4),
            )
            progress.emit(PROGRESS_COMPLETED, message=message)
            return result, (), timestamp

        if isinstance(route.compiler, AudioExtractCompiler):
            adapter_result = route.compiler.compile(
                source,
                library_root=self.library_root,
                paths=self.paths,
                timestamp_fn=self.timestamp_fn,
            )
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status=adapter_result.status,
                knowledge_domain=adapter_result.knowledge_domain,
                chunks_created=adapter_result.chunks_created,
                semantic_extractions=adapter_result.semantic_extractions,
                pending_reviews=adapter_result.pending_reviews,
                reviews_created=adapter_result.pending_reviews,
                extraction_attempted=True,
                max_batch_chars=max_batch_chars,
                process_all_batches=process_all_batches,
                max_batches=max_batches,
                live_log_path=str(live_log_path),
                progress_events=tuple(progress.events),
                duration_seconds=round(perf_counter() - start, 4),
                errors=adapter_result.errors,
            )
            if adapter_result.status == "failed":
                progress.emit(PROGRESS_FAILED, message=adapter_result.errors[0] if adapter_result.errors else "Audio extract compile failed.")
            else:
                progress.emit(PROGRESS_REVIEW_CREATED, reviews_created_so_far=adapter_result.pending_reviews, message="Audio-vocal review proposal created.")
                progress.emit(PROGRESS_COMPLETED, message="Audio extract compile completed.")
            return result, (), timestamp

        if not isinstance(route.compiler, TextSemanticCompiler):
            message = "No compiler adapter is available for this source."
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="failed",
                knowledge_domain=knowledge_domain,
                max_batch_chars=max_batch_chars,
                process_all_batches=process_all_batches,
                max_batches=max_batches,
                live_log_path=str(live_log_path),
                progress_events=tuple(progress.events),
                duration_seconds=round(perf_counter() - start, 4),
                errors=(message,),
            )
            progress.emit(PROGRESS_FAILED, message=message)
            return result, (), timestamp

        raw_corpus_path = str(Path(self.paths.raw_corpus_dir) / f"{source.source_id}.json")
        try:
            corpus = self._import_source_to_raw_corpus(source)
        except (ValueError, OSError) as exc:
            message = str(exc)
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="failed",
                knowledge_domain=knowledge_domain,
                raw_corpus_path=raw_corpus_path,
                max_batch_chars=max_batch_chars,
                process_all_batches=process_all_batches,
                max_batches=max_batches,
                live_log_path=str(live_log_path),
                progress_events=tuple(progress.events),
                duration_seconds=round(perf_counter() - start, 4),
                errors=(message,),
            )
            progress.emit(PROGRESS_FAILED, message=message)
            return result, (), timestamp

        progress.emit(
            PROGRESS_RAW_CORPUS_CREATED,
            message=f"Raw corpus saved to {raw_corpus_path}.",
        )

        pending_reviews = 0
        semantic_extractions = 0
        skipped_reviews = 0
        failed_batch_errors: list[CompileBatchError] = []
        consecutive_failures = 0
        openai_model = self._openai_model()
        stopped_early = False
        collected_extractions: list[TherapeuticFunctionExtraction] = []
        relevance_by_segment_id: dict[str, TherapeuticRelevanceDecision] = {}
        chunks_seen = 0
        chunks_skipped = 0
        chunks_extracted = 0
        skipped_by_reason: dict[str, int] = {}
        low_relevance_count = 0
        medium_relevance_count = 0
        high_relevance_count = 0

        gate_approved_segments: list[RawSourceSegment] = []
        for segment in corpus.segments:
            if not _is_gate_candidate(segment):
                continue
            chunks_seen += 1
            segment_decision = evaluate_chunk_relevance(
                source_id=source.source_id,
                chunk_id=segment.segment_id,
                text=segment.raw_text,
            )
            if not segment_decision.should_extract:
                chunks_skipped += 1
                _increment_skip_reason(skipped_by_reason, segment_decision.skip_reason)
                progress.emit(
                    PROGRESS_GATE_SKIPPED,
                    batch_id=segment.segment_id,
                    reviews_created_so_far=len(collected_extractions),
                    failed_batches_so_far=len(failed_batch_errors),
                    skipped_reviews_so_far=skipped_reviews,
                    message=(
                        f"Segment {segment.segment_id} skipped: "
                        f"{segment_decision.reasoning or segment_decision.skip_reason}"
                    ),
                )
                continue
            gate_approved_segments.append(segment)
            relevance_by_segment_id[segment.segment_id] = segment_decision

        batch_segments = _build_batch_segments(
            tuple(gate_approved_segments),
            source.source_id,
            max_batch_chars,
        )
        selected_batch_segments = self._select_batch_segments(
            batch_segments,
            process_all_batches=process_all_batches,
            max_batches=max_batches,
        )
        batch_total = len(selected_batch_segments)
        progress.emit(
            PROGRESS_BATCHES_BUILT,
            batch_total=batch_total,
            message=(
                f"Gate approved {len(gate_approved_segments)} segment(s); "
                f"built {len(batch_segments)} batch(es); processing {batch_total}."
            ),
        )

        for batch_index, batch_segment in enumerate(selected_batch_segments, start=1):
            progress.emit(
                PROGRESS_BATCH_STARTED,
                batch_index=batch_index,
                batch_total=batch_total,
                batch_id=batch_segment.segment_id,
                reviews_created_so_far=len(collected_extractions),
                failed_batches_so_far=len(failed_batch_errors),
                skipped_reviews_so_far=skipped_reviews,
                message=f"Batch {batch_index} / {batch_total} — extracting...",
            )

            batch_corpus = build_raw_source_corpus(corpus.source, (batch_segment,))
            try:
                gated_result = self._extract_batch_with_gate(
                    batch_corpus,
                    batch_segment.segment_id,
                )
                decision = gated_result.relevance_decision
                if not decision.should_extract or gated_result.extraction is None:
                    chunks_skipped += 1
                    _increment_skip_reason(
                        skipped_by_reason,
                        decision.skip_reason,
                    )
                    progress.emit(
                        PROGRESS_GATE_SKIPPED,
                        batch_index=batch_index,
                        batch_total=batch_total,
                        batch_id=batch_segment.segment_id,
                        reviews_created_so_far=len(collected_extractions),
                        failed_batches_so_far=len(failed_batch_errors),
                        skipped_reviews_so_far=skipped_reviews,
                        message=(
                            f"Batch {batch_index} / {batch_total} — skipped after extraction: "
                            f"{decision.reasoning or decision.skip_reason}"
                        ),
                    )
                    continue

                extraction = gated_result.extraction
                semantic_extractions += 1
                chunks_extracted += 1
                collected_extractions.append(extraction)
                relevance_by_segment_id[extraction.segment_id] = decision
                (
                    low_relevance_count,
                    medium_relevance_count,
                    high_relevance_count,
                ) = _increment_relevance_band(
                    decision=decision,
                    low_relevance_count=low_relevance_count,
                    medium_relevance_count=medium_relevance_count,
                    high_relevance_count=high_relevance_count,
                )
                consecutive_failures = 0
                progress.emit(
                    PROGRESS_BATCH_SUCCEEDED,
                    batch_index=batch_index,
                    batch_total=batch_total,
                    batch_id=batch_segment.segment_id,
                    reviews_created_so_far=len(collected_extractions),
                    failed_batches_so_far=len(failed_batch_errors),
                    skipped_reviews_so_far=skipped_reviews,
                    message=(
                        f"Batch {batch_index} / {batch_total} — extracted "
                        f"({decision.knowledge_kind}, score={decision.relevance_score:.2f})."
                    ),
                )
            except (SemanticExtractionAdapterError, ValueError, OSError) as exc:
                error_message = self._compile_error_message(exc)
                failed_batch_errors.append(
                    CompileBatchError(
                        batch_id=batch_segment.segment_id,
                        error_type=exc.__class__.__name__,
                        message=error_message,
                    )
                )
                consecutive_failures += 1
                progress.emit(
                    PROGRESS_BATCH_FAILED,
                    batch_index=batch_index,
                    batch_total=batch_total,
                    batch_id=batch_segment.segment_id,
                    reviews_created_so_far=len(collected_extractions),
                    failed_batches_so_far=len(failed_batch_errors),
                    skipped_reviews_so_far=skipped_reviews,
                    message=f"Batch {batch_index} / {batch_total} — {error_message}",
                )
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    stop_message = (
                        f"Stopped after {MAX_CONSECUTIVE_FAILURES} consecutive extraction failures."
                    )
                    progress.emit(
                        PROGRESS_STOPPED,
                        batch_index=batch_index,
                        batch_total=batch_total,
                        batch_id=batch_segment.segment_id,
                        reviews_created_so_far=len(collected_extractions),
                        failed_batches_so_far=len(failed_batch_errors),
                        skipped_reviews_so_far=skipped_reviews,
                        message=stop_message,
                    )
                    stopped_early = True
                    break

        failed_batches = len(failed_batch_errors)
        batches_processed = semantic_extractions + failed_batches
        consolidated_candidates = 0
        filtered_extractions = 0
        auto_approved = 0

        if collected_extractions and not defer_consolidation:
            (
                pending_reviews,
                skipped_reviews,
                consolidated_candidates,
                filtered_extractions,
                auto_approved,
            ) = self._queue_consolidated_reviews(
                collected_extractions,
                sources=(source,),
                knowledge_domain=knowledge_domain,
                force=force,
                progress=progress,
                review_mode=review_mode,
                auto_approve=auto_approve,
                force_allow_single_evidence_auto_approve=force_allow_single_evidence_auto_approve,
                relevance_by_segment_id=relevance_by_segment_id,
            )

        status = "compiled"
        if stopped_early:
            status = "partial" if collected_extractions else "failed"
        elif failed_batches and collected_extractions:
            status = "partial"
        elif failed_batches and not collected_extractions:
            status = "failed"

        if defer_consolidation:
            completion_message = (
                f"Scanned {chunks_seen} chunk(s); extracted {chunks_extracted}; "
                f"skipped {chunks_skipped}; {failed_batches} failed."
            )
        else:
            completion_message = (
                f"Compile completed: scanned {chunks_seen}, extracted {chunks_extracted}, "
                f"skipped {chunks_skipped} → {len(collected_extractions)} raw extractions → "
                f"{consolidated_candidates} consolidated candidates → "
                f"{pending_reviews} pending reviews "
                f"({failed_batches} failed, {skipped_reviews} duplicate reviews skipped)."
            )
        progress.emit(
            PROGRESS_COMPLETED if status != "failed" else PROGRESS_FAILED,
            batch_total=batch_total,
            reviews_created_so_far=pending_reviews,
            failed_batches_so_far=failed_batches,
            skipped_reviews_so_far=skipped_reviews,
            message=completion_message,
        )

        result = DocumentCompileResult(
            source_id=source.source_id,
            relative_path=source.relative_path,
            status=status,
            knowledge_domain=knowledge_domain,
            chunks_created=len(selected_batch_segments),
            semantic_extractions=semantic_extractions,
            pending_reviews=pending_reviews,
            approved_patterns=0,
            ctpc_generated=0,
            raw_corpus_path=raw_corpus_path,
            segment_count=len(corpus.segments),
            usable_batch_count=len(batch_segments),
            max_batch_chars=max_batch_chars,
            process_all_batches=process_all_batches,
            max_batches=max_batches,
            openai_model=openai_model,
            extraction_attempted=bool(selected_batch_segments),
            reviews_created=pending_reviews,
            raw_extractions=len(collected_extractions),
            filtered_extractions=filtered_extractions,
            consolidated_candidates=consolidated_candidates,
            auto_approved=auto_approved,
            books_processed=1,
            failed_batches=failed_batches,
            skipped_reviews=skipped_reviews,
            batches_processed=batches_processed,
            chunks_seen=chunks_seen,
            chunks_skipped=chunks_skipped,
            chunks_extracted=chunks_extracted,
            skipped_by_reason=_sorted_skip_reasons(skipped_by_reason),
            low_relevance_count=low_relevance_count,
            medium_relevance_count=medium_relevance_count,
            high_relevance_count=high_relevance_count,
            live_log_path=str(live_log_path),
            progress_events=tuple(progress.events),
            failed_batch_errors=tuple(failed_batch_errors),
            duration_seconds=round(perf_counter() - start, 4),
            errors=tuple(error.message for error in failed_batch_errors),
        )

        return result, tuple(collected_extractions), timestamp

    def _extract_batch_with_gate(
        self,
        batch_corpus: RawSourceCorpus,
        segment_id: str,
    ) -> SemanticExtractionResult:
        extract_gated = getattr(self.pipeline, "extract_from_corpus_gated", None)
        if callable(extract_gated):
            return extract_gated(batch_corpus, segment_id)

        extraction = self.pipeline.extract_from_corpus(batch_corpus, segment_id)
        decision = evaluate_chunk_relevance(
            source_id=extraction.source_id,
            chunk_id=segment_id,
            text=extraction.evidence_text,
        )
        return SemanticExtractionResult(
            relevance_decision=decision,
            extraction=extraction,
        )

    def _select_batch_segments(
        self,
        batch_segments: tuple[RawSourceSegment, ...],
        *,
        process_all_batches: bool,
        max_batches: int | None,
    ) -> tuple[RawSourceSegment, ...]:
        if max_batches is not None:
            return batch_segments[:max_batches]
        if process_all_batches:
            return batch_segments
        return batch_segments[:1]

    def _source_contexts(
        self,
        sources: tuple[KnowledgeLibrarySourceRecord, ...],
    ) -> dict[str, ConsolidationSourceContext]:
        return {
            source.source_id: ConsolidationSourceContext(
                source_id=source.source_id,
                source_family=source.family,
                domain=source.domain,
                title=source.title,
            )
            for source in sources
        }

    def _queue_consolidated_reviews(
        self,
        extractions: list[TherapeuticFunctionExtraction] | tuple[TherapeuticFunctionExtraction, ...],
        *,
        sources: tuple[KnowledgeLibrarySourceRecord, ...],
        knowledge_domain: str,
        force: bool,
        progress: CompileProgressTracker | None = None,
        progress_callback: Callable[[CompileProgressEvent], None] | None = None,
        scope_label: str = "",
        review_mode: str = DEFAULT_REVIEW_MODE,
        auto_approve: bool = False,
        force_allow_single_evidence_auto_approve: bool = False,
        relevance_by_segment_id: dict[str, TherapeuticRelevanceDecision] | None = None,
    ) -> tuple[int, int, int, int, int]:
        """Consolidate extractions and queue reviews. Returns pending, skipped, candidates, filtered, auto_approved."""
        extraction_list = list(extractions)
        if not extraction_list:
            return 0, 0, 0, 0, 0

        tracker = progress
        if tracker is None:
            safe_scope = re.sub(r"[^a-zA-Z0-9_]+", "_", scope_label or "compile_scope")
            live_log_path = (
                Path(self.paths.logs_dir)
                / f"consolidation_{self.timestamp_fn().replace(':', '').replace('+', '')}_{safe_scope}.jsonl"
            )
            tracker = CompileProgressTracker(
                source_id=scope_label or "compile_scope",
                live_log_path=live_log_path,
                timestamp_fn=self.timestamp_fn,
                callback=progress_callback,
            )

        tracker.emit(PROGRESS_CONSOLIDATING, message="Consolidating extracted knowledge...")
        consolidation = KnowledgeConsolidator().consolidate(
            extraction_list,
            source_contexts=self._source_contexts(sources),
            review_mode=review_mode,
        )
        candidates = consolidation.candidates
        tracker.emit(
            PROGRESS_CONSOLIDATED,
            message=(
                f"Merged {consolidation.raw_extractions} extractions "
                f"({consolidation.filtered_extractions} filtered) → "
                f"{len(candidates)} unique patterns."
            ),
        )
        tracker.emit(PROGRESS_SAVING_REVIEWS, message="Saving review queue...")

        source_type_by_id = {source.source_id: source.source_type for source in sources}
        pending_reviews = 0
        skipped_reviews = 0
        auto_approved = 0
        for candidate in candidates:
            if not force and self._existing_consolidated_review(candidate.candidate_id):
                skipped_reviews += 1
                tracker.emit(
                    PROGRESS_BATCH_SKIPPED,
                    batch_id=candidate.candidate_id,
                    reviews_created_so_far=pending_reviews,
                    skipped_reviews_so_far=skipped_reviews,
                    message=(
                        f"Consolidated pattern {candidate.canonical_name} already queued; skipping."
                    ),
                )
                continue

            anchor_source_type = source_type_by_id.get(
                candidate.source_ids[0] if candidate.source_ids else "",
                "text",
            )
            should_auto_approve = candidate_is_auto_approvable(
                candidate,
                source_type=anchor_source_type,
                knowledge_domain=knowledge_domain,
                auto_approve=auto_approve,
                force_allow_single_evidence=force_allow_single_evidence_auto_approve,
            )
            therapeutic_relevance = None
            if relevance_by_segment_id:
                decision = _relevance_for_candidate(candidate, relevance_by_segment_id)
                if decision is not None:
                    therapeutic_relevance = serialize_relevance_decision(decision)
            pending = self.pipeline.create_pending_consolidated_review(
                candidate,
                knowledge_domain=knowledge_domain,
                therapeutic_relevance=therapeutic_relevance,
            )
            if should_auto_approve:
                approved = self.pipeline.approve_review(
                    pending.review_id,
                    reviewer_id="knowledge_compiler_auto",
                    reviewer_notes="Auto-approved consolidated candidate meeting safety gates.",
                )
                self.pipeline.compile_approved_review(approved)
                auto_approved += 1
                tracker.emit(
                    PROGRESS_REVIEW_CREATED,
                    batch_id=candidate.candidate_id,
                    reviews_created_so_far=pending_reviews + auto_approved,
                    skipped_reviews_so_far=skipped_reviews,
                    message=f"Auto-approved consolidated pattern {candidate.canonical_name}.",
                )
            else:
                pending_reviews += 1
                tracker.emit(
                    PROGRESS_REVIEW_CREATED,
                    batch_id=candidate.candidate_id,
                    reviews_created_so_far=pending_reviews + auto_approved,
                    skipped_reviews_so_far=skipped_reviews,
                    message=f"Pending review created for {candidate.canonical_name}.",
                )
        return (
            pending_reviews,
            skipped_reviews,
            len(candidates),
            consolidation.filtered_extractions,
            auto_approved,
        )

    def _existing_consolidated_review(self, candidate_id: str) -> bool:
        review_dir = Path(self.paths.review_dir)
        if not review_dir.exists():
            return False
        for path in review_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("segment_id") == candidate_id:
                return True
            candidate_payload = payload.get("consolidated_candidate")
            if isinstance(candidate_payload, dict) and candidate_payload.get("candidate_id") == candidate_id:
                return True
        return False

    def _existing_review_for_batch(self, source_id: str, batch_id: str) -> bool:
        review_dir = Path(self.paths.review_dir)
        if not review_dir.exists():
            return False
        for path in review_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("source_id") == source_id and payload.get("segment_id") == batch_id:
                return True
        return False

    def _compile_live_log_path(
        self,
        source: KnowledgeLibrarySourceRecord,
        timestamp: str,
    ) -> Path:
        safe_timestamp = (
            timestamp.replace(":", "")
            .replace("+", "")
            .replace("-", "")
        )
        return (
            Path(self.paths.logs_dir)
            / f"{COMPILE_LIVE_LOG_PREFIX}_{safe_timestamp}_{source.source_id}.jsonl"
        )

    def _import_source_to_raw_corpus(
        self,
        source: KnowledgeLibrarySourceRecord,
    ) -> RawSourceCorpus:
        txt_path = Path(self.library_root) / source.relative_path
        source_record = KnowledgeSourceRecord(
            source_id=source.source_id,
            source_family=source.family,
            title=source.title,
            source_type="text",
            language="unknown",
            author=source.author,
        )
        corpus = import_txt_as_raw_corpus(txt_path, source_record)
        raw_corpus_path = Path(self.paths.raw_corpus_dir) / f"{source.source_id}.json"
        save_raw_corpus(corpus, raw_corpus_path)
        return corpus

    def _openai_model(self) -> str:
        adapter = getattr(self._pipeline, "extraction_adapter", None)
        model = getattr(adapter, "model", "")
        return model or resolve_openai_model()

    def _compile_error_message(self, exc: Exception) -> str:
        if isinstance(exc, SemanticExtractionMissingApiKeyError):
            return (
                f"{OPENAI_API_KEY_ENV_VAR} is missing. Raw corpus was created, "
                "but semantic extraction was not run."
            )
        return str(exc)

    def _compile_status_for_run_log(self, result: DocumentCompileResult) -> str:
        if result.status == "skipped":
            return "skipped"
        if result.status in {"failed", "unsupported"}:
            return "failed"
        if result.failed_batches and result.reviews_created:
            return "partial"
        if result.failed_batches:
            return "failed"
        return "success"

    def _compile_run_log_path(self, source: KnowledgeLibrarySourceRecord, timestamp: str) -> Path:
        safe_timestamp = (
            timestamp.replace(":", "")
            .replace("+", "")
            .replace("-", "")
        )
        return (
            Path(self.paths.logs_dir)
            / f"{COMPILE_RUN_LOG_PREFIX}_{safe_timestamp}_{source.source_id}.json"
        )

    def _write_compile_run_log(
        self,
        source: KnowledgeLibrarySourceRecord,
        result: DocumentCompileResult,
        timestamp: str,
    ) -> DocumentCompileResult:
        log_path = self._compile_run_log_path(source, timestamp)
        logged_result = replace(result, log_path=str(log_path))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": timestamp,
            "source_id": source.source_id,
            "source_type": source.source_type,
            "domain": source.domain,
            "family": source.family,
            "knowledge_domain": logged_result.knowledge_domain,
            "compile_scope": f"document:{source.source_id}",
            "raw_corpus_path": logged_result.raw_corpus_path,
            "segment_count": logged_result.segment_count,
            "usable_batch_count": logged_result.usable_batch_count,
            "max_batch_chars": logged_result.max_batch_chars,
            "process_all_batches": logged_result.process_all_batches,
            "max_batches": logged_result.max_batches,
            "openai_model": logged_result.openai_model,
            "extraction_attempted": logged_result.extraction_attempted,
            "reviews_created": logged_result.reviews_created,
            "raw_extractions": logged_result.raw_extractions,
            "filtered_extractions": logged_result.filtered_extractions,
            "consolidated_candidates": logged_result.consolidated_candidates,
            "auto_approved": logged_result.auto_approved,
            "books_processed": logged_result.books_processed,
            "failed_batches": logged_result.failed_batches,
            "skipped_reviews": logged_result.skipped_reviews,
            "batches_processed": logged_result.batches_processed,
            "live_log_path": logged_result.live_log_path,
            "status": self._compile_status_for_run_log(logged_result),
            "errors": [
                asdict(error)
                for error in logged_result.failed_batch_errors
            ]
            or list(logged_result.errors),
        }
        log_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return logged_result

    def _record_compile_result(
        self,
        source: KnowledgeLibrarySourceRecord,
        result: DocumentCompileResult,
        timestamp: str,
    ) -> DocumentCompileResult:
        result = replace(
            result,
            source_type=result.source_type or source.source_type,
            domain=result.domain or source.domain,
            family=result.family or source.family,
        )
        result = self._write_compile_run_log(source, result, timestamp)
        if result.status != "skipped":
            registry = self._load_compile_registry()
            registry[source.source_id] = CompileRegistryEntry(
                source_id=source.source_id,
                checksum=source.checksum,
                last_compiled_at=timestamp,
                compiler_version=COMPILER_VERSION,
                status=result.status,
                pending_reviews=result.pending_reviews,
                errors=result.errors,
            )
            self._save_compile_registry(registry)
            compile_status = result.status
            if result.status in {"compiled", "partial"} and result.pending_reviews > 0:
                compile_status = COMPILE_STATUS_PENDING_REVIEW
            elif result.status == "unsupported":
                compile_status = COMPILE_STATUS_UNSUPPORTED
            elif result.status == "failed":
                compile_status = COMPILE_STATUS_FAILED
            set_knowledge_library_source_compile_status(
                source.source_id,
                compile_status,
                self.library_root,
            )
        self._append_history(source, result, timestamp)
        return result

    def _load_compile_registry(self) -> dict[str, CompileRegistryEntry]:
        if not self.compile_registry_path.exists():
            return {}
        data = json.loads(self.compile_registry_path.read_text(encoding="utf-8"))
        return {
            source_id: CompileRegistryEntry(
                source_id=item["source_id"],
                checksum=item["checksum"],
                last_compiled_at=item["last_compiled_at"],
                compiler_version=item["compiler_version"],
                status=item["status"],
                pending_reviews=item.get("pending_reviews", 0),
                errors=tuple(item.get("errors", ())),
            )
            for source_id, item in data.items()
        }

    def _save_compile_registry(
        self,
        registry: dict[str, CompileRegistryEntry],
    ) -> None:
        self.compile_registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            source_id: asdict(entry)
            for source_id, entry in sorted(registry.items())
        }
        self.compile_registry_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _append_history(
        self,
        source: KnowledgeLibrarySourceRecord,
        result: DocumentCompileResult,
        timestamp: str,
    ) -> None:
        self.compile_history_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": timestamp,
            "document": source.relative_path,
            "source_id": source.source_id,
            "duration_seconds": result.duration_seconds,
            "status": result.status,
            "errors": list(result.errors),
        }
        with self.compile_history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _summary_from_results(
        self,
        *,
        scope: str,
        results: tuple[DocumentCompileResult, ...],
        started_at: float,
        scope_pending_reviews: int = 0,
        scope_consolidated_candidates: int = 0,
        scope_raw_extractions: int = 0,
        scope_filtered_extractions: int = 0,
        scope_auto_approved: int = 0,
        scope_books_processed: int = 0,
    ) -> CompileSummary:
        pending_reviews = scope_pending_reviews or sum(
            result.pending_reviews for result in results
        )
        return CompileSummary(
            scope=scope,
            documents_processed=len(results),
            chunks_created=sum(result.chunks_created for result in results),
            semantic_extractions=sum(result.semantic_extractions for result in results),
            pending_reviews=pending_reviews,
            approved_patterns=sum(result.approved_patterns for result in results) + (
                scope_auto_approved or sum(result.auto_approved for result in results)
            ),
            ctpc_generated=scope_auto_approved or sum(result.auto_approved for result in results),
            failed_documents=sum(
                1 for result in results if result.status in {"failed", "unsupported"}
            ),
            skipped_documents=sum(1 for result in results if result.status == "skipped"),
            raw_extractions=scope_raw_extractions or sum(
                result.raw_extractions for result in results
            ),
            filtered_extractions=scope_filtered_extractions or sum(
                result.filtered_extractions for result in results
            ),
            consolidated_candidates=scope_consolidated_candidates or sum(
                result.consolidated_candidates for result in results
            ),
            auto_approved=scope_auto_approved or sum(
                result.auto_approved for result in results
            ),
            books_processed=scope_books_processed or sum(
                result.books_processed for result in results
            ),
            chunks_seen=sum(result.chunks_seen for result in results),
            chunks_skipped=sum(result.chunks_skipped for result in results),
            chunks_extracted=sum(result.chunks_extracted for result in results),
            skipped_by_reason=_sorted_skip_reasons(
                {
                    reason: sum(
                        count
                        for result in results
                        for item_reason, count in result.skipped_by_reason
                        if item_reason == reason
                    )
                    for reason in {
                        item_reason
                        for result in results
                        for item_reason, _count in result.skipped_by_reason
                    }
                }
            ),
            low_relevance_count=sum(result.low_relevance_count for result in results),
            medium_relevance_count=sum(result.medium_relevance_count for result in results),
            high_relevance_count=sum(result.high_relevance_count for result in results),
            processing_time_seconds=round(perf_counter() - started_at, 4),
            document_results=results,
        )


def build_knowledge_compiler(
    *,
    library_root: str = DEFAULT_KNOWLEDGE_LIBRARY_ROOT,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    pipeline: KnowledgeFactoryPipeline | None = None,
) -> KnowledgeCompiler:
    """Build the default Knowledge Compiler service."""
    return KnowledgeCompiler(
        library_root=library_root,
        workspace_root=workspace_root,
        pipeline=pipeline,
    )
