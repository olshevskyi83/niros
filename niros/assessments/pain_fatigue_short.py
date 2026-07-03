from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "chronic_pain_fibromyalgia_fatigue"

PAIN_FATIGUE_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "pnf_01",
        "domain_id": "pain_burden",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Pain or discomfort is a frequent part of my day.",
            "uk": "Біль або дискомфорт часто супроводжують мій день.",
            "ru": "Боль или дискомфорт часто сопровождают мой день.",
            "es": "El dolor o malestar es una parte frecuente de mi día.",
        },
    },
    {
        "id": "pnf_02",
        "domain_id": "pain_burden",
        "reverse_scored": True,
        "text_by_language": {
            "en": "There are stretches of time when physical discomfort feels manageable.",
            "uk": "Бувають періоди, коли фізичний дискомфорт здається керованим.",
            "ru": "Бывают периоды, когда физический дискомфорт кажется управляемым.",
            "es": "Hay periodos en los que el malestar físico se siente manejable.",
        },
    },
    {
        "id": "pnf_03",
        "domain_id": "fatigue",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Fatigue limits what I can do more than I would like.",
            "uk": "Втома обмежує те, що я можу робити, більше, ніж хотілося б.",
            "ru": "Усталость ограничивает то, что я могу делать, больше, чем хотелось бы.",
            "es": "La fatiga limita lo que puedo hacer más de lo que me gustaría.",
        },
    },
    {
        "id": "pnf_04",
        "domain_id": "body_sensitivity",
        "reverse_scored": False,
        "text_by_language": {
            "en": "My body feels unusually sensitive to touch, movement, or effort.",
            "uk": "Тіло відчувається незвично чутливим до дотику, руху чи навантаження.",
            "ru": "Тело ощущается необычно чувствительным к прикосновению, движению или нагрузке.",
            "es": "Mi cuerpo se siente inusualmente sensible al tacto, movimiento o esfuerzo.",
        },
    },
    {
        "id": "pnf_05",
        "domain_id": "activity_limitation",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Physical symptoms make me cut back on activities I value.",
            "uk": "Фізичні симптоми змушують скорочувати важливі для мене заняття.",
            "ru": "Физические симптомы заставляют сокращать важные для меня занятия.",
            "es": "Los síntomas físicos me hacen reducir actividades que valoro.",
        },
    },
    {
        "id": "pnf_06",
        "domain_id": "symptom_unpredictability",
        "reverse_scored": False,
        "text_by_language": {
            "en": "It is hard to predict when symptoms will flare up.",
            "uk": "Важко передбачити, коли симптоми посиляться.",
            "ru": "Трудно предсказать, когда симптомы усилятся.",
            "es": "Es difícil predecir cuándo los síntomas empeorarán.",
        },
    },
)


def get_pain_fatigue_short_items(language: str = "en"):
    return get_items_from_specs(PAIN_FATIGUE_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_pain_fatigue_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_pain_fatigue_short_items(), responses)
