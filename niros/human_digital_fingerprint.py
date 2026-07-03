from __future__ import annotations

from niros.assessment import AssessmentResult
from niros.assessment_runner import format_assessment_signal, serialize_assessment_results
from niros.big_five.profile import BigFiveProfile
from niros.big_five.scorer import score_big_five
from niros.human_profile_summary import NO_EVIDENCE_PROFILE_TEXT, build_human_profile_summary
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact

HIGH_TRAIT_THRESHOLD = 0.65
LOW_TRAIT_THRESHOLD = 0.35
NEUTRAL_TRAIT_THRESHOLD = 0.5

TRAIT_DESCRIPTOR_PHRASES: dict[str, tuple[str, str]] = {
    "openness": (
        "shows curiosity and openness to new experiences",
        "shows preference for familiar and practical approaches",
    ),
    "conscientiousness": (
        "shows structured and goal-directed tendencies",
        "shows flexible and less structured tendencies",
    ),
    "extraversion": (
        "shows sociable and energizing social engagement",
        "shows reserved and low-stimulation social preferences",
    ),
    "agreeableness": (
        "shows cooperative and considerate interpersonal style",
        "shows direct and less accommodating interpersonal style",
    ),
    "neuroticism": (
        "shows higher emotional reactivity and sensitivity to stress",
        "shows emotional steadiness under pressure",
    ),
}

NON_DIAGNOSTIC_NOTICE = (
    "Trait estimates come from self-report and describe tendencies, not diagnoses."
)


def build_human_digital_fingerprint(
    *,
    detected_patterns: list[PatternTag],
    semantic_facts: list[SemanticFact] | None = None,
    big_five: BigFiveProfile | None = None,
    big_five_answers: dict[str, int] | None = None,
    presenting_problem: dict[str, str] | None = None,
    assessment_results: list[AssessmentResult] | None = None,
) -> dict:
    patterns = build_human_profile_summary(detected_patterns)
    facts = list(semantic_facts or [])
    serialized_assessment = serialize_assessment_results(list(assessment_results or []))

    profile = big_five
    if profile is None and big_five_answers is not None:
        profile = score_big_five(big_five_answers)

    fingerprint_payload = {
        "patterns": patterns,
        "semantic_facts": facts,
        "big_five": profile.to_dict() if profile is not None else None,
        "presenting_problem": presenting_problem or {},
        "assessment_results": serialized_assessment,
    }

    return {
        "patterns": patterns,
        "semantic_facts": [_serialize_semantic_fact(fact) for fact in facts],
        "big_five": profile.to_dict() if profile is not None else None,
        "presenting_problem": dict(presenting_problem or {}),
        "assessment_results": serialized_assessment,
        "summary_text": format_human_digital_fingerprint(fingerprint_payload),
    }


def format_human_digital_fingerprint(fingerprint: dict) -> str:
    parts: list[str] = []

    presenting_part = _format_presenting_problem_section(fingerprint.get("presenting_problem", {}))
    if presenting_part:
        parts.append(presenting_part)

    pattern_part = _format_pattern_section(fingerprint.get("patterns", {}))
    if pattern_part:
        parts.append(pattern_part)

    semantic_part = _format_semantic_facts_section(fingerprint.get("semantic_facts", []))
    if semantic_part:
        parts.append(semantic_part)

    big_five_part = _format_big_five_section(fingerprint.get("big_five"))
    if big_five_part:
        parts.append(big_five_part)

    assessment_part = _format_assessment_results_section(fingerprint.get("assessment_results", []))
    if assessment_part:
        parts.append(assessment_part)

    if not parts:
        return NO_EVIDENCE_PROFILE_TEXT

    parts.append(NON_DIAGNOSTIC_NOTICE)
    return " ".join(parts)


def _format_presenting_problem_section(presenting_problem: dict) -> str:
    if not presenting_problem:
        return ""

    labels = {
        "main_problem": "Main problem",
        "duration": "Duration",
        "perceived_causes": "Perceived causes",
        "current_impact": "Current impact",
        "previous_attempts": "Previous attempts",
        "desired_outcome": "Desired outcome",
    }
    lines: list[str] = []
    for key, label in labels.items():
        value = str(presenting_problem.get(key, "")).strip()
        if value:
            lines.append(f"{label}: {value}")

    if not lines:
        return ""

    return "Presenting problem: " + " ".join(lines) + "."


def describe_big_five_trait(trait: str, score: float) -> str:
    high_phrase, low_phrase = TRAIT_DESCRIPTOR_PHRASES[trait]
    if score >= HIGH_TRAIT_THRESHOLD:
        return high_phrase
    if score <= LOW_TRAIT_THRESHOLD:
        return low_phrase
    return f"shows a moderate level on {trait.replace('_', ' ')}"


def _serialize_semantic_fact(fact: SemanticFact) -> dict[str, str | float | None]:
    return {
        "category": fact.category,
        "attribute": fact.attribute,
        "value": fact.value,
        "evidence": fact.evidence,
        "confidence": fact.confidence,
    }


def _format_pattern_section(patterns: dict) -> str:
    if not patterns.get("pattern_counts"):
        return ""

    parts: list[str] = []
    primary = patterns.get("primary_pattern")
    if primary is not None:
        parts.append(
            f"Primary interview pattern: {primary['name']} ({primary['canonical_id']}, "
            f"count: {primary['count']})."
        )

    secondary_patterns = patterns.get("secondary_patterns", [])
    if secondary_patterns:
        secondary_names = ", ".join(
            f"{pattern['name']} ({pattern['canonical_id']})" for pattern in secondary_patterns
        )
        parts.append(f"Secondary interview patterns: {secondary_names}.")

    parts.append(patterns["profile_text"])
    return " ".join(parts)


def _format_semantic_facts_section(semantic_facts: list) -> str:
    if not semantic_facts:
        return ""

    rendered_facts: list[str] = []
    for fact in semantic_facts:
        if isinstance(fact, SemanticFact):
            category = fact.category
            attribute = fact.attribute
            value = fact.value
            evidence = fact.evidence or fact.value
        else:
            category = fact["category"]
            attribute = fact["attribute"]
            value = fact["value"]
            evidence = fact.get("evidence") or value
        rendered_facts.append(f"{category}/{attribute}={value} (\"{evidence}\")")

    return "Semantic facts: " + "; ".join(rendered_facts) + "."


def _format_big_five_section(big_five: dict[str, float] | None) -> str:
    if not big_five:
        return ""

    trait_lines = []
    for trait in BigFiveProfile.TRAIT_FIELDS:
        score = big_five[trait]
        descriptor = describe_big_five_trait(trait, score)
        trait_lines.append(f"{trait}={score:.2f} ({descriptor})")

    return "Big Five self-report: " + "; ".join(trait_lines) + "."


def _format_assessment_results_section(assessment_results: list) -> str:
    if not assessment_results:
        return ""

    signals = [format_assessment_signal(result) for result in assessment_results]
    return "Structured assessment signals: " + "; ".join(signals) + "."
