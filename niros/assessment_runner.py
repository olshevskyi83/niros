from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO

from niros.adaptive_assessment_selector import (
    render_assessment_selection_with_coverage,
    select_assessment_modules,
)
from niros.assessment import AssessmentResponse, AssessmentResult, assessment_result_to_dict
from niros.assessment_domain_map import build_assessment_domain_map
from niros.assessments._common import SCALE_MAX, SCALE_MIN, item_text_for_language
from niros.assessments.big_five_short import (
    get_big_five_short_items,
    score_big_five_short,
)
from niros.assessments.registry import get_assessment_module_items, score_assessment_module
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact

ASSESSMENT_NONE = "none"
ASSESSMENT_BIG_FIVE_SHORT = "big-five-short"
ASSESSMENT_ADAPTIVE = "adaptive"
SUPPORTED_ASSESSMENTS = frozenset(
    {ASSESSMENT_NONE, ASSESSMENT_BIG_FIVE_SHORT, ASSESSMENT_ADAPTIVE}
)

BIG_FIVE_SHORT_SECTION_TITLE = "=== Big Five Short Assessment ==="
ADAPTIVE_ASSESSMENT_SELECTION_TITLE = "=== Adaptive Assessment Selection ==="

MODULE_TITLES: dict[str, str] = {
    "big-five-short": "Big Five Short",
    "low-mood-short": "Low Mood Short",
    "anxiety-short": "Anxiety Short",
    "sleep-short": "Sleep Short",
    "trauma-stress-short": "Trauma / Stress Short",
    "grief-loss-short": "Grief / Loss Short",
    "substance-use-short": "Substance Use Short",
    "behavioral-addiction-short": "Behavioral Addiction Short",
    "pain-fatigue-short": "Pain / Fatigue Short",
    "speech-anxiety-short": "Speech Anxiety Short",
    "psychedelic-concern-short": "Psychedelic Concern Short",
    "meaning-purpose-short": "Meaning / Purpose Short",
    "self-domain-short": "Self Domain Short",
    "emotion-regulation-domain-short": "Emotion Regulation Domain Short",
    "cognitive-patterns-domain-short": "Cognitive Patterns Domain Short",
    "relationships-domain-short": "Relationships Domain Short",
    "values-identity-domain-short": "Values / Identity Domain Short",
    "emotional-flexibility-domain-short": "Emotional Flexibility Domain Short",
}

SCALE_LABELS: dict[str, tuple[str, str]] = {
    "en": ("1 = strongly disagree", "5 = strongly agree"),
    "uk": ("1 = повністю не погоджуюсь", "5 = повністю погоджуюсь"),
    "ru": ("1 = полностью не согласен", "5 = полностью согласен"),
    "es": ("1 = totalmente en desacuerdo", "5 = totalmente de acuerdo"),
}


@dataclass(frozen=True)
class AssessedModuleRun:
    module_id: str
    results: list[AssessmentResult]


class AssessmentInputError(Exception):
    """Raised when structured assessment input cannot be read."""


def module_section_title(module_id: str) -> str:
    title = MODULE_TITLES.get(module_id, module_id)
    return f"=== {title} Assessment ==="


def format_assessment_signal(
    result: AssessmentResult | dict[str, str | float],
    *,
    module_id: str | None = None,
) -> str:
    if isinstance(result, AssessmentResult):
        trait = result.domain_id
        level = result.interpretation
    else:
        trait = str(result["domain_id"])
        level = str(result["interpretation"])

    label = "tendency" if module_id in {None, ASSESSMENT_BIG_FIVE_SHORT, "big-five-short"} else "signal"
    return f"{trait}: {level} self-reported {label}"


def render_adaptive_assessment_selection(
    selection,
    *,
    module_titles: dict[str, str] | None = None,
) -> str:
    return render_assessment_selection_with_coverage(
        selection,
        module_titles=module_titles or MODULE_TITLES,
    )


def print_adaptive_assessment_selection(selection, output_stream: TextIO) -> None:
    print(render_adaptive_assessment_selection(selection), file=output_stream)
    print(file=output_stream)


def run_assessment_module(
    module_id: str,
    *,
    language: str = "en",
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    answers: dict[str, int] | None = None,
    print_output: bool = True,
) -> list[AssessmentResult]:
    items = get_assessment_module_items(module_id, language)
    responses: list[AssessmentResponse] = []
    out = output_stream or sys.stdout

    if print_output:
        low_label, high_label = SCALE_LABELS.get(language, SCALE_LABELS["en"])
        print(module_section_title(module_id), file=out)
        print(f"{low_label}", file=out)
        print(f"{high_label}", file=out)
        print(file=out)

    interactive = answers is None
    if interactive:
        _ensure_readable_input_stream(input_stream or sys.stdin)

    for index, item in enumerate(items, start=1):
        question_text = item_text_for_language(item, language)
        if print_output:
            print(f"{index}. {question_text}", file=out)

        if answers is not None:
            if item.id not in answers:
                continue
            value = answers[item.id]
        else:
            value = _read_scale_response(
                input_stream or sys.stdin,
                out,
                index,
            )

        if print_output:
            print(str(value), file=out)

        responses.append(AssessmentResponse(item_id=item.id, value=value))

    return score_assessment_module(module_id, responses)


