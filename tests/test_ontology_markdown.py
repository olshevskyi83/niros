"""Tests for Markdown ontology vault parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from niros.ontology_context import clear_default_ontology_context_cache, load_ontology_context
from niros.ontology_markdown import (
    ENTITY_TYPE_MECHANISM,
    ENTITY_TYPE_PRESENTING_CONCERN,
    ENTITY_TYPE_THERAPEUTIC_CHANGE_PROCESS,
    IMPORTANT_MECHANISM_SECTIONS,
    load_markdown_ontology_vault,
    parse_ontology_markdown,
    slugify_ontology_title,
)


FIXTURE_VAULT = Path("tests/fixtures/ontology_vault")


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_default_ontology_context_cache()
    yield
    clear_default_ontology_context_cache()


def test_markdown_ontology_file_loads_experiential_avoidance() -> None:
    path = FIXTURE_VAULT / "02 Mechanisms" / "Experiential Avoidance.md"
    document = parse_ontology_markdown(path.read_text(encoding="utf-8"), source_path=str(path))

    assert document.id == "M-0001"
    assert document.type == ENTITY_TYPE_MECHANISM
    assert document.title == "Experiential Avoidance"
    assert document.status == "draft"
    assert document.evidence_status == "Hypothesis"
    assert "experiential avoidance" in document.aliases


def test_frontmatter_fields_parsed() -> None:
    path = FIXTURE_VAULT / "02 Mechanisms" / "Experiential Avoidance.md"
    document = parse_ontology_markdown(path.read_text(encoding="utf-8"))

    assert document.psilocybin_relevance == "unknown"
    assert isinstance(document.aliases, tuple)
    assert isinstance(document.presenting_concerns, tuple)
    assert isinstance(document.related_mechanisms, tuple)
    assert isinstance(document.therapeutic_processes, tuple)


def test_sections_parsed_for_mechanism() -> None:
    path = FIXTURE_VAULT / "02 Mechanisms" / "Experiential Avoidance.md"
    document = parse_ontology_markdown(path.read_text(encoding="utf-8"))

    for section_name in IMPORTANT_MECHANISM_SECTIONS:
        assert section_name in document.sections

    assert "suppress unwanted internal experiences" in document.sections["Short Definition"]
    assert "Short-term relief reinforces avoidance" in document.sections["How It Is Maintained"]
    assert "I stay busy" in document.sections["Typical Client Signals"]


def test_vault_recursively_loads_all_entity_types() -> None:
    vault = load_markdown_ontology_vault(FIXTURE_VAULT)

    assert len(vault.presenting_concerns) >= 1
    assert len(vault.mechanisms) >= 1
    assert len(vault.therapeutic_change_processes) >= 1
    assert vault.get_document("M-0001") is not None
    assert vault.get_document("PC-0001") is not None
    assert vault.get_document("TCP-0001") is not None


def test_experiential_avoidance_markdown_maps_to_m0001() -> None:
    vault = load_markdown_ontology_vault(FIXTURE_VAULT)
    document = vault.get_mechanism("M-0001")

    assert document is not None
    assert document.title == "Experiential Avoidance"
    assert slugify_ontology_title(document.title) == "experiential_avoidance"


def test_ontology_context_exposes_markdown_entities() -> None:
    context = load_ontology_context(markdown_vault_root=FIXTURE_VAULT)

    assert context.has_markdown_vault()
    assert "M-0001" in context.get_markdown_mechanisms()[0].id or any(
        item.id == "M-0001" for item in context.get_markdown_mechanisms()
    )
    assert context.get_presenting_concern_ids()
    assert context.get_therapeutic_process_ids()
    assert context.get_presenting_concern_context("PC-0001") is not None
    assert context.get_therapeutic_process_context("TCP-0001") is not None


def test_markdown_mechanism_resolves_to_json_consolidation_id() -> None:
    context = load_ontology_context(markdown_vault_root=FIXTURE_VAULT)

    assert context.resolve_consolidation_mechanism_id("M-0001") == "experiential_avoidance"
    assert context.get_mechanism_context("M-0001") is not None
    assert context.get_mechanism_context("experiential_avoidance") is not None


def test_vault_ignores_obsidian_and_ds_store(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    (vault_root / ".obsidian").mkdir(parents=True)
    (vault_root / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")
    (vault_root / ".DS_Store").write_bytes(b"ignored")
    (vault_root / "02 Mechanisms").mkdir(parents=True)
    (vault_root / "02 Mechanisms" / "Sample.md").write_text(
        FIXTURE_VAULT.joinpath("02 Mechanisms", "Experiential Avoidance.md").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    vault = load_markdown_ontology_vault(vault_root)

    assert len(vault.mechanisms) == 1
