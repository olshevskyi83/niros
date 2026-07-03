import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from demo_interview import extract_semantic_interpretation, run_pipeline
from niros.input_language import (
    detect_language_from_text,
    normalize_language_code,
    resolve_input_language,
)
from niros.models import SupportedLanguage
from niros.semantic_interpreter.base import SemanticInterpretationResult


def _pattern_ids(
    raw_text: str,
    *,
    explicit_language: str | None = None,
    semantic_result: SemanticInterpretationResult | None = None,
) -> set[str]:
    pattern_tags, _, _ = run_pipeline(
        raw_text,
        "session-language-test",
        explicit_language=explicit_language,
        semantic_result=semantic_result,
    )
    return {tag.canonical_id for tag in pattern_tags}


def test_normalize_language_codes():
    assert normalize_language_code("uk") == "uk"
    assert normalize_language_code("UA") == "uk"
    assert normalize_language_code("en-US") == "en"
    assert normalize_language_code("es") == "es"
    assert normalize_language_code("ru") == "ru"
    assert normalize_language_code("de") is None


def test_detect_language_from_text():
    assert detect_language_from_text("я боюся жити") == SupportedLanguage.UKRAINIAN
    assert detect_language_from_text("я боюсь жить") == SupportedLanguage.RUSSIAN
    assert detect_language_from_text("tengo miedo de vivir") == SupportedLanguage.SPANISH
    assert detect_language_from_text("I'm afraid to live.") is None


def test_resolve_input_language_priority_explicit_over_semantic():
    semantic = SemanticInterpretationResult(
        raw_text="я боюся жити",
        canonical_statements=[],
        detected_language="uk",
    )

    resolved = resolve_input_language(
        raw_text="я боюся жити",
        explicit_language="en",
        semantic_result=semantic,
    )

    assert resolved == SupportedLanguage.ENGLISH


def test_resolve_input_language_uses_semantic_detected_language():
    semantic = SemanticInterpretationResult(
        raw_text="hello",
        canonical_statements=[],
        detected_language="uk",
    )

    resolved = resolve_input_language(
        raw_text="hello",
        semantic_result=semantic,
    )

    assert resolved == SupportedLanguage.UKRAINIAN


def test_resolve_input_language_falls_back_to_text_detector():
    resolved = resolve_input_language(raw_text="я боюся жити")

    assert resolved == SupportedLanguage.UKRAINIAN


def test_resolve_input_language_unknown_falls_back_to_en():
    resolved = resolve_input_language(
        raw_text="I like music.",
        explicit_language="de",
        semantic_result=SemanticInterpretationResult(
            raw_text="I like music.",
            canonical_statements=[],
            detected_language="de",
        ),
    )

    assert resolved == SupportedLanguage.ENGLISH


def test_ukrainian_input_uses_uk_typical_phrases():
    detected = _pattern_ids("я боюся жити")

    assert "existential_fear" in detected


def test_russian_input_uses_ru_typical_phrases():
    detected = _pattern_ids("я боюсь жить")

    assert "existential_fear" in detected


def test_spanish_input_uses_es_typical_phrases():
    detected = _pattern_ids("tengo miedo de vivir")

    assert "existential_fear" in detected


def test_english_fallback_uses_en_typical_phrases():
    detected = _pattern_ids("I'm afraid to live.")

    assert "existential_fear" in detected


def test_cli_language_override_wins_over_text_detection():
    detected = _pattern_ids("я боюся жити", explicit_language="en")

    assert "existential_fear" not in detected


def test_regression_ya_boyusya_zhyty():
    semantic = extract_semantic_interpretation("я боюся жити", provider="mock")
    pattern_tags, _, _ = run_pipeline(
        "я боюся жити",
        "session-regression-uk",
        semantic_result=semantic,
    )

    assert semantic.raw_text == "я боюся жити"
    assert semantic.detected_language == "uk"
    assert any(tag.canonical_id == "existential_fear" for tag in pattern_tags)
    assert all(tag.language == SupportedLanguage.UKRAINIAN for tag in pattern_tags)
