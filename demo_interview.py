#!/usr/bin/env python3
"""Interactive NIROS Human Understanding Engine MVP demo."""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass, field
from typing import TextIO

from niros.hypotheses import Hypothesis
from niros.human_profile_summary import build_human_profile_summary
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.intake_protocol import (
    DEFAULT_INTAKE_PROTOCOL,
    PRESENTING_PROBLEM_ID,
    build_presenting_problem,
    intake_state_from_answers,
)
from niros.evidence_store import EvidenceStore
from niros.intake_runner import (
    IntakeSessionResult,
    IntakeTurnRecord,
    intake_blocked_questions,
    process_intake_answer,
    run_adaptive_decision,
    select_adaptive_question,
)
from niros.knowledge import PatternLoader
from niros.patterns import PatternTag
from niros.question_localizer import localize_question
from niros.statement_normalizer import normalize_user_input
from niros.voice_input import (
    INTERVIEW_INPUT_TEXT,
    INTERVIEW_INPUT_VOICE,
    TextInput,
    VoiceInput,
    create_voice_input,
)
from niros.interview_debug import print_turn_debug_pipeline
from niros.env_loader import load_project_env
from niros.runtime_config import (
    RUNTIME_MODE_REAL,
    RUNTIME_MODE_TEST,
    build_runtime_settings,
    format_openai_startup_lines,
)
from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.factory import SUPPORTED_PROVIDERS, get_semantic_interpreter
from niros.assessment import AssessmentResult
from niros.assessment_runner import (
    ASSESSMENT_ADAPTIVE,
    ASSESSMENT_BIG_FIVE_SHORT,
    ASSESSMENT_NONE,
    AssessedModuleRun,
    flatten_assessment_results,
    run_adaptive_assessments,
    run_big_five_short_assessment,
)

FIRST_QUESTION = DEFAULT_INTAKE_PROTOCOL.question_text(PRESENTING_PROBLEM_ID, "en")
INTAKE_QUESTION_COUNT = len(DEFAULT_INTAKE_PROTOCOL.question_ids())
SEPARATOR = "⸻"
DEFAULT_NORMALIZER_MODE = "passthrough"
DEFAULT_SEMANTIC_PROVIDER = "mock"
DEFAULT_LANGUAGE = "en"
DEFAULT_TURNS = 3


@dataclass
class TurnRecord:
    question: str
    localized_question: str
    raw_answer: str
    normalized_answer: str
    pattern_tags: list[PatternTag] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    next_question: str | None = None
    semantic_result: SemanticInterpretationResult | None = None
    phase: str = "adaptive"


@dataclass
class InterviewSession:
    intake_result: IntakeSessionResult | None
    adaptive_history: list[TurnRecord] = field(default_factory=list)
    assessment_results: list[AssessmentResult] = field(default_factory=list)
    assessment_module_runs: list[AssessedModuleRun] = field(default_factory=list)

    @property
    def history(self) -> list[TurnRecord]:
        intake_turns = []
        if self.intake_result is not None:
            for turn in self.intake_result.turns:
                intake_turns.append(
                    TurnRecord(
                        question=turn.question,
                        localized_question=turn.question,
                        raw_answer=turn.raw_answer,
                        normalized_answer=turn.normalized_answer,
                        pattern_tags=turn.pattern_tags,
                        semantic_result=turn.semantic_result,
                        phase="intake",
                    )
                )
        return intake_turns + self.adaptive_history

    @property
    def presenting_problem(self) -> dict[str, str]:
        if self.intake_result is None:
            return {}
        return build_presenting_problem(self.intake_result.intake_state)

    @property
    def cumulative_pattern_tags(self) -> list[PatternTag]:
        tags: list[PatternTag] = []
        if self.intake_result is not None:
            tags.extend(self.intake_result.cumulative_pattern_tags)
        for turn in self.adaptive_history:
            tags.extend(turn.pattern_tags)
        return _merge_pattern_tags_by_id(tags)


