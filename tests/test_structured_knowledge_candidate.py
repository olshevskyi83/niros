"""Tests for structured knowledge candidate builder."""

from __future__ import annotations

import json
from pathlib import Path

from niros.human_review_workflow import HumanReviewWorkflow
from niros.knowledge_consolidator import (
    ConsolidatedCandidatePattern,
    ConsolidationSourceContext,
    EvidenceFragment as ConsolidatedEvidenceFragment,
    KnowledgeConsolidator,
)
from niros.knowledge_domain import KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.semantic_knowledge_extraction import ONTOLOGY_STATUS_KNOWN
from niros.structured_knowledge_candidate import (
    build_structured_knowledge_candidate,
    deserialize_structured_knowledge_candidate,
    serialize_structured_knowledge_candidate,
)
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id
from niros.ui_knowledge_factory import (
    load_review_for_ui,
    structured_knowledge_for_record,
)


def _context(source_id: str, family: str) -> ConsolidationSourceContext:
    return ConsolidationSourceContext(source_id, family, "psychotherapy")


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    source_id = overrides.get("source_id", "book_a")
    segment_id = overrides.get("segment_id", "book_a_batch_001")
    therapeutic_function = overrides.get("therapeutic_function", "accept emotions")
    psychological_function = overrides.get("psychological_function", "reduce experiential avoidance")
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
            "When painful feelings arise, the client avoids contact with them and short-term "
            "relief appears, but long-term suffering increases because avoidance maintains "
            "distance from valued action."
        ),
        "mechanism_name": "Experiential Avoidance",
        "ontology_mechanism_id": "experiential_avoidance",
        "ontology_status": ONTOLOGY_STATUS_KNOWN,
        "causal_process": (
            "Triggering internal experience leads to avoidance behavior, which maintains "
            "experiential avoidance over time."
        ),
        "why_this_is_a_mechanism": (
            "This passage describes a self-reinforcing avoidance cycle rather than a one-off coping tactic."
        ),
        "candidate_targets": (
            "cognitive_fusion",
            "acceptance",
            "values clarification",
        ),
        "contraindications": ("acute psychosis",),
        "confidence": 0.9,
        "extractor": "fake",
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def _consolidated_candidate() -> ConsolidatedCandidatePattern:
    return KnowledgeConsolidator().consolidate(
        (
            _extraction(source_id="book_a", segment_id="book_a_batch_001"),
            _extraction(source_id="book_b", segment_id="book_b_batch_002"),
        ),
        source_contexts={
            "book_a": _context("book_a", "act"),
            "book_b": _context("book_b", "cft"),
        },
    ).candidates[0]


def _candidate_without_runtime_rules() -> ConsolidatedCandidatePattern:
    candidate = _consolidated_candidate()
    return ConsolidatedCandidatePattern(
        candidate_id=candidate.candidate_id,
        canonical_name=candidate.canonical_name,
        therapeutic_function=candidate.therapeutic_function,
        psychological_function=candidate.psychological_function,
        description=candidate.description,
        mechanism_key=candidate.mechanism_key,
        mechanism_family=candidate.mechanism_family,
        evidence_fragments=candidate.evidence_fragments,
        source_ids=candidate.source_ids,
        source_families=candidate.source_families,
        domains=candidate.domains,
        segment_ids=candidate.segment_ids,
        source_count=candidate.source_count,
        book_count=candidate.book_count,
        batch_count=candidate.batch_count,
        mention_count=candidate.mention_count,
        confidence_summary=candidate.confidence_summary,
        mean_confidence=candidate.mean_confidence,
        generation_rules=(),
        voice_rules=(),
        repetition_rules=(),
        pause_rules=(),
        symbolic_elements=(),
        candidate_targets=candidate.candidate_targets,
        contraindications=candidate.contraindications,
        ontology_status=candidate.ontology_status,
        ontology_mechanism_id=candidate.ontology_mechanism_id,
        causal_process_summary=candidate.causal_process_summary,
        why_extraction_summary=candidate.why_extraction_summary,
    )


def test_builds_structured_candidate_from_consolidated_candidate() -> None:
    candidate = _consolidated_candidate()
    structured = build_structured_knowledge_candidate(candidate)

    assert structured.candidate_id == candidate.candidate_id
    assert structured.mechanism_name == candidate.canonical_name
    assert structured.source_ids == candidate.source_ids
    assert structured.segment_ids == candidate.segment_ids
    assert structured.clinical_notes == candidate.why_extraction_summary.strip()


def test_preserves_evidence_fragments() -> None:
    candidate = _consolidated_candidate()
    structured = build_structured_knowledge_candidate(candidate)

    assert len(structured.evidence_fragments) == len(candidate.evidence_fragments)
    for structured_fragment, source_fragment in zip(
        structured.evidence_fragments,
        candidate.evidence_fragments,
        strict=True,
    ):
        assert structured_fragment.source_id == source_fragment.source_id
        assert structured_fragment.segment_id == source_fragment.segment_id
        assert structured_fragment.source_family == source_fragment.source_family
        assert structured_fragment.evidence_text == source_fragment.evidence_text.strip()
        assert structured_fragment.confidence == source_fragment.confidence
        assert "evidence" in structured_fragment.supports


def test_extracts_maintaining_process_from_causal_summary() -> None:
    candidate = _consolidated_candidate()
    structured = build_structured_knowledge_candidate(candidate)

    assert structured.maintaining_processes
    assert any(
        "maintain" in process.description.lower()
        for process in structured.maintaining_processes
    )


