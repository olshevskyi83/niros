from __future__ import annotations

from typing import TextIO

from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.patterns import PatternTag
from niros.semantic_interpreter.base import SemanticInterpretationResult

DEBUG_SECTION_SEPARATOR = "⸻"


def format_semantic_fact_lines(facts) -> list[str]:
    if not facts:
        return ["None extracted"]

    lines: list[str] = []
    for fact in facts:
        confidence = "" if fact.confidence is None else f", confidence: {fact.confidence:.2f}"
        evidence = fact.evidence or fact.value
        lines.append(
            f"- {fact.category}/{fact.attribute}={fact.value}{confidence}: \"{evidence}\""
        )
    return lines


def format_pattern_debug_lines(pattern_tags: list[PatternTag]) -> list[str]:
    if not pattern_tags:
        return ["None detected"]

    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for tag in pattern_tags:
        key = (tag.canonical_id, tag.matched_text)
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"- {tag.canonical_id} (confidence: {tag.confidence:.2f}): \"{tag.matched_text}\""
        )
    return lines


def print_turn_debug_pipeline(
    stream: TextIO,
    *,
    raw_transcript: str,
    semantic_result: SemanticInterpretationResult | None,
    pattern_tags: list[PatternTag],
    cumulative_patterns: list[PatternTag] | None = None,
    big_five_answers: dict[str, int] | None = None,
    presenting_problem: dict[str, str] | None = None,
) -> None:
    print("=== Debug Pipeline ===", file=stream)
    print("Raw transcript:", file=stream)
    print(raw_transcript, file=stream)
    print(DEBUG_SECTION_SEPARATOR, file=stream)

    print("Semantic Facts:", file=stream)
    facts = semantic_result.facts if semantic_result is not None else []
    for line in format_semantic_fact_lines(facts):
        print(line, file=stream)
    if semantic_result is not None and semantic_result.warnings:
        print(f"Warnings: {', '.join(semantic_result.warnings)}", file=stream)
    print(DEBUG_SECTION_SEPARATOR, file=stream)

    print("Detected Patterns:", file=stream)
    for line in format_pattern_debug_lines(pattern_tags):
        print(line, file=stream)
    print(DEBUG_SECTION_SEPARATOR, file=stream)

    fingerprint = build_human_digital_fingerprint(
        detected_patterns=cumulative_patterns or pattern_tags,
        semantic_facts=facts,
        big_five_answers=big_five_answers,
        presenting_problem=presenting_problem,
    )

    print("Human Digital Fingerprint:", file=stream)
    print(fingerprint["summary_text"], file=stream)
    print(DEBUG_SECTION_SEPARATOR, file=stream)
    print(file=stream)
