"""Human Review Workflow — file-based review for therapeutic function extractions."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_UNKNOWN,
    is_compilable_knowledge_domain,
    normalize_review_knowledge_domain,
)
from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    KnowledgeWorkspacePaths,
    build_knowledge_workspace_paths,
    knowledge_artifact_path,
)
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, validate_extraction

REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_REJECTED = "rejected"
REVIEW_STATUS_CHANGES_REQUESTED = "changes_requested"

REVIEW_TYPE_BATCH = "batch_extraction"
REVIEW_TYPE_CONSOLIDATED = "consolidated_candidate"

_EXTRACTION_TUPLE_FIELDS = (
    "symbolic_elements",
    "candidate_targets",
    "generation_rules",
    "voice_rules",
    "repetition_rules",
    "pause_rules",
    "contraindications",
)


class HumanReviewError(Exception):
    """Base error for human review workflow failures."""


class HumanReviewNotFoundError(HumanReviewError):
    """Raised when a review record cannot be found."""


class HumanReviewValidationError(HumanReviewError):
    """Raised when a review record or extraction fails validation."""


class HumanReviewStateError(HumanReviewError):
    """Raised when a review action is invalid for the current status."""


@dataclass(frozen=True)
class HumanReviewRecord:
    review_id: str
    extraction_id: str
    source_id: str
    segment_id: str
    status: str
    original_extraction: TherapeuticFunctionExtraction
    reviewer_id: str = ""
    reviewer_notes: str = ""
    edited_extraction: TherapeuticFunctionExtraction | None = None
    created_at: str = ""
    updated_at: str = ""
    knowledge_domain: str = KNOWLEDGE_DOMAIN_UNKNOWN
    review_type: str = REVIEW_TYPE_BATCH
    consolidated_candidate: dict[str, Any] | None = None
    structured_knowledge_candidate: dict[str, Any] | None = None
    therapeutic_relevance: dict[str, Any] | None = None


def build_review_id(extraction_id: str) -> str:
    """Build a deterministic review ID from one extraction ID."""
    return f"review_{extraction_id}"


def _default_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def serialize_extraction(extraction: TherapeuticFunctionExtraction) -> dict[str, Any]:
    """Return a JSON-serializable dictionary for one extraction."""
    data: dict[str, Any] = {
        "extraction_id": extraction.extraction_id,
        "source_id": extraction.source_id,
        "segment_id": extraction.segment_id,
        "therapeutic_function": extraction.therapeutic_function,
        "psychological_function": extraction.psychological_function,
        "evidence_text": extraction.evidence_text,
        "mechanism_name": extraction.mechanism_name,
        "mechanism_description": extraction.mechanism_description,
        "why_this_is_a_mechanism": extraction.why_this_is_a_mechanism,
        "causal_process": extraction.causal_process,
        "ontology_status": extraction.ontology_status,
        "ontology_mechanism_id": extraction.ontology_mechanism_id,
        "symbolic_elements": list(extraction.symbolic_elements),
        "generation_rules": list(extraction.generation_rules),
        "voice_rules": list(extraction.voice_rules),
        "repetition_rules": list(extraction.repetition_rules),
        "pause_rules": list(extraction.pause_rules),
        "candidate_targets": list(extraction.candidate_targets),
        "contraindications": list(extraction.contraindications),
        "confidence": extraction.confidence,
        "extractor": extraction.extractor,
        "review_status": extraction.review_status,
    }
    return data


def deserialize_extraction(data: dict[str, Any]) -> TherapeuticFunctionExtraction:
    """Build a TherapeuticFunctionExtraction from serialized data."""
    kwargs = dict(data)
    for field_name in _EXTRACTION_TUPLE_FIELDS:
        if field_name in kwargs and kwargs[field_name] is not None:
            kwargs[field_name] = tuple(kwargs[field_name])
    return TherapeuticFunctionExtraction(**kwargs)


def serialize_human_review_record(record: HumanReviewRecord) -> dict[str, Any]:
    """Return a JSON-serializable dictionary for one human review record."""
    payload: dict[str, Any] = {
        "review_id": record.review_id,
        "extraction_id": record.extraction_id,
        "source_id": record.source_id,
        "segment_id": record.segment_id,
        "status": record.status,
        "reviewer_id": record.reviewer_id,
        "reviewer_notes": record.reviewer_notes,
        "original_extraction": serialize_extraction(record.original_extraction),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "knowledge_domain": record.knowledge_domain,
        "review_type": record.review_type,
    }
    if record.edited_extraction is not None:
        payload["edited_extraction"] = serialize_extraction(record.edited_extraction)
    else:
        payload["edited_extraction"] = None
    if record.consolidated_candidate is not None:
        payload["consolidated_candidate"] = record.consolidated_candidate
    if record.structured_knowledge_candidate is not None:
        payload["structured_knowledge_candidate"] = record.structured_knowledge_candidate
    if record.therapeutic_relevance is not None:
        payload["therapeutic_relevance"] = record.therapeutic_relevance
    return payload


def deserialize_human_review_record(data: dict[str, Any]) -> HumanReviewRecord:
    """Build a HumanReviewRecord from serialized data."""
    edited_data = data.get("edited_extraction")
    edited_extraction = (
        deserialize_extraction(edited_data) if edited_data is not None else None
    )
    return HumanReviewRecord(
        review_id=data["review_id"],
        extraction_id=data["extraction_id"],
        source_id=data["source_id"],
        segment_id=data["segment_id"],
        status=data["status"],
        reviewer_id=data.get("reviewer_id", ""),
        reviewer_notes=data.get("reviewer_notes", ""),
        original_extraction=deserialize_extraction(data["original_extraction"]),
        edited_extraction=edited_extraction,
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        knowledge_domain=normalize_review_knowledge_domain(data.get("knowledge_domain")),
        review_type=data.get("review_type", REVIEW_TYPE_BATCH),
        consolidated_candidate=data.get("consolidated_candidate"),
        structured_knowledge_candidate=data.get("structured_knowledge_candidate"),
        therapeutic_relevance=data.get("therapeutic_relevance"),
    )


def effective_extraction(record: HumanReviewRecord) -> TherapeuticFunctionExtraction | None:
    """Return the extraction that would be used after approval, if any."""
    if record.status != REVIEW_STATUS_APPROVED:
        return None
    if record.edited_extraction is not None:
        return record.edited_extraction
    return record.original_extraction


def validate_human_review_record(record: HumanReviewRecord) -> tuple[str, ...]:
    """Return validation issue strings for one human review record."""
    issues: list[str] = []

    if not record.review_id.strip():
        issues.append("review_id must not be empty")
    if not record.extraction_id.strip():
        issues.append("extraction_id must not be empty")
    if not record.source_id.strip():
        issues.append("source_id must not be empty")
    if not record.segment_id.strip():
        issues.append("segment_id must not be empty")
    if not record.status.strip():
        issues.append("status must not be empty")

    if record.status == REVIEW_STATUS_APPROVED:
        approved_extraction = effective_extraction(record)
        if approved_extraction is None:
            issues.append("approved review must contain a valid extraction")
        else:
            issues.extend(validate_extraction(approved_extraction))
        if not is_compilable_knowledge_domain(record.knowledge_domain):
            issues.append("knowledge_domain must be assigned before approval")

    if record.edited_extraction is not None:
        issues.extend(validate_extraction(record.edited_extraction))

    return tuple(issues)


class HumanReviewWorkflow:
    """Manage pending, approved, rejected, and edited extraction reviews."""

    def __init__(
        self,
        workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
        *,
        paths: KnowledgeWorkspacePaths | None = None,
        timestamp_fn: Callable[[], str] | None = None,
    ) -> None:
        self.paths = paths or build_knowledge_workspace_paths(workspace_root)
        self._timestamp_fn = timestamp_fn or _default_timestamp

    def _review_path(self, review_id: str) -> Path:
        filename = f"{review_id}.json"
        return Path(
            knowledge_artifact_path(self.paths, "review", filename)
        )

    def _touch(self, record: HumanReviewRecord, *, created: bool = False) -> HumanReviewRecord:
        timestamp = self._timestamp_fn()
        if created:
            return replace(record, created_at=timestamp, updated_at=timestamp)
        return replace(record, updated_at=timestamp)

    def _require_valid_extraction(self, extraction: TherapeuticFunctionExtraction) -> None:
        issues = validate_extraction(extraction)
        if issues:
            joined = "; ".join(issues)
            raise HumanReviewValidationError(
                f"TherapeuticFunctionExtraction failed validation: {joined}"
            )

    def _require_status(self, record: HumanReviewRecord, allowed: tuple[str, ...]) -> None:
        if record.status not in allowed:
            allowed_text = ", ".join(allowed)
            raise HumanReviewStateError(
                f"Review {record.review_id} has status {record.status!r}; "
                f"expected one of: {allowed_text}."
            )

    def _persist_mutation(
        self,
        record: HumanReviewRecord,
        *,
        created: bool = False,
    ) -> HumanReviewRecord:
        touched = self._touch(record, created=created)
        self.save_review(touched)
        return touched

    def create_pending_review(
        self,
        extraction: TherapeuticFunctionExtraction,
        *,
        knowledge_domain: str = KNOWLEDGE_DOMAIN_UNKNOWN,
    ) -> HumanReviewRecord:
        """Create a pending human review record for one proposed extraction."""
        self._require_valid_extraction(extraction)
        record = HumanReviewRecord(
            review_id=build_review_id(extraction.extraction_id),
            extraction_id=extraction.extraction_id,
            source_id=extraction.source_id,
            segment_id=extraction.segment_id,
            status=REVIEW_STATUS_PENDING,
            original_extraction=extraction,
            knowledge_domain=normalize_review_knowledge_domain(knowledge_domain),
            review_type=REVIEW_TYPE_BATCH,
        )
        return self._persist_mutation(record, created=True)

    def create_pending_consolidated_review(
        self,
        candidate: Any,
        *,
        knowledge_domain: str = KNOWLEDGE_DOMAIN_UNKNOWN,
        therapeutic_relevance: dict[str, Any] | None = None,
    ) -> HumanReviewRecord:
        """Create a pending human review for one consolidated candidate pattern."""
        from niros.knowledge_consolidator import (
            ConsolidatedCandidatePattern,
            build_consolidated_review_id,
            build_representative_extraction,
            serialize_consolidated_candidate,
        )
        from niros.structured_knowledge_candidate import (
            build_structured_knowledge_candidate,
            serialize_structured_knowledge_candidate,
        )

        if not isinstance(candidate, ConsolidatedCandidatePattern):
            raise HumanReviewValidationError(
                "candidate must be a ConsolidatedCandidatePattern"
            )
        resolved_domain = normalize_review_knowledge_domain(knowledge_domain)
        extraction = build_representative_extraction(
            candidate,
            knowledge_domain=resolved_domain,
        )
        self._require_valid_extraction(extraction)
        record = HumanReviewRecord(
            review_id=build_consolidated_review_id(candidate.candidate_id),
            extraction_id=extraction.extraction_id,
            source_id=extraction.source_id,
            segment_id=candidate.candidate_id,
            status=REVIEW_STATUS_PENDING,
            original_extraction=extraction,
            knowledge_domain=resolved_domain,
            review_type=REVIEW_TYPE_CONSOLIDATED,
            consolidated_candidate=serialize_consolidated_candidate(candidate),
            structured_knowledge_candidate=serialize_structured_knowledge_candidate(
                build_structured_knowledge_candidate(candidate)
            ),
            therapeutic_relevance=therapeutic_relevance,
        )
        return self._persist_mutation(record, created=True)

    def assign_knowledge_domain(
        self,
        review_id: str,
        knowledge_domain: str,
    ) -> HumanReviewRecord:
        """Assign a compilable knowledge domain to one review."""
        record = self.load_review(review_id)
        self._require_status(record, (REVIEW_STATUS_PENDING, REVIEW_STATUS_CHANGES_REQUESTED))
        domain = normalize_review_knowledge_domain(knowledge_domain)
        if not is_compilable_knowledge_domain(domain):
            raise HumanReviewValidationError(
                "knowledge_domain must be psychotherapy_tle or vocal_icaro"
            )
        updated = replace(record, knowledge_domain=domain)
        return self._persist_mutation(updated)

    def approve(
        self,
        review_id: str,
        *,
        reviewer_id: str = "",
        reviewer_notes: str = "",
    ) -> HumanReviewRecord:
        """Approve a pending or changes-requested review."""
        record = self.load_review(review_id)
        self._require_status(record, (REVIEW_STATUS_PENDING, REVIEW_STATUS_CHANGES_REQUESTED))
        candidate = record.edited_extraction or record.original_extraction
        self._require_valid_extraction(candidate)
        if not is_compilable_knowledge_domain(record.knowledge_domain):
            raise HumanReviewValidationError(
                "knowledge_domain must be assigned before approval"
            )
        updated = replace(
            record,
            status=REVIEW_STATUS_APPROVED,
            reviewer_id=reviewer_id,
            reviewer_notes=reviewer_notes,
        )
        return self._persist_mutation(updated)

    def reject(
        self,
        review_id: str,
        notes: str = "",
        *,
        reviewer_id: str = "",
    ) -> HumanReviewRecord:
        """Reject a pending or changes-requested review."""
        record = self.load_review(review_id)
        self._require_status(record, (REVIEW_STATUS_PENDING, REVIEW_STATUS_CHANGES_REQUESTED))
        updated = replace(
            record,
            status=REVIEW_STATUS_REJECTED,
            reviewer_id=reviewer_id,
            reviewer_notes=notes,
        )
        return self._persist_mutation(updated)

    def request_changes(
        self,
        review_id: str,
        notes: str = "",
        *,
        reviewer_id: str = "",
    ) -> HumanReviewRecord:
        """Request changes on a pending review."""
        record = self.load_review(review_id)
        self._require_status(record, (REVIEW_STATUS_PENDING,))
        updated = replace(
            record,
            status=REVIEW_STATUS_CHANGES_REQUESTED,
            reviewer_id=reviewer_id,
            reviewer_notes=notes,
        )
        return self._persist_mutation(updated)

    def edit_extraction(
        self,
        review_id: str,
        edited_extraction: TherapeuticFunctionExtraction,
    ) -> HumanReviewRecord:
        """Attach a validated edited extraction to a review."""
        record = self.load_review(review_id)
        self._require_status(record, (REVIEW_STATUS_PENDING, REVIEW_STATUS_CHANGES_REQUESTED))
        if edited_extraction.source_id != record.source_id:
            raise HumanReviewValidationError(
                "edited_extraction source_id must match review source_id"
            )
        if edited_extraction.segment_id != record.segment_id:
            raise HumanReviewValidationError(
                "edited_extraction segment_id must match review segment_id"
            )
        normalized = edited_extraction
        if edited_extraction.extraction_id != record.extraction_id:
            normalized = replace(edited_extraction, extraction_id=record.extraction_id)
        self._require_valid_extraction(normalized)
        updated = replace(record, edited_extraction=normalized)
        return self._persist_mutation(updated)

    def save_review(self, record: HumanReviewRecord) -> Path:
        """Persist one human review record as JSON in the review workspace."""
        issues = validate_human_review_record(record)
        if issues:
            joined = "; ".join(issues)
            raise HumanReviewValidationError(
                f"HumanReviewRecord failed validation: {joined}"
            )
        output_path = self._review_path(record.review_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            serialize_human_review_record(record),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        output_path.write_text(payload + "\n", encoding="utf-8")
        return output_path

    def load_review(self, review_id: str) -> HumanReviewRecord:
        """Load one human review record from JSON."""
        input_path = self._review_path(review_id)
        if not input_path.exists():
            raise HumanReviewNotFoundError(f"Review not found: {review_id}")
        data = json.loads(input_path.read_text(encoding="utf-8"))
        return deserialize_human_review_record(data)
