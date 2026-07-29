"""Structured knowledge candidate — psychological knowledge separated from runtime delivery rules."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from niros.knowledge_consolidator import (
    ConsolidatedCandidatePattern,
    EvidenceFragment as ConsolidatedEvidenceFragment,
)
from niros.master_ontology import MECHANISM_PRESENCE_KNOWN
from niros.ontology_context import OntologyContext, load_ontology_context

_MAINTAINING_KEYWORDS: tuple[str, ...] = (
    r"\bmaintain",
    r"\bmaintains\b",
    r"\bmaintaining\b",
    r"\bperpetuat",
    r"\breinforc",
    r"\bsustain",
    r"\bcontinues?\b",
    r"\bkeeps?\b",
    r"\bvicious cycle\b",
    r"\bfeedback loop\b",
)

_CAUSAL_ARROW_PATTERN = re.compile(
    r"(?P<trigger>[^.;]+?)\s*(?:→|->|leads? to|results? in)\s*(?P<effect>[^.;]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EvidenceFragment:
    source_id: str
    segment_id: str
    source_family: str
    evidence_text: str
    supports: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class CausalChain:
    trigger: str
    internal_process: str
    behavior_response: str
    short_term_effect: str
    long_term_effect: str
    therapeutic_interruption: str


@dataclass(frozen=True)
class ChangeProcess:
    process_id: str
    process_name: str
    description: str
    evidence_text: str


@dataclass(frozen=True)
class MaintainingProcess:
    description: str
    evidence_text: str
    related_mechanisms: tuple[str, ...]


@dataclass(frozen=True)
class StructuredKnowledgeCandidate:
    candidate_id: str
    mechanism_id: str
    mechanism_name: str
    ontology_status: str
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    segment_ids: tuple[str, ...]
    evidence_fragments: tuple[EvidenceFragment, ...]
    confidence: float
    maintaining_processes: tuple[MaintainingProcess, ...]
    change_processes: tuple[ChangeProcess, ...]
    causal_chains: tuple[CausalChain, ...]
    protective_functions: tuple[str, ...]
    long_term_costs: tuple[str, ...]
    related_mechanisms: tuple[str, ...]
    contraindications: tuple[str, ...]
    clinical_notes: str
    open_questions: tuple[str, ...]
    reviewer_notes: str


def _resolve_mechanism_id(candidate: ConsolidatedCandidatePattern) -> str:
    if candidate.ontology_mechanism_id.strip():
        return candidate.ontology_mechanism_id.strip()
    return candidate.mechanism_key


def _split_sentences(text: str) -> tuple[str, ...]:
    cleaned = text.strip()
    if not cleaned:
        return ()
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return tuple(part.strip() for part in parts if part.strip())


def _is_maintaining_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    return any(re.search(pattern, lowered) for pattern in _MAINTAINING_KEYWORDS)


def _extract_maintaining_processes(
    causal_summary: str,
    fragments: tuple[ConsolidatedEvidenceFragment, ...],
    related_mechanisms: tuple[str, ...],
) -> tuple[MaintainingProcess, ...]:
    processes: list[MaintainingProcess] = []
    seen: set[str] = set()

    for sentence in _split_sentences(causal_summary):
        if not _is_maintaining_sentence(sentence):
            continue
        normalized = sentence.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        processes.append(
            MaintainingProcess(
                description=sentence,
                evidence_text=causal_summary.strip(),
                related_mechanisms=related_mechanisms,
            )
        )

    for fragment in fragments:
        causal_text = fragment.causal_process.strip()
        if not causal_text or not _is_maintaining_sentence(causal_text):
            continue
        normalized = causal_text.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        processes.append(
            MaintainingProcess(
                description=causal_text,
                evidence_text=fragment.evidence_text.strip(),
                related_mechanisms=related_mechanisms,
            )
        )

    if not processes and causal_summary.strip():
        processes.append(
            MaintainingProcess(
                description=causal_summary.strip(),
                evidence_text=causal_summary.strip(),
                related_mechanisms=related_mechanisms,
            )
        )
    return tuple(processes)


def _extract_causal_chains(causal_summary: str) -> tuple[CausalChain, ...]:
    cleaned = causal_summary.strip()
    if not cleaned:
        return ()

    chains: list[CausalChain] = []
    for match in _CAUSAL_ARROW_PATTERN.finditer(cleaned):
        trigger = match.group("trigger").strip()
        effect = match.group("effect").strip()
        if not trigger or not effect:
            continue
        chains.append(
            CausalChain(
                trigger=trigger,
                internal_process="",
                behavior_response="",
                short_term_effect=effect,
                long_term_effect="",
                therapeutic_interruption="",
            )
        )

    if chains:
        return tuple(chains)

    return (
        CausalChain(
            trigger="",
            internal_process=cleaned,
            behavior_response="",
            short_term_effect="",
            long_term_effect="",
            therapeutic_interruption="",
        ),
    )


def _extract_related_mechanisms(
    candidate_targets: tuple[str, ...],
    *,
    primary_mechanism_id: str,
    context: OntologyContext,
) -> tuple[str, ...]:
    related: list[str] = []
    seen: set[str] = set()
    primary_normalized = primary_mechanism_id.casefold()

    for target in candidate_targets:
        cleaned = target.strip()
        if not cleaned:
            continue
        presence = context.classify_mechanism_presence(cleaned)
        if presence.presence != MECHANISM_PRESENCE_KNOWN:
            continue
        mechanism_id = presence.mechanism_id or cleaned
        normalized = mechanism_id.casefold()
        if normalized == primary_normalized or normalized in seen:
            continue
        seen.add(normalized)
        related.append(mechanism_id)
    return tuple(related)


def _extract_change_processes(
    candidate_targets: tuple[str, ...],
    fragments: tuple[ConsolidatedEvidenceFragment, ...],
    *,
    context: OntologyContext,
) -> tuple[ChangeProcess, ...]:
    processes: list[ChangeProcess] = []
    seen: set[str] = set()
    evidence_text = fragments[0].evidence_text.strip() if fragments else ""

    for target in candidate_targets:
        cleaned = target.strip()
        if not cleaned:
            continue
        if context.is_known_mechanism(cleaned):
            continue
        process_context = context.get_therapeutic_process_context(cleaned)
        if process_context is None:
            slug = cleaned.lower().replace(" ", "_")
            process_context = context.get_therapeutic_process_context(slug)
        if process_context is None:
            continue
        if process_context.process_id in seen:
            continue
        seen.add(process_context.process_id)
        processes.append(
            ChangeProcess(
                process_id=process_context.process_id,
                process_name=process_context.name,
                description=process_context.description,
                evidence_text=evidence_text,
            )
        )
    return tuple(processes)


def _map_evidence_fragments(
    fragments: tuple[ConsolidatedEvidenceFragment, ...],
) -> tuple[EvidenceFragment, ...]:
    mapped: list[EvidenceFragment] = []
    for fragment in fragments:
        supports: list[str] = []
        if fragment.evidence_text.strip():
            supports.append("evidence")
        if fragment.causal_process.strip():
            supports.append("causal_process")
        if fragment.why_this_is_a_mechanism.strip():
            supports.append("mechanism_rationale")
        mapped.append(
            EvidenceFragment(
                source_id=fragment.source_id,
                segment_id=fragment.segment_id,
                source_family=fragment.source_family,
                evidence_text=fragment.evidence_text.strip(),
                supports=tuple(supports),
                confidence=fragment.confidence,
            )
        )
    return tuple(mapped)


def build_structured_knowledge_candidate(
    candidate: ConsolidatedCandidatePattern,
    *,
    ontology_context: OntologyContext | None = None,
    reviewer_notes: str = "",
) -> StructuredKnowledgeCandidate:
    """Build structured psychological knowledge from one consolidated candidate pattern."""
    context = ontology_context or load_ontology_context()
    mechanism_id = _resolve_mechanism_id(candidate)
    related_mechanisms = _extract_related_mechanisms(
        candidate.candidate_targets,
        primary_mechanism_id=mechanism_id,
        context=context,
    )
    maintaining_processes = _extract_maintaining_processes(
        candidate.causal_process_summary,
        candidate.evidence_fragments,
        related_mechanisms,
    )
    causal_chains = _extract_causal_chains(candidate.causal_process_summary)
    change_processes = _extract_change_processes(
        candidate.candidate_targets,
        candidate.evidence_fragments,
        context=context,
    )

    return StructuredKnowledgeCandidate(
        candidate_id=candidate.candidate_id,
        mechanism_id=mechanism_id,
        mechanism_name=candidate.canonical_name,
        ontology_status=candidate.ontology_status,
        source_ids=candidate.source_ids,
        source_families=candidate.source_families,
        segment_ids=candidate.segment_ids,
        evidence_fragments=_map_evidence_fragments(candidate.evidence_fragments),
        confidence=candidate.mean_confidence,
        maintaining_processes=maintaining_processes,
        change_processes=change_processes,
        causal_chains=causal_chains,
        protective_functions=(),
        long_term_costs=(),
        related_mechanisms=related_mechanisms,
        contraindications=candidate.contraindications,
        clinical_notes=candidate.why_extraction_summary.strip(),
        open_questions=(),
        reviewer_notes=reviewer_notes.strip(),
    )


def serialize_structured_knowledge_candidate(
    candidate: StructuredKnowledgeCandidate,
) -> dict[str, Any]:
    return asdict(candidate)


def deserialize_structured_knowledge_candidate(
    payload: dict[str, Any],
) -> StructuredKnowledgeCandidate:
    evidence_fragments = tuple(
        EvidenceFragment(**fragment)
        for fragment in payload.get("evidence_fragments", ())
    )
    maintaining_processes = tuple(
        MaintainingProcess(**item)
        for item in payload.get("maintaining_processes", ())
    )
    change_processes = tuple(
        ChangeProcess(**item) for item in payload.get("change_processes", ())
    )
    causal_chains = tuple(
        CausalChain(**item) for item in payload.get("causal_chains", ())
    )
    return StructuredKnowledgeCandidate(
        candidate_id=payload["candidate_id"],
        mechanism_id=payload.get("mechanism_id", ""),
        mechanism_name=payload.get("mechanism_name", ""),
        ontology_status=payload.get("ontology_status", ""),
        source_ids=tuple(payload.get("source_ids", ())),
        source_families=tuple(payload.get("source_families", ())),
        segment_ids=tuple(payload.get("segment_ids", ())),
        evidence_fragments=evidence_fragments,
        confidence=float(payload.get("confidence", 0.0)),
        maintaining_processes=maintaining_processes,
        change_processes=change_processes,
        causal_chains=causal_chains,
        protective_functions=tuple(payload.get("protective_functions", ())),
        long_term_costs=tuple(payload.get("long_term_costs", ())),
        related_mechanisms=tuple(payload.get("related_mechanisms", ())),
        contraindications=tuple(payload.get("contraindications", ())),
        clinical_notes=payload.get("clinical_notes", ""),
        open_questions=tuple(payload.get("open_questions", ())),
        reviewer_notes=payload.get("reviewer_notes", ""),
    )
