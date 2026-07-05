"""Tests for Universal Pattern Evidence Engine."""

from __future__ import annotations

import json

import pytest

from niros_tle.pattern_consolidation import PatternCluster, UniversalPatternConsolidator
from niros_tle.pattern_contract import TLEPatternRecord
from niros_tle.pattern_evidence import (
    UniversalPatternEvidenceEngine,
    UniversalPatternEvidenceExport,
)


def _agency_record(
    *,
    pattern_id: str,
    source_family: str,
    evidence_note: str,
    psychological_function: tuple[str, ...] = ("agency", "self_efficacy", "hope"),
    semantic_cluster: tuple[str, ...] = ("agency", "growth", "future", "choice"),
) -> TLEPatternRecord:
    return TLEPatternRecord(
        id=pattern_id,
        name="Agency Restoration Loop",
        psychological_function=psychological_function,
        good_for=("low_agency", "hopelessness"),
        avoid_if=("mania_risk", "psychosis_risk"),
        language_style=("future_orientation", "incremental_steps"),
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
    )


def _identity_record(
    *,
    pattern_id: str,
    source_family: str,
    evidence_note: str,
) -> TLEPatternRecord:
    return TLEPatternRecord(
        id=pattern_id,
        name="Identity Reconstruction Loop",
        psychological_function=("identity", "values_clarity", "meaning"),
        good_for=("identity_confusion", "loss_of_meaning"),
        avoid_if=("psychosis_risk",),
        language_style=("exploratory", "reflective"),
        rhythm="gentle",
        semantic_cluster=("identity", "values", "meaning", "choice"),
        spiritual_compatibility=("secular", "agnostic", "spiritual_not_religious"),
        requires_symbols=(),
        forbidden_symbols=(),
        intensity="low",
        directness="low",
        repetition_level="low",
        safety_notes=("Avoid destiny or mission certainty",),
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
    )


def _build_cluster(*records: TLEPatternRecord) -> PatternCluster:
    consolidator = UniversalPatternConsolidator()
    for record in records:
        consolidator.add_pattern(record)
    return consolidator.build_clusters()[0]


@pytest.fixture
def engine() -> UniversalPatternEvidenceEngine:
    return UniversalPatternEvidenceEngine()


def test_single_source(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _agency_record(
            pattern_id="agency_act",
            source_family="act",
            evidence_note="ACT agency extraction.",
        )
    )
    export = engine.evaluate_cluster(cluster)

    assert export.evidence_report.source_count == 1
    assert export.evidence_report.support_level == "single_source"
    assert export.evidence_report.psychotherapy_families == ("act",)
    assert export.evidence_report.traditional_families == ()
    assert export.evidence_report.cross_cultural is False


def test_multi_source(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _agency_record(pattern_id="agency_act", source_family="act", evidence_note="ACT."),
        _agency_record(pattern_id="agency_erickson", source_family="erickson", evidence_note="Erickson."),
        _agency_record(pattern_id="agency_ifs", source_family="ifs", evidence_note="IFS."),
    )
    report = engine.build_report(cluster)

    assert report.source_count == 3
    assert report.psychotherapy_families == ("act", "erickson", "ifs")
    assert report.traditional_families == ()
    assert report.cross_cultural is False
    assert report.cross_theoretical is True
    assert report.confidence == "high"


def test_cross_cultural_support(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _identity_record(pattern_id="identity_act", source_family="act", evidence_note="ACT identity."),
        _identity_record(pattern_id="identity_ifs", source_family="ifs", evidence_note="IFS identity."),
        _identity_record(
            pattern_id="identity_shipibo",
            source_family="shipibo",
            evidence_note="Shipibo identity.",
        ),
        _identity_record(
            pattern_id="identity_maria_sabina",
            source_family="maria_sabina",
            evidence_note="Maria Sabina identity.",
        ),
    )
    report = engine.build_report(cluster)

    assert report.source_count == 4
    assert report.psychotherapy_families == ("act", "ifs")
    assert report.traditional_families == ("maria_sabina", "shipibo")
    assert report.cross_cultural is True
    assert report.confidence == "very_high"


