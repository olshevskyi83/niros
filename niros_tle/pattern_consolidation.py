"""Universal Pattern Consolidation Engine — merge equivalent extracted patterns deterministically."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros_tle.pattern_contract import (
    SOURCE_CONFIDENCE_VALUES,
    TLEPatternRecord,
    validate_tle_pattern_record,
)

SUPPORT_LEVELS: tuple[str, ...] = (
    "single_source",
    "multi_source",
    "cross_cultural",
    "cross_modal",
)

PSYCHOTHERAPY_SOURCE_FAMILIES: frozenset[str] = frozenset(
    {
        "act",
        "cft",
        "erickson",
        "ericksonian",
        "ifs",
        "narrative",
        "motivational",
        "motivational_interviewing",
        "compassion_focused",
        "grief_informed",
        "somatic",
        "trauma_informed",
        "values_based",
        "symbolic",
        "existential",
        "nature_based",
    }
)

INDIGENOUS_SOURCE_FAMILIES: frozenset[str] = frozenset(
    {
        "maria_sabina",
        "shipibo",
        "quechua",
    }
)

CONFIDENCE_RANK: dict[str, int] = {"low": 0, "medium": 1, "high": 2}


class PatternConsolidationError(ValueError):
    """Raised when consolidation cannot proceed safely."""


@dataclass(frozen=True)
class PatternCluster:
    cluster_id: str
    canonical_pattern: TLEPatternRecord
    supporting_patterns: tuple[str, ...]
    supporting_sources: tuple[str, ...]
    psychological_functions: tuple[str, ...]
    semantic_clusters: tuple[str, ...]
    support_level: str
    confidence: str


class UniversalPatternConsolidator:
    """Merge equivalent TLEPatternRecord objects into universal pattern clusters."""

    def __init__(self) -> None:
        self._patterns: list[TLEPatternRecord] = []
        self._clusters: tuple[PatternCluster, ...] = ()

    def add_pattern(self, record: TLEPatternRecord) -> None:
        validate_tle_pattern_record(record)
        self._patterns.append(record)
        self._clusters = ()

    def build_clusters(self) -> tuple[PatternCluster, ...]:
        if not self._patterns:
            self._clusters = ()
            return self._clusters

        sorted_patterns = sorted(self._patterns, key=lambda record: record.id)
        groups = _cluster_indices(sorted_patterns)

        clusters: list[PatternCluster] = []
        for group_index, indices in enumerate(groups, start=1):
            members = tuple(sorted_patterns[index] for index in indices)
            primary_function = _primary_function(members[0])
            cluster_id = _cluster_id(primary_function, members, group_index)
            canonical_pattern = _merge_records(members, cluster_id)
            supporting_sources = _unique_preserve_order(
                source
                for record in members
                for source in record.source_family
            )
            psychological_functions = _unique_preserve_order(
                function
                for record in members
                for function in record.psychological_function
            )
            semantic_clusters = _unique_preserve_order(
                cluster
                for record in members
                for cluster in record.semantic_cluster
            )
            delivery_formats = _unique_preserve_order(
                delivery_format
                for record in members
                for delivery_format in record.delivery_formats
            )
            clusters.append(
                PatternCluster(
                    cluster_id=cluster_id,
                    canonical_pattern=canonical_pattern,
                    supporting_patterns=tuple(record.id for record in members),
                    supporting_sources=supporting_sources,
                    psychological_functions=psychological_functions,
                    semantic_clusters=semantic_clusters,
                    support_level=_support_level(supporting_sources, delivery_formats),
                    confidence=_highest_confidence(record.source_confidence for record in members),
                )
            )

        self._clusters = tuple(sorted(clusters, key=lambda cluster: cluster.cluster_id))
        return self._clusters

    def export_universal_patterns(self) -> tuple[TLEPatternRecord, ...]:
        if not self._clusters:
            self.build_clusters()
        return tuple(cluster.canonical_pattern for cluster in self._clusters)


def _cluster_indices(patterns: tuple[TLEPatternRecord, ...]) -> list[tuple[int, ...]]:
    count = len(patterns)
    parent = list(range(count))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for left in range(count):
        for right in range(left + 1, count):
            if _should_merge(patterns[left], patterns[right]):
                union(left, right)

    grouped: dict[int, list[int]] = {}
    for index in range(count):
        root = find(index)
        grouped.setdefault(root, []).append(index)

    return [
        tuple(sorted(indices, key=lambda idx: patterns[idx].id))
        for indices in sorted(grouped.values(), key=lambda group: patterns[group[0]].id)
    ]


def _should_merge(left: TLEPatternRecord, right: TLEPatternRecord) -> bool:
    if _primary_function(left) != _primary_function(right):
        return False
    return (
        _substantial_overlap(left.good_for, right.good_for)
        and _substantial_overlap(left.semantic_cluster, right.semantic_cluster)
        and _substantial_overlap(left.language_style, right.language_style)
    )


def _substantial_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    if not left or not right:
        return False
    shared = set(left) & set(right)
    if not shared:
        return False
    smaller = min(len(left), len(right))
    required = max(1, (smaller + 1) // 2)
    return len(shared) >= required


def _merge_records(records: tuple[TLEPatternRecord, ...], cluster_id: str) -> TLEPatternRecord:
    sorted_records = tuple(sorted(records, key=lambda record: record.id))
    anchor = sorted_records[0]
    primary_function = _primary_function(anchor)

    merged = TLEPatternRecord(
        id=_canonical_pattern_id(primary_function, sorted_records),
        name=_canonical_pattern_name(primary_function, sorted_records),
        psychological_function=_unique_preserve_order(
            function
            for record in sorted_records
            for function in record.psychological_function
        ),
        good_for=_unique_preserve_order(
            item for record in sorted_records for item in record.good_for
        ),
        avoid_if=_unique_preserve_order(
            item for record in sorted_records for item in record.avoid_if
        ),
        language_style=_unique_preserve_order(
            item for record in sorted_records for item in record.language_style
        ),
        rhythm=_most_conservative_scalar(record.rhythm for record in sorted_records),
        semantic_cluster=_unique_preserve_order(
            item for record in sorted_records for item in record.semantic_cluster
        ),
        spiritual_compatibility=_unique_preserve_order(
            item for record in sorted_records for item in record.spiritual_compatibility
        ),
        requires_symbols=_unique_preserve_order(
            item for record in sorted_records for item in record.requires_symbols
        ),
        forbidden_symbols=_unique_preserve_order(
            item for record in sorted_records for item in record.forbidden_symbols
        ),
        intensity=_most_conservative_scalar(record.intensity for record in sorted_records),
        directness=_most_conservative_scalar(record.directness for record in sorted_records),
        repetition_level=_most_conservative_scalar(record.repetition_level for record in sorted_records),
        safety_notes=_merge_safety_notes(sorted_records),
        source_family=_unique_preserve_order(
            source for record in sorted_records for source in record.source_family
        ),
        source_confidence=_highest_confidence(record.source_confidence for record in sorted_records),
        extraction_method=anchor.extraction_method,
        evidence_refs=_merge_evidence_refs(sorted_records),
        notes=_consolidation_notes(sorted_records, cluster_id),
        delivery_formats=_unique_preserve_order(
            item for record in sorted_records for item in record.delivery_formats
        ),
        contraindications=_unique_preserve_order(
            item for record in sorted_records for item in record.contraindications
        ),
        example_use_case=anchor.example_use_case,
    )
    validate_tle_pattern_record(merged)
    return merged


def _primary_function(record: TLEPatternRecord) -> str:
    if not record.psychological_function:
        raise PatternConsolidationError(f"Pattern '{record.id}' lacks psychological_function.")
    return record.psychological_function[0]


def _cluster_id(
    primary_function: str,
    members: tuple[TLEPatternRecord, ...],
    group_index: int,
) -> str:
    if len(members) == 1:
        return f"cluster_{primary_function}_{members[0].id}"
    return f"cluster_{primary_function}_{group_index:02d}"


def _canonical_pattern_id(
    primary_function: str,
    records: tuple[TLEPatternRecord, ...],
) -> str:
    if len(records) == 1:
        return records[0].id
    return f"universal_{primary_function}_pattern"


def _canonical_pattern_name(
    primary_function: str,
    records: tuple[TLEPatternRecord, ...],
) -> str:
    if len(records) == 1:
        return records[0].name
    readable = primary_function.replace("_", " ").title()
    return f"Universal {readable} Pattern"


def _support_level(
    supporting_sources: tuple[str, ...],
    delivery_formats: tuple[str, ...],
) -> str:
    unique_sources = set(supporting_sources)
    if len(unique_sources) == 1:
        return "single_source"

    if len(set(delivery_formats)) >= 2:
        return "cross_modal"

    categories = {_source_category(source) for source in unique_sources}
    if "psychotherapy" in categories and "indigenous_healing" in categories:
        return "cross_cultural"

    return "multi_source"


def _source_category(source_family: str) -> str:
    normalized = source_family.strip().lower()
    if normalized in INDIGENOUS_SOURCE_FAMILIES:
        return "indigenous_healing"
    if normalized in PSYCHOTHERAPY_SOURCE_FAMILIES:
        return "psychotherapy"
    return "other"


def _highest_confidence(values: Iterable[str]) -> str:
    best = "low"
    best_rank = CONFIDENCE_RANK[best]
    for value in values:
        normalized = value.strip().lower()
        if normalized not in CONFIDENCE_RANK:
            raise PatternConsolidationError(f"Invalid source_confidence '{value}'.")
        if CONFIDENCE_RANK[normalized] > best_rank:
            best = normalized
            best_rank = CONFIDENCE_RANK[normalized]
    if best not in SOURCE_CONFIDENCE_VALUES:
        raise PatternConsolidationError(f"Invalid aggregated source_confidence '{best}'.")
    return best


def _merge_safety_notes(records: tuple[TLEPatternRecord, ...]) -> tuple[str, ...]:
    return _unique_preserve_order(note for record in records for note in record.safety_notes)


def _merge_evidence_refs(records: tuple[TLEPatternRecord, ...]) -> tuple[dict[str, str], ...]:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        for ref in record.evidence_refs:
            key = (
                ref["source_family"].strip(),
                ref["reference_type"].strip(),
                ref["note"].strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "source_family": key[0],
                    "reference_type": key[1],
                    "note": key[2],
                }
            )
    if not merged:
        raise PatternConsolidationError("Merged pattern must retain at least one evidence ref.")
    return tuple(merged)


def _consolidation_notes(records: tuple[TLEPatternRecord, ...], cluster_id: str) -> str:
    supporting = ", ".join(record.id for record in records)
    return f"Consolidated universal pattern ({cluster_id}) from extracted patterns: {supporting}."


def _unique_preserve_order(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _most_conservative_scalar(values: Iterable[str]) -> str:
    ordering = ("low", "medium", "high", "gentle", "slow", "slow_repetitive", "steady", "flowing")
    rank = {value: index for index, value in enumerate(ordering)}
    normalized_values = [value.strip() for value in values if value.strip()]
    if not normalized_values:
        return ""

    def sort_key(value: str) -> tuple[int, str]:
        return (rank.get(value, len(ordering)), value)

    return sorted(normalized_values, key=sort_key)[0]
