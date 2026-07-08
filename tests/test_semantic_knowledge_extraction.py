"""Tests for ontology-driven semantic knowledge extraction."""

from __future__ import annotations

import json

import pytest

from niros.knowledge_consolidator import (
    ConsolidationSourceContext,
    KnowledgeConsolidator,
    REVIEW_MODE_CONSERVATIVE,
    classify_mechanism_identity,
)
from niros.openai_semantic_extraction_adapter import (
    SemanticExtractionValidationError,
    parse_semantic_extraction_response_json,
)
from niros.ontology_context import clear_default_ontology_context_cache, load_ontology_context
from niros.semantic_knowledge_extraction import (
    ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
    ONTOLOGY_STATUS_KNOWN,
    ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    enrich_extraction_with_ontology,
    is_chapter_summary_extraction,
    is_definition_only_extraction,
    is_terminology_only_extraction,
    normalize_ontology_status,
    resolve_consolidation_mechanism_key,
    validate_semantic_knowledge_extraction,
)
from niros.semantic_extraction_prompt import build_semantic_extraction_prompt
from niros.raw_source import RawSource, RawSourceSegment
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id


@pytest.fixture(autouse=True)
def _clear_ontology_cache() -> None:
    clear_default_ontology_context_cache()
    yield
    clear_default_ontology_context_cache()


def _source() -> RawSource:
    return RawSource(
        source_id="source_act_book",
        source_family="act",
        title="ACT Book",
        language="en",
        source_type="text",
    )


def _segment(text: str, segment_id: str = "source_act_book_segment_001") -> RawSourceSegment:
    return RawSourceSegment(
        segment_id=segment_id,
        source_id="source_act_book",
        sequence_index=1,
        raw_text=text,
    )


def _extraction(
    *,
    source_id: str = "book_a",
    segment_id: str = "book_a_batch_001",
    therapeutic_function: str = "experiential_avoidance",
    evidence_text: str = "Evidence with enough meaningful therapeutic content.",
    mechanism_name: str = "",
    mechanism_description: str = "",
    why_this_is_a_mechanism: str = "",
    causal_process: str = "",
    ontology_status: str = "",
    ontology_mechanism_id: str = "",
    confidence: float = 0.86,
) -> TherapeuticFunctionExtraction:
    return TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id(
            source_id,
            segment_id,
            therapeutic_function,
            mechanism_description,
        ),
        source_id=source_id,
        segment_id=segment_id,
        therapeutic_function=therapeutic_function,
        psychological_function=mechanism_description,
        evidence_text=evidence_text,
        mechanism_name=mechanism_name,
        mechanism_description=mechanism_description,
        why_this_is_a_mechanism=why_this_is_a_mechanism,
        causal_process=causal_process,
        ontology_status=ontology_status,
        ontology_mechanism_id=ontology_mechanism_id,
        confidence=confidence,
        extractor="test",
    )


def _llm_payload(**extraction_overrides) -> str:
    extraction = {
        "mechanism_name": "Experiential Avoidance",
        "mechanism_description": "Attempts to escape internal experience maintain suffering.",
        "why_this_is_a_mechanism": "The passage explains maintaining logic, not a definition.",
        "causal_process": (
            "Trying to suppress emotions reduces short-term distress, therefore "
            "long-term suffering increases and valued action narrows."
        ),
        "evidence": "Trying to suppress emotions reduces short-term distress.",
        "ontology_status": "adds_new_evidence",
        "confidence": 0.91,
        "therapeutic_function": "experiential_avoidance",
        "psychological_function": "maintaining suffering through control",
        "symbolic_elements": [],
        "candidate_targets": ["emotional_avoidance"],
        "generation_rules": ["Use as a strategy principle."],
        "voice_rules": ["Use clear therapeutic language."],
        "repetition_rules": [],
        "pause_rules": [],
        "contraindications": [],
    }
    extraction.update(extraction_overrides)
    return json.dumps(
        {
            "relevance_decision": {
                "is_relevant": True,
                "relevance_score": 0.92,
                "knowledge_kind": "therapeutic_mechanism",
                "reasoning": "Explains a reusable causal mechanism.",
                "evidence_span": extraction["evidence"],
                "skip_reason": "",
                "suggested_mechanisms": ["experiential_avoidance"],
                "should_extract": True,
            },
            "extraction": extraction,
        }
    )


def test_prompt_behaves_as_psychotherapy_researcher() -> None:
    prompt = build_semantic_extraction_prompt(_source(), _segment("Example text"))
    assert "psychotherapy researcher" in prompt
    assert "mechanism_name" in prompt
    assert "ontology_status" in prompt
    assert "potential_new_mechanism" in prompt
    assert "definitions without causal process" in prompt


