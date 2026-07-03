import pytest

from niros.assessment import (
    ASSESSMENT_RESULTS_TITLE,
    EMPTY_ASSESSMENT_RESULTS_TEXT,
    AssessmentItem,
    AssessmentResponse,
    AssessmentResult,
    interpretation_is_neutral,
    normalize_assessment_score,
    recode_assessment_response,
    render_assessment_results,
    score_assessment,
)


def _item(
    item_id: str,
    *,
    domain_id: str,
    reverse_scored: bool = False,
    fingerprint_dimension: str = "semantic_facts",
) -> AssessmentItem:
    return AssessmentItem(
        id=item_id,
        text_by_language={"en": f"Sample item {item_id}"},
        domain_id=domain_id,
        scale_min=1,
        scale_max=5,
        reverse_scored=reverse_scored,
        fingerprint_dimension=fingerprint_dimension,
    )


def test_scoring_works_for_single_domain():
    items = [
        _item("mood-1", domain_id="low_mood_depression_signals"),
        _item("mood-2", domain_id="low_mood_depression_signals"),
    ]
    responses = [
        AssessmentResponse(item_id="mood-1", value=4),
        AssessmentResponse(item_id="mood-2", value=2),
    ]

    results = score_assessment(items, responses)

    assert len(results) == 1
    assert results[0].domain_id == "low_mood_depression_signals"
    assert results[0].score == pytest.approx(3.0)
    assert results[0].normalized_score == pytest.approx(0.5)
    assert results[0].interpretation == "moderate"


def test_reverse_scoring_inverts_item_values():
    item = _item("sleep-1", domain_id="sleep_nightmares", reverse_scored=True)

    assert recode_assessment_response(1, item) == 5
    assert recode_assessment_response(5, item) == 1
    assert recode_assessment_response(3, item) == 3

    results = score_assessment(
        [item],
        [AssessmentResponse(item_id="sleep-1", value=1)],
    )

    assert results[0].score == pytest.approx(5.0)
    assert results[0].normalized_score == pytest.approx(1.0)
    assert results[0].interpretation == "elevated"


def test_normalization_maps_scale_to_unit_interval():
    assert normalize_assessment_score(1.0, 1, 5) == pytest.approx(0.0)
    assert normalize_assessment_score(5.0, 1, 5) == pytest.approx(1.0)
    assert normalize_assessment_score(3.0, 1, 5) == pytest.approx(0.5)


def test_missing_response_is_skipped_safely():
    items = [
        _item("mood-1", domain_id="low_mood_depression_signals"),
        _item("mood-2", domain_id="low_mood_depression_signals"),
    ]

    results = score_assessment(items, [AssessmentResponse(item_id="mood-1", value=5)])

    assert len(results) == 1
    assert results[0].score == pytest.approx(5.0)

    assert score_assessment(items, []) == []


def test_multiple_domains_scored_separately():
    items = [
        _item("mood-1", domain_id="low_mood_depression_signals"),
        _item("anxiety-1", domain_id="anxiety_fear_panic", fingerprint_dimension="patterns"),
    ]
    responses = [
        AssessmentResponse(item_id="mood-1", value=2),
        AssessmentResponse(item_id="anxiety-1", value=4),
    ]

    results = score_assessment(items, responses)

    assert len(results) == 2
    by_domain = {result.domain_id: result for result in results}
    assert by_domain["low_mood_depression_signals"].score == pytest.approx(2.0)
    assert by_domain["low_mood_depression_signals"].interpretation == "low"
    assert by_domain["anxiety_fear_panic"].score == pytest.approx(4.0)
    assert by_domain["anxiety_fear_panic"].interpretation == "elevated"
    assert by_domain["anxiety_fear_panic"].fingerprint_dimension == "patterns"


def test_interpretation_uses_neutral_language():
    cases = [
        AssessmentResult("sleep_nightmares", 1.0, 0.0, "low", "semantic_facts"),
        AssessmentResult("sleep_nightmares", 3.0, 0.5, "moderate", "semantic_facts"),
        AssessmentResult("sleep_nightmares", 5.0, 1.0, "elevated", "semantic_facts"),
    ]

    for result in cases:
        assert interpretation_is_neutral(result.interpretation)


def test_renderer_includes_required_fields():
    results = [
        AssessmentResult(
            domain_id="anxiety_fear_panic",
            score=3.5,
            normalized_score=0.625,
            interpretation="moderate",
            fingerprint_dimension="semantic_facts",
        )
    ]

    rendered = render_assessment_results(results)

    assert ASSESSMENT_RESULTS_TITLE in rendered
    assert "Domain: anxiety_fear_panic" in rendered
    assert "Score: 3.50" in rendered
    assert "Level: moderate" in rendered
    assert "Fingerprint dimension: semantic_facts" in rendered


def test_renderer_handles_empty_results():
    assert render_assessment_results([]) == EMPTY_ASSESSMENT_RESULTS_TEXT


def test_score_assessment_output_is_deterministic():
    items = [
        _item("z-domain", domain_id="sleep_nightmares"),
        _item("a-domain", domain_id="anxiety_fear_panic"),
    ]
    responses = [
        AssessmentResponse(item_id="z-domain", value=3),
        AssessmentResponse(item_id="a-domain", value=3),
    ]

    first = score_assessment(items, responses)
    second = score_assessment(items, responses)
    first_rendered = render_assessment_results(first)
    second_rendered = render_assessment_results(second)

    assert first == second
    assert first_rendered == second_rendered
    assert [result.domain_id for result in first] == ["anxiety_fear_panic", "sleep_nightmares"]


def test_out_of_range_response_raises():
    item = _item("mood-1", domain_id="low_mood_depression_signals")

    with pytest.raises(ValueError, match="must be between"):
        score_assessment([item], [AssessmentResponse(item_id="mood-1", value=6)])
