"""Semantic mechanism understanding — ontology-guided interpretation of extracted knowledge."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from niros.ontology_context import OntologyContext, load_ontology_context
from niros.ontology_markdown import (
    ENTITY_TYPE_MECHANISM,
    OntologyMarkdownDocument,
    mechanism_semantic_corpus,
    slugify_ontology_title,
)
from niros.semantic_knowledge_extraction import (
    ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
    ONTOLOGY_STATUS_ADDS_NEW_NUANCE,
    ONTOLOGY_STATUS_CONTRADICTION,
    ONTOLOGY_STATUS_KNOWN,
    ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    detect_ontology_mechanism_ids,
    has_causal_mechanism_content,
    is_chapter_summary_extraction,
    is_definition_only_extraction,
    is_terminology_only_extraction,
    new_mechanism_key,
    normalize_ontology_status,
)
from niros.therapeutic_extraction import TherapeuticFunctionExtraction

UNDERSTANDING_STATUS_CONFIRMS_EXISTING = "confirms_existing_mechanism"
UNDERSTANDING_STATUS_ADDS_NEW_EVIDENCE = "adds_new_evidence"
UNDERSTANDING_STATUS_ADDS_NEW_NUANCE = "adds_new_nuance"
UNDERSTANDING_STATUS_POTENTIAL_NEW = "potential_new_mechanism"
UNDERSTANDING_STATUS_CONTRADICTION = "contradiction"
UNDERSTANDING_STATUS_REJECTED = "rejected"

SUPPORTED_UNDERSTANDING_STATUSES: frozenset[str] = frozenset(
    {
        UNDERSTANDING_STATUS_CONFIRMS_EXISTING,
        UNDERSTANDING_STATUS_ADDS_NEW_EVIDENCE,
        UNDERSTANDING_STATUS_ADDS_NEW_NUANCE,
        UNDERSTANDING_STATUS_POTENTIAL_NEW,
        UNDERSTANDING_STATUS_CONTRADICTION,
        UNDERSTANDING_STATUS_REJECTED,
    }
)

KEYWORD_ONLY_PATTERNS: tuple[str, ...] = (
    r"^\s*(?:acceptance|defusion|mindfulness|values|act|cbt)\s*[.:]?\s*$",
    r"^\s*(?:acceptance|defusion|mindfulness|values)\s+is\s+\w+\s*[.:]?\s*$",
)

MARKETING_PATTERNS: tuple[str, ...] = (
    r"\bthis book helps\b",
    r"\btransform your life\b",
    r"\blife-changing\b",
    r"\bbestseller\b",
    r"\bmust read\b",
    r"\bgroundbreaking approach\b",
)

STATISTICS_ONLY_PATTERNS: tuple[str, ...] = (
    r"^\s*\d+(?:\.\d+)?%\s+of\b",
    r"\baccording to (?:studies|research)\b.*\d+(?:\.\d+)?%",
    r"^\s*\d+\s+participants\b",
)

VAGUE_CASE_EXAMPLE_PATTERNS: tuple[str, ...] = (
    r"\bone client\b.*\bfor example\b",
    r"\bfor instance\b.*\bclient\b",
    r"\ban example\b.*\bclient\b",
)

CAUSAL_EVIDENCE_PATTERNS: tuple[str, ...] = (
    r"\bbecause\b",
    r"\btherefore\b",
    r"\bas a result\b",
    r"\bmaintains?\b",
    r"\bincreases?\b",
    r"\breduces?\b",
    r"\bnarrows?\b",
    r"\bleads to\b",
    r"\bover time\b",
)

MECHANISM_NAME_ONLY_PATTERNS: tuple[str, ...] = (
    r"^\s*(?:acceptance|defusion|mindfulness|values|experiential avoidance|cognitive fusion)\s*[.:]?\s*$",
)

SEMANTIC_MATCH_THRESHOLD = 0.18
SEMANTIC_MATCH_MIN_SHARED_TOKENS = 3

_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "them",
        "they",
        "this",
        "to",
        "was",
        "when",
        "with",
        "without",
    }
)


@dataclass(frozen=True)
class SemanticMechanismUnderstanding:
    source_id: str
    segment_id: str
    mechanism_name: str
    mechanism_description: str
    causal_process: str
    why_this_is_a_mechanism: str
    intervention_principle: str
    evidence_span: str
    ontology_status: str
    ontology_mechanism_id: str
    confidence: float
    should_create_candidate: bool
    rejection_reason: str = ""


@dataclass(frozen=True)
class SemanticMechanismMatch:
    mechanism_id: str
    document_id: str
    canonical_name: str
    score: float
    explicit: bool = False


def build_semantic_mechanism_understanding(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext | None = None,
) -> SemanticMechanismUnderstanding:
    """Interpret one extraction as ontology-guided semantic mechanism understanding."""
    resolved_context = context or load_ontology_context()
    explicit_status = normalize_ontology_status(extraction.ontology_status)
    rejection = _rejection_reason(
        extraction,
        allow_unknown_mechanism=explicit_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    )
    if rejection:
        return _rejected_understanding(extraction, rejection_reason=rejection)

    mechanism_name = (
        extraction.mechanism_name.strip()
        or extraction.therapeutic_function.strip()
    )
    mechanism_description = (
        extraction.mechanism_description.strip()
        or extraction.psychological_function.strip()
    )
    evidence_span = extraction.evidence_text.strip()
    causal_process = extraction.causal_process.strip()
    if not causal_process and _evidence_describes_causal_process(evidence_span):
        causal_process = evidence_span
    why_mechanism = extraction.why_this_is_a_mechanism.strip()
    intervention_principle = _intervention_principle_from_extraction(extraction)

    if explicit_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        return SemanticMechanismUnderstanding(
            source_id=extraction.source_id,
            segment_id=extraction.segment_id,
            mechanism_name=mechanism_name,
            mechanism_description=mechanism_description,
            causal_process=causal_process,
            why_this_is_a_mechanism=why_mechanism,
            intervention_principle=intervention_principle,
            evidence_span=evidence_span,
            ontology_status=UNDERSTANDING_STATUS_POTENTIAL_NEW,
            ontology_mechanism_id="",
            confidence=extraction.confidence,
            should_create_candidate=True,
        )

    if explicit_status == ONTOLOGY_STATUS_CONTRADICTION:
        return SemanticMechanismUnderstanding(
            source_id=extraction.source_id,
            segment_id=extraction.segment_id,
            mechanism_name=mechanism_name,
            mechanism_description=mechanism_description,
            causal_process=causal_process,
            why_this_is_a_mechanism=why_mechanism,
            intervention_principle=intervention_principle,
            evidence_span=evidence_span,
            ontology_status=UNDERSTANDING_STATUS_CONTRADICTION,
            ontology_mechanism_id=extraction.ontology_mechanism_id.strip(),
            confidence=extraction.confidence,
            should_create_candidate=True,
        )

    match = _resolve_semantic_match(extraction, context=resolved_context)
    if match is None:
        return SemanticMechanismUnderstanding(
            source_id=extraction.source_id,
            segment_id=extraction.segment_id,
            mechanism_name=mechanism_name,
            mechanism_description=mechanism_description,
            causal_process=causal_process or mechanism_description,
            why_this_is_a_mechanism=why_mechanism or _default_why_for_new_mechanism(mechanism_name),
            intervention_principle=intervention_principle,
            evidence_span=evidence_span,
            ontology_status=UNDERSTANDING_STATUS_POTENTIAL_NEW,
            ontology_mechanism_id="",
            confidence=extraction.confidence,
            should_create_candidate=True,
        )

    ontology_status = _ontology_status_for_match(
        extraction,
        match=match,
        explicit_status=explicit_status,
    )
    return SemanticMechanismUnderstanding(
        source_id=extraction.source_id,
        segment_id=extraction.segment_id,
        mechanism_name=match.canonical_name or mechanism_name,
        mechanism_description=mechanism_description,
        causal_process=causal_process or _causal_from_match(match, resolved_context),
        why_this_is_a_mechanism=why_mechanism or _why_from_match(match),
        intervention_principle=intervention_principle,
        evidence_span=evidence_span,
        ontology_status=ontology_status,
        ontology_mechanism_id=match.mechanism_id,
        confidence=extraction.confidence,
        should_create_candidate=True,
    )


def split_extraction_into_understandings(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext | None = None,
) -> tuple[SemanticMechanismUnderstanding, ...]:
    """Split one extraction into separate semantic understandings when needed."""
    resolved_context = context or load_ontology_context()
    explicit_status = normalize_ontology_status(extraction.ontology_status)
    if explicit_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        return (build_semantic_mechanism_understanding(extraction, context=resolved_context),)

    detected_ids = detect_ontology_mechanism_ids(extraction, context=resolved_context)
    if len(detected_ids) > 1:
        understandings: list[SemanticMechanismUnderstanding] = []
        for mechanism_id in detected_ids:
            mechanism = resolved_context.get_mechanism_context(mechanism_id)
            enriched = replace(
                extraction,
                extraction_id=f"{extraction.extraction_id}_{mechanism_id}",
                ontology_mechanism_id=mechanism_id,
                mechanism_name=mechanism.name if mechanism is not None else mechanism_id,
                therapeutic_function=mechanism_id,
            )
            understandings.append(
                build_semantic_mechanism_understanding(enriched, context=resolved_context)
            )
        return tuple(understandings)

    matches = _find_semantic_matches(extraction, context=resolved_context)
    if len(matches) > 1:
        understandings = []
        for match in matches:
            enriched = replace(
                extraction,
                extraction_id=f"{extraction.extraction_id}_{match.mechanism_id}",
                ontology_mechanism_id=match.mechanism_id,
                mechanism_name=match.canonical_name,
                therapeutic_function=match.mechanism_id,
            )
            understandings.append(
                build_semantic_mechanism_understanding(enriched, context=resolved_context)
            )
        return tuple(understandings)

    return (build_semantic_mechanism_understanding(extraction, context=resolved_context),)


def apply_understanding_to_extraction(
    extraction: TherapeuticFunctionExtraction,
    understanding: SemanticMechanismUnderstanding,
) -> TherapeuticFunctionExtraction:
    """Copy semantic understanding fields onto one extraction record."""
    return replace(
        extraction,
        mechanism_name=understanding.mechanism_name,
        mechanism_description=understanding.mechanism_description,
        causal_process=understanding.causal_process,
        why_this_is_a_mechanism=understanding.why_this_is_a_mechanism,
        ontology_status=_extraction_ontology_status(understanding.ontology_status),
        ontology_mechanism_id=understanding.ontology_mechanism_id,
        evidence_text=understanding.evidence_span or extraction.evidence_text,
        therapeutic_function=(
            understanding.ontology_mechanism_id
            or new_mechanism_key(understanding.mechanism_name)
        ),
    )


def _extraction_ontology_status(understanding_status: str) -> str:
    if understanding_status == UNDERSTANDING_STATUS_CONFIRMS_EXISTING:
        return ONTOLOGY_STATUS_KNOWN
    if understanding_status == UNDERSTANDING_STATUS_REJECTED:
        return ""
    return understanding_status


def consolidation_mechanism_key_for_understanding(
    understanding: SemanticMechanismUnderstanding,
    *,
    context: OntologyContext | None = None,
) -> tuple[str, str, str]:
    """Return (mechanism_key, mechanism_family, canonical_name) for consolidation."""
    del context
    if understanding.ontology_status == UNDERSTANDING_STATUS_POTENTIAL_NEW:
        name = understanding.mechanism_name.strip()
        mechanism_key = new_mechanism_key(name)
        return mechanism_key, "potential_new", name

    if understanding.ontology_mechanism_id.strip():
        mechanism_id = understanding.ontology_mechanism_id.strip()
        return mechanism_id, mechanism_id, understanding.mechanism_name.strip() or mechanism_id

    name = understanding.mechanism_name.strip()
    if name:
        mechanism_key = new_mechanism_key(name)
        return mechanism_key, "potential_new", name
    return "unknown", "unknown", "Unknown therapeutic mechanism"


def _rejection_reason(
    extraction: TherapeuticFunctionExtraction,
    *,
    allow_unknown_mechanism: bool = False,
) -> str:
    if is_keyword_only_extraction(extraction):
        return "keyword-only text"
    if is_definition_only_extraction(extraction):
        return "definition-only text"
    if is_chapter_summary_extraction(extraction):
        return "chapter summary"
    if is_marketing_extraction(extraction):
        return "marketing text"
    if is_vague_case_example_extraction(extraction):
        return "vague case example"
    if is_statistics_only_extraction(extraction):
        return "statistics-only text"
    if is_mechanism_name_without_process(extraction):
        return "mechanism named without causal process"
    if is_terminology_only_extraction(extraction):
        return "terminology-only text"
    if not allow_unknown_mechanism and not has_explainable_mechanism_content(extraction):
        return "no causal mechanism"
    return ""


def has_explainable_mechanism_content(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction explains a reusable causal mechanism."""
    if has_causal_mechanism_content(extraction):
        return True
    evidence = extraction.evidence_text.strip()
    return len(evidence) >= 80 and _evidence_describes_causal_process(evidence)