def test_keeps_related_mechanisms_separate_from_candidate_targets() -> None:
    candidate = _consolidated_candidate()
    structured = build_structured_knowledge_candidate(candidate)

    assert "cognitive_fusion" in structured.related_mechanisms
    assert "acceptance" not in structured.related_mechanisms
    assert "values clarification" not in structured.related_mechanisms
    assert candidate.candidate_targets != structured.related_mechanisms


def test_does_not_require_generation_rules() -> None:
    candidate = _candidate_without_runtime_rules()
    structured = build_structured_knowledge_candidate(candidate)

    assert structured.mechanism_name
    assert structured.evidence_fragments
    assert candidate.generation_rules == ()


def test_does_not_require_voice_rules() -> None:
    candidate = _candidate_without_runtime_rules()
    structured = build_structured_knowledge_candidate(candidate)

    assert structured.causal_chains
    assert candidate.voice_rules == ()


def test_includes_ontology_status_and_mechanism_id() -> None:
    candidate = _consolidated_candidate()
    structured = build_structured_knowledge_candidate(candidate)

    assert structured.ontology_status == candidate.ontology_status
    assert structured.mechanism_id == candidate.ontology_mechanism_id


def test_review_json_includes_structured_knowledge_candidate(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    workflow = HumanReviewWorkflow(paths=paths)
    candidate = _consolidated_candidate()
    pending = workflow.create_pending_consolidated_review(
        candidate,
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    )

    assert pending.consolidated_candidate is not None
    assert pending.structured_knowledge_candidate is not None

    saved_path = Path(paths.review_dir) / f"{pending.review_id}.json"
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    expected_consolidated = json.loads(json.dumps(pending.consolidated_candidate))
    expected_structured = json.loads(json.dumps(pending.structured_knowledge_candidate))
    assert payload["consolidated_candidate"] == expected_consolidated
    assert payload["structured_knowledge_candidate"] == expected_structured

    roundtrip = deserialize_structured_knowledge_candidate(
        payload["structured_knowledge_candidate"]
    )
    assert roundtrip.candidate_id == candidate.candidate_id
    assert roundtrip.mechanism_id == candidate.ontology_mechanism_id


def test_ui_loader_exposes_structured_knowledge_candidate(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    workflow = HumanReviewWorkflow(paths=paths)
    candidate = _consolidated_candidate()
    pending = workflow.create_pending_consolidated_review(
        candidate,
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    )
    loaded = workflow.load_review(pending.review_id)

    structured = structured_knowledge_for_record(loaded)
    assert structured is not None
    assert structured.mechanism_id == candidate.ontology_mechanism_id

    detail = load_review_for_ui(pending.review_id, str(root))
    assert detail.uses_structured_knowledge_review
    assert detail.structured_knowledge_candidate is not None
    assert detail.structured_knowledge_candidate["candidate_id"] == candidate.candidate_id
    assert detail.structured_knowledge_candidate["mechanism_id"] == candidate.ontology_mechanism_id
    assert detail.mechanism_name


def test_serialize_roundtrip_preserves_structured_fields() -> None:
    candidate = _consolidated_candidate()
    structured = build_structured_knowledge_candidate(candidate)
    payload = serialize_structured_knowledge_candidate(structured)
    restored = deserialize_structured_knowledge_candidate(payload)

    assert restored == structured


def test_maps_contraindications_from_consolidated_candidate() -> None:
    candidate = _consolidated_candidate()
    structured = build_structured_knowledge_candidate(candidate)

    assert structured.contraindications == candidate.contraindications


def test_builds_causal_chains_from_summary() -> None:
    fragment = ConsolidatedEvidenceFragment(
        extraction_id="ext_001",
        source_id="book_a",
        segment_id="book_a_batch_001",
        source_family="act",
        domain="psychotherapy",
        therapeutic_function="experiential_avoidance",
        psychological_function="reduce distress",
        evidence_text="Evidence about avoidance.",
        confidence=0.9,
        mechanism_key="experiential_avoidance",
        causal_process="Painful feeling leads to avoidance behavior.",
        why_this_is_a_mechanism="Avoidance is self-reinforcing.",
    )
    candidate = ConsolidatedCandidatePattern(
        candidate_id="candidate_test",
        canonical_name="Experiential Avoidance",
        therapeutic_function="experiential_avoidance",
        psychological_function="reduce distress",
        description="Avoidance mechanism",
        mechanism_key="experiential_avoidance",
        mechanism_family="act",
        evidence_fragments=(fragment,),
        source_ids=("book_a",),
        source_families=("act",),
        domains=("psychotherapy",),
        segment_ids=("book_a_batch_001",),
        source_count=1,
        book_count=1,
        batch_count=1,
        mention_count=1,
        confidence_summary="high",
        mean_confidence=0.9,
        generation_rules=(),
        voice_rules=(),
        repetition_rules=(),
        pause_rules=(),
        symbolic_elements=(),
        candidate_targets=(),
        contraindications=(),
        ontology_status=ONTOLOGY_STATUS_KNOWN,
        ontology_mechanism_id="experiential_avoidance",
        causal_process_summary="Painful feeling leads to avoidance behavior.",
        why_extraction_summary="Avoidance is self-reinforcing.",
    )

    structured = build_structured_knowledge_candidate(candidate)

    assert structured.causal_chains
    assert structured.causal_chains[0].trigger.lower().startswith("painful feeling")
    assert "avoidance" in structured.causal_chains[0].short_term_effect.lower()
