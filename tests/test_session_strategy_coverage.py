import re

from niros.assessment import AssessmentResult
from niros.assessment_runner import (
    AssessedModuleRun,
    neutral_answers_for_module,
    run_big_five_short_assessment,
)
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_GOOD,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageAnalyzer,
)
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    STRATEGY_CONFIDENCE_MEDIUM,
    build_intervention_strategy,
    coverage_level_to_strategy_confidence,
    render_intervention_strategy,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(is|e|ed|ing)?|disorder|patholog|clinical syndrome|bipolar|"
    r"ptsd|narcissistic personality|borderline personality)\b",
    re.IGNORECASE,
)


def _pattern_tag(canonical_id: str) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-strategy-coverage",
        evidence_id="session-strategy-coverage:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _full_intake() -> dict[str, str]:
    return {
        "main_problem": "feeling disconnected after loss",
        "duration": "months",
        "perceived_causes": "grief",
        "current_impact": "withdrawal",
        "previous_attempts": "talking with friends",
        "desired_outcome": "feel more like myself",
    }


def _coverage_report(**kwargs):
    return FingerprintCoverageAnalyzer().analyze(
        presenting_problem=_full_intake(),
        patterns=[_pattern_tag("social_withdrawal")],
        **kwargs,
    )


def _fingerprint_with_patterns(pattern_ids: list[str]) -> dict:
    return build_human_digital_fingerprint(
        detected_patterns=[_pattern_tag(pattern_id) for pattern_id in pattern_ids],
        presenting_problem=_full_intake(),
    )


def test_strategy_receives_coverage_result():
    coverage = _coverage_report()
    strategy = build_intervention_strategy(
        _fingerprint_with_patterns(["social_withdrawal"]),
        fingerprint_coverage_report=coverage,
    )

    assert strategy.coverage_summary is not None
    assert strategy.focus_confidence
    assert any(item.focus_area == "emotion regulation" for item in strategy.focus_confidence)


def test_high_coverage_domains_produce_high_confidence():
    big_five_results = run_big_five_short_assessment(
        language="en",
        output_stream=__import__("io").StringIO(),
        answers=neutral_answers_for_module("big-five-short"),
        print_output=False,
    )
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem=_full_intake(),
        patterns=[_pattern_tag("social_withdrawal")],
        completed_assessments={"big-five-short": big_five_results},
    )
    strategy = build_intervention_strategy(
        _fingerprint_with_patterns(["social_withdrawal"]),
        fingerprint_coverage_report=coverage,
    )

    assert strategy.coverage_summary is not None
    assert "Presenting Problem" in strategy.coverage_summary.high_confidence
    assert "Big Five" in strategy.coverage_summary.high_confidence

    personality_focus = next(
        item for item in strategy.focus_confidence if item.focus_area == "personality / pacing"
    )
    assert personality_focus.confidence == STRATEGY_CONFIDENCE_HIGH


def test_partial_domains_produce_medium_confidence():
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "I feel useless"},
        patterns=[_pattern_tag("shame_sensitivity"), _pattern_tag("social_withdrawal")],
        semantic_facts=[
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="useless",
            ),
            SemanticFact(
                category="self",
                attribute="self_criticism",
                value="present",
                evidence="harsh",
            ),
        ],
    )
    strategy = build_intervention_strategy(
        _fingerprint_with_patterns(["shame_sensitivity", "social_withdrawal"]),
        fingerprint_coverage_report=coverage,
    )

    assert coverage.domains["self_domain"].level == COVERAGE_LEVEL_PARTIAL
    assert strategy.coverage_summary is not None
    assert "Self" in strategy.coverage_summary.medium_confidence


def test_unknown_domains_produce_low_exploratory_confidence():
    coverage = _coverage_report()
    strategy = build_intervention_strategy(
        _fingerprint_with_patterns(["social_withdrawal"]),
        fingerprint_coverage_report=coverage,
    )

    assert coverage.domains["emotion_regulation_domain"].level == COVERAGE_LEVEL_UNKNOWN
    emotion_focus = next(
        item for item in strategy.focus_confidence if item.focus_area == "emotion regulation"
    )
    assert emotion_focus.confidence == STRATEGY_CONFIDENCE_LOW
    assert strategy.coverage_summary is not None
    assert "Emotion Regulation" in strategy.coverage_summary.low_confidence


def test_uncertainty_notes_appear_for_weak_domains():
    coverage = _coverage_report()
    strategy = build_intervention_strategy(
        _fingerprint_with_patterns(["social_withdrawal"]),
        fingerprint_coverage_report=coverage,
    )
    rendered = render_intervention_strategy(strategy)

    assert "Strategy Confidence Summary" in rendered
    assert "Low confidence / exploratory:" in rendered
    assert "Emotion Regulation domain coverage is unknown" in rendered
    assert "Further clarification is recommended before strong self-focused framing" in rendered


