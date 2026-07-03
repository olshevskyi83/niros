import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from niros.adaptive_assessment_selector import SELF_DOMAIN_SHORT, SLEEP_SHORT, SUBSTANCE_USE_SHORT
from niros.assessment import interpretation_is_neutral
from niros.assessment_runner import (
    ADAPTIVE_ASSESSMENT_SELECTION_TITLE,
    ASSESSMENT_ADAPTIVE,
    ASSESSMENT_BIG_FIVE_SHORT,
    ASSESSMENT_NONE,
    BIG_FIVE_SHORT_SECTION_TITLE,
    MODULE_TITLES,
    format_assessment_signal,
    neutral_answers_for_module,
    run_adaptive_assessments,
)
from niros.assessments.registry import get_assessment_module_items
from demo_interview import run_interview_session
from run_niros import parse_args, run_niros
from tests.intake_test_helpers import DEFAULT_TEST_INTAKE_INPUTS


def _neutral_answers_for_modules(module_ids: list[str]) -> dict[str, dict[str, int]]:
    return {module_id: neutral_answers_for_module(module_id) for module_id in module_ids}


def _elevated_sleep_answers() -> dict[str, dict[str, int]]:
    answers = _neutral_answers_for_modules(["big-five-short", "sleep-short"])
    for item in get_assessment_module_items("sleep-short"):
        if item.domain_id == "insomnia":
            answers["sleep-short"][item.id] = 5
        if item.domain_id == "daytime_impact" and not item.reverse_scored:
            answers["sleep-short"][item.id] = 5
    return answers


DEPRESSION_INTAKE_ANSWERS = {
    "presenting_problem": "мені здається у мене депресія",
    "duration": "приблизно два роки",
    "perceived_causes": "наслідок автокатастрофи",
    "current_impact": "майже не сплю, їсти не хочеться",
    "previous_attempts": "пробував терапію",
    "desired_outcome": "хочу відновити сон",
}

SLEEP_INTAKE_ANSWERS = {
    "presenting_problem": "я майже не сплю",
    "duration": "кілька місяців",
    "perceived_causes": "стрес",
    "current_impact": "сон зовсім поганий, втома вдень",
    "previous_attempts": "нічого не допомогло",
    "desired_outcome": "нормальний сон",
}

SUBSTANCE_INTAKE_ANSWERS = {
    "presenting_problem": "не можу контролювати вживання речовини",
    "duration": "більше року",
    "perceived_causes": "стрес і звичка",
    "current_impact": "залежність від речовини, компульсивне вживання",
    "previous_attempts": "намагався припинити",
    "desired_outcome": "повернути контроль",
}


def test_parse_args_accepts_adaptive_assessment():
    args = parse_args(["--assessment", "adaptive"])

    assert args.assessment == ASSESSMENT_ADAPTIVE


def test_adaptive_assessment_selection_is_printed():
    output = io.StringIO()
    runs = run_adaptive_assessments(
        presenting_problem=DEPRESSION_INTAKE_ANSWERS,
        detected_patterns=["self_reported_depression_concern", "insomnia_signal"],
        language="uk",
        output_stream=output,
        answers_by_module=_neutral_answers_for_modules(["big-five-short", "self-domain-short"]),
        print_output=True,
    )

    rendered = output.getvalue()
    assert ADAPTIVE_ASSESSMENT_SELECTION_TITLE in rendered
    assert "Selected modules:" in rendered
    assert "big-five-short:" in rendered
    assert runs