def _evidence_describes_causal_process(evidence: str) -> bool:
    lowered = evidence.lower()
    return _matches_any(lowered, CAUSAL_EVIDENCE_PATTERNS)


def _rejected_understanding(
    extraction: TherapeuticFunctionExtraction,
    *,
    rejection_reason: str,
) -> SemanticMechanismUnderstanding:
    return SemanticMechanismUnderstanding(
        source_id=extraction.source_id,
        segment_id=extraction.segment_id,
        mechanism_name=extraction.mechanism_name.strip(),
        mechanism_description=extraction.mechanism_description.strip(),
        causal_process=extraction.causal_process.strip(),
        why_this_is_a_mechanism=extraction.why_this_is_a_mechanism.strip(),
        intervention_principle=_intervention_principle_from_extraction(extraction),
        evidence_span=extraction.evidence_text.strip(),
        ontology_status=UNDERSTANDING_STATUS_REJECTED,
        ontology_mechanism_id="",
        confidence=extraction.confidence,
        should_create_candidate=False,
        rejection_reason=rejection_reason,
    )


def is_keyword_only_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    combined = _combined_text(extraction)
    if any(re.search(pattern, combined) for pattern in KEYWORD_ONLY_PATTERNS):
        return True
    label = (
        extraction.mechanism_name.strip()
        or extraction.therapeutic_function.strip()
    ).lower()
    if len(label.split()) <= 2 and not extraction.causal_process.strip():
        return any(re.search(pattern, label) for pattern in MECHANISM_NAME_ONLY_PATTERNS)
    return False


