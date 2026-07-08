"""Semantic knowledge extraction — ontology-guided reusable mechanism contracts."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable

from niros.ontology_context import OntologyContext, load_ontology_context
from niros.therapeutic_extraction import (
    TherapeuticFunctionExtraction,
    validate_extraction,
)

ONTOLOGY_STATUS_KNOWN = "known"
ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE = "adds_new_evidence"
ONTOLOGY_STATUS_ADDS_NEW_NUANCE = "adds_new_nuance"
ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM = "potential_new_mechanism"
ONTOLOGY_STATUS_CONTRADICTION = "contradiction"

SUPPORTED_ONTOLOGY_STATUSES: frozenset[str] = frozenset(
    {
        ONTOLOGY_STATUS_KNOWN,
        ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
        ONTOLOGY_STATUS_ADDS_NEW_NUANCE,
        ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        ONTOLOGY_STATUS_CONTRADICTION,
    }
)

REQUIRED_SEMANTIC_KNOWLEDGE_FIELDS: tuple[str, ...] = (
    "mechanism_name",
    "mechanism_description",
    "why_this_is_a_mechanism",
    "causal_process",
    "evidence",
    "ontology_status",
    "confidence",
)

DEFINITION_ONLY_PATTERNS: tuple[str, ...] = (
    r"\bis defined as\b",
    r"\brefers to\b",
    r"\bmeans that\b",
    r"\bis the process of\b",
    r"\bis a form of\b",
    r"\bis an?\s+(?:important|key|core|central)\b",
    r"\bacceptance is important\b",
    r"\bmindfulness is\b",
    r"\bact stands for\b",
)

CHAPTER_SUMMARY_PATTERNS: tuple[str, ...] = (
    r"this chapter (?:introduces|explores|describes)",
    r"this book (?:helps|provides|explores|introduces)",
    r"in this (?:chapter|section|book)",
    r"overview of",
    r"introduction to act",
    r"what is act",
    r"the purpose of this (?:book|chapter)",
    r"readers will learn",
)

TERMINOLOGY_ONLY_PATTERNS: tuple[str, ...] = (
    r"^\s*(?:acceptance|defusion|mindfulness|values|act|cbt)\s*[.:]?\s*$",
    r"^\s*(?:acceptance|defusion|mindfulness|values)\s+is\s+\w+\s*[.:]?\s*$",
)

# ACT wording groups used ONLY to normalize text before ontology lookup.
ACT_WORDING_SYNONYM_PHRASES: dict[str, tuple[str, ...]] = {
    "acceptance": (
        "acceptance",
        "accept emotions",
        "accept emotion",
        "allow painful feelings",
        "allow emotions",
        "allow feelings",
        "stop fighting feelings",
        "make room for emotions",
        "willingness to feel",
        "acceptance of internal experience",
    ),
    "defusion": (
        "cognitive defusion",
        "defusion",
        "defuse from thoughts",
        "unhook from thoughts",
        "see thoughts as thoughts",
        "thoughts are just thoughts",
    ),
    "present_moment": (
        "mindfulness",
        "present moment",
        "present-moment awareness",
        "contact with the present",
    ),
    "values_committed_action": (
        "values",
        "live by values",
        "clarify values",
        "committed action",
        "move toward what matters",
    ),
    "experiential_avoidance": (
        "avoid feelings",
        "control strategies",
        "suppress feelings",
        "happiness trap",
        "struggle switch",
        "experiential avoidance",
        "control emotions",
    ),
    "psychological_flexibility": (
        "psychological flexibility",
        "rich full meaningful life",
    ),
}

# Optional ontology lookup hints after ACT wording normalization.
# Never merge distinct ACT groups — each hint maps to at most one ontology mechanism.
ACT_WORDING_ONTOLOGY_HINTS: dict[str, str] = {
    "experiential_avoidance": "experiential_avoidance",
    "defusion": "cognitive_fusion",
}

UNKNOWN_MECHANISM_KEY = "unknown"


def normalize_ontology_status(value: str | None) -> str:
    """Normalize ontology_status from LLM output."""
    cleaned = str(value or "").strip().lower().replace(" ", "_")
    if not cleaned:
        return ""
    aliases = {
        "known_mechanism": ONTOLOGY_STATUS_KNOWN,
        "new_evidence": ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE,
        "new_nuance": ONTOLOGY_STATUS_ADDS_NEW_NUANCE,
        "potential_new": ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        "new_mechanism": ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
        "unknown": ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM,
    }
    if cleaned in aliases:
        return aliases[cleaned]
    if cleaned in SUPPORTED_ONTOLOGY_STATUSES:
        return cleaned
    return ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM


def has_semantic_knowledge_fields(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction carries ontology-driven knowledge metadata."""
    return bool(
        extraction.mechanism_name.strip()
        or extraction.causal_process.strip()
        or extraction.why_this_is_a_mechanism.strip()
        or extraction.ontology_status.strip()
    )


