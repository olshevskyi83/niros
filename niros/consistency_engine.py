from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from niros.evidence_store import EvidenceStore, SemanticEvidenceEntry
from niros.semantic_interpreter.facts import SemanticFact

CONTRADICTION = "contradiction"
AMBIGUITY = "ambiguity"
EVOLVING_BELIEF = "evolving_belief"

DEFAULT_CONFIDENCE = 0.5
AMBIGUITY_BALANCE_THRESHOLD = 0.45

INCOMPATIBLE_VALUE_PAIRS = frozenset(
    {
        frozenset({"low", "high"}),
        frozenset({"weak", "strong"}),
        frozenset({"stable", "unstable"}),
        frozenset({"present", "absent"}),
        frozenset({"avoidant", "anxious"}),
    }
)

ATTRIBUTE_LABELS = {
    "identity": "Identity",
    "self_efficacy": "Self-efficacy",
    "self_worth": "Self-worth",
    "reaction_to_criticism": "Reaction to criticism",
    "fear_of_rejection": "Fear of rejection",
    "boundary_setting": "Boundary setting",
    "trust": "Trust",
    "attachment": "Attachment",
    "conflict": "Conflict",
}

NEGATIVE_VALUES = frozenset({"low", "weak", "absent", "avoidant", "unclear", "anxious"})


class ConsistencySeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ConsistencyIssue:
    type: str
    severity: str
    attribute: str
    old_value: str
    new_value: str
    evidence_old: str
    evidence_new: str


def analyze_consistency(evidence_store: EvidenceStore) -> list[ConsistencyIssue]:
    grouped = _group_by_attribute(evidence_store.entries)
    issues: list[ConsistencyIssue] = []

    for attribute in sorted(grouped):
        attribute_issues = _analyze_attribute(attribute, grouped[attribute])
        issues.extend(attribute_issues)

    return sorted(
        issues,
        key=lambda issue: (issue.attribute, issue.type, issue.old_value, issue.new_value),
    )


def format_consistency_observations(issues: list[ConsistencyIssue]) -> list[str]:
    observations: list[str] = []
    for issue in issues:
        observations.append(_observation_line(issue))
    return observations


