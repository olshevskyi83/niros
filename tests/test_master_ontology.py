"""Tests for master therapeutic ontology loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from niros.master_ontology import (
    DEFAULT_MASTER_ONTOLOGY_ROOT,
    MasterOntology,
    MasterOntologyValidationError,
    OntologyRepository,
    validate_master_ontology,
)


def _repo_root() -> Path:
    return Path(DEFAULT_MASTER_ONTOLOGY_ROOT)


def test_default_ontology_files_load() -> None:
    ontology = OntologyRepository(_repo_root()).load_validated()

    assert ontology.version == "master_ontology_v1"
    assert ontology.ontology_is_complete is False
    assert len(ontology.problems) >= 5
    assert len(ontology.mechanisms) >= 5
    assert len(ontology.therapy_processes) >= 3
    assert len(ontology.psilocybin_relevances) >= 1


def test_problems_map_to_mechanisms() -> None:
    ontology = OntologyRepository(_repo_root()).load_validated()
    mechanism_ids = {mechanism.mechanism_id for mechanism in ontology.mechanisms}

    for problem in ontology.problems:
        assert problem.associated_mechanism_ids
        assert set(problem.associated_mechanism_ids).issubset(mechanism_ids)


def test_mechanisms_map_to_therapy_processes() -> None:
    ontology = OntologyRepository(_repo_root()).load_validated()
    process_ids = {process.process_id for process in ontology.therapy_processes}

    linked = {
        process_id
        for mechanism in ontology.mechanisms
        for process_id in mechanism.therapy_process_ids
    }
    assert linked
    assert linked.issubset(process_ids)


def test_psilocybin_relevance_requires_evidence_status(tmp_path: Path) -> None:
    root = tmp_path / "ontology"
    root.mkdir()
    _write_minimal_valid_ontology(root)
    payload = json.loads((root / "psilocybin_relevance.json").read_text(encoding="utf-8"))
    payload["psilocybin_relevances"][0]["evidence_status"] = ""
    (root / "psilocybin_relevance.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    ontology = OntologyRepository(root).load()
    issues = validate_master_ontology(ontology)
    assert any("evidence_status is required" in issue for issue in issues)


def test_invalid_ontology_missing_mechanism_link_fails_validation(tmp_path: Path) -> None:
    root = tmp_path / "ontology"
    root.mkdir()
    _write_minimal_valid_ontology(root)
    payload = json.loads((root / "problems.json").read_text(encoding="utf-8"))
    payload["problems"][0]["associated_mechanism_ids"] = ["missing_mechanism"]
    (root / "problems.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MasterOntologyValidationError):
        OntologyRepository(root).load_validated()


def test_invalid_ontology_missing_required_mechanism_fields_fails_validation(tmp_path: Path) -> None:
    root = tmp_path / "ontology"
    root.mkdir()
    _write_minimal_valid_ontology(root)
    payload = json.loads((root / "mechanisms.json").read_text(encoding="utf-8"))
    payload["mechanisms"][0]["therapeutic_responses"] = []
    (root / "mechanisms.json").write_text(json.dumps(payload), encoding="utf-8")

    ontology = OntologyRepository(root).load()
    issues = validate_master_ontology(ontology)
    assert any("therapeutic_responses must not be empty" in issue for issue in issues)


def test_psilocybin_relevance_rejects_cure_claims(tmp_path: Path) -> None:
    root = tmp_path / "ontology"
    root.mkdir()
    _write_minimal_valid_ontology(root)
    payload = json.loads((root / "psilocybin_relevance.json").read_text(encoding="utf-8"))
    payload["psilocybin_relevances"][0]["relevance_summary"] = (
        "Psilocybin cures depression for everyone."
    )
    (root / "psilocybin_relevance.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    ontology = OntologyRepository(root).load()
    issues = validate_master_ontology(ontology)
    assert any("must not claim cure" in issue for issue in issues)


def test_seed_examples_include_requested_mechanisms_and_patterns() -> None:
    ontology = OntologyRepository(_repo_root()).load_validated()
    mechanism_ids = {mechanism.mechanism_id for mechanism in ontology.mechanisms}
    process_ids = {process.process_id for process in ontology.therapy_processes}
    pattern_ids = {pattern.pattern_id for pattern in ontology.ericksonian_patterns}

    for seed_id in (
        "experiential_avoidance",
        "cognitive_fusion",
        "shame_sensitivity",
        "harsh_self_criticism",
        "rumination",
        "addictive_relief_cycle",
        "pain_catastrophizing",
    ):
        assert seed_id in mechanism_ids

    assert "surrender" in process_ids
    assert "emotional_breakthrough" in process_ids
    assert "indirect_suggestion" in pattern_ids


def test_runtime_modules_do_not_import_master_ontology() -> None:
    runtime_files = (
        Path("niros/session_engine.py"),
        Path("niros/intervention_strategy.py"),
        Path("niros/ctpc_tle_adapter.py"),
    )
    for path in runtime_files:
        source = path.read_text(encoding="utf-8")
        assert "master_ontology" not in source


def test_knowledge_consolidator_imports_ontology_context() -> None:
    source = Path("niros/knowledge_consolidator.py").read_text(encoding="utf-8")
    assert "ontology_context" in source


def test_legacy_human_review_status_seed_normalizes_to_draft(tmp_path: Path) -> None:
    root = tmp_path / "ontology"
    root.mkdir()
    _write_minimal_valid_ontology(root)
    ontology = OntologyRepository(root).load_validated()

    assert ontology.problems[0].human_review_status == "draft"
    assert ontology.mechanisms[0].human_review_status == "draft"


def test_invalid_status_fails_validation(tmp_path: Path) -> None:
    root = tmp_path / "ontology"
    root.mkdir()
    _write_minimal_valid_ontology(root)
    payload = json.loads((root / "mechanisms.json").read_text(encoding="utf-8"))
    payload["mechanisms"][0]["status"] = "published"
    (root / "mechanisms.json").write_text(json.dumps(payload), encoding="utf-8")

    ontology = OntologyRepository(root).load()
    issues = validate_master_ontology(ontology)
    assert any("status is invalid" in issue for issue in issues)


def _write_minimal_valid_ontology(root: Path) -> None:
    (root / "ontology_manifest.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "ontology_is_complete": False,
            }
        ),
        encoding="utf-8",
    )
    (root / "problems.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "problems": [
                    {
                        "problem_id": "anxiety",
                        "name": "Anxiety",
                        "presenting_concern": "Persistent worry.",
                        "associated_mechanism_ids": ["experiential_avoidance"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "mechanisms.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "mechanisms": [
                    {
                        "mechanism_id": "experiential_avoidance",
                        "name": "Experiential Avoidance",
                        "definition": "Avoidance of internal experience.",
                        "how_it_forms": "Learned escape.",
                        "maintaining_logic": "Short-term relief maintains the loop.",
                        "client_signals": ["I avoid feelings."],
                        "associated_problem_ids": ["anxiety"],
                        "therapeutic_responses": ["acceptance"],
                        "therapy_process_ids": ["acceptance_process"],
                        "evidence_status": "established",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "therapy_processes.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "therapy_processes": [
                    {
                        "process_id": "acceptance_process",
                        "name": "Acceptance Process",
                        "description": "Willingness to feel.",
                        "target_mechanism_ids": ["experiential_avoidance"],
                        "change_logic": "Less struggle, more action.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "psilocybin_relevance.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "psilocybin_relevances": [
                    {
                        "relevance_id": "psi_rel_experiential_avoidance",
                        "target_type": "mechanism",
                        "target_id": "experiential_avoidance",
                        "relevance_summary": "May support contact with avoided experience in supported settings.",
                        "evidence_status": "emerging",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "ericksonian_patterns.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "ericksonian_patterns": [
                    {
                        "pattern_id": "indirect_suggestion",
                        "name": "Indirect Suggestion",
                        "description": "Implied change language.",
                        "language_function": "Reduce resistance.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "session_support_patterns.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "session_support_patterns": [
                    {
                        "pattern_id": "preparation_safety_frame",
                        "name": "Preparation Safety Frame",
                        "description": "Establish safety before depth.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "risk_factors.json").write_text(
        json.dumps(
            {
                "ontology_version": "master_ontology_v1",
                "risk_factors": [
                    {
                        "risk_id": "unmanaged_suicidality",
                        "name": "Unmanaged Suicidality",
                        "description": "Active suicidal risk without adequate support.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
