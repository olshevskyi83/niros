"""Typed Knowledge Compiler routing and source-specific adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from niros.human_review_workflow import REVIEW_STATUS_PENDING
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_library import (
    KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT,
    KNOWLEDGE_SOURCE_TYPE_TEXT,
    KnowledgeLibrarySourceRecord,
)
from niros.knowledge_workspace import KnowledgeWorkspacePaths


@dataclass(frozen=True)
class AdapterCompileResult:
    status: str
    knowledge_domain: str = ""
    chunks_created: int = 0
    semantic_extractions: int = 0
    pending_reviews: int = 0
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompilerRoute:
    compiler: object | None
    knowledge_domain: str = ""
    supported: bool = False
    unsupported_reason: str = ""


class TextSemanticCompiler:
    """Route marker for the existing TXT semantic extraction pipeline."""


@dataclass(frozen=True)
class AudioVocalExtractionProposal:
    extraction_id: str
    source_id: str
    segment_id: str
    source_type: str
    knowledge_domain: str
    features: dict[str, Any]
    source_title: str = ""
    source_family: str = ""
    confidence: float = 0.0
    extractor: str = "audio_extract_compiler_mvp"


def _safe_review_id(value: str) -> str:
    return "review_" + "".join(
        character if character.isalnum() or character in {"_", "-"} else "_"
        for character in value
    )


def _find_value(data: Any, candidates: tuple[str, ...]) -> Any:
    if isinstance(data, dict):
        for key, value in data.items():
            normalized = key.lower().replace(" ", "_").replace("-", "_")
            if normalized in candidates:
                return value
        for value in data.values():
            found = _find_value(value, candidates)
            if found is not None:
                return found
    if isinstance(data, list):
        for item in data:
            found = _find_value(item, candidates)
            if found is not None:
                return found
    return None


def _extract_audio_vocal_features(data: Any) -> dict[str, Any]:
    fields: dict[str, tuple[str, ...]] = {
        "tempo_bpm": ("tempo", "bpm", "tempo_bpm"),
        "tonal_center": ("tonal_center", "key"),
        "pitch_range": ("pitch_range",),
        "phrase_count": ("phrase_count", "phrases"),
        "pauses": ("pauses", "pause_profile"),
        "repetition_index": ("repetition_index", "repetition"),
        "melodic_motifs": ("melodic_motifs", "motifs"),
        "rhythmic_patterns": ("rhythmic_patterns", "rhythm_patterns"),
        "vocal_texture": ("vocal_texture", "texture"),
        "energy_curve": ("energy_curve", "energy"),
        "spectral_features": ("spectral_features", "spectral"),
    }
    return {
        output_name: value
        for output_name, candidates in fields.items()
        if (value := _find_value(data, candidates)) is not None
    }


class AudioExtractCompiler:
    """Compile vocal audio analysis JSON into pending audio-vocal review proposals."""

    def compile(
        self,
        source: KnowledgeLibrarySourceRecord,
        *,
        library_root: str,
        paths: KnowledgeWorkspacePaths,
        timestamp_fn: Callable[[], str],
    ) -> AdapterCompileResult:
        source_path = Path(library_root) / source.relative_path
        try:
            data = json.loads(source_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return AdapterCompileResult(
                status="failed",
                knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
                errors=(str(exc),),
            )

        features = _extract_audio_vocal_features(data)
        extraction_id = f"audio_vocal_extraction_{source.source_id}"
        proposal = AudioVocalExtractionProposal(
            extraction_id=extraction_id,
            source_id=source.source_id,
            segment_id=f"{source.source_id}_audio_extract",
            source_type=KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT,
            knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
            features=features,
            source_title=source.title,
            source_family=source.family,
            confidence=0.5 if features else 0.0,
        )
        timestamp = timestamp_fn()
        review_id = _safe_review_id(extraction_id)
        payload = {
            "review_type": "audio_vocal_extraction",
            "review_id": review_id,
            "extraction_id": proposal.extraction_id,
            "source_id": proposal.source_id,
            "segment_id": proposal.segment_id,
            "status": REVIEW_STATUS_PENDING,
            "knowledge_domain": proposal.knowledge_domain,
            "source_type": proposal.source_type,
            "source_title": proposal.source_title,
            "source_family": proposal.source_family,
            "original_extraction": {
                "extraction_id": proposal.extraction_id,
                "source_id": proposal.source_id,
                "segment_id": proposal.segment_id,
                "source_type": proposal.source_type,
                "knowledge_domain": proposal.knowledge_domain,
                "features": proposal.features,
                "confidence": proposal.confidence,
                "extractor": proposal.extractor,
            },
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        review_path = Path(paths.review_dir) / f"{review_id}.json"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return AdapterCompileResult(
            status="compiled",
            knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
            semantic_extractions=1,
            pending_reviews=1,
        )


def route_knowledge_source(source: KnowledgeLibrarySourceRecord) -> CompilerRoute:
    """Select the typed compiler adapter for one Knowledge Library source."""
    if source.source_type == KNOWLEDGE_SOURCE_TYPE_TEXT:
        if source.domain in {"psychotherapy", "psychedelic_research"}:
            return CompilerRoute(
                compiler=TextSemanticCompiler(),
                knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
                supported=True,
            )
        if source.domain == "vocal_icaro":
            return CompilerRoute(
                compiler=TextSemanticCompiler(),
                knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
                supported=True,
            )
        return CompilerRoute(
            compiler=None,
            supported=False,
            unsupported_reason=(
                f"Unsupported knowledge library domain/source_type: "
                f"{source.domain}/{source.source_type}"
            ),
        )
    if source.source_type == KNOWLEDGE_SOURCE_TYPE_AUDIO_EXTRACT:
        if source.domain == "vocal_icaro":
            return CompilerRoute(
                compiler=AudioExtractCompiler(),
                knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
                supported=True,
            )
        return CompilerRoute(
            compiler=None,
            supported=False,
            unsupported_reason=(
                f"Unsupported knowledge library domain/source_type: "
                f"{source.domain}/{source.source_type}"
            ),
        )
    return CompilerRoute(
        compiler=None,
        supported=False,
        unsupported_reason=(
            f"Unsupported knowledge library source_type: {source.source_type}"
        ),
    )
