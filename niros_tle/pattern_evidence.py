"""Universal Pattern Evidence Engine — deterministic evidence aggregation only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros_tle.pattern_consolidation import (
    INDIGENOUS_SOURCE_FAMILIES,
    PSYCHOTHERAPY_SOURCE_FAMILIES,
    PatternCluster,
)
from niros_tle.pattern_contract import TLEPatternRecord

CONFIDENCE_LEVELS: tuple[str, ...] = ("low", "medium", "high", "very_high")
EVIDENCE_STRENGTH_LEVELS: tuple[str, ...] = ("weak", "moderate", "strong", "very_strong")
SAFETY_CONFIDENCE_LEVELS: tuple[str, ...] = ("low", "medium", "high")


@dataclass(frozen=True)
class PatternEvidenceReport:
    pattern_id: str
    support_level: str
    source_count: int
    source_families: tuple[str, ...]
    psychotherapy_families: tuple[str, ...]
    traditional_families: tuple[str, ...]
    cross_cultural: bool
    cross_theoretical: bool
    confidence: str
    evidence_strength: str
    safety_confidence: str
    notes: str


@dataclass(frozen=True)
class UniversalPatternEvidenceExport:
    pattern: TLEPatternRecord
    evidence_report: PatternEvidenceReport


class UniversalPatternEvidenceEngine:
    """Aggregate deterministic evidence for universal therapeutic patterns."""

    def evaluate_cluster(self, cluster: PatternCluster) -> UniversalPatternEvidenceExport:
        report = self.build_report(cluster)
        return UniversalPatternEvidenceExport(
            pattern=cluster.canonical_pattern,
            evidence_report=report,
        )

    def evaluate_clusters(
        self,
        clusters: Iterable[PatternCluster],
    ) -> tuple[UniversalPatternEvidenceExport, ...]:
        return tuple(
            self.evaluate_cluster(cluster)
            for cluster in sorted(clusters, key=lambda item: item.cluster_id)
        )

    def build_report(self, cluster: PatternCluster) -> PatternEvidenceReport:
        source_families = cluster.supporting_sources
        psychotherapy_families = _families_in_category(
            source_families,
            PSYCHOTHERAPY_SOURCE_FAMILIES,
        )
        traditional_families = _families_in_category(
            source_families,
            INDIGENOUS_SOURCE_FAMILIES,
        )
        cross_cultural = _is_cross_cultural(psychotherapy_families, traditional_families)
        cross_theoretical = len(psychotherapy_families) >= 2
        consistent_psychological_function = _has_consistent_primary_function(cluster)
        consistent_semantic_cluster = _has_consistent_semantic_cluster(cluster)

        evidence_score = _evidence_score(
            source_count=len(source_families),
            psychotherapy_count=len(psychotherapy_families),
            traditional_count=len(traditional_families),
            cross_cultural=cross_cultural,
            cross_theoretical=cross_theoretical,
            consistent_psychological_function=consistent_psychological_function,
            consistent_semantic_cluster=consistent_semantic_cluster,
        )

        return PatternEvidenceReport(
            pattern_id=cluster.canonical_pattern.id,
            support_level=cluster.support_level,
            source_count=len(source_families),
            source_families=source_families,
            psychotherapy_families=psychotherapy_families,
            traditional_families=traditional_families,
            cross_cultural=cross_cultural,
            cross_theoretical=cross_theoretical,
            confidence=_confidence_level(
                source_count=len(source_families),
                psychotherapy_count=len(psychotherapy_families),
                traditional_count=len(traditional_families),
                cross_cultural=cross_cultural,
                cross_theoretical=cross_theoretical,
                evidence_score=evidence_score,
            ),
            evidence_strength=_evidence_strength(evidence_score),
            safety_confidence=_safety_confidence(cluster.canonical_pattern, len(source_families)),
            notes=_report_notes(
                cluster=cluster,
                evidence_score=evidence_score,
                cross_cultural=cross_cultural,
                cross_theoretical=cross_theoretical,
            ),
        )


def _families_in_category(
    source_families: tuple[str, ...],
    category_families: frozenset[str],
) -> tuple[str, ...]:
    return tuple(
        source
        for source in source_families
        if source.strip().lower() in category_families
    )


def _is_cross_cultural(
    psychotherapy_families: tuple[str, ...],
    traditional_families: tuple[str, ...],
) -> bool:
    return bool(psychotherapy_families and traditional_families)


def _has_consistent_primary_function(cluster: PatternCluster) -> bool:
    if not cluster.psychological_functions:
        return False
    primary = cluster.psychological_functions[0]
    return primary in cluster.psychological_functions


def _has_consistent_semantic_cluster(cluster: PatternCluster) -> bool:
    return len(cluster.semantic_clusters) >= 1


def _evidence_score(
    *,
    source_count: int,
    psychotherapy_count: int,
    traditional_count: int,
    cross_cultural: bool,
    cross_theoretical: bool,
    consistent_psychological_function: bool,
    consistent_semantic_cluster: bool,
) -> int:
    score = source_count
    score += psychotherapy_count
    score += traditional_count * 2
    if cross_cultural:
        score += 3
    if cross_theoretical:
        score += 2
    if consistent_psychological_function:
        score += 1
    if consistent_semantic_cluster:
        score += 1
    return score


def _confidence_level(
    *,
    source_count: int,
    psychotherapy_count: int,
    traditional_count: int,
    cross_cultural: bool,
    cross_theoretical: bool,
    evidence_score: int,
) -> str:
    if cross_cultural and psychotherapy_count >= 1 and traditional_count >= 1 and source_count >= 4:
        return "very_high"
    if cross_cultural and psychotherapy_count >= 1 and traditional_count >= 1:
        return "very_high"
    if source_count >= 3 and psychotherapy_count >= 2 and cross_theoretical:
        return "high"
    if source_count >= 3:
        return "high"
    if source_count == 2:
        return "medium"
    if evidence_score >= 4 and source_count == 1:
        return "medium"
    return "low"


def _evidence_strength(evidence_score: int) -> str:
    if evidence_score >= 12:
        return "very_strong"
    if evidence_score >= 8:
        return "strong"
    if evidence_score >= 4:
        return "moderate"
    return "weak"


def _safety_confidence(pattern: TLEPatternRecord, source_count: int) -> str:
    if pattern.safety_notes and pattern.avoid_if and source_count >= 2:
        return "high"
    if pattern.safety_notes and pattern.avoid_if:
        return "medium"
    if pattern.safety_notes or pattern.avoid_if:
        return "medium"
    return "low"


def _report_notes(
    *,
    cluster: PatternCluster,
    evidence_score: int,
    cross_cultural: bool,
    cross_theoretical: bool,
) -> str:
    supporting = ", ".join(cluster.supporting_patterns)
    families = ", ".join(cluster.supporting_sources)
    return (
        f"Evidence aggregation for {cluster.canonical_pattern.id}: "
        f"score={evidence_score}, sources=[{families}], "
        f"supporting_patterns=[{supporting}], "
        f"cross_cultural={cross_cultural}, cross_theoretical={cross_theoretical}."
    )
