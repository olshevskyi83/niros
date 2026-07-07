"""Knowledge Workspace — deterministic local layout for NIROS Knowledge Factory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)

DEFAULT_KNOWLEDGE_ROOT = "knowledge_factory"

REGISTRY_DIR = "registry"
RAW_CORPUS_DIR = "raw_corpus"
EXTRACTIONS_DIR = "extractions"
REVIEW_DIR = "review"
CTPC_DIR = "ctpc"
AUDIO_DIR = "audio"
LOGS_DIR = "logs"

KNOWLEDGE_SUBDIRECTORIES: tuple[str, ...] = (
    REGISTRY_DIR,
    RAW_CORPUS_DIR,
    EXTRACTIONS_DIR,
    REVIEW_DIR,
    CTPC_DIR,
    AUDIO_DIR,
    LOGS_DIR,
)

CTPC_DOMAIN_SUBDIRECTORIES: tuple[str, ...] = (
    f"{CTPC_DIR}/{KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE}",
    f"{CTPC_DIR}/{KNOWLEDGE_DOMAIN_VOCAL_ICARO}",
)

ARTIFACT_TYPE_TO_DIR: dict[str, str] = {
    "registry": REGISTRY_DIR,
    "raw_corpus": RAW_CORPUS_DIR,
    "extractions": EXTRACTIONS_DIR,
    "review": REVIEW_DIR,
    "ctpc": CTPC_DIR,
    "audio": AUDIO_DIR,
    "logs": LOGS_DIR,
}


@dataclass(frozen=True)
class KnowledgeWorkspacePaths:
    root: str
    registry_dir: str
    raw_corpus_dir: str
    extractions_dir: str
    review_dir: str
    ctpc_dir: str
    audio_dir: str
    logs_dir: str


def build_knowledge_workspace_paths(root: str = DEFAULT_KNOWLEDGE_ROOT) -> KnowledgeWorkspacePaths:
    """Return deterministic knowledge workspace paths for a root directory."""
    root_path = Path(root)
    return KnowledgeWorkspacePaths(
        root=str(root_path),
        registry_dir=str(root_path / REGISTRY_DIR),
        raw_corpus_dir=str(root_path / RAW_CORPUS_DIR),
        extractions_dir=str(root_path / EXTRACTIONS_DIR),
        review_dir=str(root_path / REVIEW_DIR),
        ctpc_dir=str(root_path / CTPC_DIR),
        audio_dir=str(root_path / AUDIO_DIR),
        logs_dir=str(root_path / LOGS_DIR),
    )


def ensure_knowledge_workspace(root: str = DEFAULT_KNOWLEDGE_ROOT) -> KnowledgeWorkspacePaths:
    """Create the knowledge workspace root and all subdirectories."""
    paths = build_knowledge_workspace_paths(root)
    Path(paths.root).mkdir(parents=True, exist_ok=True)
    for subdirectory in KNOWLEDGE_SUBDIRECTORIES:
        (Path(paths.root) / subdirectory).mkdir(parents=True, exist_ok=True)
    for subdirectory in CTPC_DOMAIN_SUBDIRECTORIES:
        (Path(paths.root) / subdirectory).mkdir(parents=True, exist_ok=True)
    return paths


def knowledge_artifact_path(
    paths: KnowledgeWorkspacePaths,
    artifact_type: str,
    filename: str,
) -> str:
    """Return the full path for one knowledge artifact within the workspace."""
    directory_name = ARTIFACT_TYPE_TO_DIR.get(artifact_type)
    if directory_name is None:
        raise ValueError(f"Unknown artifact_type: {artifact_type}")

    directory = Path(paths.root) / directory_name
    return str(directory / filename)
