"""Tests for Knowledge Consolidation Engine."""

from __future__ import annotations

import pytest

from niros.knowledge_consolidator import (
    ConsolidationSourceContext,
    KnowledgeConsolidator,
    REVIEW_MODE_CONSERVATIVE,
    POTENTIAL_NEW_CAUSAL_SUMMARY,
    POTENTIAL_NEW_WHY_SUMMARY,
    build_representative_extraction,
    candidate_is_auto_approvable,
    classify_mechanism,
    consolidation_reduction_ratio,
    is_front_matter,
    is_vague_book_summary,
    should_discard_from_consolidation,
    split_multi_mechanism_extraction,
)
from niros.ontology_context import load_ontology_context
from niros.semantic_knowledge_extraction import (
    collect_extraction_validation_issues,
    validate_semantic_knowledge_extraction,
)
from niros.knowledge_domain import KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE, KNOWLEDGE_DOMAIN_VOCAL_ICARO
from niros.semantic_knowledge_extraction import (
    ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
    ONTOLOGY_STATUS_ADDS_NEW_NUANCE,
    ONTOLOGY_STATUS_CONTRADICTION,
    ONTOLOGY_STATUS_KNOWN,
    ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
)
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id


def _extraction(
    *,
    source_id: str,
    segment_id: str,
    therapeutic_function: str,
    psychological_function: str = "",
    evidence_text: str = "Evidence text with enough meaningful therapeutic content.",
    mechanism_name: str = "",
    causal_process: str = "",
    why_this_is_a_mechanism: str = "Explains maintaining logic.",
    ontology_status: str = "",
    ontology_mechanism_id: str = "",
    confidence: float = 0.82,
) -> TherapeuticFunctionExtraction:
    return TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id(
            source_id,
            segment_id,
            therapeutic_function,
            psychological_function,
        ),
        source_id=source_id,
        segment_id=segment_id,
        therapeutic_function=therapeutic_function,
        psychological_function=psychological_function,
        evidence_text=evidence_text,
        mechanism_name=mechanism_name,
        mechanism_description=psychological_function,
        causal_process=causal_process,
        why_this_is_a_mechanism=why_this_is_a_mechanism,
        ontology_status=ontology_status,
        ontology_mechanism_id=ontology_mechanism_id,
        confidence=confidence,
        extractor="fake",
    )


def _context(source_id: str, family: str, domain: str = "psychotherapy") -> ConsolidationSourceContext:
    return ConsolidationSourceContext(
        source_id=source_id,
        source_family=family,
        domain=domain,
    )


def _consolidate(extractions, contexts):
    return KnowledgeConsolidator().consolidate(
        extractions,
        source_contexts=contexts,
        review_mode=REVIEW_MODE_CONSERVATIVE,
    )


def test_experiential_avoidance_variants_merge_into_one_ontology_candidate() -> None:
    extractions = (
        _extraction(
            source_id="book_a",
            segment_id="book_a_batch_001",
            therapeutic_function="experiential_avoidance",
            mechanism_name="Experiential Avoidance",
            causal_process="Avoiding painful thoughts maintains suffering.",
            ontology_mechanism_id="experiential_avoidance",
            ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
            evidence_text="Avoiding painful thoughts maintains suffering.",
        ),
        _extraction(
            source_id="book_b",
            segment_id="book_b_batch_004",
            therapeutic_function="control strategies",
            mechanism_name="Experiential Avoidance",
            causal_process="Suppressing internal experiences strengthens distress.",
            ontology_mechanism_id="experiential_avoidance",
            ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
            evidence_text="Suppressing internal experiences strengthens distress.",
        ),
        _extraction(
            source_id="book_c",
            segment_id="book_c_batch_010",
            therapeutic_function="happiness trap",
            mechanism_name="Experiential Avoidance",
            causal_process="Attempts to control emotions reinforce suffering.",
            ontology_mechanism_id="experiential_avoidance",
            ontology_status=ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
            evidence_text="Attempts to control emotions reinforce suffering.",
        ),
    )
    contexts = {
        "book_a": _context("book_a", "act"),
        "book_b": _context("book_b", "cft"),
        "book_c": _context("book_c", "ifs"),
    }

    result = _consolidate(extractions, contexts)

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.mechanism_key == "experiential_avoidance"
    assert candidate.canonical_name == "Experiential Avoidance"
    assert candidate.ontology_mechanism_id == "experiential_avoidance"
    assert candidate.mention_count == 3


