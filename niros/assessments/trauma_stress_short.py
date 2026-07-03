from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "trauma_stress_signals"

TRAUMA_STRESS_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "trm_01",
        "domain_id": "intrusive_memories",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Unwanted memories or images come back when I do not expect them.",
            "uk": "Небажані спогади чи образи повертаються, коли я їх не очікую.",
            "ru": "Нежелательные воспоминания или образы возвращаются, когда я их не ожидаю.",
            "es": "Recuerdos o imágenes no deseadas vuelven cuando no los espero.",
        },
    },
    {
        "id": "trm_02",
        "domain_id": "intrusive_memories",
        "reverse_scored": True,
        "text_by_language": {
            "en": "Distressing memories usually fade when I turn my attention elsewhere.",
            "uk": "Тривожні спогади зазвичай слабшають, коли я перемикаю увагу.",
            "ru": "Тревожные воспоминания обычно ослабевают, когда я переключаю внимание.",
            "es": "Los recuerdos angustiantes suelen desvanecerse cuando dirijo la atención a otra cosa.",
        },
    },
    {
        "id": "trm_03",
        "domain_id": "avoidance",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I avoid places, people, or reminders linked to difficult events.",
            "uk": "Я уникаю місць, людей або нагадувань, повʼязаних із важкими подіями.",
            "ru": "Я избегаю мест, людей или напоминаний, связанных с трудными событиями.",
            "es": "Evito lugares, personas o recordatorios ligados a eventos difíciles.",
        },
    },
    {
        "id": "trm_04",
        "domain_id": "hypervigilance",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I stay on alert for signs that something could go wrong.",
            "uk": "Я залишаюся напоготові до ознак того, що щось може піти не так.",
            "ru": "Я остаюсь начеку к признакам того, что что-то может пойти не так.",
            "es": "Me mantengo alerta ante señales de que algo podría salir mal.",
        },
    },
    {
        "id": "trm_05",
        "domain_id": "post_event_distress",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Difficult events still weigh on how I feel day to day.",
            "uk": "Важкі події досі впливають на мій щоденний стан.",
            "ru": "Трудные события всё ещё влияют на моё ежедневное состояние.",
            "es": "Los eventos difíciles aún pesan en cómo me siento día a día.",
        },
    },
    {
        "id": "trm_06",
        "domain_id": "post_event_distress",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can talk about past events without feeling overwhelmed.",
            "uk": "Я можу говорити про минулі події без відчуття перевантаження.",
            "ru": "Я могу говорить о прошлых событиях без чувства перегрузки.",
            "es": "Puedo hablar de eventos pasados sin sentirme abrumado.",
        },
    },
)


def get_trauma_stress_short_items(language: str = "en"):
    return get_items_from_specs(TRAUMA_STRESS_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_trauma_stress_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_trauma_stress_short_items(), responses)
