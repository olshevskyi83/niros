"""Tests for human-readable UI helpers."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    RECOMMENDED,
    USE_WITH_CAUTION,
    PersonFitProfile,
    PatternFitScore,
)
from niros.strategy_candidate_builder import StrategyCandidate
from niros.ui_human_readable import (
    LANG_EN,
    LANG_ES,
    LANG_UK,
    SUPPORTED_LANGUAGES,
    UI_LANGUAGE_OPTIONS,
    build_human_caution_reason,
    build_human_pattern_reason,
    build_human_session_summary,
    humanize_signal,
    normalize_language,
)


def _shame_profile() -> PersonFitProfile:
    return PersonFitProfile(
        profile_id="ui_demo_shame_profile",
        active_signals=(
            "shame_sensitivity",
            "harsh_self_criticism",
            "emotional_avoidance",
        ),
        dominant_domains=("self", "emotion_regulation"),
        risk_signals=("overwhelm_risk",),
        needs=("self_compassion", "emotional_tolerance"),
    )


def _shame_strategy() -> StrategyCandidate:
    return StrategyCandidate(
        profile_id="ui_demo_shame_profile",
        selected_patterns=(
            PatternFitScore(
                pattern_id="pattern_self_compassion",
                canonical_name="self compassion for shame",
                fit_score=0.98,
                confidence=0.90,
                matched_signals=("shame_sensitivity", "harsh_self_criticism"),
                recommendation_status=RECOMMENDED,
            ),
            PatternFitScore(
                pattern_id="pattern_acceptance",
                canonical_name="acceptance of difficult emotions",
                fit_score=0.98,
                confidence=0.85,
                matched_signals=("emotional_avoidance",),
                matched_needs=("emotional_tolerance",),
                recommendation_status=RECOMMENDED,
            ),
        ),
        caution_patterns=(
            PatternFitScore(
                pattern_id="pattern_deep_exposure",
                canonical_name="deep emotional exposure",
                fit_score=0.72,
                confidence=0.90,
                matched_signals=("emotional_avoidance",),
                contraindication_hits=("overwhelm_risk",),
                recommendation_status=USE_WITH_CAUTION,
            ),
        ),
    )


def test_signal_label_english() -> None:
    assert humanize_signal("shame_sensitivity", LANG_EN) == "Shame sensitivity"
    assert humanize_signal("self_compassion", LANG_EN) == "Self-compassion"


def test_signal_label_spanish() -> None:
    assert humanize_signal("harsh_self_criticism", LANG_ES) == "Autocrítica severa"
    assert humanize_signal("emotional_tolerance", LANG_ES) == "Tolerancia emocional"


def test_signal_label_ukrainian() -> None:
    assert humanize_signal("emotional_avoidance", LANG_UK) == "Уникання емоцій"
    assert humanize_signal("overwhelm_risk", LANG_UK) == "Ризик перевантаження"


def test_unknown_signal_falls_back_safely() -> None:
    assert humanize_signal("unknown_custom_signal", LANG_EN) == "Unknown Custom Signal"
    assert humanize_signal("unknown_custom_signal", "fr") == "Unknown Custom Signal"


def test_human_summary_deterministic() -> None:
    profile = _shame_profile()
    strategy = _shame_strategy()
    first = build_human_session_summary(profile, strategy, LANG_EN)
    second = build_human_session_summary(profile, strategy, LANG_EN)
    assert first == second
    assert "shame, self-criticism, and emotional avoidance" in first


def test_human_summary_spanish_and_ukrainian() -> None:
    profile = _shame_profile()
    strategy = _shame_strategy()
    spanish = build_human_session_summary(profile, strategy, LANG_ES)
    ukrainian = build_human_session_summary(profile, strategy, LANG_UK)
    assert "vergüenza, autocrítica y evitación emocional" in spanish
    assert "сором, самокритика та уникання емоцій" in ukrainian


def test_pattern_reason_deterministic() -> None:
    score = _shame_strategy().selected_patterns[0]
    first = build_human_pattern_reason(score, LANG_EN)
    second = build_human_pattern_reason(score, LANG_EN)
    assert first == second
    assert first == "Matches shame sensitivity and harsh self-criticism."


def test_pattern_reason_spanish() -> None:
    score = _shame_strategy().selected_patterns[1]
    reason = build_human_pattern_reason(score, LANG_ES)
    assert "evitación emocional" in reason
    assert "tolerancia emocional" in reason


def test_caution_reason_deterministic() -> None:
    score = _shame_strategy().caution_patterns[0]
    first = build_human_caution_reason(score, LANG_EN)
    second = build_human_caution_reason(score, LANG_EN)
    assert first == second
    assert "overwhelm risk" in first


def test_language_selector_values_supported() -> None:
    option_codes = {code for _, code in UI_LANGUAGE_OPTIONS}
    assert option_codes == set(SUPPORTED_LANGUAGES)
    assert normalize_language("unknown") == LANG_EN
    assert normalize_language(LANG_UK) == LANG_UK
