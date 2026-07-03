from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "psychedelic_session_concerns"

PSYCHEDELIC_CONCERN_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "psy_01",
        "domain_id": "fear_of_bad_trip",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I worry that a session could become frightening or overwhelming.",
            "uk": "Я хвилююся, що сесія може стати лякаючою або надто інтенсивною.",
            "ru": "Я беспокоюсь, что сессия может стать пугающей или слишком интенсивной.",
            "es": "Me preocupa que una sesión pueda volverse aterradora o abrumadora.",
        },
    },
    {
        "id": "psy_02",
        "domain_id": "fear_of_bad_trip",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I feel I could ask for support if a session felt too intense.",
            "uk": "Я відчуваю, що зможу попросити підтримку, якщо сесія стане надто інтенсивною.",
            "ru": "Я чувствую, что смогу попросить поддержку, если сессия станет слишком интенсивной.",
            "es": "Siento que podría pedir apoyo si una sesión se sintiera demasiado intensa.",
        },
    },
    {
        "id": "psy_03",
        "domain_id": "fear_of_losing_control",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I worry about losing control during an inner experience.",
            "uk": "Я хвилююся через можливість втратити контроль під час внутрішнього досвіду.",
            "ru": "Я беспокоюсь о возможности потерять контроль во время внутреннего опыта.",
            "es": "Me preocupa perder el control durante una experiencia interior.",
        },
    },
    {
        "id": "psy_04",
        "domain_id": "trust_in_facilitator",
        "reverse_scored": False,
        "text_by_language": {
            "en": "It would help me to trust the person guiding the session.",
            "uk": "Мені допомогло б довіряти людині, яка супроводжує сесію.",
            "ru": "Мне помогло бы доверять человеку, который сопровождает сессию.",
            "es": "Me ayudaría confiar en la persona que guía la sesión.",
        },
    },
    {
        "id": "psy_05",
        "domain_id": "surrender_difficulty",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Letting go and allowing the experience feels difficult for me.",
            "uk": "Відпустити контроль і дозволити досвіду розгортатися мені важко.",
            "ru": "Отпустить контроль и позволить опыту разворачиваться мне трудно.",
            "es": "Soltar y permitir que la experiencia se desarrolle me resulta difícil.",
        },
    },
    {
        "id": "psy_06",
        "domain_id": "fear_of_body_sensations",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Strong body sensations during a session would unsettle me.",
            "uk": "Сильні відчуття в тілі під час сесії мене турбують.",
            "ru": "Сильные ощущения в теле во время сессии меня беспокоят.",
            "es": "Las sensaciones corporales intensas durante una sesión me inquietarían.",
        },
    },
)


def get_psychedelic_concern_short_items(language: str = "en"):
    return get_items_from_specs(PSYCHEDELIC_CONCERN_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_psychedelic_concern_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_psychedelic_concern_short_items(), responses)
