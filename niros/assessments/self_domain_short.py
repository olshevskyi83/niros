from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "self_domain"

SELF_DOMAIN_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "sd_01",
        "domain_id": "self_worth",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I often recognize my own worth even when things go wrong.",
            "uk": "Я часто визнаю власну цінність навіть коли щось іде не так.",
            "ru": "Я часто признаю собственную ценность даже когда что-то идёт не так.",
            "es": "A menudo reconozco mi propio valor incluso cuando las cosas salen mal.",
        },
    },
    {
        "id": "sd_02",
        "domain_id": "shame",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often feel exposed or flawed after making a mistake.",
            "uk": "Я часто відчуваю себе вразливим або недосконалим після помилки.",
            "ru": "Я часто чувствую себя уязвимым или недостаточным после ошибки.",
            "es": "A menudo me siento expuesto o defectuoso después de cometer un error.",
        },
    },
    {
        "id": "sd_03",
        "domain_id": "self_compassion",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I feel that I deserve kindness even when I make mistakes.",
            "uk": "Я відчуваю, що заслуговую на доброту навіть коли припускаю помилки.",
            "ru": "Я чувствую, что заслуживаю доброты даже когда допускаю ошибки.",
            "es": "Siento que merezco amabilidad incluso cuando cometo errores.",
        },
    },
    {
        "id": "sd_04",
        "domain_id": "self_criticism",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often judge myself more harshly than other people would.",
            "uk": "Я часто суджу себе суворіше, ніж це зробили б інші.",
            "ru": "Я часто сужу себя строже, чем это сделали бы другие.",
            "es": "A menudo me juzgo con más dureza de la que lo harían otras personas.",
        },
    },
    {
        "id": "sd_05",
        "domain_id": "agency",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I feel capable of influencing the direction of my life.",
            "uk": "Я відчуваю, що можу впливати на напрямок свого життя.",
            "ru": "Я чувствую, что могу влиять на направление своей жизни.",
            "es": "Siento que puedo influir en la dirección de mi vida.",
        },
    },
    {
        "id": "sd_06",
        "domain_id": "belonging",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often feel like I don't really belong.",
            "uk": "Я часто відчуваю, що мені справді немає місця.",
            "ru": "Я часто чувствую, что мне действительно негде быть.",
            "es": "A menudo siento que realmente no encajo.",
        },
    },
)


def get_self_domain_short_items(language: str = "en"):
    return get_items_from_specs(SELF_DOMAIN_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_self_domain_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_self_domain_short_items(), responses)
