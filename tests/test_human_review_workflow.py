"""Tests for human review workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from niros.human_review_workflow import (
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_CHANGES_REQUESTED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_REJECTED,
    HumanReviewValidationError,
    HumanReviewWorkflow,
    build_review_id,
    effective_extraction,
)
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.therapeutic_extraction import TherapeuticFunctionExtraction


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    base = {
        "extraction_id": "extraction_source_001_segment_001_self_compassion",
        "source_id": "source_001",
        "segment_id": "source_001_segment_001",
        "therapeutic_function": "self_compassion",
        "evidence_text": "May the heart be softened and fear released.",
        "confidence": 0.85,
        "extractor": "openai",
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def _workflow(tmp_path: Path) -> HumanReviewWorkflow:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    return HumanReviewWorkflow(
        paths=paths,
        timestamp_fn=lambda: "2026-07-06T12:00:00+00:00",
    )


def test_create_pending_review_from_extraction(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    record = workflow.create_pending_review(_extraction())

    assert record.review_id == build_review_id(_extraction().extraction_id)
    assert record.status == REVIEW_STATUS_PENDING
    assert record.original_extraction == _extraction()
    assert record.edited_extraction is None
    assert record.created_at == "2026-07-06T12:00:00+00:00"


def test_approve_review(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    workflow.save_review(pending)

    approved = workflow.approve(
        pending.review_id,
        reviewer_id="reviewer_001",
        reviewer_notes="Looks grounded in the source segment.",
    )
    workflow.save_review(approved)

    loaded = workflow.load_review(pending.review_id)
    assert loaded.status == REVIEW_STATUS_APPROVED
    assert loaded.reviewer_id == "reviewer_001"
    assert effective_extraction(loaded) == _extraction()


def test_reject_review_with_notes(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    workflow.save_review(pending)

    rejected = workflow.reject(
        pending.review_id,
        notes="Mechanism not supported by the text.",
        reviewer_id="reviewer_001",
    )
    workflow.save_review(rejected)

    loaded = workflow.load_review(pending.review_id)
    assert loaded.status == REVIEW_STATUS_REJECTED
    assert loaded.reviewer_notes == "Mechanism not supported by the text."
    assert effective_extraction(loaded) is None


def test_request_changes_with_notes(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    workflow.save_review(pending)

    updated = workflow.request_changes(
        pending.review_id,
        notes="Clarify symbolic elements.",
        reviewer_id="reviewer_001",
    )
    workflow.save_review(updated)

    loaded = workflow.load_review(pending.review_id)
    assert loaded.status == REVIEW_STATUS_CHANGES_REQUESTED
    assert loaded.reviewer_notes == "Clarify symbolic elements."
    assert effective_extraction(loaded) is None


def test_edit_extraction_and_approve_edited_version(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    workflow.save_review(pending)

    workflow.request_changes(pending.review_id, notes="Tighten wording.")
    edited = _extraction(
        psychological_function="reduce self-criticism",
        symbolic_elements=("heart", "water"),
    )
    edited_record = workflow.edit_extraction(pending.review_id, edited)
    approved = workflow.approve(edited_record.review_id, reviewer_id="reviewer_001")
    workflow.save_review(approved)

    loaded = workflow.load_review(pending.review_id)
    assert loaded.status == REVIEW_STATUS_APPROVED
    assert loaded.edited_extraction == edited
    assert effective_extraction(loaded) == edited


def test_save_and_load_review_json(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    record = workflow.create_pending_review(_extraction())
    output_path = workflow.save_review(record)

    loaded = workflow.load_review(record.review_id)
    assert output_path.exists()
    assert loaded == record


def test_invalid_edited_extraction_fails(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    workflow.save_review(pending)

    invalid = _extraction(therapeutic_function="", evidence_text="")
    with pytest.raises(HumanReviewValidationError) as exc_info:
        workflow.edit_extraction(pending.review_id, invalid)

    message = str(exc_info.value)
    assert "therapeutic_function must not be empty" in message
    assert "evidence_text must not be empty" in message


def test_workflow_does_not_write_into_ctpc_folder(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    approved = workflow.approve(pending.review_id)
    workflow.save_review(approved)

    ctpc_dir = Path(workflow.paths.ctpc_dir)
    assert ctpc_dir.exists()
    assert list(ctpc_dir.iterdir()) == []
