import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from demo_interview import run_interview_session
from niros.assessment import interpretation_is_neutral
from niros.assessment_runner import (
    ASSESSMENT_ADAPTIVE,
    ASSESSMENT_BIG_FIVE_SHORT,
    ASSESSMENT_NONE,
    BIG_FIVE_SHORT_SECTION_TITLE,
    format_assessment_signal,
    neutral_answers_for_module,
    run_big_five_short_assessment,
)
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.human_profile_report import build_human_profile_report_from_tags
from niros.intervention_strategy import LEVEL_RANK, build_intervention_strategy
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from run_niros import parse_args, run_niros
from tests.intake_test_helpers import DEFAULT_TEST_INTAKE_INPUTS


def _neutral_big_five_short_answers() -> dict[str, int]:
    return neutral_answers_for_module("big-five-short")


def _high_neuroticism_big_five_short_answers() -> dict[str, int]:
    from niros.assessments.registry import get_assessment_module_items

    answers = _neutral_big_five_short_answers()
    for item in get_assessment_module_items("big-five-short"):
        if item.domain_id != "neuroticism":
            continue
        answers[item.id] = 1 if item.reverse_scored else 5
    return answers


def _pattern_tag(canonical_id: str) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-assessment-001",
        evidence_id="session-assessment-001:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def test_default_assessment_is_none():
    args = parse_args([])

    assert args.assessment == ASSESSMENT_NONE


def test_big_five_short_flag_exists():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--assessment",
        choices=[ASSESSMENT_NONE, ASSESSMENT_BIG_FIVE_SHORT, ASSESSMENT_ADAPTIVE],
        default=ASSESSMENT_NONE,
    )
    args = parser.parse_args(["--assessment", ASSESSMENT_BIG_FIVE_SHORT])

    assert args.assessment == ASSESSMENT_BIG_FIVE_SHORT


def test_questionnaire_accepts_fake_answers():
    answers = _neutral_big_five_short_answers()
    output = io.StringIO()

    results = run_big_five_short_assessment(
        language="en",
        output_stream=output,
        answers=answers,
        print_output=True,
    )

    assert len(results) == 5
    assert BIG_FIVE_SHORT_SECTION_TITLE in output.getvalue()
    assert "1 = strongly disagree" in output.getvalue()
    assert "5 = strongly agree" in output.getvalue()


def test_assessment_results_appear_in_profile_report():
    results = run_big_five_short_assessment(
        language="en",
        output_stream=io.StringIO(),
        answers=_neutral_big_five_short_answers(),
        print_output=False,
    )
    report = build_human_profile_report_from_tags(
        [_pattern_tag("rumination")],
        assessment_results=results,
    )

    assert report.assessment_signals
    assert any("self-reported tendency" in signal for signal in report.assessment_signals)
    assert any("neuroticism" in signal for signal in report.assessment_signals)


def test_assessment_results_appear_in_fingerprint_summary():
    results = run_big_five_short_assessment(
        language="en",
        output_stream=io.StringIO(),
        answers=_neutral_big_five_short_answers(),
        print_output=False,
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[_pattern_tag("rumination")],
        assessment_results=results,
    )

    assert fingerprint["assessment_results"]
    assert "Structured assessment signals" in fingerprint["summary_text"]
    assert "self-reported tendency" in fingerprint["summary_text"]


def test_elevated_neuroticism_influences_strategy_safely():
    results = run_big_five_short_assessment(
        language="en",
        output_stream=io.StringIO(),
        answers=_high_neuroticism_big_five_short_answers(),
        print_output=False,
    )
    neuroticism = next(result for result in results if result.domain_id == "neuroticism")
    assert neuroticism.interpretation == "elevated"

    baseline = build_intervention_strategy(
        build_human_digital_fingerprint(detected_patterns=[_pattern_tag("rumination")])
    )
    adjusted = build_intervention_strategy(
        build_human_digital_fingerprint(
            detected_patterns=[_pattern_tag("rumination")],
            assessment_results=results,
        )
    )

    assert LEVEL_RANK[adjusted.grounding_priority] > LEVEL_RANK[baseline.grounding_priority]
    assert adjusted.cognitive_load == "low"
    assert adjusted.emotional_intensity != "high"


def test_assessment_output_avoids_diagnostic_wording():
    results = run_big_five_short_assessment(
        language="en",
        output_stream=io.StringIO(),
        answers=_neutral_big_five_short_answers(),
        print_output=False,
    )

    for result in results:
        assert interpretation_is_neutral(result.interpretation)
        signal = format_assessment_signal(result).lower()
        assert "diagnosis" not in signal
        assert "disorder" not in signal
        assert "clinical" not in signal


def test_existing_runner_still_works_without_assessment():
    output = io.StringIO()

    exit_code = run_niros(
        user_inputs=["I worry people will stop liking me."],
        intake_inputs=DEFAULT_TEST_INTAKE_INPUTS,
        turns=1,
        provider="mock",
        assessment=ASSESSMENT_NONE,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert BIG_FIVE_SHORT_SECTION_TITLE not in rendered
    assert "Structured Assessment Signals" not in rendered


def test_runner_big_five_short_integration():
    output = io.StringIO()

    exit_code = run_niros(
        user_inputs=["I worry people will stop liking me."],
        intake_inputs=DEFAULT_TEST_INTAKE_INPUTS,
        turns=1,
        provider="mock",
        assessment=ASSESSMENT_BIG_FIVE_SHORT,
        big_five_short_answers=_neutral_big_five_short_answers(),
        output_stream=output,
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert BIG_FIVE_SHORT_SECTION_TITLE in rendered
    assert "Structured Assessment Signals" in rendered
    assert rendered.index(BIG_FIVE_SHORT_SECTION_TITLE) < rendered.index("Adaptive Interview")


def test_interview_session_runs_assessment_before_adaptive():
    output = io.StringIO()

    session = run_interview_session(
        user_inputs=["I worry people will stop liking me."],
        intake_inputs=DEFAULT_TEST_INTAKE_INPUTS,
        turns=1,
        provider="mock",
        assessment=ASSESSMENT_BIG_FIVE_SHORT,
        big_five_short_answers=_neutral_big_five_short_answers(),
        stream=output,
        print_output=True,
    )

    rendered = output.getvalue()
    assert len(session.assessment_results) == 5
    assert rendered.index(BIG_FIVE_SHORT_SECTION_TITLE) < rendered.index("Adaptive Interview")
