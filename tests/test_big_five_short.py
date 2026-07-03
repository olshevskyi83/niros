import pytest

from niros.assessment import AssessmentResponse, interpretation_is_neutral
from niros.assessments.big_five_short import (
    BIG_FIVE_SHORT_ITEM_SPECS,
    BIG_FIVE_SHORT_RESULTS_TITLE,
    BIG_FIVE_TRAITS,
    SUPPORTED_LANGUAGES,
    big_five_short_item_has_neutral_wording,
    get_big_five_short_items,
    item_text_for_language,
    render_big_five_short_results,
    score_big_five_short,
)


def test_twenty_items_exist():
    items = get_big_five_short_items()

    assert len(items) == 20
    assert len(BIG_FIVE_SHORT_ITEM_SPECS) == 20


def test_all_five_traits_exist():
    items = get_big_five_short_items()
    trait_ids = {item.domain_id for item in items}

    assert trait_ids == set(BIG_FIVE_TRAITS)


def test_each_trait_has_four_items():
    items = get_big_five_short_items()

    for trait in BIG_FIVE_TRAITS:
        trait_items = [item for item in items if item.domain_id == trait]
        assert len(trait_items) == 4


@pytest.mark.parametrize("language", sorted(SUPPORTED_LANGUAGES))
def test_all_languages_return_twenty_items(language: str):
    items = get_big_five_short_items(language)

    assert len(items) == 20
    for item in items:
        assert language in item.text_by_language
        assert item_text_for_language(item, language).strip()


def test_reverse_scored_items_exist():
    items = get_big_five_short_items()
    reverse_items = [item for item in items if item.reverse_scored]

    assert len(reverse_items) == 10
    for trait in BIG_FIVE_TRAITS:
        trait_items = [item for item in items if item.domain_id == trait]
        assert sum(1 for item in trait_items if item.reverse_scored) == 2


def test_neutral_answers_produce_scores_near_midpoint():
    items = get_big_five_short_items()
    responses = [AssessmentResponse(item_id=item.id, value=3) for item in items]

    results = score_big_five_short(responses)

    assert len(results) == 5
    for result in results:
        assert result.normalized_score == pytest.approx(0.5)
        assert result.interpretation == "moderate"
        assert result.fingerprint_dimension == "big_five"


def test_high_neuroticism_answers_produce_elevated_neuroticism():
    items = get_big_five_short_items()
    responses: list[AssessmentResponse] = []

    for item in items:
        if item.domain_id != "neuroticism":
            responses.append(AssessmentResponse(item_id=item.id, value=3))
            continue
        value = 1 if item.reverse_scored else 5
        responses.append(AssessmentResponse(item_id=item.id, value=value))

    results = score_big_five_short(responses)
    neuroticism = next(result for result in results if result.domain_id == "neuroticism")

    assert neuroticism.normalized_score == pytest.approx(1.0)
    assert neuroticism.interpretation == "elevated"


def test_no_diagnostic_wording_in_items_or_interpretations():
    items = get_big_five_short_items()

    for item in items:
        assert big_five_short_item_has_neutral_wording(item)

    neutral_results = score_big_five_short(
        [AssessmentResponse(item_id=item.id, value=3) for item in items]
    )
    for result in neutral_results:
        assert interpretation_is_neutral(result.interpretation)


def test_renderer_uses_big_five_section_label():
    items = get_big_five_short_items()
    results = score_big_five_short(
        [AssessmentResponse(item_id=item.id, value=3) for item in items]
    )

    rendered = render_big_five_short_results(results)

    assert rendered.startswith(BIG_FIVE_SHORT_RESULTS_TITLE)
    assert "Trait: openness" in rendered
    assert "Fingerprint dimension: big_five" in rendered


def test_score_and_render_output_is_deterministic():
    items = get_big_five_short_items()
    responses = [AssessmentResponse(item_id=item.id, value=3) for item in items]

    first_score = score_big_five_short(responses)
    second_score = score_big_five_short(responses)
    first_render = render_big_five_short_results(first_score)
    second_render = render_big_five_short_results(second_score)

    assert first_score == second_score
    assert first_render == second_render
    assert [result.domain_id for result in first_score] == sorted(BIG_FIVE_TRAITS)
