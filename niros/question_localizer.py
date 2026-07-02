from __future__ import annotations

SUPPORTED_LANGUAGES = frozenset({"en", "uk", "ru", "es"})

QUESTION_TRANSLATIONS: dict[str, dict[str, str]] = {
    "Tell me a little about yourself.": {
        "uk": "Розкажіть трохи про себе.",
        "ru": "Расскажите немного о себе.",
        "es": "Cuéntame un poco sobre ti.",
    },
    "When do you feel most unclear about who you are?": {
        "uk": "Коли ви найбільше відчуваєте, що вам незрозуміло, хто ви?",
        "ru": "Когда вы сильнее всего чувствуете, что вам непонятно, кто вы?",
        "es": "¿Cuándo sientes más claramente que no sabes quién eres?",
    },
    "What makes you feel like you probably cannot do this?": {
        "uk": "Що саме змушує вас відчувати, що ви, ймовірно, не зможете це зробити?",
        "ru": "Что именно заставляет вас чувствовать, что вы, скорее всего, не сможете это сделать?",
        "es": "¿Qué te hace sentir que probablemente no podrás hacerlo?",
    },
    "Tell me what brought you here today.": {
        "uk": "Розкажіть, що привело вас сюди сьогодні.",
        "ru": "Расскажите, что привело вас сюда сегодня.",
        "es": "Cuéntame qué te trajo aquí hoy.",
    },
}


def localize_question(question: str, language: str = "en") -> str:
    trimmed = question.strip()
    if not trimmed:
        return ""

    if language == "en":
        return trimmed

    if language not in SUPPORTED_LANGUAGES:
        return trimmed

    translations = QUESTION_TRANSLATIONS.get(trimmed, {})
    return translations.get(language, trimmed)
