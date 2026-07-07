"""Therapeutic Function Extraction — contracts for source-segment extraction output."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from niros.ctpc import CanonicalTherapeuticPattern

DEFAULT_EXTRACTOR = "human_or_llm_assisted"
DEFAULT_REVIEW_STATUS = "draft"
PENDING_HUMAN_REVIEW_STATUS = "pending_human_review"
SOURCE_SEGMENT_EVIDENCE_LEVEL = "source_segment"
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0
EXTRACTION_ID_HASH_LENGTH = 8
MAX_SAFE_ARTIFACT_ID_LENGTH = 200


@dataclass(frozen=True)
class TherapeuticFunctionExtraction:
    extraction_id: str
    source_id: str
    segment_id: str
    therapeutic_function: str
    psychological_function: str = ""
    evidence_text: str = ""
    symbolic_elements: tuple[str, ...] = field(default_factory=tuple)
    generation_rules: tuple[str, ...] = field(default_factory=tuple)
    voice_rules: tuple[str, ...] = field(default_factory=tuple)
    repetition_rules: tuple[str, ...] = field(default_factory=tuple)
    pause_rules: tuple[str, ...] = field(default_factory=tuple)
    candidate_targets: tuple[str, ...] = field(default_factory=tuple)
    contraindications: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    extractor: str = DEFAULT_EXTRACTOR
    review_status: str = DEFAULT_REVIEW_STATUS


def _normalize_identifier_part(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return re.sub(r"_+", "_", normalized)


def _extraction_id_hash(
    source_id: str,
    segment_id: str,
    therapeutic_function: str,
    psychological_function: str = "",
) -> str:
    payload = "|".join(
        (
            source_id.strip(),
            segment_id.strip(),
            therapeutic_function.strip(),
            psychological_function.strip(),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:EXTRACTION_ID_HASH_LENGTH]


def build_extraction_id(
    source_id: str,
    segment_id: str,
    therapeutic_function: str,
    psychological_function: str = "",
) -> str:
    """Build a short deterministic extraction ID from source, segment, and functions."""
    digest = _extraction_id_hash(
        source_id,
        segment_id,
        therapeutic_function,
        psychological_function,
    )
    parts = (
        _normalize_identifier_part(source_id),
        _normalize_identifier_part(segment_id),
        digest,
    )
    return f"extraction_{'_'.join(parts)}"


def validate_extraction(extraction: TherapeuticFunctionExtraction) -> tuple[str, ...]:
    """Return validation issue strings for one therapeutic function extraction."""
    issues: list[str] = []

    if not extraction.extraction_id.strip():
        issues.append("extraction_id must not be empty")
    if not extraction.source_id.strip():
        issues.append("source_id must not be empty")
    if not extraction.segment_id.strip():
        issues.append("segment_id must not be empty")
    if not extraction.therapeutic_function.strip():
        issues.append("therapeutic_function must not be empty")
    if not extraction.evidence_text.strip():
        issues.append("evidence_text must not be empty")
    if extraction.confidence < MIN_CONFIDENCE or extraction.confidence > MAX_CONFIDENCE:
        issues.append("confidence must be between 0.0 and 1.0")

    return tuple(issues)


def build_ctpc_pattern_from_extraction(
    extraction: TherapeuticFunctionExtraction,
    pattern_id: str | None = None,
) -> CanonicalTherapeuticPattern:
    """Map an extraction record to a pending-review CTPC pattern."""
    resolved_pattern_id = pattern_id or f"ctp_from_{extraction.extraction_id}"
    return CanonicalTherapeuticPattern(
        pattern_id=resolved_pattern_id,
        name=extraction.therapeutic_function.replace("_", " ").title(),
        source_family=extraction.source_id,
        source_reference=extraction.segment_id,
        therapeutic_function=extraction.therapeutic_function,
        psychological_function=extraction.psychological_function,
        candidate_targets=extraction.candidate_targets,
        generation_rules=extraction.generation_rules,
        voice_rules=extraction.voice_rules,
        repetition_rules=extraction.repetition_rules,
        pause_rules=extraction.pause_rules,
        symbolic_elements=extraction.symbolic_elements,
        contraindications=extraction.contraindications,
        evidence_level=SOURCE_SEGMENT_EVIDENCE_LEVEL,
        confidence=extraction.confidence,
        review_status=PENDING_HUMAN_REVIEW_STATUS,
    )