def extract_semantic_interpretation(
    raw_text: str,
    provider: str,
) -> SemanticInterpretationResult:
    return get_semantic_interpreter(provider).interpret_result(raw_text)


def run_pipeline(
    raw_text: str,
    session_id: str,
    *,
    explicit_language: str | None = None,
    semantic_result: SemanticInterpretationResult | None = None,
    turn_count: int = 0,
    cumulative_pattern_tags: list[PatternTag] | None = None,
    answered_questions: list[str] | None = None,
    blocked_questions: list[str] | None = None,
) -> tuple[list[PatternTag], list[Hypothesis], str | None]:
    turn_pattern_tags, hypotheses, next_question, _all_tags = run_adaptive_decision(
        session_id=session_id,
        raw_text=raw_text,
        normalized_answer=raw_text,
        turn_count=turn_count,
        cumulative_pattern_tags=cumulative_pattern_tags or [],
        answered_questions=answered_questions or [],
        blocked_questions=blocked_questions or [],
        semantic_result=semantic_result,
        explicit_language=explicit_language,
    )
    return turn_pattern_tags, hypotheses, next_question


def _merge_pattern_tags_by_id(pattern_tags: list[PatternTag]) -> list[PatternTag]:
    best_by_id: dict[str, PatternTag] = {}
    for tag in pattern_tags:
        current = best_by_id.get(tag.canonical_id)
        if current is None or tag.confidence > current.confidence:
            best_by_id[tag.canonical_id] = tag
    return list(best_by_id.values())


def summarize_patterns(pattern_tags: list[PatternTag]) -> list[tuple[str, str, float]]:
    loader = PatternLoader()
    best_by_id: dict[str, tuple[str, float]] = {}

    for tag in pattern_tags:
        pattern = loader.load(tag.canonical_id)
        current = best_by_id.get(tag.canonical_id)
        if current is None or tag.confidence > current[1]:
            best_by_id[tag.canonical_id] = (pattern.name, tag.confidence)

    return [
        (canonical_id, name, confidence)
        for canonical_id, (name, confidence) in sorted(best_by_id.items())
    ]


def strongest_hypothesis(hypotheses: list[Hypothesis]) -> Hypothesis | None:
    if not hypotheses:
        return None
    return max(hypotheses, key=lambda hypothesis: hypothesis.confidence)


def format_pattern_lines(pattern_tags: list[PatternTag]) -> list[str]:
    summaries = summarize_patterns(pattern_tags)
    if not summaries:
        return ["None detected"]

    return [
        f"- {name} ({canonical_id}, confidence: {confidence:.2f})"
        for canonical_id, name, confidence in summaries
    ]


def format_hypothesis_line(hypothesis: Hypothesis | None) -> str:
    if hypothesis is None:
        return "None"
    return f"{hypothesis.canonical_id} (confidence: {hypothesis.confidence:.2f})"


def strongest_detected_pattern(
    history: list[TurnRecord],
) -> tuple[str, str, float, int] | None:
    if not history:
        return None

    loader = PatternLoader()
    counts: dict[str, int] = {}
    max_confidence: dict[str, float] = {}

    for turn in history:
        for tag in turn.pattern_tags:
            counts[tag.canonical_id] = counts.get(tag.canonical_id, 0) + 1
            current = max_confidence.get(tag.canonical_id, 0.0)
            if tag.confidence > current:
                max_confidence[tag.canonical_id] = tag.confidence

    if not counts:
        return None

    canonical_id = max(
        counts,
        key=lambda pattern_id: (counts[pattern_id], max_confidence[pattern_id]),
    )
    pattern = loader.load(canonical_id)
    return (
        canonical_id,
        pattern.name,
        max_confidence[canonical_id],
        counts[canonical_id],
    )