def test_definitions_are_rejected() -> None:
    extraction = _extraction(
        mechanism_name="Acceptance",
        mechanism_description="Acceptance is defined as openness to experience.",
        evidence_text="Acceptance is defined as openness to experience.",
    )
    assert is_definition_only_extraction(extraction) is True
    issues = validate_semantic_knowledge_extraction(extraction)
    assert issues


def test_chapter_summaries_are_rejected() -> None:
    extraction = _extraction(
        mechanism_name="Overview",
        mechanism_description="This chapter introduces ACT and its core ideas.",
        evidence_text="This chapter introduces ACT and its core ideas.",
        causal_process="This chapter introduces ACT and its core ideas.",
    )
    assert is_chapter_summary_extraction(extraction) is True


def test_terminology_only_chunks_are_rejected() -> None:
    extraction = _extraction(
        mechanism_name="Acceptance",
        therapeutic_function="acceptance",
        evidence_text="Acceptance.",
    )
    assert is_terminology_only_extraction(extraction) is True


def test_causal_explanations_are_extracted() -> None:
    result = parse_semantic_extraction_response_json(
        _llm_payload(),
        source_id="source_act_book",
        segment_id="source_act_book_segment_001",
        evidence_text="Trying to suppress emotions reduces short-term distress.",
    )
    assert result.extraction is not None
    assert "suppress emotions" in result.extraction.causal_process
    assert result.extraction.mechanism_name == "Experiential Avoidance"


def test_intervention_principles_are_extracted() -> None:
    payload = _llm_payload(
        mechanism_name="Values Clarification",
        ontology_status="known",
        causal_process=(
            "Values clarification increases willingness to experience difficult emotions "
            "because contact with what matters makes distress more tolerable."
        ),
    )
    result = parse_semantic_extraction_response_json(
        payload,
        source_id="source_act_book",
        segment_id="source_act_book_segment_001",
        evidence_text="Values clarification increases willingness.",
    )
    assert result.extraction is not None
    assert "willingness" in result.extraction.causal_process


def test_definition_payload_rejected_by_adapter() -> None:
    payload = _llm_payload(
        mechanism_name="Acceptance",
        mechanism_description="Acceptance is important.",
        why_this_is_a_mechanism="",
        causal_process="",
        evidence="Acceptance is important.",
    )
    with pytest.raises(SemanticExtractionValidationError):
        parse_semantic_extraction_response_json(
            payload,
            source_id="source_act_book",
            segment_id="source_act_book_segment_001",
            evidence_text="Acceptance is important.",
        )


def test_ontology_known_mechanisms_are_recognized() -> None:
    enriched = enrich_extraction_with_ontology(
        _extraction(
            mechanism_name="Experiential Avoidance",
            causal_process="Avoidance maintains suffering over time.",
            why_this_is_a_mechanism="Explains maintaining logic.",
            ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
        )
    )
    assert enriched.ontology_mechanism_id == "experiential_avoidance"
    assert normalize_ontology_status(enriched.ontology_status) in {
        ONTOLOGY_STATUS_KNOWN,
        ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
    }


def test_unknown_mechanisms_become_potential_new_mechanism() -> None:
    enriched = enrich_extraction_with_ontology(
        _extraction(
            mechanism_name="Novel Somatic Shutdown Loop",
            mechanism_description="A newly described shutdown pattern.",
            causal_process="Shutdown reduces contact with threat cues but narrows recovery behaviors.",
            why_this_is_a_mechanism="Introduces a new maintaining loop.",
            ontology_status="",
        )
    )
    assert enriched.ontology_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM
    assert enriched.ontology_mechanism_id == ""


