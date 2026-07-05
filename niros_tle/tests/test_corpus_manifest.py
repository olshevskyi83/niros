"""Tests for TLE corpus manifest and upload folder structure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

TLE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = TLE_ROOT.parent

EXPECTED_SOURCE_FAMILIES = (
    "erickson",
    "act",
    "ifs",
    "cft",
    "narrative",
    "motivational_interviewing",
    "maria_sabina",
    "shipibo",
    "quechua",
)

CORPUS_SUBDIRS = ("raw", "processed", "metadata")
ALLOWED_FILE_TYPES = (".pdf", ".txt", ".md", ".epub")
MANIFEST_PATH = TLE_ROOT / "metadata" / "corpus_manifest.json"


def _load_manifest() -> list[dict]:
    payloads = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(payloads, list)
    return payloads


def _folder_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [item for item in path.iterdir() if item.is_file()]


@pytest.mark.parametrize("source_family", EXPECTED_SOURCE_FAMILIES)
@pytest.mark.parametrize("subdir", CORPUS_SUBDIRS)
def test_source_family_has_required_subfolders(source_family: str, subdir: str):
    folder = TLE_ROOT / "corpus" / source_family / subdir
    assert folder.is_dir(), f"Missing folder: {folder}"


def test_corpus_manifest_json_exists():
    assert MANIFEST_PATH.is_file()


def test_manifest_includes_all_source_families():
    manifest = _load_manifest()
    manifest_families = {entry["source_family"] for entry in manifest}
    missing = set(EXPECTED_SOURCE_FAMILIES) - manifest_families
    assert not missing, f"Missing manifest entries: {sorted(missing)}"


def test_manifest_paths_exist():
    for entry in _load_manifest():
        for key in ("raw_path", "processed_path", "metadata_path"):
            path = REPO_ROOT / entry[key]
            assert path.is_dir(), f"Manifest path missing: {entry[key]}"


def test_allowed_file_types_are_defined():
    for entry in _load_manifest():
        allowed = entry.get("allowed_file_types")
        assert isinstance(allowed, list)
        assert allowed
        assert tuple(allowed) == ALLOWED_FILE_TYPES


def test_status_is_empty_initially():
    for entry in _load_manifest():
        assert entry["status"] == "empty"


@pytest.mark.parametrize("source_family", EXPECTED_SOURCE_FAMILIES)
def test_raw_files_not_required_yet(source_family: str):
    raw_dir = TLE_ROOT / "corpus" / source_family / "raw"
    files = _folder_files(raw_dir)
    non_gitkeep = [path for path in files if path.name != ".gitkeep"]
    assert non_gitkeep == []


@pytest.mark.parametrize("source_family", EXPECTED_SOURCE_FAMILIES)
def test_processed_folders_empty_or_gitkeep_only(source_family: str):
    processed_dir = TLE_ROOT / "corpus" / source_family / "processed"
    files = _folder_files(processed_dir)
    non_gitkeep = [path for path in files if path.name != ".gitkeep"]
    assert non_gitkeep == []


@pytest.mark.parametrize("source_family", EXPECTED_SOURCE_FAMILIES)
def test_metadata_folders_exist(source_family: str):
    metadata_dir = TLE_ROOT / "corpus" / source_family / "metadata"
    assert metadata_dir.is_dir()


def test_no_niros_core_corpus_integration():
    niros_dir = REPO_ROOT / "niros"
    matches = []
    for path in niros_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "corpus_manifest" in text or "niros_tle/corpus" in text:
            matches.append(str(path.relative_to(REPO_ROOT)))
    assert matches == []
