from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "relationships_domain"

RELATIONSHIPS_DOMAIN_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "rl_01",
        "domain_id": "trust",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I find it hard to trust that others will be there for me.",
            "uk": "Мені важко довіряти, що інші будуть поруч, коли мені потрібно.",
            "ru": "Мне трудно доверять, что другие будут рядом, когда мне нужно.",
            "es": "Me cuesta confiar en que otros estarán ahí cuando los necesito.",
        },
    },
    {
        "id": "rl_02",
        "domain_id": "intimacy",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can let people know what matters to me without pulling away.",
            "uk": "Я можу показати людям, що для мене важливо, не віддаляючись.",
            "ru": "Я могу показать людям, что для меня важно, не отдаляясь.",
            "es": "Puedo mostrar a las personas lo que me importa sin alejarme.",
        },
    },
    {
        "id": "rl_03",
        "domain_id": "abandonment",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often worry that people close to me will leave.",
            "uk": "Я часто хвилююся, що близькі люди можуть піти.",
            "ru": "Я часто беспокоюсь, что близкие люди могут уйти.",
            "es": "A menudo me preocupa que las personas cercanas se vayan.",
        },
    },
    {
        "id": "rl_04",
        "domain_id": "boundaries",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can protect my own limits even when others want more from me.",
            "uk": "Я можу захищати власні межі навіть коли інші хочуть більше від мене.",
            "ru": "Я могу защищать свои границы даже когда другие хотят от меня большего.",
            "es": "Puedo proteger mis propios límites aunque otros quieran más de mí.",
        },
    },
    {
        "id": "rl_05",
        "domain_id": "dependence",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often feel that I need others to feel steady.",
            "uk": "Я часто відчуваю, що мені потрібні інші, щоб почуватися стійко.",
            "ru": "Я часто чувствую, что мне нужны другие, чтобы чувствовать устойчивость.",
            "es": "A menudo siento que necesito a otros para sentirme estable.",
        },
    },
    {
        "id": "rl_06",
        "domain_id": "attachment_security",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can ask for support without feeling that I will be rejected.",
            "uk": "Я можу просити підтримку, не відчуваючи, що мене відкинуть.",
            "ru": "Я могу просить поддержку, не чувствуя, что меня отвергнут.",
            "es": "Puedo pedir apoyo sin sentir que seré rechazado.",
        },
    },
)


def get_relationships_domain_short_items(language: str = "en"):
    return get_items_from_specs(
        RELATIONSHIPS_DOMAIN_SHORT_ITEM_SPECS,
        FINGERPRINT_DIMENSION,
        language,
    )


def score_relationships_domain_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_relationships_domain_short_items(), responses)
