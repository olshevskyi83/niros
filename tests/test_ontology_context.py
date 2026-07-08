"""Tests for incremental ontology context behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from niros.master_ontology import (
    MECHANISM_PRESENCE_KNOWN,
    MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW,
    OntologyRepository,
    SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM,
)
from niros.ontology_context import (
    OntologyContext,
    classify_mechanism_presence,
    clear_default_ontology_context_cache,
    gate_decision_for_mechanism_presence,
    get_known_mechanism_ids,
    get_mechanism_context,
    load_ontology_context,
    ontology_is_complete,
)


@pytest.fixture(autouse=True)
def _reset_default_context_cache() -> None:
    clear_default_ontology_context_cache()
    yield
    clear_default_ontology_context_cache()


def test_ontology_loads_with_only_seed_mechanisms() -> None:
    context = load_ontology_context()

    mechanism_ids = context.get_known_mechanism_ids()
    assert mechanism_ids
    assert len(mechanism_ids) < 50
    assert "experiential_avoidance" in mechanism_ids


def test_context_reports_ontology_is_complete_false() -> None:
    context = load_ontology_context()

    assert context.ontology_is_complete() is False
    assert ontology_is_complete() is False
    assert context.ontology.ontology_is_complete is False


def test_known_mechanism_returns_known() -> None:
    context = load_ontology_context()
    result = context.classify_mechanism_presence("experiential_avoidance")

    assert result.presence == MECHANISM_PRESENCE_KNOWN
    assert result.mechanism_id == "experiential_avoidance"
    assert result.suggested_gate_decision == "confirms_existing_mechanism"


def test_known_mechanism_by_name_returns_known() -> None:
    result = classify_mechanism_presence("Experiential Avoidance")

    assert result.presence == MECHANISM_PRESENCE_KNOWN
    assert result.mechanism_id == "experiential_avoidance"


def test_unknown_mechanism_returns_unknown_possible_new() -> None:
    context = load_ontology_context()
    result = context.classify_mechanism_presence("trauma_memory_loops")

    assert result.presence == MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW
    assert result.mechanism_id == ""
    assert result.suggested_gate_decision == SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM


def test_unknown_mechanism_is_not_treated_as_invalid() -> None:
    result = classify_mechanism_presence("central_sensitization")

    assert result.presence == MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW
    assert gate_decision_for_mechanism_presence(result.presence) == (
        SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM
    )


def test_get_mechanism_context_for_known_mechanism() -> None:
    context = get_mechanism_context("experiential_avoidance")

    assert context is not None
    assert context.mechanism_id == "experiential_avoidance"
    assert context.definition
    assert context.coverage in {"minimal", "partial", "strong"}
    assert context.status


def test_get_mechanism_context_for_unknown_returns_none() -> None:
    assert get_mechanism_context("trauma_memory_loops") is None


def test_find_mechanisms_for_problem_returns_linked_mechanisms() -> None:
    context = load_ontology_context()
    mechanisms = context.find_mechanisms_for_problem("anxiety")

    assert mechanisms
    assert all(item.mechanism_id in context.get_known_mechanism_ids() for item in mechanisms)


def test_deprecated_mechanism_classifies_as_deprecated(tmp_path: Path) -> None:
    root = tmp_path / "ontology"
    root.mkdir()
    _write_minimal_ontology_with_deprecated_mechanism(root)
    context = load_ontology_context(root)

    result = context.classify_mechanism_presence("legacy_avoidance")

    assert result.presence == "deprecated"
    assert result.suggested_gate_decision == "skip"


def test_module_level_known_mechanism_ids_match_context() -> None:
    context = load_ontology_context()

    assert get_known_mechanism_ids() == context.get_known_mechanism_ids()


def test_runtime_unchanged_does_not_import_ontology_context() -> None:
    runtime_files = (
        Path("niros/session_engine.py"),
        Path("niros/intervention_strategy.py"),
        Path("niros/ctpc_tle_adapter.py"),
    )
    for path in runtime_files:
        source = path.read_text(encoding="utf-8")
        assert "ontology_context" not in source


def test_knowledge_compiler_imports_ontology_via_consolidator() -> None:
    from niros import knowledge_consolidator

    source = Path(knowledge_consolidator.__file__).read_text(encoding="utf-8")
    assert "ontology_context" in source
    assert "resolve_consolidation_mechanism_key" in source


def test_semantic_extraction_imports_ontology_context() -> None:
    from niros import openai_semantic_extraction_adapter

    source = Path(openai_semantic_extraction_adapter.__file__).read_text(encoding="utf-8")
    assert "ontology_context" in source


def _write_minimal_ontology_with_deprecated_mechanism(root: Path) -> None:
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
                        "associated_mechanism_ids": ["legacy_avoidance"],
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
                        "mechanism_id": "legacy_avoidance",
                        "name": "Legacy Avoidance",
                        "definition": "Deprecated avoidance framing.",
                        "how_it_forms": "Historical model.",
                        "maintaining_logic": "Short-term relief.",
                        "client_signals": ["I avoid feelings."],
                        "associated_problem_ids": ["anxiety"],
                        "therapeutic_responses": ["acceptance"],
                        "therapy_process_ids": ["acceptance_process"],
                        "evidence_status": "unsupported",
                        "status": "deprecated",
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
                        "target_mechanism_ids": ["legacy_avoidance"],
                        "change_logic": "Less struggle, more action.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "psilocybin_relevance.json").write_text(
        json.dumps({"ontology_version": "master_ontology_v1", "psilocybin_relevances": []}),
        encoding="utf-8",
    )
    (root / "ericksonian_patterns.json").write_text(
        json.dumps({"ontology_version": "master_ontology_v1", "ericksonian_patterns": []}),
        encoding="utf-8",
    )
    (root / "session_support_patterns.json").write_text(
        json.dumps({"ontology_version": "master_ontology_v1", "session_support_patterns": []}),
        encoding="utf-8",
    )
    (root / "risk_factors.json").write_text(
        json.dumps({"ontology_version": "master_ontology_v1", "risk_factors": []}),
        encoding="utf-8",
    )
