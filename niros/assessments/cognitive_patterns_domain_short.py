from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "cognitive_patterns_domain"

COGNITIVE_PATTERNS_DOMAIN_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "cp_01",
        "domain_id": "rumination",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often replay the same thoughts again and again.",
            "uk": "Я часто прокручую одні й ті самі думки знову і знову.",
            "ru": "Я часто прокручиваю одни и те же мысли снова и снова.",
            "es": "A menudo repito una y otra vez los mismos pensamientos.",
        },
    },
    {
        "id": "cp_02",
        "domain_id": "catastrophizing",
        "reverse_scored": False,
        "text_by_language": {
            "en": "When something goes wrong, I quickly imagine the worst outcome.",
            "uk": "Коли щось іде не так, я швидко уявляю найгірший результат.",
            "ru": "Когда что-то идёт не так, я быстро представляю худший исход.",
            "es": "Cuando algo sale mal, imagino rápidamente el peor resultado.",
        },
    },
    {
        "id": "cp_03",
        "domain_id": "black_white_thinking",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I often see situations in only two extremes.",
            "uk": "Я часто бачу ситуації лише в двох крайнощах.",
            "ru": "Я часто вижу ситуации только в двух крайностях.",
            "es": "A menudo veo las situaciones solo en dos extremos.",
        },
    },
    {
        "id": "cp_04",
        "domain_id": "overgeneralization",
        "reverse_scored": False,
        "text_by_language": {
            "en": "One difficult event often feels like a pattern that will repeat.",
            "uk": "Одна складна подія часто здається закономірністю, що повториться.",
            "ru": "Одно трудное событие часто кажется закономерностью, которая повторится.",
            "es": "Un evento difícil a menudo se siente como un patrón que se repetirá.",
        },
    },
    {
        "id": "cp_05",
        "domain_id": "hopelessness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "It often feels like nothing I do will make a real difference.",
            "uk": "Часто здається, що нічого з того, що я роблю, не матиме справжнього значення.",
            "ru": "Часто кажется, что ничто из того, что я делаю, не имеет реального значения.",
            "es": "A menudo siento que nada de lo que hago marcará una diferencia real.",
        },
    },
    {
        "id": "cp_06",
        "domain_id": "mental_flexibility",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can usually imagine more than one way to see a situation.",
            "uk": "Я зазвичай можу уявити більше ніж один спосіб побачити ситуацію.",
            "ru": "Я обычно могу представить больше одного способа увидеть ситуацию.",
            "es": "Por lo general puedo imaginar más de una forma de ver una situación.",
        },
    },
)


def get_cognitive_patterns_domain_short_items(language: str = "en"):
    return get_items_from_specs(
        COGNITIVE_PATTERNS_DOMAIN_SHORT_ITEM_SPECS,
        FINGERPRINT_DIMENSION,
        language,
    )


def score_cognitive_patterns_domain_short(
    responses: list[AssessmentResponse],
) -> list[AssessmentResult]:
    return score_items(get_cognitive_patterns_domain_short_items(), responses)
