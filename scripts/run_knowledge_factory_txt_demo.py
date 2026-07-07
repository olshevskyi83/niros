#!/usr/bin/env python3
"""Manual Knowledge Factory demo — run one TXT file through the Knowledge Factory pipeline."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
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
from niros.openai_semantic_extraction_adapter import SemanticExtractionAdapterError
from niros.raw_corpus_io import save_raw_corpus
from niros.raw_source import RawSourceCorpus, RawSourceSegment, build_raw_source_corpus
from niros.runtime_config import OPENAI_KEY_ENV_VAR, OPENAI_SETUP_HINT, has_openai_api_key
from niros.source_registry import KnowledgeSourceRecord
from niros.therapeutic_extraction import TherapeuticFunctionExtraction
from niros.txt_source_importer import import_txt_as_raw_corpus

SCANNED_PDF_GUIDANCE = (
    "Scanned PDFs are not supported in Sprint 029. Convert scanned pages to TXT first."
)
DEFAULT_SOURCE_TYPE = "text"
DEFAULT_LANGUAGE = "unknown"
DEFAULT_MAX_BATCH_CHARS = 3000
MIN_MEANINGFUL_CHARS = 40
BATCH_SEPARATOR = "\n\n---\n\n"


@dataclass(frozen=True)
class BatchGroup:
    batch_segment: RawSourceSegment
    included_segments: tuple[RawSourceSegment, ...]


@dataclass(frozen=True)
class BatchExtractionResult:
    batch_segment: RawSourceSegment
    included_segments: tuple[RawSourceSegment, ...]
    extraction: TherapeuticFunctionExtraction | None = None
    review_id: str | None = None
    failure_message: str | None = None


def _normalize_source_id(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    normalized = re.sub(r"[^a-z0-9_]+", "", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "txt_source"


def default_source_id(txt_path: Path) -> str:
    """Build a deterministic source ID from a TXT filename."""
    return f"source_{_normalize_source_id(txt_path.stem)}"


def meaningful_char_count(text: str) -> int:
    """Count non-whitespace characters in one text block."""
    return len(re.sub(r"\s+", "", text.strip()))


def is_obvious_heading(text: str) -> bool:
    """Return True when short text looks like a heading rather than body content."""
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
    """Return True when a segment should be included in batch extraction."""
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
    """Return corpus segments that are usable for extraction."""
    return tuple(segment for segment in segments if is_usable_segment(segment))


def build_batch_segment(
    source_id: str,
    batch_index: int,
    included_segments: tuple[RawSourceSegment, ...],
) -> RawSourceSegment:
    """Build one deterministic batch segment from included source segments."""
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
    max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
) -> tuple[BatchGroup, ...]:
    """Group usable segments into deterministic extraction batches."""
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

    return tuple(
        BatchGroup(
            batch_segment=build_batch_segment(source_id, index, group),
            included_segments=group,
        )
        for index, group in enumerate(groups, start=1)
    )


def group_segments_into_batches(
    segments: tuple[RawSourceSegment, ...] | list[RawSourceSegment],
    source_id: str,
    max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
) -> tuple[RawSourceSegment, ...]:
    """Return only the batch segments for grouped usable segments."""
    return tuple(
        group.batch_segment
        for group in build_batch_groups(segments, source_id, max_batch_chars)
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run one TXT file through the NIROS Knowledge Factory pipeline.",
    )
    parser.add_argument(
        "txt_path",
        type=Path,
        help="Path to a plain-text source file.",
    )
    parser.add_argument(
        "--segment-id",
        help="Segment ID to extract. Omit to inspect imported segments only.",
    )
    parser.add_argument(
        "--process-all",
        action="store_true",
        help="Extract all usable segments in deterministic batches.",
    )
    parser.add_argument(
        "--max-batch-chars",
        type=int,
        default=DEFAULT_MAX_BATCH_CHARS,
        help="Maximum approximate characters per batch when using --process-all.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Approve the review and compile CTPC after single-segment extraction.",
    )
    parser.add_argument(
        "--source-id",
        help="Optional source ID override. Defaults to the TXT filename stem.",
    )
    parser.add_argument(
        "--source-title",
        help="Optional source title override. Defaults to the TXT filename.",
    )
    parser.add_argument(
        "--source-family",
        default="manual_import",
        help="Source family label for the imported TXT file.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding used when reading the TXT file.",
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


def _failure_log_path(paths: KnowledgeWorkspacePaths, source_id: str) -> Path:
    return Path(knowledge_artifact_path(paths, "logs", f"{source_id}_batch_failures.log"))


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
    print(f"Segment count: {len(corpus.segments)}", file=stream)
    print(f"Raw corpus file: {raw_corpus_path}", file=stream)


def _print_segment_inspection(
    corpus: RawSourceCorpus,
    stream: TextIO,
    *,
    usable_only: bool = False,
) -> None:
    segments = filter_usable_segments(corpus.segments) if usable_only else corpus.segments
    label = "Usable segments" if usable_only else "Available segments"
    print("", file=stream)
    print(f"{label}:", file=stream)
    if not segments:
        print("- none", file=stream)
        return
    for segment in segments:
        print(f"- segment_id: {segment.segment_id}", file=stream)
        print(f"  sequence_index: {segment.sequence_index}", file=stream)
        print(f"  preview: {_preview_text(segment.raw_text)}", file=stream)


def _find_segment(corpus: RawSourceCorpus, segment_id: str) -> RawSourceSegment | None:
    for segment in corpus.segments:
        if segment.segment_id == segment_id:
            return segment
    return None


def _segment_range_label(segments: tuple[RawSourceSegment, ...]) -> str:
    if not segments:
        return "none"
    if len(segments) == 1:
        return segments[0].segment_id
    return f"{segments[0].segment_id} .. {segments[-1].segment_id}"


def _build_source_record(
    *,
    source_id: str,
    source_title: str,
    source_family: str,
) -> KnowledgeSourceRecord:
    return KnowledgeSourceRecord(
        source_id=source_id,
        source_family=source_family,
        title=source_title,
        source_type=DEFAULT_SOURCE_TYPE,
        language=DEFAULT_LANGUAGE,
    )


def _append_failure_log(
    paths: KnowledgeWorkspacePaths,
    source_id: str,
    batch_id: str,
    message: str,
) -> None:
    log_path = _failure_log_path(paths, source_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} | {batch_id} | {message}\n")


def process_all_batches(
    pipeline: KnowledgeFactoryPipeline,
    corpus: RawSourceCorpus,
    batch_groups: tuple[BatchGroup, ...],
    paths: KnowledgeWorkspacePaths,
    stream: TextIO,
) -> list[BatchExtractionResult]:
    """Extract each batch segment and create pending reviews."""
    results: list[BatchExtractionResult] = []

    for batch_group in batch_groups:
        batch_segment = batch_group.batch_segment
        included_segments = batch_group.included_segments
        try:
            batch_corpus = build_raw_source_corpus(corpus.source, (batch_segment,))
            extraction = pipeline.extract_from_corpus(
                batch_corpus,
                batch_segment.segment_id,
            )
            pending_review = pipeline.create_pending_review(extraction)
            results.append(
                BatchExtractionResult(
                    batch_segment=batch_segment,
                    included_segments=included_segments,
                    extraction=extraction,
                    review_id=pending_review.review_id,
                )
            )
        except (SemanticExtractionAdapterError, ValueError) as exc:
            message = str(exc)
            _append_failure_log(paths, corpus.source.source_id, batch_segment.segment_id, message)
            results.append(
                BatchExtractionResult(
                    batch_segment=batch_segment,
                    included_segments=included_segments,
                    failure_message=message,
                )
            )
            print(f"Batch failed: {batch_segment.segment_id}", file=stream)
            print(f"  failure: {message}", file=stream)

    return results


def run_knowledge_factory_txt_demo(
    txt_path: Path,
    *,
    segment_id: str | None = None,
    process_all: bool = False,
    max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
    auto_approve: bool = False,
    source_id: str | None = None,
    source_title: str | None = None,
    source_family: str = "manual_import",
    encoding: str = "utf-8",
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    reviewer_id: str = "manual_reviewer",
    output_stream: TextIO | None = None,
) -> int:
    """Run the Knowledge Factory demo for one TXT file."""
    stream = output_stream or sys.stdout

    load_project_env()

    if segment_id is not None and process_all:
        print("Use either --segment-id or --process-all, not both.", file=stream)
        return 1

    resolved_txt = txt_path.expanduser().resolve()
    if not resolved_txt.is_file():
        print(f"TXT file not found: {resolved_txt}", file=stream)
        return 1
    if resolved_txt.suffix.lower() != ".txt":
        print(f"Expected a .txt file: {resolved_txt}", file=stream)
        return 1

    resolved_source_id = source_id or default_source_id(resolved_txt)
    resolved_source_title = source_title or resolved_txt.name

    paths = ensure_knowledge_workspace(workspace_root)
    pipeline = KnowledgeFactoryPipeline.from_workspace_root(
        workspace_root,
        paths=paths,
    )

    print("=== NIROS Knowledge Factory TXT Demo ===", file=stream)
    print(SCANNED_PDF_GUIDANCE, file=stream)
    print(f"Workspace: {paths.root}", file=stream)
    print(f"TXT: {resolved_txt}", file=stream)
    print("", file=stream)

    source_record = _build_source_record(
        source_id=resolved_source_id,
        source_title=resolved_source_title,
        source_family=source_family,
    )
    corpus = import_txt_as_raw_corpus(
        resolved_txt,
        source_record,
        encoding=encoding,
    )
    if not corpus.segments:
        print("No text segments were found in the TXT file.", file=stream)
        return 1

    raw_corpus_path = _save_raw_corpus_artifact(corpus, paths)
    _print_import_summary(corpus, raw_corpus_path, stream)

    if segment_id is None and not process_all:
        _print_segment_inspection(corpus, stream, usable_only=True)
        print("", file=stream)
        print("OpenAI extraction was not run.", file=stream)
        print("Re-run with --segment-id <segment_id> or --process-all", file=stream)
        return 0

    if not has_openai_api_key():
        print(f"Missing required environment variable: {OPENAI_KEY_ENV_VAR}", file=stream)
        print(OPENAI_SETUP_HINT, file=stream)
        return 1

    if process_all:
        if auto_approve:
            print("Batch auto-approval is not supported yet.", file=stream)
            print("Pending reviews were not auto-approved.", file=stream)
            print("", file=stream)

        usable_segments = filter_usable_segments(corpus.segments)
        batch_groups = build_batch_groups(
            corpus.segments,
            corpus.source.source_id,
            max_batch_chars,
        )

        print(f"Total segments: {len(corpus.segments)}", file=stream)
        print(f"Usable segments: {len(usable_segments)}", file=stream)
        print(f"Batch count: {len(batch_groups)}", file=stream)
        print("", file=stream)

        if not batch_groups:
            print("No usable segments were available for batch extraction.", file=stream)
            return 1

        results = process_all_batches(
            pipeline,
            corpus,
            batch_groups,
            paths,
            stream,
        )

        for result in results:
            print(f"Batch: {result.batch_segment.segment_id}", file=stream)
            print(
                f"  included segment range: {_segment_range_label(result.included_segments)}",
                file=stream,
            )
            if result.failure_message is not None:
                print(f"  failure: {result.failure_message}", file=stream)
                continue
            print(f"  extraction_id: {result.extraction.extraction_id}", file=stream)
            print(f"  review_id: {result.review_id}", file=stream)
            print(f"  review file: {_review_file_path(pipeline, result.review_id)}", file=stream)

        print("", file=stream)
        print("Batch extraction complete. Reviews are pending human approval.", file=stream)
        return 0

    selected_segment = _find_segment(corpus, segment_id or "")
    if selected_segment is None:
        print(f"Segment not found in imported corpus: {segment_id}", file=stream)
        _print_segment_inspection(corpus, stream, usable_only=True)
        print("", file=stream)
        print("Re-run with --segment-id <segment_id> or --process-all", file=stream)
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
        reviewer_notes="Approved via Knowledge Factory TXT demo.",
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
    return run_knowledge_factory_txt_demo(
        args.txt_path,
        segment_id=args.segment_id,
        process_all=args.process_all,
        max_batch_chars=args.max_batch_chars,
        auto_approve=args.auto_approve,
        source_id=args.source_id,
        source_title=args.source_title,
        source_family=args.source_family,
        encoding=args.encoding,
        workspace_root=args.workspace_root,
        reviewer_id=args.reviewer_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
