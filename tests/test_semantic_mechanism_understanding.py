"""Tests for semantic mechanism understanding layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from niros.knowledge_consolidator import (
    KnowledgeConsolidator,
    ConsolidationSourceContext,
    REVIEW_MODE_CONSERVATIVE,
    POTENTIAL_NEW_CAUSAL_SUMMARY,
    POTENTIAL_NEW_WHY_SUMMARY,
    build_representative_extraction,
)
from niros.ontology_context import (
    OntologyContext,
    clear_default_ontology_context_cache,
    load_ontology_context,
)
from niros.semantic_mechanism_understanding import (
    UNDERSTANDING_STATUS_ADDS_NEW_EVIDENCE,
    UNDERSTANDING_STATUS_POTENTIAL_NEW,
    UNDERSTANDING_STATUS_REJECTED,
    build_semantic_mechanism_understanding,
    is_keyword_only_extraction,
)
from niros.semantic_knowledge_extraction import (
    ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
    ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    validate_semantic_knowledge_extraction,
)
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id

FIXTURE_VAULT = Path("tests/fixtures/ontology_vault")


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_default_ontology_context_cache()
    yield
    clear_default_ontology_context_cache()


def _context() -> OntologyContext:
    return load_ontology_context(markdown_vault_root=FIXTURE_VAULT)


def _extraction(**kwargs) -> TherapeuticFunctionExtraction:
    defaults = {
        "extraction_id": build_extraction_id("book_a", "seg_001", "test", "desc"),
        "source_id": "book_a",
        "segment_id": "seg_001",
        "therapeutic_function": "experiential_avoidance",
        "psychological_function": "maintaining suffering through control",
        "evidence_text": (
            "When a client tries to suppress painful feelings, short-term relief appears "
            "but long-term suffering increases because avoidance moves them away from valued action."
        ),
        "confidence": 0.88,
        "extractor": "test",
    }
    defaults.update(kwargs)
    return TherapeuticFunctionExtraction(**defaults)


def test_known_mechanism_returns_adds_new_evidence_or_confirms() -> None:
    context = _context()
    extraction = _extraction(
        mechanism_name="Experiential Avoidance",
        causal_process=(
            "Trying to suppress emotions reduces short-term distress, therefore long-term "
            "suffering increases and valued action narrows."
        ),
        why_this_is_a_mechanism="Explains maintaining logic.",
        ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
    )
    understanding = build_semantic_mechanism_understanding(extraction, context=context)

    assert understanding.should_create_candidate is True
    assert understanding.ontology_mechanism_id == "experiential_avoidance"
    assert understanding.ontology_status in {
        UNDERSTANDING_STATUS_ADDS_NEW_EVIDENCE,
        "confirms_existing_mechanism",
    }


def test_unknown_meaningful_mechanism_becomes_potential_new() -> None:
    context = _context()
    extraction = _extraction(
        mechanism_name="Novel Body Guarding Loop",
        therapeutic_function="body guarding",
        causal_process=(
            "Body guarding reduces immediate pain signals but maintains disability by "
            "preventing normal movement and recovery behaviors."
        ),
        why_this_is_a_mechanism="Describes a somatic maintaining loop.",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    )
    understanding = build_semantic_mechanism_understanding(extraction, context=context)

    assert understanding.should_create_candidate is True
    assert understanding.ontology_status == UNDERSTANDING_STATUS_POTENTIAL_NEW
    assert understanding.ontology_mechanism_id == ""


def test_body_guarding_does_not_map_to_experiential_avoidance() -> None:
    context = _context()
    extraction = _extraction(
        mechanism_name="Novel Body Guarding Loop",
        therapeutic_function="body guarding",
        causal_process=(
            "Body guarding reduces immediate pain signals but maintains disability by "
            "preventing normal movement and recovery behaviors."
        ),
        why_this_is_a_mechanism="Describes a somatic maintaining loop.",
    )
    understanding = build_semantic_mechanism_understanding(extraction, context=context)

    assert understanding.ontology_mechanism_id != "experiential_avoidance"
    assert understanding.ontology_status == UNDERSTANDING_STATUS_POTENTIAL_NEW


def test_keyword_only_text_rejected() -> None:
    extraction = _extraction(
        mechanism_name="Acceptance",
        therapeutic_function="acceptance",
        evidence_text="Acceptance.",
        causal_process="",
        why_this_is_a_mechanism="",
        psychological_function="",
    )

    assert is_keyword_only_extraction(extraction) is True
    understanding = build_semantic_mechanism_understanding(extraction)
    assert understanding.should_create_candidate is False
    assert understanding.ontology_status == UNDERSTANDING_STATUS_REJECTED


def test_causal_process_accepted() -> None:
    context = _context()
    extraction = _extraction(
        mechanism_name="Experiential Avoidance",
        causal_process="Avoidance maintains suffering over time by narrowing valued action.",
        why_this_is_a_mechanism="Maintaining logic is explained.",
    )
    understanding = build_semantic_mechanism_understanding(extraction, context=context)

    assert understanding.should_create_candidate is True
    assert understanding.causal_process.strip()


def test_consolidated_candidate_has_non_empty_reasoning_summaries() -> None:
    context = _context()
    extraction = _extraction(
        mechanism_name="Experiential Avoidance",
        ontology_mechanism_id="experiential_avoidance",
        causal_process="Avoidance maintains suffering.",
        why_this_is_a_mechanism="Maintaining logic explained.",
    )
    result = KnowledgeConsolidator(ontology_context=context).consolidate(
        (extraction,),
        source_contexts={
            "book_a": ConsolidationSourceContext(
                source_id="book_a",
                source_family="act",
                domain="psychotherapy",
            )
        },
        review_mode=REVIEW_MODE_CONSERVATIVE,
    )
    candidate = result.candidates[0]

    assert candidate.causal_process_summary.strip()
    assert candidate.why_extraction_summary.strip()
    representative = build_representative_extraction(candidate)
    assert representative.causal_process.strip()
    assert representative.why_this_is_a_mechanism.strip()


def test_potential_new_without_source_causal_uses_fallback_templates() -> None:
    context = _context()
    extraction = _extraction(
        mechanism_name="Novel Body Guarding Loop",
        therapeutic_function="body guarding",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        evidence_text="Guarding evidence with enough meaningful therapeutic content for review.",
        causal_process="",
        why_this_is_a_mechanism="",
        psychological_function="",
    )
    candidate = KnowledgeConsolidator(ontology_context=context).consolidate(
        (extraction,),
        source_contexts={
            "book_a": ConsolidationSourceContext(
                source_id="book_a",
                source_family="act",
                domain="psychotherapy",
            )
        },
        review_mode=REVIEW_MODE_CONSERVATIVE,
    ).candidates[0]

    assert candidate.causal_process_summary == POTENTIAL_NEW_CAUSAL_SUMMARY
    assert candidate.why_extraction_summary == POTENTIAL_NEW_WHY_SUMMARY


def test_validation_is_not_weakened() -> None:
    extraction = _extraction(
        mechanism_name="Values Clarification",
        ontology_status="known",
        evidence_text="Values clarification is important in ACT.",
        causal_process="",
        why_this_is_a_mechanism="",
        psychological_function="",
    )
    issues = validate_semantic_knowledge_extraction(extraction)
    assert issues
