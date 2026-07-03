from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "behavioral_addictions"

BEHAVIORAL_ADDICTION_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "bad_01",
        "domain_id": "compulsive_behavior",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I repeat certain behaviors even when I know they are not helping.",
            "uk": "Я повторюю певні дії, навіть коли знаю, що вони не допомагають.",
            "ru": "Я повторяю определённые действия, даже когда знаю, что они не помогают.",
            "es": "Repito ciertos comportamientos aunque sé que no me ayudan.",
        },
    },
    {
        "id": "bad_02",
        "domain_id": "compulsive_behavior",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can usually pause before acting on a strong urge.",
            "uk": "Зазвичай я можу зупинитися перед тим, як піддатися сильному позиву.",
            "ru": "Обычно я могу остановиться перед тем, как поддаться сильному позыву.",
            "es": "Normalmente puedo pausar antes de actuar ante un impulso fuerte.",
        },
    },
    {
        "id": "bad_03",
        "domain_id": "loss_of_control",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Once I start, it is hard to stop the behavior when I planned to.",
            "uk": "Коли починаю, важко зупинитися тоді, коли планував.",
            "ru": "Когда начинаю, трудно остановиться тогда, когда планировал.",
            "es": "Una vez que empiezo, me cuesta parar cuando lo había planeado.",
        },
    },
    {
        "id": "bad_04",
        "domain_id": "preoccupation",
        "reverse_scored": False,
        "text_by_language": {
            "en": "The behavior occupies my thoughts more than I would like.",
            "uk": "Ця поведінка займає думки більше, ніж мені хотілося б.",
            "ru": "Это поведение занимает мысли больше, чем мне хотелось бы.",
            "es": "El comportamiento ocupa mis pensamientos más de lo que me gustaría.",
        },
    },
    {
        "id": "bad_05",
        "domain_id": "consequences",
        "reverse_scored": False,
        "text_by_language": {
            "en": "The behavior creates problems in my daily life or relationships.",
            "uk": "Ця поведінка створює проблеми в щоденному житті чи стосунках.",
            "ru": "Это поведение создаёт проблемы в повседневной жизни или отношениях.",
            "es": "El comportamiento crea problemas en mi vida diaria o relaciones.",
        },
    },
    {
        "id": "bad_06",
        "domain_id": "failed_attempts_to_reduce",
        "reverse_scored": False,
        "text_by_language": {
            "en": "My attempts to change this habit have not lasted as I hoped.",
            "uk": "Мої спроби змінити цю звичку не тривали так, як я сподівався.",
            "ru": "Мои попытки изменить эту привычку не продлились так, как я надеялся.",
            "es": "Mis intentos de cambiar este hábito no han durado como esperaba.",
        },
    },
)


def get_behavioral_addiction_short_items(language: str = "en"):
    return get_items_from_specs(BEHAVIORAL_ADDICTION_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_behavioral_addiction_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_behavioral_addiction_short_items(), responses)
