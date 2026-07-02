from __future__ import annotations

from niros.knowledge import PatternLoader
from niros.patterns import PatternTag

PATTERN_INTERPRETATIONS: dict[str, str] = {
    "identity_uncertainty": (
        "The person shows signs of unstable self-definition and difficulty "
        "knowing who they are or what is truly their own."
    ),
    "low_self_efficacy": (
        "The person shows reduced confidence in their ability to influence "
        "outcomes through their own actions."
    ),
    "self_worth_instability": (
        "The person's sense of value appears reactive to achievement, approval, "
        "criticism, rejection, or comparison."
    ),
    "perfectionism": (
        "The person appears to link safety or worth with flawless performance."
    ),
    "harsh_self_criticism": (
        "The person shows a tendency to attack themselves internally after "
        "mistakes or perceived failures."
    ),
    "shame_sensitivity": (
        "The person appears sensitive to criticism, exposure, or signs of "
        "personal defectiveness."
    ),
}

NO_EVIDENCE_PROFILE_TEXT = (
    "There is not enough evidence yet to describe a clear psychological profile."
)
GENERIC_PATTERN_TEXT = "The person shows repeated evidence for this pattern."


def build_human_profile_summary(detected_patterns: list[PatternTag]) -> dict:
    pattern_counts, max_confidence = _aggregate_patterns(detected_patterns)

    if not pattern_counts:
        return {
            "primary_pattern": None,
            "secondary_patterns": [],
            "pattern_counts": {},
            "profile_text": NO_EVIDENCE_PROFILE_TEXT,
        }

    loader = PatternLoader()
    ranked = _rank_patterns(pattern_counts, max_confidence)
    primary_id = ranked[0]
    secondary_ids = ranked[1:]

    primary_pattern = _pattern_summary(loader, primary_id, pattern_counts, max_confidence)
    secondary_patterns = [
        _pattern_summary(loader, pattern_id, pattern_counts, max_confidence)
        for pattern_id in secondary_ids
    ]

    profile_parts = [_interpretation_text(primary_id)]
    profile_parts.extend(_interpretation_text(pattern_id) for pattern_id in secondary_ids)

    return {
        "primary_pattern": primary_pattern,
        "secondary_patterns": secondary_patterns,
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "profile_text": " ".join(profile_parts),
    }


def _aggregate_patterns(
    detected_patterns: list[PatternTag],
) -> tuple[dict[str, int], dict[str, float]]:
    pattern_counts: dict[str, int] = {}
    max_confidence: dict[str, float] = {}

    for tag in detected_patterns:
        pattern_counts[tag.canonical_id] = pattern_counts.get(tag.canonical_id, 0) + 1
        current = max_confidence.get(tag.canonical_id, 0.0)
        if tag.confidence > current:
            max_confidence[tag.canonical_id] = tag.confidence

    return pattern_counts, max_confidence


def _rank_patterns(
    pattern_counts: dict[str, int],
    max_confidence: dict[str, float],
) -> list[str]:
    return sorted(
        pattern_counts,
        key=lambda pattern_id: (pattern_counts[pattern_id], max_confidence[pattern_id]),
        reverse=True,
    )


def _pattern_summary(
    loader: PatternLoader,
    pattern_id: str,
    pattern_counts: dict[str, int],
    max_confidence: dict[str, float],
) -> dict[str, str | int | float]:
    pattern = loader.load(pattern_id)
    return {
        "canonical_id": pattern_id,
        "name": pattern.name,
        "count": pattern_counts[pattern_id],
        "confidence": max_confidence[pattern_id],
    }


def _interpretation_text(pattern_id: str) -> str:
    return PATTERN_INTERPRETATIONS.get(pattern_id, GENERIC_PATTERN_TEXT)
