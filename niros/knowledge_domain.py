"""Knowledge Factory domain separation — psychotherapy/TLE vs vocal/icaro."""

from __future__ import annotations

KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE = "psychotherapy_tle"
KNOWLEDGE_DOMAIN_VOCAL_ICARO = "vocal_icaro"
KNOWLEDGE_DOMAIN_UNKNOWN = "unknown"

SUPPORTED_KNOWLEDGE_DOMAINS: tuple[str, ...] = (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)

COMPILABLE_KNOWLEDGE_DOMAINS: frozenset[str] = frozenset(SUPPORTED_KNOWLEDGE_DOMAINS)

TLE_RUNTIME_KNOWLEDGE_DOMAINS: frozenset[str] = frozenset({KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE})

VOCAL_DOMAIN_HINTS: tuple[str, ...] = (
    "maria_sabina",
    "icaro",
    "chant",
    "shipibo",
    "quechua",
)

PSYCHOTHERAPY_DOMAIN_HINTS: tuple[str, ...] = (
    "act",
    "cft",
    "ifs",
    "erickson",
    "narrative",
    "motivational_interviewing",
)


def normalize_review_knowledge_domain(value: str | None) -> str:
    """Normalize a review or pattern knowledge domain value."""
    cleaned = (value or "").strip().lower()
    if not cleaned or cleaned == KNOWLEDGE_DOMAIN_UNKNOWN:
        return KNOWLEDGE_DOMAIN_UNKNOWN
    if cleaned in COMPILABLE_KNOWLEDGE_DOMAINS:
        return cleaned
    return KNOWLEDGE_DOMAIN_UNKNOWN


def is_compilable_knowledge_domain(value: str | None) -> bool:
    """Return True when a review may be approved and compiled to CTPC."""
    return normalize_review_knowledge_domain(value) in COMPILABLE_KNOWLEDGE_DOMAINS


def is_tle_runtime_eligible_domain(value: str | None) -> bool:
    """Return True when a compiled CTPC pattern may feed TLE runtime loading."""
    return normalize_review_knowledge_domain(value) in TLE_RUNTIME_KNOWLEDGE_DOMAINS


def ctpc_subdirectory_for_domain(knowledge_domain: str) -> str:
    """Return the CTPC workspace subdirectory for one knowledge domain."""
    domain = normalize_review_knowledge_domain(knowledge_domain)
    if domain not in COMPILABLE_KNOWLEDGE_DOMAINS:
        raise ValueError(
            f"knowledge_domain must be one of: {', '.join(SUPPORTED_KNOWLEDGE_DOMAINS)}"
        )
    return domain


def ctpc_pattern_relative_path(knowledge_domain: str, pattern_id: str) -> str:
    """Return the CTPC artifact path relative to the ctpc workspace root."""
    return f"{ctpc_subdirectory_for_domain(knowledge_domain)}/{pattern_id}.json"


def infer_knowledge_domain(
    *,
    source_id: str = "",
    txt_path: str = "",
) -> str:
    """Infer knowledge domain from source identifiers or file paths."""
    blob = f"{source_id} {txt_path}".lower()
    if any(hint in blob for hint in VOCAL_DOMAIN_HINTS):
        return KNOWLEDGE_DOMAIN_VOCAL_ICARO
    if any(hint in blob for hint in PSYCHOTHERAPY_DOMAIN_HINTS):
        return KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    return KNOWLEDGE_DOMAIN_VOCAL_ICARO


def knowledge_domain_label(knowledge_domain: str) -> str:
    """Return a short UI label for one knowledge domain."""
    domain = normalize_review_knowledge_domain(knowledge_domain)
    if domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE:
        return "Psychotherapy / TLE"
    if domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO:
        return "Vocal / Icaro"
    return "unknown"