def run_big_five_short_assessment(
    *,
    language: str = "en",
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    answers: dict[str, int] | None = None,
    print_output: bool = True,
) -> list[AssessmentResult]:
    return run_assessment_module(
        ASSESSMENT_BIG_FIVE_SHORT,
        language=language,
        input_stream=input_stream,
        output_stream=output_stream,
        answers=answers,
        print_output=print_output,
    )


def completed_assessments_from_answers(
    answers_by_module: dict[str, dict[str, int]],
    *,
    language: str = "en",
) -> dict[str, list[AssessmentResult]]:
    completed: dict[str, list[AssessmentResult]] = {}
    for module_id, answers in answers_by_module.items():
        items = get_assessment_module_items(module_id, language)
        responses = [
            AssessmentResponse(item_id=item.id, value=answers[item.id])
            for item in items
            if item.id in answers
        ]
        if responses:
            completed[module_id] = score_assessment_module(module_id, responses)
    return completed


def run_adaptive_assessments(
    *,
    presenting_problem: dict[str, str],
    detected_patterns: list[str] | list[PatternTag],
    language: str = "en",
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    answers_by_module: dict[str, dict[str, int]] | None = None,
    semantic_facts: list[SemanticFact] | None = None,
    completed_assessments: dict[str, list[AssessmentResult]] | None = None,
    print_output: bool = True,
) -> list[AssessedModuleRun]:
    completed = dict(completed_assessments or {})
    selection = select_assessment_modules(
        presenting_problem=presenting_problem,
        detected_patterns=detected_patterns,
        assessment_domain_map=build_assessment_domain_map(),
        semantic_facts=semantic_facts,
        completed_assessments=completed,
    )

    if print_output:
        print_adaptive_assessment_selection(selection, output_stream or sys.stdout)

    runs: list[AssessedModuleRun] = [
        AssessedModuleRun(module_id=module_id, results=list(results))
        for module_id, results in sorted(completed.items())
    ]
    completed_ids = set(completed)

    for module_id in selection.selected_modules:
        if module_id in completed_ids:
            continue
        if print_output and runs:
            print(file=output_stream or sys.stdout)
        if answers_by_module is not None:
            module_answers = answers_by_module.get(module_id)
            if module_answers is None:
                module_answers = neutral_answers_for_module(module_id, language)
        else:
            module_answers = None
        results = run_assessment_module(
            module_id,
            language=language,
            input_stream=input_stream,
            output_stream=output_stream,
            answers=module_answers,
            print_output=print_output,
        )
        runs.append(AssessedModuleRun(module_id=module_id, results=results))

    return runs


def flatten_assessment_results(runs: list[AssessedModuleRun]) -> list[AssessmentResult]:
    results: list[AssessmentResult] = []
    for run in runs:
        results.extend(run.results)
    return results


def render_assessment_module_results(module_id: str, results: list[AssessmentResult]) -> str:
    title = module_section_title(module_id)
    lines = [title, ""]
    for result in sorted(results, key=lambda item: item.domain_id):
        lines.extend(
            [
                f"Domain: {result.domain_id}",
                f"Score: {result.score:.2f}",
                f"Level: {result.interpretation}",
                f"Fingerprint dimension: {result.fingerprint_dimension}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def render_assessed_module_runs(runs: list[AssessedModuleRun]) -> str:
    if not runs:
        return ""
    return "\n\n".join(
        render_assessment_module_results(run.module_id, run.results) for run in runs
    )


def neutral_answers_for_module(module_id: str, language: str = "en") -> dict[str, int]:
    items = get_assessment_module_items(module_id, language)
    return {item.id: 3 for item in items}


def _ensure_readable_input_stream(input_stream: TextIO) -> None:
    readable = getattr(input_stream, "readable", None)
    if callable(readable) and not readable():
        raise AssessmentInputError(
            "Assessment input stream is not readable. Use sys.stdin for CLI input."
        )


def _read_scale_response(input_stream: TextIO, output_stream: TextIO, index: int) -> int:
    _ensure_readable_input_stream(input_stream)

    while True:
        print(f"  Answer {index} ({SCALE_MIN}-{SCALE_MAX}): ", file=output_stream, end="")
        output_stream.flush()
        raw = input_stream.readline()
        if not raw:
            raise AssessmentInputError(
                "Assessment input ended before all questions were answered."
            )
        try:
            value = int(raw.strip())
        except ValueError:
            print(
                f"  Please enter a number from {SCALE_MIN} to {SCALE_MAX}.",
                file=output_stream,
            )
            continue
        if SCALE_MIN <= value <= SCALE_MAX:
            return value
        print(
            f"  Please enter a number from {SCALE_MIN} to {SCALE_MAX}.",
            file=output_stream,
        )


def serialize_assessment_results(results: list[AssessmentResult]) -> list[dict[str, str | float]]:
    return [assessment_result_to_dict(result) for result in results]
