"""Markdown master ontology — parse Obsidian-style vault files with YAML frontmatter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ENTITY_TYPE_PRESENTING_CONCERN = "presenting_concern"
ENTITY_TYPE_MECHANISM = "mechanism"
ENTITY_TYPE_THERAPEUTIC_CHANGE_PROCESS = "therapeutic_change_process"

SUPPORTED_ENTITY_TYPES: frozenset[str] = frozenset(
    {
        ENTITY_TYPE_PRESENTING_CONCERN,
        ENTITY_TYPE_MECHANISM,
        ENTITY_TYPE_THERAPEUTIC_CHANGE_PROCESS,
    }
)

MECHANISM_SECTION_SHORT_DEFINITION = "Short Definition"
MECHANISM_SECTION_PRACTICAL_DESCRIPTION = "Practical Description"
MECHANISM_SECTION_HOW_IT_FORMS = "How It Forms"
MECHANISM_SECTION_HOW_IT_IS_MAINTAINED = "How It Is Maintained"
MECHANISM_SECTION_PROTECTIVE_FUNCTION = "Protective Function"
MECHANISM_SECTION_LONG_TERM_COST = "Long-Term Cost"
MECHANISM_SECTION_TYPICAL_CLIENT_SIGNALS = "Typical Client Signals"
MECHANISM_SECTION_OBSERVABLE_BEHAVIORS = "Observable Behaviors"
MECHANISM_SECTION_TYPICAL_THOUGHTS = "Typical Thoughts"
MECHANISM_SECTION_TYPICAL_EMOTIONS = "Typical Emotions"
MECHANISM_SECTION_BODY_RESPONSES = "Body Responses"
MECHANISM_SECTION_ASSOCIATED_PRESENTING_CONCERNS = "Associated Presenting Concerns"
MECHANISM_SECTION_RELATED_MECHANISMS = "Related Mechanisms"
MECHANISM_SECTION_THERAPEUTIC_CHANGE_PROCESSES = "Therapeutic Change Processes"
MECHANISM_SECTION_USEFUL_INTERVENTIONS = "Useful Interventions"
MECHANISM_SECTION_SESSION_CONSIDERATIONS = "Session Considerations"
MECHANISM_SECTION_CONTRAINDICATIONS = "Contraindications / Cautions"
MECHANISM_SECTION_EVIDENCE_STATUS = "Evidence Status"

IMPORTANT_MECHANISM_SECTIONS: tuple[str, ...] = (
    MECHANISM_SECTION_SHORT_DEFINITION,
    MECHANISM_SECTION_PRACTICAL_DESCRIPTION,
    MECHANISM_SECTION_HOW_IT_FORMS,
    MECHANISM_SECTION_HOW_IT_IS_MAINTAINED,
    MECHANISM_SECTION_PROTECTIVE_FUNCTION,
    MECHANISM_SECTION_LONG_TERM_COST,
    MECHANISM_SECTION_TYPICAL_CLIENT_SIGNALS,
    MECHANISM_SECTION_OBSERVABLE_BEHAVIORS,
    MECHANISM_SECTION_TYPICAL_THOUGHTS,
    MECHANISM_SECTION_TYPICAL_EMOTIONS,
    MECHANISM_SECTION_BODY_RESPONSES,
    MECHANISM_SECTION_ASSOCIATED_PRESENTING_CONCERNS,
    MECHANISM_SECTION_RELATED_MECHANISMS,
    MECHANISM_SECTION_THERAPEUTIC_CHANGE_PROCESSES,
    MECHANISM_SECTION_USEFUL_INTERVENTIONS,
    MECHANISM_SECTION_SESSION_CONSIDERATIONS,
    MECHANISM_SECTION_CONTRAINDICATIONS,
    MECHANISM_SECTION_EVIDENCE_STATUS,
)

SEMANTIC_MATCH_SECTIONS: tuple[str, ...] = (
    MECHANISM_SECTION_SHORT_DEFINITION,
    MECHANISM_SECTION_PRACTICAL_DESCRIPTION,
    MECHANISM_SECTION_HOW_IT_FORMS,
    MECHANISM_SECTION_HOW_IT_IS_MAINTAINED,
    MECHANISM_SECTION_TYPICAL_CLIENT_SIGNALS,
    MECHANISM_SECTION_OBSERVABLE_BEHAVIORS,
    MECHANISM_SECTION_TYPICAL_THOUGHTS,
    MECHANISM_SECTION_BODY_RESPONSES,
    MECHANISM_SECTION_RELATED_MECHANISMS,
    MECHANISM_SECTION_THERAPEUTIC_CHANGE_PROCESSES,
)

DEFAULT_MARKDOWN_ONTOLOGY_VAULT_ROOT = "knowledge_library/ontology_vault"

VAULT_IGNORE_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".obsidian",
        "__MACOSX",
        "templates",
        ".git",
    }
)

VAULT_IGNORE_FILE_NAMES: frozenset[str] = frozenset({".DS_Store"})

_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


class OntologyMarkdownError(Exception):
    """Base error for Markdown ontology parsing."""


class OntologyMarkdownParseError(OntologyMarkdownError):
    """Raised when one Markdown ontology file cannot be parsed."""


@dataclass(frozen=True)
class OntologyMarkdownDocument:
    """One parsed Markdown ontology entity."""

    id: str
    type: str
    status: str
    evidence_status: str
    aliases: tuple[str, ...]
    presenting_concerns: tuple[str, ...]
    related_mechanisms: tuple[str, ...]
    therapeutic_processes: tuple[str, ...]
    psilocybin_relevance: str
    title: str
    sections: dict[str, str]
    source_path: str = ""


@dataclass
class MarkdownOntologyVault:
    """Recursively loaded Markdown ontology vault."""

    root: Path
    presenting_concerns: tuple[OntologyMarkdownDocument, ...] = ()
    mechanisms: tuple[OntologyMarkdownDocument, ...] = ()
    therapeutic_change_processes: tuple[OntologyMarkdownDocument, ...] = ()
    documents_by_id: dict[str, OntologyMarkdownDocument] = field(default_factory=dict)

    def get_document(self, document_id: str) -> OntologyMarkdownDocument | None:
        return self.documents_by_id.get(document_id.strip())

    def get_mechanism(self, document_id: str) -> OntologyMarkdownDocument | None:
        document = self.get_document(document_id)
        if document is None or document.type != ENTITY_TYPE_MECHANISM:
            return None
        return document

    def mechanism_ids(self) -> tuple[str, ...]:
        return tuple(document.id for document in self.mechanisms)

    def presenting_concern_ids(self) -> tuple[str, ...]:
        return tuple(document.id for document in self.presenting_concerns)

    def therapeutic_process_ids(self) -> tuple[str, ...]:
        return tuple(document.id for document in self.therapeutic_change_processes)


def parse_ontology_markdown(text: str, *, source_path: str = "") -> OntologyMarkdownDocument:
    """Parse one Markdown ontology file with YAML frontmatter and section headings."""
    if yaml is None:
        raise OntologyMarkdownParseError("PyYAML is required to parse ontology frontmatter.")

    frontmatter, body = _split_frontmatter(text)
    metadata = yaml.safe_load(frontmatter) or {}
    if not isinstance(metadata, dict):
        raise OntologyMarkdownParseError("Frontmatter must be a YAML mapping.")

    title, sections = _parse_markdown_sections(body)
    document_id = str(metadata.get("id", "")).strip()
    if not document_id:
        raise OntologyMarkdownParseError("Frontmatter id is required.")

    entity_type = str(metadata.get("type", "")).strip().lower()
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise OntologyMarkdownParseError(f"Unsupported ontology type: {entity_type}")

    return OntologyMarkdownDocument(
        id=document_id,
        type=entity_type,
        status=str(metadata.get("status", "draft")).strip().lower() or "draft",
        evidence_status=str(metadata.get("evidence_status", "")).strip(),
        aliases=_as_string_tuple(metadata.get("aliases")),
        presenting_concerns=_as_string_tuple(metadata.get("presenting_concerns")),
        related_mechanisms=_as_string_tuple(metadata.get("related_mechanisms")),
        therapeutic_processes=_as_string_tuple(metadata.get("therapeutic_processes")),
        psilocybin_relevance=str(metadata.get("psilocybin_relevance", "unknown")).strip()
        or "unknown",
        title=title,
        sections=sections,
        source_path=source_path,
    )


def load_markdown_ontology_vault(
    root: str | Path,
    *,
    include_incomplete: bool = True,
) -> MarkdownOntologyVault:
    """Recursively load all Markdown ontology files from an Obsidian-style vault."""
    del include_incomplete
    vault_root = Path(root)
    if not vault_root.exists():
        return MarkdownOntologyVault(root=vault_root)

    presenting: list[OntologyMarkdownDocument] = []
    mechanisms: list[OntologyMarkdownDocument] = []
    processes: list[OntologyMarkdownDocument] = []
    by_id: dict[str, OntologyMarkdownDocument] = {}

    for path in _iter_vault_markdown_files(vault_root):
        try:
            document = parse_ontology_markdown(
                path.read_text(encoding="utf-8"),
                source_path=str(path),
            )
        except OntologyMarkdownParseError:
            continue
        if document.id in by_id:
            continue
        by_id[document.id] = document
        if document.type == ENTITY_TYPE_PRESENTING_CONCERN:
            presenting.append(document)
        elif document.type == ENTITY_TYPE_MECHANISM:
            mechanisms.append(document)
        elif document.type == ENTITY_TYPE_THERAPEUTIC_CHANGE_PROCESS:
            processes.append(document)

    return MarkdownOntologyVault(
        root=vault_root,
        presenting_concerns=tuple(sorted(presenting, key=lambda item: item.id)),
        mechanisms=tuple(sorted(mechanisms, key=lambda item: item.id)),
        therapeutic_change_processes=tuple(sorted(processes, key=lambda item: item.id)),
        documents_by_id=by_id,
    )


def mechanism_semantic_corpus(document: OntologyMarkdownDocument) -> str:
    """Build semantic matching corpus from mechanism meaning fields."""
    parts: list[str] = [document.title, *document.aliases]
    for section_name in SEMANTIC_MATCH_SECTIONS:
        section_text = document.sections.get(section_name, "").strip()
        if section_text:
            parts.append(section_text)
    return " ".join(part for part in parts if part).strip()


def slugify_ontology_title(title: str) -> str:
    """Convert a mechanism title to a slug id compatible with JSON ontology."""
    collapsed = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip().lower())
    return collapsed.strip("_")


def _split_frontmatter(text: str) -> tuple[str, str]:
    match = _FRONTMATTER_PATTERN.match(text)
    if match is None:
        raise OntologyMarkdownParseError("Missing YAML frontmatter.")
    return match.group(1), text[match.end() :]


def _parse_markdown_sections(body: str) -> tuple[str, dict[str, str]]:
    matches = list(_HEADING_PATTERN.finditer(body))
    if not matches:
        return "", {}

    title = ""
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        if level == 1 and not title:
            title = heading
            continue
        if level == 2:
            sections[heading] = content
    return title, sections


def _iter_vault_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if any(part in VAULT_IGNORE_DIR_NAMES for part in path.parts):
            continue
        if path.name in VAULT_IGNORE_FILE_NAMES:
            continue
        if path.name.lower().startswith("template"):
            continue
        yield path


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        cleaned = value.strip()
        return (cleaned,) if cleaned else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()
