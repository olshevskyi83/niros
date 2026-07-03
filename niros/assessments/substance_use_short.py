from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "substance_use_patterns"

SUBSTANCE_USE_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "sub_01",
        "domain_id": "craving",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I feel a strong urge to use the substance when I try to stop.",
            "uk": "Коли намагаюся припинити, відчуваю сильний позив до речовини.",
            "ru": "Когда пытаюсь прекратить, чувствую сильный позыв к веществу.",
            "es": "Cuando intento dejarlo, siento un fuerte impulso de usar la sustancia.",
        },
    },
    {
        "id": "sub_02",
        "domain_id": "craving",
        "reverse_scored": True,
        "text_by_language": {
            "en": "Urges to use usually pass without me acting on them.",
            "uk": "Позиви до вживання зазвичай проходять без дій з мого боку.",
            "ru": "Позывы к употреблению обычно проходят без действий с моей стороны.",
            "es": "Los impulsos de usar suelen pasar sin que actúe sobre ellos.",
        },
    },
    {
        "id": "sub_03",
        "domain_id": "loss_of_control",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Once I start, it is hard to stop at the amount I planned.",
            "uk": "Коли починаю, важко зупинитися на запланованій кількості.",
            "ru": "Когда начинаю, трудно остановиться на запланированном количестве.",
            "es": "Una vez que empiezo, me cuesta parar en la cantidad que planeé.",
        },
    },
    {
        "id": "sub_04",
        "domain_id": "use_despite_consequences",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I keep using even when it creates problems in my life.",
            "uk": "Я продовжую вживати, навіть коли це створює проблеми в житті.",
            "ru": "Я продолжаю употреблять, даже когда это создаёт проблемы в жизни.",
            "es": "Sigo usando incluso cuando crea problemas en mi vida.",
        },
    },
    {
        "id": "sub_05",
        "domain_id": "preoccupation",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Thoughts about using take up more space than I would like.",
            "uk": "Думки про вживання займають більше місця, ніж мені хотілося б.",
            "ru": "Мысли об употреблении занимают больше места, чем мне хотелось бы.",
            "es": "Los pensamientos sobre usar ocupan más espacio del que me gustaría.",
        },
    },
    {
        "id": "sub_06",
        "domain_id": "failed_attempts_to_reduce",
        "reverse_scored": False,
        "text_by_language": {
            "en": "My attempts to cut down or stop have not worked as I hoped.",
            "uk": "Мої спроби зменшити або припинити не дали бажаного результату.",
            "ru": "Мои попытки сократить или прекратить не дали желаемого результата.",
            "es": "Mis intentos de reducir o dejar no han funcionado como esperaba.",
        },
    },
)


def get_substance_use_short_items(language: str = "en"):
    return get_items_from_specs(SUBSTANCE_USE_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_substance_use_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_substance_use_short_items(), responses)
