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
    FIRST_QUESTION,
    SEPARATOR,
    TurnRecord,
    extract_semantic_interpretation,
    format_hypothesis_line,
    format_pattern_lines,
    print_human_profile_report,
    print_human_profile_summary,
    print_interview_summary,
    read_answer,
    resolve_turn_inputs,
    run_pipeline,
    strongest_hypothesis,
)
from niros.human_profile_summary import build_human_profile_summary
from niros.interview_debug import print_turn_debug_pipeline
from niros.question_localizer import localize_question
from niros.env_loader import load_project_env
from niros.runtime_config import (
    RUNTIME_MODE_REAL,
    RUNTIME_MODE_TEST,
    build_runtime_settings,
    format_openai_startup_lines,
)
from niros.scenario_blueprint import build_scenario_blueprint
from niros.semantic_interpreter.factory import SUPPORTED_PROVIDERS
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline
from niros.statement_normalizer import normalize_user_input
from niros.voice_input import (
    INTERVIEW_INPUT_TEXT,
    INTERVIEW_INPUT_VOICE,
    VoiceInput,
    create_voice_input,
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


def print_scenario_blueprint_section(profile: dict, stream: TextIO) -> None:
    blueprint = build_scenario_blueprint(profile)

    print("Scenario Blueprint", file=stream)
    print(f"- Opening objective: {blueprint.opening_phase.objective}", file=stream)
    print(
        f"- Stabilization objective: {blueprint.stabilization_phase.objective}",
        file=stream,
    )
    print(f"- Exploration phases: {len(blueprint.exploration_phases)}", file=stream)
    for index, phase in enumerate(blueprint.exploration_phases, start=1):
        patterns = ", ".join(phase.target_patterns) if phase.target_patterns else "None"
        print(
            f"  - Exploration {index} ({patterns}): {phase.objective}",
            file=stream,
        )
    print(f"- Integration objective: {blueprint.integration_phase.objective}", file=stream)
    print(f"- Closing objective: {blueprint.closing_phase.objective}", file=stream)
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
    turns: int,
    mode: str,
    provider: str,
    language: str,
    stream: TextIO,
    debug: bool = False,
    input_mode: str = INTERVIEW_INPUT_TEXT,
    voice_input: VoiceInput | None = None,
    big_five_answers: dict[str, int] | None = None,
) -> list[TurnRecord]:
    effective_turns, planned_inputs = resolve_turn_inputs(user_input, user_inputs, turns)
    session_id = f"niros-session-{uuid.uuid4().hex[:8]}"
    history: list[TurnRecord] = []
    current_question = FIRST_QUESTION

    active_voice_input = voice_input
    fallback_message: str | None = None
    if active_voice_input is None and user_input is None and user_inputs is None:
        active_voice_input, fallback_message = create_voice_input(
            input_mode,
            stream=stream,
        )

    print("Interview", file=stream)
    if debug:
        print("Debug mode: enabled", file=stream)
    print_input_mode_banner(
        INTERVIEW_INPUT_TEXT if fallback_message else input_mode,
        stream,
        fallback_message=fallback_message,
    )

    if active_voice_input is not None:
        active_voice_input.start()

    try:
        for turn_index in range(1, effective_turns + 1):
            localized_question = localize_question(current_question, language)
            print(SEPARATOR, file=stream)
            print(f"Question {turn_index}:", file=stream)
            print(localized_question, file=stream)
            print(file=stream)

            raw_answer = read_answer(
                planned_inputs[turn_index - 1],
                turn_index,
                stream,
                voice_input=active_voice_input,
            )
            if active_voice_input is None or active_voice_input.name == "text":
                print(raw_answer, file=stream)

            semantic_result = None
            if debug or provider == "openai":
                semantic_result = extract_semantic_interpretation(raw_answer, provider)

            normalized_answer = normalize_user_input(raw_answer, mode=mode, provider=provider)
            print(SEPARATOR, file=stream)

            pattern_tags, hypotheses, next_question = run_pipeline(normalized_answer, session_id)

            if debug:
                cumulative_patterns = [
                    tag for turn in history for tag in turn.pattern_tags
                ] + pattern_tags
                print_turn_debug_pipeline(
                    stream,
                    raw_transcript=raw_answer,
                    semantic_result=semantic_result,
                    pattern_tags=pattern_tags,
                    cumulative_patterns=cumulative_patterns,
                    big_five_answers=big_five_answers,
                )

            print("Detected Patterns", file=stream)
            for line in format_pattern_lines(pattern_tags):
                print(line, file=stream)
            print(SEPARATOR, file=stream)

            print("Current Hypothesis", file=stream)
            print(format_hypothesis_line(strongest_hypothesis(hypotheses)), file=stream)
            print(SEPARATOR, file=stream)

            history.append(
                TurnRecord(
                    question=current_question,
                    localized_question=localized_question,
                    raw_answer=raw_answer,
                    normalized_answer=normalized_answer,
                    pattern_tags=pattern_tags,
                    hypotheses=hypotheses,
                    next_question=next_question,
                    semantic_result=semantic_result,
                )
            )

            if next_question:
                current_question = next_question
            elif turn_index < effective_turns:
                break
    finally:
        if active_voice_input is not None:
            active_voice_input.stop()

    return history


def build_profile_from_history(history: list[TurnRecord]) -> dict:
    detected_patterns = [tag for turn in history for tag in turn.pattern_tags]
    return build_human_profile_summary(detected_patterns)


def run_niros(
    user_input: str | None = None,
    *,
    user_inputs: list[str] | None = None,
    turns: int = DEFAULT_TURNS,
    mode: str | None = None,
    provider: str | None = None,
    language: str = DEFAULT_LANGUAGE,
    output_stream: TextIO | None = None,
    debug: bool = False,
    runtime_mode: str | None = None,
    input_mode: str = INTERVIEW_INPUT_TEXT,
    voice_input: VoiceInput | None = None,
    big_five_answers: dict[str, int] | None = None,
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

    history = run_interview(
        user_input=user_input,
        user_inputs=user_inputs,
        turns=turns,
        mode=runtime_settings.normalizer_mode,
        provider=runtime_settings.provider,
        language=language,
        stream=stream,
        debug=debug,
        input_mode=input_mode,
        voice_input=voice_input,
        big_five_answers=big_five_answers,
    )

    print_interview_summary(history, stream)
    print_human_profile_summary(history, stream)
    print_human_profile_report(history, stream)

    profile = build_profile_from_history(history)
    print_scenario_blueprint_section(profile, stream)
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
        default=DEFAULT_LANGUAGE,
        help="Output language for interview questions (default: en)",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=DEFAULT_TURNS,
        help="Number of interview turns (default: 3)",
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
    )


if __name__ == "__main__":
    raise SystemExit(main())
