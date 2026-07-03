from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "existential_distress_meaning"

MEANING_PURPOSE_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "mng_01",
        "domain_id": "meaning_seeking",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I am searching for a clearer sense of meaning in my life.",
            "uk": "Я шукаю більш ясне відчуття сенсу у своєму житті.",
            "ru": "Я ищу более ясное ощущение смысла в своей жизни.",
            "es": "Busco un sentido de significado más claro en mi vida.",
        },
    },
    {
        "id": "mng_02",
        "domain_id": "loss_of_meaning",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Life feels empty or without direction more than I would like.",
            "uk": "Життя відчувається порожнім або без напряму більше, ніж хотілося б.",
            "ru": "Жизнь ощущается пустой или без направления больше, чем хотелось бы.",
            "es": "La vida se siente vacía o sin dirección más de lo que me gustaría.",
        },
    },
    {
        "id": "mng_03",
        "domain_id": "loss_of_meaning",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I still notice moments when life feels meaningful to me.",
            "uk": "Я все ще помічаю моменти, коли життя відчувається осмисленим.",
            "ru": "Я всё ещё замечаю моменты, когда жизнь ощущается осмысленной.",
            "es": "Todavía noto momentos en los que la vida se siente significativa.",
        },
    },
    {
        "id": "mng_04",
        "domain_id": "desire_for_change",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I want my life to move in a different direction.",
            "uk": "Я хочу, щоб моє життя рухалося в іншому напрямку.",
            "ru": "Я хочу, чтобы моя жизнь двигалась в другом направлении.",
            "es": "Quiero que mi vida vaya en una dirección diferente.",
        },
    },
    {
        "id": "mng_05",
        "domain_id": "values_clarity",
        "reverse_scored": False,
        "text_by_language": {
            "en": "It is hard to know what matters most to me right now.",
            "uk": "Важко зрозуміти, що для мене зараз найважливіше.",
            "ru": "Трудно понять, что для меня сейчас наиболее важно.",
            "es": "Me cuesta saber qué es lo más importante para mí ahora.",
        },
    },
    {
        "id": "mng_06",
        "domain_id": "integration_goal",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I want to bring what I learn about myself into daily life.",
            "uk": "Я хочу переносити те, що дізнаюся про себе, у щоденне життя.",
            "ru": "Я хочу переносить то, что узнаю о себе, в повседневную жизнь.",
            "es": "Quiero llevar lo que aprendo sobre mí a la vida diaria.",
        },
    },
)


def get_meaning_purpose_short_items(language: str = "en"):
    return get_items_from_specs(MEANING_PURPOSE_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_meaning_purpose_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_meaning_purpose_short_items(), responses)
