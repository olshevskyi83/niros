"""CTPC Compiler — deterministic compilation of approved human reviews into CTPC artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from niros.ctpc import CanonicalTherapeuticPattern, validate_ctpc_pattern
from niros.human_review_workflow import (
    REVIEW_STATUS_APPROVED,
    HumanReviewRecord,
    effective_extraction,
)
from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    KnowledgeWorkspacePaths,
    build_knowledge_workspace_paths,
    knowledge_artifact_path,
)
from niros.therapeutic_extraction import (
    SOURCE_SEGMENT_EVIDENCE_LEVEL,
    build_ctpc_pattern_from_extraction,
    validate_extraction,
)

COMPILED_CTPC_REVIEW_STATUS = "approved"

_CTPC_TUPLE_FIELDS = (
    "candidate_targets",
    "generation_rules",
    "voice_rules",
    "repetition_rules",
    "pause_rules",
    "symbolic_elements",
    "contraindications",
)


class CTPCCompilerError(Exception):
    """Base error for CTPC compiler failures."""


class CTPCCompilationStateError(CTPCCompilerError):
    """Raised when a review is not approved for compilation."""


class CTPCCompilationValidationError(CTPCCompilerError):
    """Raised when a compiled CTPC pattern fails validation."""


class CTPCPatternNotFoundError(CTPCCompilerError):
    """Raised when a compiled CTPC pattern cannot be found."""


def compile_pattern_from_approved_review(
    record: HumanReviewRecord,
) -> CanonicalTherapeuticPattern:
    """Convert one approved human review record into a CTPC pattern."""
    if record.status != REVIEW_STATUS_APPROVED:
        raise CTPCCompilationStateError(
            f"Review {record.review_id} has status {record.status!r}; "
            "only approved reviews may compile."
        )

    extraction = effective_extraction(record)
    if extraction is None:
        raise CTPCCompilationValidationError(
            f"Review {record.review_id} does not contain an approved extraction."
        )

    extraction_issues = validate_extraction(extraction)
    if extraction_issues:
        joined = "; ".join(extraction_issues)
        raise CTPCCompilationValidationError(
            f"Approved extraction failed validation: {joined}"
        )

    pattern = build_ctpc_pattern_from_extraction(extraction)
    compiled = replace(
        pattern,
        review_status=COMPILED_CTPC_REVIEW_STATUS,
        evidence_level=SOURCE_SEGMENT_EVIDENCE_LEVEL,
    )

    pattern_issues = validate_ctpc_pattern(compiled)
    if pattern_issues:
        joined = "; ".join(pattern_issues)
        raise CTPCCompilationValidationError(
            f"Compiled CTPC pattern failed validation: {joined}"
        )

    return compiled


def serialize_ctpc_pattern(pattern: CanonicalTherapeuticPattern) -> dict[str, Any]:
    """Return a JSON-serializable dictionary for one CTPC pattern."""
    return {
        "pattern_id": pattern.pattern_id,
        "name": pattern.name,
        "source_family": pattern.source_family,
        "source_reference": pattern.source_reference,
        "therapeutic_function": pattern.therapeutic_function,
        "psychological_function": pattern.psychological_function,
        "candidate_targets": list(pattern.candidate_targets),
        "generation_rules": list(pattern.generation_rules),
        "voice_rules": list(pattern.voice_rules),
        "repetition_rules": list(pattern.repetition_rules),
        "pause_rules": list(pattern.pause_rules),
        "symbolic_elements": list(pattern.symbolic_elements),
        "contraindications": list(pattern.contraindications),
        "evidence_level": pattern.evidence_level,
        "confidence": pattern.confidence,
        "review_status": pattern.review_status,
    }


def deserialize_ctpc_pattern(data: dict[str, Any]) -> CanonicalTherapeuticPattern:
    """Build a CanonicalTherapeuticPattern from serialized data."""
    kwargs = dict(data)
    for field_name in _CTPC_TUPLE_FIELDS:
        if field_name in kwargs and kwargs[field_name] is not None:
            kwargs[field_name] = tuple(kwargs[field_name])
    return CanonicalTherapeuticPattern(**kwargs)


@dataclass(frozen=True)
class CTPCCompiler:
    """Compile approved human reviews into CTPC workspace JSON artifacts."""

    paths: KnowledgeWorkspacePaths

    @classmethod
    def from_workspace_root(cls, workspace_root: str = DEFAULT_KNOWLEDGE_ROOT) -> CTPCCompiler:
        """Build a compiler bound to one knowledge workspace root."""
        return cls(paths=build_knowledge_workspace_paths(workspace_root))

    def _pattern_path(self, pattern_id: str) -> Path:
        filename = f"{pattern_id}.json"
        return Path(knowledge_artifact_path(self.paths, "ctpc", filename))

    def compile_review(self, record: HumanReviewRecord) -> CanonicalTherapeuticPattern:
        """Compile one approved review and persist the resulting CTPC pattern."""
        pattern = compile_pattern_from_approved_review(record)
        self.save_pattern(pattern)
        return pattern

    def save_pattern(self, pattern: CanonicalTherapeuticPattern) -> Path:
        """Write one CTPC pattern JSON file into the CTPC workspace."""
        issues = validate_ctpc_pattern(pattern)
        if issues:
            joined = "; ".join(issues)
            raise CTPCCompilationValidationError(
                f"CTPC pattern failed validation: {joined}"
            )

        output_path = self._pattern_path(pattern.pattern_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            serialize_ctpc_pattern(pattern),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        output_path.write_text(payload + "\n", encoding="utf-8")
        return output_path

    def load_pattern(self, pattern_id: str) -> CanonicalTherapeuticPattern:
        """Load one compiled CTPC pattern from the CTPC workspace."""
        input_path = self._pattern_path(pattern_id)
        if not input_path.exists():
            raise CTPCPatternNotFoundError(f"CTPC pattern not found: {pattern_id}")
        data = json.loads(input_path.read_text(encoding="utf-8"))
        return deserialize_ctpc_pattern(data)
