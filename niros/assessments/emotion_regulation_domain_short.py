from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "emotion_regulation_domain"

EMOTION_REGULATION_DOMAIN_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "er_01",
        "domain_id": "emotional_awareness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can usually name what I am feeling in the moment.",
            "uk": "Я зазвичай можу назвати те, що відчуваю в даний момент.",
            "ru": "Я обычно могу назвать то, что чувствую в данный момент.",
            "es": "Por lo general puedo nombrar lo que siento en el momento.",
        },
    },
    {
        "id": "er_02",
        "domain_id": "emotional_suppression",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often push my emotions away instead of letting them be there.",
            "uk": "Я часто відштовхую емоції замість того, щоб дозволити їм бути.",
            "ru": "Я часто отталкиваю эмоции вместо того, чтобы позволить им быть.",
            "es": "A menudo aparto mis emociones en lugar de dejarlas estar.",
        },
    },
    {
        "id": "er_03",
        "domain_id": "emotional_overwhelm",
        "reverse_scored": False,
        "text_by_language": {
            "en": "My emotions sometimes feel too strong to manage.",
            "uk": "Мої емоції іноді здаються надто сильними, щоб з ними впоратися.",
            "ru": "Мои эмоции иногда кажутся слишком сильными, чтобы с ними справиться.",
            "es": "Mis emociones a veces se sienten demasiado intensas para manejarlas.",
        },
    },
    {
        "id": "er_04",
        "domain_id": "emotional_avoidance",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often avoid situations because of how I might feel.",
            "uk": "Я часто уникаю ситуацій через те, як можу себе відчути.",
            "ru": "Я часто избегаю ситуаций из-за того, как могу себя почувствовать.",
            "es": "A menudo evito situaciones por cómo podría sentirme.",
        },
    },
    {
        "id": "er_05",
        "domain_id": "recovery",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I usually return to a steady state after emotional distress.",
            "uk": "Я зазвичай повертаюся до стабільного стану після емоційного напруження.",
            "ru": "Я обычно возвращаюсь к устойчивому состоянию после эмоционального напряжения.",
            "es": "Por lo general vuelvo a un estado estable después de una angustia emocional.",
        },
    },
    {
        "id": "er_06",
        "domain_id": "regulation",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can stay grounded even when my feelings are intense.",
            "uk": "Я можу залишатися стійким навіть коли почуття інтенсивні.",
            "ru": "Я могу оставаться устойчивым даже когда чувства интенсивны.",
            "es": "Puedo mantenerme estable incluso cuando mis sentimientos son intensos.",
        },
    },
)


def get_emotion_regulation_domain_short_items(language: str = "en"):
    return get_items_from_specs(
        EMOTION_REGULATION_DOMAIN_SHORT_ITEM_SPECS,
        FINGERPRINT_DIMENSION,
        language,
    )


def score_emotion_regulation_domain_short(
    responses: list[AssessmentResponse],
) -> list[AssessmentResult]:
    return score_items(get_emotion_regulation_domain_short_items(), responses)
