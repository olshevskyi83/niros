"""Knowledge Consolidation Engine — merge semantically equivalent extractions before human review."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.ontology_context import OntologyContext, load_ontology_context
from niros.semantic_knowledge_extraction import (
    ACT_WORDING_SYNONYM_PHRASES,
    ONTOLOGY_STATUS_KNOWN,
    ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    UNKNOWN_MECHANISM_KEY,
    canonical_name_for_mechanism_key,
    collect_extraction_validation_issues,
    detect_act_wording_groups,
    detect_ontology_mechanism_ids,
    has_causal_mechanism_content,
    has_explicit_semantic_knowledge_metadata,
    has_semantic_knowledge_fields,
    is_low_value_knowledge_extraction,
    new_mechanism_key,
    normalize_ontology_status,
    resolve_consolidation_mechanism_key,
    split_extraction_by_ontology_mechanisms,
)
from niros.semantic_mechanism_understanding import (
    UNDERSTANDING_STATUS_POTENTIAL_NEW,
    UNDERSTANDING_STATUS_REJECTED,
    apply_understanding_to_extraction,
    consolidation_mechanism_key_for_understanding,
    split_extraction_into_understandings,
)
from niros.therapeutic_extraction import (
    TherapeuticFunctionExtraction,
)

DEFAULT_PSYCHOTHERAPY_GENERATION_RULES: tuple[str, ...] = (
    "Use the consolidated therapeutic mechanism as a strategy principle.",
)
DEFAULT_PSYCHOTHERAPY_VOICE_RULES: tuple[str, ...] = (
    "Use clear, grounded, non-directive therapeutic language.",
)
DEFAULT_VOCAL_ICARO_VOICE_RULES: tuple[str, ...] = (
    "Use gentle, repetitive, supportive vocal phrasing.",
)

CONSOLIDATED_ID_HASH_LENGTH = 12

REVIEW_MODE_CONSERVATIVE = "conservative"
REVIEW_MODE_NORMAL = "normal"
REVIEW_MODE_AGGRESSIVE = "aggressive"
DEFAULT_REVIEW_MODE = REVIEW_MODE_CONSERVATIVE

FRONT_MATTER_PATTERNS: tuple[str, ...] = (
    r"\bcopyright\b",
    r"\bisbn\b",
    r"all rights reserved",
    r"table of contents",
    r"\bcontents\b",
    r"published by",
    r"publisher",
    r"front cover",
    r"back cover",
    r"endorsement",
    r"\bbibliography\b",
    r"title page",
    r"library of congress",
    r"printed in",
    r"first edition",
    r"second edition",
    r"^\s*page\s+\d+\s*$",
)

VAGUE_BOOK_SUMMARY_PATTERNS: tuple[str, ...] = (
    r"this book helps",
    r"this chapter introduces",
    r"overview of the book",
    r"in this book you will",
    r"this workbook provides",
    r"the purpose of this book",
    r"readers will learn",
)

GENERIC_CONTRAINDICATIONS: frozenset[str] = frozenset(
    {
        "",
        "none",
        "not stated",
        "unknown",
        "n/a",
        "na",
    }
)


@dataclass(frozen=True)
class MechanismClassification:
    mechanism_key: str
    mechanism_family: str
    canonical_mechanism_name: str


@dataclass(frozen=True)
class ConsolidationSourceContext:
    source_id: str
    source_family: str
    domain: str
    title: str = ""


@dataclass(frozen=True)
class EvidenceFragment:
    extraction_id: str
    source_id: str
    segment_id: str
    source_family: str
    domain: str
    therapeutic_function: str
    psychological_function: str
    evidence_text: str
    confidence: float
    mechanism_key: str = UNKNOWN_MECHANISM_KEY
    causal_process: str = ""
    why_this_is_a_mechanism: str = ""


@dataclass(frozen=True)
class ConsolidatedCandidatePattern:
    candidate_id: str
    canonical_name: str
    therapeutic_function: str
    psychological_function: str
    description: str
    mechanism_key: str
    mechanism_family: str
    evidence_fragments: tuple[EvidenceFragment, ...]
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    domains: tuple[str, ...]
    segment_ids: tuple[str, ...]
    source_count: int
    book_count: int
    batch_count: int
    mention_count: int
    confidence_summary: str
    mean_confidence: float
    generation_rules: tuple[str, ...]
    voice_rules: tuple[str, ...]
    repetition_rules: tuple[str, ...]
    pause_rules: tuple[str, ...]
    symbolic_elements: tuple[str, ...]
    candidate_targets: tuple[str, ...]
    contraindications: tuple[str, ...]
    ontology_status: str = ""
    ontology_mechanism_id: str = ""
    causal_process_summary: str = ""
    why_extraction_summary: str = ""


@dataclass(frozen=True)
class ConsolidationResult:
    raw_extractions: int
    filtered_extractions: int
    candidates: tuple[ConsolidatedCandidatePattern, ...]


class KnowledgeConsolidationError(ValueError):
    """Raised when consolidation cannot proceed safely."""


class KnowledgeConsolidator:
    """Merge semantically equivalent therapeutic extractions into candidate patterns."""

    def __init__(self, *, ontology_context: OntologyContext | None = None) -> None:
        self._ontology_context = ontology_context or load_ontology_context()

    def consolidate(
        self,
        extractions: Iterable[TherapeuticFunctionExtraction],
        *,
        source_contexts: dict[str, ConsolidationSourceContext],
        review_mode: str = DEFAULT_REVIEW_MODE,
    ) -> ConsolidationResult:
        members = tuple(extractions)
        if not members:
            return ConsolidationResult(
                raw_extractions=0,
                filtered_extractions=0,
                candidates=(),
            )

        tagged: list[tuple[TherapeuticFunctionExtraction, MechanismClassification]] = []
        filtered_count = 0
        for extraction in members:
            understandings = split_extraction_into_understandings(
                extraction,
                context=self._ontology_context,
            )
            for understanding in understandings:
                if not understanding.should_create_candidate:
                    filtered_count += 1
                    continue
                item = apply_understanding_to_extraction(extraction, understanding)
                mechanism_key, mechanism_family, canonical_name = (
                    consolidation_mechanism_key_for_understanding(
                        understanding,
                        context=self._ontology_context,
                    )
                )
                classification = MechanismClassification(
                    mechanism_key=mechanism_key,
                    mechanism_family=mechanism_family,
                    canonical_mechanism_name=canonical_name,
                )
                if should_filter_extraction(item, classification):
                    filtered_count += 1
                    continue
                if not passes_review_mode(classification, item, review_mode):
                    filtered_count += 1
                    continue
                tagged.append((item, classification))

        grouped: dict[str, list[tuple[TherapeuticFunctionExtraction, MechanismClassification]]] = {}
        for extraction, classification in tagged:
            grouped.setdefault(classification.mechanism_key, []).append(
                (extraction, classification)
            )

        candidates: list[ConsolidatedCandidatePattern] = []
        for mechanism_key in sorted(grouped):
            group = grouped[mechanism_key]
            candidates.append(
                _build_candidate_pattern(
                    group,
                    mechanism_key=mechanism_key,
                    source_contexts=source_contexts,
                    context=self._ontology_context,
                )
            )

        return ConsolidationResult(
            raw_extractions=len(members),
            filtered_extractions=filtered_count,
            candidates=tuple(sorted(candidates, key=lambda item: item.candidate_id)),
        )


def classify_mechanism_identity(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext,
) -> MechanismClassification:
    """Resolve ontology-only mechanism identity for consolidation grouping."""
    mechanism_key, mechanism_family, canonical_name = resolve_consolidation_mechanism_key(
        extraction,
        context=context,
    )
    return MechanismClassification(
        mechanism_key=mechanism_key,
        mechanism_family=mechanism_family,
        canonical_mechanism_name=canonical_name,
    )


def classify_mechanism(extraction: TherapeuticFunctionExtraction) -> MechanismClassification:
    """Return ontology-based mechanism classification for one extraction."""
    return classify_mechanism_identity(extraction, context=load_ontology_context())


def detect_mechanism_keys(text: str) -> tuple[str, ...]:
    """Return ACT wording groups detected in text (normalization helper only)."""
    return detect_act_wording_groups(text)


def split_multi_mechanism_extraction(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext | None = None,
) -> tuple[TherapeuticFunctionExtraction, ...]:
    """Split one extraction into separate ontology mechanism extractions when needed."""
    return split_extraction_by_ontology_mechanisms(
        extraction,
        context=context or load_ontology_context(),
    )


def is_front_matter(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction evidence looks like front/back matter."""
    combined = " ".join(
        (
            extraction.therapeutic_function,
            extraction.psychological_function,
            extraction.evidence_text,
        )
    ).lower()
    matches = sum(1 for pattern in FRONT_MATTER_PATTERNS if re.search(pattern, combined))
    if matches >= 2:
        return True
    if matches == 1 and len(combined.strip()) < 400:
        return True
    if re.fullmatch(r"\s*page\s+\d+\s*", combined.strip()):
        return True
    return False


