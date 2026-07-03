from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "values_identity_domain"

VALUES_IDENTITY_DOMAIN_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "vi_01",
        "domain_id": "values_clarity",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I have a clear sense of what matters most to me.",
            "uk": "У мене є чітке відчуття того, що для мене найважливіше.",
            "ru": "У меня есть ясное ощущение того, что для меня важнее всего.",
            "es": "Tengo una idea clara de lo que más me importa.",
        },
    },
    {
        "id": "vi_02",
        "domain_id": "identity_clarity",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often feel uncertain about who I really am.",
            "uk": "Я часто відчуваю невизначеність щодо того, хто я насправді.",
            "ru": "Я часто чувствую неопределённость относительно того, кто я на самом деле.",
            "es": "A menudo me siento incierto sobre quién soy realmente.",
        },
    },
    {
        "id": "vi_03",
        "domain_id": "authenticity",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can live in a way that feels true to myself.",
            "uk": "Я можу жити так, як відчувається правдивим для мене.",
            "ru": "Я могу жить так, как ощущается правдивым для меня.",
            "es": "Puedo vivir de una forma que se siente fiel a mí mismo.",
        },
    },
    {
        "id": "vi_04",
        "domain_id": "inner_conflict",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Different parts of me often pull in opposite directions.",
            "uk": "Різні частини мене часто тягнуть у протилежні боки.",
            "ru": "Разные части меня часто тянут в противоположные стороны.",
            "es": "Distintas partes de mí a menudo tiran en direcciones opuestas.",
        },
    },
    {
        "id": "vi_05",
        "domain_id": "purpose_direction",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I feel a sense of direction in where my life is going.",
            "uk": "Я відчуваю напрямок у тому, куди рухається моє життя.",
            "ru": "Я чувствую направление в том, куда движется моя жизнь.",
            "es": "Siento una dirección hacia dónde va mi vida.",
        },
    },
    {
        "id": "vi_06",
        "domain_id": "role_confusion",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often feel unclear about the roles I am expected to play.",
            "uk": "Я часто не розумію, які ролі від мене очікують.",
            "ru": "Я часто не понимаю, какие роли от меня ожидают.",
            "es": "A menudo no tengo claro qué roles se esperan de mí.",
        },
    },
)


def get_values_identity_domain_short_items(language: str = "en"):
    return get_items_from_specs(
        VALUES_IDENTITY_DOMAIN_SHORT_ITEM_SPECS,
        FINGERPRINT_DIMENSION,
        language,
    )


def score_values_identity_domain_short(
    responses: list[AssessmentResponse],
) -> list[AssessmentResult]:
    return score_items(get_values_identity_domain_short_items(), responses)
