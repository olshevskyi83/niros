import pytest

from niros.big_five.profile import BigFiveProfile
from niros.big_five.questionnaire import BIG_FIVE_QUESTIONNAIRE, questionnaire_item_ids
from niros.big_five.scorer import (
    normalize_trait_mean,
    recode_item_response,
    score_big_five,
    score_big_five_from_list,
)
from niros.human_digital_fingerprint import (
    build_human_digital_fingerprint,
    describe_big_five_trait,
    format_human_digital_fingerprint,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact


def _pattern_tag(canonical_id: str, confidence: float = 0.8) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-001",
        evidence_id="session-001:evidence:0",
        canonical_id=canonical_id,
        matched_text="I do not know who I am",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _neutral_answers() -> dict[str, int]:
    return {item.item_id: 3 for item in BIG_FIVE_QUESTIONNAIRE}


def _high_neuroticism_answers() -> dict[str, int]:
    answers = _neutral_answers()
    for item in BIG_FIVE_QUESTIONNAIRE:
        if item.domain != "neuroticism":
            continue
        answers[item.item_id] = 5 if item.keyed == "positive" else 1
    return answers


def test_questionnaire_has_twenty_items_with_four_per_trait():
    assert len(BIG_FIVE_QUESTIONNAIRE) == 20
    for trait in BigFiveProfile.TRAIT_FIELDS:
        trait_items = [item for item in BIG_FIVE_QUESTIONNAIRE if item.domain == trait]
        assert len(trait_items) == 4


def test_reverse_scoring_recode():
    assert recode_item_response(1, "reverse") == 5
    assert recode_item_response(5, "reverse") == 1
    assert recode_item_response(3, "reverse") == 3
    assert recode_item_response(4, "positive") == 4


def test_normalize_trait_mean_maps_scale_to_unit_interval():
    assert normalize_trait_mean(1.0) == pytest.approx(0.0)
    assert normalize_trait_mean(3.0) == pytest.approx(0.5)
    assert normalize_trait_mean(5.0) == pytest.approx(1.0)


def test_score_big_five_neutral_answers_produce_mid_scores():
    profile = score_big_five(_neutral_answers())

    assert profile.openness == pytest.approx(0.5)
    assert profile.conscientiousness == pytest.approx(0.5)
    assert profile.extraversion == pytest.approx(0.5)
    assert profile.agreeableness == pytest.approx(0.5)
    assert profile.neuroticism == pytest.approx(0.5)


def test_score_big_five_from_list_matches_answer_map():
    answers = [3] * 20
    profile = score_big_five_from_list(answers)

    assert profile.to_dict() == score_big_five(_neutral_answers()).to_dict()


def test_score_big_five_high_neuroticism():
    profile = score_big_five(_high_neuroticism_answers())

    assert profile.neuroticism == pytest.approx(1.0)
    assert profile.openness == pytest.approx(0.5)


def test_score_big_five_rejects_invalid_answer():
    answers = _neutral_answers()
    answers["bf_o_01"] = 6

    with pytest.raises(ValueError, match="must be between"):
        score_big_five(answers)


def test_high_neuroticism_affects_profile_summary():
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[],
        semantic_facts=[],
        big_five_answers=_high_neuroticism_answers(),
    )

    summary = fingerprint["summary_text"]

    assert "neuroticism=1.00" in summary
    assert "emotional reactivity" in summary
    assert "sensitivity to stress" in summary


def test_human_digital_fingerprint_includes_patterns_semantic_facts_and_big_five():
    pattern = _pattern_tag("identity_uncertainty")
    fact = SemanticFact(
        category="emotion",
        attribute="worry",
        value="present",
        evidence="I worry a lot",
        confidence=0.7,
    )

    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[pattern],
        semantic_facts=[fact],
        big_five_answers=_neutral_answers(),
    )

    summary = fingerprint["summary_text"]

    assert fingerprint["patterns"]["primary_pattern"]["canonical_id"] == "identity_uncertainty"
    assert fingerprint["semantic_facts"][0]["category"] == "emotion"
    assert fingerprint["big_five"]["neuroticism"] == pytest.approx(0.5)
    assert "Primary interview pattern" in summary
    assert "Semantic facts:" in summary
    assert "Big Five self-report:" in summary


def test_no_diagnosis_language_in_big_five_output():
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[],
        big_five_answers=_high_neuroticism_answers(),
    )
    summary = fingerprint["summary_text"].lower()

    forbidden_terms = (
        "disorder",
        "diagnosis",
        "diagnostic",
        "pathology",
        "clinical label",
        "personality disorder",
        "mental illness",
    )
    for term in forbidden_terms:
        assert term not in summary

    assert "not diagnoses" in summary


def test_describe_big_five_trait_uses_non_diagnostic_language():
    assert "stress" in describe_big_five_trait("neuroticism", 0.9)
    assert "moderate" in describe_big_five_trait("openness", 0.5)


def test_format_human_digital_fingerprint_without_data():
    rendered = format_human_digital_fingerprint(
        {"patterns": {"pattern_counts": {}}, "semantic_facts": [], "big_five": None}
    )

    assert "not enough evidence" in rendered.lower()


def test_questionnaire_item_ids_are_unique():
    item_ids = questionnaire_item_ids()
    assert len(item_ids) == len(set(item_ids))
