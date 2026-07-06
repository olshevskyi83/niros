"""Semantic validation fixtures — realistic text cases and expected signal mappings."""

from __future__ import annotations

from dataclasses import dataclass

from niros.pattern_person_fit_contracts import PersonFitProfile


@dataclass(frozen=True)
class SemanticValidationCase:
    case_id: str
    user_text: str
    expected_signals: tuple[str, ...]
    expected_domains: tuple[str, ...]
    expected_needs: tuple[str, ...]
    expected_risk_signals: tuple[str, ...] = ()


def build_profile_from_case(case: SemanticValidationCase) -> PersonFitProfile:
    """Build a PersonFitProfile from a semantic validation case."""
    return PersonFitProfile(
        profile_id=case.case_id,
        active_signals=case.expected_signals,
        dominant_domains=case.expected_domains,
        needs=case.expected_needs,
        risk_signals=case.expected_risk_signals,
        session_phase="preparation",
    )


def semantic_validation_cases() -> tuple[SemanticValidationCase, ...]:
    """Deterministic catalog of semantic validation cases."""
    return (
        SemanticValidationCase(
            case_id="semantic_case_shame_self_criticism",
            user_text=(
                "Я постійно думаю, що зі мною щось не так. Мені соромно за себе, "
                "я дуже жорстко себе критикую і намагаюся не відчувати сильних емоцій."
            ),
            expected_signals=(
                "shame_sensitivity",
                "harsh_self_criticism",
                "emotional_avoidance",
            ),
            expected_domains=("self", "emotion_regulation"),
            expected_needs=("self_compassion", "emotional_tolerance"),
            expected_risk_signals=("overwhelm_risk",),
        ),
        SemanticValidationCase(
            case_id="semantic_case_values_confusion",
            user_text=(
                "Я не розумію, чого хочу. Начебто живу автоматично, але не відчуваю "
                "напрямку. Мені важко зрозуміти, які рішення мої."
            ),
            expected_signals=("values_confusion", "low_direction"),
            expected_domains=("values", "meaning"),
            expected_needs=("values_alignment",),
        ),
        SemanticValidationCase(
            case_id="semantic_case_meaning_emptiness",
            user_text=(
                "У мене відчуття порожнечі. Наче все втратило сенс. "
                "Я не розумію, заради чого щось робити."
            ),
            expected_signals=("existential_emptiness", "loss_of_meaning"),
            expected_domains=("meaning",),
            expected_needs=("meaning_making",),
        ),
        SemanticValidationCase(
            case_id="semantic_case_identity_diffusion",
            user_text=(
                "Я не розумію, хто я. У різних ситуаціях я ніби різна людина. "
                "Всередині немає цілісного відчуття себе."
            ),
            expected_signals=("identity_diffusion", "low_self_coherence"),
            expected_domains=("self", "meaning"),
            expected_needs=("identity_coherence",),
        ),
        SemanticValidationCase(
            case_id="semantic_case_rumination_catastrophizing",
            user_text=(
                "Я постійно прокручую думки в голові і уявляю найгірші сценарії. "
                "Не можу зупинити це мислення."
            ),
            expected_signals=("rumination", "catastrophizing"),
            expected_domains=("cognitive",),
            expected_needs=("cognitive_distance",),
        ),
        SemanticValidationCase(
            case_id="semantic_case_overwhelm_instability",
            user_text=(
                "Мене дуже швидко накриває. Емоції стають занадто сильними, "
                "і я боюся, що не витримаю."
            ),
            expected_signals=("overwhelm_risk", "emotional_instability"),
            expected_domains=("emotion_regulation",),
            expected_needs=("stabilization",),
            expected_risk_signals=("overwhelm_risk",),
        ),
        SemanticValidationCase(
            case_id="semantic_case_low_agency",
            user_text=(
                "Я відчуваю, що не керую своїм життям. Наче все вирішується без мене, "
                "а я просто пливу за течією."
            ),
            expected_signals=("low_agency", "learned_helplessness"),
            expected_domains=("self", "values"),
            expected_needs=("agency_support", "values_alignment"),
        ),
        SemanticValidationCase(
            case_id="semantic_case_rejection_sensitivity",
            user_text=(
                "Я дуже боюся, що мене відкинуть. Через це постійно підлаштовуюся "
                "під інших і не кажу, що насправді відчуваю."
            ),
            expected_signals=(
                "rejection_sensitivity",
                "people_pleasing",
                "emotional_suppression",
            ),
            expected_domains=("relationships", "emotion_regulation"),
            expected_needs=("boundary_support", "emotional_expression"),
        ),
    )


def test_all_cases_have_non_empty_user_text():
    for case in semantic_validation_cases():
        assert case.user_text.strip()


def test_all_cases_have_non_empty_expected_signals():
    for case in semantic_validation_cases():
        assert case.expected_signals


def test_all_cases_have_non_empty_expected_domains():
    for case in semantic_validation_cases():
        assert case.expected_domains


def test_build_profile_from_case_preserves_case_id():
    case = semantic_validation_cases()[0]
    profile = build_profile_from_case(case)
    assert profile.profile_id == case.case_id


def test_build_profile_from_case_maps_expected_signals_to_active_signals():
    case = semantic_validation_cases()[0]
    profile = build_profile_from_case(case)
    assert profile.active_signals == case.expected_signals


def test_build_profile_from_case_maps_expected_domains_to_dominant_domains():
    case = semantic_validation_cases()[0]
    profile = build_profile_from_case(case)
    assert profile.dominant_domains == case.expected_domains


def test_build_profile_from_case_maps_expected_needs_to_needs():
    case = semantic_validation_cases()[0]
    profile = build_profile_from_case(case)
    assert profile.needs == case.expected_needs


def test_build_profile_from_case_maps_expected_risk_signals_to_risk_signals():
    case = semantic_validation_cases()[0]
    profile = build_profile_from_case(case)
    assert profile.risk_signals == case.expected_risk_signals


def test_build_profile_from_case_sets_preparation_session_phase():
    case = semantic_validation_cases()[0]
    profile = build_profile_from_case(case)
    assert profile.session_phase == "preparation"


def test_all_case_ids_are_unique():
    case_ids = [case.case_id for case in semantic_validation_cases()]
    assert len(case_ids) == len(set(case_ids))


def test_cases_are_deterministic():
    first = semantic_validation_cases()
    second = semantic_validation_cases()
    assert first == second
