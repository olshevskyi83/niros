"""Tests for human review workflow."""

from __future__ import annotations

import json
from dataclasses import replace
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
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_UNKNOWN,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.semantic_knowledge_extraction import ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id


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
        "evidence_text": "May the heart be softened and fear released.",
        "confidence": 0.85,
        "extractor": "openai",
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def _experiential_avoidance_extraction(**overrides) -> TherapeuticFunctionExtraction:
    source_id = overrides.get("source_id", "book_a")
    segment_id = overrides.get("segment_id", "book_a_batch_001")
    therapeutic_function = overrides.get("therapeutic_function", "experiential_avoidance")
    psychological_function = overrides.get(
        "psychological_function",
        (
            "Attempts to avoid painful internal experiences reduce distress briefly but "
            "maintain long-term suffering and reduce valued action."
        ),
    )
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
        "evidence_text": (
            "When painful feelings arise, the client uses control or avoidance strategies. "
            "Short-term relief appears, but valued action narrows and suffering persists over time."
        ),
        "mechanism_name": "Experiential Avoidance",
        "ontology_status": ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
        "ontology_mechanism_id": "experiential_avoidance",
        "causal_process": (
            "Painful thoughts and feelings trigger control or avoidance strategies. "
            "These strategies reduce distress briefly but reinforce avoidance and narrow "
            "behavior over time."
        ),
        "why_this_is_a_mechanism": (
            "This describes a maintaining loop linking internal distress, avoidance behavior, "
            "short-term relief, and long-term suffering."
        ),
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


def _create_pending(
    workflow: HumanReviewWorkflow,
    *,
    knowledge_domain: str = KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
) -> HumanReviewRecord:
    return workflow.create_pending_review(
        _extraction(),
        knowledge_domain=knowledge_domain,
    )


def test_create_pending_consolidated_review_and_approve(tmp_path: Path) -> None:
    from niros.knowledge_consolidator import (
        ConsolidationSourceContext,
        KnowledgeConsolidator,
    )
    from niros.ctpc_compiler import CTPCCompiler

    workflow = _workflow(tmp_path)
    extractions = (
        _experiential_avoidance_extraction(
            source_id="book_a",
            segment_id="book_a_batch_001",
        ),
        _experiential_avoidance_extraction(
            source_id="book_b",
            segment_id="book_b_batch_002",
            evidence_text=(
                "The client notices urges to escape uncomfortable emotions and chooses avoidance. "
                "Relief is immediate, but avoidance maintains distance from what matters over time."
            ),
        ),
    )
    candidate = KnowledgeConsolidator().consolidate(
        extractions,
        source_contexts={
            "book_a": ConsolidationSourceContext("book_a", "act", "psychotherapy"),
            "book_b": ConsolidationSourceContext("book_b", "cft", "psychotherapy"),
        },
    ).candidates[0]
    pending = workflow.create_pending_consolidated_review(
        candidate,
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    )
    approved = workflow.approve(pending.review_id, reviewer_id="reviewer_1")
    pattern = CTPCCompiler(paths=workflow.paths).compile_review(approved)

    assert pending.review_type == "consolidated_candidate"
    assert pending.consolidated_candidate is not None
    assert pending.review_id.startswith("review_candidate_")
    assert len(pending.review_id) < 64
    assert approved.original_extraction.generation_rules
    assert approved.original_extraction.voice_rules
    assert approved.status == REVIEW_STATUS_APPROVED
    assert pattern.therapeutic_function
    assert pattern.generation_rules
    assert pattern.voice_rules


