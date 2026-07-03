from __future__ import annotations

from dataclasses import dataclass

from niros.knowledge import PatternLoader
from niros.models import InterviewPhase, InterviewState

TRACKED_DOMAINS = frozenset(
    {
        "relationships",
        "self_concept",
        "emotion_regulation",
    }
)
RESOLVED_HYPOTHESIS_CONFIDENCE = 0.65
DEPTH_TARGET_EVIDENCE_COUNT = 3


@dataclass(frozen=True)
class InterviewQualityMetrics:
    coverage_score: float
    evidence_depth_score: float
    unresolved_hypotheses_count: int
    repeated_topic_count: int
    confidence_score: float
    overall_score: float


def calculate_interview_quality(
    interview_state: InterviewState,
    human_profile: dict,
) -> InterviewQualityMetrics:
    pattern_counts: dict[str, int] = human_profile.get("pattern_counts", {})
    domains_with_evidence = _domains_with_evidence(pattern_counts)

    coverage_score = _coverage_score(domains_with_evidence)
    evidence_depth_score = _evidence_depth_score(pattern_counts)
    unresolved_hypotheses_count = _unresolved_hypotheses_count(interview_state)
    repeated_topic_count = _repeated_topic_count(pattern_counts)
    confidence_score = _confidence_score(human_profile)
    overall_score = _overall_score(
        coverage_score=coverage_score,
        evidence_depth_score=evidence_depth_score,
        confidence_score=confidence_score,
        unresolved_hypotheses_count=unresolved_hypotheses_count,
        repeated_topic_count=repeated_topic_count,
    )

    return InterviewQualityMetrics(
        coverage_score=coverage_score,
        evidence_depth_score=evidence_depth_score,
        unresolved_hypotheses_count=unresolved_hypotheses_count,
        repeated_topic_count=repeated_topic_count,
        confidence_score=confidence_score,
        overall_score=overall_score,
    )


def _domains_with_evidence(pattern_counts: dict[str, int]) -> set[str]:
    if not pattern_counts:
        return set()

    loader = PatternLoader()
    domains: set[str] = set()
    for pattern_id in pattern_counts:
        pattern = loader.load(pattern_id)
        if pattern.domain in TRACKED_DOMAINS:
            domains.add(pattern.domain)
    return domains


def _coverage_score(domains_with_evidence: set[str]) -> float:
    if not TRACKED_DOMAINS:
        return 0.0
    return len(domains_with_evidence) / len(TRACKED_DOMAINS)


def _evidence_depth_score(pattern_counts: dict[str, int]) -> float:
    if not pattern_counts:
        return 0.0

    depth_values = [
        min(count / DEPTH_TARGET_EVIDENCE_COUNT, 1.0) for count in pattern_counts.values()
    ]
    return sum(depth_values) / len(depth_values)


def _unresolved_hypotheses_count(interview_state: InterviewState) -> int:
    unresolved = 0
    for hypothesis in interview_state.current_hypotheses:
        if hypothesis.get("resolved") is True:
            continue
        confidence = float(hypothesis.get("confidence", 0.0))
        if confidence >= RESOLVED_HYPOTHESIS_CONFIDENCE:
            continue
        unresolved += 1
    return unresolved


def _repeated_topic_count(pattern_counts: dict[str, int]) -> int:
    return sum(1 for count in pattern_counts.values() if count >= 2)


def _confidence_score(human_profile: dict) -> float:
    confidences: list[float] = []
    primary = human_profile.get("primary_pattern")
    if primary is not None:
        confidences.append(float(primary["confidence"]))

    for pattern in human_profile.get("secondary_patterns", []):
        confidences.append(float(pattern["confidence"]))

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)


def _overall_score(
    *,
    coverage_score: float,
    evidence_depth_score: float,
    confidence_score: float,
    unresolved_hypotheses_count: int,
    repeated_topic_count: int,
) -> float:
    unresolved_penalty = min(unresolved_hypotheses_count * 0.15, 0.45)
    repeated_penalty = min(repeated_topic_count * 0.10, 0.30)

    raw_score = (
        0.30 * coverage_score
        + 0.30 * evidence_depth_score
        + 0.25 * confidence_score
        - unresolved_penalty
        - repeated_penalty
    )
    return max(0.0, min(raw_score, 1.0))


def empty_interview_state(session_id: str = "session-quality-001") -> InterviewState:
    return InterviewState(
        session_id=session_id,
        state=InterviewPhase.FREE_NARRATIVE,
        turn_count=0,
    )