def test_defusion_variants_merge_into_cognitive_fusion_candidate() -> None:
    extractions = (
        _extraction(
            source_id="book_a",
            segment_id="a1",
            therapeutic_function="cognitive_fusion",
            mechanism_name="Cognitive Fusion",
            causal_process="Entanglement with thoughts drives rigid behavior.",
            ontology_mechanism_id="cognitive_fusion",
            evidence_text="Stop struggling with thoughts and believe them literally.",
        ),
        _extraction(
            source_id="book_b",
            segment_id="b1",
            therapeutic_function="unhook from thoughts",
            mechanism_name="Cognitive Fusion",
            causal_process="Fused thoughts increase distress.",
            ontology_mechanism_id="cognitive_fusion",
            evidence_text="Unhook from thoughts without believing them.",
        ),
    )
    contexts = {"book_a": _context("book_a", "act"), "book_b": _context("book_b", "act")}

    candidate = _consolidate(extractions, contexts).candidates[0]

    assert candidate.mechanism_key == "cognitive_fusion"
    assert candidate.canonical_name == "Cognitive Fusion"
    assert candidate.mention_count == 2


def test_acceptance_and_defusion_never_merge() -> None:
    extractions = (
        _extraction(
            source_id="book_a",
            segment_id="a1",
            therapeutic_function="acceptance",
            mechanism_name="Acceptance of internal experience",
            causal_process="Allowing emotions reduces struggle.",
            ontology_mechanism_id="",
            ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
            evidence_text="Accept emotions without fighting them.",
        ),
        _extraction(
            source_id="book_b",
            segment_id="b1",
            therapeutic_function="cognitive_fusion",
            mechanism_name="Cognitive Fusion",
            causal_process="Thought entanglement amplifies distress.",
            ontology_mechanism_id="cognitive_fusion",
            evidence_text="See thoughts as thoughts.",
        ),
    )
    contexts = {"book_a": _context("book_a", "act"), "book_b": _context("book_b", "act")}

    candidates = _consolidate(extractions, contexts).candidates

    assert len(candidates) == 2
    assert {item.mechanism_key for item in candidates} == {
        "new_acceptance_of_internal_experience",
        "cognitive_fusion",
    }


def test_potential_new_mechanism_never_maps_to_existing_ontology() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="a1",
        therapeutic_function="experiential_avoidance",
        mechanism_name="Novel Body Guarding Loop",
        causal_process="Guarding reduces immediate pain but maintains disability.",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        evidence_text="Body guarding loop evidence with enough meaningful therapeutic content.",
    )

    candidate = _consolidate((extraction,), {"book_a": _context("book_a", "act")}).candidates[0]

    assert candidate.mechanism_key == "new_novel_body_guarding_loop"
    assert candidate.ontology_mechanism_id == ""
    assert candidate.canonical_name == "Novel Body Guarding Loop"


def test_unknown_mechanisms_remain_independent() -> None:
    extractions = (
        _extraction(
            source_id="book_a",
            segment_id="a1",
            mechanism_name="Novel Body Guarding Loop",
            therapeutic_function="body guarding",
            causal_process="Guarding maintains pain disability.",
            ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
            evidence_text="Guarding evidence with enough meaningful therapeutic content.",
        ),
        _extraction(
            source_id="book_b",
            segment_id="b1",
            mechanism_name="Novel Shutdown Loop",
            therapeutic_function="shutdown",
            causal_process="Shutdown narrows recovery behaviors.",
            ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
            evidence_text="Shutdown evidence with enough meaningful therapeutic content.",
        ),
    )
    contexts = {"book_a": _context("book_a", "act"), "book_b": _context("book_b", "act")}

    candidates = _consolidate(extractions, contexts).candidates

    assert len(candidates) == 2
    assert {item.mechanism_key for item in candidates} == {
        "new_novel_body_guarding_loop",
        "new_novel_shutdown_loop",
    }


def test_evidence_fragments_and_ids_preserved_after_merge() -> None:
    extractions = (
        _extraction(
            source_id="book_a",
            segment_id="book_a_batch_001",
            therapeutic_function="experiential_avoidance",
            mechanism_name="Experiential Avoidance",
            ontology_mechanism_id="experiential_avoidance",
            causal_process="Avoidance maintains suffering.",
            evidence_text="Book A evidence.",
        ),
        _extraction(
            source_id="book_b",
            segment_id="book_b_batch_002",
            therapeutic_function="experiential_avoidance",
            mechanism_name="Experiential Avoidance",
            ontology_mechanism_id="experiential_avoidance",
            causal_process="Control strategies backfire.",
            evidence_text="Book B evidence.",
        ),
    )
    contexts = {"book_a": _context("book_a", "act"), "book_b": _context("book_b", "cft")}

    candidate = _consolidate(extractions, contexts).candidates[0]

    assert candidate.source_ids == ("book_a", "book_b")
    assert candidate.segment_ids == ("book_a_batch_001", "book_b_batch_002")
    assert len(candidate.evidence_fragments) == 2


