"""Semantic Therapeutic Relevance Gate — decide whether a chunk contains actionable therapeutic knowledge."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM = "therapeutic_mechanism"
KNOWLEDGE_KIND_INTERVENTION_PRINCIPLE = "intervention_principle"
KNOWLEDGE_KIND_EXERCISE_OR_PRACTICE = "exercise_or_practice"
KNOWLEDGE_KIND_CLINICAL_CONTRAINDICATION = "clinical_contraindication"
KNOWLEDGE_KIND_CASE_EXAMPLE = "case_example"
KNOWLEDGE_KIND_THEORETICAL_BACKGROUND = "theoretical_background"
KNOWLEDGE_KIND_FRONT_MATTER = "front_matter"
KNOWLEDGE_KIND_MARKETING = "marketing"
KNOWLEDGE_KIND_STATISTICS_ONLY = "statistics_only"
KNOWLEDGE_KIND_BIBLIOGRAPHY = "bibliography"
KNOWLEDGE_KIND_UNKNOWN = "unknown"

SKIP_REASON_FRONT_MATTER = "front_matter"
SKIP_REASON_MARKETING = "marketing"
SKIP_REASON_STATISTICS_ONLY = "statistics_only"
SKIP_REASON_GENERIC_OVERVIEW = "generic_overview"
SKIP_REASON_KEYWORD_ONLY = "keyword_only"
SKIP_REASON_NO_ACTIONABLE_MECHANISM = "no_actionable_mechanism"
SKIP_REASON_CASE_EXAMPLE_WITHOUT_MECHANISM = "case_example_without_mechanism"
SKIP_REASON_BIBLIOGRAPHY = "bibliography"
SKIP_REASON_LLM_REJECTED = "llm_rejected"

RELEVANCE_HIGH = "high"
RELEVANCE_MEDIUM = "medium"
RELEVANCE_LOW = "low"

KEYWORD_TRAP_TERMS: frozenset[str] = frozenset(
    {
        "acceptance",
        "values",
        "mindfulness",
        "defusion",
        "act",
        "pain",
        "anxiety",
        "happiness",
        "suffering",
        "psychological flexibility",
    }
)

EXPLANATORY_SIGNALS: tuple[str, ...] = (
    r"\bbecause\b",
    r"\bwhen\b",
    r"\bhow\b",
    r"\bwhy\b",
    r"\bleads to\b",
    r"\bresults in\b",
    r"\binstead of\b",
    r"\brather than\b",
    r"\bpractice\b",
    r"\bexercise\b",
    r"\bclient\b",
    r"\bpatient\b",
    r"\bmechanism\b",
    r"\bprocess\b",
    r"\bintervention\b",
    r"\bprinciple\b",
    r"\bshort-term\b",
    r"\blong-term\b",
    r"\bavoidance\b",
    r"\bexperiential\b",
    r"\bthoughts as thoughts\b",
    r"\bunhook\b",
    r"\bdefusion\b",
    r"\bcommitted action\b",
    r"\bvalued action\b",
    r"\binternal experience\b",
)

FRONT_MATTER_PATTERNS: tuple[str, ...] = (
    r"\bcopyright\b",
    r"\bisbn\b",
    r"all rights reserved",
    r"table of contents",
    r"^\s*contents\s*$",
    r"published by",
    r"library of congress",
    r"title page",
    r"front cover",
    r"back cover",
)

MARKETING_PATTERNS: tuple[str, ...] = (
    r"this book helps",
    r"this workbook provides",
    r"readers will learn",
    r"bestselling author",
    r"endorsement",
    r"praise for this book",
    r"in this book you will",
)

GENERIC_OVERVIEW_PATTERNS: tuple[str, ...] = (
    r"overview of",
    r"introduction to act",
    r"what is act",
    r"this chapter introduces",
    r"the purpose of this book",
    r"this book explores",
)

BIBLIOGRAPHY_PATTERNS: tuple[str, ...] = (
    r"\bbibliography\b",
    r"\breferences\b",
    r"\bworks cited\b",
)

CASE_EXAMPLE_PATTERNS: tuple[str, ...] = (
    r"\bfor example, a client\b",
    r"\bfor example, a patient\b",
    r"\bfor example, one client\b",
    r"\bone client\b",
    r"\bcase example\b",
)

MIN_CASE_EXAMPLE_MECHANISM_SCORE = 3

STATISTICS_PATTERNS: tuple[str, ...] = (
    r"\b\d+\s*%\s+of (?:people|patients|participants|respondents)\b",
    r"\bstudies show that \d+",
    r"\bmeta-analysis\b",
    r"\bprevalence\b",
    r"\bepidemiological\b",
)


@dataclass(frozen=True)
class TherapeuticRelevanceDecision:
    chunk_id: str
    source_id: str
    is_relevant: bool
    relevance_score: float
    knowledge_kind: str
    reasoning: str
    evidence_span: str
    skip_reason: str
    suggested_mechanisms: tuple[str, ...]
    should_extract: bool

    @property
    def relevance_band(self) -> str:
        if self.relevance_score >= 0.75:
            return RELEVANCE_HIGH
        if self.relevance_score >= 0.5:
            return RELEVANCE_MEDIUM
        return RELEVANCE_LOW


def evaluate_chunk_relevance(
    *,
    source_id: str,
    chunk_id: str,
    text: str,
) -> TherapeuticRelevanceDecision:
    """Deterministically evaluate whether one chunk should proceed to extraction."""
    normalized = re.sub(r"\s+", " ", text.strip())
    lowered = normalized.lower()
    evidence_span = _evidence_span(normalized)

    if _matches_any(lowered, FRONT_MATTER_PATTERNS):
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_FRONT_MATTER,
            skip_reason=SKIP_REASON_FRONT_MATTER,
            reasoning="Chunk appears to be front matter such as copyright, ISBN, or table of contents.",
            evidence_span=evidence_span,
        )

    if _matches_any(lowered, BIBLIOGRAPHY_PATTERNS):
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_BIBLIOGRAPHY,
            skip_reason=SKIP_REASON_BIBLIOGRAPHY,
            reasoning="Chunk appears to be bibliography or references without therapeutic mechanism content.",
            evidence_span=evidence_span,
        )

    if _matches_any(lowered, MARKETING_PATTERNS):
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_MARKETING,
            skip_reason=SKIP_REASON_MARKETING,
            reasoning="Chunk reads like marketing or promotional copy rather than actionable therapeutic knowledge.",
            evidence_span=evidence_span,
        )

    if _matches_any(lowered, GENERIC_OVERVIEW_PATTERNS) and not _has_explanatory_signals(lowered):
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_UNKNOWN,
            skip_reason=SKIP_REASON_GENERIC_OVERVIEW,
            reasoning="Chunk is a generic book or chapter overview without an explained change process.",
            evidence_span=evidence_span,
        )

    if _is_statistics_only(lowered):
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_STATISTICS_ONLY,
            skip_reason=SKIP_REASON_STATISTICS_ONLY,
            reasoning="Chunk contains statistics or prevalence data without intervention logic.",
            evidence_span=evidence_span,
        )

    if _is_keyword_only(lowered):
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_UNKNOWN,
            skip_reason=SKIP_REASON_KEYWORD_ONLY,
            reasoning="Chunk mentions ACT-related terms but does not explain what changes, why, or how.",
            evidence_span=evidence_span,
            suggested_mechanisms=_suggested_mechanisms(lowered),
        )

    mechanism_score = _mechanism_score(lowered)
    if _is_vague_case_example(lowered, mechanism_score):
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_CASE_EXAMPLE,
            skip_reason=SKIP_REASON_NO_ACTIONABLE_MECHANISM,
            reasoning=(
                "Case example names client state without explaining a therapeutic mechanism, "
                "intervention, change process, or consequence chain."
            ),
            evidence_span=evidence_span,
        )
    if mechanism_score <= 0:
        return _skip_decision(
            source_id=source_id,
            chunk_id=chunk_id,
            knowledge_kind=KNOWLEDGE_KIND_UNKNOWN,
            skip_reason=SKIP_REASON_NO_ACTIONABLE_MECHANISM,
            reasoning="Chunk lacks an actionable therapeutic mechanism, practice, or change process.",
            evidence_span=evidence_span,
        )

    knowledge_kind, reasoning, suggested = _classify_relevant_kind(lowered, mechanism_score)
    relevance_score = min(0.95, 0.55 + mechanism_score * 0.1)

    return TherapeuticRelevanceDecision(
        chunk_id=chunk_id,
        source_id=source_id,
        is_relevant=True,
        relevance_score=round(relevance_score, 3),
        knowledge_kind=knowledge_kind,
        reasoning=reasoning,
        evidence_span=evidence_span,
        skip_reason="",
        suggested_mechanisms=suggested,
        should_extract=True,
    )


def parse_relevance_decision_json(
    data: dict[str, Any],
    *,
    source_id: str,
    chunk_id: str,
    fallback_text: str,
) -> TherapeuticRelevanceDecision:
    """Build a TherapeuticRelevanceDecision from LLM JSON fields."""
    should_extract = bool(data.get("should_extract", data.get("is_relevant", False)))
    relevance_score = float(data.get("relevance_score", 0.0))
    knowledge_kind = str(data.get("knowledge_kind", KNOWLEDGE_KIND_UNKNOWN)).strip() or KNOWLEDGE_KIND_UNKNOWN
    reasoning = str(data.get("reasoning", "")).strip()
    evidence_span = str(data.get("evidence_span", "")).strip() or _evidence_span(fallback_text)
    skip_reason = str(data.get("skip_reason", "")).strip()
    if not should_extract and not skip_reason:
        skip_reason = SKIP_REASON_LLM_REJECTED
    suggested = tuple(
        str(item).strip()
        for item in data.get("suggested_mechanisms", ())
        if str(item).strip()
    )
    return TherapeuticRelevanceDecision(
        chunk_id=chunk_id,
        source_id=source_id,
        is_relevant=should_extract,
        relevance_score=max(0.0, min(relevance_score, 1.0)),
        knowledge_kind=knowledge_kind,
        reasoning=reasoning,
        evidence_span=evidence_span,
        skip_reason=skip_reason,
        suggested_mechanisms=suggested,
        should_extract=should_extract,
    )


def serialize_relevance_decision(decision: TherapeuticRelevanceDecision) -> dict[str, Any]:
    payload = asdict(decision)
    payload["suggested_mechanisms"] = list(decision.suggested_mechanisms)
    payload["relevance_band"] = decision.relevance_band
    payload["gate_reasoning"] = decision.reasoning
    payload["why_extracted"] = why_extracted_text(decision)
    return payload


def why_extracted_text(decision: TherapeuticRelevanceDecision) -> str:
    if not decision.should_extract:
        return decision.reasoning or decision.skip_reason
    if decision.reasoning:
        return decision.reasoning
    return (
        f"This chunk was extracted because it contains actionable "
        f"{decision.knowledge_kind.replace('_', ' ')} content."
    )


def _skip_decision(
    *,
    source_id: str,
    chunk_id: str,
    knowledge_kind: str,
    skip_reason: str,
    reasoning: str,
    evidence_span: str,
    suggested_mechanisms: tuple[str, ...] = (),
) -> TherapeuticRelevanceDecision:
    return TherapeuticRelevanceDecision(
        chunk_id=chunk_id,
        source_id=source_id,
        is_relevant=False,
        relevance_score=0.0,
        knowledge_kind=knowledge_kind,
        reasoning=reasoning,
        evidence_span=evidence_span,
        skip_reason=skip_reason,
        suggested_mechanisms=suggested_mechanisms,
        should_extract=False,
    )


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _has_explanatory_signals(text: str) -> bool:
    return sum(1 for pattern in EXPLANATORY_SIGNALS if re.search(pattern, text)) >= 2


def _is_statistics_only(text: str) -> bool:
    if not _matches_any(text, STATISTICS_PATTERNS):
        return False
    return not _has_explanatory_signals(text)


def _is_vague_case_example(text: str, mechanism_score: int) -> bool:
    if not _matches_any(text, CASE_EXAMPLE_PATTERNS):
        return False
    return mechanism_score < MIN_CASE_EXAMPLE_MECHANISM_SCORE


def _is_keyword_only(text: str) -> bool:
    has_keywords = any(re.search(rf"\b{re.escape(term)}\b", text) for term in KEYWORD_TRAP_TERMS)
    if not has_keywords:
        return False
    word_count = len(text.split())
    if word_count > 80 and _has_explanatory_signals(text):
        return False
    return not _has_explanatory_signals(text)


def _mechanism_score(text: str) -> int:
    score = sum(1 for pattern in EXPLANATORY_SIGNALS if re.search(pattern, text))
    if "experiential avoidance" in text:
        score += 2
    if "cognitive defusion" in text or "defusion" in text:
        score += 2
    if "committed action" in text or "valued action" in text:
        score += 2
    if re.search(r"\b(exercise|practice|homework)\b", text):
        score += 2
    return score


def _classify_relevant_kind(
    text: str,
    mechanism_score: int,
) -> tuple[str, str, tuple[str, ...]]:
    suggested = _suggested_mechanisms(text)
    if re.search(r"\b(contraindication|avoid if|not appropriate when|risk of)\b", text):
        return (
            KNOWLEDGE_KIND_CLINICAL_CONTRAINDICATION,
            "Chunk explains a clinical risk, contraindication, or caution relevant to intervention choice.",
            suggested,
        )
    if re.search(r"\b(exercise|practice|homework|try this|notice|observe your)\b", text):
        return (
            KNOWLEDGE_KIND_EXERCISE_OR_PRACTICE,
            "Chunk describes a concrete therapeutic exercise or practice with actionable steps.",
            suggested,
        )
    if "experiential avoidance" in text or ("avoid" in text and "short-term" in text):
        return (
            KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
            (
                "Chunk explains experiential avoidance as a process where attempts to avoid "
                "painful internal experiences reduce short-term distress but increase long-term "
                "suffering and move the person away from valued action."
            ),
            suggested,
        )
    if "defusion" in text or "thoughts as thoughts" in text or "unhook" in text:
        return (
            KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
            "Chunk explains cognitive defusion as a mechanism for changing the relationship to thoughts rather than changing thought content.",
            suggested,
        )
    if re.search(r"\b(case example|for example, a client|one client)\b", text) and mechanism_score >= 3:
        return (
            KNOWLEDGE_KIND_CASE_EXAMPLE,
            "Case example explicitly illustrates a therapeutic mechanism rather than only naming it.",
            suggested,
        )
    if re.search(r"\b(theory|model|framework|background)\b", text) and mechanism_score >= 2:
        return (
            KNOWLEDGE_KIND_THEORETICAL_BACKGROUND,
            "Theoretical background directly supports understanding of a therapeutic mechanism.",
            suggested,
        )
    if re.search(r"\b(principle|guideline|approach)\b", text):
        return (
            KNOWLEDGE_KIND_INTERVENTION_PRINCIPLE,
            "Chunk explains an intervention principle describing how change is supported in session.",
            suggested,
        )
    return (
        KNOWLEDGE_KIND_THERAPEUTIC_MECHANISM,
        "Chunk explains a therapeutic mechanism with enough process detail to be actionable for NIROS.",
        suggested,
    )


def _suggested_mechanisms(text: str) -> tuple[str, ...]:
    suggestions: list[str] = []
    if "accept" in text or "allow" in text or "willingness" in text:
        suggestions.append("acceptance")
    if "defusion" in text or "unhook" in text or "thoughts as thoughts" in text:
        suggestions.append("defusion")
    if "avoid" in text or "experiential avoidance" in text or "control strateg" in text:
        suggestions.append("experiential_avoidance")
    if "values" in text or "committed action" in text:
        suggestions.append("values_committed_action")
    if "mindfulness" in text or "present moment" in text:
        suggestions.append("present_moment")
    return tuple(dict.fromkeys(suggestions))


def _evidence_span(text: str, *, max_chars: int = 240) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."
