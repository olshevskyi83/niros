"""TLE end-to-end pipeline coherence audit."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TLE_ROOT = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = TLE_ROOT.parent

REQUIRED_COMPONENTS: tuple[tuple[str, str, str], ...] = (
    ("corpus_registry", "niros_tle.corpus_ingestion", "CorpusRegistry"),
    ("chunk_builder", "niros_tle.chunk_builder", "ChunkBuilder"),
    ("meaning_unit_extractor", "niros_tle.meaning_unit_extractor", "MeaningUnitExtractor"),
    ("candidate_pattern_builder", "niros_tle.candidate_pattern_builder", "CandidatePatternBuilder"),
    ("pattern_contract", "niros_tle.pattern_contract", "TLEPatternRecord"),
    ("extraction_pipeline", "niros_tle.extraction_pipeline", "UniversalPatternExtractionPipeline"),
    ("pattern_consolidation", "niros_tle.pattern_consolidation", "UniversalPatternConsolidator"),
    ("pattern_evidence", "niros_tle.pattern_evidence", "UniversalPatternEvidenceEngine"),
)

OPTIONAL_FUTURE_COMPONENTS: tuple[tuple[str, Path, str], ...] = (
    (
        "human_review_queue",
        TLE_ROOT / "human_review",
        "Human review queue is not implemented yet.",
    ),
    (
        "approved_pattern_library",
        TLE_ROOT / "patterns" / "approved_patterns.json",
        "Approved pattern library is not implemented yet.",
    ),
    (
        "audio_lab",
        TLE_ROOT / "audio_lab",
        "Audio lab is not implemented yet.",
    ),
    (
        "embeddings",
        TLE_ROOT / "embeddings",
        "Embeddings workspace exists but no embedding artifacts are present yet.",
    ),
)

CORPUS_MANIFEST_PATH = TLE_ROOT / "metadata" / "corpus_manifest.json"
RECOMMENDED_NEXT_STEP = (
    "Implement the human review queue before promoting candidate patterns "
    "into an approved universal pattern library."
)


@dataclass(frozen=True)
class TLEPipelineAuditResult:
    passed: bool
    checked_modules: tuple[str, ...]
    missing_components: tuple[str, ...]
    warnings: tuple[str, ...]
    recommended_next_step: str
    data_flow_verified: bool = False
    details: tuple[str, ...] = field(default_factory=tuple)


def audit_tle_pipeline(
    *,
    tle_root: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> TLEPipelineAuditResult:
    """Audit TLE module presence, importability, and logical data-flow compatibility."""
    root = Path(tle_root or TLE_ROOT)
    repository_root = Path(repo_root or DEFAULT_REPO_ROOT)

    checked_modules: list[str] = []
    missing_components: list[str] = []
    warnings: list[str] = []
    details: list[str] = []

    for component_name, module_path, symbol_name in REQUIRED_COMPONENTS:
        checked_modules.append(component_name)
        if not _module_symbol_importable(module_path, symbol_name):
            missing_components.append(component_name)
            continue
        details.append(f"importable:{component_name}")

    if not CORPUS_MANIFEST_PATH.is_file():
        missing_components.append("corpus_manifest")
        checked_modules.append("corpus_manifest")
    else:
        checked_modules.append("corpus_manifest")
        details.append("present:corpus_manifest")

    for component_name, path, message in OPTIONAL_FUTURE_COMPONENTS:
        checked_modules.append(component_name)
        if not _optional_component_present(path):
            warnings.append(message)
            details.append(f"missing_optional:{component_name}")
        else:
            details.append(f"present_optional:{component_name}")

    data_flow_verified = False
    if not missing_components:
        try:
            data_flow_verified = _verify_data_flow(repository_root)
            details.append("data_flow:verified")
        except Exception as exc:
            warnings.append(f"Data flow compatibility check failed: {exc}")
            details.append("data_flow:failed")

    passed = not missing_components and data_flow_verified

    return TLEPipelineAuditResult(
        passed=passed,
        checked_modules=tuple(sorted(set(checked_modules))),
        missing_components=tuple(sorted(set(missing_components))),
        warnings=tuple(warnings),
        recommended_next_step=RECOMMENDED_NEXT_STEP,
        data_flow_verified=data_flow_verified,
        details=tuple(details),
    )


def _module_symbol_importable(module_path: str, symbol_name: str) -> bool:
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return False
    return hasattr(module, symbol_name)


def _optional_component_present(path: Path) -> bool:
    if path.suffix == ".json":
        return path.is_file()
    if path.name == "embeddings":
        if not path.is_dir():
            return False
        artifacts = [
            item
            for item in path.iterdir()
            if item.is_file() and item.name != ".gitkeep"
        ]
        return bool(artifacts)
    return path.is_dir() and any(path.iterdir())


def _verify_data_flow(repo_root: Path) -> bool:
    from niros_tle.candidate_pattern_builder import CandidatePatternBuilder
    from niros_tle.chunk_builder import KnowledgeChunk
    from niros_tle.corpus_ingestion import SourceDocument
    from niros_tle.extraction_pipeline import SourceFragment, UniversalPatternExtractionPipeline
    from niros_tle.meaning_unit_extractor import MeaningUnit
    from niros_tle.pattern_consolidation import UniversalPatternConsolidator
    from niros_tle.pattern_contract import TLEPatternRecord, validate_tle_pattern_record
    from niros_tle.pattern_evidence import UniversalPatternEvidenceEngine

    source_document = SourceDocument(
        document_id="audit_act_sample_txt",
        title="Audit Sample",
        author="unknown",
        source_family="act",
        language="en",
        file_path="niros_tle/corpus/act/raw/audit_sample.txt",
        file_type="txt",
        copyright_status="unknown",
        license="unknown",
        notes="Pipeline audit fixture.",
    )

    knowledge_chunk = KnowledgeChunk(
        chunk_id="audit_act_sample_txt_0001",
        document_id=source_document.document_id,
        source_family=source_document.source_family,
        language=source_document.language,
        chunk_type="paragraph",
        title="Audit Chunk",
        text="You do not need to fight every thought that arrives.",
        page_start=1,
        page_end=1,
        section_path=("Chapter 1",),
        sequence_number=1,
        metadata={"source_document": source_document.document_id},
    )

    meaning_unit = MeaningUnit(
        meaning_unit_id="audit_act_sample_txt_0001_mu_001",
        chunk_id=knowledge_chunk.chunk_id,
        summary="Invite allowing thoughts without immediate struggle.",
        original_span={"start_char": 0, "end_char": 20},
        psychological_functions=("acceptance", "defusion"),
        language_patterns=("permission_based",),
        confidence="high",
        metadata={
            "source_document": source_document.document_id,
            "source_family": source_document.source_family,
        },
    )

    candidate_patterns = CandidatePatternBuilder(repo_root=repo_root).build((meaning_unit,))
    if len(candidate_patterns) != 1:
        raise ValueError("Expected one candidate pattern from audit meaning unit.")

    candidate = candidate_patterns[0]
    tle_pattern = _candidate_to_tle_pattern_record(candidate)
    validate_tle_pattern_record(tle_pattern)

    fragment = SourceFragment(
        source_family=source_document.source_family,
        source_reference="audit_reference",
        language=source_document.language,
        fragment_text=knowledge_chunk.text,
        metadata={"document_id": source_document.document_id},
    )
    pipeline_result = UniversalPatternExtractionPipeline().extract_from_fragment(fragment)
    if pipeline_result.tle_pattern_record is None:
        raise ValueError("Extraction pipeline did not produce a TLE pattern record.")

    consolidator = UniversalPatternConsolidator()
    consolidator.add_pattern(tle_pattern)
    consolidator.add_pattern(pipeline_result.tle_pattern_record)
    clusters = consolidator.build_clusters()
    if not clusters:
        raise ValueError("Consolidation did not produce any pattern clusters.")

    evidence_engine = UniversalPatternEvidenceEngine()
    exports = evidence_engine.evaluate_clusters(clusters)
    if not exports:
        raise ValueError("Evidence engine did not produce any reports.")

    _assert_handoff_fields(source_document, knowledge_chunk, meaning_unit, candidate, tle_pattern)
    return True


def _candidate_to_tle_pattern_record(candidate: Any) -> TLEPatternRecord:
    from niros_tle.pattern_contract import TLEPatternRecord

    slug = candidate.candidate_id.replace("candidate_", "", 1)
    return TLEPatternRecord(
        id=f"tle_{slug}",
        name=candidate.proposed_name,
        psychological_function=candidate.psychological_functions,
        good_for=candidate.possible_good_for,
        avoid_if=candidate.possible_avoid_for,
        language_style=candidate.language_mechanisms,
        rhythm="slow_repetitive",
        semantic_cluster=candidate.psychological_functions,
        spiritual_compatibility=("secular", "agnostic"),
        requires_symbols=(),
        forbidden_symbols=(),
        intensity="low",
        directness="low",
        repetition_level="medium",
        safety_notes=("Avoid strong identity claims",),
        source_family=(candidate.source_family,),
        source_confidence=candidate.confidence,
        extraction_method="manual_seed",
        evidence_refs=(
            {
                "source_family": candidate.source_family,
                "reference_type": "candidate_audit",
                "note": "Mapped from candidate pattern during pipeline audit.",
            },
        ),
        notes="Pipeline audit handoff record.",
        example_use_case=candidate.therapeutic_goal,
    )


def _assert_handoff_fields(
    source_document: Any,
    knowledge_chunk: Any,
    meaning_unit: Any,
    candidate: Any,
    tle_pattern: TLEPatternRecord,
) -> None:
    if knowledge_chunk.document_id != source_document.document_id:
        raise ValueError("KnowledgeChunk document_id must match SourceDocument.")
    if meaning_unit.metadata.get("source_document") != source_document.document_id:
        raise ValueError("MeaningUnit must reference source document metadata.")
    if candidate.source_document != source_document.document_id:
        raise ValueError("CandidatePattern must reference source document.")
    if meaning_unit.meaning_unit_id not in candidate.meaning_unit_ids:
        raise ValueError("CandidatePattern must reference contributing meaning units.")
    if not tle_pattern.psychological_function:
        raise ValueError("TLEPatternRecord must retain psychological functions.")
