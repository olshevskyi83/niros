from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "low_mood_depression_signals"

LOW_MOOD_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "lm_01",
        "domain_id": "low_mood",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Most days my mood feels lower than I would like.",
            "uk": "Більшість днів мій настрій нижчий, ніж мені хотілося б.",
            "ru": "Большинство дней моё настроение ниже, чем мне хотелось бы.",
            "es": "La mayoría de los días mi ánimo se siente más bajo de lo que me gustaría.",
        },
    },
    {
        "id": "lm_02",
        "domain_id": "low_mood",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I often notice my mood lifting during ordinary moments.",
            "uk": "Я часто помічаю, що настрій піднімається в звичайні моменти.",
            "ru": "Я часто замечаю, что настроение поднимается в обычные моменты.",
            "es": "A menudo noto que mi ánimo se eleva en momentos ordinarios.",
        },
    },
    {
        "id": "lm_03",
        "domain_id": "anhedonia",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Things I used to enjoy feel less interesting lately.",
            "uk": "Те, що раніше приносило задоволення, останнім часом менше цікавить.",
            "ru": "То, что раньше приносило удовольствие, в последнее время меньше интересует.",
            "es": "Lo que antes disfrutaba me interesa menos últimamente.",
        },
    },
    {
        "id": "lm_04",
        "domain_id": "hopelessness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "It feels hard to imagine things getting better.",
            "uk": "Важко уявити, що стан може покращитися.",
            "ru": "Трудно представить, что состояние может улучшиться.",
            "es": "Me cuesta imaginar que las cosas puedan mejorar.",
        },
    },
    {
        "id": "lm_05",
        "domain_id": "functioning_impact",
        "reverse_scored": False,
        "text_by_language": {
            "en": "My daily tasks feel harder to keep up with.",
            "uk": "Щоденні справи даються важче, ніж раніше.",
            "ru": "Повседневные дела даются труднее, чем раньше.",
            "es": "Mis tareas diarias me resultan más difíciles de sostener.",
        },
    },
    {
        "id": "lm_06",
        "domain_id": "functioning_impact",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can still manage most of my daily responsibilities.",
            "uk": "Я все ще можу справлятися з більшістю щоденних обовʼязків.",
            "ru": "Я всё ещё могу справляться с большинством ежедневных обязанностей.",
            "es": "Todavía puedo manejar la mayoría de mis responsabilidades diarias.",
        },
    },
)


def get_low_mood_short_items(language: str = "en"):
    return get_items_from_specs(LOW_MOOD_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_low_mood_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_low_mood_short_items(), responses)