def is_marketing_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    return _matches_any(_combined_text(extraction), MARKETING_PATTERNS)


def is_statistics_only_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    combined = _combined_text(extraction)
    if not _matches_any(combined, STATISTICS_ONLY_PATTERNS):
        return False
    return not extraction.causal_process.strip()


def is_vague_case_example_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    combined = _combined_text(extraction)
    if not _matches_any(combined, VAGUE_CASE_EXAMPLE_PATTERNS):
        return False
    return len(combined) < 220 and not extraction.causal_process.strip()


def is_mechanism_name_without_process(extraction: TherapeuticFunctionExtraction) -> bool:
    if extraction.causal_process.strip() or extraction.why_this_is_a_mechanism.strip():
        return False
    label = (
        extraction.mechanism_name.strip()
        or extraction.therapeutic_function.strip()
    )
    if not label:
        return False
    combined = _combined_text(extraction)
    if len(_meaningful_tokens(combined)) <= 6:
        return True
    return False


def _resolve_semantic_match(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext,
) -> SemanticMechanismMatch | None:
    if extraction.ontology_mechanism_id.strip():
        mechanism_id = extraction.ontology_mechanism_id.strip()
        canonical = _canonical_name_for_id(mechanism_id, context=context)
        return SemanticMechanismMatch(
            mechanism_id=mechanism_id,
            document_id=_document_id_for_mechanism(mechanism_id, context=context),
            canonical_name=canonical,
            score=1.0,
            explicit=True,
        )

    matches = _find_semantic_matches(extraction, context=context)
    if matches:
        if len(matches) > 1:
            return max(matches, key=lambda item: item.score)
        return matches[0]

    detected_ids = detect_ontology_mechanism_ids(extraction, context=context)
    if len(detected_ids) == 1:
        mechanism_id = detected_ids[0]
        return SemanticMechanismMatch(
            mechanism_id=mechanism_id,
            document_id=_document_id_for_mechanism(mechanism_id, context=context),
            canonical_name=_canonical_name_for_id(mechanism_id, context=context),
            score=1.0,
        )

    return None