def is_vague_book_summary(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction is a vague book-level summary."""
    combined = " ".join(
        (
            extraction.therapeutic_function,
            extraction.psychological_function,
            extraction.evidence_text,
        )
    ).lower()
    return any(re.search(pattern, combined) for pattern in VAGUE_BOOK_SUMMARY_PATTERNS)


def should_discard_from_consolidation(
    extraction: TherapeuticFunctionExtraction,
) -> bool:
    """Return True only for extractions that must never become review candidates."""
    if is_front_matter(extraction):
        return True
    if is_vague_book_summary(extraction):
        return True
    if is_low_value_knowledge_extraction(extraction):
        return True
    if normalize_ontology_status(extraction.ontology_status) == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        return False
    if has_explicit_semantic_knowledge_metadata(extraction):
        return not has_causal_mechanism_content(extraction)
    return False


def has_actionable_mechanism(classification: MechanismClassification) -> bool:
    return classification.mechanism_key != UNKNOWN_MECHANISM_KEY


def should_filter_extraction(
    extraction: TherapeuticFunctionExtraction,
    classification: MechanismClassification,
) -> bool:
    del classification
    return should_discard_from_consolidation(extraction)


def passes_review_mode(
    classification: MechanismClassification,
    extraction: TherapeuticFunctionExtraction,
    review_mode: str,
) -> bool:
    del classification, review_mode
    return not should_discard_from_consolidation(extraction)


def contraindications_allow_auto_approve(contraindications: tuple[str, ...]) -> bool:
    if not contraindications:
        return True
    normalized = {item.strip().lower() for item in contraindications}
    return normalized.issubset(GENERIC_CONTRAINDICATIONS)


def candidate_is_auto_approvable(
    candidate: ConsolidatedCandidatePattern,
    *,
    source_type: str,
    knowledge_domain: str,
    auto_approve: bool,
    force_allow_single_evidence: bool = False,
) -> bool:
    if not auto_approve:
        return False
    if source_type != "text":
        return False
    if knowledge_domain != KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE:
        return False
    ontology_ids = frozenset(load_ontology_context().get_known_mechanism_ids())
    if (
        candidate.mechanism_key not in ontology_ids
        and not candidate.ontology_mechanism_id
        and not candidate.mechanism_key.startswith("new_")
    ):
        return False
    if candidate.mechanism_key.startswith("new_"):
        return False
    if candidate.mean_confidence < 0.8:
        return False
    if not contraindications_allow_auto_approve(candidate.contraindications):
        return False
    if candidate.mention_count < 2 and not force_allow_single_evidence:
        return False
    for fragment in candidate.evidence_fragments:
        pseudo = TherapeuticFunctionExtraction(
            extraction_id=fragment.extraction_id,
            source_id=fragment.source_id,
            segment_id=fragment.segment_id,
            therapeutic_function=fragment.therapeutic_function,
            psychological_function=fragment.psychological_function,
            evidence_text=fragment.evidence_text,
            confidence=fragment.confidence,
        )
        if is_front_matter(pseudo) or is_vague_book_summary(pseudo):
            return False
    return True


def build_consolidated_extraction_id(candidate_id: str) -> str:
    digest = hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()[
        :CONSOLIDATED_ID_HASH_LENGTH
    ]
    return f"extraction_candidate_{digest}"


def build_consolidated_review_id(candidate_id: str) -> str:
    digest = hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()[
        :CONSOLIDATED_ID_HASH_LENGTH
    ]
    return f"review_candidate_{digest}"


def build_representative_extraction(
    candidate: ConsolidatedCandidatePattern,
    *,
    knowledge_domain: str = KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
) -> TherapeuticFunctionExtraction:
    anchor = candidate.evidence_fragments[0]
    evidence_text = _merged_evidence_preview(candidate.evidence_fragments)
    extraction_id = build_consolidated_extraction_id(candidate.candidate_id)
    generation_rules = _resolved_generation_rules(candidate, knowledge_domain)
    voice_rules = _resolved_voice_rules(candidate, knowledge_domain)
    causal_process = resolve_representative_causal_process_summary(candidate)
    why_this_is_a_mechanism = resolve_representative_why_extraction_summary(candidate)
    extraction = TherapeuticFunctionExtraction(
        extraction_id=extraction_id,
        source_id=anchor.source_id,
        segment_id=candidate.candidate_id,
        therapeutic_function=candidate.therapeutic_function,
        psychological_function=candidate.psychological_function,
        evidence_text=evidence_text,
        mechanism_name=candidate.canonical_name,
        mechanism_description=candidate.description,
        why_this_is_a_mechanism=why_this_is_a_mechanism,
        causal_process=causal_process,
        ontology_status=candidate.ontology_status,
        ontology_mechanism_id=candidate.ontology_mechanism_id,
        symbolic_elements=candidate.symbolic_elements,
        generation_rules=generation_rules,
        voice_rules=voice_rules,
        repetition_rules=candidate.repetition_rules,
        pause_rules=candidate.pause_rules,
        candidate_targets=candidate.candidate_targets,
        contraindications=candidate.contraindications,
        confidence=candidate.mean_confidence,
        extractor="knowledge_consolidator",
    )
    issues = collect_extraction_validation_issues(extraction)
    if issues:
        joined = "; ".join(issues)
        raise KnowledgeConsolidationError(
            f"Representative extraction failed validation: {joined}"
        )
    return extraction


def serialize_consolidated_candidate(
    candidate: ConsolidatedCandidatePattern,
) -> dict[str, Any]:
    return asdict(candidate)


def deserialize_consolidated_candidate(
    payload: dict[str, Any],
) -> ConsolidatedCandidatePattern:
    fragments = tuple(
        EvidenceFragment(**fragment)
        for fragment in payload.get("evidence_fragments", ())
    )
    return ConsolidatedCandidatePattern(
        candidate_id=payload["candidate_id"],
        canonical_name=payload["canonical_name"],
        therapeutic_function=payload["therapeutic_function"],
        psychological_function=payload["psychological_function"],
        description=payload["description"],
        mechanism_key=payload.get("mechanism_key", UNKNOWN_MECHANISM_KEY),
        mechanism_family=payload.get("mechanism_family", UNKNOWN_MECHANISM_KEY),
        evidence_fragments=fragments,
        source_ids=tuple(payload.get("source_ids", ())),
        source_families=tuple(payload.get("source_families", ())),
        domains=tuple(payload.get("domains", ())),
        segment_ids=tuple(payload.get("segment_ids", ())),
        source_count=int(payload.get("source_count", 0)),
        book_count=int(payload.get("book_count", 0)),
        batch_count=int(payload.get("batch_count", 0)),
        mention_count=int(payload.get("mention_count", 0)),
        confidence_summary=payload.get("confidence_summary", "medium"),
        mean_confidence=float(payload.get("mean_confidence", 0.0)),
        generation_rules=tuple(payload.get("generation_rules", ())),
        voice_rules=tuple(payload.get("voice_rules", ())),
        repetition_rules=tuple(payload.get("repetition_rules", ())),
        pause_rules=tuple(payload.get("pause_rules", ())),
        symbolic_elements=tuple(payload.get("symbolic_elements", ())),
        candidate_targets=tuple(payload.get("candidate_targets", ())),
        contraindications=tuple(payload.get("contraindications", ())),
        ontology_status=str(payload.get("ontology_status", "")),
        ontology_mechanism_id=str(payload.get("ontology_mechanism_id", "")),
        causal_process_summary=str(payload.get("causal_process_summary", "")),
        why_extraction_summary=str(payload.get("why_extraction_summary", "")),
    )


def consolidation_reduction_ratio(
    raw_extractions: int,
    consolidated_candidates: int,
) -> float:
    if raw_extractions <= 0:
        return 0.0
    return 1.0 - (consolidated_candidates / raw_extractions)


def resolve_causal_process_summary(
    extractions: tuple[TherapeuticFunctionExtraction, ...],
    *,
    mechanism_key: str,
    canonical_name: str,
    psychological_function: str,
) -> str:
    """Build consolidated causal process summary from source extractions or safe fallback."""
    causal_values = _unique_joined(
        extraction.causal_process.strip()
        for extraction in extractions
        if extraction.causal_process.strip()
    )
    if causal_values:
        return causal_values
    semantic_reasoning = _unique_joined(
        value
        for extraction in extractions
        for value in (
            extraction.mechanism_description.strip(),
            extraction.psychological_function.strip(),
        )
        if value
    )
    if semantic_reasoning:
        return semantic_reasoning
    return _fallback_causal_process_summary(
        mechanism_key=mechanism_key,
        canonical_name=canonical_name,
        psychological_function=psychological_function,
        evidence_text=_unique_joined(item.evidence_text.strip() for item in extractions),
    )


def resolve_why_extraction_summary(
    extractions: tuple[TherapeuticFunctionExtraction, ...],
    *,
    mechanism_key: str,
    canonical_name: str,
    ontology_status: str,
) -> str:
    """Build consolidated why-summary from source extractions or safe fallback."""
    why_values = _unique_joined(
        extraction.why_this_is_a_mechanism.strip()
        for extraction in extractions
        if extraction.why_this_is_a_mechanism.strip()
    )
    if why_values:
        return why_values
    semantic_reasoning = _unique_joined(
        value
        for extraction in extractions
        for value in (
            extraction.mechanism_description.strip(),
            extraction.psychological_function.strip(),
        )
        if value
    )
    if semantic_reasoning:
        return (
            "This candidate is treated as a therapeutic mechanism because the source "
            f"describes reusable reasoning related to {canonical_name}: {semantic_reasoning}"
        )
    return _fallback_why_extraction_summary(
        mechanism_key=mechanism_key,
        canonical_name=canonical_name,
        ontology_status=ontology_status,
    )


def resolve_representative_causal_process_summary(
    candidate: ConsolidatedCandidatePattern,
) -> str:
    """Resolve causal process summary for representative extraction validation."""
    if candidate.causal_process_summary.strip():
        return candidate.causal_process_summary.strip()
    from_fragments = _unique_joined(
        fragment.causal_process.strip()
        for fragment in candidate.evidence_fragments
        if fragment.causal_process.strip()
    )
    if from_fragments:
        return from_fragments
    from_fragments = _unique_joined(
        fragment.why_this_is_a_mechanism.strip()
        for fragment in candidate.evidence_fragments
        if fragment.why_this_is_a_mechanism.strip()
    )
    if from_fragments:
        return from_fragments
    return _fallback_causal_process_summary(
        mechanism_key=candidate.mechanism_key,
        canonical_name=candidate.canonical_name,
        psychological_function=candidate.psychological_function,
        evidence_text=_merged_evidence_preview(candidate.evidence_fragments),
    )


def resolve_representative_why_extraction_summary(
    candidate: ConsolidatedCandidatePattern,
) -> str:
    """Resolve why-summary for representative extraction validation."""
    if candidate.why_extraction_summary.strip():
        return candidate.why_extraction_summary.strip()
    from_fragments = _unique_joined(
        fragment.why_this_is_a_mechanism.strip()
        for fragment in candidate.evidence_fragments
        if fragment.why_this_is_a_mechanism.strip()
    )
    if from_fragments:
        return from_fragments
    return _fallback_why_extraction_summary(
        mechanism_key=candidate.mechanism_key,
        canonical_name=candidate.canonical_name,
        ontology_status=candidate.ontology_status,
    )


def _fallback_causal_process_summary(
    *,
    mechanism_key: str,
    canonical_name: str,
    psychological_function: str,
    evidence_text: str,
) -> str:
    if mechanism_key == "experiential_avoidance":
        return EXPERIENTIAL_AVOIDANCE_CAUSAL_SUMMARY
    if mechanism_key == "cognitive_fusion":
        return COGNITIVE_FUSION_CAUSAL_SUMMARY
    if "acceptance" in mechanism_key:
        return ACCEPTANCE_CAUSAL_SUMMARY
    if "values" in mechanism_key or "committed_action" in mechanism_key:
        return VALUES_COMMITTED_ACTION_CAUSAL_SUMMARY
    if mechanism_key.startswith("new_") or mechanism_key == UNKNOWN_MECHANISM_KEY:
        return POTENTIAL_NEW_CAUSAL_SUMMARY
    if psychological_function.strip():
        return (
            f"The source evidence describes a maintaining or change process related to "
            f"{canonical_name}: {psychological_function.strip()}"
        )
    preview = evidence_text.strip()
    if preview:
        shortened = preview[:240].rstrip()
        if len(preview) > 240:
            shortened += "..."
        return (
            f"The source evidence describes a reusable process related to {canonical_name}: "
            f"{shortened}"
        )
    return (
        f"The source evidence describes a reusable psychological process related to "
        f"{canonical_name}."
    )


def _fallback_why_extraction_summary(
    *,
    mechanism_key: str,
    canonical_name: str,
    ontology_status: str,
) -> str:
    if mechanism_key == "experiential_avoidance":
        return EXPERIENTIAL_AVOIDANCE_WHY_SUMMARY
    if mechanism_key == "cognitive_fusion":
        return COGNITIVE_FUSION_WHY_SUMMARY
    if "acceptance" in mechanism_key:
        return ACCEPTANCE_WHY_SUMMARY
    if "values" in mechanism_key or "committed_action" in mechanism_key:
        return VALUES_COMMITTED_ACTION_WHY_SUMMARY
    if mechanism_key.startswith("new_"):
        return POTENTIAL_NEW_WHY_SUMMARY
    if ontology_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        return POTENTIAL_NEW_WHY_SUMMARY
    return (
        "This candidate is treated as a therapeutic mechanism because the consolidated "
        f"source evidence appears to describe a reusable causal process related to "
        f"{canonical_name}."
    )


def _build_candidate_pattern(
    group: list[tuple[TherapeuticFunctionExtraction, MechanismClassification]],
    *,
    mechanism_key: str,
    source_contexts: dict[str, ConsolidationSourceContext],
    context: OntologyContext,
) -> ConsolidatedCandidatePattern:
    sorted_group = sorted(group, key=lambda item: item[0].extraction_id)
    classification = sorted_group[0][1]
    extractions = tuple(item[0] for item in sorted_group)
    candidate_id = _candidate_id(mechanism_key)
    fragments = tuple(
        _evidence_fragment(extraction, source_contexts, mechanism_key)
        for extraction in extractions
    )
    source_ids = _unique_preserve_order(fragment.source_id for fragment in fragments)
    source_families = _unique_preserve_order(fragment.source_family for fragment in fragments)
    domains = _unique_preserve_order(fragment.domain for fragment in fragments)
    segment_ids = _unique_preserve_order(fragment.segment_id for fragment in fragments)
    mean_confidence = round(
        sum(fragment.confidence for fragment in fragments) / len(fragments),
        4,
    )
    ontology_mechanism_id = ""
    if mechanism_key in context.get_known_mechanism_ids():
        ontology_mechanism_id = mechanism_key
    else:
        for extraction in extractions:
            if extraction.ontology_mechanism_id.strip():
                ontology_mechanism_id = extraction.ontology_mechanism_id.strip()
                break
    ontology_statuses = _unique_preserve_order(
        extraction.ontology_status.strip()
        for extraction in extractions
        if extraction.ontology_status.strip()
    )
    ontology_status = (
        ontology_statuses[0]
        if len(ontology_statuses) == 1
        else (
            ontology_statuses[0]
            if ontology_statuses
            else (
                ONTOLOGY_STATUS_KNOWN
                if mechanism_key in context.get_known_mechanism_ids()
                else ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM
            )
        )
    )
    if mechanism_key.startswith("new_"):
        ontology_status = ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM
        ontology_mechanism_id = ""
    canonical_name = canonical_name_for_mechanism_key(
        mechanism_key,
        context=context,
        fallback_name=classification.canonical_mechanism_name,
    )
    psychological_function = _unique_joined(
        extraction.psychological_function for extraction in extractions
    )
    causal_process_summary = resolve_causal_process_summary(
        extractions,
        mechanism_key=mechanism_key,
        canonical_name=canonical_name,
        psychological_function=psychological_function,
    )
    why_extraction_summary = resolve_why_extraction_summary(
        extractions,
        mechanism_key=mechanism_key,
        canonical_name=canonical_name,
        ontology_status=ontology_status,
    )
    return ConsolidatedCandidatePattern(
        candidate_id=candidate_id,
        canonical_name=canonical_name,
        therapeutic_function=mechanism_key,
        psychological_function=psychological_function,
        description=_merged_description(extractions, classification),
        mechanism_key=mechanism_key,
        mechanism_family=classification.mechanism_family,
        evidence_fragments=fragments,
        source_ids=source_ids,
        source_families=source_families,
        domains=domains,
        segment_ids=segment_ids,
        source_count=len(source_ids),
        book_count=len(source_ids),
        batch_count=len(segment_ids),
        mention_count=len(fragments),
        confidence_summary=_confidence_summary(mean_confidence),
        mean_confidence=mean_confidence,
        generation_rules=_unique_preserve_order(
            rule for extraction in extractions for rule in extraction.generation_rules
        ),
        voice_rules=_unique_preserve_order(
            rule for extraction in extractions for rule in extraction.voice_rules
        ),
        repetition_rules=_unique_preserve_order(
            rule for extraction in extractions for rule in extraction.repetition_rules
        ),
        pause_rules=_unique_preserve_order(
            rule for extraction in extractions for rule in extraction.pause_rules
        ),
        symbolic_elements=_unique_preserve_order(
            item for extraction in extractions for item in extraction.symbolic_elements
        ),
        candidate_targets=_unique_preserve_order(
            item for extraction in extractions for item in extraction.candidate_targets
        ),
        contraindications=_unique_preserve_order(
            item for extraction in extractions for item in extraction.contraindications
        ),
        ontology_status=ontology_status,
        ontology_mechanism_id=ontology_mechanism_id,
        causal_process_summary=causal_process_summary,
        why_extraction_summary=why_extraction_summary,
    )


def _candidate_id(mechanism_key: str) -> str:
    digest = hashlib.sha256(mechanism_key.encode("utf-8")).hexdigest()[
        :CONSOLIDATED_ID_HASH_LENGTH
    ]
    return f"candidate_{digest}"


def _evidence_fragment(
    extraction: TherapeuticFunctionExtraction,
    source_contexts: dict[str, ConsolidationSourceContext],
    mechanism_key: str,
) -> EvidenceFragment:
    context = source_contexts.get(extraction.source_id)
    return EvidenceFragment(
        extraction_id=extraction.extraction_id,
        source_id=extraction.source_id,
        segment_id=extraction.segment_id,
        source_family=context.source_family if context is not None else "",
        domain=context.domain if context is not None else "",
        therapeutic_function=extraction.therapeutic_function,
        psychological_function=extraction.psychological_function,
        evidence_text=extraction.evidence_text,
        confidence=extraction.confidence,
        mechanism_key=mechanism_key,
        causal_process=extraction.causal_process.strip(),
        why_this_is_a_mechanism=extraction.why_this_is_a_mechanism.strip(),
    )


def _merged_description(
    extractions: tuple[TherapeuticFunctionExtraction, ...],
    classification: MechanismClassification,
) -> str:
    observed = _unique_preserve_order(
        extraction.mechanism_name.strip() or extraction.therapeutic_function.strip()
        for extraction in extractions
        if extraction.mechanism_name.strip() or extraction.therapeutic_function.strip()
    )
    parts = [
        f"Consolidated mechanism: {classification.canonical_mechanism_name}.",
    ]
    if observed:
        parts.append("Observed labels: " + "; ".join(observed) + ".")
    parts.append(
        f"Merged {len(extractions)} extraction(s) across "
        f"{len(_unique_preserve_order(item.source_id for item in extractions))} source(s)."
    )
    return " ".join(parts)


def _resolved_generation_rules(
    candidate: ConsolidatedCandidatePattern,
    knowledge_domain: str,
) -> tuple[str, ...]:
    if candidate.generation_rules:
        return candidate.generation_rules
    return DEFAULT_PSYCHOTHERAPY_GENERATION_RULES


def _resolved_voice_rules(
    candidate: ConsolidatedCandidatePattern,
    knowledge_domain: str,
) -> tuple[str, ...]:
    if candidate.voice_rules:
        return candidate.voice_rules
    if knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO:
        return DEFAULT_VOCAL_ICARO_VOICE_RULES
    return DEFAULT_PSYCHOTHERAPY_VOICE_RULES


def _merged_evidence_preview(
    fragments: tuple[EvidenceFragment, ...],
    *,
    max_fragments: int = 5,
    max_chars: int = 1200,
) -> str:
    lines: list[str] = []
    for index, fragment in enumerate(fragments[:max_fragments], start=1):
        lines.append(
            f"[{index}] {fragment.source_id} / {fragment.segment_id}: "
            f"{fragment.evidence_text.strip()}"
        )
    if len(fragments) > max_fragments:
        lines.append(f"... and {len(fragments) - max_fragments} more evidence fragment(s).")
    preview = "\n\n".join(lines).strip()
    if len(preview) <= max_chars:
        return preview
    return preview[: max_chars - 3].rstrip() + "..."


def _confidence_summary(mean_confidence: float) -> str:
    if mean_confidence >= 0.75:
        return "high"
    if mean_confidence >= 0.5:
        return "medium"
    return "low"


def _unique_joined(values: Iterable[str]) -> str:
    ordered = _unique_preserve_order(value.strip() for value in values if value.strip())
    return "; ".join(ordered)


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


MECHANISM_SYNONYM_PHRASES = ACT_WORDING_SYNONYM_PHRASES
KNOWN_MECHANISM_KEYS = frozenset(load_ontology_context().get_known_mechanism_ids())

EXPERIENTIAL_AVOIDANCE_CAUSAL_SUMMARY = (
    "Attempts to avoid or control painful internal experiences may reduce distress briefly, "
    "but can maintain suffering by narrowing behavior and pulling the person away from "
    "valued action."
)
EXPERIENTIAL_AVOIDANCE_WHY_SUMMARY = (
    "This candidate is treated as a therapeutic mechanism because the source describes a "
    "causal maintaining process linking internal experience, avoidance/control behavior, "
    "and longer-term suffering or reduced valued action."
)
COGNITIVE_FUSION_CAUSAL_SUMMARY = (
    "Cognitive fusion can increase distress when thoughts are treated as literal truths; "
    "defusion changes the person's relationship to thoughts by helping them observe "
    "thoughts as mental events."
)
COGNITIVE_FUSION_WHY_SUMMARY = (
    "This candidate is treated as a therapeutic mechanism because the source describes "
    "how entanglement with thoughts can amplify distress and how changing the relationship "
    "to thoughts can reduce rigid responding."
)
ACCEPTANCE_CAUSAL_SUMMARY = (
    "Acceptance changes the relationship to painful internal experience by making room "
    "for thoughts and feelings rather than escalating struggle against them."
)
ACCEPTANCE_WHY_SUMMARY = (
    "This candidate is treated as a therapeutic mechanism because the source describes "
    "how willingness to experience difficult internal states can reduce struggle and "
    "support more flexible behavior."
)
VALUES_COMMITTED_ACTION_CAUSAL_SUMMARY = (
    "Values-based action links chosen life directions to concrete behavior, helping the "
    "person move toward meaning even when difficult internal experiences are present."
)
VALUES_COMMITTED_ACTION_WHY_SUMMARY = (
    "This candidate is treated as a therapeutic mechanism because the source describes "
    "how contact with values can increase willingness to act meaningfully despite "
    "difficult internal experiences."
)
POTENTIAL_NEW_CAUSAL_SUMMARY = (
    "Potential new mechanism inferred from the source evidence; reviewer must verify the "
    "causal process before approval."
)
POTENTIAL_NEW_WHY_SUMMARY = (
    "This candidate is marked as a potential new mechanism because the source appears to "
    "describe a reusable psychological change or maintaining process that is not yet "
    "covered by the current ontology."
)
