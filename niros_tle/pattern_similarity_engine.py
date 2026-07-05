"""Deterministic Pattern Similarity Engine — cluster candidate mechanisms before human review."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from niros_tle.candidate_pattern_builder import CandidatePattern

DEFAULT_SIMILARITY_THRESHOLD = 0.72

STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "for",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "this",
        "to",
        "with",
    }
)

TOKEN_GROUPS: dict[str, frozenset[str]] = {
    "accept": frozenset(
        {
            "accept",
            "accepted",
            "acceptance",
            "allow",
            "allowed",
            "permit",
            "let",
            "present",
            "presence",
            "be",
        }
    ),
    "emotion": frozenset(
        {
            "emotion",
            "emotions",
            "feeling",
            "feelings",
            "experience",
            "experiences",
            "internal",
        }
    ),
    "difficult": frozenset(
        {
            "difficult",
            "painful",
            "unwanted",
            "hard",
            "distress",
            "struggle",
        }
    ),
    "values": frozenset({"values", "value", "personal", "clarify", "clarification"}),
    "activation": frozenset({"activation", "behavioral", "action", "activate", "increase"}),
    "attachment": frozenset({"attachment", "repair", "rupture", "relationship", "bond"}),
}


@dataclass(frozen=True)
class SimilarityInputPattern:
    pattern_id: str
    source_family: str
    label: str
    mechanism_description: str
    therapeutic_intent: str = ""

    @classmethod
    def from_candidate_pattern(cls, pattern: CandidatePattern) -> SimilarityInputPattern:
        evidence_summaries = " ".join(
            item.get("summary", "") for item in pattern.supporting_evidence
        )
        function_text = " ".join(
            function.replace("_", " ") for function in pattern.psychological_functions
        )
        mechanism_parts = [
            pattern.proposed_name,
            function_text,
            evidence_summaries,
        ]
        mechanism_description = " ".join(
            part.strip() for part in mechanism_parts if part and part.strip()
        )
        return cls(
            pattern_id=pattern.candidate_id,
            source_family=pattern.source_family,
            label=pattern.proposed_name,
            mechanism_description=mechanism_description or pattern.proposed_name,
            therapeutic_intent=pattern.therapeutic_goal,
        )


@dataclass(frozen=True)
class SimilarityMatch:
    pattern_id: str
    source_family: str
    label: str
    similarity_score: float


@dataclass(frozen=True)
class SimilarityCluster:
    cluster_id: str
    representative_label: str
    members: tuple[SimilarityMatch, ...]
    contributing_sources: tuple[str, ...]
    average_similarity: float
    suggested_canonical_name: str


@dataclass(frozen=True)
class PatternSimilarityEngine:
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD

    def cluster(
        self,
        patterns: Iterable[SimilarityInputPattern],
    ) -> tuple[SimilarityCluster, ...]:
        sorted_patterns = tuple(sorted(patterns, key=lambda item: item.pattern_id))
        if not sorted_patterns:
            return ()

        clusters: list[_MutableCluster] = []
        for pattern in sorted_patterns:
            best_cluster: _MutableCluster | None = None
            best_score = -1.0
            for cluster in clusters:
                score = similarity_score(pattern, cluster.representative)
                if score >= self.threshold and score > best_score:
                    best_cluster = cluster
                    best_score = score
            if best_cluster is None:
                clusters.append(_MutableCluster(representative=pattern))
            else:
                best_cluster.add(pattern, best_score)

        return tuple(
            cluster.finalize(index)
            for index, cluster in enumerate(clusters, start=1)
        )

    def score(
        self,
        left: SimilarityInputPattern,
        right: SimilarityInputPattern,
    ) -> float:
        return similarity_score(left, right)


@dataclass
class _MutableCluster:
    representative: SimilarityInputPattern
    members: list[tuple[SimilarityInputPattern, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.members.append((self.representative, 1.0))

    def add(self, pattern: SimilarityInputPattern, score: float) -> None:
        self.members.append((pattern, score))

    def finalize(self, index: int) -> SimilarityCluster:
        matches = tuple(
            SimilarityMatch(
                pattern_id=pattern.pattern_id,
                source_family=pattern.source_family,
                label=pattern.label,
                similarity_score=round(score, 4),
            )
            for pattern, score in sorted(self.members, key=lambda item: item[0].pattern_id)
        )
        sources = tuple(sorted({match.source_family for match in matches}))
        average_similarity = round(
            sum(match.similarity_score for match in matches) / len(matches),
            4,
        )
        labels = [pattern.label for pattern, _score in self.members]
        suggested = suggested_canonical_name(labels)
        return SimilarityCluster(
            cluster_id=f"similarity_cluster_{index:03d}",
            representative_label=self.representative.label,
            members=matches,
            contributing_sources=sources,
            average_similarity=average_similarity,
            suggested_canonical_name=suggested,
        )


def cluster_patterns(
    candidate_patterns: Iterable[CandidatePattern],
    *,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> tuple[SimilarityCluster, ...]:
    """Cluster candidate therapeutic mechanisms before human review."""
    inputs = tuple(
        SimilarityInputPattern.from_candidate_pattern(pattern)
        for pattern in candidate_patterns
    )
    return PatternSimilarityEngine(threshold=threshold).cluster(inputs)


def similarity_score(
    left: SimilarityInputPattern,
    right: SimilarityInputPattern,
) -> float:
    name_overlap = _token_jaccard(_label_tokens(left.label), _label_tokens(right.label))
    mechanism_overlap = _token_jaccard(
        _text_tokens(left.mechanism_description),
        _text_tokens(right.mechanism_description),
    )
    intent_overlap = _token_jaccard(
        _text_tokens(left.therapeutic_intent),
        _text_tokens(right.therapeutic_intent),
    )

    score = (0.30 * name_overlap) + (0.45 * mechanism_overlap) + (0.25 * intent_overlap)

    if left.source_family != right.source_family and score >= 0.35:
        score += 0.05

    return round(min(score, 1.0), 4)


def suggested_canonical_name(labels: Iterable[str]) -> str:
    normalized_labels = [_normalize_label(label) for label in labels if label.strip()]
    if not normalized_labels:
        return "Unnamed Mechanism"

    counts = Counter(normalized_labels)
    most_common_count = counts.most_common(1)[0][1]
    candidates = sorted(
        label for label, count in counts.items() if count == most_common_count
    )
    return min(candidates, key=lambda label: (len(label.split()), label))


def _normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower())


def _label_tokens(label: str) -> set[str]:
    return _canonical_tokens(_normalize_text(label))


def _text_tokens(text: str) -> set[str]:
    return _canonical_tokens(_normalize_text(text))


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokenize(text: str) -> list[str]:
    return [token for token in _normalize_text(text).split() if token and token not in STOP_WORDS]


def _canonical_tokens(text: str) -> set[str]:
    canonical: set[str] = set()
    for token in _tokenize(text):
        canonical.add(_canonicalize_token(token))
    return canonical


def _canonicalize_token(token: str) -> str:
    for root, group in TOKEN_GROUPS.items():
        if token in group:
            return root
    return token


def _token_jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = left & right
    union = left | right
    return len(intersection) / len(union)
