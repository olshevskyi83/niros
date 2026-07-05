"""Tests for TLE pipeline coherence audit."""

from __future__ import annotations

from pathlib import Path

from niros_tle.pipeline_audit import (
    RECOMMENDED_NEXT_STEP,
    TLEPipelineAuditResult,
    audit_tle_pipeline,
)

TLE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = TLE_ROOT.parent


def test_audit_passes_with_current_components():
    result = audit_tle_pipeline(tle_root=TLE_ROOT, repo_root=REPO_ROOT)
    assert isinstance(result, TLEPipelineAuditResult)
    assert result.passed is True
    assert result.data_flow_verified is True


def test_checked_modules_listed():
    result = audit_tle_pipeline(tle_root=TLE_ROOT, repo_root=REPO_ROOT)
    expected = {
        "corpus_registry",
        "chunk_builder",
        "meaning_unit_extractor",
        "candidate_pattern_builder",
        "pattern_contract",
        "extraction_pipeline",
        "pattern_consolidation",
        "pattern_evidence",
        "corpus_manifest",
        "human_review_queue",
        "approved_pattern_library",
        "audio_lab",
        "embeddings",
    }
    assert expected.issubset(set(result.checked_modules))


def test_future_missing_components_are_warnings():
    result = audit_tle_pipeline(tle_root=TLE_ROOT, repo_root=REPO_ROOT)
    assert result.missing_components == ()
    assert any("human review queue" in warning.lower() for warning in result.warnings)
    assert any("approved pattern library" in warning.lower() for warning in result.warnings)
    assert any("audio lab" in warning.lower() for warning in result.warnings)
    assert any("embedding" in warning.lower() for warning in result.warnings)


def test_no_niros_core_import_required():
    niros_dir = REPO_ROOT / "niros"
    matches = []
    for path in niros_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "pipeline_audit" in text or "audit_tle_pipeline" in text:
            matches.append(str(path.relative_to(REPO_ROOT)))
    assert not matches


def test_recommended_next_step_mentions_human_review_queue():
    result = audit_tle_pipeline(tle_root=TLE_ROOT, repo_root=REPO_ROOT)
    assert "human review queue" in result.recommended_next_step.lower()


def test_deterministic_output():
    first = audit_tle_pipeline(tle_root=TLE_ROOT, repo_root=REPO_ROOT)
    second = audit_tle_pipeline(tle_root=TLE_ROOT, repo_root=REPO_ROOT)
    assert first == second
    assert first.recommended_next_step == RECOMMENDED_NEXT_STEP
