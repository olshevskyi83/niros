"""Tests for Knowledge Compiler orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from niros.human_review_workflow import HumanReviewWorkflow
from niros.knowledge_compiler import (
    KnowledgeCompiler,
    PROGRESS_BATCHES_BUILT,
    PROGRESS_COMPLETED,
    PROGRESS_CONSOLIDATED,
    PROGRESS_CONSOLIDATING,
    PROGRESS_GATE_SKIPPED,
    PROGRESS_STARTED,
    PROGRESS_STOPPED,
)
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_library import (
    ensure_knowledge_library,
    index_knowledge_library_sources,
    list_knowledge_sources,
)
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.openai_semantic_extraction_adapter import SemanticExtractionResult
from niros.semantic_therapeutic_gate import evaluate_chunk_relevance
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id


def _mechanism_paragraph(index: int = 1) -> str:
    return (
        f"Paragraph {index}: When a client notices urges to avoid painful feelings, "
        "short-term relief appears but long-term suffering increases because "
        "experiential avoidance moves them away from valued action. "
        "This practice teaches willingness to feel emotions instead of fighting them."
    )


def _write_source(
    library_root: Path,
    domain: str,
    family: str,
    filename: str,
    text: str | None = None,
) -> Path:
    path = library_root / domain / family / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text or _mechanism_paragraph(1),
        encoding="utf-8",
    )
    return path


class FakePipeline:
    def __init__(
        self,
        workspace_root: Path,
        *,
        fail_on_segment: str = "",
        fail_always: bool = False,
    ) -> None:
        self.paths = ensure_knowledge_workspace(str(workspace_root))
        self.review_workflow = HumanReviewWorkflow(paths=self.paths)
        self.extracted_segment_ids: list[str] = []
        self.review_domains: list[str] = []
        self.fail_on_segment = fail_on_segment
        self.fail_always = fail_always

    def _build_extraction(self, corpus, segment_id) -> TherapeuticFunctionExtraction:
        therapeutic_function = "accept emotions"
        psychological_function = "reduce experiential avoidance"
        return TherapeuticFunctionExtraction(
            extraction_id=build_extraction_id(
                corpus.source.source_id,
                segment_id,
                therapeutic_function,
                psychological_function,
            ),
            source_id=corpus.source.source_id,
            segment_id=segment_id,
            therapeutic_function=therapeutic_function,
            psychological_function=psychological_function,
            evidence_text=corpus.segments[0].raw_text,
            generation_rules=("Use gentle phrasing.",),
            voice_rules=("Use calm pacing.",),
            confidence=0.85,
            extractor="fake",
        )

    def extract_from_corpus_gated(self, corpus, segment_id):
        self.extracted_segment_ids.append(segment_id)
        if self.fail_always or (
            self.fail_on_segment and self.fail_on_segment in segment_id
        ):
            raise ValueError("fake OpenAI extraction failed")
        text = corpus.segments[0].raw_text
        decision = evaluate_chunk_relevance(
            source_id=corpus.source.source_id,
            chunk_id=segment_id,
            text=text,
        )
        if not decision.should_extract:
            return SemanticExtractionResult(relevance_decision=decision, extraction=None)
        return SemanticExtractionResult(
            relevance_decision=decision,
            extraction=self._build_extraction(corpus, segment_id),
        )

    def extract_from_corpus(self, corpus, segment_id):
        result = self.extract_from_corpus_gated(corpus, segment_id)
        if result.extraction is None:
            raise ValueError(result.relevance_decision.skip_reason or "skipped by gate")
        return result.extraction

    def create_pending_review(self, extraction, *, knowledge_domain):
        self.review_domains.append(knowledge_domain)
        return self.review_workflow.create_pending_review(
            extraction,
            knowledge_domain=knowledge_domain,
        )

    def create_pending_consolidated_review(
        self,
        candidate,
        *,
        knowledge_domain,
        therapeutic_relevance=None,
    ):
        self.review_domains.append(knowledge_domain)
        return self.review_workflow.create_pending_consolidated_review(
            candidate,
            knowledge_domain=knowledge_domain,
            therapeutic_relevance=therapeutic_relevance,
        )

    def approve_review(self, review_id, *, reviewer_id="", reviewer_notes=""):
        return self.review_workflow.approve(
            review_id,
            reviewer_id=reviewer_id,
            reviewer_notes=reviewer_notes,
        )

    def compile_approved_review(self, review_record):
        from niros.ctpc_compiler import CTPCCompiler

        return CTPCCompiler(paths=self.paths).compile_review(review_record)


def _compiler(tmp_path: Path) -> tuple[KnowledgeCompiler, FakePipeline, Path, Path]:
    library_root = tmp_path / "knowledge_library"
    workspace_root = tmp_path / "knowledge_factory"
    ensure_knowledge_library(str(library_root))
    ensure_knowledge_workspace(str(workspace_root))
    pipeline = FakePipeline(workspace_root)
    compiler = KnowledgeCompiler(
        library_root=str(library_root),
        workspace_root=str(workspace_root),
        pipeline=pipeline,
        timestamp_fn=lambda: "2026-07-07T18:00:00+00:00",
    )
    return compiler, pipeline, library_root, workspace_root


def _compiler_with_pipeline(
    tmp_path: Path,
    pipeline: FakePipeline,
) -> tuple[KnowledgeCompiler, Path, Path]:
    library_root = tmp_path / "knowledge_library"
    workspace_root = tmp_path / "knowledge_factory"
    ensure_knowledge_library(str(library_root))
    ensure_knowledge_workspace(str(workspace_root))
    compiler = KnowledgeCompiler(
        library_root=str(library_root),
        workspace_root=str(workspace_root),
        pipeline=pipeline,
        timestamp_fn=lambda: "2026-07-07T18:00:00+00:00",
    )
    return compiler, library_root, workspace_root


def test_compile_document_creates_raw_corpus_and_pending_review(tmp_path: Path) -> None:
    compiler, pipeline, library_root, workspace_root = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id)

    assert summary.documents_processed == 1
    assert summary.chunks_created == 1
    assert summary.semantic_extractions == 1
    assert summary.pending_reviews == 1
    assert summary.ctpc_generated == 0
    assert summary.failed_documents == 0
    assert pipeline.review_domains == [KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE]
    assert Path(workspace_root, "raw_corpus", f"{source.source_id}.json").exists()
    assert list(Path(workspace_root, "review").glob("*.json"))
    result = summary.document_results[0]
    assert result.raw_corpus_path
    assert result.segment_count == 1
    assert result.usable_batch_count == 1
    assert result.reviews_created == 1
    assert result.failed_batches == 0
    assert Path(result.log_path).exists()


def test_compile_family_compiles_only_matching_family(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    _write_source(library_root, "psychotherapy", "cft", "cft.txt")

    summary = compiler.compile_family("psychotherapy", "act")

    assert summary.documents_processed == 1
    assert len(pipeline.extracted_segment_ids) == 1
    assert summary.document_results[0].relative_path == "psychotherapy/act/act.txt"


def test_compile_domain_compiles_domain_sources(tmp_path: Path) -> None:
    compiler, _, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    _write_source(library_root, "psychotherapy", "cft", "cft.txt")
    _write_source(library_root, "vocal_icaro", "maria_sabina", "chants.txt")

    summary = compiler.compile_domain("psychotherapy")

    assert summary.documents_processed == 2
    assert summary.raw_extractions == 2
    assert summary.consolidated_candidates == 1
    assert summary.pending_reviews == 1
    assert summary.books_processed == 2
    assert all(
        result.knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
        for result in summary.document_results
    )


def test_compile_library_compiles_supported_domains_and_reports_failures(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    _write_source(library_root, "vocal_icaro", "maria_sabina", "chants.txt")
    _write_source(library_root, "music_session", "maps", "music.txt")

    summary = compiler.compile_library()

    assert summary.documents_processed == 3
    assert summary.raw_extractions == 2
    assert summary.consolidated_candidates == 1
    assert summary.pending_reviews == 1
    assert summary.books_processed == 3
    assert summary.failed_documents == 1
    assert pipeline.review_domains == [KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE]


def test_psychedelic_research_compiles_as_psychotherapy_tle(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychedelic_research", "johns_hopkins", "study.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id)

    assert summary.failed_documents == 0
    assert summary.pending_reviews == 1
    assert pipeline.review_domains == [KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE]


def test_long_source_id_consolidated_review_uses_short_filename(tmp_path: Path) -> None:
    compiler, _, library_root, workspace_root = _compiler(tmp_path)
    long_name = (
        "source_psychotherapy_psychedelic_research_johns_hopkins_"
        "longitudinal_psilocybin_assisted_therapy_study_volume_one"
    )
    source_dir = library_root / "psychedelic_research" / "johns_hopkins"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / f"{long_name}.txt").write_text(
        (
            "Experiential avoidance occurs when a person tries to escape painful thoughts "
            "and feelings. This may reduce distress briefly, but over time it narrows "
            "behavior and pulls the person away from valued action."
        ),
        encoding="utf-8",
    )
    index_knowledge_library_sources(str(library_root))
    source = next(
        item
        for item in list_knowledge_sources(str(library_root))
        if item.filename == f"{long_name}.txt"
    )

    summary = compiler.compile_document(source.source_id)
    result = summary.document_results[0]

    assert result.pending_reviews == 1
    review_dir = workspace_root / "review"
    review_files = list(review_dir.glob("review_candidate_*.json"))
    assert len(review_files) == 1
    assert len(review_files[0].name) < 200


def test_audio_extract_document_compile_creates_pending_vocal_review_proposal(
    tmp_path: Path,
) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    audio_path = Path(
        library_root,
        "vocal_icaro",
        "maria_sabina",
        "audio_extracts",
        "01_maria_sabina.audio_extract.json",
    )
    audio_path.parent.mkdir(parents=True)
    audio_path.write_text(
        json.dumps(
            {
                "tempo": 82,
                "pitch_range": "low_to_mid",
                "motifs": ["descending_phrase"],
                "pauses": [{"duration_seconds": 1.2}],
            }
        ),
        encoding="utf-8",
    )
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id)

    assert summary.failed_documents == 0
    assert summary.pending_reviews == 1
    assert summary.document_results[0].knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO
    review_files = list(Path(compiler.paths.review_dir).glob("review_audio_vocal_*.json"))
    assert review_files
    review_payload = json.loads(review_files[0].read_text(encoding="utf-8"))
    assert review_payload["review_type"] == "audio_vocal_extraction"
    assert review_payload["source_type"] == "audio_extract"
    assert review_payload["knowledge_domain"] == KNOWLEDGE_DOMAIN_VOCAL_ICARO
    assert review_payload["original_extraction"]["features"]["tempo_bpm"] == 82
    assert pipeline.review_domains == []


def test_incremental_compile_skips_unchanged_source(tmp_path: Path) -> None:
    compiler, pipeline, library_root, workspace_root = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    first = compiler.compile_document(source.source_id)
    second = compiler.compile_document(source.source_id)

    assert first.pending_reviews == 1
    assert second.skipped_documents == 1
    assert second.pending_reviews == 0
    assert len(pipeline.extracted_segment_ids) == 1
    assert second.document_results[0].status == "skipped"
    assert Path(second.document_results[0].log_path).exists()
    registry = json.loads(Path(workspace_root, "registry", "compile_registry.json").read_text())
    assert registry[source.source_id]["checksum"] == source.checksum
    assert registry[source.source_id]["compiler_version"]


def test_force_recompiles_unchanged_source(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    compiler.compile_document(source.source_id)
    summary = compiler.compile_document(source.source_id, force=True)

    assert summary.skipped_documents == 0
    assert summary.pending_reviews == 1
    assert len(pipeline.extracted_segment_ids) == 2


def test_compile_history_is_written(tmp_path: Path) -> None:
    compiler, _, library_root, workspace_root = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    compiler.compile_document(source.source_id)

    history_path = Path(workspace_root, "logs", "compile_history.jsonl")
    payload = json.loads(history_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["source_id"] == source.source_id
    assert payload["document"] == "psychotherapy/act/act.txt"
    assert payload["status"] == "compiled"


def test_compile_writes_structured_log_on_success(tmp_path: Path) -> None:
    compiler, _, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id, max_batch_chars=500)
    log_payload = json.loads(
        Path(summary.document_results[0].log_path).read_text(encoding="utf-8")
    )

    assert log_payload["source_id"] == source.source_id
    assert log_payload["source_type"] == "text"
    assert log_payload["domain"] == "psychotherapy"
    assert log_payload["knowledge_domain"] == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    assert log_payload["raw_corpus_path"]
    assert log_payload["segment_count"] == 1
    assert log_payload["usable_batch_count"] == 1
    assert log_payload["max_batch_chars"] == 500
    assert log_payload["extraction_attempted"] is True
    assert log_payload["reviews_created"] == 1
    assert log_payload["failed_batches"] == 0
    assert log_payload["status"] == "success"


def test_process_all_batches_true_creates_review_for_each_usable_batch(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(
        library_root,
        "psychotherapy",
        "act",
        "act.txt",
        text=(
            f"{_mechanism_paragraph(1)}\n\n"
            f"{_mechanism_paragraph(2)}"
        ),
    )
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        process_all_batches=True,
    )

    assert summary.document_results[0].usable_batch_count == 2
    assert summary.pending_reviews == 1
    assert summary.document_results[0].raw_extractions == 2
    assert summary.document_results[0].consolidated_candidates == 1
    assert len(pipeline.extracted_segment_ids) == 2


def test_process_all_batches_false_creates_one_review(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(
        library_root,
        "psychotherapy",
        "act",
        "act.txt",
        text=(
            f"{_mechanism_paragraph(1)}\n\n"
            f"{_mechanism_paragraph(2)}"
        ),
    )
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        process_all_batches=False,
    )

    assert summary.document_results[0].usable_batch_count == 2
    assert summary.chunks_created == 1
    assert summary.pending_reviews == 1
    assert summary.document_results[0].raw_extractions == 1
    assert summary.document_results[0].consolidated_candidates == 1
    assert len(pipeline.extracted_segment_ids) == 1


def test_compile_writes_log_on_extraction_failure(tmp_path: Path) -> None:
    workspace_root = tmp_path / "knowledge_factory"
    pipeline = FakePipeline(workspace_root, fail_on_segment="batch_001")
    compiler, library_root, _ = _compiler_with_pipeline(tmp_path, pipeline)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id)
    result = summary.document_results[0]
    log_payload = json.loads(Path(result.log_path).read_text(encoding="utf-8"))

    assert result.status == "failed"
    assert result.failed_batches == 1
    assert result.failed_batch_errors[0].error_type == "ValueError"
    assert log_payload["status"] == "failed"
    assert log_payload["failed_batches"] == 1
    assert log_payload["errors"][0]["batch_id"].endswith("batch_001")


def test_missing_api_key_failure_is_structured_after_raw_import(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    library_root = tmp_path / "knowledge_library"
    workspace_root = tmp_path / "knowledge_factory"
    ensure_knowledge_library(str(library_root))
    ensure_knowledge_workspace(str(workspace_root))
    compiler = KnowledgeCompiler(
        library_root=str(library_root),
        workspace_root=str(workspace_root),
        timestamp_fn=lambda: "2026-07-07T18:00:00+00:00",
    )
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id)
    result = summary.document_results[0]

    assert Path(result.raw_corpus_path).exists()
    assert result.extraction_attempted is True
    assert result.reviews_created == 0
    assert result.failed_batches == 1
    assert result.errors == (
        "OPENAI_API_KEY is missing. Raw corpus was created, but semantic extraction was not run.",
    )
    assert Path(result.log_path).exists()
    assert Path(result.live_log_path).exists()


def test_compiler_emits_progress_events_and_writes_jsonl_log(tmp_path: Path) -> None:
    compiler, _, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]
    events: list = []

    summary = compiler.compile_document(
        source.source_id,
        progress_callback=events.append,
    )
    result = summary.document_results[0]

    assert events[0].event == PROGRESS_STARTED
    assert any(event.event == PROGRESS_BATCHES_BUILT for event in events)
    assert any(event.event == PROGRESS_CONSOLIDATING for event in events)
    assert any(event.event == PROGRESS_CONSOLIDATED for event in events)
    assert any(event.event == PROGRESS_COMPLETED for event in events)
    assert result.progress_events
    assert Path(result.live_log_path).exists()
    log_lines = Path(result.live_log_path).read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == len(result.progress_events)
    assert json.loads(log_lines[0])["event"] == PROGRESS_STARTED


def test_max_batches_limits_processed_batches(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    paragraphs = "\n\n".join(
        _mechanism_paragraph(index)
        for index in range(1, 6)
    )
    _write_source(library_root, "psychotherapy", "act", "act.txt", text=paragraphs)
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        max_batches=3,
        force=True,
    )
    result = summary.document_results[0]

    assert result.usable_batch_count >= 3
    assert result.batches_processed == 3
    assert summary.pending_reviews == 1
    assert result.raw_extractions == 3
    assert result.consolidated_candidates == 1
    assert len(pipeline.extracted_segment_ids) == 3


def test_duplicate_review_prevention_skips_existing_consolidated_candidate(
    tmp_path: Path,
) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(
        library_root,
        "psychotherapy",
        "act",
        "act.txt",
        text=(
            f"{_mechanism_paragraph(1)}\n\n"
            f"{_mechanism_paragraph(2)}"
        ),
    )
    source = list_knowledge_sources(str(library_root))[0]

    first = compiler.compile_document(source.source_id, max_batch_chars=80, max_batches=2)
    assert first.pending_reviews == 1
    assert first.document_results[0].raw_extractions == 2
    compiler.compile_registry_path.unlink()
    second = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        max_batches=2,
        force=False,
    )
    result = second.document_results[0]

    assert result.skipped_reviews == 1
    assert result.pending_reviews == 0
    assert len(pipeline.extracted_segment_ids) == 4


def test_repeated_openai_failures_stop_after_threshold(tmp_path: Path) -> None:
    workspace_root = tmp_path / "knowledge_factory"
    pipeline = FakePipeline(workspace_root, fail_always=True)
    compiler, library_root, _ = _compiler_with_pipeline(tmp_path, pipeline)
    paragraphs = "\n\n".join(_mechanism_paragraph(index) for index in range(1, 8))
    _write_source(library_root, "psychotherapy", "act", "act.txt", text=paragraphs)
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        max_batches=10,
        force=True,
    )
    result = summary.document_results[0]

    assert result.failed_batches == 3
    assert result.reviews_created == 0
    assert any(event.event == PROGRESS_STOPPED for event in result.progress_events)


def test_three_acceptance_batches_produce_one_consolidated_review(tmp_path: Path) -> None:
    compiler, _, library_root, _ = _compiler(tmp_path)
    paragraphs = "\n\n".join(
        _mechanism_paragraph(index)
        for index in range(1, 6)
    )
    _write_source(library_root, "psychotherapy", "act", "act.txt", text=paragraphs)
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        max_batches=3,
        force=True,
    )

    assert summary.raw_extractions == 3
    assert summary.consolidated_candidates == 1
    assert summary.pending_reviews == 1
    assert summary.filtered_extractions == 0


class FrontMatterFakePipeline(FakePipeline):
    def extract_from_corpus(self, corpus, segment_id):
        self.extracted_segment_ids.append(segment_id)
        therapeutic_function = "accept emotions"
        psychological_function = ""
        return TherapeuticFunctionExtraction(
            extraction_id=build_extraction_id(
                corpus.source.source_id,
                segment_id,
                therapeutic_function,
                psychological_function,
            ),
            source_id=corpus.source.source_id,
            segment_id=segment_id,
            therapeutic_function=therapeutic_function,
            psychological_function=psychological_function,
            evidence_text=(
                "Copyright 2024 Example Publisher. ISBN 978-0-000-0000-0. "
                "All rights reserved. Table of contents."
            ),
            generation_rules=("Use gentle phrasing.",),
            voice_rules=("Use calm pacing.",),
            confidence=0.85,
            extractor="fake",
        )


def test_front_matter_batch_produces_no_reviews(tmp_path: Path) -> None:
    workspace_root = tmp_path / "knowledge_factory"
    pipeline = FrontMatterFakePipeline(workspace_root)
    compiler, library_root, _ = _compiler_with_pipeline(tmp_path, pipeline)
    _write_source(
        library_root,
        "psychotherapy",
        "act",
        "act.txt",
        text=(
            "Copyright 2024 Example Publisher. ISBN 978-0-000-0000-0. "
            "All rights reserved. Table of contents."
        ),
    )
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id, force=True)
    result = summary.document_results[0]

    assert pipeline.extracted_segment_ids == []
    assert result.chunks_skipped == 1
    assert result.raw_extractions == 0
    assert summary.consolidated_candidates == 0
    assert summary.pending_reviews == 0
    assert any(event.event == PROGRESS_GATE_SKIPPED for event in result.progress_events)


def test_auto_approve_off_creates_pending_review(tmp_path: Path) -> None:
    compiler, _, library_root, workspace_root = _compiler(tmp_path)
    paragraphs = "\n\n".join(
        _mechanism_paragraph(index)
        for index in range(1, 4)
    )
    _write_source(library_root, "psychotherapy", "act", "act.txt", text=paragraphs)
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        max_batches=3,
        force=True,
        auto_approve=False,
    )

    assert summary.pending_reviews == 1
    assert summary.auto_approved == 0
    assert list((workspace_root / "review").glob("*.json"))


def test_auto_approve_on_approves_when_gates_pass(tmp_path: Path) -> None:
    compiler, _, library_root, workspace_root = _compiler(tmp_path)
    paragraphs = "\n\n".join(
        _mechanism_paragraph(index)
        for index in range(1, 4)
    )
    _write_source(library_root, "psychotherapy", "act", "act.txt", text=paragraphs)
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=80,
        max_batches=3,
        force=True,
        auto_approve=True,
        force_allow_single_evidence_auto_approve=True,
    )

    assert summary.auto_approved == 1
    assert summary.pending_reviews == 0
    assert list((workspace_root / "ctpc").rglob("*.json"))


def test_skipped_chunks_do_not_call_extraction_adapter(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(
        library_root,
        "psychotherapy",
        "act",
        "act.txt",
        text="ACT uses acceptance and values.",
    )
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id, force=True)

    assert pipeline.extracted_segment_ids == []
    assert summary.chunks_skipped == 1
    assert summary.raw_extractions == 0


def test_relevant_chunk_creates_review_with_relevance_metadata(tmp_path: Path) -> None:
    compiler, _, library_root, workspace_root = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "act.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id, force=True)
    result = summary.document_results[0]

    assert result.chunks_extracted == 1
    assert summary.pending_reviews == 1
    review_path = next((workspace_root / "review").glob("*.json"))
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    relevance = payload["therapeutic_relevance"]
    assert relevance["relevance_score"] > 0.0
    assert relevance["knowledge_kind"]
    assert relevance["gate_reasoning"] or relevance["reasoning"]
    assert relevance["why_extracted"]


def test_keyword_only_act_chunk_produces_zero_candidates(tmp_path: Path) -> None:
    compiler, _, library_root, _ = _compiler(tmp_path)
    _write_source(
        library_root,
        "psychotherapy",
        "act",
        "keyword_only.txt",
        text="ACT uses acceptance and values.",
    )
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id, force=True)

    assert summary.raw_extractions == 0
    assert summary.consolidated_candidates == 0
    assert ("keyword_only", 1) in summary.skipped_by_reason


def test_real_mechanism_chunk_produces_one_candidate(tmp_path: Path) -> None:
    compiler, _, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychotherapy", "act", "mechanism.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id, force=True)

    assert summary.raw_extractions == 1
    assert summary.consolidated_candidates == 1


def test_compile_summary_includes_skipped_and_extracted_counts(tmp_path: Path) -> None:
    compiler, _, library_root, _ = _compiler(tmp_path)
    _write_source(
        library_root,
        "psychotherapy",
        "act",
        "mixed.txt",
        text=(
            f"{_mechanism_paragraph(1)}\n\n"
            "ACT uses acceptance and values.\n\n"
            "Copyright 2024 Example Publisher. All rights reserved."
        ),
    )
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(
        source.source_id,
        max_batch_chars=500,
        max_batches=5,
        force=True,
    )

    assert summary.chunks_seen >= 2
    assert summary.chunks_skipped >= 1
    assert summary.chunks_extracted >= 1
    assert summary.skipped_by_reason