def test_multi_mechanism_extraction_splits_into_ontology_candidates() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="experiential avoidance and cognitive defusion",
        evidence_text=(
            "Avoid painful feelings while unhooking from thoughts using cognitive defusion "
            "with enough meaningful therapeutic content."
        ),
        causal_process="Both avoidance and fusion processes are explained in one passage.",
    )
    contexts = {"book_a": _context("book_a", "act")}

    result = _consolidate((extraction,), contexts)

    keys = {candidate.mechanism_key for candidate in result.candidates}
    assert keys == {"experiential_avoidance", "cognitive_fusion"}


def test_front_matter_extraction_is_filtered_out() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="experiential_avoidance",
        mechanism_name="Experiential Avoidance",
        ontology_mechanism_id="experiential_avoidance",
        causal_process="Avoidance maintains suffering.",
        evidence_text="Copyright 2024 Publisher. ISBN 978-0-000-0000-0. All rights reserved. Table of contents.",
    )

    assert is_front_matter(extraction) is True
    result = _consolidate((extraction,), {"book_a": _context("book_a", "act")})
    assert result.candidates == ()
    assert result.filtered_extractions == 1


def test_vague_book_summary_is_filtered_out() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="overview",
        evidence_text="This book helps readers understand psychological flexibility in general terms.",
    )

    assert is_vague_book_summary(extraction) is True
    result = _consolidate((extraction,), {"book_a": _context("book_a", "act")})
    assert result.candidates == ()


def test_consolidation_reduction_ratio_meets_target_for_ontology_mechanism() -> None:
    extractions = tuple(
        _extraction(
            source_id="book_a",
            segment_id=f"book_a_batch_{index:03d}",
            therapeutic_function="experiential_avoidance",
            mechanism_name="Experiential Avoidance",
            ontology_mechanism_id="experiential_avoidance",
            causal_process="Avoidance maintains suffering.",
            evidence_text=f"Evidence batch {index} with enough meaningful therapeutic content.",
        )
        for index in range(1, 11)
    )
    contexts = {"book_a": _context("book_a", "act")}

    result = _consolidate(extractions, contexts)
    ratio = consolidation_reduction_ratio(result.raw_extractions, len(result.candidates))

    assert ratio >= 0.8


def test_classify_mechanism_uses_ontology_canonical_name() -> None:
    classification = classify_mechanism(
        _extraction(
            source_id="book_a",
            segment_id="a1",
            therapeutic_function="experiential_avoidance",
            mechanism_name="Experiential Avoidance",
            ontology_mechanism_id="experiential_avoidance",
            causal_process="Avoidance maintains suffering.",
        )
    )

    assert classification.mechanism_key == "experiential_avoidance"
    assert classification.canonical_mechanism_name == "Experiential Avoidance"


def test_split_multi_mechanism_extraction_preserves_evidence() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="cognitive defusion and experiential avoidance",
        evidence_text="Shared evidence with enough meaningful therapeutic content.",
        causal_process="Both mechanisms are explained.",
    )

    split_items = split_multi_mechanism_extraction(extraction)

    assert len(split_items) >= 2
    assert all(item.evidence_text == extraction.evidence_text for item in split_items)


def test_legacy_extraction_without_ontology_match_still_produces_candidate() -> None:
    extraction = TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id("book_a", "book_a_batch_001", "accept emotions", "reduce experiential avoidance"),
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="accept emotions",
        psychological_function="reduce experiential avoidance",
        evidence_text=(
            "When a client notices urges to avoid painful feelings, short-term relief appears "
            "but long-term suffering increases because experiential avoidance moves them away "
            "from valued action."
        ),
        confidence=0.85,
        extractor="fake",
    )
    result = _consolidate((extraction,), {"book_a": _context("book_a", "act")})

    assert len(result.candidates) == 1
    assert result.filtered_extractions == 0


def test_consolidated_candidate_includes_non_empty_reasoning_summaries() -> None:
    extraction = TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id("book_a", "book_a_batch_001", "accept emotions", "reduce experiential avoidance"),
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="accept emotions",
        psychological_function="reduce experiential avoidance",
        evidence_text=(
            "When a client notices urges to avoid painful feelings, short-term relief appears "
            "but long-term suffering increases because experiential avoidance moves them away "
            "from valued action."
        ),
        confidence=0.85,
        extractor="fake",
    )
    candidate = _consolidate((extraction,), {"book_a": _context("book_a", "act")}).candidates[0]

    assert candidate.causal_process_summary.strip()
    assert candidate.why_extraction_summary.strip()


