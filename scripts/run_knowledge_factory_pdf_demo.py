#!/usr/bin/env python3
"""Manual Knowledge Factory demo — run one PDF through the Knowledge Factory pipeline."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from niros.env_loader import load_project_env
from niros.knowledge_factory_pipeline import KnowledgeFactoryPipeline
from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    KnowledgeWorkspacePaths,
    ensure_knowledge_workspace,
    knowledge_artifact_path,
)
from niros.raw_corpus_io import save_raw_corpus
from niros.raw_source import RawSourceCorpus, RawSourceSegment
from niros.runtime_config import OPENAI_KEY_ENV_VAR, OPENAI_SETUP_HINT, has_openai_api_key

SCANNED_PDF_GUIDANCE = (
    "Scanned PDFs are not supported in Sprint 029. Convert scanned pages to TXT first."
)


def _normalize_source_id(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    normalized = re.sub(r"[^a-z0-9_]+", "", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "pdf_source"


def default_source_id(pdf_path: Path) -> str:
    """Build a deterministic source ID from a PDF filename."""
    return f"source_{_normalize_source_id(pdf_path.stem)}"


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run one PDF through the NIROS Knowledge Factory pipeline.",
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to a text-based PDF file.",
    )
    parser.add_argument(
        "--segment-id",
        help="Segment ID to extract. Omit to inspect imported segments only.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Approve the review and compile CTPC after extraction.",
    )
    parser.add_argument(
        "--source-id",
        help="Optional source ID override. Defaults to the PDF filename stem.",
    )
    parser.add_argument(
        "--source-title",
        help="Optional source title override. Defaults to the PDF filename.",
    )
    parser.add_argument(
        "--source-family",
        default="manual_import",
        help="Source family label for the imported PDF.",
    )
    parser.add_argument(
        "--workspace-root",
        default=DEFAULT_KNOWLEDGE_ROOT,
        help="Knowledge Factory workspace root directory.",
    )
    parser.add_argument(
        "--reviewer-id",
        default="manual_reviewer",
        help="Reviewer ID used only when --auto-approve is set.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    return build_arg_parser().parse_args(argv)


def _raw_corpus_file_path(paths: KnowledgeWorkspacePaths, source_id: str) -> str:
    return knowledge_artifact_path(paths, "raw_corpus", f"{source_id}.json")


def _review_file_path(pipeline: KnowledgeFactoryPipeline, review_id: str) -> str:
    return knowledge_artifact_path(
        pipeline.review_workflow.paths,
        "review",
        f"{review_id}.json",
    )


def _ctpc_file_path(pipeline: KnowledgeFactoryPipeline, pattern_id: str) -> str:
    return knowledge_artifact_path(
        pipeline.ctpc_compiler.paths,
        "ctpc",
        f"{pattern_id}.json",
    )


def _parse_page_number(segment: RawSourceSegment) -> str | None:
    for part in segment.notes.split(";"):
        item = part.strip()
        if item.startswith("page_number="):
            return item.split("=", 1)[1]
    return None


def _preview_text(raw_text: str, limit: int = 200) -> str:
    collapsed = " ".join(raw_text.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}..."


def _save_raw_corpus_artifact(
    corpus: RawSourceCorpus,
    paths: KnowledgeWorkspacePaths,
) -> Path:
    output_path = Path(_raw_corpus_file_path(paths, corpus.source.source_id))
    return save_raw_corpus(corpus, output_path)


def _print_import_summary(
    corpus: RawSourceCorpus,
    raw_corpus_path: Path,
    stream: TextIO,
) -> None:
    print(f"Imported source_id: {corpus.source.source_id}", file=stream)
    print(f"Segment/page count: {len(corpus.segments)}", file=stream)
    print(f"Raw corpus file: {raw_corpus_path}", file=stream)


def _print_segment_inspection(corpus: RawSourceCorpus, stream: TextIO) -> None:
    print("", file=stream)
    print("Available segments:", file=stream)
    for segment in corpus.segments:
        page_number = _parse_page_number(segment)
        page_label = page_number if page_number is not None else "unknown"
        print(f"- segment_id: {segment.segment_id}", file=stream)
        print(f"  page_number: {page_label}", file=stream)
        print(f"  preview: {_preview_text(segment.raw_text)}", file=stream)


def _find_segment(corpus: RawSourceCorpus, segment_id: str) -> RawSourceSegment | None:
    for segment in corpus.segments:
        if segment.segment_id == segment_id:
            return segment
    return None


def run_knowledge_factory_pdf_demo(
    pdf_path: Path,
    *,
    segment_id: str | None = None,
    auto_approve: bool = False,
    source_id: str | None = None,
    source_title: str | None = None,
    source_family: str = "manual_import",
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    reviewer_id: str = "manual_reviewer",
    output_stream: TextIO | None = None,
) -> int:
    """Run the Knowledge Factory demo for one PDF file."""
    stream = output_stream or sys.stdout

    load_project_env()

    resolved_pdf = pdf_path.expanduser().resolve()
    if not resolved_pdf.is_file():
        print(f"PDF file not found: {resolved_pdf}", file=stream)
        return 1

    resolved_source_id = source_id or default_source_id(resolved_pdf)
    resolved_source_title = source_title or resolved_pdf.name

    paths = ensure_knowledge_workspace(workspace_root)
    pipeline = KnowledgeFactoryPipeline.from_workspace_root(
        workspace_root,
        paths=paths,
    )

    print("=== NIROS Knowledge Factory PDF Demo ===", file=stream)
    print(SCANNED_PDF_GUIDANCE, file=stream)
    print(f"Workspace: {paths.root}", file=stream)
    print(f"PDF: {resolved_pdf}", file=stream)
    print("", file=stream)

    corpus = pipeline.import_pdf(
        resolved_pdf,
        resolved_source_id,
        resolved_source_title,
        source_family=source_family,
    )
    if not corpus.segments:
        print("No extractable text segments were found in the PDF.", file=stream)
        return 1

    raw_corpus_path = _save_raw_corpus_artifact(corpus, paths)
    _print_import_summary(corpus, raw_corpus_path, stream)

    if segment_id is None:
        _print_segment_inspection(corpus, stream)
        print("", file=stream)
        print("OpenAI extraction was not run.", file=stream)
        print("Re-run with --segment-id <segment_id>", file=stream)
        return 0

    if not has_openai_api_key():
        print(f"Missing required environment variable: {OPENAI_KEY_ENV_VAR}", file=stream)
        print(OPENAI_SETUP_HINT, file=stream)
        return 1

    selected_segment = _find_segment(corpus, segment_id)
    if selected_segment is None:
        print(f"Segment not found in imported corpus: {segment_id}", file=stream)
        _print_segment_inspection(corpus, stream)
        print("", file=stream)
        print("Re-run with --segment-id <segment_id>", file=stream)
        return 1

    extraction = pipeline.extract_from_corpus(corpus, selected_segment.segment_id)
    pending_review = pipeline.create_pending_review(extraction)
    review_path = _review_file_path(pipeline, pending_review.review_id)

    print(f"Selected segment_id: {selected_segment.segment_id}", file=stream)
    print(f"Created extraction_id: {extraction.extraction_id}", file=stream)
    print(f"Created review_id: {pending_review.review_id}", file=stream)
    print(f"Review file: {review_path}", file=stream)

    if not auto_approve:
        print("", file=stream)
        print("Review is pending human approval.", file=stream)
        print("CTPC compilation was not run.", file=stream)
        print("Re-run with --auto-approve after reviewing the extraction JSON.", file=stream)
        return 0

    approved_review = pipeline.approve_review(
        pending_review.review_id,
        reviewer_id=reviewer_id,
        reviewer_notes="Approved via Knowledge Factory PDF demo.",
    )
    pattern = pipeline.compile_approved_review(approved_review)
    ctpc_path = _ctpc_file_path(pipeline, pattern.pattern_id)

    print(f"Approved review_id: {approved_review.review_id}", file=stream)
    print(f"CTPC pattern_id: {pattern.pattern_id}", file=stream)
    print(f"CTPC file: {ctpc_path}", file=stream)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    return run_knowledge_factory_pdf_demo(
        args.pdf_path,
        segment_id=args.segment_id,
        auto_approve=args.auto_approve,
        source_id=args.source_id,
        source_title=args.source_title,
        source_family=args.source_family,
        workspace_root=args.workspace_root,
        reviewer_id=args.reviewer_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
