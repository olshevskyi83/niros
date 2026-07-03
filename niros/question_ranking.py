from __future__ import annotations

from dataclasses import dataclass

from niros.hypotheses import Hypothesis
from niros.patterns import PatternTag
from niros.questions import QuestionSuggestion

HYPOTHESIS_TARGET_PATTERNS: dict[str, frozenset[str]] = {
    "people_pleasing_pattern": frozenset(
        {
            "people_pleasing",
            "conflict_avoidance",
            "fear_of_disappointing_others",
        }
    ),
}

WEIGHT_INFORMATION_GAIN = 0.35
WEIGHT_EVIDENCE_GAP = 0.25
WEIGHT_NOVELTY = 0.25
WEIGHT_GRAPH_PRIORITY = 0.15


@dataclass(frozen=True)
class QuestionScore:
    information_gain: float
    evidence_gap: float
    novelty: float
    graph_priority: float
    total_score: float


@dataclass(frozen=True)
class RankedQuestion:
    source_pattern: str
    question: str
    reason: str
    score: QuestionScore
    source_index: int


class QuestionRankingEngine:
    def rank(
        self,
        candidates: list[QuestionSuggestion],
        *,
        pattern_tags: list[PatternTag],
        hypotheses: list[Hypothesis],
        answered_questions: list[str] | None = None,
    ) -> list[RankedQuestion]:
        if not candidates:
            return []

        pattern_counts = _pattern_counts(pattern_tags)
        answered = answered_questions or []
        ranked: list[RankedQuestion] = []

        for index, candidate in enumerate(candidates):
            score = self.score_candidate(
                candidate,
                pattern_counts=pattern_counts,
                hypotheses=hypotheses,
                answered_questions=answered,
            )
            ranked.append(
                RankedQuestion(
                    source_pattern=candidate.source_pattern,
                    question=candidate.question,
                    reason=_score_reason(candidate, score),
                    score=score,
                    source_index=index,
                )
            )

        return sorted(
            ranked,
            key=lambda item: (
                -item.score.total_score,
                item.source_index,
                item.question,
            ),
        )

    def score_candidate(
        self,
        candidate: QuestionSuggestion,
        *,
        pattern_counts: dict[str, int],
        hypotheses: list[Hypothesis],
        answered_questions: list[str],
    ) -> QuestionScore:
        information_gain = _information_gain(candidate.source_pattern, pattern_counts)
        evidence_gap = _evidence_gap(candidate.source_pattern, pattern_counts, hypotheses)
        novelty = _novelty(
            candidate.question,
            candidate.source_pattern,
            pattern_counts,
            answered_questions,
        )
        graph_priority = _graph_priority(candidate)

        total_score = (
            WEIGHT_INFORMATION_GAIN * information_gain
            + WEIGHT_EVIDENCE_GAP * evidence_gap
            + WEIGHT_NOVELTY * novelty
            + WEIGHT_GRAPH_PRIORITY * graph_priority
        )

        return QuestionScore(
            information_gain=information_gain,
            evidence_gap=evidence_gap,
            novelty=novelty,
            graph_priority=graph_priority,
            total_score=total_score,
        )


def format_ranking_debug(ranked_questions: list[RankedQuestion]) -> str:
    if not ranked_questions:
        return "No candidate questions were ranked."

    sections: list[str] = []
    for item in ranked_questions:
        sections.extend(
            [
                f"Question: {item.question}",
                f"Score: {item.score.total_score:.3f}",
                f"Reason: {item.reason}",
                "",
            ]
        )
    return "\n".join(sections).rstrip()


def _pattern_counts(pattern_tags: list[PatternTag]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tag in pattern_tags:
        counts[tag.canonical_id] = counts.get(tag.canonical_id, 0) + 1
    return counts


def _information_gain(source_pattern: str, pattern_counts: dict[str, int]) -> float:
    return 1.0 / (1 + pattern_counts.get(source_pattern, 0))


def _evidence_gap(
    source_pattern: str,
    pattern_counts: dict[str, int],
    hypotheses: list[Hypothesis],
) -> float:
    gap = _information_gain(source_pattern, pattern_counts)

    for hypothesis in hypotheses:
        target_patterns = HYPOTHESIS_TARGET_PATTERNS.get(hypothesis.canonical_id, frozenset())
        if source_pattern in target_patterns:
            gap += 0.5 * hypothesis.confidence

    return min(gap, 1.0)


def _novelty(
    question: str,
    source_pattern: str,
    pattern_counts: dict[str, int],
    answered_questions: list[str],
) -> float:
    if question in answered_questions:
        return 0.0

    if pattern_counts.get(source_pattern, 0) >= 2:
        return 0.2

    return 1.0


def _graph_priority(candidate: QuestionSuggestion) -> float:
    if candidate.reason.startswith("relationship:"):
        return candidate.priority
    return 1.0


def _score_reason(candidate: QuestionSuggestion, score: QuestionScore) -> str:
    return (
        f"{candidate.reason}; "
        f"information_gain={score.information_gain:.2f}, "
        f"evidence_gap={score.evidence_gap:.2f}, "
        f"novelty={score.novelty:.2f}, "
        f"graph_priority={score.graph_priority:.2f}"
    )