def unique_detected_patterns(history: list[TurnRecord]) -> list[tuple[str, str]]:
    loader = PatternLoader()
    canonical_ids = sorted(
        {
            tag.canonical_id
            for turn in history
            for tag in turn.pattern_tags
        }
    )
    return [(canonical_id, loader.load(canonical_id).name) for canonical_id in canonical_ids]


def print_interview_summary(history: list[TurnRecord], stream: TextIO) -> None:
    print("NIROS Interview Summary", file=stream)
    print(f"Total turns: {len(history)}", file=stream)

    unique_patterns = unique_detected_patterns(history)
    if unique_patterns:
        print("Unique detected patterns:", file=stream)
        for canonical_id, name in unique_patterns:
            print(f"- {name} ({canonical_id})", file=stream)
    else:
        print("Unique detected patterns: None detected", file=stream)

    strongest = strongest_detected_pattern(history)
    if strongest is None:
        print("Strongest pattern: None detected", file=stream)
    else:
        canonical_id, name, confidence, count = strongest
        print(
            "Strongest pattern: "
            f"{name} ({canonical_id}, count: {count}, confidence: {confidence:.2f})",
            file=stream,
        )

    print("Questions asked:", file=stream)
    for index, turn in enumerate(history, start=1):
        print(f"- Turn {index}: {turn.localized_question}", file=stream)

    print(SEPARATOR, file=stream)


def print_human_profile_summary(history: list[TurnRecord], stream: TextIO) -> None:
    detected_patterns = [tag for turn in history for tag in turn.pattern_tags]
    summary = build_human_profile_summary(detected_patterns)

    print("Human Profile Summary", file=stream)

    primary = summary["primary_pattern"]
    if primary is None:
        print("Primary pattern: None", file=stream)
    else:
        print(
            "Primary pattern: "
            f"{primary['name']} ({primary['canonical_id']}, "
            f"count: {primary['count']}, confidence: {primary['confidence']:.2f})",
            file=stream,
        )

    secondary_patterns = summary["secondary_patterns"]
    if secondary_patterns:
        print("Secondary patterns:", file=stream)
        for pattern in secondary_patterns:
            print(
                f"- {pattern['name']} ({pattern['canonical_id']}, "
                f"count: {pattern['count']}, confidence: {pattern['confidence']:.2f})",
                file=stream,
            )
    else:
        print("Secondary patterns: None", file=stream)

    print("Profile:", file=stream)
    print(summary["profile_text"], file=stream)
    print(SEPARATOR, file=stream)


def print_human_profile_report(
    history: list[TurnRecord],
    stream: TextIO,
    *,
    presenting_problem: dict[str, str] | None = None,
    assessment_results: list[AssessmentResult] | None = None,
    assessment_module_runs: list[AssessedModuleRun] | None = None,
) -> None:
    detected_patterns = [tag for turn in history for tag in turn.pattern_tags]
    hypotheses = [hypothesis for turn in history for hypothesis in turn.hypotheses]
    report = build_human_profile_report_from_tags(
        detected_patterns,
        hypotheses=hypotheses,
        presenting_problem=presenting_problem,
        assessment_results=assessment_results,
        assessment_module_runs=assessment_module_runs,
    )

    print("=== Human Profile Report ===", file=stream)
    print(render_human_profile_report(report), file=stream)
    print(SEPARATOR, file=stream)


