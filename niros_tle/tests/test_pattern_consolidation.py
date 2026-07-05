"""Tests for Universal Pattern Consolidation Engine."""

from __future__ import annotations

import json

import pytest

from niros_tle.pattern_consolidation import (
    PatternCluster,
    UniversalPatternConsolidator,
)
from niros_tle.pattern_contract import TLEPatternRecord, validate_tle_pattern_record


def _agency_record(
    *,
    pattern_id: str,
    source_family: str,
    name: str,
    evidence_note: str,
    good_for: tuple[str, ...] = ("low_agency", "hopelessness"),
    semantic_cluster: tuple[str, ...] = ("agency", "growth", "future", "choice"),
    language_style: tuple[str, ...] = ("future_orientation", "incremental_steps"),
    delivery_formats: tuple[str, ...] = ("text", "voice"),
) -> TLEPatternRecord:
    return TLEPatternRecord(
        id=pattern_id,
        name=name,
        psychological_function=("agency", "self_efficacy", "hope"),
        good_for=good_for,
        avoid_if=("mania_risk", "psychosis_risk"),
        language_style=language_style,
        rhythm="slow_repetitive",
        semantic_cluster=semantic_cluster,
        spiritual_compatibility=("secular", "agnostic"),
        requires_symbols=(),
        forbidden_symbols=(),
        intensity="medium",
        directness="medium",
        repetition_level="medium",
        safety_notes=("Avoid grandiose empowerment claims",),
        source_family=(source_family,),
        source_confidence="high",
        extraction_method="manual_seed",
        evidence_refs=(
            {
                "source_family": source_family,
                "reference_type": "conceptual",
                "note": evidence_note,
            },
        ),
        notes=f"Extracted from {source_family}.",
        delivery_formats=delivery_formats,
        example_use_case="Low agency or hopelessness.",
    )


def _acceptance_record(
    *,
    pattern_id: str,
    source_family: str,
) -> TLEPatternRecord:
    return TLEPatternRecord(
        id=pattern_id,
        name="Acceptance Loop",
        psychological_function=("acceptance", "defusion"),
        good_for=("intrusive_thoughts", "resistance"),
        avoid_if=("psychosis_risk",),
        language_style=("permission_based", "non_confrontational"),
        rhythm="slow",
        semantic_cluster=("acceptance", "thought", "permission"),
        spiritual_compatibility=("secular", "agnostic"),
        requires_symbols=(),
        forbidden_symbols=(),
        intensity="low",
        directness="low",
        repetition_level="low",
        safety_notes=("Avoid strong identity claims",),
        source_family=(source_family,),
        source_confidence="medium",
        extraction_method="manual_seed",
        evidence_refs=(
            {
                "source_family": source_family,
                "reference_type": "conceptual",
                "note": "Acceptance-oriented conceptual extraction.",
            },
        ),
    )


@pytest.fixture
def consolidator() -> UniversalPatternConsolidator:
    return UniversalPatternConsolidator()


def test_single_pattern_forms_one_cluster(consolidator: UniversalPatternConsolidator):
    record = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
    )
    consolidator.add_pattern(record)
    clusters = consolidator.build_clusters()

    assert len(clusters) == 1
    assert clusters[0].support_level == "single_source"
    assert clusters[0].supporting_patterns == ("agency_act",)


def test_equivalent_patterns_merge(consolidator: UniversalPatternConsolidator):
    act = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
    )
    erickson = _agency_record(
        pattern_id="agency_erickson",
        source_family="erickson",
        name="Agency Restoration Loop",
        evidence_note="Ericksonian agency extraction.",
    )
    ifs = _agency_record(
        pattern_id="agency_ifs",
        source_family="ifs",
        name="Agency Restoration Loop",
        evidence_note="IFS agency extraction.",
    )

    for record in (act, erickson, ifs):
        consolidator.add_pattern(record)

    clusters = consolidator.build_clusters()
    assert len(clusters) == 1
    cluster = clusters[0]
    assert set(cluster.supporting_patterns) == {"agency_act", "agency_erickson", "agency_ifs"}
    assert set(cluster.supporting_sources) == {"act", "erickson", "ifs"}
    assert cluster.canonical_pattern.name == "Universal Agency Pattern"


def test_different_patterns_remain_separate(consolidator: UniversalPatternConsolidator):
    agency = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
    )
    acceptance = _acceptance_record(pattern_id="acceptance_act", source_family="act")

    consolidator.add_pattern(agency)
    consolidator.add_pattern(acceptance)

    clusters = consolidator.build_clusters()
    assert len(clusters) == 2
    assert {cluster.canonical_pattern.id for cluster in clusters} == {
        "agency_act",
        "acceptance_act",
    }


