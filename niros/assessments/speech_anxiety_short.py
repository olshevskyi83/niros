from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items

FINGERPRINT_DIMENSION = "speech_stuttering_expression"

SPEECH_ANXIETY_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "spk_01",
        "domain_id": "fear_of_speaking",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Speaking in front of others makes me tense or afraid.",
            "uk": "Говорити перед іншими викликає в мене напругу чи страх.",
            "ru": "Говорить перед другими вызывает у меня напряжение или страх.",
            "es": "Hablar delante de otros me pone tenso o temeroso.",
        },
    },
    {
        "id": "spk_02",
        "domain_id": "fear_of_speaking",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can speak comfortably in familiar one-to-one conversations.",
            "uk": "Мені комфортно говорити в знайомих розмовах один на один.",
            "ru": "Мне комфортно говорить в знакомых разговорах один на один.",
            "es": "Puedo hablar cómodamente en conversaciones familiares uno a uno.",
        },
    },
    {
        "id": "spk_03",
        "domain_id": "avoidance",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I avoid speaking situations when I can.",
            "uk": "Я уникаю ситуацій, де потрібно говорити, коли можу.",
            "ru": "Я избегаю ситуаций, где нужно говорить, когда могу.",
            "es": "Evito situaciones de habla cuando puedo.",
        },
    },
    {
        "id": "spk_04",
        "domain_id": "shame_about_speech",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I feel embarrassed or ashamed about how I speak.",
            "uk": "Мені соромно або незручно через те, як я говорю.",
            "ru": "Мне стыдно или неловко из-за того, как я говорю.",
            "es": "Me siento avergonzado por cómo hablo.",
        },
    },
    {
        "id": "spk_05",
        "domain_id": "loss_of_control_in_speech",
        "reverse_scored": False,
        "text_by_language": {
            "en": "When I speak, I worry that my words will not come out as I want.",
            "uk": "Коли говорю, хвилююся, що слова не вийдуть так, як хочу.",
            "ru": "Когда говорю, беспокоюсь, что слова не выйдут так, как хочу.",
            "es": "Cuando hablo, me preocupa que las palabras no salgan como quiero.",
        },
    },
    {
        "id": "spk_06",
        "domain_id": "loss_of_control_in_speech",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can usually finish sentences without getting stuck.",
            "uk": "Зазвичай я можу завершити речення без застрягання.",
            "ru": "Обычно я могу закончить предложение без застревания.",
            "es": "Normalmente puedo terminar frases sin quedarme atascado.",
        },
    },
)


def get_speech_anxiety_short_items(language: str = "en"):
    return get_items_from_specs(SPEECH_ANXIETY_SHORT_ITEM_SPECS, FINGERPRINT_DIMENSION, language)


def score_speech_anxiety_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_speech_anxiety_short_items(), responses)