def run_interview_session(
    *,
    user_input: str | None = None,
    user_inputs: list[str] | None = None,
    intake_inputs: list[str] | None = None,
    intake_answers: dict[str, str] | None = None,
    turns: int = DEFAULT_TURNS,
    mode: str = DEFAULT_NORMALIZER_MODE,
    provider: str = DEFAULT_SEMANTIC_PROVIDER,
    language: str | None = None,
    stream: TextIO | None = None,
    debug: bool = False,
    input_mode: str = INTERVIEW_INPUT_TEXT,
    voice_input: VoiceInput | None = None,
    big_five_answers: dict[str, int] | None = None,
    skip_intake: bool = False,
    assessment: str = ASSESSMENT_NONE,
    big_five_short_answers: dict[str, int] | None = None,
    adaptive_assessment_answers: dict[str, dict[str, int]] | None = None,
    print_output: bool = True,
) -> InterviewSession:
    stream = stream or sys.stdout
    effective_turns, planned_inputs = resolve_turn_inputs(user_input, user_inputs, turns)
    session_id = f"niros-session-{uuid.uuid4().hex[:8]}"
    resolved_language = language or DEFAULT_LANGUAGE
    blocked_questions = intake_blocked_questions(DEFAULT_INTAKE_PROTOCOL, resolved_language)
    answered_questions: list[str] = []
    completed_topics: list[str] = []

    active_voice_input = voice_input
    fallback_message: str | None = None
    if (
        active_voice_input is None
        and user_input is None
        and user_inputs is None
        and intake_inputs is None
        and intake_answers is None
    ):
        active_voice_input, fallback_message = create_voice_input(
            input_mode,
            stream=stream,
        )

    if active_voice_input is not None:
        active_voice_input.start()

    intake_result: IntakeSessionResult | None = None
    adaptive_history: list[TurnRecord] = []
    cumulative_pattern_tags: list[PatternTag] = []
    evidence_store = None
    assessment_results: list[AssessmentResult] = []
    assessment_module_runs: list[AssessedModuleRun] = []

    try:
        if not skip_intake:
            resolved_intake_answers = resolve_intake_inputs(intake_inputs, intake_answers)
            intake_turns: list[IntakeTurnRecord] = []
            collected_answers: dict[str, str] = {}
            evidence_store = EvidenceStore()

            if print_output:
                print("Structured Intake", file=stream)
                if fallback_message:
                    print(fallback_message, file=stream)

            for index, question_id in enumerate(DEFAULT_INTAKE_PROTOCOL.question_ids(), start=1):
                question_text = DEFAULT_INTAKE_PROTOCOL.question_text(question_id, resolved_language)
                if print_output:
                    print(SEPARATOR, file=stream)
                    print(f"Intake Question {index}:", file=stream)
                    print(question_text, file=stream)
                    print(file=stream)

                if resolved_intake_answers is not None and question_id in resolved_intake_answers:
                    raw_answer = resolved_intake_answers[question_id]
                elif intake_inputs is not None and index - 1 < len(intake_inputs):
                    raw_answer = intake_inputs[index - 1]
                else:
                    raw_answer = read_answer(
                        None,
                        index,
                        stream,
                        voice_input=active_voice_input,
                    )

                if print_output and (active_voice_input is None or active_voice_input.name == "text"):
                    print(raw_answer, file=stream)

                semantic_result = None
                if debug or provider == "openai":
                    semantic_result = extract_semantic_interpretation(raw_answer, provider)

                normalized_answer = normalize_user_input(raw_answer, mode=mode, provider=provider)
                pattern_tags, evidence_store = process_intake_answer(
                    question_id=question_id,
                    raw_answer=raw_answer,
                    session_id=session_id,
                    normalized_answer=normalized_answer,
                    semantic_result=semantic_result,
                    explicit_language=language,
                    evidence_store=evidence_store,
                )
                collected_answers[question_id] = raw_answer
                cumulative_pattern_tags = _merge_pattern_tags_by_id(cumulative_pattern_tags + pattern_tags)
                answered_questions.append(question_text)
                intake_turns.append(
                    IntakeTurnRecord(
                        question_id=question_id,
                        question=question_text,
                        raw_answer=raw_answer,
                        normalized_answer=normalized_answer,
                        pattern_tags=pattern_tags,
                        semantic_result=semantic_result,
                    )
                )

                if print_output:
                    print("Detected Patterns", file=stream)
                    for line in format_pattern_lines(pattern_tags):
                        print(line, file=stream)
                    print(SEPARATOR, file=stream)

            intake_result = IntakeSessionResult(
                intake_state=intake_state_from_answers(collected_answers, language=resolved_language),
                turns=intake_turns,
                cumulative_pattern_tags=list(cumulative_pattern_tags),
                evidence_store=evidence_store,
            )

        presenting_problem: dict[str, str] = {}
        if intake_result is not None:
            presenting_problem = build_presenting_problem(intake_result.intake_state)

        assessment_results = []
        assessment_module_runs = []
        if assessment == ASSESSMENT_BIG_FIVE_SHORT:
            if print_output:
                print(SEPARATOR, file=stream)
            big_five_results = run_big_five_short_assessment(
                language=resolved_language,
                input_stream=sys.stdin,
                output_stream=stream,
                answers=big_five_short_answers,
                print_output=print_output,
            )
            assessment_module_runs = [
                AssessedModuleRun(module_id=ASSESSMENT_BIG_FIVE_SHORT, results=big_five_results)
            ]
            assessment_results = list(big_five_results)
            if print_output:
                print(SEPARATOR, file=stream)
        elif assessment == ASSESSMENT_ADAPTIVE:
            if print_output:
                print(SEPARATOR, file=stream)
            assessment_module_runs = run_adaptive_assessments(
                presenting_problem=presenting_problem,
                detected_patterns=cumulative_pattern_tags,
                language=resolved_language,
                input_stream=sys.stdin,
                output_stream=stream,
                answers_by_module=adaptive_assessment_answers,
                print_output=print_output,
            )
            assessment_results = flatten_assessment_results(assessment_module_runs)
            if print_output:
                print(SEPARATOR, file=stream)

        if print_output:
            print("Adaptive Interview", file=stream)
            print(SEPARATOR, file=stream)

        current_question = select_adaptive_question(
            session_id=session_id,
            cumulative_pattern_tags=cumulative_pattern_tags,
            turn_count=0,
            answered_questions=answered_questions,
            blocked_questions=blocked_questions,
            explicit_language=language,
            presenting_problem=presenting_problem,
            completed_topics=completed_topics,
        )

        for turn_index in range(1, effective_turns + 1):
            if current_question is None:
                break

            localized_question = localize_question(current_question, resolved_language)
            if print_output:
                print(f"Question {turn_index}:", file=stream)
                print(localized_question, file=stream)
                print(file=stream)

            raw_answer = read_answer(
                planned_inputs[turn_index - 1],
                turn_index,
                stream,
                voice_input=active_voice_input,
            )
            if print_output and (active_voice_input is None or active_voice_input.name == "text"):
                print(raw_answer, file=stream)

            semantic_result = None
            if debug or provider == "openai":
                semantic_result = extract_semantic_interpretation(raw_answer, provider)

            normalized_answer = normalize_user_input(raw_answer, mode=mode, provider=provider)
            if print_output:
                print(SEPARATOR, file=stream)

            pattern_tags, hypotheses, next_question, cumulative_pattern_tags = run_adaptive_decision(
                session_id=session_id,
                raw_text=raw_answer,
                normalized_answer=normalized_answer,
                turn_count=turn_index,
                cumulative_pattern_tags=cumulative_pattern_tags,
                answered_questions=answered_questions,
                blocked_questions=blocked_questions,
                semantic_result=semantic_result,
                explicit_language=language,
                presenting_problem=presenting_problem,
                completed_topics=completed_topics,
                current_question=localized_question,
            )

            if debug:
                print_turn_debug_pipeline(
                    stream,
                    raw_transcript=raw_answer,
                    semantic_result=semantic_result,
                    pattern_tags=pattern_tags,
                    cumulative_patterns=cumulative_pattern_tags,
                    big_five_answers=big_five_answers,
                    presenting_problem=build_presenting_problem(intake_result.intake_state)
                    if intake_result is not None
                    else None,
                )

            if print_output:
                print("Detected Patterns", file=stream)
                for line in format_pattern_lines(pattern_tags):
                    print(line, file=stream)
                print(SEPARATOR, file=stream)
                print("Current Hypothesis", file=stream)
                print(format_hypothesis_line(strongest_hypothesis(hypotheses)), file=stream)
                print(SEPARATOR, file=stream)

            adaptive_history.append(
                TurnRecord(
                    question=current_question,
                    localized_question=localized_question,
                    raw_answer=raw_answer,
                    normalized_answer=normalized_answer,
                    pattern_tags=pattern_tags,
                    hypotheses=hypotheses,
                    next_question=next_question,
                    semantic_result=semantic_result,
                    phase="adaptive",
                )
            )

            if next_question:
                current_question = next_question
            elif turn_index < effective_turns:
                break
    finally:
        if active_voice_input is not None:
            active_voice_input.stop()

    return InterviewSession(
        intake_result=intake_result,
        adaptive_history=adaptive_history,
        assessment_results=assessment_results,
        assessment_module_runs=assessment_module_runs,
    )


