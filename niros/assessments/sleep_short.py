from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "sleep_nightmares"

SLEEP_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "slp_01",
        "domain_id": "insomnia",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I have trouble falling asleep or staying asleep.",
            "uk": "Мені важко заснути або не прокидатися вночі.",
            "ru": "Мне трудно заснуть или не просыпаться ночью.",
            "es": "Me cuesta conciliar el sueño o mantenerlo.",
        },
    },
    {
        "id": "slp_02",
        "domain_id": "insomnia",
        "reverse_scored": True,
        "text_by_language": {
            "en": "Most nights I get enough uninterrupted sleep.",
            "uk": "Більшість ночей я сплю достатньо без частих пробуджень.",
            "ru": "Большинство ночей я сплю достаточно без частых пробуждений.",
            "es": "La mayoría de las noches duermo lo suficiente sin interrupciones frecuentes.",
        },
    },
    {
        "id": "slp_03",
        "domain_id": "nightmares",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Disturbing dreams or nightmares affect my sleep.",
            "uk": "Тривожні сни або кошмари впливають на мій сон.",
            "ru": "Тревожные сны или кошмары влияют на мой сон.",
            "es": "Sueños perturbadores o pesadillas afectan mi sueño.",
        },
    },
    {
        "id": "slp_04",
        "domain_id": "sleep_quality",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Even after sleeping, I often do not feel rested.",
            "uk": "Навіть після сну я часто не відчуваю відновлення.",
            "ru": "Даже после сна я часто не чувствую восстановления.",
            "es": "Incluso después de dormir, a menudo no me siento descansado.",
        },
    },
    {
        "id": "slp_05",
        "domain_id": "daytime_impact",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Poor sleep makes my days harder to get through.",
            "uk": "Поганий сон ускладнює переживання дня.",
            "ru": "Плохой сон усложняет переживание дня.",
            "es": "El mal sueño hace que los días me cuesten más.",
        },
    },
    {
        "id": "slp_06",
        "domain_id": "daytime_impact",
        "reverse_scored": True,
        "text_by_language": {
            "en": "Sleep problems rarely interfere with my daytime focus.",
            "uk": "Проблеми зі сном рідко заважають зосередженості вдень.",
            "ru": "Проблемы со сном редко мешают сосредоточенности днём.",
            "es": "Los problemas de sueño rara vez interfieren con mi concentración diurna.",
        },
    },
)


def get_sleep_short_items(language: str = "en"):
    return get_items_from_specs(SLEEP_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_sleep_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_sleep_short_items(), responses)