def test_confidence_increases(engine: UniversalPatternEvidenceEngine):
    single = engine.build_report(
        _build_cluster(
            _agency_record(
                pattern_id="agency_act",
                source_family="act",
                evidence_note="ACT.",
            )
        )
    )
    triple = engine.build_report(
        _build_cluster(
            _agency_record(pattern_id="agency_act", source_family="act", evidence_note="ACT."),
            _agency_record(pattern_id="agency_erickson", source_family="erickson", evidence_note="Erickson."),
            _agency_record(pattern_id="agency_ifs", source_family="ifs", evidence_note="IFS."),
        )
    )
    cross = engine.build_report(
        _build_cluster(
            _identity_record(pattern_id="identity_act", source_family="act", evidence_note="ACT."),
            _identity_record(pattern_id="identity_ifs", source_family="ifs", evidence_note="IFS."),
            _identity_record(pattern_id="identity_shipibo", source_family="shipibo", evidence_note="Shipibo."),
            _identity_record(
                pattern_id="identity_maria_sabina",
                source_family="maria_sabina",
                evidence_note="Maria Sabina.",
            ),
        )
    )

    rank = {"low": 0, "medium": 1, "high": 2, "very_high": 3}
    assert rank[single.confidence] < rank[triple.confidence] < rank[cross.confidence]


def test_evidence_deterministic(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _agency_record(pattern_id="agency_act", source_family="act", evidence_note="ACT."),
        _agency_record(pattern_id="agency_ifs", source_family="ifs", evidence_note="IFS."),
    )
    first = engine.build_report(cluster)
    second = engine.build_report(cluster)
    assert first == second


def test_support_counts_correct(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _agency_record(pattern_id="agency_act", source_family="act", evidence_note="ACT."),
        _agency_record(pattern_id="agency_erickson", source_family="erickson", evidence_note="Erickson."),
    )
    report = engine.build_report(cluster)

    assert report.source_count == len(report.source_families) == 2
    assert len(report.psychotherapy_families) == 2
    assert len(report.traditional_families) == 0


def test_pattern_ids_preserved(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _agency_record(pattern_id="agency_act", source_family="act", evidence_note="ACT."),
        _agency_record(pattern_id="agency_ifs", source_family="ifs", evidence_note="IFS."),
    )
    export = engine.evaluate_cluster(cluster)

    assert export.pattern.id == cluster.canonical_pattern.id
    assert export.evidence_report.pattern_id == cluster.canonical_pattern.id
    assert export.pattern.id == "universal_agency_pattern"


def test_no_data_loss(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _agency_record(pattern_id="agency_act", source_family="act", evidence_note="ACT agency."),
        _agency_record(pattern_id="agency_ifs", source_family="ifs", evidence_note="IFS agency."),
    )
    export = engine.evaluate_cluster(cluster)
    serialized = json.dumps(
        {
            "pattern_id": export.evidence_report.pattern_id,
            "source_families": list(export.evidence_report.source_families),
            "supporting_patterns": list(cluster.supporting_patterns),
            "evidence_refs": [dict(ref) for ref in export.pattern.evidence_refs],
        }
    )

    assert "agency_act" in serialized
    assert "agency_ifs" in serialized
    assert "act" in serialized
    assert "ifs" in serialized
    assert "ACT agency." in serialized
    assert "IFS agency." in serialized


def test_export_shape(engine: UniversalPatternEvidenceEngine):
    cluster = _build_cluster(
        _agency_record(pattern_id="agency_act", source_family="act", evidence_note="ACT."),
    )
    export = engine.evaluate_cluster(cluster)
    assert isinstance(export, UniversalPatternEvidenceExport)
    assert export.pattern.id == export.evidence_report.pattern_id
