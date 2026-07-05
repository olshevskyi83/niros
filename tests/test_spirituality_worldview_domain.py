"""Tests for Spirituality / Worldview fingerprint domain."""

from __future__ import annotations

import io

from niros.assessment import AssessmentResult
from niros.assessment_runner import (
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
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.icaros_readiness import (
    IcarosReadinessEvaluator,
    SPIRITUAL_ORIENTATION_ATHEIST,
    SPIRITUAL_ORIENTATION_CHRISTIAN,
    SPIRITUAL_ORIENTATION_RELIGION_AVERSE,
)
from niros.intervention_strategy import build_intervention_strategy
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint, render_scenario_blueprint
from niros.spirituality_worldview import (
    COMFORT_AVOID,
    ORIENTATION_AGNOSTIC,
    ORIENTATION_ATHEIST,
    ORIENTATION_CHRISTIAN,
    ORIENTATION_NATURE_SPIRITUAL,
    ORIENTATION_RELIGION_AVERSE,
    ORIENTATION_SECULAR_HUMANIST,
    ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
    ORIENTATION_SYMBOLIC_OPEN,
    ORIENTATION_SKEPTICAL_OPEN,
    ORIENTATION_UNKNOWN,
    SPIRITUALITY_WORLDVIEW_DOMAIN,
    build_spirituality_worldview_profile,
    extract_worldview_signals_from_text,
    worldview_coverage_value,
)
from niros.adaptive_assessment_selector import select_assessment_modules


def _tag(canonical_id: str, matched_text: str) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-swv",
        evidence_id="session-swv:evidence:0",
        canonical_id=canonical_id,
        matched_text=matched_text,
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _profile_from_text(text: str):
    return build_spirituality_worldview_profile(
        presenting_problem={"main_problem": text},
        matched_texts=[text],
    )


def test_atheist_input_detected():
    profile = _profile_from_text("I do not believe in God.")
    assert profile.worldview_orientation == ORIENTATION_ATHEIST
    assert profile.religious_language_comfort == COMFORT_AVOID


def test_agnostic_input_detected():
    profile = _profile_from_text("I do not know what I believe.")
    assert profile.worldview_orientation == ORIENTATION_AGNOSTIC


def test_spiritual_not_religious_detected():
    profile = _profile_from_text(
        "I am not religious, but I feel connected to something bigger."
    )
    assert profile.worldview_orientation == ORIENTATION_SPIRITUAL_NOT_RELIGIOUS


def test_christian_input_detected():
    profile = _profile_from_text(
        "I believe in God, Jesus, and the Holy Trinity. My Christian faith is important to me."
    )
    assert profile.worldview_orientation == ORIENTATION_CHRISTIAN


def test_nature_spiritual_detected():
    profile = _profile_from_text(
        "I feel connected through nature, forests, rivers, mountains, plants."
    )
    assert profile.worldview_orientation == ORIENTATION_NATURE_SPIRITUAL
    assert "nature" in profile.symbolic_language_preferences


def test_religion_averse_detected():
    profile = _profile_from_text(
        "Religious language makes me uncomfortable. I do not want prayer or God language."
    )
    assert profile.worldview_orientation == ORIENTATION_RELIGION_AVERSE
    assert profile.religious_language_comfort == COMFORT_AVOID


def test_symbolic_openness_detected():
    profile = _profile_from_text(
        "I do not literally believe in spirits, but symbols and myths can move me."
    )
    assert profile.worldview_orientation == ORIENTATION_SYMBOLIC_OPEN


def test_skeptical_but_open_detected():
    profile = _profile_from_text(
        "I am skeptical, but I am open to symbolic or poetic language."
    )
    assert profile.worldview_orientation == ORIENTATION_SKEPTICAL_OPEN


def test_secular_humanist_detected():
    profile = _profile_from_text("I prefer secular, psychological language.")
    assert profile.worldview_orientation == ORIENTATION_SECULAR_HUMANIST


def test_coverage_levels():
    unknown = build_spirituality_worldview_profile()
    assert unknown.coverage_level() == COVERAGE_LEVEL_UNKNOWN
    assert worldview_coverage_value(unknown) < 0.25

    partial = _profile_from_text("I am not sure about spirituality.")
    assert partial.coverage_level() in {COVERAGE_LEVEL_PARTIAL, COVERAGE_LEVEL_GOOD}

    good = _profile_from_text("I do not believe in God.")
    assert good.coverage_level() in {COVERAGE_LEVEL_GOOD, COVERAGE_LEVEL_COMPLETE}

    complete = build_spirituality_worldview_profile(
        presenting_problem={
            "main_problem": (
                "Religious language makes me uncomfortable. "
                "I prefer nature, breath, and light imagery."
            )
        },
        matched_texts=[
            "Religious language makes me uncomfortable. "
            "I prefer nature, breath, and light imagery."
        ],
    )
    assert complete.coverage_level() == COVERAGE_LEVEL_COMPLETE


def test_missing_domain_when_worldview_unknown():
    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "work stress"},
        patterns=[_tag("rumination", "I keep replaying work mistakes.")],
    )
    assert SPIRITUALITY_WORLDVIEW_DOMAIN in report.missing_domains


def test_assessment_selection_includes_worldview_when_missing():
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "spiritual life feels unresolved"},
        detected_patterns=[_tag("rumination", "I keep replaying work mistakes.")],
    )
    assert SPIRITUALITY_WORLDVIEW_DOMAIN in selection.coverage_report.missing_domains
    assert "spirituality-worldview-short" in selection.selected_modules


