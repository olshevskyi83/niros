#!/usr/bin/env python3
"""Unified NIROS console application for the complete MVP flow."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo_interview import (
    DEFAULT_TURNS,
    SEPARATOR,
    InterviewSession,
    TurnRecord,
    print_human_profile_report,
    print_human_profile_summary,
    print_interview_summary,
    run_interview_session,
)
from niros.assessment_runner import (
    ASSESSMENT_ADAPTIVE,
    ASSESSMENT_BIG_FIVE_SHORT,
    ASSESSMENT_NONE,
    render_assessed_module_runs,
)
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.human_profile_summary import build_human_profile_summary
from niros.env_loader import load_project_env
from niros.fingerprint_coverage import FingerprintCoverageAnalyzer, FingerprintCoverageReport
from niros.intervention_strategy import build_intervention_strategy, render_intervention_strategy
from niros.runtime_config import (
    RUNTIME_MODE_REAL,
    RUNTIME_MODE_TEST,
    build_runtime_settings,
    format_openai_startup_lines,
)
from niros.scenario_blueprint import build_scenario_blueprint, render_scenario_blueprint
from niros.semantic_interpreter.factory import SUPPORTED_PROVIDERS
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline
from niros.voice_input import (
    INTERVIEW_INPUT_TEXT,
    INTERVIEW_INPUT_VOICE,
    VoiceInput,
)

DEFAULT_LANGUAGE = "en"
WELCOME_BANNER = "\n".join(
    [
        "====================",
        "NIROS",
        "Human Understanding Engine",
        "====================",
    ]
)
COMPLETION_MESSAGE = "\n".join(
    [
        "NIROS session preparation completed.",
        "Ready for future Session Engine.",
    ]
)


def print_welcome(stream: TextIO) -> None:
    print(WELCOME_BANNER, file=stream)
    print(file=stream)


def print_runtime_banner(settings, stream: TextIO) -> None:
    print("Provider selection:", file=stream)
    print("- mock (TEST runtime)", file=stream)
    print("- openai (REAL runtime)", file=stream)
    print(f"Runtime mode: {settings.runtime_mode}", file=stream)
    print(f"Semantic provider: {settings.provider}", file=stream)
    for line in format_openai_startup_lines():
        print(line, file=stream)
    if settings.selection_message:
        print(settings.selection_message, file=stream)
    print(file=stream)


def print_scenario_blueprint_section(
    profile: dict,
    stream: TextIO,
    *,
    intervention_strategy=None,
) -> None:
    blueprint = build_scenario_blueprint(
        profile,
        intervention_strategy=intervention_strategy,
    )
    print(render_scenario_blueprint(blueprint), file=stream)
    print(SEPARATOR, file=stream)


def print_session_timeline_section(profile: dict, stream: TextIO) -> None:
    print("Session Timeline", file=stream)
    print(render_session_timeline(simulate_session(profile)), file=stream)
    print(SEPARATOR, file=stream)


def print_input_mode_banner(
    input_mode: str,
    stream: TextIO,
    *,
    fallback_message: str | None = None,
) -> None:
    print("Interview input:", file=stream)
    print(f"- {INTERVIEW_INPUT_TEXT} (typed answers)", file=stream)
    print(f"- {INTERVIEW_INPUT_VOICE} (microphone)", file=stream)
    print(f"Interview input: {input_mode}", file=stream)
    if fallback_message:
        print(fallback_message, file=stream)
        print(f"Interview input: {INTERVIEW_INPUT_TEXT}", file=stream)
    print(file=stream)


def run_interview(
    *,
    user_input: str | None,
    user_inputs: list[str] | None,
    intake_inputs: list[str] | None,
    intake_answers: dict[str, str] | None,
    turns: int,
    mode: str,
    provider: str,
    language: str | None,
    stream: TextIO,
    debug: bool = False,
    input_mode: str = INTERVIEW_INPUT_TEXT,
    voice_input: VoiceInput | None = None,
    big_five_answers: dict[str, int] | None = None,
    skip_intake: bool = False,
    assessment: str = ASSESSMENT_NONE,
    big_five_short_answers: dict[str, int] | None = None,
    adaptive_assessment_answers: dict[str, dict[str, int]] | None = None,
) -> InterviewSession:
    print("Interview", file=stream)
    if debug:
        print("Debug mode: enabled", file=stream)
    print_input_mode_banner(input_mode, stream)

    return run_interview_session(
        user_input=user_input,
        user_inputs=user_inputs,
        intake_inputs=intake_inputs,
        intake_answers=intake_answers,
        turns=turns,
        mode=mode,
        provider=provider,
        language=language,
        stream=stream,
        debug=debug,
        input_mode=input_mode,
        voice_input=voice_input,
        big_five_answers=big_five_answers,
        skip_intake=skip_intake,
        assessment=assessment,
        big_five_short_answers=big_five_short_answers,
        adaptive_assessment_answers=adaptive_assessment_answers,
        print_output=True,
    )


def build_profile_from_history(session: InterviewSession) -> dict:
    detected_patterns = session.cumulative_pattern_tags
    return build_human_profile_summary(detected_patterns)


def build_fingerprint_from_session(session: InterviewSession) -> dict:
    return build_human_digital_fingerprint(
        detected_patterns=session.cumulative_pattern_tags,
        presenting_problem=session.presenting_problem,
        assessment_results=session.assessment_results,
    )


def build_coverage_from_session(session: InterviewSession) -> FingerprintCoverageReport:
    completed = {
        run.module_id: list(run.results)
        for run in session.assessment_module_runs
    }
    semantic_facts = None
    if session.intake_result is not None:
        semantic_facts = session.intake_result.evidence_store.facts()
    return FingerprintCoverageAnalyzer().analyze(
        presenting_problem=session.presenting_problem,
        patterns=session.cumulative_pattern_tags,
        semantic_facts=semantic_facts,
        completed_assessments=completed,
    )


def print_intervention_strategy_section(
    fingerprint: dict,
    stream: TextIO,
    *,
    fingerprint_coverage_report: FingerprintCoverageReport | None = None,
) -> None:
    strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=fingerprint_coverage_report,
    )
    print(render_intervention_strategy(strategy), file=stream)
    print(SEPARATOR, file=stream)


def run_niros(
    user_input: str | None = None,
    *,
    user_inputs: list[str] | None = None,
    intake_inputs: list[str] | None = None,
    intake_answers: dict[str, str] | None = None,
    turns: int = DEFAULT_TURNS,
    mode: str | None = None,
    provider: str | None = None,
    language: str | None = None,
    output_stream: TextIO | None = None,
    debug: bool = False,
    runtime_mode: str | None = None,
    input_mode: str = INTERVIEW_INPUT_TEXT,
    voice_input: VoiceInput | None = None,
    big_five_answers: dict[str, int] | None = None,
    skip_intake: bool = False,
    assessment: str = ASSESSMENT_NONE,
    big_five_short_answers: dict[str, int] | None = None,
    adaptive_assessment_answers: dict[str, dict[str, int]] | None = None,
) -> int:
    stream = output_stream or sys.stdout
    runtime_settings = build_runtime_settings(
        explicit_provider=provider,
        explicit_runtime_mode=runtime_mode,
        explicit_normalizer_mode=mode,
    )

    if runtime_settings.provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported semantic interpreter provider: {runtime_settings.provider}")

    print_welcome(stream)
    print_runtime_banner(runtime_settings, stream)

    session = run_interview(
        user_input=user_input,
        user_inputs=user_inputs,
        intake_inputs=intake_inputs,
        intake_answers=intake_answers,
        turns=turns,
        mode=runtime_settings.normalizer_mode,
        provider=runtime_settings.provider,
        language=language,
        stream=stream,
        debug=debug,
        input_mode=input_mode,
        voice_input=voice_input,
        big_five_answers=big_five_answers,
        skip_intake=skip_intake,
        assessment=assessment,
        big_five_short_answers=big_five_short_answers,
        adaptive_assessment_answers=adaptive_assessment_answers,
    )

    print_interview_summary(session.history, stream)
    print_human_profile_summary(session.history, stream)

    fingerprint = build_fingerprint_from_session(session)
    coverage_report = build_coverage_from_session(session)
    semantic_facts = None
    if session.intake_result is not None:
        semantic_facts = session.intake_result.evidence_store.facts()
    print_human_profile_report(
        session.history,
        stream,
        presenting_problem=session.presenting_problem,
        assessment_results=session.assessment_results,
        assessment_module_runs=session.assessment_module_runs,
        semantic_facts=semantic_facts,
    )

    if session.assessment_module_runs and assessment == ASSESSMENT_BIG_FIVE_SHORT:
        rendered = render_assessed_module_runs(session.assessment_module_runs)
        if rendered:
            print(rendered, file=stream)
            print(SEPARATOR, file=stream)

    print_intervention_strategy_section(
        fingerprint,
        stream,
        fingerprint_coverage_report=coverage_report,
    )

    profile = build_profile_from_history(session)
    strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage_report,
    )
    print_scenario_blueprint_section(
        profile,
        stream,
        intervention_strategy=strategy,
    )
    print_session_timeline_section(profile, stream)

    print(COMPLETION_MESSAGE, file=stream)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified NIROS MVP console application")
    parser.add_argument(
        "--mode",
        choices=["passthrough", "mock_llm"],
        default=None,
        help="Statement normalizer mode (default depends on runtime mode)",
    )
    parser.add_argument(
        "--provider",
        choices=sorted(SUPPORTED_PROVIDERS),
        default=None,
        help="Semantic interpreter provider (default: openai when OPENAI_API_KEY is set, else mock)",
    )
    parser.add_argument(
        "--runtime",
        choices=[RUNTIME_MODE_TEST, RUNTIME_MODE_REAL],
        default=None,
        help="Runtime mode: test=mock, real=openai",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print raw transcript, semantic facts, patterns, and digital fingerprint each turn",
    )
    parser.add_argument(
        "--input",
        dest="input_mode",
        choices=[INTERVIEW_INPUT_TEXT, INTERVIEW_INPUT_VOICE],
        default=INTERVIEW_INPUT_TEXT,
        help="Interview input: text or voice (default: text)",
    )
    parser.add_argument(
        "--language",
        choices=["en", "uk", "ru", "es"],
        default=None,
        help="Override input language for pattern matching and questions (default: auto-detect)",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=DEFAULT_TURNS,
        help="Number of adaptive interview turns after intake (default: 3)",
    )
    parser.add_argument(
        "--assessment",
        choices=[ASSESSMENT_NONE, ASSESSMENT_BIG_FIVE_SHORT, ASSESSMENT_ADAPTIVE],
        default=ASSESSMENT_NONE,
        help="Optional structured assessment after intake (default: none)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_project_env()
    args = parse_args(argv)
    if args.turns < 1:
        print("Turn count must be at least 1.", file=sys.stderr)
        return 1
    return run_niros(
        mode=args.mode,
        provider=args.provider,
        language=args.language,
        turns=args.turns,
        debug=args.debug,
        runtime_mode=args.runtime,
        input_mode=args.input_mode,
        assessment=args.assessment,
    )


if __name__ == "__main__":
    raise SystemExit(main())
