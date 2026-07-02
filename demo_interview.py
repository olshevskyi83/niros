#!/usr/bin/env python3
"""Interactive NIROS Human Understanding Engine MVP demo."""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass, field
from typing import TextIO

from niros.evidence import statements_to_evidence
from niros.hypotheses import Hypothesis, generate_hypotheses
from niros.human_profile_summary import build_human_profile_summary
from niros.interview_engine import BlueprintPhase, InterviewDecisionEngine
from niros.knowledge import PatternLoader
from niros.models import InterviewPhase, SupportedLanguage
from niros.patterns import PatternTag, pattern_tag_evidence_items
from niros.question_localizer import localize_question
from niros.state_machine import advance, initial_state
from niros.statement_normalizer import normalize_user_input
from niros.statements import split_transcript_to_statements
from niros.transcript import Transcript

FIRST_QUESTION = "Tell me a little about yourself."
SEPARATOR = "⸻"
DEFAULT_NORMALIZER_MODE = "passthrough"
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


def run_pipeline(
    raw_text: str,
    session_id: str,
) -> tuple[list[PatternTag], list[Hypothesis], str | None]:
    transcript = Transcript(
        session_id=session_id,
        raw_text=raw_text,
        language=SupportedLanguage.ENGLISH,
    )

    statements = split_transcript_to_statements(transcript)
    evidence_items = statements_to_evidence(statements)
    pattern_tags = pattern_tag_evidence_items(evidence_items)
    hypotheses = generate_hypotheses(pattern_tags)

    interview_state = advance(initial_state(session_id), consent_granted=True)
    interview_state = interview_state.model_copy(
        update={
            "input_language": SupportedLanguage.ENGLISH,
            "turn_count": 0,
        }
    )
    assert interview_state.state == InterviewPhase.FREE_NARRATIVE

    decision = InterviewDecisionEngine().decide(
        interview_state,
        pattern_tags,
        hypotheses,
        BlueprintPhase.FREE_NARRATIVE,
    )

    return pattern_tags, hypotheses, decision.selected_question


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


def read_answer(
    user_input: str | None,
    turn_index: int,
    stream: TextIO,
) -> str:
    if user_input is not None:
        return user_input

    print(f"You (turn {turn_index}):", file=stream)
    return sys.stdin.readline().rstrip("\n")


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
    turns: int = DEFAULT_TURNS,
    mode: str = DEFAULT_NORMALIZER_MODE,
    language: str = DEFAULT_LANGUAGE,
    output_stream: TextIO | None = None,
) -> int:
    stream = output_stream or sys.stdout
    effective_turns, planned_inputs = resolve_turn_inputs(user_input, user_inputs, turns)

    print("NIROS Human Understanding Engine", file=stream)
    print("Interactive Interview MVP", file=stream)
    print(file=stream)

    session_id = f"demo-session-{uuid.uuid4().hex[:8]}"
    history: list[TurnRecord] = []
    current_question = FIRST_QUESTION

    for turn_index in range(1, effective_turns + 1):
        localized_question = localize_question(current_question, language)
        print(SEPARATOR, file=stream)
        print(f"Question {turn_index}:", file=stream)
        print(localized_question, file=stream)
        print(file=stream)

        raw_answer = read_answer(planned_inputs[turn_index - 1], turn_index, stream)
        print(raw_answer, file=stream)

        normalized_answer = normalize_user_input(raw_answer, mode=mode)
        if mode != DEFAULT_NORMALIZER_MODE:
            print(f"Normalizer mode: {mode}", file=stream)
            print("Normalized input:", file=stream)
            print(normalized_answer, file=stream)

        print(SEPARATOR, file=stream)

        pattern_tags, hypotheses, next_question = run_pipeline(normalized_answer, session_id)

        print("Detected Patterns", file=stream)
        for line in format_pattern_lines(pattern_tags):
            print(line, file=stream)
        print(SEPARATOR, file=stream)

        print("Current Hypothesis", file=stream)
        print(format_hypothesis_line(strongest_hypothesis(hypotheses)), file=stream)
        print(SEPARATOR, file=stream)

        if turn_index < effective_turns:
            print("Next Question", file=stream)
            if next_question:
                print(localize_question(next_question, language), file=stream)
            else:
                print("None", file=stream)
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
            )
        )

        if next_question:
            current_question = next_question
        elif turn_index < effective_turns:
            break

    print_interview_summary(history, stream)
    print_human_profile_summary(history, stream)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NIROS interactive interview MVP demo")
    parser.add_argument(
        "--mode",
        choices=["passthrough", "mock_llm"],
        default=DEFAULT_NORMALIZER_MODE,
        help="Statement normalizer mode (default: passthrough)",
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
    args = parse_args(argv)
    if args.turns < 1:
        print("Turn count must be at least 1.", file=sys.stderr)
        return 1
    return run_demo(mode=args.mode, language=args.language, turns=args.turns)


if __name__ == "__main__":
    raise SystemExit(main())