def read_answer(
    user_input: str | None,
    turn_index: int,
    stream: TextIO,
    voice_input: VoiceInput | None = None,
) -> str:
    if user_input is not None:
        return user_input

    adapter = voice_input or TextInput(stream=stream)
    if not adapter.is_available:
        adapter = TextInput(stream=stream)

    if adapter.name == "text":
        print(f"You (turn {turn_index}):", file=stream)

    return adapter.listen()


def resolve_intake_inputs(
    intake_inputs: list[str] | None,
    intake_answers: dict[str, str] | None,
) -> dict[str, str] | None:
    if intake_answers is not None:
        return dict(intake_answers)

    if intake_inputs is None:
        return None

    answers: dict[str, str] = {}
    for index, question_id in enumerate(DEFAULT_INTAKE_PROTOCOL.question_ids()):
        if index < len(intake_inputs):
            answers[question_id] = intake_inputs[index]
    return answers


def resolve_turn_inputs(
    user_input: str | None,
    user_inputs: list[str] | None,
    turns: int,
) -> tuple[int, list[str | None]]:
    if user_input is not None:
        return 1, [user_input]

    if user_inputs is not None:
        effective_turns = min(turns, len(user_inputs))
        inputs: list[str | None] = list(user_inputs[:effective_turns])
        while len(inputs) < effective_turns:
            inputs.append(None)
        return effective_turns, inputs

    return turns, [None] * turns


