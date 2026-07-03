from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "anxiety_fear_panic"

ANXIETY_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "anx_01",
        "domain_id": "worry",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I find myself worrying about many things.",
            "uk": "Я часто хвилююся з багатьох приводів.",
            "ru": "Я часто беспокоюсь по многим поводам.",
            "es": "Me encuentro preocupándome por muchas cosas.",
        },
    },
    {
        "id": "anx_02",
        "domain_id": "worry",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can usually let worries pass without getting stuck on them.",
            "uk": "Зазвичай я можу відпустити тривогу, не застрягаючи в ній.",
            "ru": "Обычно я могу отпустить тревогу, не застревая в ней.",
            "es": "Normalmente puedo dejar pasar las preocupaciones sin quedarme atrapado en ellas.",
        },
    },
    {
        "id": "anx_03",
        "domain_id": "panic",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Sudden waves of fear or panic come over me at times.",
            "uk": "Іноді на мене накочують раптові хвилі страху чи паніки.",
            "ru": "Иногда на меня накатывают внезапные волны страха или паники.",
            "es": "A veces me invaden oleadas repentinas de miedo o pánico.",
        },
    },
    {
        "id": "anx_04",
        "domain_id": "somatic_anxiety",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Stress shows up in my body as tension or restlessness.",
            "uk": "Стрес проявляється в тілі як напруга або неспокій.",
            "ru": "Стресс проявляется в теле как напряжение или беспокойство.",
            "es": "El estrés se manifiesta en mi cuerpo como tensión o inquietud.",
        },
    },
    {
        "id": "anx_05",
        "domain_id": "somatic_anxiety",
        "reverse_scored": True,
        "text_by_language": {
            "en": "My body usually feels calm when nothing urgent is happening.",
            "uk": "Коли немає нагальних причин, тіло зазвичай відчувається спокійним.",
            "ru": "Когда нет срочных причин, тело обычно ощущается спокойным.",
            "es": "Mi cuerpo suele sentirse calmado cuando no hay nada urgente.",
        },
    },
    {
        "id": "anx_06",
        "domain_id": "fear_of_losing_control",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I worry about losing control over myself or the situation.",
            "uk": "Я хвилююся через можливість втратити контроль над собою чи ситуацією.",
            "ru": "Я беспокоюсь о возможности потерять контроль над собой или ситуацией.",
            "es": "Me preocupa perder el control sobre mí mismo o la situación.",
        },
    },
)


def get_anxiety_short_items(language: str = "en"):
    return get_items_from_specs(ANXIETY_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_anxiety_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_anxiety_short_items(), responses)