def test_representative_extraction_passes_validation_for_legacy_candidate() -> None:
    extraction = TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id("book_a", "book_a_batch_001", "accept emotions", "reduce experiential avoidance"),
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="accept emotions",
        psychological_function="reduce experiential avoidance",
        evidence_text=(
            "When a client notices urges to avoid painful feelings, short-term relief appears "
            "but long-term suffering increases because experiential avoidance moves them away "
            "from valued action."
        ),
        confidence=0.85,
        extractor="fake",
    )
    candidate = _consolidate((extraction,), {"book_a": _context("book_a", "act")}).candidates[0]

    representative = build_representative_extraction(candidate)

    assert representative.causal_process.strip()
    assert representative.why_this_is_a_mechanism.strip()
    assert collect_extraction_validation_issues(representative) == ()


def test_potential_new_mechanism_gets_safe_fallback_reasoning() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        mechanism_name="Novel Shutdown Loop",
        therapeutic_function="shutdown",
        causal_process="Shutdown narrows recovery behaviors over time.",
        why_this_is_a_mechanism="Explains a maintaining loop.",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        evidence_text="Shutdown evidence with enough meaningful therapeutic content for review.",
    )
    candidate = _consolidate((extraction,), {"book_a": _context("book_a", "act")}).candidates[0]

    assert candidate.causal_process_summary == "Shutdown narrows recovery behaviors over time."
    assert candidate.why_extraction_summary == "Explains a maintaining loop."

    fallback_extraction = TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id("book_b", "book_b_batch_001", "body guarding", ""),
        source_id="book_b",
        segment_id="book_b_batch_001",
        therapeutic_function="body guarding",
        psychological_function="",
        mechanism_name="Novel Body Guarding Loop",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        causal_process="Guarding reduces immediate pain but maintains disability over time.",
        evidence_text="Guarding evidence with enough meaningful therapeutic content for review.",
        confidence=0.85,
        extractor="fake",
    )
    fallback_candidate = _consolidate(
        (fallback_extraction,),
        {"book_b": _context("book_b", "act")},
    ).candidates[0]

    assert fallback_candidate.causal_process_summary == (
        "Guarding reduces immediate pain but maintains disability over time."
    )
    assert fallback_candidate.why_extraction_summary.strip()
    assert collect_extraction_validation_issues(
        build_representative_extraction(fallback_candidate)
    ) == ()


def test_experiential_avoidance_candidate_uses_mechanism_fallback_when_reasoning_missing() -> None:
    extraction = TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id("book_a", "book_a_batch_001", "control strategies", ""),
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="control strategies",
        psychological_function="",
        ontology_mechanism_id="experiential_avoidance",
        evidence_text=(
            "When a client notices urges to avoid painful feelings, short-term relief appears "
            "but long-term suffering increases because experiential avoidance moves them away "
            "from valued action."
        ),
        confidence=0.85,
        extractor="fake",
    )
    candidate = _consolidate((extraction,), {"book_a": _context("book_a", "act")}).candidates[0]

    assert candidate.mechanism_key == "experiential_avoidance"
    assert candidate.causal_process_summary.strip()
    assert "therapeutic mechanism" in candidate.why_extraction_summary


def test_validation_is_not_weakened_for_invalid_semantic_extraction() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="values clarification",
        mechanism_name="Values Clarification",
        ontology_status=ONTOLOGY_STATUS_KNOWN,
        evidence_text="Values clarification is important in ACT.",
    )

    assert should_discard_from_consolidation(extraction) is True
    assert validate_semantic_knowledge_extraction(extraction)


@pytest.mark.parametrize(
    "ontology_status",
    [
        ONTOLOGY_STATUS_KNOWN,
        ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
        ONTOLOGY_STATUS_ADDS_NEW_NUANCE,
        ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        ONTOLOGY_STATUS_CONTRADICTION,
    ],
)
def test_every_supported_ontology_status_produces_candidate(ontology_status: str) -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        mechanism_name="Novel Somatic Shutdown Loop",
        therapeutic_function="shutdown loop",
        causal_process="Shutdown reduces contact with threat cues but narrows recovery behaviors.",
        why_this_is_a_mechanism="Explains a maintaining loop.",
        ontology_status=ontology_status,
        evidence_text="Shutdown evidence with enough meaningful therapeutic content.",
    )
    result = _consolidate((extraction,), {"book_a": _context("book_a", "act")})

    assert len(result.candidates) == 1
    assert result.filtered_extractions == 0