def _find_semantic_matches(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext,
) -> tuple[SemanticMechanismMatch, ...]:
    explicit_name = extraction.mechanism_name.strip().lower()
    if explicit_name:
        presence = context.classify_mechanism_presence(explicit_name)
        if presence.mechanism_id:
            return (
                SemanticMechanismMatch(
                    mechanism_id=presence.mechanism_id,
                    document_id=_document_id_for_mechanism(
                        presence.mechanism_id,
                        context=context,
                    ),
                    canonical_name=_canonical_name_for_id(
                        presence.mechanism_id,
                        context=context,
                    ),
                    score=1.0,
                    explicit=True,
                ),
            )

    evidence_corpus = _extraction_semantic_corpus(extraction)
    evidence_tokens = _meaningful_tokens(evidence_corpus)
    if not evidence_tokens:
        return ()

    scored: list[SemanticMechanismMatch] = []
    for candidate in _iter_mechanism_match_candidates(context):
        score = _semantic_similarity_score(
            evidence_tokens,
            evidence_corpus,
            candidate,
        )
        if score < SEMANTIC_MATCH_THRESHOLD:
            continue
        scored.append(
            SemanticMechanismMatch(
                mechanism_id=candidate.mechanism_id,
                document_id=candidate.document_id,
                canonical_name=candidate.canonical_name,
                score=score,
            )
        )
    scored.sort(key=lambda item: (-item.score, item.mechanism_id))
    return tuple(scored)


