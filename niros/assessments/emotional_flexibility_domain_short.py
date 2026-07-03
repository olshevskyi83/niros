from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "emotional_flexibility_domain"

EMOTIONAL_FLEXIBILITY_DOMAIN_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "ef_01",
        "domain_id": "acceptance",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can allow difficult feelings to be present without fighting them.",
            "uk": "Я можу дозволити важким почуттям бути присутніми, не борючись з ними.",
            "ru": "Я могу позволить трудным чувствам присутствовать, не борясь с ними.",
            "es": "Puedo permitir que los sentimientos difíciles estén presentes sin luchar contra ellos.",
        },
    },
    {
        "id": "ef_02",
        "domain_id": "experiential_avoidance",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often try to escape what I feel inside.",
            "uk": "Я часто намагаюся втекти від того, що відчуваю всередині.",
            "ru": "Я часто пытаюсь убежать от того, что чувствую внутри.",
            "es": "A menudo intento escapar de lo que siento por dentro.",
        },
    },
    {
        "id": "ef_03",
        "domain_id": "psychological_flexibility",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can stay with discomfort and still choose what matters to me.",
            "uk": "Я можу залишатися з дискомфортом і все одно обирати те, що для мене важливо.",
            "ru": "Я могу оставаться с дискомфортом и всё равно выбирать то, что для меня важно.",
            "es": "Puedo permanecer con la incomodidad y aun así elegir lo que me importa.",
        },
    },
    {
        "id": "ef_04",
        "domain_id": "openness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I remain open to new experiences even when they feel unfamiliar.",
            "uk": "Я залишаюся відкритим до нового досвіду навіть коли він незнайомий.",
            "ru": "Я остаюсь открытым к новому опыту даже когда он незнаком.",
            "es": "Permanezco abierto a nuevas experiencias aunque se sientan poco familiares.",
        },
    },
    {
        "id": "ef_05",
        "domain_id": "adaptation",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can adjust my actions when a situation changes.",
            "uk": "Я можу змінювати свої дії, коли ситуація змінюється.",
            "ru": "Я могу менять свои действия, когда ситуация меняется.",
            "es": "Puedo ajustar mis acciones cuando la situación cambia.",
        },
    },
    {
        "id": "ef_06",
        "domain_id": "willingness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I am willing to move toward what matters even when it feels hard.",
            "uk": "Я готовий рухатися до важливого навіть коли це дається важко.",
            "ru": "Я готов двигаться к важному даже когда это даётся трудно.",
            "es": "Estoy dispuesto a avanzar hacia lo que importa aunque se sienta difícil.",
        },
    },
)


def get_emotional_flexibility_domain_short_items(language: str = "en"):
    return get_items_from_specs(
        EMOTIONAL_FLEXIBILITY_DOMAIN_SHORT_ITEM_SPECS,
        FINGERPRINT_DIMENSION,
        language,
    )


def score_emotional_flexibility_domain_short(
    responses: list[AssessmentResponse],
) -> list[AssessmentResult]:
    return score_items(get_emotional_flexibility_domain_short_items(), responses)
