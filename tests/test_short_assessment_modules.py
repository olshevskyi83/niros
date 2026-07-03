import pytest

from niros.assessment import AssessmentResponse, FORBIDDEN_INTERPRETATION_PHRASES, interpretation_is_neutral
from niros.assessments._common import (
    FORBIDDEN_ITEM_PHRASES,
    SCALE_MAX,
    SCALE_MIN,
    SUPPORTED_LANGUAGES,
    item_has_neutral_wording,
    item_text_for_language,
)
from niros.assessments.registry import (
    get_assessment_module_items,
    list_available_modules,
    score_assessment_module,
)

EXPECTED_MODULE_IDS = (
    "big-five-short",
    "low-mood-short",
    "anxiety-short",
    "sleep-short",
    "trauma-stress-short",
    "grief-loss-short",
    "substance-use-short",
    "behavioral-addiction-short",
    "pain-fatigue-short",
    "speech-anxiety-short",
    "psychedelic-concern-short",
    "meaning-purpose-short",
    "self-domain-short",
    "emotion-regulation-domain-short",
    "cognitive-patterns-domain-short",
    "relationships-domain-short",
    "values-identity-domain-short",
    "emotional-flexibility-domain-short",
)

SHORT_MODULE_ITEM_COUNTS = {
    "big-five-short": 20,
    "low-mood-short": 6,
    "anxiety-short": 6,
    "sleep-short": 6,
    "trauma-stress-short": 6,
    "grief-loss-short": 6,
    "substance-use-short": 6,
    "behavioral-addiction-short": 6,
    "pain-fatigue-short": 6,
    "speech-anxiety-short": 6,
    "psychedelic-concern-short": 6,
    "meaning-purpose-short": 6,
    "self-domain-short": 6,
    "emotion-regulation-domain-short": 6,
    "cognitive-patterns-domain-short": 6,
    "relationships-domain-short": 6,
    "values-identity-domain-short": 6,
    "emotional-flexibility-domain-short": 6,
}


def test_all_modules_are_registered():
    assert list_available_modules() == sorted(EXPECTED_MODULE_IDS)


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_module_returns_expected_item_count(module_id: str):
    items = get_assessment_module_items(module_id)

    assert len(items) == SHORT_MODULE_ITEM_COUNTS[module_id]


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
@pytest.mark.parametrize("language", sorted(SUPPORTED_LANGUAGES))
def test_module_supports_all_languages(module_id: str, language: str):
    items = get_assessment_module_items(module_id, language)

    assert len(items) == SHORT_MODULE_ITEM_COUNTS[module_id]
    for item in items:
        assert language in item.text_by_language
        assert item_text_for_language(item, language).strip()


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_all_items_use_one_to_five_scale(module_id: str):
    items = get_assessment_module_items(module_id)

    for item in items:
        assert item.scale_min == SCALE_MIN
        assert item.scale_max == SCALE_MAX


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_every_item_has_fingerprint_dimension(module_id: str):
    items = get_assessment_module_items(module_id)

    for item in items:
        assert item.fingerprint_dimension.strip()


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_scoring_works_for_each_module(module_id: str):
    items = get_assessment_module_items(module_id)
    responses = [AssessmentResponse(item_id=item.id, value=3) for item in items]

    results = score_assessment_module(module_id, responses)

    assert results
    domain_ids = {item.domain_id for item in items}
    assert {result.domain_id for result in results} == domain_ids


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_results_use_neutral_language_only(module_id: str):
    items = get_assessment_module_items(module_id)
    responses = [AssessmentResponse(item_id=item.id, value=3) for item in items]

    results = score_assessment_module(module_id, responses)

    for result in results:
        assert interpretation_is_neutral(result.interpretation)
        lowered = result.interpretation.lower()
        assert not any(phrase in lowered for phrase in FORBIDDEN_INTERPRETATION_PHRASES)


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_items_have_no_diagnostic_wording(module_id: str):
    items = get_assessment_module_items(module_id)

    for item in items:
        assert item_has_neutral_wording(item)
        for text in item.text_by_language.values():
            lowered = text.lower()
            assert not any(phrase in lowered for phrase in FORBIDDEN_ITEM_PHRASES)


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_each_short_module_has_reverse_scored_item(module_id: str):
    if module_id == "big-five-short":
        pytest.skip("Big Five reverse-scoring covered in test_big_five_short.py")

    items = get_assessment_module_items(module_id)
    assert any(item.reverse_scored for item in items)


@pytest.mark.parametrize("module_id", EXPECTED_MODULE_IDS)
def test_deterministic_scoring_output(module_id: str):
    items = get_assessment_module_items(module_id)
    responses = [AssessmentResponse(item_id=item.id, value=4) for item in items]

    first = score_assessment_module(module_id, responses)
    second = score_assessment_module(module_id, responses)

    assert first == second


def test_unknown_module_raises_value_error():
    with pytest.raises(ValueError, match="Unknown assessment module"):
        get_assessment_module_items("unknown-module")

    with pytest.raises(ValueError, match="Unknown assessment module"):
        score_assessment_module("unknown-module", [])