def test_low_self_coverage_reduces_self_focus_and_adds_exploratory_notes():
    coverage = _coverage_report()
    from niros.intervention_strategy import LEVEL_RANK

    baseline = build_intervention_strategy(_fingerprint_with_patterns(["speech_anxiety"]))
    adjusted = build_intervention_strategy(
        _fingerprint_with_patterns(["speech_anxiety"]),
        fingerprint_coverage_report=coverage,
    )

    assert coverage.domains["self_domain"].level in {
        COVERAGE_LEVEL_UNKNOWN,
        COVERAGE_LEVEL_PARTIAL,
    }
    self_focus = next(
        item for item in adjusted.focus_confidence if item.focus_area == "self-worth / self-criticism"
    )
    assert self_focus.confidence in {STRATEGY_CONFIDENCE_LOW, STRATEGY_CONFIDENCE_MEDIUM}
    assert LEVEL_RANK[adjusted.self_focus] <= LEVEL_RANK[baseline.self_focus]


def test_low_emotion_regulation_coverage_increases_grounding_priority():
    coverage = _coverage_report()
    baseline = build_intervention_strategy(_fingerprint_with_patterns(["meaning_seeking"]))
    adjusted = build_intervention_strategy(
        _fingerprint_with_patterns(["meaning_seeking"]),
        fingerprint_coverage_report=coverage,
    )

    from niros.intervention_strategy import LEVEL_RANK

    assert LEVEL_RANK[adjusted.grounding_priority] >= LEVEL_RANK[baseline.grounding_priority]
    assert any(
        "Emotion Regulation coverage is limited" in note
        for note in adjusted.strategy_notes
    )


def test_rendered_strategy_avoids_diagnosis_language():
    coverage = _coverage_report()
    strategy = build_intervention_strategy(
        _fingerprint_with_patterns(["rumination", "shame_sensitivity"]),
        fingerprint_coverage_report=coverage,
    )
    rendered = render_intervention_strategy(strategy)

    assert DIAGNOSIS_PATTERN.search(rendered) is None
    assert "not diagnostic" not in rendered.lower()


def test_build_intervention_strategy_with_coverage_is_deterministic():
    coverage = _coverage_report()
    fingerprint = _fingerprint_with_patterns(["social_withdrawal"])

    first = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage,
    )
    second = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage,
    )

    assert first == second
    assert render_intervention_strategy(first) == render_intervention_strategy(second)


def test_existing_strategy_output_remains_backward_compatible():
    fingerprint = _fingerprint_with_patterns(["existential_fear"])
    baseline = build_intervention_strategy(fingerprint)
    rendered = render_intervention_strategy(baseline)

    assert baseline.coverage_summary is None
    assert baseline.focus_confidence == ()
    assert "=== NIROS Intervention Strategy ===" in rendered
    assert "Pacing:" in rendered
    assert "Grounding priority:" in rendered
    assert "Strategy Confidence Summary" not in rendered


def test_coverage_level_to_strategy_confidence_mapping():
    assert coverage_level_to_strategy_confidence(COVERAGE_LEVEL_COMPLETE) == STRATEGY_CONFIDENCE_HIGH
    assert coverage_level_to_strategy_confidence(COVERAGE_LEVEL_GOOD) == STRATEGY_CONFIDENCE_HIGH
    assert coverage_level_to_strategy_confidence(COVERAGE_LEVEL_PARTIAL) == STRATEGY_CONFIDENCE_MEDIUM
    assert coverage_level_to_strategy_confidence(COVERAGE_LEVEL_UNKNOWN) == STRATEGY_CONFIDENCE_LOW


def test_completed_big_five_adds_confident_personality_note():
    big_five_results = run_big_five_short_assessment(
        language="en",
        output_stream=__import__("io").StringIO(),
        answers=neutral_answers_for_module("big-five-short"),
        print_output=False,
    )
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem=_full_intake(),
        patterns=[_pattern_tag("rumination")],
        completed_assessments={"big-five-short": big_five_results},
    )
    strategy = build_intervention_strategy(
        build_human_digital_fingerprint(
            detected_patterns=[_pattern_tag("rumination")],
            presenting_problem=_full_intake(),
            assessment_results=big_five_results,
        ),
        fingerprint_coverage_report=coverage,
    )

    assert coverage.domains["big_five"].level in {COVERAGE_LEVEL_COMPLETE, COVERAGE_LEVEL_GOOD}
    assert any(
        "Big Five coverage is strong" in note
        for note in strategy.strategy_notes
    )
    personality_focus = next(
        item for item in strategy.focus_confidence if item.focus_area == "personality / pacing"
    )
    assert personality_focus.confidence == STRATEGY_CONFIDENCE_HIGH
