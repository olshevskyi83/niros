import pytest

from niros.assessment import (
    AssessmentResponse,
    FORBIDDEN_INTERPRETATION_PHRASES,
    interpretation_is_neutral,
    recode_assessment_response,
)
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
    score_assessment_module,
)

CORE_DOMAIN_MODULE_IDS: tuple[str, ...] = (
    "self-domain-short",
    "emotion-regulation-domain-short",
    "cognitive-patterns-domain-short",
    "relationships-domain-short",
    "values-identity-domain-short",
    "emotional-flexibility-domain-short",
)

EXPECTED_FINGERPRINT_DIMENSIONS: dict[str, str] = {
    "self-domain-short": "self_domain",
    "emotion-regulation-domain-short": "emotion_regulation_domain",
    "cognitive-patterns-domain-short": "cognitive_patterns_domain",
    "relationships-domain-short": "relationships_domain",
    "values-identity-domain-short": "values_identity_domain",
    "emotional-flexibility-domain-short": "emotional_flexibility_domain",
}

EXPECTED_DIMENSION_COUNTS: dict[str, int] = {
    "self-domain-short": 6,
    "emotion-regulation-domain-short": 6,
    "cognitive-patterns-domain-short": 6,
    "relationships-domain-short": 6,
    "values-identity-domain-short": 6,
    "emotional-flexibility-domain-short": 6,
}


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_modules_are_registered(module_id: str):
    items = get_assessment_module_items(module_id)
    assert len(items) == 6


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
@pytest.mark.parametrize("language", sorted(SUPPORTED_LANGUAGES))
def test_core_domain_modules_support_all_languages(module_id: str, language: str):
    items = get_assessment_module_items(module_id, language)

    assert len(items) == 6
    for item in items:
        assert language in item.text_by_language
        assert item_text_for_language(item, language).strip()


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_modules_have_six_items(module_id: str):
    items = get_assessment_module_items(module_id)

    assert len(items) == 6
    assert len({item.id for item in items}) == 6
    assert len({item.domain_id for item in items}) == EXPECTED_DIMENSION_COUNTS[module_id]


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_modules_use_one_to_five_scale(module_id: str):
    items = get_assessment_module_items(module_id)

    for item in items:
        assert item.scale_min == SCALE_MIN
        assert item.scale_max == SCALE_MAX


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_modules_have_reverse_scored_items(module_id: str):
    items = get_assessment_module_items(module_id)

    assert any(item.reverse_scored for item in items)
    assert any(not item.reverse_scored for item in items)


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_reverse_scoring_recode(module_id: str):
    items = get_assessment_module_items(module_id)
    reverse_item = next(item for item in items if item.reverse_scored)

    assert recode_assessment_response(1, reverse_item) == 5
    assert recode_assessment_response(5, reverse_item) == 1


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_fingerprint_output(module_id: str):
    items = get_assessment_module_items(module_id)
    expected = EXPECTED_FINGERPRINT_DIMENSIONS[module_id]

    for item in items:
        assert item.fingerprint_dimension == expected

    responses = [AssessmentResponse(item_id=item.id, value=3) for item in items]
    results = score_assessment_module(module_id, responses)

    assert len(results) == EXPECTED_DIMENSION_COUNTS[module_id]
    for result in results:
        assert result.fingerprint_dimension == expected


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_deterministic_scoring(module_id: str):
    items = get_assessment_module_items(module_id)
    responses = [AssessmentResponse(item_id=item.id, value=4) for item in items]

    first = score_assessment_module(module_id, responses)
    second = score_assessment_module(module_id, responses)

    assert first == second


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_summary_generation_uses_neutral_labels(module_id: str):
    items = get_assessment_module_items(module_id)
    responses = [AssessmentResponse(item_id=item.id, value=3) for item in items]
    results = score_assessment_module(module_id, responses)

    for result in results:
        assert result.domain_id
        assert result.score
        assert 0.0 <= result.normalized_score <= 1.0
        assert interpretation_is_neutral(result.interpretation)
        lowered = result.interpretation.lower()
        assert not any(phrase in lowered for phrase in FORBIDDEN_INTERPRETATION_PHRASES)


@pytest.mark.parametrize("module_id", CORE_DOMAIN_MODULE_IDS)
def test_core_domain_items_have_no_diagnostic_wording(module_id: str):
    items = get_assessment_module_items(module_id)

    for item in items:
        assert item_has_neutral_wording(item)
        for text in item.text_by_language.values():
            lowered = text.lower()
            assert not any(phrase in lowered for phrase in FORBIDDEN_ITEM_PHRASES)


def test_self_domain_module_covers_self_structure_dimensions():
    items = get_assessment_module_items("self-domain-short")
    domain_ids = {item.domain_id for item in items}

    assert domain_ids == {
        "self_worth",
        "shame",
        "self_compassion",
        "self_criticism",
        "agency",
        "belonging",
    }


def test_emotion_regulation_module_covers_regulation_dimensions():
    items = get_assessment_module_items("emotion-regulation-domain-short")
    domain_ids = {item.domain_id for item in items}

    assert domain_ids == {
        "emotional_awareness",
        "emotional_suppression",
        "emotional_overwhelm",
        "emotional_avoidance",
        "recovery",
        "regulation",
    }
