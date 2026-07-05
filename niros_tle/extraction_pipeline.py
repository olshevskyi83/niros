"""Universal Pattern Extraction Pipeline — deterministic process model only.

Books and source fragments are raw material. This pipeline describes how therapeutic
language becomes structured Universal Therapeutic Patterns. No NLP, AI, RAG, or LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from niros_tle.pattern_contract import (
    TLEPatternRecord,
    validate_tle_pattern_record,
)

PROVISIONAL_FUNCTIONS: tuple[str, ...] = (
    "permission",
    "acceptance",
    "identity",
    "agency",
    "hope",
    "safety",
    "curiosity",
    "compassion",
)

CONFIDENCE_VALUES: tuple[str, ...] = ("low", "medium", "high")

FUNCTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "permission": ("permission", "may", "allowed", "need not", "can choose", "pause"),
    "acceptance": ("accept", "allow", "fight", "thought", "resist", "defusion"),
    "identity": ("identity", "self", "who you are", "become"),
    "agency": ("agency", "choice", "choose", "action", "step"),
    "hope": ("hope", "future", "possibility", "forward"),
    "safety": ("safe", "safety", "ground", "steady", "protect"),
    "curiosity": ("curious", "curiosity", "wonder", "explore", "question"),
    "compassion": ("kind", "kindness", "compassion", "gentle", "care"),
}

FUNCTION_PROFILES: dict[str, dict[str, Any]] = {
    "acceptance": {
        "good_for": ("intrusive_thoughts", "resistance", "emotional_avoidance"),
        "avoid_if": ("acute_dissociation", "psychosis_risk"),
        "language_style": ("permission_based", "non_confrontational", "acceptance_oriented"),
        "semantic_cluster": ("acceptance", "thought", "permission", "defusion"),
        "therapeutic_intention": "Reduce struggle with internal experience through acceptance framing.",
    },
    "permission": {
        "good_for": ("self_criticism", "pressure", "perfectionism"),
        "avoid_if": ("psychosis_risk",),
        "language_style": ("permission_based", "gentle", "non_prescriptive"),
        "semantic_cluster": ("permission", "choice", "pace", "safety"),
        "therapeutic_intention": "Offer paced permission without forcing change.",
    },
    "identity": {
        "good_for": ("identity_confusion", "self_doubt"),
        "avoid_if": ("psychosis_risk",),
        "language_style": ("reflective", "identity_repetition", "exploratory"),
        "semantic_cluster": ("identity", "self", "meaning", "choice"),
        "therapeutic_intention": "Support identity exploration without fixed labels.",
    },
    "agency": {
        "good_for": ("low_agency", "hopelessness"),
        "avoid_if": ("mania_risk", "psychosis_risk"),
        "language_style": ("future_orientation", "incremental_steps"),
        "semantic_cluster": ("agency", "choice", "growth", "future"),
        "therapeutic_intention": "Restore incremental sense of choice and action.",
    },
    "hope": {
        "good_for": ("hopelessness", "despair"),
        "avoid_if": ("mania_risk",),
        "language_style": ("future_orientation", "gentle"),
        "semantic_cluster": ("hope", "future", "possibility"),
        "therapeutic_intention": "Introduce cautious future-oriented possibility language.",
    },
    "safety": {
        "good_for": ("anxiety", "emotional_overwhelm"),
        "avoid_if": ("acute_dissociation",),
        "language_style": ("grounding_language", "body_orientation", "present_moment"),
        "semantic_cluster": ("safety", "grounding", "body", "breath"),
        "therapeutic_intention": "Stabilize through safety and grounding orientation.",
    },
    "curiosity": {
        "good_for": ("rigidity", "certainty_seeking"),
        "avoid_if": ("psychosis_risk",),
        "language_style": ("question_based", "exploratory", "uncertainty_language"),
        "semantic_cluster": ("curiosity", "question", "openness", "possibility"),
        "therapeutic_intention": "Invite open curiosity instead of forced resolution.",
    },
    "compassion": {
        "good_for": ("shame", "self_criticism"),
        "avoid_if": ("acute_dissociation", "psychosis_risk"),
        "language_style": ("gentle", "permission_based", "non_confrontational"),
        "semantic_cluster": ("kindness", "compassion", "acceptance", "safety"),
        "therapeutic_intention": "Support self-compassionate framing without identity claims.",
    },
}

CLAUSE_SPLIT_PATTERN = re.compile(r"[.!?;]+")


class ExtractionPipelineError(ValueError):
    """Raised when the extraction pipeline cannot proceed safely."""


@dataclass(frozen=True)
class SourceFragment:
    source_family: str
    source_reference: str
    language: str
    fragment_text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MeaningUnit:
    id: str
    text: str
    provisional_function: str
    confidence: str


@dataclass(frozen=True)
class CandidatePattern:
    pattern_id: str
    psychological_function: tuple[str, ...]
    language_characteristics: tuple[str, ...]
    symbolic_characteristics: tuple[str, ...]
    rhythm_characteristics: str
    therapeutic_intention: str
    evidence_units: tuple[str, ...]


@dataclass(frozen=True)
class ValidatedPatternCandidate:
    candidate: CandidatePattern
    is_valid: bool
    validation_notes: tuple[str, ...]


@dataclass(frozen=True)
class ExtractionPipelineResult:
    fragment: SourceFragment
    meaning_units: tuple[MeaningUnit, ...]
    candidate_pattern: CandidatePattern | None
    validated_pattern: ValidatedPatternCandidate | None
    tle_pattern_record: TLEPatternRecord | None


class UniversalPatternExtractionPipeline:
    """Deterministic placeholder pipeline for fragment-to-pattern extraction."""

    def extract_from_fragment(self, fragment: SourceFragment) -> ExtractionPipelineResult:
        meaning_units = self.extract_meaning_units(fragment)
        if not meaning_units:
            return ExtractionPipelineResult(
                fragment=fragment,
                meaning_units=(),
                candidate_pattern=None,
                validated_pattern=ValidatedPatternCandidate(
                    candidate=_empty_candidate(),
                    is_valid=False,
                    validation_notes=("Empty or unusable source fragment.",),
                ),
                tle_pattern_record=None,
            )

        candidate_pattern = self.build_candidate_pattern(fragment, meaning_units)
        validated_pattern = self.validate_candidate(fragment, candidate_pattern, meaning_units)
        tle_pattern_record = None
        if validated_pattern.is_valid:
            tle_pattern_record = self.to_tle_pattern_record(
                fragment,
                candidate_pattern,
                meaning_units,
                validated_pattern,
            )

        return ExtractionPipelineResult(
            fragment=fragment,
            meaning_units=meaning_units,
            candidate_pattern=candidate_pattern,
            validated_pattern=validated_pattern,
            tle_pattern_record=tle_pattern_record,
        )

    def extract_meaning_units(self, fragment: SourceFragment) -> tuple[MeaningUnit, ...]:
        text = fragment.fragment_text.strip()
        if not text:
            return ()

        clauses = [clause.strip() for clause in CLAUSE_SPLIT_PATTERN.split(text) if clause.strip()]
        if not clauses:
            return ()

        units: list[MeaningUnit] = []
        for index, clause in enumerate(clauses, start=1):
            provisional_function, confidence = _score_provisional_function(clause)
            units.append(
                MeaningUnit(
                    id=f"unit_{index:02d}",
                    text=provisional_function,
                    provisional_function=provisional_function,
                    confidence=confidence,
                )
            )
        return tuple(units)

    def build_candidate_pattern(
        self,
        fragment: SourceFragment,
        meaning_units: tuple[MeaningUnit, ...],
    ) -> CandidatePattern:
        functions = _unique_preserve_order(unit.provisional_function for unit in meaning_units)
        primary_function = functions[0]
        profile = FUNCTION_PROFILES[primary_function]

        language_characteristics = _unique_preserve_order(
            characteristic
            for function in functions
            for characteristic in FUNCTION_PROFILES[function]["language_style"]
        )
        symbolic_characteristics = _unique_preserve_order(
            characteristic
            for function in functions
            for characteristic in FUNCTION_PROFILES[function]["semantic_cluster"]
        )

        return CandidatePattern(
            pattern_id=f"{primary_function}_loop",
            psychological_function=functions,
            language_characteristics=language_characteristics,
            symbolic_characteristics=symbolic_characteristics,
            rhythm_characteristics="slow_repetitive",
            therapeutic_intention=str(profile["therapeutic_intention"]),
            evidence_units=tuple(unit.id for unit in meaning_units),
        )

    def validate_candidate(
        self,
        fragment: SourceFragment,
        candidate: CandidatePattern,
        meaning_units: tuple[MeaningUnit, ...],
    ) -> ValidatedPatternCandidate:
        notes: list[str] = []

        if not candidate.psychological_function:
            notes.append("Candidate lacks psychological functions.")
        if len(candidate.evidence_units) < 1:
            notes.append("Insufficient evidence units.")
        if not _is_internally_coherent(candidate):
            notes.append("Candidate functions are not internally coherent.")
        if not _is_psychologically_meaningful(candidate):
            notes.append("Candidate is not psychologically meaningful.")
        if _is_source_specific_only(fragment, candidate):
            notes.append("Candidate appears source-specific only.")
        if _contains_fragment_text(candidate, fragment.fragment_text):
            notes.append("Candidate stores copyrighted or source fragment text.")
        if _is_merely_stylistic(candidate):
            notes.append("Candidate appears merely stylistic.")

        is_valid = not notes
        if is_valid:
            notes.append("Candidate passed deterministic validation checks.")

        return ValidatedPatternCandidate(
            candidate=candidate,
            is_valid=is_valid,
            validation_notes=tuple(notes),
        )

    def to_tle_pattern_record(
        self,
        fragment: SourceFragment,
        candidate: CandidatePattern,
        meaning_units: tuple[MeaningUnit, ...],
        validated: ValidatedPatternCandidate,
    ) -> TLEPatternRecord:
        if not validated.is_valid:
            raise ExtractionPipelineError("Cannot export an invalid candidate pattern.")

        primary_function = candidate.psychological_function[0]
        good_for = _unique_preserve_order(
            item
            for function in candidate.psychological_function
            for item in FUNCTION_PROFILES[function]["good_for"]
        )
        avoid_if = _unique_preserve_order(
            item
            for function in candidate.psychological_function
            for item in FUNCTION_PROFILES[function]["avoid_if"]
        )

        record = TLEPatternRecord(
            id=candidate.pattern_id,
            name=_pattern_display_name(candidate.pattern_id),
            psychological_function=candidate.psychological_function,
            good_for=good_for,
            avoid_if=avoid_if,
            language_style=candidate.language_characteristics,
            rhythm=candidate.rhythm_characteristics,
            semantic_cluster=candidate.symbolic_characteristics,
            spiritual_compatibility=("secular", "agnostic", "spiritual_not_religious"),
            requires_symbols=(),
            forbidden_symbols=(),
            intensity="low",
            directness="low",
            repetition_level="medium",
            safety_notes=(
                "Avoid strong identity claims",
                "Use non-directive conceptual framing only",
            ),
            source_family=(fragment.source_family,),
            source_confidence=_aggregate_confidence(meaning_units),
            extraction_method="manual_seed",
            evidence_refs=(
                {
                    "source_family": fragment.source_family,
                    "reference_type": "conceptual",
                    "note": (
                        f"Derived from {len(meaning_units)} meaning unit(s) with "
                        f"{primary_function} orientation via deterministic pipeline."
                    ),
                },
            ),
            notes="Extracted via Universal Pattern Extraction Pipeline placeholder.",
            example_use_case=candidate.therapeutic_intention,
        )
        validate_tle_pattern_record(record)
        return record


def _score_provisional_function(clause: str) -> tuple[str, str]:
    lowered = clause.lower()
    scores: dict[str, int] = {function: 0 for function in PROVISIONAL_FUNCTIONS}

    for function, keywords in FUNCTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                scores[function] += 1

    best_function = max(scores, key=lambda function: (scores[function], function))
    best_score = scores[best_function]
    if best_score == 0:
        return "acceptance", "low"

    if best_score >= 3:
        confidence = "high"
    elif best_score == 2:
        confidence = "medium"
    else:
        confidence = "low"
    return best_function, confidence


def _unique_preserve_order(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _is_internally_coherent(candidate: CandidatePattern) -> bool:
    return len(candidate.psychological_function) >= 1 and len(candidate.language_characteristics) >= 1


def _is_psychologically_meaningful(candidate: CandidatePattern) -> bool:
    return all(function in PROVISIONAL_FUNCTIONS for function in candidate.psychological_function)


def _is_source_specific_only(fragment: SourceFragment, candidate: CandidatePattern) -> bool:
    normalized_reference = fragment.source_reference.lower().replace(" ", "_")
    normalized_family = fragment.source_family.lower().replace(" ", "_")
    pattern_id = candidate.pattern_id.lower()
    return normalized_reference in pattern_id and normalized_family in pattern_id


def _contains_fragment_text(candidate: CandidatePattern, fragment_text: str) -> bool:
    normalized_fragment = fragment_text.strip().lower()
    if not normalized_fragment:
        return False

    candidate_values = (
        candidate.pattern_id,
        candidate.rhythm_characteristics,
        candidate.therapeutic_intention,
        *candidate.psychological_function,
        *candidate.language_characteristics,
        *candidate.symbolic_characteristics,
    )
    for value in candidate_values:
        if normalized_fragment in value.lower():
            return True
    return False


def _is_merely_stylistic(candidate: CandidatePattern) -> bool:
    stylistic_only = {"metaphorical", "poetic", "rhythmic", "lyrical"}
    function_set = set(candidate.psychological_function)
    return function_set.issubset(stylistic_only)


def _aggregate_confidence(meaning_units: tuple[MeaningUnit, ...]) -> str:
    rank = {"low": 0, "medium": 1, "high": 2}
    lowest = min(rank[unit.confidence] for unit in meaning_units)
    return ("low", "medium", "high")[lowest]


def _pattern_display_name(pattern_id: str) -> str:
    base = pattern_id.removesuffix("_loop").replace("_", " ")
    return f"{base.title()} Loop"


def _empty_candidate() -> CandidatePattern:
    return CandidatePattern(
        pattern_id="empty_candidate",
        psychological_function=(),
        language_characteristics=(),
        symbolic_characteristics=(),
        rhythm_characteristics="",
        therapeutic_intention="",
        evidence_units=(),
    )