def _group_by_attribute(
    entries: tuple[SemanticEvidenceEntry, ...],
) -> dict[str, list[SemanticEvidenceEntry]]:
    grouped: dict[str, list[SemanticEvidenceEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.fact.attribute, []).append(entry)
    for attribute in grouped:
        grouped[attribute].sort(key=lambda item: item.sequence)
    return grouped


def _analyze_attribute(
    attribute: str,
    entries: list[SemanticEvidenceEntry],
) -> list[ConsistencyIssue]:
    values = {entry.fact.value for entry in entries}
    if len(values) <= 1:
        return []

    evolving = _detect_evolving_belief(attribute, entries)
    if evolving is not None:
        return [evolving]

    contradiction = _detect_contradiction(attribute, entries)
    if contradiction is not None:
        return [contradiction]

    ambiguity = _detect_ambiguity(attribute, entries)
    if ambiguity is not None:
        return [ambiguity]

    return []


def _detect_evolving_belief(
    attribute: str,
    entries: list[SemanticEvidenceEntry],
) -> ConsistencyIssue | None:
    if len(entries) < 3:
        return None

    midpoint = max(len(entries) // 2, 1)
    first_half = entries[:midpoint]
    second_half = entries[midpoint:]
    if not second_half:
        return None

    first_value, _ = _dominant_value(first_half)
    second_value, _ = _dominant_value(second_half)
    if first_value == second_value:
        return None

    old_entry = _first_entry_for_value(first_half, first_value)
    new_entry = _last_entry_for_value(second_half, second_value)

    return ConsistencyIssue(
        type=EVOLVING_BELIEF,
        severity=ConsistencySeverity.LOW.value,
        attribute=attribute,
        old_value=first_value,
        new_value=second_value,
        evidence_old=_evidence_text(old_entry.fact),
        evidence_new=_evidence_text(new_entry.fact),
    )


def _detect_contradiction(
    attribute: str,
    entries: list[SemanticEvidenceEntry],
) -> ConsistencyIssue | None:
    weights = _weights_by_value(entries)
    ranked = sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) < 2:
        return None

    (value_a, weight_a), (value_b, weight_b) = ranked[0], ranked[1]
    if not _values_incompatible(value_a, value_b):
        return None

    balance = min(weight_a, weight_b) / max(weight_a, weight_b)
    if balance < AMBIGUITY_BALANCE_THRESHOLD:
        return None

    old_entry = _first_entry_for_value(entries, value_a)
    new_entry = _first_entry_for_value(entries, value_b)

    return ConsistencyIssue(
        type=CONTRADICTION,
        severity=ConsistencySeverity.HIGH.value,
        attribute=attribute,
        old_value=value_a,
        new_value=value_b,
        evidence_old=_evidence_text(old_entry.fact),
        evidence_new=_evidence_text(new_entry.fact),
    )


def _detect_ambiguity(
    attribute: str,
    entries: list[SemanticEvidenceEntry],
) -> ConsistencyIssue | None:
    weights = _weights_by_value(entries)
    ranked = sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) < 2:
        return None

    (value_a, weight_a), (value_b, weight_b) = ranked[0], ranked[1]
    if _values_incompatible(value_a, value_b):
        return None

    balance = min(weight_a, weight_b) / max(weight_a, weight_b)
    if balance < AMBIGUITY_BALANCE_THRESHOLD:
        return None

    old_entry = _first_entry_for_value(entries, value_a)
    new_entry = _first_entry_for_value(entries, value_b)

    return ConsistencyIssue(
        type=AMBIGUITY,
        severity=ConsistencySeverity.MEDIUM.value,
        attribute=attribute,
        old_value=value_a,
        new_value=value_b,
        evidence_old=_evidence_text(old_entry.fact),
        evidence_new=_evidence_text(new_entry.fact),
    )


def _weights_by_value(entries: list[SemanticEvidenceEntry]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for entry in entries:
        value = entry.fact.value
        weights[value] = weights.get(value, 0.0) + _effective_confidence(entry.fact)
    return weights


def _dominant_value(entries: list[SemanticEvidenceEntry]) -> tuple[str, float]:
    weights = _weights_by_value(entries)
    value = sorted(weights.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return value, weights[value]


def _first_entry_for_value(
    entries: list[SemanticEvidenceEntry],
    value: str,
) -> SemanticEvidenceEntry:
    for entry in entries:
        if entry.fact.value == value:
            return entry
    return entries[0]


def _last_entry_for_value(
    entries: list[SemanticEvidenceEntry],
    value: str,
) -> SemanticEvidenceEntry:
    for entry in reversed(entries):
        if entry.fact.value == value:
            return entry
    return entries[-1]


def _values_incompatible(left: str, right: str) -> bool:
    if left == right:
        return False
    return frozenset({left, right}) in INCOMPATIBLE_VALUE_PAIRS


def _effective_confidence(fact: SemanticFact) -> float:
    if fact.confidence is None:
        return DEFAULT_CONFIDENCE
    return fact.confidence


def _evidence_text(fact: SemanticFact) -> str:
    return fact.evidence or ""


def _observation_line(issue: ConsistencyIssue) -> str:
    label = ATTRIBUTE_LABELS.get(issue.attribute, issue.attribute.replace("_", " ").title())

    if issue.type == EVOLVING_BELIEF:
        direction = "more negative" if issue.new_value in NEGATIVE_VALUES else "more positive"
        if issue.attribute == "identity" and issue.new_value == "unclear":
            direction = "less clear"
        if issue.attribute in {"identity", "reaction_to_criticism"} and issue.new_value == "strong":
            direction = "stronger"
        return f"{label} statements became {direction} during the interview."

    if issue.type == CONTRADICTION:
        return f"{label} statements were inconsistent."

    if issue.type == AMBIGUITY:
        return f"{label} statements were mixed and remain uncertain."

    return f"{label} statements showed a consistency note."
