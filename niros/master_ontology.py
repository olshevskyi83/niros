"""Master Therapeutic Ontology — structured source/context layer for NIROS knowledge work."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_MASTER_ONTOLOGY_ROOT = "knowledge_library/master_ontology"
ONTOLOGY_MANIFEST_FILENAME = "ontology_manifest.json"
ONTOLOGY_VERSION = "master_ontology_v1"

ONTOLOGY_STATUS_SEED = "seed"
ONTOLOGY_STATUS_DRAFT = "draft"
ONTOLOGY_STATUS_REVIEWED = "reviewed"
ONTOLOGY_STATUS_APPROVED = "approved"
ONTOLOGY_STATUS_DEPRECATED = "deprecated"

ONTOLOGY_COVERAGE_MINIMAL = "minimal"
ONTOLOGY_COVERAGE_PARTIAL = "partial"
ONTOLOGY_COVERAGE_STRONG = "strong"

HUMAN_REVIEW_STATUS_DRAFT = "draft"
HUMAN_REVIEW_STATUS_PENDING_REVIEW = "pending_review"
HUMAN_REVIEW_STATUS_APPROVED = "approved"
HUMAN_REVIEW_STATUS_REJECTED = "rejected"

SUPPORTED_ONTOLOGY_STATUSES: frozenset[str] = frozenset(
    {
        ONTOLOGY_STATUS_SEED,
        ONTOLOGY_STATUS_DRAFT,
        ONTOLOGY_STATUS_REVIEWED,
        ONTOLOGY_STATUS_APPROVED,
        ONTOLOGY_STATUS_DEPRECATED,
    }
)

SUPPORTED_ONTOLOGY_COVERAGE: frozenset[str] = frozenset(
    {
        ONTOLOGY_COVERAGE_MINIMAL,
        ONTOLOGY_COVERAGE_PARTIAL,
        ONTOLOGY_COVERAGE_STRONG,
    }
)

SUPPORTED_HUMAN_REVIEW_STATUSES: frozenset[str] = frozenset(
    {
        HUMAN_REVIEW_STATUS_DRAFT,
        HUMAN_REVIEW_STATUS_PENDING_REVIEW,
        HUMAN_REVIEW_STATUS_APPROVED,
        HUMAN_REVIEW_STATUS_REJECTED,
    }
)

MECHANISM_PRESENCE_KNOWN = "known"
MECHANISM_PRESENCE_UNKNOWN_POSSIBLE_NEW = "unknown_possible_new"
MECHANISM_PRESENCE_DEPRECATED = "deprecated"
MECHANISM_PRESENCE_AMBIGUOUS = "ambiguous"

SEMANTIC_GATE_DECISION_SKIP = "skip"
SEMANTIC_GATE_DECISION_CONFIRMS_EXISTING_MECHANISM = "confirms_existing_mechanism"
SEMANTIC_GATE_DECISION_ADDS_NUANCE_TO_EXISTING = "adds_nuance_to_existing"
SEMANTIC_GATE_DECISION_POTENTIAL_NEW_MECHANISM = "potential_new_mechanism"
SEMANTIC_GATE_DECISION_CONTRADICTION = "contradiction"

EVIDENCE_STATUS_ESTABLISHED = "established"
EVIDENCE_STATUS_EMERGING = "emerging"
EVIDENCE_STATUS_HYPOTHETICAL = "hypothetical"
EVIDENCE_STATUS_UNSUPPORTED = "unsupported"
EVIDENCE_STATUS_CONTRAINDICATED = "contraindicated"

SUPPORTED_EVIDENCE_STATUSES: frozenset[str] = frozenset(
    {
        EVIDENCE_STATUS_ESTABLISHED,
        EVIDENCE_STATUS_EMERGING,
        EVIDENCE_STATUS_HYPOTHETICAL,
        EVIDENCE_STATUS_UNSUPPORTED,
        EVIDENCE_STATUS_CONTRAINDICATED,
    }
)

PSILOCYBIN_CURE_CLAIM_PATTERNS: tuple[str, ...] = (
    r"\bcures?\b",
    r"\bcure for\b",
    r"\beliminates?\b",
    r"\bguarantees?\b",
    r"\bwill fix\b",
    r"\balways resolves\b",
)

ONTOLOGY_FILENAMES: tuple[str, ...] = (
    "problems.json",
    "mechanisms.json",
    "therapy_processes.json",
    "psilocybin_relevance.json",
    "ericksonian_patterns.json",
    "session_support_patterns.json",
    "risk_factors.json",
)


class MasterOntologyError(Exception):
    """Base error for master ontology loading and validation."""


class MasterOntologyValidationError(MasterOntologyError):
    """Raised when ontology data fails validation."""


def normalize_human_review_status(value: str | None) -> str:
    """Normalize legacy review status values to the current vocabulary."""
    cleaned = str(value or "").strip().lower()
    if cleaned in {"", "seed"}:
        return HUMAN_REVIEW_STATUS_DRAFT
    return cleaned


def normalize_ontology_status(value: str | None, *, default: str = ONTOLOGY_STATUS_SEED) -> str:
    cleaned = str(value or "").strip().lower()
    return cleaned or default


def normalize_ontology_coverage(
    value: str | None,
    *,
    default: str = ONTOLOGY_COVERAGE_MINIMAL,
) -> str:
    cleaned = str(value or "").strip().lower()
    return cleaned or default


def _slugify_label(value: str) -> str:
    collapsed = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return collapsed.strip("_")


@dataclass(frozen=True)
class OntologyProblem:
    problem_id: str
    name: str
    presenting_concern: str
    associated_mechanism_ids: tuple[str, ...]
    status: str = ONTOLOGY_STATUS_SEED
    coverage: str = ONTOLOGY_COVERAGE_MINIMAL
    human_review_status: str = HUMAN_REVIEW_STATUS_DRAFT
    source_references: tuple[str, ...] = ()
    runtime_use_notes: str = ""


@dataclass(frozen=True)
class OntologyMechanism:
    mechanism_id: str
    name: str
    definition: str
    how_it_forms: str
    maintaining_logic: str
    client_signals: tuple[str, ...]
    associated_problem_ids: tuple[str, ...]
    therapeutic_responses: tuple[str, ...]
    relevant_therapy_models: tuple[str, ...] = ()
    therapy_process_ids: tuple[str, ...] = ()
    session_risk_notes: str = ""
    integration_relevance: str = ""
    evidence_status: str = EVIDENCE_STATUS_HYPOTHETICAL
    status: str = ONTOLOGY_STATUS_SEED
    coverage: str = ONTOLOGY_COVERAGE_MINIMAL
    source_references: tuple[str, ...] = ()
    human_review_status: str = HUMAN_REVIEW_STATUS_DRAFT


@dataclass(frozen=True)
class OntologyTherapyProcess:
    process_id: str
    name: str
    description: str
    target_mechanism_ids: tuple[str, ...]
    change_logic: str
    status: str = ONTOLOGY_STATUS_SEED
    coverage: str = ONTOLOGY_COVERAGE_MINIMAL
    human_review_status: str = HUMAN_REVIEW_STATUS_DRAFT
    source_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class OntologyPsilocybinRelevance:
    relevance_id: str
    target_type: str
    target_id: str
    relevance_summary: str
    evidence_status: str
    clinical_context_notes: str = ""
    integration_relevance: str = ""
    session_risk_notes: str = ""
    status: str = ONTOLOGY_STATUS_SEED
    coverage: str = ONTOLOGY_COVERAGE_MINIMAL
    human_review_status: str = HUMAN_REVIEW_STATUS_DRAFT
    source_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class OntologyEricksonianPattern:
    pattern_id: str
    name: str
    description: str
    language_function: str
    linked_mechanism_ids: tuple[str, ...] = ()
    linked_process_ids: tuple[str, ...] = ()
    status: str = ONTOLOGY_STATUS_SEED
    coverage: str = ONTOLOGY_COVERAGE_MINIMAL
    human_review_status: str = HUMAN_REVIEW_STATUS_DRAFT
    source_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class OntologySessionSupportPattern:
    pattern_id: str
    name: str
    description: str
    linked_mechanism_ids: tuple[str, ...] = ()
    linked_process_ids: tuple[str, ...] = ()
    session_phase: str = ""
    status: str = ONTOLOGY_STATUS_SEED
    coverage: str = ONTOLOGY_COVERAGE_MINIMAL
    human_review_status: str = HUMAN_REVIEW_STATUS_DRAFT
    source_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class OntologyRiskFactor:
    risk_id: str
    name: str
    description: str
    linked_mechanism_ids: tuple[str, ...] = ()
    linked_problem_ids: tuple[str, ...] = ()
    contraindication_notes: str = ""
    status: str = ONTOLOGY_STATUS_SEED
    coverage: str = ONTOLOGY_COVERAGE_MINIMAL
    human_review_status: str = HUMAN_REVIEW_STATUS_DRAFT
    source_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class MasterOntology:
    version: str
    ontology_is_complete: bool = False
    problems: tuple[OntologyProblem, ...] = ()
    mechanisms: tuple[OntologyMechanism, ...] = ()
    therapy_processes: tuple[OntologyTherapyProcess, ...] = ()
    psilocybin_relevances: tuple[OntologyPsilocybinRelevance, ...] = ()
    ericksonian_patterns: tuple[OntologyEricksonianPattern, ...] = ()
    session_support_patterns: tuple[OntologySessionSupportPattern, ...] = ()
    risk_factors: tuple[OntologyRiskFactor, ...] = ()


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        cleaned = value.strip()
        return (cleaned,) if cleaned else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _require_text(data: dict[str, Any], field_name: str) -> str:
    return str(data.get(field_name, "")).strip()


def _parse_problem(data: dict[str, Any]) -> OntologyProblem:
    return OntologyProblem(
        problem_id=_require_text(data, "problem_id"),
        name=_require_text(data, "name"),
        presenting_concern=_require_text(data, "presenting_concern"),
        associated_mechanism_ids=_as_string_tuple(data.get("associated_mechanism_ids")),
        status=normalize_ontology_status(data.get("status")),
        coverage=normalize_ontology_coverage(data.get("coverage")),
        human_review_status=normalize_human_review_status(data.get("human_review_status")),
        source_references=_as_string_tuple(data.get("source_references")),
        runtime_use_notes=_require_text(data, "runtime_use_notes"),
    )


def _parse_mechanism(data: dict[str, Any]) -> OntologyMechanism:
    return OntologyMechanism(
        mechanism_id=_require_text(data, "mechanism_id"),
        name=_require_text(data, "name"),
        definition=_require_text(data, "definition"),
        how_it_forms=_require_text(data, "how_it_forms"),
        maintaining_logic=_require_text(data, "maintaining_logic"),
        client_signals=_as_string_tuple(data.get("client_signals")),
        associated_problem_ids=_as_string_tuple(data.get("associated_problem_ids")),
        therapeutic_responses=_as_string_tuple(data.get("therapeutic_responses")),
        relevant_therapy_models=_as_string_tuple(data.get("relevant_therapy_models")),
        therapy_process_ids=_as_string_tuple(data.get("therapy_process_ids")),
        session_risk_notes=_require_text(data, "session_risk_notes"),
        integration_relevance=_require_text(data, "integration_relevance"),
        evidence_status=_require_text(data, "evidence_status") or EVIDENCE_STATUS_HYPOTHETICAL,
        status=normalize_ontology_status(data.get("status")),
        coverage=normalize_ontology_coverage(data.get("coverage")),
        source_references=_as_string_tuple(data.get("source_references")),
        human_review_status=normalize_human_review_status(data.get("human_review_status")),
    )


def _parse_therapy_process(data: dict[str, Any]) -> OntologyTherapyProcess:
    return OntologyTherapyProcess(
        process_id=_require_text(data, "process_id"),
        name=_require_text(data, "name"),
        description=_require_text(data, "description"),
        target_mechanism_ids=_as_string_tuple(data.get("target_mechanism_ids")),
        change_logic=_require_text(data, "change_logic"),
        status=normalize_ontology_status(data.get("status")),
        coverage=normalize_ontology_coverage(data.get("coverage")),
        human_review_status=normalize_human_review_status(data.get("human_review_status")),
        source_references=_as_string_tuple(data.get("source_references")),
    )


def _parse_psilocybin_relevance(data: dict[str, Any]) -> OntologyPsilocybinRelevance:
    return OntologyPsilocybinRelevance(
        relevance_id=_require_text(data, "relevance_id"),
        target_type=_require_text(data, "target_type"),
        target_id=_require_text(data, "target_id"),
        relevance_summary=_require_text(data, "relevance_summary"),
        evidence_status=_require_text(data, "evidence_status"),
        clinical_context_notes=_require_text(data, "clinical_context_notes"),
        integration_relevance=_require_text(data, "integration_relevance"),
        session_risk_notes=_require_text(data, "session_risk_notes"),
        status=normalize_ontology_status(data.get("status")),
        coverage=normalize_ontology_coverage(data.get("coverage")),
        human_review_status=normalize_human_review_status(data.get("human_review_status")),
        source_references=_as_string_tuple(data.get("source_references")),
    )


def _parse_ericksonian_pattern(data: dict[str, Any]) -> OntologyEricksonianPattern:
    return OntologyEricksonianPattern(
        pattern_id=_require_text(data, "pattern_id"),
        name=_require_text(data, "name"),
        description=_require_text(data, "description"),
        language_function=_require_text(data, "language_function"),
        linked_mechanism_ids=_as_string_tuple(data.get("linked_mechanism_ids")),
        linked_process_ids=_as_string_tuple(data.get("linked_process_ids")),
        status=normalize_ontology_status(data.get("status")),
        coverage=normalize_ontology_coverage(data.get("coverage")),
        human_review_status=normalize_human_review_status(data.get("human_review_status")),
        source_references=_as_string_tuple(data.get("source_references")),
    )


def _parse_session_support_pattern(data: dict[str, Any]) -> OntologySessionSupportPattern:
    return OntologySessionSupportPattern(
        pattern_id=_require_text(data, "pattern_id"),
        name=_require_text(data, "name"),
        description=_require_text(data, "description"),
        linked_mechanism_ids=_as_string_tuple(data.get("linked_mechanism_ids")),
        linked_process_ids=_as_string_tuple(data.get("linked_process_ids")),
        session_phase=_require_text(data, "session_phase"),
        status=normalize_ontology_status(data.get("status")),
        coverage=normalize_ontology_coverage(data.get("coverage")),
        human_review_status=normalize_human_review_status(data.get("human_review_status")),
        source_references=_as_string_tuple(data.get("source_references")),
    )


def _parse_risk_factor(data: dict[str, Any]) -> OntologyRiskFactor:
    return OntologyRiskFactor(
        risk_id=_require_text(data, "risk_id"),
        name=_require_text(data, "name"),
        description=_require_text(data, "description"),
        linked_mechanism_ids=_as_string_tuple(data.get("linked_mechanism_ids")),
        linked_problem_ids=_as_string_tuple(data.get("linked_problem_ids")),
        contraindication_notes=_require_text(data, "contraindication_notes"),
        status=normalize_ontology_status(data.get("status")),
        coverage=normalize_ontology_coverage(data.get("coverage")),
        human_review_status=normalize_human_review_status(data.get("human_review_status")),
        source_references=_as_string_tuple(data.get("source_references")),
    )


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MasterOntologyError(f"Unable to read ontology file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MasterOntologyError(f"Invalid JSON in ontology file: {path}") from exc
    if not isinstance(payload, dict):
        raise MasterOntologyError(f"Ontology file must contain a JSON object: {path}")
    return payload


def _items_from_payload(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = payload.get(key, ())
    if items is None:
        return []
    if not isinstance(items, list):
        raise MasterOntologyError(f"{key} must be a list.")
    parsed: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise MasterOntologyError(f"{key}[{index}] must be an object.")
        parsed.append(item)
    return parsed


def _contains_cure_claim(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in PSILOCYBIN_CURE_CLAIM_PATTERNS)


def _validate_entity_metadata(
    *,
    prefix: str,
    status: str,
    coverage: str,
    human_review_status: str,
    issues: list[str],
) -> None:
    if status not in SUPPORTED_ONTOLOGY_STATUSES:
        issues.append(f"{prefix}: status is invalid")
    if coverage not in SUPPORTED_ONTOLOGY_COVERAGE:
        issues.append(f"{prefix}: coverage is invalid")
    if human_review_status not in SUPPORTED_HUMAN_REVIEW_STATUSES:
        issues.append(f"{prefix}: human_review_status is invalid")


def _load_ontology_is_complete(root: Path) -> bool:
    manifest_path = root / ONTOLOGY_MANIFEST_FILENAME
    if manifest_path.exists():
        payload = _load_json_file(manifest_path)
        return bool(payload.get("ontology_is_complete", False))
    return False


def validate_master_ontology(ontology: MasterOntology) -> tuple[str, ...]:
    """Return validation issue strings for one loaded master ontology."""
    issues: list[str] = []

    problem_ids = {problem.problem_id for problem in ontology.problems}
    mechanism_ids = {mechanism.mechanism_id for mechanism in ontology.mechanisms}
    process_ids = {process.process_id for process in ontology.therapy_processes}

    if ontology.version.strip() != ONTOLOGY_VERSION:
        issues.append(f"ontology version must be {ONTOLOGY_VERSION}")

    for problem in ontology.problems:
        prefix = f"problem {problem.problem_id or '<missing>'}"
        if not problem.problem_id:
            issues.append("problem_id must not be empty")
            continue
        if not problem.name:
            issues.append(f"{prefix}: name must not be empty")
        if not problem.presenting_concern:
            issues.append(f"{prefix}: presenting_concern must not be empty")
        _validate_entity_metadata(
            prefix=prefix,
            status=problem.status,
            coverage=problem.coverage,
            human_review_status=problem.human_review_status,
            issues=issues,
        )
        if not problem.associated_mechanism_ids:
            issues.append(f"{prefix}: must link to at least one mechanism")
        for mechanism_id in problem.associated_mechanism_ids:
            if mechanism_id not in mechanism_ids:
                issues.append(
                    f"{prefix}: associated_mechanism_ids references unknown mechanism {mechanism_id}"
                )

    for mechanism in ontology.mechanisms:
        prefix = f"mechanism {mechanism.mechanism_id or '<missing>'}"
        if not mechanism.mechanism_id:
            issues.append("mechanism_id must not be empty")
            continue
        if not mechanism.definition:
            issues.append(f"{prefix}: definition must not be empty")
        if not mechanism.maintaining_logic:
            issues.append(f"{prefix}: maintaining_logic must not be empty")
        if not mechanism.client_signals:
            issues.append(f"{prefix}: client_signals must not be empty")
        if not mechanism.therapeutic_responses:
            issues.append(f"{prefix}: therapeutic_responses must not be empty")
        _validate_entity_metadata(
            prefix=prefix,
            status=mechanism.status,
            coverage=mechanism.coverage,
            human_review_status=mechanism.human_review_status,
            issues=issues,
        )
        if mechanism.evidence_status not in SUPPORTED_EVIDENCE_STATUSES:
            issues.append(f"{prefix}: evidence_status is invalid")
        for problem_id in mechanism.associated_problem_ids:
            if problem_id not in problem_ids:
                issues.append(
                    f"{prefix}: associated_problem_ids references unknown problem {problem_id}"
                )
        for process_id in mechanism.therapy_process_ids:
            if process_id not in process_ids:
                issues.append(
                    f"{prefix}: therapy_process_ids references unknown process {process_id}"
                )

    for process in ontology.therapy_processes:
        prefix = f"therapy_process {process.process_id or '<missing>'}"
        if not process.process_id:
            issues.append("process_id must not be empty")
            continue
        if not process.description:
            issues.append(f"{prefix}: description must not be empty")
        if not process.change_logic:
            issues.append(f"{prefix}: change_logic must not be empty")
        _validate_entity_metadata(
            prefix=prefix,
            status=process.status,
            coverage=process.coverage,
            human_review_status=process.human_review_status,
            issues=issues,
        )
        if not process.target_mechanism_ids:
            issues.append(f"{prefix}: must target at least one mechanism")
        for mechanism_id in process.target_mechanism_ids:
            if mechanism_id not in mechanism_ids:
                issues.append(
                    f"{prefix}: target_mechanism_ids references unknown mechanism {mechanism_id}"
                )

    for entry in ontology.psilocybin_relevances:
        prefix = f"psilocybin_relevance {entry.relevance_id or '<missing>'}"
        if not entry.relevance_id:
            issues.append("relevance_id must not be empty")
            continue
        if not entry.evidence_status:
            issues.append(f"{prefix}: evidence_status is required")
        elif entry.evidence_status not in SUPPORTED_EVIDENCE_STATUSES:
            issues.append(f"{prefix}: evidence_status is invalid")
        if not entry.relevance_summary:
            issues.append(f"{prefix}: relevance_summary must not be empty")
        _validate_entity_metadata(
            prefix=prefix,
            status=entry.status,
            coverage=entry.coverage,
            human_review_status=entry.human_review_status,
            issues=issues,
        )
        combined = " ".join(
            (
                entry.relevance_summary,
                entry.clinical_context_notes,
                entry.integration_relevance,
                entry.session_risk_notes,
            )
        )
        if _contains_cure_claim(combined):
            issues.append(f"{prefix}: must not claim cure or guaranteed elimination")
        if entry.target_type == "mechanism" and entry.target_id not in mechanism_ids:
            issues.append(f"{prefix}: target_id references unknown mechanism {entry.target_id}")
        if entry.target_type == "problem" and entry.target_id not in problem_ids:
            issues.append(f"{prefix}: target_id references unknown problem {entry.target_id}")

    return tuple(issues)


@dataclass
class OntologyRepository:
    """Load and validate the master therapeutic ontology from JSON files."""

    root: Path = field(default_factory=lambda: Path(DEFAULT_MASTER_ONTOLOGY_ROOT))

    def load(self) -> MasterOntology:
        """Load the master ontology from the configured root directory."""
        return self.load_from_directory(self.root)

    def load_from_directory(self, directory: str | Path) -> MasterOntology:
        """Load ontology JSON files from one directory."""
        root = Path(directory)
        if not root.exists():
            raise MasterOntologyError(f"Master ontology directory not found: {root}")

        ontology_is_complete = _load_ontology_is_complete(root)
        version = ONTOLOGY_VERSION
        problems: list[OntologyProblem] = []
        mechanisms: list[OntologyMechanism] = []
        therapy_processes: list[OntologyTherapyProcess] = []
        psilocybin_relevances: list[OntologyPsilocybinRelevance] = []
        ericksonian_patterns: list[OntologyEricksonianPattern] = []
        session_support_patterns: list[OntologySessionSupportPattern] = []
        risk_factors: list[OntologyRiskFactor] = []

        loaders: tuple[tuple[str, str, Any], ...] = (
            ("problems.json", "problems", _parse_problem),
            ("mechanisms.json", "mechanisms", _parse_mechanism),
            ("therapy_processes.json", "therapy_processes", _parse_therapy_process),
            ("psilocybin_relevance.json", "psilocybin_relevances", _parse_psilocybin_relevance),
            ("ericksonian_patterns.json", "ericksonian_patterns", _parse_ericksonian_pattern),
            (
                "session_support_patterns.json",
                "session_support_patterns",
                _parse_session_support_pattern,
            ),
            ("risk_factors.json", "risk_factors", _parse_risk_factor),
        )

        for filename, key, parser in loaders:
            path = root / filename
            if not path.exists():
                raise MasterOntologyError(f"Missing ontology file: {path}")
            payload = _load_json_file(path)
            file_version = str(payload.get("ontology_version", "")).strip()
            if file_version and file_version != ONTOLOGY_VERSION:
                raise MasterOntologyError(
                    f"{filename} ontology_version must be {ONTOLOGY_VERSION}"
                )
            for item in _items_from_payload(payload, key):
                parsed = parser(item)
                {
                    "problems": problems,
                    "mechanisms": mechanisms,
                    "therapy_processes": therapy_processes,
                    "psilocybin_relevances": psilocybin_relevances,
                    "ericksonian_patterns": ericksonian_patterns,
                    "session_support_patterns": session_support_patterns,
                    "risk_factors": risk_factors,
                }[key].append(parsed)

        return MasterOntology(
            version=version,
            ontology_is_complete=ontology_is_complete,
            problems=tuple(problems),
            mechanisms=tuple(mechanisms),
            therapy_processes=tuple(therapy_processes),
            psilocybin_relevances=tuple(psilocybin_relevances),
            ericksonian_patterns=tuple(ericksonian_patterns),
            session_support_patterns=tuple(session_support_patterns),
            risk_factors=tuple(risk_factors),
        )

    def load_validated(self) -> MasterOntology:
        """Load ontology and raise when validation fails."""
        ontology = self.load()
        issues = validate_master_ontology(ontology)
        if issues:
            joined = "; ".join(issues)
            raise MasterOntologyValidationError(
                f"Master ontology failed validation: {joined}"
            )
        return ontology