def test_consolidation_merges_evidence_by_mechanism_not_wording() -> None:
    extractions = (
        _extraction(
            source_id="book_a",
            segment_id="book_a_batch_001",
            therapeutic_function="experiential_avoidance",
            mechanism_name="Experiential Avoidance",
            causal_process="Avoiding painful thoughts maintains suffering.",
            why_this_is_a_mechanism="Explains maintaining logic.",
            ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
            evidence_text="Avoiding painful thoughts maintains suffering.",
        ),
        _extraction(
            source_id="book_b",
            segment_id="book_b_batch_004",
            therapeutic_function="control internal experience",
            mechanism_name="Experiential Avoidance",
            causal_process="Suppressing internal experiences strengthens distress.",
            why_this_is_a_mechanism="Same mechanism, different wording.",
            ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
            evidence_text="Suppressing internal experiences strengthens distress.",
        ),
        _extraction(
            source_id="book_c",
            segment_id="book_c_batch_010",
            therapeutic_function="control emotions",
            mechanism_name="Experiential Avoidance",
            causal_process="Attempts to control emotions reinforce suffering.",
            why_this_is_a_mechanism="Same mechanism, different wording.",
            ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
            evidence_text="Attempts to control emotions reinforce suffering.",
        ),
    )
    contexts = {
        "book_a": ConsolidationSourceContext(source_id="book_a", source_family="act", domain="psychotherapy"),
        "book_b": ConsolidationSourceContext(source_id="book_b", source_family="cft", domain="psychotherapy"),
        "book_c": ConsolidationSourceContext(source_id="book_c", source_family="ifs", domain="psychotherapy"),
    }

    result = KnowledgeConsolidator().consolidate(
        extractions,
        source_contexts=contexts,
        review_mode=REVIEW_MODE_CONSERVATIVE,
    )

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.mechanism_key == "experiential_avoidance"
    assert candidate.ontology_mechanism_id == "experiential_avoidance"
    assert candidate.mention_count == 3
    assert len(candidate.evidence_fragments) == 3
    assert {fragment.source_id for fragment in candidate.evidence_fragments} == {
        "book_a",
        "book_b",
        "book_c",
    }


def test_evidence_fragments_preserved_after_ontology_merge() -> None:
    extractions = (
        _extraction(
            source_id="book_a",
            segment_id="book_a_batch_001",
            mechanism_name="Experiential Avoidance",
            causal_process="Avoidance maintains suffering.",
            why_this_is_a_mechanism="Maintaining logic explained.",
            evidence_text="Book A evidence fragment.",
        ),
        _extraction(
            source_id="book_b",
            segment_id="book_b_batch_002",
            mechanism_name="Experiential Avoidance",
            causal_process="Control strategies backfire.",
            why_this_is_a_mechanism="Maintaining logic explained.",
            evidence_text="Book B evidence fragment.",
        ),
    )
    contexts = {
        "book_a": ConsolidationSourceContext(source_id="book_a", source_family="act", domain="psychotherapy"),
        "book_b": ConsolidationSourceContext(source_id="book_b", source_family="act", domain="psychotherapy"),
    }
    candidate = KnowledgeConsolidator().consolidate(
        extractions,
        source_contexts=contexts,
        review_mode=REVIEW_MODE_CONSERVATIVE,
    ).candidates[0]
    texts = {fragment.evidence_text for fragment in candidate.evidence_fragments}
    assert "Book A evidence fragment." in texts
    assert "Book B evidence fragment." in texts


def test_classify_mechanism_identity_uses_ontology() -> None:
    extraction = _extraction(
        mechanism_name="Experiential Avoidance",
        ontology_mechanism_id="experiential_avoidance",
        causal_process="Avoidance maintains suffering.",
        why_this_is_a_mechanism="Maintaining logic explained.",
    )
    identity = classify_mechanism_identity(
        extraction,
        context=load_ontology_context(),
    )
    assert identity.mechanism_key == "experiential_avoidance"
    assert identity.canonical_mechanism_name == "Experiential Avoidance"


def test_resolve_consolidation_mechanism_key_for_unknown() -> None:
    extraction = _extraction(
        mechanism_name="Novel Body Guarding Loop",
        causal_process="Guarding reduces immediate pain but maintains disability.",
        why_this_is_a_mechanism="New maintaining loop.",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    )
    mechanism_key, _, canonical = resolve_consolidation_mechanism_key(
        extraction,
        context=load_ontology_context(),
    )
    assert mechanism_key == "new_novel_body_guarding_loop"
    assert canonical == "Novel Body Guarding Loop"


def test_potential_new_never_maps_to_experiential_avoidance() -> None:
    extraction = _extraction(
        mechanism_name="Novel Body Guarding Loop",
        therapeutic_function="experiential_avoidance",
        causal_process="Guarding reduces immediate pain but maintains disability.",
        why_this_is_a_mechanism="New maintaining loop.",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    )
    mechanism_key, _, _ = resolve_consolidation_mechanism_key(
        extraction,
        context=load_ontology_context(),
    )
    assert mechanism_key == "new_novel_body_guarding_loop"
    assert mechanism_key != "experiential_avoidance"


def test_collect_validation_issues_returns_all_errors() -> None:
    from niros.semantic_knowledge_extraction import collect_extraction_validation_issues

    extraction = _extraction(
        mechanism_name="",
        therapeutic_function="",
        evidence_text="",
        causal_process="",
    )
    issues = collect_extraction_validation_issues(extraction, require_semantic_knowledge=True)
    assert len(issues) >= 2
