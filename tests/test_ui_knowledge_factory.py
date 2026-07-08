"""Tests for Knowledge Factory UI helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

import niros.ui_knowledge_factory as ui_knowledge_factory
from niros.human_review_workflow import (
    REVIEW_STATUS_PENDING,
    HumanReviewError,
    HumanReviewRecord,
    HumanReviewWorkflow,
)
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_UNKNOWN,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_library import ensure_knowledge_library
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id
from niros.knowledge_compiler import DocumentCompileResult
from niros.ui_knowledge_factory import (
    assign_review_domain_for_ui,
    approve_review_for_ui,
    build_batch_groups,
    compile_progress_ui_summary,
    compile_summary_ui_funnel,
    count_knowledge_library_sources_by_family,
    filter_usable_segments,
    import_knowledge_source_for_ui,
    import_txt_for_ui,
    knowledge_domain_for_library_source,
    list_extraction_results_for_ui,
    list_knowledge_library_sources_for_ui,
    list_latest_ctpc_patterns,
    list_tle_eligible_ctpc_patterns,
    list_review_records,
    parse_max_batches_option,
    parse_review_mode_option,
    archive_pending_reviews_for_ui,
    DEFAULT_REVIEW_MODE_UI_OPTION,
    REVIEW_MODE_UI_OPTIONS,
    load_review_for_ui,
    parse_multiline_field,
    reject_review_for_ui,
    request_changes_for_ui,
    resolve_txt_input_path,
    review_can_be_approved,
    review_is_actionable,
    run_library_source_extraction_for_ui,
    suggested_action_for_review,
    summarize_workspace,
)


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    source_id = overrides.get("source_id", "source_001")
    segment_id = overrides.get("segment_id", "source_001_segment_001")
    therapeutic_function = overrides.get("therapeutic_function", "self_compassion")
    psychological_function = overrides.get("psychological_function", "")
    base = {
        "extraction_id": build_extraction_id(
            source_id,
            segment_id,
            therapeutic_function,
            psychological_function,
        ),
        "source_id": source_id,
        "segment_id": segment_id,
        "therapeutic_function": therapeutic_function,
        "psychological_function": psychological_function,
        "evidence_text": "Evidence text long enough for validation requirements.",
        "generation_rules": ("Use gentle tone.",),
        "voice_rules": ("Slow pace.",),
        "symbolic_elements": ("heart", "water"),
        "confidence": 0.85,
        "extractor": "openai",
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def _create_pending_review(
    tmp_path: Path,
    *,
    knowledge_domain: str = KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
) -> str:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    workflow = HumanReviewWorkflow(paths=paths)
    extraction = _extraction()
    record = workflow.create_pending_review(
        extraction,
        knowledge_domain=knowledge_domain,
    )
    return record.review_id


def test_summarize_workspace_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "knowledge_factory"
    library_root = tmp_path / "knowledge_library"
    paths = ensure_knowledge_workspace(str(root))
    ensure_knowledge_library(str(library_root))
    monkeypatch.setattr(
        ui_knowledge_factory,
        "DEFAULT_KNOWLEDGE_LIBRARY_ROOT",
        str(library_root),
    )
    Path(library_root, "psychotherapy", "act", "sample.txt").write_text(
        "Sample incoming file.",
        encoding="utf-8",
    )
    Path(paths.raw_corpus_dir, "source_001.json").write_text("{}", encoding="utf-8")
    Path(paths.ctpc_dir, "psychotherapy_tle", "ctp_example.json").write_text(
        "{}",
        encoding="utf-8",
    )
    _create_pending_review(tmp_path)

    summary = summarize_workspace(str(root))

    assert summary.incoming_files == 1
    assert summary.raw_corpus_count == 1
    assert summary.pending_review_count == 1
    assert summary.approved_review_count == 0
    assert summary.rejected_review_count == 0
    assert summary.ctpc_pattern_count == 1


def test_import_txt_for_ui_creates_raw_corpus_and_batches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "knowledge_factory"
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_workspace(str(root))
    ensure_knowledge_library(str(library_root))
    monkeypatch.setattr(
        ui_knowledge_factory,
        "DEFAULT_KNOWLEDGE_LIBRARY_ROOT",
        str(library_root),
    )
    txt_path = Path(library_root, "psychotherapy", "act", "sample.txt")
    txt_path.write_text(
        "First paragraph with enough meaningful content to pass filtering.\n\n"
        "Second paragraph with enough meaningful content to pass filtering.",
        encoding="utf-8",
    )

    result = import_txt_for_ui(txt_path, str(root), max_batch_chars=500)

    assert result.source_id == "source_psychotherapy_act_sample"
    assert result.total_segments >= 2
    assert result.usable_segments >= 2
    assert result.batch_groups
    assert Path(result.raw_corpus_path).exists()
    assert not Path(root, "incoming").exists()


def test_list_knowledge_library_sources_for_ui(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(library_root))
    monkeypatch.setattr(
        ui_knowledge_factory,
        "DEFAULT_KNOWLEDGE_LIBRARY_ROOT",
        str(library_root),
    )
    Path(library_root, "vocal_icaro", "maria_sabina", "chants.txt").write_text(
        "Clean chant text.",
        encoding="utf-8",
    )

    sources = list_knowledge_library_sources_for_ui(str(library_root))

    assert len(sources) == 1
    assert sources[0].source_id == "source_vocal_icaro_maria_sabina_chants"
    assert sources[0].domain == "vocal_icaro"
    assert sources[0].family == "maria_sabina"
    assert sources[0].source_type == "text"


def test_knowledge_library_summary_separates_text_and_audio_extract_counts(
    tmp_path: Path,
) -> None:
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(library_root))
    text_path = Path(library_root, "vocal_icaro", "maria_sabina", "text", "chants.txt")
    text_path.parent.mkdir(parents=True)
    text_path.write_text("Clean chant text.", encoding="utf-8")
    audio_path = Path(
        library_root,
        "vocal_icaro",
        "maria_sabina",
        "audio_extracts",
        "01_maria_sabina.audio_extract.json",
    )
    audio_path.parent.mkdir(parents=True)
    audio_path.write_text('{"transcript": "chant"}', encoding="utf-8")

    counts = count_knowledge_library_sources_by_family(str(library_root))

    assert counts == {
        ("vocal_icaro", "maria_sabina/audio_extracts", "audio_extract", "never_compiled"): 1,
        ("vocal_icaro", "maria_sabina/text", "text", "never_compiled"): 1,
    }


def test_import_knowledge_source_for_ui_creates_raw_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "knowledge_factory"
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_workspace(str(root))
    ensure_knowledge_library(str(library_root))
    monkeypatch.setattr(
        ui_knowledge_factory,
        "DEFAULT_KNOWLEDGE_LIBRARY_ROOT",
        str(library_root),
    )
    Path(library_root, "psychotherapy", "act", "ACT Made Simple.txt").write_text(
        "First paragraph with enough meaningful content to pass filtering.",
        encoding="utf-8",
    )
    source = list_knowledge_library_sources_for_ui(str(library_root))[0]

    result = import_knowledge_source_for_ui(
        source.source_id,
        str(root),
        library_root=str(library_root),
    )

    assert result.source_id == "source_psychotherapy_act_act_made_simple"
    assert result.source_family == "act"
    assert Path(result.raw_corpus_path).exists()
    assert not Path(root, "incoming").exists()


def test_library_source_domains_map_to_supported_review_domains(
    tmp_path: Path,
) -> None:
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(library_root))
    psychotherapy_path = Path(library_root, "psychotherapy", "act", "act.txt")
    psychotherapy_path.write_text("Clean ACT text.", encoding="utf-8")
    vocal_path = Path(library_root, "vocal_icaro", "maria_sabina", "chants.txt")
    vocal_path.write_text("Clean chant text.", encoding="utf-8")
    sources = list(ui_knowledge_factory.list_knowledge_sources(str(library_root)))

    by_domain = {source.domain: source for source in sources}

    assert knowledge_domain_for_library_source(by_domain["psychotherapy"]) == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    assert knowledge_domain_for_library_source(by_domain["vocal_icaro"]) == KNOWLEDGE_DOMAIN_VOCAL_ICARO


def test_psychedelic_research_maps_to_psychotherapy_tle(tmp_path: Path) -> None:
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(library_root))
    source_path = Path(library_root, "psychedelic_research", "Psilocybin therapy.txt")
    source_path.parent.mkdir(parents=True)
    source_path.write_text("Clean research text.", encoding="utf-8")
    source = ui_knowledge_factory.list_knowledge_sources(str(library_root))[0]

    assert source.domain == "psychedelic_research"
    assert source.family == "general"
    assert knowledge_domain_for_library_source(source) == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE


def test_unknown_domain_is_visible_but_compile_unsupported(tmp_path: Path) -> None:
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(library_root))
    source_path = Path(library_root, "new_domain", "source.txt")
    source_path.parent.mkdir(parents=True)
    source_path.write_text("Clean unknown-domain text.", encoding="utf-8")
    source = ui_knowledge_factory.list_knowledge_sources(str(library_root))[0]

    assert source.domain == "new_domain"
    assert source.family == "general"
    with pytest.raises(ValueError, match="not supported"):
        knowledge_domain_for_library_source(source)


def test_audio_extract_source_is_visible_and_maps_to_vocal_icaro(tmp_path: Path) -> None:
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_library(str(library_root))
    audio_path = Path(
        library_root,
        "vocal_icaro",
        "maria_sabina",
        "audio_extracts",
        "01_maria_sabina.audio_extract.json",
    )
    audio_path.parent.mkdir(parents=True)
    audio_path.write_text('{"transcript": "chant"}', encoding="utf-8")
    source = ui_knowledge_factory.list_knowledge_sources(str(library_root))[0]

    assert source.source_type == "audio_extract"
    assert knowledge_domain_for_library_source(source) == KNOWLEDGE_DOMAIN_VOCAL_ICARO


def test_run_library_source_extraction_creates_pending_reviews_with_domain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "knowledge_factory"
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_workspace(str(root))
    ensure_knowledge_library(str(library_root))
    monkeypatch.setattr(
        ui_knowledge_factory,
        "DEFAULT_KNOWLEDGE_LIBRARY_ROOT",
        str(library_root),
    )
    Path(library_root, "psychotherapy", "act", "ACT Made Simple.txt").write_text(
        "First paragraph with enough meaningful content to pass filtering.\n\n"
        "Second paragraph with enough meaningful content to pass filtering.",
        encoding="utf-8",
    )
    source = list_knowledge_library_sources_for_ui(str(library_root))[0]

    class FakePipeline:
        def __init__(self) -> None:
            self.created_domains: list[str] = []

        def extract_from_corpus(self, corpus, segment_id):
            return _extraction(
                source_id=corpus.source.source_id,
                segment_id=segment_id,
            )

        def create_pending_review(self, extraction, *, knowledge_domain):
            self.created_domains.append(knowledge_domain)
            workflow = HumanReviewWorkflow(
                paths=ensure_knowledge_workspace(str(root)),
            )
            return workflow.create_pending_review(
                extraction,
                knowledge_domain=knowledge_domain,
            )

    fake_pipeline = FakePipeline()
    monkeypatch.setattr(ui_knowledge_factory, "_pipeline", lambda workspace_root: fake_pipeline)

    result = run_library_source_extraction_for_ui(
        source.source_id,
        str(root),
        library_root=str(library_root),
        max_batch_chars=500,
    )

    assert result.knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    assert fake_pipeline.created_domains == [KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE]
    assert result.extraction_results[0].review_id is not None
    assert list(Path(root, "review").glob("*.json"))
    assert not Path(root, "incoming").exists()


def test_resolve_txt_input_path_from_incoming_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "knowledge_factory"
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_workspace(str(root))
    ensure_knowledge_library(str(library_root))
    monkeypatch.setattr(
        ui_knowledge_factory,
        "DEFAULT_KNOWLEDGE_LIBRARY_ROOT",
        str(library_root),
    )
    txt_path = Path(library_root, "psychotherapy", "act", "sample.txt")
    txt_path.write_text("Sample text.", encoding="utf-8")

    resolved = resolve_txt_input_path("sample.txt", str(root))

    assert resolved == txt_path.resolve()


def test_resolve_txt_input_path_rejects_ambiguous_library_basename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "knowledge_factory"
    library_root = tmp_path / "knowledge_library"
    ensure_knowledge_workspace(str(root))
    ensure_knowledge_library(str(library_root))
    monkeypatch.setattr(
        ui_knowledge_factory,
        "DEFAULT_KNOWLEDGE_LIBRARY_ROOT",
        str(library_root),
    )
    Path(library_root, "psychotherapy", "act", "sample.txt").write_text(
        "Sample ACT text.",
        encoding="utf-8",
    )
    Path(library_root, "psychotherapy", "cft", "sample.txt").write_text(
        "Sample CFT text.",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ambiguous"):
        resolve_txt_input_path("sample.txt", str(root))


def test_list_and_load_pending_review_for_ui(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path)

    table_items = list_extraction_results_for_ui(str(root))
    assert len(table_items) == 1
    assert table_items[0].review_id == review_id
    assert table_items[0].knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    assert table_items[0].suggested_action in {
        "approve_candidate",
        "needs_edit",
        "reject_candidate",
        "duplicate_candidate",
    }

    detail = load_review_for_ui(review_id, str(root))
    assert detail.review_id == review_id
    assert detail.therapeutic_function == "self_compassion"
    assert detail.generation_rules == ("Use gentle tone.",)
    assert detail.evidence_text.startswith("Evidence text")
    assert detail.knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE


def test_load_review_for_ui_includes_why_extracted(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    workflow = HumanReviewWorkflow(paths=paths)
    extraction = _extraction()
    record = workflow.create_pending_review(
        extraction,
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    )
    saved = workflow.load_review(record.review_id)
    workflow.save_review(
        HumanReviewRecord(
            review_id=saved.review_id,
            extraction_id=saved.extraction_id,
            source_id=saved.source_id,
            segment_id=saved.segment_id,
            status=saved.status,
            original_extraction=saved.original_extraction,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
            knowledge_domain=saved.knowledge_domain,
            review_type=saved.review_type,
            therapeutic_relevance={
                "relevance_score": 0.88,
                "knowledge_kind": "therapeutic_mechanism",
                "gate_reasoning": (
                    "This chunk explains experiential avoidance as a process where attempts "
                    "to avoid painful internal experiences reduce short-term distress."
                ),
                "why_extracted": (
                    "This chunk was extracted because it explains experiential avoidance."
                ),
                "evidence_span": "When a client tries to avoid painful feelings...",
            },
        )
    )
    detail = load_review_for_ui(saved.review_id, str(root))
    assert detail.relevance_score == 0.88
    assert detail.knowledge_kind == "therapeutic_mechanism"
    assert "experiential avoidance" in detail.why_extracted
    assert detail.evidence_span.startswith("When a client")


def test_suggested_action_for_review() -> None:
    action = suggested_action_for_review(
        segment_id="batch_001",
        confidence=0.85,
        therapeutic_function="self_compassion",
        evidence_text="x" * 120,
        duplicate_segments=set(),
    )
    assert action == "approve_candidate"


def test_list_latest_ctpc_patterns_after_approve(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path)
    approve_review_for_ui(review_id, str(root))

    patterns = list_latest_ctpc_patterns(str(root))

    assert len(patterns) == 1
    assert patterns[0].pattern_id.startswith("ctp_from_")
    assert patterns[0].knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE


def test_approve_review_for_ui_compiles_ctpc(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path)

    result = approve_review_for_ui(review_id, str(root))

    assert result.review.status == "approved"
    assert result.pattern.pattern_id.startswith("ctp_from_")
    assert Path(result.ctpc_path).exists()
    assert "psychotherapy_tle" in result.ctpc_path
    assert len(list_review_records(str(root), status=REVIEW_STATUS_PENDING)) == 0


def test_reject_review_for_ui_does_not_compile_ctpc(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    review_id = _create_pending_review(tmp_path)

    record = reject_review_for_ui(review_id, str(root), notes="Not grounded.")

    assert record.status == "rejected"
    assert list(Path(paths.ctpc_dir).rglob("*.json")) == []


def test_request_changes_for_ui_updates_status(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path)

    record = request_changes_for_ui(review_id, str(root), notes="Clarify symbols.")

    assert record.status == "changes_requested"
    assert review_is_actionable(record.status)


def test_batch_helpers_group_usable_segments() -> None:
    from niros.raw_source import RawSourceSegment

    segments = (
        RawSourceSegment(
            segment_id="seg_001",
            source_id="source_sample",
            sequence_index=1,
            raw_text="A" * 50,
        ),
        RawSourceSegment(
            segment_id="seg_002",
            source_id="source_sample",
            sequence_index=2,
            raw_text="Short",
        ),
    )

    usable = filter_usable_segments(segments)
    groups = build_batch_groups(usable, "source_sample", max_batch_chars=120)

    assert len(usable) == 1
    assert len(groups) == 1


def test_parse_multiline_field() -> None:
    assert parse_multiline_field(" one \n\n two \n") == ("one", "two")


def test_unknown_domain_review_cannot_be_approved_via_ui(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path, knowledge_domain=KNOWLEDGE_DOMAIN_UNKNOWN)

    with pytest.raises(HumanReviewError, match="knowledge_domain"):
        approve_review_for_ui(review_id, str(root))


def test_assign_domain_then_approve_vocal_icaro(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path, knowledge_domain=KNOWLEDGE_DOMAIN_UNKNOWN)

    assign_review_domain_for_ui(
        review_id,
        KNOWLEDGE_DOMAIN_VOCAL_ICARO,
        str(root),
    )
    result = approve_review_for_ui(review_id, str(root))

    assert result.pattern.knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO
    assert "vocal_icaro" in result.ctpc_path


def test_vocal_icaro_pattern_not_tle_eligible(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path, knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO)
    approve_review_for_ui(review_id, str(root))

    tle_patterns = list_tle_eligible_ctpc_patterns(str(root))
    all_patterns = list_latest_ctpc_patterns(str(root))

    assert len(all_patterns) == 1
    assert all_patterns[0].knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO
    assert tle_patterns == ()


def test_psychotherapy_tle_pattern_is_tle_eligible(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    review_id = _create_pending_review(tmp_path, knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE)
    approve_review_for_ui(review_id, str(root))

    tle_patterns = list_tle_eligible_ctpc_patterns(str(root))

    assert len(tle_patterns) == 1
    assert tle_patterns[0].knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE


def test_review_can_be_approved_requires_domain(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    workflow = HumanReviewWorkflow(paths=paths)
    unknown = workflow.create_pending_review(
        _extraction(),
        knowledge_domain=KNOWLEDGE_DOMAIN_UNKNOWN,
    )
    assigned = workflow.create_pending_review(
        _extraction(segment_id="source_001_segment_002"),
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    )

    assert review_can_be_approved(unknown) is False
    assert review_can_be_approved(assigned) is True


def test_parse_max_batches_option() -> None:
    assert parse_max_batches_option("3") == 3
    assert parse_max_batches_option("all") is None


def test_parse_review_mode_option_defaults_conservative() -> None:
    assert parse_review_mode_option("Conservative") == "conservative"
    assert DEFAULT_REVIEW_MODE_UI_OPTION == "Conservative"
    assert "Conservative" in REVIEW_MODE_UI_OPTIONS


def test_archive_pending_reviews_moves_files(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    review_dir = Path(paths.review_dir)
    pending_path = review_dir / "review_pending_example.json"
    pending_path.write_text(
        '{"review_id":"review_pending_example","status":"pending"}',
        encoding="utf-8",
    )
    approved_path = review_dir / "review_approved_example.json"
    approved_path.write_text(
        '{"review_id":"review_approved_example","status":"approved"}',
        encoding="utf-8",
    )

    result = archive_pending_reviews_for_ui(str(root), timestamp="2026-07-08T12:00:00+00:00")

    assert result.archived_count == 1
    assert not pending_path.exists()
    assert approved_path.exists()
    assert result.archive_dir.endswith("review_20260708T1200000000")


def test_compile_summary_ui_funnel() -> None:
    from niros.knowledge_compiler import CompileSummary

    summary = CompileSummary(
        scope="document:source_test",
        chunks_created=241,
        raw_extractions=1238,
        filtered_extractions=100,
        consolidated_candidates=61,
        pending_reviews=61,
        auto_approved=5,
        books_processed=4,
        chunks_seen=241,
        chunks_skipped=120,
        chunks_extracted=121,
        skipped_by_reason=(("keyword_only", 40), ("front_matter", 80)),
        high_relevance_count=70,
        medium_relevance_count=30,
        low_relevance_count=21,
    )
    funnel = compile_summary_ui_funnel(summary)

    assert funnel["books_processed"] == 4
    assert funnel["batches"] == 241
    assert funnel["chunks_seen"] == 241
    assert funnel["chunks_skipped"] == 120
    assert funnel["chunks_extracted"] == 121
    assert funnel["skipped_by_reason"] == (("keyword_only", 40), ("front_matter", 80))
    assert funnel["raw_extractions"] == 1238
    assert funnel["filtered_extractions"] == 100
    assert funnel["consolidated_candidates"] == 61
    assert funnel["pending_reviews"] == 61
    assert funnel["auto_approved"] == 5


def test_compile_progress_ui_summary_includes_counts() -> None:
    result = DocumentCompileResult(
        source_id="source_test",
        relative_path="psychotherapy/act/act.txt",
        status="partial",
        source_type="text",
        domain="psychotherapy",
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
        usable_batch_count=5,
        batches_processed=3,
        reviews_created=2,
        failed_batches=1,
        skipped_reviews=0,
        duration_seconds=1.5,
        raw_corpus_path="/tmp/raw.json",
        log_path="/tmp/log.json",
        live_log_path="/tmp/live.jsonl",
        openai_model="gpt-4.1-mini",
        max_batch_chars=500,
        max_batches=3,
        chunks_seen=5,
        chunks_skipped=2,
        chunks_extracted=3,
        skipped_by_reason=(("keyword_only", 2),),
        high_relevance_count=2,
        medium_relevance_count=1,
        low_relevance_count=0,
    )

    summary = compile_progress_ui_summary(result)

    assert summary.total_batches == 5
    assert summary.processed == 3
    assert summary.chunks_seen == 5
    assert summary.chunks_skipped == 2
    assert summary.chunks_extracted == 3
    assert summary.skipped_by_reason == (("keyword_only", 2),)
    assert summary.reviews_created == 2
    assert summary.failed == 1
    assert summary.skipped == 0
    assert summary.live_log_path == "/tmp/live.jsonl"