def test_semantic_extraction_without_causal_content_is_discarded() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        therapeutic_function="values clarification",
        mechanism_name="Values Clarification",
        ontology_status=ONTOLOGY_STATUS_KNOWN,
        evidence_text="Values clarification is important in ACT.",
    )
    result = _consolidate((extraction,), {"book_a": _context("book_a", "act")})

    assert result.candidates == ()
    assert result.filtered_extractions == 1


def test_unknown_ontology_coverage_never_discards_valid_extraction() -> None:
    extraction = _extraction(
        source_id="book_a",
        segment_id="book_a_batch_001",
        mechanism_name="Novel Shutdown Loop",
        therapeutic_function="shutdown",
        causal_process="Shutdown narrows recovery behaviors over time.",
        why_this_is_a_mechanism="Maintaining logic is explained.",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        evidence_text="Shutdown evidence with enough meaningful therapeutic content for review.",
    )
    result = _consolidate((extraction,), {"book_a": _context("book_a", "act")})

    assert len(result.candidates) == 1
    assert result.candidates[0].mechanism_key == "new_novel_shutdown_loop"


def test_potential_new_without_source_causal_uses_safe_fallback_templates() -> None:
    context = load_ontology_context()
    extraction = TherapeuticFunctionExtraction(
        extraction_id=build_extraction_id("book_b", "book_b_batch_001", "body guarding", ""),
        source_id="book_b",
        segment_id="book_b_batch_001",
        therapeutic_function="body guarding",
        psychological_function="",
        mechanism_name="Novel Body Guarding Loop",
        ontology_status=ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        evidence_text="Guarding evidence with enough meaningful therapeutic content for review.",
        confidence=0.85,
        extractor="fake",
    )
    candidate = KnowledgeConsolidator(ontology_context=context).consolidate(
        (extraction,),
        source_contexts={"book_b": _context("book_b", "act")},
        review_mode=REVIEW_MODE_CONSERVATIVE,
    ).candidates[0]

    assert candidate.causal_process_summary == POTENTIAL_NEW_CAUSAL_SUMMARY
    assert candidate.why_extraction_summary == POTENTIAL_NEW_WHY_SUMMARY


def test_auto_approve_requires_known_ontology_mechanism() -> None:
    from niros.knowledge_consolidator import ConsolidatedCandidatePattern, EvidenceFragment

    candidate = ConsolidatedCandidatePattern(
        candidate_id="candidate_test",
        canonical_name="Experiential Avoidance",
        therapeutic_function="experiential_avoidance",
        psychological_function="",
        description="test",
        mechanism_key="experiential_avoidance",
        mechanism_family="experiential_avoidance",
        ontology_mechanism_id="experiential_avoidance",
        evidence_fragments=(
            EvidenceFragment(
                extraction_id="e1",
                source_id="book_a",
                segment_id="book_a_batch_001",
                source_family="act",
                domain="psychotherapy",
                therapeutic_function="experiential_avoidance",
                psychological_function="",
                evidence_text="Evidence with enough meaningful therapeutic content.",
                confidence=0.9,
                mechanism_key="experiential_avoidance",
            ),
            EvidenceFragment(
                extraction_id="e2",
                source_id="book_b",
                segment_id="book_b_batch_001",
                source_family="act",
                domain="psychotherapy",
                therapeutic_function="experiential_avoidance",
                psychological_function="",
                evidence_text="More evidence with enough meaningful therapeutic content.",
                confidence=0.9,
                mechanism_key="experiential_avoidance",
            ),
        ),
        source_ids=("book_a", "book_b"),
        source_families=("act",),
        domains=("psychotherapy",),
        segment_ids=("book_a_batch_001", "book_b_batch_001"),
        source_count=2,
        book_count=2,
        batch_count=2,
        mention_count=2,
        confidence_summary="high",
        mean_confidence=0.9,
        generation_rules=(),
        voice_rules=(),
        repetition_rules=(),
        pause_rules=(),
        symbolic_elements=(),
        candidate_targets=(),
        contraindications=(),
    )

    assert candidate_is_auto_approvable(
        candidate,
        source_type="text",
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
        auto_approve=True,
    )
    assert not candidate_is_auto_approvable(
        candidate,
        source_type="text",
        knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
        auto_approve=True,
    )
    assert not candidate_is_auto_approvable(
        candidate,
        source_type="audio_extract",
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
        auto_approve=True,
    )