@dataclass(frozen=True)
class _MechanismMatchCandidate:
    mechanism_id: str
    document_id: str
    canonical_name: str
    corpus: str


def _iter_mechanism_match_candidates(
    context: OntologyContext,
) -> tuple[_MechanismMatchCandidate, ...]:
    candidates: list[_MechanismMatchCandidate] = []
    seen: set[str] = set()

    for document in context.get_markdown_mechanisms():
        mechanism_id = context.resolve_consolidation_mechanism_id(document.id)
        if mechanism_id in seen:
            continue
        seen.add(mechanism_id)
        candidates.append(
            _MechanismMatchCandidate(
                mechanism_id=mechanism_id,
                document_id=document.id,
                canonical_name=document.title,
                corpus=mechanism_semantic_corpus(document),
            )
        )

    for mechanism_id in context.get_known_mechanism_ids():
        if mechanism_id in seen:
            continue
        mechanism = context.get_mechanism_context(mechanism_id)
        if mechanism is None:
            continue
        seen.add(mechanism_id)
        candidates.append(
            _MechanismMatchCandidate(
                mechanism_id=mechanism_id,
                document_id=mechanism_id,
                canonical_name=mechanism.name,
                corpus=" ".join(
                    part
                    for part in (
                        mechanism.name,
                        mechanism.definition,
                        mechanism.maintaining_logic,
                        " ".join(mechanism.client_signals),
                        " ".join(mechanism.therapeutic_responses),
                    )
                    if part.strip()
                ),
            )
        )
    return tuple(candidates)


def _semantic_similarity_score(
    evidence_tokens: set[str],
    evidence_corpus: str,
    candidate: _MechanismMatchCandidate,
) -> float:
    candidate_tokens = _meaningful_tokens(candidate.corpus)
    if not candidate_tokens:
        return 0.0

    shared = evidence_tokens & candidate_tokens
    if len(shared) < SEMANTIC_MATCH_MIN_SHARED_TOKENS:
        title_tokens = _meaningful_tokens(candidate.canonical_name)
        if not (title_tokens and title_tokens <= evidence_tokens):
            return 0.0

    union = evidence_tokens | candidate_tokens
    jaccard = len(shared) / len(union) if union else 0.0

    evidence_bigrams = _bigrams(evidence_corpus)
    candidate_bigrams = _bigrams(candidate.corpus)
    bigram_overlap = 0.0
    if evidence_bigrams and candidate_bigrams:
        bigram_overlap = len(evidence_bigrams & candidate_bigrams) / len(
            evidence_bigrams | candidate_bigrams
        )

    maintaining_section = _section_text(candidate.corpus, ("maintained", "maintaining", "avoidance"))
    maintaining_overlap = 0.0
    if maintaining_section:
        maintaining_tokens = _meaningful_tokens(maintaining_section)
        if maintaining_tokens:
            maintaining_overlap = len(evidence_tokens & maintaining_tokens) / len(
                evidence_tokens | maintaining_tokens
            )

    return round(jaccard * 0.55 + bigram_overlap * 0.30 + maintaining_overlap * 0.15, 4)


