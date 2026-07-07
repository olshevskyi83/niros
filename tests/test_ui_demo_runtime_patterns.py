"""Tests for runtime pattern library provenance and CTPC bridge."""

from __future__ import annotations

import json
from pathlib import Path

from niros.ctpc import CanonicalTherapeuticPattern
from niros.ctpc_compiler import serialize_ctpc_pattern
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.ui_demo import (
    build_runtime_pattern_library,
    demo_pattern_library,
    get_runtime_pattern_library_summary,
    merge_runtime_patterns,
)
from niros_tle.universal_pattern import SOURCE_TYPE_CTPC, SOURCE_TYPE_DEMO


def _write_ctpc(path: Path, pattern: CanonicalTherapeuticPattern) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize_ctpc_pattern(pattern), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _psychotherapy_ctpc(pattern_id: str = "ctp_runtime_act") -> CanonicalTherapeuticPattern:
    return CanonicalTherapeuticPattern(
        pattern_id=pattern_id,
        name="Values Clarification",
        source_family="act",
        source_reference="source_act_segment_002",
        therapeutic_function="values_clarification",
        generation_rules=("Ask values-oriented questions.",),
        voice_rules=("Use calm pacing.",),
        confidence=0.84,
        review_status="approved",
        knowledge_domain=KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    )


def test_demo_patterns_marked_as_demo() -> None:
    patterns = demo_pattern_library()

    assert len(patterns) == 8
    assert all(pattern.source_type == SOURCE_TYPE_DEMO for pattern in patterns)


def test_runtime_library_includes_demo_and_psychotherapy_ctpc(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    psychotherapy_dir = Path(paths.ctpc_dir) / KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    _write_ctpc(psychotherapy_dir / "ctp_runtime_act.json", _psychotherapy_ctpc())

    library, summary = build_runtime_pattern_library(str(root))

    assert summary.demo_count == 8
    assert summary.ctpc_count == 1
    assert summary.total_count == 9
    assert summary.tle_badge_label == "Demo + CTPC"
    assert library.pattern_count == 9
    assert any(pattern.source_type == SOURCE_TYPE_CTPC for pattern in library.patterns)


def test_empty_ctpc_falls_back_to_demo_only(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    ensure_knowledge_workspace(str(root))

    library, summary = build_runtime_pattern_library(str(root))

    assert summary.demo_count == 8
    assert summary.ctpc_count == 0
    assert summary.total_count == 8
    assert summary.tle_badge_label == "Demo"
    assert library.pattern_count == 8
    assert all(pattern.source_type == SOURCE_TYPE_DEMO for pattern in library.patterns)


def test_vocal_icaro_ctpc_not_in_runtime_library(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    vocal_dir = Path(paths.ctpc_dir) / KNOWLEDGE_DOMAIN_VOCAL_ICARO
    _write_ctpc(
        vocal_dir / "ctp_vocal_only.json",
        CanonicalTherapeuticPattern(
            pattern_id="ctp_vocal_only",
            name="Chant Invocation",
            source_family="maria_sabina",
            source_reference="source_maria_sabina_batch_001",
            therapeutic_function="spiritual_invocation",
            generation_rules=("Repeat sacred titles.",),
            voice_rules=("Alternate spoken and hummed lines.",),
            confidence=0.8,
            review_status="approved",
            knowledge_domain=KNOWLEDGE_DOMAIN_VOCAL_ICARO,
        ),
    )

    _, summary = build_runtime_pattern_library(str(root))

    assert summary.ctpc_count == 0
    assert summary.total_count == 8


def test_merge_runtime_patterns_deduplicates_by_pattern_id() -> None:
    from niros.ctpc_tle_adapter import ctpc_pattern_to_universal_pattern

    demo = demo_pattern_library()
    ctpc = (
        ctpc_pattern_to_universal_pattern(_psychotherapy_ctpc(pattern_id=demo[0].pattern_id)),
        ctpc_pattern_to_universal_pattern(_psychotherapy_ctpc(pattern_id="ctp_unique")),
    )
    merged = merge_runtime_patterns(demo, ctpc)

    assert len(merged) == 9
    assert merged[0].source_type == SOURCE_TYPE_DEMO
    assert merged[0].pattern_id == demo[0].pattern_id


def test_get_runtime_pattern_library_summary_matches_builder(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    ensure_knowledge_workspace(str(root))

    summary = get_runtime_pattern_library_summary(str(root))

    assert summary.demo_count == 8
    assert summary.ctpc_count == 0
