"""Patient Repository — local-first anonymous patient and session storage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_REPOSITORY_PATH = Path("data/patient_repository.json")

PATIENT_STATUS_ACTIVE = "active"
INPUT_MODE_TEXT = "text"


@dataclass(frozen=True)
class PatientRecord:
    patient_id: str
    created_at: str
    status: str = PATIENT_STATUS_ACTIVE
    notes: str = ""


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    patient_id: str
    created_at: str
    input_mode: str = INPUT_MODE_TEXT
    transcript: str = ""
    fingerprint_snapshot: dict[str, Any] = field(default_factory=dict)
    strategy_snapshot: dict[str, Any] = field(default_factory=dict)
    explanation_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PatientRepository:
    patients: tuple[PatientRecord, ...] = ()
    sessions: tuple[SessionRecord, ...] = ()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def generate_patient_id(existing_patients: Iterable[PatientRecord]) -> str:
    """Return the next anonymous patient ID: PT-000001, PT-000002, ..."""
    numbers: list[int] = []
    for patient in existing_patients:
        if patient.patient_id.startswith("PT-"):
            suffix = patient.patient_id[3:]
            if suffix.isdigit():
                numbers.append(int(suffix))
    next_number = max(numbers, default=0) + 1
    return f"PT-{next_number:06d}"


def generate_session_id(
    patient_id: str,
    existing_sessions: Iterable[SessionRecord],
) -> str:
    """Return the next session ID for a patient: PT-000001-S001, ..."""
    prefix = f"{patient_id}-S"
    numbers: list[int] = []
    for session in existing_sessions:
        if session.patient_id != patient_id:
            continue
        if not session.session_id.startswith(prefix):
            continue
        suffix = session.session_id[len(prefix) :]
        if suffix.isdigit():
            numbers.append(int(suffix))
    next_number = max(numbers, default=0) + 1
    return f"{patient_id}-S{next_number:03d}"


def create_patient(
    repository: PatientRepository,
    notes: str = "",
) -> tuple[PatientRepository, PatientRecord]:
    """Add a new anonymous patient record."""
    patient = PatientRecord(
        patient_id=generate_patient_id(repository.patients),
        created_at=_utc_now_iso(),
        notes=notes,
    )
    updated = PatientRepository(
        patients=repository.patients + (patient,),
        sessions=repository.sessions,
    )
    return updated, patient


def create_session(
    repository: PatientRepository,
    patient_id: str,
    *,
    input_mode: str = INPUT_MODE_TEXT,
    transcript: str = "",
    fingerprint_snapshot: dict[str, Any] | None = None,
    strategy_snapshot: dict[str, Any] | None = None,
    explanation_snapshot: dict[str, Any] | None = None,
) -> tuple[PatientRepository, SessionRecord]:
    """Attach a new session to an existing patient."""
    if get_patient(repository, patient_id) is None:
        raise ValueError(f"Unknown patient_id: {patient_id}")

    session = SessionRecord(
        session_id=generate_session_id(patient_id, repository.sessions),
        patient_id=patient_id,
        created_at=_utc_now_iso(),
        input_mode=input_mode,
        transcript=transcript,
        fingerprint_snapshot=dict(fingerprint_snapshot or {}),
        strategy_snapshot=dict(strategy_snapshot or {}),
        explanation_snapshot=dict(explanation_snapshot or {}),
    )
    updated = PatientRepository(
        patients=repository.patients,
        sessions=repository.sessions + (session,),
    )
    return updated, session


def get_patient(
    repository: PatientRepository,
    patient_id: str,
) -> PatientRecord | None:
    """Return a patient by ID, or None if not found."""
    for patient in repository.patients:
        if patient.patient_id == patient_id:
            return patient
    return None


def list_sessions_for_patient(
    repository: PatientRepository,
    patient_id: str,
) -> tuple[SessionRecord, ...]:
    """Return sessions for one patient, sorted by session_id."""
    return tuple(
        sorted(
            (session for session in repository.sessions if session.patient_id == patient_id),
            key=lambda session: session.session_id,
        )
    )


def serialize_repository(repository: PatientRepository) -> dict[str, Any]:
    """Convert a repository to a JSON-serializable dictionary."""
    return {
        "patients": [asdict(patient) for patient in repository.patients],
        "sessions": [asdict(session) for session in repository.sessions],
    }


def deserialize_repository(data: dict[str, Any]) -> PatientRepository:
    """Build a repository from serialized data."""
    patients = tuple(
        PatientRecord(**patient_data) for patient_data in data.get("patients", [])
    )
    sessions = tuple(
        SessionRecord(**session_data) for session_data in data.get("sessions", [])
    )
    return PatientRepository(patients=patients, sessions=sessions)


def save_repository(
    repository: PatientRepository,
    path: str | Path = DEFAULT_REPOSITORY_PATH,
) -> Path:
    """Persist a repository to a local JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(serialize_repository(repository), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


def load_repository(path: str | Path = DEFAULT_REPOSITORY_PATH) -> PatientRepository:
    """Load a repository from disk, or return an empty repository if missing."""
    input_path = Path(path)
    if not input_path.exists():
        return PatientRepository()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    return deserialize_repository(data)


def patient_record_field_names() -> tuple[str, ...]:
    """Return PatientRecord field names for contract checks."""
    return tuple(field.name for field in fields(PatientRecord))
