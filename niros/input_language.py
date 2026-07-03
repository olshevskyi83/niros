from __future__ import annotations

import re

from niros.models import SupportedLanguage
from niros.semantic_interpreter.base import SemanticInterpretationResult

SUPPORTED_LANGUAGE_CODES = frozenset({"en", "uk", "ru", "es"})

LANGUAGE_ALIASES = {
    "ua": "uk",
    "ukr": "uk",
    "eng": "en",
    "en-us": "en",
    "en-gb": "en",
    "esp": "es",
    "spa": "es",
    "rus": "ru",
}


def normalize_language_code(code: str | None) -> str | None:
    if code is None or not code.strip():
        return None

    token = code.strip().lower().replace("_", "-")
    primary = token.split("-")[0]
    normalized = LANGUAGE_ALIASES.get(token, LANGUAGE_ALIASES.get(primary, primary))
    if normalized in SUPPORTED_LANGUAGE_CODES:
        return normalized
    return None


def to_supported_language(code: str | None) -> SupportedLanguage | None:
    normalized = normalize_language_code(code)
    if normalized is None:
        return None
    return SupportedLanguage(normalized)


_UKRAINIAN_MARKERS = re.compile(r"[іїєґ]", re.IGNORECASE)
_UKRAINIAN_WORDS = re.compile(
    r"\b(боюся|жити|мені|нічого|що|ці|погані|сни|сняться|моє|твоє|дуже|хочу|знайти)\b",
    re.IGNORECASE,
)
_RUSSIAN_WORDS = re.compile(
    r"\b(боюсь|жить|мне|что|этот|кошмар|плох|снятся|хочу)\b",
    re.IGNORECASE,
)
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_SPANISH_MARKERS = re.compile(r"[ñáéíóúü¿¡]", re.IGNORECASE)
_SPANISH_WORDS = re.compile(
    r"\b(miedo|tengo|soy|estoy|para|una|los|las|del|vida|sueño|pesadilla)\b",
    re.IGNORECASE,
)


def detect_language_from_text(text: str) -> SupportedLanguage | None:
    stripped = text.strip()
    if not stripped:
        return None

    if _UKRAINIAN_MARKERS.search(stripped):
        return SupportedLanguage.UKRAINIAN

    if _UKRAINIAN_WORDS.search(stripped):
        return SupportedLanguage.UKRAINIAN

    if _RUSSIAN_WORDS.search(stripped):
        return SupportedLanguage.RUSSIAN

    if _CYRILLIC.search(stripped):
        return SupportedLanguage.RUSSIAN

    if _SPANISH_MARKERS.search(stripped) or _SPANISH_WORDS.search(stripped):
        return SupportedLanguage.SPANISH

    return None


def resolve_input_language(
    *,
    raw_text: str,
    explicit_language: str | None = None,
    semantic_result: SemanticInterpretationResult | None = None,
) -> SupportedLanguage:
    explicit = to_supported_language(explicit_language)
    if explicit is not None:
        return explicit

    if semantic_result is not None and semantic_result.detected_language:
        from_semantic = to_supported_language(semantic_result.detected_language)
        if from_semantic is not None:
            return from_semantic

    detected = detect_language_from_text(raw_text)
    if detected is not None:
        return detected

    return SupportedLanguage.ENGLISH