def test_depression_intake_selects_big_five_and_self_domain():
    output = io.StringIO()

    run_niros(
        user_inputs=["більшість днів настрій низький"],
        intake_answers=DEPRESSION_INTAKE_ANSWERS,
        turns=1,
        provider="mock",
        language="uk",
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_neutral_answers_for_modules(
            ["big-five-short", "self-domain-short", "emotion-regulation-domain-short", "sleep-short"]
        ),
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "===== Fingerprint Coverage =====" in rendered
    assert ADAPTIVE_ASSESSMENT_SELECTION_TITLE in rendered
    assert "big-five-short" in rendered
    assert SELF_DOMAIN_SHORT in rendered
    assert BIG_FIVE_SHORT_SECTION_TITLE in rendered
    assert MODULE_TITLES[SELF_DOMAIN_SHORT] in rendered


def test_sleep_intake_selects_sleep_short():
    output = io.StringIO()

    run_niros(
        user_inputs=["майже не сплю вночі"],
        intake_answers=SLEEP_INTAKE_ANSWERS,
        turns=1,
        provider="mock",
        language="uk",
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_neutral_answers_for_modules(
            ["big-five-short", "sleep-short"]
        ),
        output_stream=output,
    )

    rendered = output.getvalue()
    assert SLEEP_SHORT in rendered
    assert MODULE_TITLES[SLEEP_SHORT] in rendered


def test_substance_intake_selects_substance_use_short():
    output = io.StringIO()

    run_niros(
        user_inputs=["вживання виходить з-під контролю"],
        intake_answers=SUBSTANCE_INTAKE_ANSWERS,
        turns=1,
        provider="mock",
        language="uk",
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_neutral_answers_for_modules(
            ["big-five-short", "substance-use-short"]
        ),
        output_stream=output,
    )

    rendered = output.getvalue()
    assert SUBSTANCE_USE_SHORT in rendered
    assert MODULE_TITLES[SUBSTANCE_USE_SHORT] in rendered


def test_selected_modules_run_with_fake_answers():
    output = io.StringIO()

    session = run_interview_session(
        user_inputs=["майже не сплю"],
        intake_answers=SLEEP_INTAKE_ANSWERS,
        turns=1,
        provider="mock",
        language="uk",
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_elevated_sleep_answers(),
        stream=output,
        print_output=True,
    )

    assert session.assessment_module_runs
    assert session.assessment_results
    assert any(run.module_id == "sleep-short" for run in session.assessment_module_runs)
    assert MODULE_TITLES["sleep-short"] in output.getvalue()


def test_assessment_results_grouped_in_report():
    output = io.StringIO()

    run_niros(
        user_inputs=["майже не сплю"],
        intake_answers=SLEEP_INTAKE_ANSWERS,
        turns=1,
        provider="mock",
        language="uk",
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_elevated_sleep_answers(),
        output_stream=output,
    )

    rendered = output.getvalue()
    assert "Structured Assessment Signals" in rendered
    assert f"{MODULE_TITLES['big-five-short']}:" in rendered
    assert f"{MODULE_TITLES['sleep-short']}:" in rendered
    assert "insomnia:" in rendered
    assert "self-reported signal" in rendered
    assert rendered.index(ADAPTIVE_ASSESSMENT_SELECTION_TITLE) < rendered.index("Adaptive Interview")


def test_assessment_none_still_works():
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
    assert ADAPTIVE_ASSESSMENT_SELECTION_TITLE not in rendered
    assert BIG_FIVE_SHORT_SECTION_TITLE not in rendered


def test_assessment_big_five_short_still_works():
    output = io.StringIO()
    big_five_answers = neutral_answers_for_module("big-five-short")

    exit_code = run_niros(
        user_inputs=["I worry people will stop liking me."],
        intake_inputs=DEFAULT_TEST_INTAKE_INPUTS,
        turns=1,
        provider="mock",
        assessment=ASSESSMENT_BIG_FIVE_SHORT,
        big_five_short_answers=big_five_answers,
        output_stream=output,
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert BIG_FIVE_SHORT_SECTION_TITLE in rendered
    assert "Structured Assessment Signals" in rendered
    assert rendered.index(BIG_FIVE_SHORT_SECTION_TITLE) < rendered.index("Adaptive Interview")


def test_adaptive_assessment_output_avoids_diagnostic_wording():
    runs = run_adaptive_assessments(
        presenting_problem=SLEEP_INTAKE_ANSWERS,
        detected_patterns=["sleep_disruption", "insomnia_signal"],
        language="uk",
        output_stream=io.StringIO(),
        answers_by_module=_elevated_sleep_answers(),
        print_output=False,
    )

    for run in runs:
        for result in run.results:
            assert interpretation_is_neutral(result.interpretation)
            signal = format_assessment_signal(result, module_id=run.module_id).lower()
            assert "diagnosis" not in signal
            assert "disorder" not in signal
            assert "clinical" not in signal
            assert "cure" not in signal