def test_create_pending_review_from_extraction(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    record = workflow.create_pending_review(
        _extraction(),
        knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
    )

    assert record.review_id == build_review_id(_extraction().extraction_id)
    assert record.status == REVIEW_STATUS_PENDING
    assert record.original_extraction == _extraction()
    assert record.edited_extraction is None
    assert record.knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO
    assert record.created_at == "2026-07-06T12:00:00+00:00"


def test_approve_review(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = _create_pending(workflow)
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
    pending = _create_pending(workflow)
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
    pending = _create_pending(workflow)
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
    pending = _create_pending(workflow)
    workflow.save_review(pending)

    workflow.request_changes(pending.review_id, notes="Tighten wording.")
    edited = _extraction(
        psychological_function="reduce self-criticism",
        symbolic_elements=("heart", "water"),
    )
    edited_record = workflow.edit_extraction(pending.review_id, edited)
    expected_edited = replace(edited, extraction_id=pending.extraction_id)
    approved = workflow.approve(edited_record.review_id, reviewer_id="reviewer_001")
    workflow.save_review(approved)

    loaded = workflow.load_review(pending.review_id)
    assert loaded.status == REVIEW_STATUS_APPROVED
    assert loaded.review_id == pending.review_id
    assert loaded.edited_extraction == expected_edited
    assert effective_extraction(loaded) == expected_edited


def test_save_and_load_review_json(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    record = _create_pending(workflow)
    output_path = workflow.save_review(record)

    loaded = workflow.load_review(record.review_id)
    assert output_path.exists()
    assert loaded == record


def test_edit_extraction_normalizes_extraction_id(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = _create_pending(workflow)
    workflow.save_review(pending)

    edited = _extraction(psychological_function="reduce self-criticism")
    assert edited.extraction_id != pending.extraction_id

    updated = workflow.edit_extraction(pending.review_id, edited)

    assert updated.review_id == pending.review_id
    assert updated.edited_extraction is not None
    assert updated.edited_extraction.extraction_id == pending.extraction_id
    assert updated.edited_extraction.psychological_function == "reduce self-criticism"


def test_edit_extraction_rejects_mismatched_source_or_segment(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = _create_pending(workflow)
    workflow.save_review(pending)

    wrong_source = _extraction(source_id="other_source")
    with pytest.raises(HumanReviewValidationError, match="source_id must match"):
        workflow.edit_extraction(pending.review_id, wrong_source)

    wrong_segment = _extraction(segment_id="other_segment")
    with pytest.raises(HumanReviewValidationError, match="segment_id must match"):
        workflow.edit_extraction(pending.review_id, wrong_segment)


def test_invalid_edited_extraction_fails(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = _create_pending(workflow)
    workflow.save_review(pending)

    invalid = _extraction(therapeutic_function="", evidence_text="")
    with pytest.raises(HumanReviewValidationError) as exc_info:
        workflow.edit_extraction(pending.review_id, invalid)

    message = str(exc_info.value)
    assert "therapeutic_function must not be empty" in message
    assert "evidence_text must not be empty" in message


def test_cannot_approve_without_knowledge_domain(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    workflow.save_review(pending)

    with pytest.raises(HumanReviewValidationError, match="knowledge_domain"):
        workflow.approve(pending.review_id, reviewer_id="reviewer_001")


def test_assign_knowledge_domain_before_approval(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    workflow.save_review(pending)

    assigned = workflow.assign_knowledge_domain(
        pending.review_id,
        KNOWLEDGE_DOMAIN_VOCAL_ICARO,
    )
    approved = workflow.approve(assigned.review_id, reviewer_id="reviewer_001")

    assert assigned.knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO
    assert approved.knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO


def test_legacy_review_without_domain_deserializes_as_unknown(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = workflow.create_pending_review(_extraction())
    review_path = workflow.save_review(pending)
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    payload.pop("knowledge_domain", None)
    review_path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = workflow.load_review(pending.review_id)

    assert loaded.knowledge_domain == KNOWLEDGE_DOMAIN_UNKNOWN


def test_workflow_does_not_write_into_ctpc_folder(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    pending = _create_pending(workflow)
    approved = workflow.approve(pending.review_id)
    workflow.save_review(approved)

    ctpc_dir = Path(workflow.paths.ctpc_dir)
    assert ctpc_dir.exists()
    assert list(ctpc_dir.rglob("*.json")) == []
