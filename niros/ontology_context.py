"""Ontology context — incremental, incomplete-but-valid knowledge layer for compiler decisions."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from niros.master_ontology import (
    DEFAULT_MASTER_ONTOLOGY_ROOT,
    MECHANISM_PRESENCE_AMBIGUOUS,
    MECHANISM_PRESENCE_DEPRECATED,
    MECHANISM_PRESENCE_KNOWN,
    MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW,
    ONTOLOGY_STATUS_DEPRECATED,
    OntologyMechanism,
    OntologyProblem,
    OntologyRepository,
    MasterOntology,
    SEMANTIC_GATE_DECISION_ADDS_NUANCE_TO_EXISTING,
    SEMANTIC_GATE_DECISION_CONFIRMS_EXISTING_MECHANISM,
    SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM,
    SEMANTIC_GATE_DECISION_SKIP,
    _slugify_label,
)
from niros.ontology_markdown import (
    DEFAULT_MARKDOWN_ONTOLOGY_VAULT_ROOT,
    ENTITY_TYPE_MECHANISM,
    MarkdownOntologyVault,
    OntologyMarkdownDocument,
    load_markdown_ontology_vault,
    slugify_ontology_title,
)


@dataclass(frozen=True)
class MechanismContext:
    mechanism_id: str
    name: str
    definition: str
    maintaining_logic: str
    status: str
    coverage: str
    human_review_status: str
    client_signals: tuple[str, ...]
    therapeutic_responses: tuple[str, ...]
    associated_problem_ids: tuple[str, ...]
    therapy_process_ids: tuple[str, ...]
    evidence_status: str
    markdown_id: str = ""


@dataclass(frozen=True)
class ProblemContext:
    problem_id: str
    name: str
    presenting_concern: str
    status: str
    coverage: str
    human_review_status: str
    associated_mechanism_ids: tuple[str, ...]
    markdown_id: str = ""


@dataclass(frozen=True)
class TherapeuticProcessContext:
    process_id: str
    name: str
    description: str
    status: str
    evidence_status: str
    markdown_id: str = ""


@dataclass(frozen=True)
class PresentingConcernContext:
    concern_id: str
    name: str
    status: str
    evidence_status: str
    markdown_id: str = ""


@dataclass(frozen=True)
class MechanismPresenceResult:
    presence: str
    mechanism_id: str = ""
    matched_mechanism_ids: tuple[str, ...] = ()
    suggested_gate_decision: str = SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM


class OntologyContext:
    """Read-only view over an incremental master ontology."""

    def __init__(
        self,
        ontology: MasterOntology,
        *,
        root: str | Path | None = None,
        markdown_vault: MarkdownOntologyVault | None = None,
    ) -> None:
        self._ontology = ontology
        self._root = Path(root) if root is not None else Path(DEFAULT_MASTER_ONTOLOGY_ROOT)
        self._markdown_vault = markdown_vault
        self._mechanisms_by_id = {
            mechanism.mechanism_id: mechanism for mechanism in ontology.mechanisms
        }
        self._problems_by_id = {
            problem.problem_id: problem for problem in ontology.problems
        }
        self._mechanism_alias_index = _build_mechanism_alias_index(ontology.mechanisms)
        self._markdown_mechanism_by_id: dict[str, OntologyMarkdownDocument] = {}
        self._markdown_presenting_by_id: dict[str, OntologyMarkdownDocument] = {}
        self._markdown_process_by_id: dict[str, OntologyMarkdownDocument] = {}
        self._consolidation_id_by_markdown_id: dict[str, str] = {}
        self._markdown_id_by_consolidation_id: dict[str, str] = {}
        if markdown_vault is not None:
            self._index_markdown_vault(markdown_vault)

    @property
    def ontology(self) -> MasterOntology:
        return self._ontology

    @property
    def root(self) -> Path:
        return self._root

    @property
    def markdown_vault(self) -> MarkdownOntologyVault | None:
        return self._markdown_vault

    def has_markdown_vault(self) -> bool:
        return self._markdown_vault is not None and bool(self._markdown_vault.documents_by_id)

    def ontology_is_complete(self) -> bool:
        return bool(self._ontology.ontology_is_complete)

    def get_known_mechanism_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._mechanisms_by_id))

    def get_known_problem_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._problems_by_id))

    def get_presenting_concern_ids(self) -> tuple[str, ...]:
        if self._markdown_vault is None:
            return self.get_known_problem_ids()
        markdown_ids = self._markdown_vault.presenting_concern_ids()
        if markdown_ids:
            return markdown_ids
        return self.get_known_problem_ids()

    def get_therapeutic_process_ids(self) -> tuple[str, ...]:
        if self._markdown_vault is None:
            return tuple(process.process_id for process in self._ontology.therapy_processes)
        markdown_ids = self._markdown_vault.therapeutic_process_ids()
        if markdown_ids:
            return markdown_ids
        return tuple(process.process_id for process in self._ontology.therapy_processes)

    def get_markdown_mechanisms(self) -> tuple[OntologyMarkdownDocument, ...]:
        if self._markdown_vault is None:
            return ()
        return self._markdown_vault.mechanisms

    def get_markdown_mechanism(self, document_id: str) -> OntologyMarkdownDocument | None:
        return self._markdown_mechanism_by_id.get(document_id.strip())

    def get_markdown_mechanism_by_consolidation_id(
        self,
        mechanism_id: str,
    ) -> OntologyMarkdownDocument | None:
        markdown_id = self._markdown_id_by_consolidation_id.get(mechanism_id.strip(), "")
        if not markdown_id:
            return None
        return self.get_markdown_mechanism(markdown_id)

    def resolve_consolidation_mechanism_id(self, markdown_document_id: str) -> str:
        """Map a Markdown mechanism document id (e.g. M-0001) to consolidation id."""
        cleaned = markdown_document_id.strip()
        if cleaned in self._consolidation_id_by_markdown_id:
            return self._consolidation_id_by_markdown_id[cleaned]
        return cleaned

    def get_mechanism_context(self, mechanism_id: str) -> MechanismContext | None:
        cleaned = mechanism_id.strip()
        mechanism = self._mechanisms_by_id.get(cleaned)
        if mechanism is not None:
            markdown_id = self._markdown_id_by_consolidation_id.get(cleaned, "")
            return _mechanism_to_context(mechanism, markdown_id=markdown_id)

        markdown_document = self.get_markdown_mechanism(cleaned)
        if markdown_document is not None and markdown_document.type == ENTITY_TYPE_MECHANISM:
            return _markdown_mechanism_to_context(markdown_document)

        markdown_document = self.get_markdown_mechanism_by_consolidation_id(cleaned)
        if markdown_document is not None:
            return _markdown_mechanism_to_context(markdown_document)
        return None

    def get_presenting_concern_context(
        self,
        concern_id: str,
    ) -> PresentingConcernContext | None:
        document = self._markdown_presenting_by_id.get(concern_id.strip())
        if document is None:
            problem = self._problems_by_id.get(concern_id.strip())
            if problem is None:
                return None
            return PresentingConcernContext(
                concern_id=problem.problem_id,
                name=problem.name,
                status=problem.status,
                evidence_status="",
                markdown_id="",
            )
        return PresentingConcernContext(
            concern_id=document.id,
            name=document.title,
            status=document.status,
            evidence_status=document.evidence_status,
            markdown_id=document.id,
        )

    def get_therapeutic_process_context(
        self,
        process_id: str,
    ) -> TherapeuticProcessContext | None:
        document = self._markdown_process_by_id.get(process_id.strip())
        if document is not None:
            return TherapeuticProcessContext(
                process_id=document.id,
                name=document.title,
                description=document.sections.get("Practical Description", ""),
                status=document.status,
                evidence_status=document.evidence_status,
                markdown_id=document.id,
            )
        for process in self._ontology.therapy_processes:
            if process.process_id == process_id.strip():
                return TherapeuticProcessContext(
                    process_id=process.process_id,
                    name=process.name,
                    description=process.description,
                    status=process.status,
                    evidence_status="",
                    markdown_id="",
                )
        return None

    def find_mechanisms_for_problem(self, problem_id: str) -> tuple[MechanismContext, ...]:
        problem = self._problems_by_id.get(problem_id.strip())
        if problem is None:
            return ()
        contexts: list[MechanismContext] = []
        for mechanism_id in problem.associated_mechanism_ids:
            context = self.get_mechanism_context(mechanism_id)
            if context is not None:
                contexts.append(context)
        return tuple(contexts)

    def classify_mechanism_presence(self, candidate_label_or_id: str) -> MechanismPresenceResult:
        """Classify whether a candidate mechanism label is known in the current ontology."""
        cleaned = candidate_label_or_id.strip()
        if not cleaned:
            return MechanismPresenceResult(
                presence=MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW,
                suggested_gate_decision=SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM,
            )

        slug = _slugify_label(cleaned)
        matched_ids = self._match_mechanism_ids(cleaned, slug)
        if not matched_ids:
            return MechanismPresenceResult(
                presence=MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW,
                suggested_gate_decision=SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM,
            )
        if len(matched_ids) > 1:
            return MechanismPresenceResult(
                presence=MECHANISM_PRESENCE_AMBIGUOUS,
                matched_mechanism_ids=matched_ids,
                suggested_gate_decision=SEMANTIC_GATE_DECISION_ADDS_NUANCE_TO_EXISTING,
            )

        mechanism_id = matched_ids[0]
        mechanism = self._mechanisms_by_id.get(mechanism_id)
        if mechanism is not None and mechanism.status == ONTOLOGY_STATUS_DEPRECATED:
            return MechanismPresenceResult(
                presence=MECHANISM_PRESENCE_DEPRECATED,
                mechanism_id=mechanism_id,
                matched_mechanism_ids=matched_ids,
                suggested_gate_decision=SEMANTIC_GATE_DECISION_SKIP,
            )

        markdown_document = self.get_markdown_mechanism(mechanism_id)
        if markdown_document is not None and markdown_document.status == ONTOLOGY_STATUS_DEPRECATED:
            return MechanismPresenceResult(
                presence=MECHANISM_PRESENCE_DEPRECATED,
                mechanism_id=mechanism_id,
                matched_mechanism_ids=matched_ids,
                suggested_gate_decision=SEMANTIC_GATE_DECISION_SKIP,
            )

        return MechanismPresenceResult(
            presence=MECHANISM_PRESENCE_KNOWN,
            mechanism_id=mechanism_id,
            matched_mechanism_ids=matched_ids,
            suggested_gate_decision=SEMANTIC_GATE_DECISION_CONFIRMS_EXISTING_MECHANISM,
        )

    def is_known_mechanism(self, candidate_label_or_id: str) -> bool:
        return (
            self.classify_mechanism_presence(candidate_label_or_id).presence
            == MECHANISM_PRESENCE_KNOWN
        )

    def is_unknown_possible_new_mechanism(self, candidate_label_or_id: str) -> bool:
        return (
            self.classify_mechanism_presence(candidate_label_or_id).presence
            == MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW
        )

    def _index_markdown_vault(self, markdown_vault: MarkdownOntologyVault) -> None:
        for document in markdown_vault.presenting_concerns:
            self._markdown_presenting_by_id[document.id] = document
        for document in markdown_vault.therapeutic_change_processes:
            self._markdown_process_by_id[document.id] = document
        for document in markdown_vault.mechanisms:
            self._markdown_mechanism_by_id[document.id] = document
            consolidation_id = _resolve_markdown_mechanism_consolidation_id(
                document,
                json_mechanism_ids=set(self._mechanisms_by_id),
            )
            self._consolidation_id_by_markdown_id[document.id] = consolidation_id
            self._markdown_id_by_consolidation_id[consolidation_id] = document.id
            self._register_markdown_aliases(document, consolidation_id)

    def _register_markdown_aliases(
        self,
        document: OntologyMarkdownDocument,
        consolidation_id: str,
    ) -> None:
        aliases = {
            document.id,
            document.id.lower(),
            _slugify_label(document.id),
            document.title.strip().lower(),
            _slugify_label(document.title),
            consolidation_id,
            _slugify_label(consolidation_id),
        }
        for alias in document.aliases:
            aliases.add(alias.strip().lower())
            aliases.add(_slugify_label(alias))
        for alias in aliases:
            if not alias:
                continue
            self._mechanism_alias_index.setdefault(alias, set()).add(consolidation_id)

    def _match_mechanism_ids(self, cleaned: str, slug: str) -> tuple[str, ...]:
        lowered = cleaned.lower()
        exact_matches: set[str] = set()
        for key in (cleaned, lowered, slug):
            exact_matches.update(self._mechanism_alias_index.get(key, ()))

        if exact_matches:
            return tuple(sorted(exact_matches))

        partial_matches: set[str] = set()
        for alias, mechanism_ids in self._mechanism_alias_index.items():
            if slug and (slug in alias or alias in slug):
                partial_matches.update(mechanism_ids)
        return tuple(sorted(partial_matches))


def _resolve_markdown_mechanism_consolidation_id(
    document: OntologyMarkdownDocument,
    *,
    json_mechanism_ids: set[str],
) -> str:
    slug = slugify_ontology_title(document.title)
    if slug in json_mechanism_ids:
        return slug
    for alias in document.aliases:
        alias_slug = _slugify_label(alias)
        if alias_slug in json_mechanism_ids:
            return alias_slug
    return document.id


def _build_mechanism_alias_index(
    mechanisms: tuple[OntologyMechanism, ...],
) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for mechanism in mechanisms:
        aliases = {
            mechanism.mechanism_id,
            _slugify_label(mechanism.mechanism_id),
            _slugify_label(mechanism.name),
            mechanism.name.strip().lower(),
        }
        for alias in aliases:
            if not alias:
                continue
            index.setdefault(alias, set()).add(mechanism.mechanism_id)
    return index


def _mechanism_to_context(
    mechanism: OntologyMechanism,
    *,
    markdown_id: str = "",
) -> MechanismContext:
    return MechanismContext(
        mechanism_id=mechanism.mechanism_id,
        name=mechanism.name,
        definition=mechanism.definition,
        maintaining_logic=mechanism.maintaining_logic,
        status=mechanism.status,
        coverage=mechanism.coverage,
        human_review_status=mechanism.human_review_status,
        client_signals=mechanism.client_signals,
        therapeutic_responses=mechanism.therapeutic_responses,
        associated_problem_ids=mechanism.associated_problem_ids,
        therapy_process_ids=mechanism.therapy_process_ids,
        evidence_status=mechanism.evidence_status,
        markdown_id=markdown_id,
    )


def _markdown_mechanism_to_context(document: OntologyMarkdownDocument) -> MechanismContext:
    return MechanismContext(
        mechanism_id=document.id,
        name=document.title,
        definition=document.sections.get("Short Definition", ""),
        maintaining_logic=document.sections.get("How It Is Maintained", ""),
        status=document.status,
        coverage="minimal",
        human_review_status="draft",
        client_signals=_section_lines(document.sections.get("Typical Client Signals", "")),
        therapeutic_responses=_section_lines(
            document.sections.get("Useful Interventions", "")
        ),
        associated_problem_ids=document.presenting_concerns,
        therapy_process_ids=document.therapeutic_processes,
        evidence_status=document.evidence_status,
        markdown_id=document.id,
    )


def _section_lines(text: str) -> tuple[str, ...]:
    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
    return tuple(lines)


def load_ontology_context(
    root: str | Path = DEFAULT_MASTER_ONTOLOGY_ROOT,
    *,
    validated: bool = True,
    markdown_vault_root: str | Path | None = None,
) -> OntologyContext:
    """Load ontology context from JSON seed data and optional Markdown vault."""
    repository = OntologyRepository(Path(root))
    ontology = repository.load_validated() if validated else repository.load()
    markdown_vault = _load_optional_markdown_vault(markdown_vault_root)
    return OntologyContext(ontology, root=root, markdown_vault=markdown_vault)


def _load_optional_markdown_vault(
    markdown_vault_root: str | Path | None,
) -> MarkdownOntologyVault | None:
    candidates: list[Path] = []
    if markdown_vault_root is not None:
        candidates.append(Path(markdown_vault_root))
    else:
        candidates.append(Path(DEFAULT_MARKDOWN_ONTOLOGY_VAULT_ROOT))
    for candidate in candidates:
        if candidate.exists():
            vault = load_markdown_ontology_vault(candidate)
            if vault.documents_by_id:
                return vault
    return None


@lru_cache(maxsize=1)
def _default_context() -> OntologyContext:
    return load_ontology_context()


def ontology_is_complete() -> bool:
    """Return whether the loaded master ontology is marked complete."""
    return _default_context().ontology_is_complete()


def get_known_mechanism_ids() -> tuple[str, ...]:
    return _default_context().get_known_mechanism_ids()


def get_known_problem_ids() -> tuple[str, ...]:
    return _default_context().get_known_problem_ids()


def get_mechanism_context(mechanism_id: str) -> MechanismContext | None:
    return _default_context().get_mechanism_context(mechanism_id)


def find_mechanisms_for_problem(problem_id: str) -> tuple[MechanismContext, ...]:
    return _default_context().find_mechanisms_for_problem(problem_id)


def classify_mechanism_presence(candidate_label_or_id: str) -> MechanismPresenceResult:
    return _default_context().classify_mechanism_presence(candidate_label_or_id)


def gate_decision_for_mechanism_presence(presence: str) -> str:
    """Map mechanism presence classification to a future semantic-gate decision."""
    mapping = {
        MECHANISM_PRESENCE_KNOWN: SEMANTIC_GATE_DECISION_CONFIRMS_EXISTING_MECHANISM,
        MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW: SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM,
        MECHANISM_PRESENCE_DEPRECATED: SEMANTIC_GATE_DECISION_SKIP,
        MECHANISM_PRESENCE_AMBIGUOUS: SEMANTIC_GATE_DECISION_ADDS_NUANCE_TO_EXISTING,
    }
    return mapping.get(presence, SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM)


def clear_default_ontology_context_cache() -> None:
    """Clear cached default context (primarily for tests)."""
    _default_context.cache_clear()