def has_explicit_semantic_knowledge_metadata(
    extraction: TherapeuticFunctionExtraction,
) -> bool:
    """Return True when the extractor explicitly provided semantic knowledge fields."""
    return bool(
        normalize_ontology_status(extraction.ontology_status)
        or extraction.causal_process.strip()
        or extraction.why_this_is_a_mechanism.strip()
        or (
            extraction.mechanism_name.strip()
            and extraction.mechanism_description.strip()
        )
    )


def has_causal_mechanism_content(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction explains a reusable causal mechanism."""
    return bool(
        extraction.causal_process.strip()
        or extraction.why_this_is_a_mechanism.strip()
        or extraction.mechanism_description.strip()
        or extraction.psychological_function.strip()
    )


def _combined_knowledge_text(extraction: TherapeuticFunctionExtraction) -> str:
    return " ".join(
        part
        for part in (
            extraction.mechanism_name,
            extraction.mechanism_description,
            extraction.why_this_is_a_mechanism,
            extraction.causal_process,
            extraction.therapeutic_function,
            extraction.psychological_function,
            extraction.evidence_text,
        )
        if part.strip()
    ).lower()


def is_definition_only_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction reads like a definition without reusable process."""
    combined = _combined_knowledge_text(extraction)
    if not _matches_any(combined, DEFINITION_ONLY_PATTERNS):
        return False
    if extraction.causal_process.strip():
        return False
    if len(extraction.why_this_is_a_mechanism.strip()) > 80:
        return False
    return True


def is_chapter_summary_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction is a chapter or book summary."""
    combined = _combined_knowledge_text(extraction)
    return _matches_any(combined, CHAPTER_SUMMARY_PATTERNS)


def is_terminology_only_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction names terminology without explaining a mechanism."""
    label = (
        extraction.mechanism_name.strip()
        or extraction.therapeutic_function.strip()
    ).lower()
    if _matches_any(label, TERMINOLOGY_ONLY_PATTERNS):
        return True
    if len(label.split()) <= 3 and not extraction.causal_process.strip():
        keywords = ("acceptance", "defusion", "mindfulness", "values", "act", "cbt")
        if any(re.search(rf"\b{re.escape(keyword)}\b", label) for keyword in keywords) and len(
            combined := _combined_knowledge_text(extraction)
        ) < 120:
            return True
    return False


def is_low_value_knowledge_extraction(extraction: TherapeuticFunctionExtraction) -> bool:
    """Return True when extraction should be filtered as non-reusable knowledge."""
    if is_definition_only_extraction(extraction):
        return True
    if is_chapter_summary_extraction(extraction):
        return True
    if is_terminology_only_extraction(extraction):
        return True
    return False


def validate_semantic_knowledge_extraction(
    extraction: TherapeuticFunctionExtraction,
) -> tuple[str, ...]:
    """Return validation issues for ontology-driven knowledge extractions."""
    issues: list[str] = []
    if is_low_value_knowledge_extraction(extraction):
        issues.append("extraction is definition, summary, or terminology-only content")
    if has_semantic_knowledge_fields(extraction):
        if not extraction.mechanism_name.strip():
            issues.append("mechanism_name must not be empty for semantic knowledge extraction")
        if (
            not extraction.causal_process.strip()
            and not extraction.why_this_is_a_mechanism.strip()
        ):
            issues.append("causal_process or why_this_is_a_mechanism is required")
        status = normalize_ontology_status(extraction.ontology_status)
        if status and status not in SUPPORTED_ONTOLOGY_STATUSES:
            issues.append(f"unsupported ontology_status: {extraction.ontology_status}")
    return tuple(issues)


def collect_extraction_validation_issues(
    extraction: TherapeuticFunctionExtraction,
    *,
    require_semantic_knowledge: bool | None = None,
) -> tuple[str, ...]:
    """Collect all extraction validation issues before raising."""
    issues: list[str] = []
    issues.extend(validate_extraction(extraction))
    should_validate_semantic = (
        require_semantic_knowledge
        if require_semantic_knowledge is not None
        else has_semantic_knowledge_fields(extraction)
    )
    if should_validate_semantic:
        issues.extend(validate_semantic_knowledge_extraction(extraction))
    return tuple(issues)


def format_ontology_mechanism_catalog(context: OntologyContext) -> str:
    """Format known ontology mechanisms for inclusion in extraction prompts."""
    lines: list[str] = []
    for mechanism_id in context.get_known_mechanism_ids():
        mechanism = context.get_mechanism_context(mechanism_id)
        if mechanism is None:
            continue
        lines.append(
            f"- {mechanism_id}: {mechanism.name} — {mechanism.definition.strip()}"
        )
    return "\n".join(lines)


def detect_act_wording_groups(text: str) -> tuple[str, ...]:
    """Return ACT wording groups detected in text for pre-lookup normalization only."""
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    if not normalized:
        return ()
    matched: list[str] = []
    for group, phrases in ACT_WORDING_SYNONYM_PHRASES.items():
        if any(phrase in normalized for phrase in phrases):
            matched.append(group)
    return tuple(_unique_preserve_order(matched))


def normalize_text_for_ontology_lookup(text: str) -> str:
    """Expand text with ontology hint tokens derived from ACT wording normalization."""
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    if not normalized:
        return ""
    hints: list[str] = []
    for group in detect_act_wording_groups(normalized):
        ontology_id = ACT_WORDING_ONTOLOGY_HINTS.get(group)
        if ontology_id:
            hints.append(ontology_id.replace("_", " "))
    if hints:
        return f"{normalized} {' '.join(hints)}"
    return normalized


def detect_ontology_mechanism_ids(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext | None = None,
    include_function_fields: bool = True,
) -> tuple[str, ...]:
    """Return ontology mechanism IDs detected for one extraction."""
    resolved_context = context or load_ontology_context()
    ontology_status = normalize_ontology_status(extraction.ontology_status)

    if ontology_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        return ()

    if extraction.ontology_mechanism_id.strip():
        return (extraction.ontology_mechanism_id.strip(),)

    matched: list[str] = []
    search_parts: list[str] = [
        extraction.mechanism_name,
        extraction.mechanism_description,
        extraction.causal_process,
        extraction.why_this_is_a_mechanism,
        extraction.evidence_text,
    ]
    if include_function_fields:
        search_parts.extend(
            (
                extraction.therapeutic_function,
                extraction.psychological_function,
            )
        )
    for part in search_parts:
        if not part.strip():
            continue
        normalized = normalize_text_for_ontology_lookup(part)
        for group in detect_act_wording_groups(normalized):
            hint_id = ACT_WORDING_ONTOLOGY_HINTS.get(group)
            if hint_id and hint_id not in matched:
                if resolved_context.get_mechanism_context(hint_id) is not None:
                    matched.append(hint_id)
        presence = resolved_context.classify_mechanism_presence(normalized)
        if presence.mechanism_id and presence.mechanism_id not in matched:
            matched.append(presence.mechanism_id)

    return tuple(matched)


def new_mechanism_key(mechanism_name: str) -> str:
    """Build a deterministic key for a potential new ontology mechanism."""
    slug = _slugify_mechanism_label(mechanism_name)
    return f"new_{slug}"


def canonical_name_for_mechanism_key(
    mechanism_key: str,
    *,
    context: OntologyContext,
    fallback_name: str = "",
) -> str:
    """Return the canonical display name for one consolidation mechanism key."""
    mechanism = context.get_mechanism_context(mechanism_key)
    if mechanism is not None:
        return mechanism.name
    if fallback_name.strip():
        return fallback_name.strip()
    if mechanism_key.startswith("new_"):
        return mechanism_key.removeprefix("new_").replace("_", " ").title()
    if mechanism_key == UNKNOWN_MECHANISM_KEY:
        return "Unknown therapeutic mechanism"
    return mechanism_key.replace("_", " ").title()


def enrich_extraction_with_ontology(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext | None = None,
) -> TherapeuticFunctionExtraction:
    """Resolve ontology linkage and normalize semantic knowledge fields."""
    resolved_context = context or load_ontology_context()
    mechanism_name = extraction.mechanism_name.strip() or extraction.therapeutic_function.strip()
    mechanism_description = (
        extraction.mechanism_description.strip() or extraction.psychological_function.strip()
    )
    causal_process = extraction.causal_process.strip()
    why_mechanism = extraction.why_this_is_a_mechanism.strip()
    evidence_text = extraction.evidence_text.strip()
    ontology_status = normalize_ontology_status(extraction.ontology_status)

    ontology_mechanism_id = extraction.ontology_mechanism_id.strip()
    if ontology_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        ontology_mechanism_id = ""
    elif not ontology_mechanism_id and mechanism_name:
        name_only_ids = detect_ontology_mechanism_ids(
            extraction,
            context=resolved_context,
            include_function_fields=False,
        )
        if len(name_only_ids) == 1:
            ontology_mechanism_id = name_only_ids[0]
        elif not name_only_ids:
            if not ontology_status:
                ontology_status = ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM
        else:
            if not ontology_status:
                ontology_status = ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM
    elif not ontology_mechanism_id:
        detected_ids = detect_ontology_mechanism_ids(extraction, context=resolved_context)
        if len(detected_ids) == 1:
            ontology_mechanism_id = detected_ids[0]
        elif not ontology_status:
            ontology_status = ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM

    if ontology_mechanism_id and ontology_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        ontology_status = ONTOLOGY_STATUS_KNOWN

    if (
        ontology_mechanism_id
        and causal_process
        and ontology_status == ONTOLOGY_STATUS_KNOWN
    ):
        ontology_status = ONTOLOGY_STATUS_ADDS_NEW_EVIDENCE

    therapeutic_function = extraction.therapeutic_function.strip()
    if not therapeutic_function:
        therapeutic_function = ontology_mechanism_id or new_mechanism_key(mechanism_name)

    psychological_function = extraction.psychological_function.strip() or mechanism_description
    if not why_mechanism and causal_process:
        why_mechanism = (
            "This passage explains a causal process that can be reused as therapeutic knowledge."
        )

    return replace(
        extraction,
        mechanism_name=mechanism_name,
        mechanism_description=mechanism_description,
        why_this_is_a_mechanism=why_mechanism,
        causal_process=causal_process,
        ontology_status=ontology_status,
        ontology_mechanism_id=ontology_mechanism_id,
        therapeutic_function=therapeutic_function,
        psychological_function=psychological_function,
        evidence_text=evidence_text,
    )


def resolve_consolidation_mechanism_key(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext | None = None,
) -> tuple[str, str, str]:
    """Return (mechanism_key, mechanism_family, canonical_name) for consolidation grouping."""
    resolved_context = context or load_ontology_context()
    ontology_status = normalize_ontology_status(extraction.ontology_status)

    if ontology_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        name = extraction.mechanism_name.strip() or extraction.therapeutic_function.strip()
        if not name:
            return UNKNOWN_MECHANISM_KEY, UNKNOWN_MECHANISM_KEY, "Unknown therapeutic mechanism"
        mechanism_key = new_mechanism_key(name)
        return mechanism_key, "potential_new", name

    if extraction.ontology_mechanism_id.strip():
        mechanism_id = extraction.ontology_mechanism_id.strip()
        canonical = canonical_name_for_mechanism_key(
            mechanism_id,
            context=resolved_context,
            fallback_name=extraction.mechanism_name,
        )
        return mechanism_id, mechanism_id, canonical

    if extraction.mechanism_name.strip():
        name_only_ids = detect_ontology_mechanism_ids(
            extraction,
            context=resolved_context,
            include_function_fields=False,
        )
        if len(name_only_ids) == 1:
            mechanism_id = name_only_ids[0]
            canonical = canonical_name_for_mechanism_key(
                mechanism_id,
                context=resolved_context,
                fallback_name=extraction.mechanism_name,
            )
            return mechanism_id, mechanism_id, canonical

    detected_ids = detect_ontology_mechanism_ids(extraction, context=resolved_context)
    if len(detected_ids) == 1:
        mechanism_id = detected_ids[0]
        canonical = canonical_name_for_mechanism_key(
            mechanism_id,
            context=resolved_context,
            fallback_name=extraction.mechanism_name,
        )
        return mechanism_id, mechanism_id, canonical

    if extraction.mechanism_name.strip():
        name = extraction.mechanism_name.strip()
        mechanism_key = new_mechanism_key(name)
        return mechanism_key, "potential_new", name

    fallback_label = (
        extraction.therapeutic_function.strip()
        or extraction.psychological_function.strip()
        or extraction.evidence_text.strip()[:80]
    )
    if fallback_label:
        mechanism_key = new_mechanism_key(fallback_label)
        return mechanism_key, "potential_new", fallback_label.title()

    return UNKNOWN_MECHANISM_KEY, UNKNOWN_MECHANISM_KEY, "Unknown therapeutic mechanism"


def split_extraction_by_ontology_mechanisms(
    extraction: TherapeuticFunctionExtraction,
    *,
    context: OntologyContext | None = None,
) -> tuple[TherapeuticFunctionExtraction, ...]:
    """Split one extraction into separate ontology mechanism extractions when needed."""
    resolved_context = context or load_ontology_context()
    ontology_status = normalize_ontology_status(extraction.ontology_status)

    if ontology_status == ONTOLOGY_STATUS_POTENTIAL_NEW_MECHANISM:
        return (extraction,)

    mechanism_ids = detect_ontology_mechanism_ids(extraction, context=resolved_context)
    if len(mechanism_ids) <= 1:
        if len(mechanism_ids) == 1:
            mechanism_id = mechanism_ids[0]
            mechanism = resolved_context.get_mechanism_context(mechanism_id)
            return (
                replace(
                    extraction,
                    ontology_mechanism_id=mechanism_id,
                    mechanism_name=mechanism.name if mechanism is not None else mechanism_id,
                    therapeutic_function=mechanism_id,
                ),
            )
        return (extraction,)

    split_items: list[TherapeuticFunctionExtraction] = []
    for mechanism_id in mechanism_ids:
        mechanism = resolved_context.get_mechanism_context(mechanism_id)
        split_items.append(
            replace(
                extraction,
                extraction_id=f"{extraction.extraction_id}_{mechanism_id}",
                ontology_mechanism_id=mechanism_id,
                mechanism_name=mechanism.name if mechanism is not None else mechanism_id,
                therapeutic_function=mechanism_id,
            )
        )
    return tuple(split_items)


def _slugify_mechanism_label(value: str) -> str:
    collapsed = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return collapsed.strip("_") or "mechanism"


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


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)
