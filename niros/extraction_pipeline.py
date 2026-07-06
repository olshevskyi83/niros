"""Extraction Pipeline — convert raw source extractions into CTPC pattern drafts."""

from __future__ import annotations

from dataclasses import dataclass, field

from niros.ctpc import CanonicalTherapeuticPattern
from niros.raw_source import RawSourceCorpus
from niros.therapeutic_extraction import (
    TherapeuticFunctionExtraction,
    build_ctpc_pattern_from_extraction,
    validate_extraction,
)


@dataclass(frozen=True)
class ExtractionPipelineResult:
    source_id: str
    total_segments: int
    total_extractions: int
    total_patterns: int
    patterns: tuple[CanonicalTherapeuticPattern, ...] = field(default_factory=tuple)
    validation_issues: tuple[str, ...] = field(default_factory=tuple)


def _issue_for_extraction(extraction_id: str, message: str) -> str:
    return f"{extraction_id}: {message}"


def build_extraction_pipeline(
    corpus: RawSourceCorpus,
    extractions: tuple[TherapeuticFunctionExtraction, ...] | list[TherapeuticFunctionExtraction],
) -> ExtractionPipelineResult:
    """Convert validated extractions for one corpus into CTPC pattern drafts."""
    extraction_items = tuple(extractions)
    patterns: list[CanonicalTherapeuticPattern] = []
    issues: list[str] = []

    for extraction in extraction_items:
        if extraction.source_id != corpus.source.source_id:
            issues.append(
                _issue_for_extraction(
                    extraction.extraction_id,
                    "source_id does not match corpus source_id",
                )
            )
            continue

        extraction_issues = validate_extraction(extraction)
        if extraction_issues:
            for issue in extraction_issues:
                issues.append(_issue_for_extraction(extraction.extraction_id, issue))
            continue

        patterns.append(build_ctpc_pattern_from_extraction(extraction))

    sorted_patterns = tuple(sorted(patterns, key=lambda pattern: pattern.pattern_id))
    sorted_issues = tuple(sorted(issues))

    return ExtractionPipelineResult(
        source_id=corpus.source.source_id,
        total_segments=len(corpus.segments),
        total_extractions=len(extraction_items),
        total_patterns=len(sorted_patterns),
        patterns=sorted_patterns,
        validation_issues=sorted_issues,
    )


def merge_pipeline_results(
    results: tuple[ExtractionPipelineResult, ...] | list[ExtractionPipelineResult],
) -> ExtractionPipelineResult:
    """Merge multiple extraction pipeline results into one deterministic result."""
    result_items = tuple(results)
    if not result_items:
        return ExtractionPipelineResult(
            source_id="",
            total_segments=0,
            total_extractions=0,
            total_patterns=0,
        )

    merged_patterns: dict[str, CanonicalTherapeuticPattern] = {}
    merged_issues: list[str] = []
    source_ids = sorted({result.source_id for result in result_items if result.source_id})

    total_segments = sum(result.total_segments for result in result_items)
    total_extractions = sum(result.total_extractions for result in result_items)

    for result in result_items:
        for pattern in result.patterns:
            merged_patterns.setdefault(pattern.pattern_id, pattern)
        merged_issues.extend(result.validation_issues)

    patterns = tuple(sorted(merged_patterns.values(), key=lambda pattern: pattern.pattern_id))
    validation_issues = tuple(sorted(set(merged_issues)))

    if len(source_ids) == 1:
        source_id = source_ids[0]
    elif not source_ids:
        source_id = ""
    else:
        source_id = "merged"

    return ExtractionPipelineResult(
        source_id=source_id,
        total_segments=total_segments,
        total_extractions=total_extractions,
        total_patterns=len(patterns),
        patterns=patterns,
        validation_issues=validation_issues,
    )