def _ontology_status_for_match(
    extraction: TherapeuticFunctionExtraction,
    *,
    match: SemanticMechanismMatch,
    explicit_status: str,
) -> str:
    if explicit_status == ONTOLOGY_STATUS_CONTRADICTION:
        return UNDERSTANDING_STATUS_CONTRADICTION
    if explicit_status == ONTOLOGY_STATUS_ADDS_NEW_NUANCE:
        return UNDERSTANDING_STATUS_ADDS_NEW_NUANCE
    if explicit_status in {ONTOLOGY_STATUS_KNOWN, ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE}:
        return (
            UNDERSTANDING_STATUS_ADDS_NEW_EVIDENCE
            if explicit_status == ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE
            else UNDERSTANDING_STATUS_CONFIRMS_EXISTING
        )
    if extraction.causal_process.strip() or extraction.why_this_is_a_mechanism.strip():
        return UNDERSTANDING_STATUS_ADDS_NEW_EVIDENCE
    if match.explicit:
        return UNDERSTANDING_STATUS_CONFIRMS_EXISTING
    return UNDERSTANDING_STATUS_ADDS_NEW_EVIDENCE


def _causal_from_match(
    match: SemanticMechanismMatch,
    context: OntologyContext,
) -> str:
    document = context.get_markdown_mechanism(match.document_id)
    if document is not None:
        for section_name in ("How It Is Maintained", "How It Forms", "Practical Description"):
            section_text = document.sections.get(section_name, "").strip()
            if section_text:
                return section_text
    mechanism = context.get_mechanism_context(match.mechanism_id)
    if mechanism is not None and mechanism.maintaining_logic.strip():
        return mechanism.maintaining_logic
    return ""


def _why_from_match(match: SemanticMechanismMatch) -> str:
    return (
        "This candidate is treated as a therapeutic mechanism because the source evidence "
        f"aligns with the ontology meaning of {match.canonical_name}."
    )


def _default_why_for_new_mechanism(mechanism_name: str) -> str:
    label = mechanism_name.strip() or "this mechanism"
    return (
        "This candidate is marked as a potential new mechanism because the source appears "
        f"to describe a reusable psychological change or maintaining process related to "
        f"{label} that is not yet covered by the current ontology."
    )


def _intervention_principle_from_extraction(
    extraction: TherapeuticFunctionExtraction,
) -> str:
    if extraction.generation_rules:
        return extraction.generation_rules[0]
    return extraction.psychological_function.strip()


def _canonical_name_for_id(mechanism_id: str, *, context: OntologyContext) -> str:
    document = context.get_markdown_mechanism_by_consolidation_id(mechanism_id)
    if document is not None:
        return document.title
    mechanism = context.get_mechanism_context(mechanism_id)
    if mechanism is not None:
        return mechanism.name
    return mechanism_id.replace("_", " ").title()


def _document_id_for_mechanism(mechanism_id: str, *, context: OntologyContext) -> str:
    document = context.get_markdown_mechanism_by_consolidation_id(mechanism_id)
    if document is not None:
        return document.id
    return mechanism_id


def _extraction_semantic_corpus(extraction: TherapeuticFunctionExtraction) -> str:
    return " ".join(
        part
        for part in (
            extraction.mechanism_name,
            extraction.mechanism_description,
            extraction.causal_process,
            extraction.why_this_is_a_mechanism,
            extraction.evidence_text,
        )
        if part.strip()
    )


def _combined_text(extraction: TherapeuticFunctionExtraction) -> str:
    return _extraction_semantic_corpus(extraction).lower()


def _meaningful_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    return {token for token in tokens if token not in _STOP_WORDS}


def _bigrams(text: str) -> set[str]:
    tokens = [token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if token not in _STOP_WORDS]
    return {f"{tokens[index]} {tokens[index + 1]}" for index in range(len(tokens) - 1)}


def _section_text(corpus: str, keywords: tuple[str, ...]) -> str:
    lowered = corpus.lower()
    for keyword in keywords:
        if keyword in lowered:
            return corpus
    return ""


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)
