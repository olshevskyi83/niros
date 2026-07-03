from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "grief_loss_bereavement"

GRIEF_LOSS_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "grf_01",
        "domain_id": "grief_intensity",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Feelings linked to my loss still feel very strong.",
            "uk": "Почуття, повʼязані з втратою, досі відчуваються дуже сильними.",
            "ru": "Чувства, связанные с потерей, всё ещё ощущаются очень сильными.",
            "es": "Los sentimientos ligados a mi pérdida aún se sienten muy intensos.",
        },
    },
    {
        "id": "grf_02",
        "domain_id": "grief_intensity",
        "reverse_scored": True,
        "text_by_language": {
            "en": "Moments of warmth or connection still reach me despite the loss.",
            "uk": "Моменти тепла чи звʼязку досі до мене доходять попри втрату.",
            "ru": "Моменты тепла или связи всё ещё доходят до меня несмотря на потерю.",
            "es": "Momentos de calidez o conexión aún me llegan a pesar de la pérdida.",
        },
    },
    {
        "id": "grf_03",
        "domain_id": "loss_preoccupation",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Thoughts about the loss take up a lot of my mental space.",
            "uk": "Думки про втрату займають багато місця в моїй голові.",
            "ru": "Мысли о потере занимают много места в моей голове.",
            "es": "Los pensamientos sobre la pérdida ocupan mucho espacio en mi mente.",
        },
    },
    {
        "id": "grf_04",
        "domain_id": "difficulty_accepting_loss",
        "reverse_scored": False,
        "text_by_language": {
            "en": "It still feels unreal or hard to accept that this loss happened.",
            "uk": "Досі важко прийняти, що ця втрата сталася.",
            "ru": "Всё ещё трудно принять, что эта потеря произошла.",
            "es": "Todavía me cuesta aceptar que esta pérdida ocurrió.",
        },
    },
    {
        "id": "grf_05",
        "domain_id": "life_after_loss",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Daily life feels changed in ways that are hard to adjust to.",
            "uk": "Щоденне життя змінилося так, що важко до цього звикнути.",
            "ru": "Повседневная жизнь изменилась так, что трудно к этому привыкнуть.",
            "es": "La vida diaria cambió de formas difíciles de ajustar.",
        },
    },
    {
        "id": "grf_06",
        "domain_id": "life_after_loss",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I am finding small ways to move through life after the loss.",
            "uk": "Я знаходжу невеликі способи рухатися далі після втрати.",
            "ru": "Я нахожу небольшие способы двигаться дальше после потери.",
            "es": "Estoy encontrando pequeñas formas de seguir adelante tras la pérdida.",
        },
    },
)


def get_grief_loss_short_items(language: str = "en"):
    return get_items_from_specs(GRIEF_LOSS_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_grief_loss_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_grief_loss_short_items(), responses)
