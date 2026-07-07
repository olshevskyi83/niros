"""Knowledge Compiler — orchestrate library TXT sources into review artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable

from niros.knowledge_compiler_router import (
    AudioExtractCompiler,
    TextSemanticCompiler,
    route_knowledge_source,
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
from niros.openai_semantic_extraction_adapter import SemanticExtractionAdapterError
from niros.raw_corpus_io import save_raw_corpus
from niros.raw_source import RawSourceCorpus, RawSourceSegment, build_raw_source_corpus
from niros.source_registry import KnowledgeSourceRecord
from niros.txt_source_importer import import_txt_as_raw_corpus

COMPILER_VERSION = "knowledge_compiler_mvp_1"
COMPILE_REGISTRY_FILENAME = "compile_registry.json"
COMPILE_HISTORY_FILENAME = "compile_history.jsonl"
DEFAULT_MAX_BATCH_CHARS = 2000
MIN_MEANINGFUL_CHARS = 40
BATCH_SEPARATOR = "\n\n---\n\n"

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
    knowledge_domain: str = ""
    chunks_created: int = 0
    semantic_extractions: int = 0
    pending_reviews: int = 0
    approved_patterns: int = 0
    ctpc_generated: int = 0
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
    processing_time_seconds: float = 0.0
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
        self.paths = ensure_knowledge_workspace(workspace_root)
        self.pipeline = pipeline or KnowledgeFactoryPipeline.from_workspace_root(
            workspace_root,
            paths=self.paths,
        )
        self.timestamp_fn = timestamp_fn

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
    ) -> CompileSummary:
        source = self._resolve_source(source_id_or_path)
        start = perf_counter()
        result = self._compile_source(
            source,
            force=force,
            max_batch_chars=max_batch_chars,
        )
        return self._summary_from_results(
            scope=f"document:{source.source_id}",
            results=(result,),
            started_at=start,
        )

    def compile_family(
        self,
        domain: str,
        family: str,
        *,
        force: bool = False,
        max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
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
        )

    def compile_domain(
        self,
        domain: str,
        *,
        force: bool = False,
        max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
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
        )

    def compile_library(
        self,
        *,
        force: bool = False,
        max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
    ) -> CompileSummary:
        sources = list_knowledge_sources(self.library_root)
        return self._compile_sources(
            scope="library",
            sources=sources,
            force=force,
            max_batch_chars=max_batch_chars,
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
    ) -> CompileSummary:
        start = perf_counter()
        results = tuple(
            self._compile_source(
                source,
                force=force,
                max_batch_chars=max_batch_chars,
            )
            for source in sources
        )
        return self._summary_from_results(scope=scope, results=results, started_at=start)

    def _compile_source(
        self,
        source: KnowledgeLibrarySourceRecord,
        *,
        force: bool,
        max_batch_chars: int,
    ) -> DocumentCompileResult:
        start = perf_counter()
        timestamp = self.timestamp_fn()
        route = route_knowledge_source(source)
        if not route.supported:
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="unsupported",
                duration_seconds=round(perf_counter() - start, 4),
                errors=(route.unsupported_reason,),
            )
            self._record_compile_result(source, result, timestamp)
            return result

        knowledge_domain = route.knowledge_domain
        if not knowledge_domain:
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="failed",
                duration_seconds=round(perf_counter() - start, 4),
                errors=(f"Unsupported knowledge library domain: {source.domain}",),
            )
            self._record_compile_result(source, result, timestamp)
            return result

        registry = self._load_compile_registry()
        previous = registry.get(source.source_id)
        if (
            previous is not None
            and previous.checksum == source.checksum
            and previous.compiler_version == COMPILER_VERSION
            and not force
        ):
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="skipped",
                knowledge_domain=knowledge_domain,
                duration_seconds=round(perf_counter() - start, 4),
            )
            self._append_history(source, result, timestamp)
            return result

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
                duration_seconds=round(perf_counter() - start, 4),
                errors=adapter_result.errors,
            )
            self._record_compile_result(source, result, timestamp)
            return result

        if not isinstance(route.compiler, TextSemanticCompiler):
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="failed",
                knowledge_domain=knowledge_domain,
                duration_seconds=round(perf_counter() - start, 4),
                errors=("No compiler adapter is available for this source.",),
            )
            self._record_compile_result(source, result, timestamp)
            return result

        try:
            corpus = self._import_source_to_raw_corpus(source)
            batch_segments = _build_batch_segments(
                corpus.segments,
                source.source_id,
                max_batch_chars,
            )
            pending_reviews = 0
            semantic_extractions = 0
            for batch_segment in batch_segments:
                batch_corpus = build_raw_source_corpus(corpus.source, (batch_segment,))
                extraction = self.pipeline.extract_from_corpus(
                    batch_corpus,
                    batch_segment.segment_id,
                )
                semantic_extractions += 1
                self.pipeline.create_pending_review(
                    extraction,
                    knowledge_domain=knowledge_domain,
                )
                pending_reviews += 1
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="compiled",
                knowledge_domain=knowledge_domain,
                chunks_created=len(batch_segments),
                semantic_extractions=semantic_extractions,
                pending_reviews=pending_reviews,
                approved_patterns=0,
                ctpc_generated=0,
                duration_seconds=round(perf_counter() - start, 4),
            )
        except (SemanticExtractionAdapterError, ValueError, OSError) as exc:
            result = DocumentCompileResult(
                source_id=source.source_id,
                relative_path=source.relative_path,
                status="failed",
                knowledge_domain=knowledge_domain,
                duration_seconds=round(perf_counter() - start, 4),
                errors=(str(exc),),
            )

        self._record_compile_result(source, result, timestamp)
        return result

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

    def _record_compile_result(
        self,
        source: KnowledgeLibrarySourceRecord,
        result: DocumentCompileResult,
        timestamp: str,
    ) -> None:
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
            if result.status == "compiled" and result.pending_reviews > 0:
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
    ) -> CompileSummary:
        return CompileSummary(
            scope=scope,
            documents_processed=len(results),
            chunks_created=sum(result.chunks_created for result in results),
            semantic_extractions=sum(result.semantic_extractions for result in results),
            pending_reviews=sum(result.pending_reviews for result in results),
            approved_patterns=sum(result.approved_patterns for result in results),
            ctpc_generated=sum(result.ctpc_generated for result in results),
                  failed_documents=sum(
                      1 for result in results if result.status in {"failed", "unsupported"}
                  ),
            skipped_documents=sum(1 for result in results if result.status == "skipped"),
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