def run_demo(
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
) -> int:
    stream = output_stream or sys.stdout

    runtime_settings = build_runtime_settings(
        explicit_provider=provider,
        explicit_runtime_mode=runtime_mode,
        explicit_normalizer_mode=mode,
    )
    if runtime_settings.provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported semantic interpreter provider: {runtime_settings.provider}")

    print("NIROS Human Understanding Engine", file=stream)
    print("Interactive Interview MVP", file=stream)
    print(f"Runtime mode: {runtime_settings.runtime_mode}", file=stream)
    print(f"Semantic provider: {runtime_settings.provider}", file=stream)
    for line in format_openai_startup_lines():
        print(line, file=stream)
    if runtime_settings.selection_message:
        print(runtime_settings.selection_message, file=stream)
    if debug:
        print("Debug mode: enabled", file=stream)
    print(f"Interview input: {input_mode}", file=stream)
    print(file=stream)

    session = run_interview_session(
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
        print_output=True,
    )

    print_interview_summary(session.history, stream)
    print_human_profile_summary(session.history, stream)
    print_human_profile_report(
        session.history,
        stream,
        presenting_problem=session.presenting_problem,
    )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NIROS interactive interview MVP demo")
    parser.add_argument(
        "--mode",
        choices=["passthrough", "mock_llm"],
        default=None,
        help="Statement normalizer mode (default: passthrough for TEST, passthrough for REAL)",
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
        help="Number of interview turns (default: 3)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_project_env()
    args = parse_args(argv)
    if args.turns < 1:
        print("Turn count must be at least 1.", file=sys.stderr)
        return 1
    return run_demo(
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
