"""Candidate Pattern Builder — propose reusable mechanisms from Meaning Units."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from niros_tle.meaning_unit_extractor import CONFIDENCE_VALUES, MeaningUnit

TLE_ROOT = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = TLE_ROOT.parent

CANDIDATE_STATUS = "candidate"

CONFIDENCE_RANK: dict[str, int] = {"low": 0, "medium": 1, "high": 2}

PROPOSED_NAMES: dict[str, str] = {
    "acceptance": "Acceptance Invitation",
    "agency_restoration": "Agency Restoration",
    "compassion_invitation": "Compassion Loop",
    "identity_reconstruction": "Identity Reconstruction",
    "narrative_reframing": "Narrative Reframing",
    "values_clarification": "Values Clarification",
    "hope_induction": "Hope Induction",
    "permission": "Permission Giving",
    "future_orientation": "Future Orientation",
    "safety_cue": "Safety Cue",
    "perspective_shift": "Perspective Shift",
    "defusion": "Acceptance Invitation",
    "grounding": "Safety Cue",
    "curiosity": "Perspective Shift",
    "grief_processing": "Emotion Labeling",
    "meaning_making": "Narrative Reframing",
}

MECHANISM_PROFILES: dict[str, dict[str, Any]] = {
    "acceptance": {
        "therapeutic_goal": "Reduce struggle with internal experience through acceptance framing.",
        "possible_good_for": ("intrusive_thoughts", "resistance", "emotional_avoidance"),
        "possible_avoid_for": ("acute_dissociation", "psychosis_risk"),
    },
    "agency_restoration": {
        "therapeutic_goal": "Restore incremental sense of choice and action.",
        "possible_good_for": ("low_agency", "hopelessness"),
        "possible_avoid_for": ("mania_risk", "psychosis_risk"),
    },
    "compassion_invitation": {
        "therapeutic_goal": "Support self-compassionate framing without identity claims.",
        "possible_good_for": ("shame", "self_criticism"),
        "possible_avoid_for": ("acute_dissociation", "psychosis_risk"),
    },
    "identity_reconstruction": {
        "therapeutic_goal": "Support identity exploration without fixed labels.",
        "possible_good_for": ("identity_confusion", "self_doubt"),
        "possible_avoid_for": ("psychosis_risk",),
    },
    "narrative_reframing": {
        "therapeutic_goal": "Invite alternative meaning without forcing closure.",
        "possible_good_for": ("rigidity", "stuck_narrative"),
        "possible_avoid_for": ("psychosis_risk",),
    },
    "values_clarification": {
        "therapeutic_goal": "Clarify values-linked direction without prescriptive destiny claims.",
        "possible_good_for": ("identity_confusion", "values_conflict"),
        "possible_avoid_for": ("mania_risk", "psychosis_risk"),
    },
    "hope_induction": {
        "therapeutic_goal": "Introduce cautious future-oriented possibility language.",
        "possible_good_for": ("hopelessness", "despair"),
        "possible_avoid_for": ("mania_risk",),
    },
    "permission": {
        "therapeutic_goal": "Offer paced permission without forcing change.",
        "possible_good_for": ("self_criticism", "pressure", "perfectionism"),
        "possible_avoid_for": ("psychosis_risk",),
    },
    "future_orientation": {
        "therapeutic_goal": "Orient attention toward actionable future possibilities.",
        "possible_good_for": ("low_agency", "hopelessness"),
        "possible_avoid_for": ("mania_risk",),
    },
    "safety_cue": {
        "therapeutic_goal": "Stabilize through safety and grounding orientation.",
        "possible_good_for": ("anxiety", "emotional_overwhelm"),
        "possible_avoid_for": ("acute_dissociation",),
    },
    "perspective_shift": {
        "therapeutic_goal": "Invite a broader or alternative perspective without certainty.",
        "possible_good_for": ("rigidity", "certainty_seeking"),
        "possible_avoid_for": ("psychosis_risk",),
    },
}


class CandidatePatternBuilderError(ValueError):
    """Raised when candidate pattern building fails."""


@dataclass(frozen=True)
class CandidatePattern:
    candidate_id: str
    source_document: str
    source_family: str
    meaning_unit_ids: tuple[str, ...]
    proposed_name: str
    psychological_functions: tuple[str, ...]
    language_mechanisms: tuple[str, ...]
    therapeutic_goal: str
    possible_good_for: tuple[str, ...]
    possible_avoid_for: tuple[str, ...]
    confidence: str
    supporting_evidence: tuple[dict[str, str], ...]
    status: str
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source_document": self.source_document,
            "source_family": self.source_family,
            "meaning_unit_ids": list(self.meaning_unit_ids),
            "proposed_name": self.proposed_name,
            "psychological_functions": list(self.psychological_functions),
            "language_mechanisms": list(self.language_mechanisms),
            "therapeutic_goal": self.therapeutic_goal,
            "possible_good_for": list(self.possible_good_for),
            "possible_avoid_for": list(self.possible_avoid_for),
            "confidence": self.confidence,
            "supporting_evidence": [dict(item) for item in self.supporting_evidence],
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CandidatePatternBuilder:
    repo_root: Path = field(default_factory=lambda: DEFAULT_REPO_ROOT)

    def build(self, meaning_units: tuple[MeaningUnit, ...]) -> tuple[CandidatePattern, ...]:
        if not meaning_units:
            return ()

        sorted_units = tuple(sorted(meaning_units, key=lambda unit: unit.meaning_unit_id))
        groups = _group_meaning_units(sorted_units)
        candidates: list[CandidatePattern] = []

        for group_index, group in enumerate(groups, start=1):
            candidates.append(_build_candidate_pattern(group, group_index))

        return tuple(sorted(candidates, key=lambda item: item.candidate_id))

    def save_candidates(
        self,
        *,
        source_document: str,
        source_family: str,
        candidates: tuple[CandidatePattern, ...],
    ) -> Path:
        output_path = candidate_patterns_output_path(
            source_document=source_document,
            source_family=source_family,
            repo_root=self.repo_root,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source_document": source_document,
            "source_family": source_family,
            "candidate_count": len(candidates),
            "candidates": [candidate.to_dict() for candidate in candidates],
        }
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return output_path

    def build_and_save(self, meaning_units: tuple[MeaningUnit, ...]) -> tuple[CandidatePattern, ...]:
        candidates = self.build(meaning_units)
        if not candidates:
            return ()
        source_document = candidates[0].source_document
        source_family = candidates[0].source_family
        self.save_candidates(
            source_document=source_document,
            source_family=source_family,
            candidates=candidates,
        )
        return candidates


def candidate_patterns_output_path(
    *,
    source_document: str,
    source_family: str,
    repo_root: Path,
) -> Path:
    return (
        repo_root
        / "niros_tle"
        / "corpus"
        / source_family
        / "processed"
        / "candidate_patterns"
        / f"{source_document}.candidate_patterns.json"
    )


def generate_candidate_id(source_family: str, mechanism: str, group_index: int) -> str:
    slug = _slugify(mechanism)
    return f"candidate_{source_family}_{slug}_{group_index:03d}"


def _build_candidate_pattern(
    units: tuple[MeaningUnit, ...],
    group_index: int,
) -> CandidatePattern:
    source_document = _source_document(units[0])
    source_family = _source_family(units[0])
    primary_mechanism = _primary_mechanism(units[0])
    profile = MECHANISM_PROFILES.get(primary_mechanism, _default_profile(primary_mechanism))

    psychological_functions = _unique_preserve_order(
        function for unit in units for function in unit.psychological_functions
    )
    language_mechanisms = _unique_preserve_order(
        pattern for unit in units for pattern in unit.language_patterns
    )
    meaning_unit_ids = tuple(unit.meaning_unit_id for unit in units)
    supporting_evidence = tuple(
        {
            "meaning_unit_id": unit.meaning_unit_id,
            "summary": unit.summary,
        }
        for unit in units
    )

    return CandidatePattern(
        candidate_id=generate_candidate_id(source_family, primary_mechanism, group_index),
        source_document=source_document,
        source_family=source_family,
        meaning_unit_ids=meaning_unit_ids,
        proposed_name=PROPOSED_NAMES.get(primary_mechanism, _title_case(primary_mechanism)),
        psychological_functions=psychological_functions,
        language_mechanisms=language_mechanisms,
        therapeutic_goal=str(profile["therapeutic_goal"]),
        possible_good_for=tuple(profile["possible_good_for"]),
        possible_avoid_for=tuple(profile["possible_avoid_for"]),
        confidence=_aggregate_confidence(unit.confidence for unit in units),
        supporting_evidence=supporting_evidence,
        status=CANDIDATE_STATUS,
        metadata={
            "primary_mechanism": primary_mechanism,
            "meaning_unit_count": str(len(units)),
        },
    )


def _group_meaning_units(units: tuple[MeaningUnit, ...]) -> list[tuple[MeaningUnit, ...]]:
    count = len(units)
    parent = list(range(count))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for left in range(count):
        for right in range(left + 1, count):
            if _should_merge(units[left], units[right]):
                union(left, right)

    grouped: dict[int, list[int]] = {}
    for index in range(count):
        root = find(index)
        grouped.setdefault(root, []).append(index)

    return [
        tuple(units[index] for index in sorted(indices, key=lambda idx: units[idx].meaning_unit_id))
        for indices in sorted(grouped.values(), key=lambda group: units[group[0]].meaning_unit_id)
    ]


def _should_merge(left: MeaningUnit, right: MeaningUnit) -> bool:
    if _primary_mechanism(left) != _primary_mechanism(right):
        return False
    if _source_family(left) != _source_family(right):
        return False
    psych_overlap = set(left.psychological_functions) & set(right.psychological_functions)
    lang_overlap = set(left.language_patterns) & set(right.language_patterns)
    return bool(psych_overlap) and bool(lang_overlap)


def _primary_mechanism(unit: MeaningUnit) -> str:
    if not unit.psychological_functions:
        raise CandidatePatternBuilderError(
            f"Meaning unit '{unit.meaning_unit_id}' lacks psychological_functions."
        )
    return unit.psychological_functions[0]


def _source_document(unit: MeaningUnit) -> str:
    document = unit.metadata.get("source_document", "").strip()
    if not document:
        raise CandidatePatternBuilderError(
            f"Meaning unit '{unit.meaning_unit_id}' lacks source_document metadata."
        )
    return document


def _source_family(unit: MeaningUnit) -> str:
    family = unit.metadata.get("source_family", "").strip().lower()
    if not family:
        raise CandidatePatternBuilderError(
            f"Meaning unit '{unit.meaning_unit_id}' lacks source_family metadata."
        )
    return family


def _aggregate_confidence(values: Iterable[str]) -> str:
    best = "low"
    best_rank = CONFIDENCE_RANK[best]
    for value in values:
        normalized = value.strip().lower()
        if normalized not in CONFIDENCE_RANK:
            raise CandidatePatternBuilderError(f"Invalid confidence '{value}'.")
        if CONFIDENCE_RANK[normalized] > best_rank:
            best = normalized
            best_rank = CONFIDENCE_RANK[normalized]
    if best not in CONFIDENCE_VALUES:
        raise CandidatePatternBuilderError(f"Invalid aggregated confidence '{best}'.")
    return best


def _default_profile(mechanism: str) -> dict[str, Any]:
    return {
        "therapeutic_goal": f"Support {mechanism.replace('_', ' ')} through structured language mechanisms.",
        "possible_good_for": (mechanism,),
        "possible_avoid_for": ("psychosis_risk",),
    }


def _unique_preserve_order(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"


def _title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("_"))