def test_human_profile_includes_worldview_domain():
    report = build_human_profile_report_from_tags(
        [_tag("rumination", "My mind loops on mistakes.")],
        presenting_problem={"main_problem": "I do not believe in God."},
    )
    rendered = render_human_profile_report(report)

    assert report.spirituality_worldview is not None
    assert report.spirituality_worldview.worldview_orientation == ORIENTATION_ATHEIST
    assert "Spirituality / Worldview" in rendered
    assert "Worldview orientation: atheist" in rendered


def test_human_digital_fingerprint_embeds_worldview():
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[_tag("meaning_seeking", "I am an atheist.")],
        presenting_problem={"main_problem": "I am an atheist."},
    )
    assert "spirituality_worldview" in fingerprint
    assert fingerprint["spirituality_worldview"]["worldview_orientation"] == ORIENTATION_ATHEIST


def test_extract_worldview_signals_from_text_is_deterministic():
    text = "I am skeptical, but I am open to symbolic or poetic language."
    first = extract_worldview_signals_from_text(text)
    second = extract_worldview_signals_from_text(text)
    assert [(f.category, f.attribute, f.value) for f in first] == [
        (f.category, f.attribute, f.value) for f in second
    ]


def _readiness_context(text: str, *, pattern_ids: list[str] | None = None):
    patterns = pattern_ids or ["shame_sensitivity"]
    tags = [_tag(pid, text) for pid in patterns]
    completed = {
        "big-five-short": run_big_five_short_assessment(
            language="en",
            output_stream=io.StringIO(),
            answers=neutral_answers_for_module("big-five-short"),
            print_output=False,
        )
    }
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": text},
        patterns=tags,
        completed_assessments=completed,
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=tags,
        presenting_problem={"main_problem": text},
        assessment_results=[
            result for module_results in completed.values() for result in module_results
        ],
    )
    strategy = build_intervention_strategy(fingerprint, fingerprint_coverage_report=coverage)
    blueprint = build_scenario_blueprint(fingerprint["patterns"], intervention_strategy=strategy)
    return fingerprint, coverage, strategy, blueprint, completed


def test_icaros_readiness_warns_when_worldview_unknown():
    fingerprint, coverage, strategy, blueprint, completed = _readiness_context(
        "I feel ashamed and disconnected.",
        pattern_ids=["shame_sensitivity"],
    )
    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    assert "spiritual_orientation" in result.missing_information
    assert any(
        "Spiritual / worldview orientation is unknown" in warning
        for warning in result.warnings
    )


def test_icaros_readiness_adapts_for_atheist():
    text = "I do not believe in God. I prefer secular, psychological language."
    fingerprint, coverage, strategy, blueprint, completed = _readiness_context(
        text,
        pattern_ids=["meaning_seeking"],
    )
    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    assert result.spiritual_orientation == SPIRITUAL_ORIENTATION_ATHEIST
    assert result.recommended_symbolic_style["religious"] == "avoid"


def test_icaros_readiness_adapts_for_christian():
    text = "I believe in God, Jesus, and the Holy Trinity."
    fingerprint, coverage, strategy, blueprint, completed = _readiness_context(
        text,
        pattern_ids=["spiritual_openness"],
    )
    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    assert result.spiritual_orientation == SPIRITUAL_ORIENTATION_CHRISTIAN
    assert result.recommended_symbolic_style["religious"] == "preferred"


def test_icaros_readiness_adapts_for_religion_averse():
    text = "Religious language makes me uncomfortable. I do not want prayer or God language."
    fingerprint, coverage, strategy, blueprint, completed = _readiness_context(
        text,
        pattern_ids=["spiritual_resistance"],
    )
    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    assert result.spiritual_orientation == SPIRITUAL_ORIENTATION_RELIGION_AVERSE
    assert result.recommended_symbolic_style["religious"] == "avoid"


def test_strategy_and_scenario_include_worldview_notes():
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[_tag("spiritual_resistance", "No God language for me.")],
        presenting_problem={
            "main_problem": "Religious language makes me uncomfortable."
        },
    )
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "Religious language makes me uncomfortable."},
        patterns=[_tag("spiritual_resistance", "No God language for me.")],
    )
    strategy = build_intervention_strategy(fingerprint, fingerprint_coverage_report=coverage)
    blueprint = build_scenario_blueprint(fingerprint["patterns"], intervention_strategy=strategy)
    strategy_text = "\n".join(strategy.strategy_notes)
    scenario_text = render_scenario_blueprint(blueprint)

    assert "Avoided symbolic language" in strategy_text or "Worldview framing" in strategy_text
    assert "spirituality / worldview" in scenario_text.lower() or "symbolic framing" in scenario_text.lower()


def test_no_forced_religion_or_secularism():
    atheist = _profile_from_text("I do not believe in God.")
    christian = _profile_from_text("My Christian faith is important to me.")
    unknown = build_spirituality_worldview_profile()

    assert atheist.worldview_orientation != ORIENTATION_CHRISTIAN
    assert christian.worldview_orientation != ORIENTATION_ATHEIST
    assert unknown.worldview_orientation == ORIENTATION_UNKNOWN


def test_spirituality_worldview_short_module_scores():
    from niros.assessments.spirituality_worldview_short import (
        get_spirituality_worldview_short_items,
        score_spirituality_worldview_short,
    )
    from niros.assessment import AssessmentResponse

    items = get_spirituality_worldview_short_items("en")
    assert len(items) == 7
    responses = [
        AssessmentResponse(item_id=item.id, value=4) for item in items
    ]
    results = score_spirituality_worldview_short(responses)
    assert results
    assert all(result.fingerprint_dimension == SPIRITUALITY_WORLDVIEW_DOMAIN for result in results)