def test_source_provenance_preserved(consolidator: UniversalPatternConsolidator):
    act = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
    )
    ifs = _agency_record(
        pattern_id="agency_ifs",
        source_family="ifs",
        name="Agency Restoration Loop",
        evidence_note="IFS agency extraction.",
    )
    consolidator.add_pattern(act)
    consolidator.add_pattern(ifs)

    cluster = consolidator.build_clusters()[0]
    assert cluster.supporting_patterns == ("agency_act", "agency_ifs")
    assert cluster.supporting_sources == ("act", "ifs")
    assert "agency_act" in cluster.canonical_pattern.notes
    assert "agency_ifs" in cluster.canonical_pattern.notes


def test_evidence_preserved(consolidator: UniversalPatternConsolidator):
    act = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
    )
    ifs = _agency_record(
        pattern_id="agency_ifs",
        source_family="ifs",
        name="Agency Restoration Loop",
        evidence_note="IFS agency extraction.",
    )
    consolidator.add_pattern(act)
    consolidator.add_pattern(ifs)

    canonical = consolidator.export_universal_patterns()[0]
    notes = {ref["note"] for ref in canonical.evidence_refs}
    assert "ACT agency extraction." in notes
    assert "IFS agency extraction." in notes


def test_support_level_updated(consolidator: UniversalPatternConsolidator):
    psychotherapy = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
        delivery_formats=("text",),
    )
    indigenous = _agency_record(
        pattern_id="agency_shipibo",
        source_family="shipibo",
        name="Agency Restoration Loop",
        evidence_note="Shipibo agency extraction.",
        delivery_formats=("voice", "icaro"),
    )
    consolidator.add_pattern(psychotherapy)
    consolidator.add_pattern(indigenous)

    cluster = consolidator.build_clusters()[0]
    assert cluster.support_level == "cross_modal"


def test_merged_lists_unique(consolidator: UniversalPatternConsolidator):
    first = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
        good_for=("low_agency", "hopelessness", "self_criticism"),
    )
    second = _agency_record(
        pattern_id="agency_ifs",
        source_family="ifs",
        name="Agency Restoration Loop",
        evidence_note="IFS agency extraction.",
        good_for=("low_agency", "hopelessness"),
    )
    consolidator.add_pattern(first)
    consolidator.add_pattern(second)

    canonical = consolidator.export_universal_patterns()[0]
    assert canonical.good_for == ("low_agency", "hopelessness", "self_criticism")
    assert len(canonical.good_for) == len(set(canonical.good_for))


def test_deterministic_output(consolidator: UniversalPatternConsolidator):
    records = (
        _agency_record(
            pattern_id="agency_ifs",
            source_family="ifs",
            name="Agency Restoration Loop",
            evidence_note="IFS agency extraction.",
        ),
        _agency_record(
            pattern_id="agency_act",
            source_family="act",
            name="Agency Restoration Loop",
            evidence_note="ACT agency extraction.",
        ),
    )
    for record in records:
        consolidator.add_pattern(record)

    first = consolidator.export_universal_patterns()
    second = consolidator.export_universal_patterns()
    assert [record.to_dict() for record in first] == [record.to_dict() for record in second]


def test_cluster_ids_deterministic(consolidator: UniversalPatternConsolidator):
    consolidator.add_pattern(
        _agency_record(
            pattern_id="agency_act",
            source_family="act",
            name="Agency Restoration Loop",
            evidence_note="ACT agency extraction.",
        )
    )
    consolidator.add_pattern(
        _agency_record(
            pattern_id="agency_ifs",
            source_family="ifs",
            name="Agency Restoration Loop",
            evidence_note="IFS agency extraction.",
        )
    )

    first_ids = [cluster.cluster_id for cluster in consolidator.build_clusters()]
    second_ids = [cluster.cluster_id for cluster in consolidator.build_clusters()]
    assert first_ids == second_ids
    assert first_ids == ["cluster_agency_01"]


def test_no_data_loss(consolidator: UniversalPatternConsolidator):
    act = _agency_record(
        pattern_id="agency_act",
        source_family="act",
        name="Agency Restoration Loop",
        evidence_note="ACT agency extraction.",
    )
    ifs = _agency_record(
        pattern_id="agency_ifs",
        source_family="ifs",
        name="Agency Restoration Loop",
        evidence_note="IFS agency extraction.",
    )
    consolidator.add_pattern(act)
    consolidator.add_pattern(ifs)

    cluster = consolidator.build_clusters()[0]
    assert isinstance(cluster, PatternCluster)
    validate_tle_pattern_record(cluster.canonical_pattern)

    serialized = json.dumps(cluster.canonical_pattern.to_dict())
    for source in ("act", "ifs"):
        assert source in serialized
    for pattern_id in ("agency_act", "agency_ifs"):
        assert pattern_id in cluster.canonical_pattern.notes
