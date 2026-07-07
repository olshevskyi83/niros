"""Tests for Knowledge Compiler orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from niros.human_review_workflow import HumanReviewWorkflow
from niros.knowledge_compiler import KnowledgeCompiler
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_library import ensure_knowledge_library, list_knowledge_sources
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id


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
        text
        or (
            "This paragraph contains enough meaningful therapeutic source text "
            "for one deterministic compiler batch."
        ),
        encoding="utf-8",
    )
    return path


class FakePipeline:
    def __init__(self, workspace_root: Path) -> None:
        self.paths = ensure_knowledge_workspace(str(workspace_root))
        self.review_workflow = HumanReviewWorkflow(paths=self.paths)
        self.extracted_segment_ids: list[str] = []
        self.review_domains: list[str] = []

    def extract_from_corpus(self, corpus, segment_id):
        self.extracted_segment_ids.append(segment_id)
        therapeutic_function = "self_compassion"
        psychological_function = "reduce self-criticism"
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

    def create_pending_review(self, extraction, *, knowledge_domain):
        self.review_domains.append(knowledge_domain)
        return self.review_workflow.create_pending_review(
            extraction,
            knowledge_domain=knowledge_domain,
        )


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
    assert summary.pending_reviews == 2
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
    assert summary.pending_reviews == 2
    assert summary.failed_documents == 1
    assert pipeline.review_domains == [
        KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
        KNOWLEDGE_DOMAIN_VOCAL_ICARO,
    ]


def test_psychedelic_research_compiles_as_psychotherapy_tle(tmp_path: Path) -> None:
    compiler, pipeline, library_root, _ = _compiler(tmp_path)
    _write_source(library_root, "psychedelic_research", "johns_hopkins", "study.txt")
    source = list_knowledge_sources(str(library_root))[0]

    summary = compiler.compile_document(source.source_id)

    assert summary.failed_documents == 0
    assert summary.pending_reviews == 1
    assert pipeline.review_domains == [KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE]


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
