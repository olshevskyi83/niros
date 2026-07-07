"""Tests for Knowledge Factory TXT demo script."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from run_knowledge_factory_txt_demo import (
    SCANNED_PDF_GUIDANCE,
    build_arg_parser,
    build_batch_groups,
    default_source_id,
    filter_usable_segments,
    group_segments_into_batches,
    is_usable_segment,
    parse_args,
    process_all_batches,
    run_knowledge_factory_txt_demo,
)
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.openai_semantic_extraction_adapter import SemanticExtractionValidationError
from niros.raw_source import RawSource, RawSourceCorpus, RawSourceSegment, build_raw_source_corpus
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id


def _sample_corpus() -> RawSourceCorpus:
    source = RawSource(
        source_id="source_sample",
        source_family="manual_import",
        title="sample.txt",
        language="unknown",
        source_type="text",
    )
    segments = (
        RawSourceSegment(
            segment_id="source_sample_segment_001",
            source_id="source_sample",
            sequence_index=1,
            raw_text="First paragraph text for inspection.",
        ),
        RawSourceSegment(
            segment_id="source_sample_segment_002",
            source_id="source_sample",
            sequence_index=2,
            raw_text="Second paragraph text for inspection.",
        ),
    )
    return build_raw_source_corpus(source, segments)


def _batch_corpus() -> RawSourceCorpus:
    source = RawSource(
        source_id="source_maria_sabina_chants",
        source_family="manual_import",
        title="maria_sabina_chants.txt",
        language="unknown",
        source_type="text",
    )
    segments = (
        RawSourceSegment(
            segment_id="source_maria_sabina_chants_segment_001",
            source_id="source_maria_sabina_chants",
            sequence_index=1,
            raw_text="",
        ),
        RawSourceSegment(
            segment_id="source_maria_sabina_chants_segment_002",
            source_id="source_maria_sabina_chants",
            sequence_index=2,
            raw_text="INTRO",
        ),
        RawSourceSegment(
            segment_id="source_maria_sabina_chants_segment_003",
            source_id="source_maria_sabina_chants",
            sequence_index=3,
            raw_text="A" * 50,
        ),
        RawSourceSegment(
            segment_id="source_maria_sabina_chants_segment_004",
            source_id="source_maria_sabina_chants",
            sequence_index=4,
            raw_text="B" * 50,
        ),
        RawSourceSegment(
            segment_id="source_maria_sabina_chants_segment_005",
            source_id="source_maria_sabina_chants",
            sequence_index=5,
            raw_text="C" * 50,
        ),
    )
    return build_raw_source_corpus(source, segments)


def _extraction(segment_id: str, therapeutic_function: str) -> TherapeuticFunctionExtraction:
    source_id = "source_maria_sabina_chants"
    return TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id(source_id, segment_id, therapeutic_function),
        source_id=source_id,
        segment_id=segment_id,
        therapeutic_function=therapeutic_function,
        evidence_text="Evidence text long enough for validation requirements.",
        generation_rules=("Use gentle tone.",),
        voice_rules=("Slow pace.",),
        confidence=0.8,
        extractor="openai",
    )


def test_script_exists() -> None:
    assert (SCRIPTS_DIR / "run_knowledge_factory_txt_demo.py").is_file()


def test_module_imports_successfully() -> None:
    import run_knowledge_factory_txt_demo

    assert run_knowledge_factory_txt_demo.main is not None


def test_argument_parser_defaults() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(["sample.txt"])

    assert args.txt_path == Path("sample.txt")
    assert args.segment_id is None
    assert args.process_all is False
    assert args.max_batch_chars == 3000
    assert args.auto_approve is False


def test_parse_args_supports_segment_id_and_process_all() -> None:
    args = parse_args(["sample.txt", "--segment-id", "source_sample_segment_001"])
    assert args.segment_id == "source_sample_segment_001"

    all_args = parse_args(["sample.txt", "--process-all", "--max-batch-chars", "120"])
    assert all_args.process_all is True
    assert all_args.max_batch_chars == 120


def test_default_source_id_is_deterministic() -> None:
    assert default_source_id(Path("Maria Sabina Chants.txt")) == "source_maria_sabina_chants"


def test_empty_and_short_segments_are_skipped() -> None:
    usable = filter_usable_segments(_batch_corpus().segments)
    assert [segment.segment_id for segment in usable] == [
        "source_maria_sabina_chants_segment_003",
        "source_maria_sabina_chants_segment_004",
        "source_maria_sabina_chants_segment_005",
    ]
    assert is_usable_segment(_batch_corpus().segments[0]) is False
    assert is_usable_segment(_batch_corpus().segments[1]) is False


def test_process_all_groups_usable_segments_into_deterministic_batches() -> None:
    groups = build_batch_groups(_batch_corpus().segments, "source_maria_sabina_chants", 120)
    batch_ids = [group.batch_segment.segment_id for group in groups]

    assert batch_ids == [
        "source_maria_sabina_chants_batch_001",
        "source_maria_sabina_chants_batch_002",
    ]
    assert "source_maria_sabina_chants_segment_003" in groups[0].batch_segment.notes
    assert "source_maria_sabina_chants_segment_004" in groups[0].batch_segment.notes
    assert groups[0].batch_segment.raw_text.count("\n\n---\n\n") == 1
    assert groups[1].batch_segment.raw_text.count("\n\n---\n\n") == 0

    second_run = group_segments_into_batches(
        _batch_corpus().segments,
        "source_maria_sabina_chants",
        120,
    )
    assert [segment.segment_id for segment in second_run] == batch_ids


def test_inspection_mode_does_not_call_openai(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
    workspace = tmp_path / "knowledge_factory"

    mock_pipeline = MagicMock()

    output = io.StringIO()
    with patch(
        "run_knowledge_factory_txt_demo.KnowledgeFactoryPipeline.from_workspace_root",
        return_value=mock_pipeline,
    ), patch(
        "run_knowledge_factory_txt_demo.import_txt_as_raw_corpus",
        return_value=_sample_corpus(),
    ):
        exit_code = run_knowledge_factory_txt_demo(
            txt_path,
            workspace_root=str(workspace),
            output_stream=output,
        )

    assert exit_code == 0
    rendered = output.getvalue()
    assert SCANNED_PDF_GUIDANCE in rendered
    assert "OpenAI extraction was not run." in rendered
    assert "--process-all" in rendered
    mock_pipeline.extract_from_corpus.assert_not_called()


def test_run_requires_openai_api_key_when_segment_id_provided(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("First paragraph.", encoding="utf-8")
    workspace = tmp_path / "knowledge_factory"

    mock_pipeline = MagicMock()

    output = io.StringIO()
    with patch(
        "run_knowledge_factory_txt_demo.KnowledgeFactoryPipeline.from_workspace_root",
        return_value=mock_pipeline,
    ), patch(
        "run_knowledge_factory_txt_demo.import_txt_as_raw_corpus",
        return_value=_sample_corpus(),
    ):
        exit_code = run_knowledge_factory_txt_demo(
            txt_path,
            segment_id="source_sample_segment_001",
            workspace_root=str(workspace),
            output_stream=output,
        )

    assert exit_code == 1
    assert "OPENAI_API_KEY" in output.getvalue()
    mock_pipeline.extract_from_corpus.assert_not_called()


def test_one_failed_batch_does_not_stop_remaining_batches(tmp_path: Path) -> None:
    corpus = _batch_corpus()
    groups = build_batch_groups(corpus.segments, corpus.source.source_id, 120)
    workspace = tmp_path / "knowledge_factory"

    mock_pipeline = MagicMock()
    mock_pipeline.extract_from_corpus.side_effect = [
        SemanticExtractionValidationError("invalid batch"),
        _extraction(groups[1].batch_segment.segment_id, "self_compassion"),
    ]
    mock_pipeline.create_pending_review.return_value = MagicMock(review_id="review_batch_002")

    paths = ensure_knowledge_workspace(str(workspace))
    results = process_all_batches(
        mock_pipeline,
        corpus,
        groups,
        paths,
        io.StringIO(),
    )

    assert len(results) == 2
    assert results[0].failure_message is not None
    assert results[1].review_id == "review_batch_002"
    assert mock_pipeline.extract_from_corpus.call_count == 2
    assert mock_pipeline.create_pending_review.call_count == 1


def test_process_all_mode_calls_openai_for_each_batch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("sample", encoding="utf-8")
    workspace = tmp_path / "knowledge_factory"

    mock_pipeline = MagicMock()
    mock_pipeline.extract_from_corpus.return_value = _extraction(
        "source_maria_sabina_chants_batch_001",
        "self_compassion",
    )
    mock_pipeline.create_pending_review.return_value = MagicMock(
        review_id="review_extraction_source_maria_sabina_chants_batch_001_self_compassion"
    )

    output = io.StringIO()
    with patch(
        "run_knowledge_factory_txt_demo.KnowledgeFactoryPipeline.from_workspace_root",
        return_value=mock_pipeline,
    ), patch(
        "run_knowledge_factory_txt_demo.import_txt_as_raw_corpus",
        return_value=_batch_corpus(),
    ):
        exit_code = run_knowledge_factory_txt_demo(
            txt_path,
            process_all=True,
            max_batch_chars=120,
            workspace_root=str(workspace),
            output_stream=output,
        )

    assert exit_code == 0
    rendered = output.getvalue()
    assert "Batch count: 2" in rendered
    assert "extraction_id:" in rendered
    assert "review_id:" in rendered
    assert mock_pipeline.extract_from_corpus.call_count == 2
