"""Tests for psychotherapy_tle CTPC → UniversalPattern runtime adapter."""

from __future__ import annotations

import json
from pathlib import Path

from niros.ctpc import CanonicalTherapeuticPattern
from niros.ctpc_compiler import serialize_ctpc_pattern
from niros.ctpc_tle_adapter import (
    ctpc_pattern_to_universal_pattern,
    load_psychotherapy_tle_ctpc_patterns,
    load_psychotherapy_tle_universal_patterns,
    psychotherapy_tle_ctpc_directory,
)
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros_tle.universal_pattern import SOURCE_TYPE_CTPC, SOURCE_TYPE_DEMO


def _sample_ctpc(
    *,
    pattern_id: str = "ctp_from_extraction_act_001",
    knowledge_domain: str = KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
) -> CanonicalTherapeuticPattern:
    return CanonicalTherapeuticPattern(
        pattern_id=pattern_id,
        name="Acceptance Of Difficult Emotions",
        source_family="act",
        source_reference="source_act_segment_001",
        therapeutic_function="acceptance",
        psychological_function="reduce experiential avoidance",
        generation_rules=("Use gentle second-person phrasing.",),
        voice_rules=("Keep tempo slow and supportive.",),
        confidence=0.88,
        review_status="approved",
        knowledge_domain=knowledge_domain,
    )


def _write_ctpc(path: Path, pattern: CanonicalTherapeuticPattern) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize_ctpc_pattern(pattern), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_ctpc_pattern_converts_to_universal_pattern() -> None:
    pattern = _sample_ctpc()
    universal = ctpc_pattern_to_universal_pattern(pattern)

    assert universal.pattern_id == pattern.pattern_id
    assert universal.canonical_name == pattern.name
    assert universal.source_families == ("act",)
    assert universal.source_reference == "source_act_segment_001"
    assert universal.source_type == SOURCE_TYPE_CTPC
    assert universal.confidence == 0.88


def test_load_psychotherapy_tle_ctpc_patterns_ignores_vocal_icaro(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    psychotherapy_dir = Path(paths.ctpc_dir) / KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    vocal_dir = Path(paths.ctpc_dir) / KNOWLEDGE_DOMAIN_VOCAL_ICARO

    _write_ctpc(
        psychotherapy_dir / "ctp_psychotherapy.json",
        _sample_ctpc(pattern_id="ctp_psychotherapy"),
    )
    _write_ctpc(
        vocal_dir / "ctp_vocal.json",
        _sample_ctpc(
            pattern_id="ctp_vocal",
            knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
        ),
    )

    loaded = load_psychotherapy_tle_ctpc_patterns(str(root))

    assert len(loaded) == 1
    assert loaded[0].pattern_id == "ctp_psychotherapy"


def test_load_psychotherapy_tle_universal_patterns_marks_source_type_ctpc(
    tmp_path: Path,
) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    psychotherapy_dir = Path(paths.ctpc_dir) / KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    _write_ctpc(
        psychotherapy_dir / "ctp_psychotherapy.json",
        _sample_ctpc(pattern_id="ctp_psychotherapy"),
    )

    patterns = load_psychotherapy_tle_universal_patterns(str(root))

    assert len(patterns) == 1
    assert patterns[0].source_type == SOURCE_TYPE_CTPC


def test_missing_ctpc_directory_returns_empty_tuple(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    ensure_knowledge_workspace(str(root))

    assert load_psychotherapy_tle_ctpc_patterns(str(root)) == ()
    assert load_psychotherapy_tle_universal_patterns(str(root)) == ()


def test_adapter_reads_only_psychotherapy_tle_subdirectory(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    book_corpus = tmp_path / "niros_tle" / "corpus" / "act" / "raw"
    book_corpus.mkdir(parents=True)
    (book_corpus / "sample.pdf").write_bytes(b"%PDF-1.4 fake")

    psychotherapy_dir = psychotherapy_tle_ctpc_directory(str(root))
    _write_ctpc(
        psychotherapy_dir / "ctp_only_here.json",
        _sample_ctpc(pattern_id="ctp_only_here"),
    )

    loaded = load_psychotherapy_tle_universal_patterns(str(root))

    assert len(loaded) == 1
    assert not any("niros_tle" in str(path) for path in psychotherapy_dir.parent.rglob("*.json"))
