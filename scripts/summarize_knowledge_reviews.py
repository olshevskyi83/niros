#!/usr/bin/env python3
"""Summarize Knowledge Factory human review JSON files for faster manual triage."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from niros.human_review_workflow import (
    HumanReviewRecord,
    deserialize_human_review_record,
)
from niros.knowledge_workspace import DEFAULT_KNOWLEDGE_ROOT, build_knowledge_workspace_paths
from niros.therapeutic_extraction import TherapeuticFunctionExtraction

EVIDENCE_PREVIEW_LENGTH = 180
EVIDENCE_APPROVE_MIN_LENGTH = 100
APPROVE_MIN_CONFIDENCE = 0.8

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

TABLE_COLUMNS = (
    "filename",
    "review_id",
    "status",
    "segment_id",
    "confidence",
    "therapeutic_function",
    "psychological_function",
    "evidence_preview",
    "suggested_action",
)


@dataclass(frozen=True)
class ReviewSummaryRow:
    filename: str
    review_id: str
    status: str
    segment_id: str
    confidence: float
    therapeutic_function: str
    psychological_function: str
    evidence_preview: str
    suggested_action: str


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize Knowledge Factory review JSON files into a readable table "
            "for manual triage."
        ),
    )
    parser.add_argument(
        "--workspace-root",
        default=DEFAULT_KNOWLEDGE_ROOT,
        help="Knowledge Factory workspace root directory.",
    )
    parser.add_argument(
        "--status",
        default="",
        help="Only include reviews with this status (for example: pending).",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=None,
        help="Only include reviews with confidence >= this value.",
    )
    parser.add_argument(
        "--show-duplicates",
        action="store_true",
        help="Only include reviews flagged as duplicate_candidate.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_arg_parser().parse_args(argv)


def _review_extraction(record: HumanReviewRecord) -> TherapeuticFunctionExtraction:
    if record.edited_extraction is not None:
        return record.edited_extraction
    return record.original_extraction


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def evidence_preview(text: str, limit: int = EVIDENCE_PREVIEW_LENGTH) -> str:
    collapsed = _collapse_whitespace(text)
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}..."


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


def suggested_action(
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
    if confidence < APPROVE_MIN_CONFIDENCE or is_vague_therapeutic_function(
        therapeutic_function
    ):
        return "needs_edit"
    return "needs_edit"


def load_review_records(review_dir: Path) -> list[tuple[str, HumanReviewRecord]]:
    if not review_dir.exists():
        return []

    loaded: list[tuple[str, HumanReviewRecord]] = []
    for path in sorted(review_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        loaded.append((path.name, deserialize_human_review_record(data)))
    return loaded


def build_summary_row(
    filename: str,
    record: HumanReviewRecord,
    duplicate_segments: set[str],
) -> ReviewSummaryRow:
    extraction = _review_extraction(record)
    return ReviewSummaryRow(
        filename=filename,
        review_id=record.review_id,
        status=record.status,
        segment_id=record.segment_id,
        confidence=extraction.confidence,
        therapeutic_function=extraction.therapeutic_function,
        psychological_function=extraction.psychological_function,
        evidence_preview=evidence_preview(extraction.evidence_text),
        suggested_action=suggested_action(
            segment_id=record.segment_id,
            confidence=extraction.confidence,
            therapeutic_function=extraction.therapeutic_function,
            evidence_text=extraction.evidence_text,
            duplicate_segments=duplicate_segments,
        ),
    )


def filter_records(
    loaded: list[tuple[str, HumanReviewRecord]],
    *,
    status: str,
) -> list[tuple[str, HumanReviewRecord]]:
    if not status:
        return loaded
    return [(filename, record) for filename, record in loaded if record.status == status]


def filter_rows(
    rows: list[ReviewSummaryRow],
    *,
    min_confidence: float | None,
    show_duplicates: bool,
) -> list[ReviewSummaryRow]:
    filtered = rows
    if min_confidence is not None:
        filtered = [row for row in filtered if row.confidence >= min_confidence]
    if show_duplicates:
        filtered = [
            row for row in filtered if row.suggested_action == "duplicate_candidate"
        ]
    return filtered


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    if limit <= 3:
        return value[:limit]
    return f"{value[: limit - 3]}..."


def format_table(rows: list[ReviewSummaryRow]) -> str:
    if not rows:
        return "No matching reviews."

    widths = {
        "filename": 24,
        "review_id": 28,
        "status": 12,
        "segment_id": 28,
        "confidence": 10,
        "therapeutic_function": 36,
        "psychological_function": 36,
        "evidence_preview": EVIDENCE_PREVIEW_LENGTH,
        "suggested_action": 18,
    }

    header = " | ".join(column.ljust(widths[column]) for column in TABLE_COLUMNS)
    divider = "-+-".join("-" * widths[column] for column in TABLE_COLUMNS)
    lines = [header, divider]

    for row in rows:
        values = {
            "filename": _truncate(row.filename, widths["filename"]),
            "review_id": _truncate(row.review_id, widths["review_id"]),
            "status": _truncate(row.status, widths["status"]),
            "segment_id": _truncate(row.segment_id, widths["segment_id"]),
            "confidence": f"{row.confidence:.2f}".ljust(widths["confidence"]),
            "therapeutic_function": _truncate(
                row.therapeutic_function,
                widths["therapeutic_function"],
            ),
            "psychological_function": _truncate(
                row.psychological_function,
                widths["psychological_function"],
            ),
            "evidence_preview": _truncate(
                row.evidence_preview,
                widths["evidence_preview"],
            ),
            "suggested_action": row.suggested_action.ljust(widths["suggested_action"]),
        }
        lines.append(" | ".join(values[column] for column in TABLE_COLUMNS))

    return "\n".join(lines)


def action_counts(rows: list[ReviewSummaryRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.suggested_action] = counts.get(row.suggested_action, 0) + 1
    return counts


def summarize_knowledge_reviews(
    *,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
    status: str = "",
    min_confidence: float | None = None,
    show_duplicates: bool = False,
) -> str:
    paths = build_knowledge_workspace_paths(workspace_root)
    review_dir = Path(paths.review_dir)
    loaded = load_review_records(review_dir)
    status_filtered = filter_records(loaded, status=status.strip())
    duplicates = duplicate_segment_ids([record for _, record in status_filtered])

    rows = [
        build_summary_row(filename, record, duplicates)
        for filename, record in status_filtered
    ]
    rows = filter_rows(
        rows,
        min_confidence=min_confidence,
        show_duplicates=show_duplicates,
    )

    table = format_table(rows)
    counts = action_counts(rows)
    summary_parts = [f"shown={len(rows)}"]
    for action in (
        "approve_candidate",
        "needs_edit",
        "duplicate_candidate",
        "reject_candidate",
    ):
        if action in counts:
            summary_parts.append(f"{action}={counts[action]}")
    return f"{table}\n\nSummary: {', '.join(summary_parts)}"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(
        summarize_knowledge_reviews(
            workspace_root=args.workspace_root,
            status=args.status,
            min_confidence=args.min_confidence,
            show_duplicates=args.show_duplicates,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
