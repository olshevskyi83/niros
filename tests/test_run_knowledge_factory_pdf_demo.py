"""Tests for Knowledge Factory PDF demo script."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from run_knowledge_factory_pdf_demo import (
    build_arg_parser,
    default_source_id,
    parse_args,
    run_knowledge_factory_pdf_demo,
)
from niros.raw_source import RawSource, RawSourceCorpus, RawSourceSegment, build_raw_source_corpus


def _sample_corpus() -> RawSourceCorpus:
    source = RawSource(
        source_id="source_sample",
        source_family="manual_import",
        title="sample.pdf",
        language="unknown",
        source_type="document",
    )
    segments = (
        RawSourceSegment(
            segment_id="source_sample_page_001",
            source_id="source_sample",
            sequence_index=1,
            raw_text="First page text for inspection.",
            notes="page_number=1; source_page_label=Page 1",
        ),
        RawSourceSegment(
            segment_id="source_sample_page_002",
            source_id="source_sample",
            sequence_index=2,
            raw_text="Second page text for inspection.",
            notes="page_number=2; source_page_label=Page 2",
        ),
    )
    return build_raw_source_corpus(source, segments)


def test_script_exists() -> None:
    assert (SCRIPTS_DIR / "run_knowledge_factory_pdf_demo.py").is_file()


def test_module_imports_successfully() -> None:
    import run_knowledge_factory_pdf_demo

    assert run_knowledge_factory_pdf_demo.main is not None


def test_argument_parser_defaults() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(["sample.pdf"])

    assert args.pdf_path == Path("sample.pdf")
    assert args.segment_id is None
    assert args.auto_approve is False
    assert args.workspace_root == "knowledge_factory"
    assert args.source_family == "manual_import"


def test_parse_args_supports_auto_approve() -> None:
    args = parse_args(["sample.pdf", "--auto-approve"])
    assert args.auto_approve is True


def test_parse_args_supports_segment_id() -> None:
    args = parse_args(["sample.pdf", "--segment-id", "source_sample_page_001"])
    assert args.segment_id == "source_sample_page_001"


def test_default_source_id_is_deterministic() -> None:
    assert default_source_id(Path("Chant Notes.pdf")) == "source_chant_notes"


def test_inspection_mode_does_not_require_openai_api_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    workspace = tmp_path / "knowledge_factory"

    mock_pipeline = MagicMock()
    mock_pipeline.import_pdf.return_value = _sample_corpus()

    output = io.StringIO()
    with patch(
        "run_knowledge_factory_pdf_demo.KnowledgeFactoryPipeline.from_workspace_root",
        return_value=mock_pipeline,
    ):
        exit_code = run_knowledge_factory_pdf_demo(
            pdf_path,
            workspace_root=str(workspace),
            output_stream=output,
        )

    assert exit_code == 0
    rendered = output.getvalue()
    assert "Raw corpus file:" in rendered
    assert "source_sample_page_001" in rendered
    assert "OpenAI extraction was not run." in rendered
    assert "Re-run with --segment-id <segment_id>" in rendered
    mock_pipeline.extract_from_corpus.assert_not_called()


def test_run_requires_openai_api_key_when_segment_id_provided(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    workspace = tmp_path / "knowledge_factory"

    mock_pipeline = MagicMock()
    mock_pipeline.import_pdf.return_value = _sample_corpus()

    output = io.StringIO()
    with patch(
        "run_knowledge_factory_pdf_demo.KnowledgeFactoryPipeline.from_workspace_root",
        return_value=mock_pipeline,
    ):
        exit_code = run_knowledge_factory_pdf_demo(
            pdf_path,
            segment_id="source_sample_page_001",
            workspace_root=str(workspace),
            output_stream=output,
        )

    assert exit_code == 1
    assert "OPENAI_API_KEY" in output.getvalue()
    mock_pipeline.extract_from_corpus.assert_not_called()
