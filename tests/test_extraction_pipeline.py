"""Tests for therapeutic extraction pipeline."""

from __future__ import annotations

from niros.extraction_pipeline import (
    ExtractionPipelineResult,
    build_extraction_pipeline,
    merge_pipeline_results,
)
from niros.raw_source import RawSource, RawSourceSegment, build_raw_source_corpus
from niros.therapeutic_extraction import TherapeuticFunctionExtraction


def _source(source_id: str = "source_001") -> RawSource:
    return RawSource(
        source_id=source_id,
        source_family="mazatec_tradition",
        title="Chant source",
        language="mazatec",
        source_type="chant",
    )


def _corpus(source_id: str = "source_001", segment_count: int = 2):
    source = _source(source_id)
    segments = tuple(
        RawSourceSegment(
            segment_id=f"segment_{index:03d}",
            source_id=source_id,
            sequence_index=index,
            raw_text=f"Line {index}",
        )
        for index in range(segment_count)
    )
    return build_raw_source_corpus(source, segments)


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    base = {
        "extraction_id": "extraction_source_001_segment_001_self_compassion",
        "source_id": "source_001",
        "segment_id": "segment_001",
        "therapeutic_function": "self_compassion",
        "evidence_text": "Evidence from the chant segment.",
        "generation_rules": ("Use gentle phrasing.",),
        "voice_rules": ("Keep tempo slow.",),
        "confidence": 0.85,
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def test_empty_pipeline() -> None:
    result = build_extraction_pipeline(_corpus(segment_count=0), ())
    assert result.source_id == "source_001"
    assert result.total_segments == 0
    assert result.total_extractions == 0
    assert result.total_patterns == 0
    assert result.patterns == ()
    assert result.validation_issues == ()


def test_valid_extraction_becomes_one_pattern() -> None:
    result = build_extraction_pipeline(_corpus(), (_extraction(),))
    assert result.total_patterns == 1
    assert result.patterns[0].therapeutic_function == "self_compassion"
    assert result.patterns[0].review_status == "pending_human_review"


def test_invalid_extraction_skipped() -> None:
    invalid = _extraction(evidence_text="", confidence=1.5)
    result = build_extraction_pipeline(_corpus(), (invalid,))
    assert result.total_patterns == 0
    assert result.validation_issues


def test_validation_issue_collected() -> None:
    invalid = _extraction(evidence_text="")
    result = build_extraction_pipeline(_corpus(), (invalid,))
    assert any("evidence_text must not be empty" in issue for issue in result.validation_issues)


def test_wrong_source_rejected() -> None:
    wrong_source = _extraction(source_id="source_other")
    result = build_extraction_pipeline(_corpus(), (wrong_source,))
    assert result.total_patterns == 0
    assert any("source_id does not match corpus source_id" in issue for issue in result.validation_issues)


def test_multiple_extractions() -> None:
    extractions = (
        _extraction(
            extraction_id="extraction_b",
            therapeutic_function="acceptance",
            segment_id="segment_002",
        ),
        _extraction(
            extraction_id="extraction_a",
            therapeutic_function="self_compassion",
            segment_id="segment_001",
        ),
    )
    result = build_extraction_pipeline(_corpus(), extractions)
    assert result.total_extractions == 2
    assert result.total_patterns == 2
    assert [pattern.therapeutic_function for pattern in result.patterns] == [
        "self_compassion",
        "acceptance",
    ]
    assert [pattern.pattern_id for pattern in result.patterns] == [
        "ctp_from_extraction_a",
        "ctp_from_extraction_b",
    ]


def test_deterministic_ordering_by_pattern_id() -> None:
    extractions = (
        _extraction(extraction_id="extraction_z"),
        _extraction(
            extraction_id="extraction_a",
            therapeutic_function="acceptance",
            segment_id="segment_002",
        ),
    )
    first = build_extraction_pipeline(_corpus(), extractions)
    second = build_extraction_pipeline(_corpus(), extractions)
    assert first == second
    assert [pattern.pattern_id for pattern in first.patterns] == [
        "ctp_from_extraction_a",
        "ctp_from_extraction_z",
    ]
    assert list(first.validation_issues) == sorted(first.validation_issues)


def test_merge_results() -> None:
    corpus_a = _corpus("source_a", segment_count=1)
    corpus_b = _corpus("source_b", segment_count=2)
    result_a = build_extraction_pipeline(
        corpus_a,
        (_extraction(source_id="source_a", extraction_id="extraction_a"),),
    )
    result_b = build_extraction_pipeline(
        corpus_b,
        (
            _extraction(
                source_id="source_b",
                extraction_id="extraction_b",
                therapeutic_function="acceptance",
                segment_id="segment_001",
            ),
        ),
    )
    merged = merge_pipeline_results((result_a, result_b))
    assert merged.source_id == "merged"
    assert len(merged.patterns) == 2


def test_merge_counts() -> None:
    result_a = ExtractionPipelineResult(
        source_id="source_a",
        total_segments=1,
        total_extractions=2,
        total_patterns=1,
        patterns=(),
    )
    result_b = ExtractionPipelineResult(
        source_id="source_b",
        total_segments=3,
        total_extractions=1,
        total_patterns=0,
        patterns=(),
    )
    merged = merge_pipeline_results((result_a, result_b))
    assert merged.total_segments == 4
    assert merged.total_extractions == 3


def test_merge_validation_issues() -> None:
    result_a = ExtractionPipelineResult(
        source_id="source_a",
        total_segments=1,
        total_extractions=1,
        total_patterns=0,
        validation_issues=("z_issue", "a_issue"),
    )
    result_b = ExtractionPipelineResult(
        source_id="source_b",
        total_segments=1,
        total_extractions=1,
        total_patterns=0,
        validation_issues=("m_issue", "a_issue"),
    )
    merged = merge_pipeline_results((result_a, result_b))
    assert merged.validation_issues == ("a_issue", "m_issue", "z_issue")


def test_output_deterministic() -> None:
    corpus = _corpus()
    extractions = (_extraction(),)
    first = build_extraction_pipeline(corpus, extractions)
    second = build_extraction_pipeline(corpus, extractions)
    assert first == second
    assert merge_pipeline_results((first,)) == merge_pipeline_results((first,))
