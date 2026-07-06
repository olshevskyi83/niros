"""Tests for Patient Repository MVP."""

from __future__ import annotations

import json

import pytest

from niros.patient_repository import (
    PATIENT_STATUS_ACTIVE,
    PatientRecord,
    PatientRepository,
    SessionRecord,
    create_patient,
    create_session,
    deserialize_repository,
    generate_patient_id,
    generate_session_id,
    get_patient,
    list_sessions_for_patient,
    load_repository,
    patient_record_field_names,
    save_repository,
    serialize_repository,
)


def test_empty_repository_defaults():
    repository = PatientRepository()
    assert repository.patients == ()
    assert repository.sessions == ()


def test_generate_first_patient_id():
    assert generate_patient_id(()) == "PT-000001"


def test_generate_next_patient_id():
    existing = (
        PatientRecord(patient_id="PT-000001", created_at="2026-01-01T00:00:00+00:00"),
        PatientRecord(patient_id="PT-000002", created_at="2026-01-01T00:00:00+00:00"),
    )
    assert generate_patient_id(existing) == "PT-000003"


def test_create_patient_adds_patient():
    repository, patient = create_patient(PatientRepository(), notes="demo")
    assert len(repository.patients) == 1
    assert patient.patient_id == "PT-000001"
    assert patient.status == PATIENT_STATUS_ACTIVE
    assert patient.notes == "demo"


def test_get_patient_returns_patient():
    repository, patient = create_patient(PatientRepository())
    found = get_patient(repository, patient.patient_id)
    assert found == patient


def test_get_patient_missing_returns_none():
    assert get_patient(PatientRepository(), "PT-999999") is None


def test_generate_first_session_id():
    assert generate_session_id("PT-000001", ()) == "PT-000001-S001"


def test_create_session_attaches_session_to_patient():
    repository, patient = create_patient(PatientRepository())
    updated, session = create_session(
        repository,
        patient.patient_id,
        transcript="sample transcript",
        fingerprint_snapshot={"active_signals": ["shame_sensitivity"]},
    )
    assert len(updated.sessions) == 1
    assert session.patient_id == patient.patient_id
    assert session.session_id == "PT-000001-S001"
    assert session.transcript == "sample transcript"
    assert session.fingerprint_snapshot == {"active_signals": ["shame_sensitivity"]}


def test_create_session_unknown_patient_raises():
    with pytest.raises(ValueError, match="Unknown patient_id"):
        create_session(PatientRepository(), "PT-000001")


def test_list_sessions_for_patient_only_returns_matching_patient_sessions():
    repository, first_patient = create_patient(PatientRepository())
    repository, second_patient = create_patient(repository)
    repository, first_session = create_session(repository, first_patient.patient_id, transcript="a")
    repository, _second_session = create_session(repository, first_patient.patient_id, transcript="b")
    repository, other_session = create_session(repository, second_patient.patient_id, transcript="c")

    sessions = list_sessions_for_patient(repository, first_patient.patient_id)
    assert len(sessions) == 2
    assert {session.session_id for session in sessions} == {
        first_session.session_id,
        "PT-000001-S002",
    }
    assert other_session.patient_id != first_patient.patient_id


def test_sessions_sorted_by_session_id():
    repository, patient = create_patient(PatientRepository())
    repository, _third = create_session(repository, patient.patient_id, transcript="third")
    repository, _first = create_session(repository, patient.patient_id, transcript="first")
    repository, _second = create_session(repository, patient.patient_id, transcript="second")

    sessions = list_sessions_for_patient(repository, patient.patient_id)
    assert [session.session_id for session in sessions] == [
        "PT-000001-S001",
        "PT-000001-S002",
        "PT-000001-S003",
    ]


def test_serialization_roundtrip_preserves_patients():
    repository, patient = create_patient(PatientRepository(), notes="keep")
    restored = deserialize_repository(serialize_repository(repository))
    assert restored.patients == (patient,)


def test_serialization_roundtrip_preserves_sessions():
    repository, patient = create_patient(PatientRepository())
    repository, session = create_session(
        repository,
        patient.patient_id,
        input_mode="voice_transcript_mock",
        transcript="text",
        strategy_snapshot={"strategy_id": "strategy_candidate_001"},
    )
    restored = deserialize_repository(serialize_repository(repository))
    assert restored.sessions == (session,)


def test_load_missing_repository_returns_empty_repository():
    assert load_repository("/tmp/nonexistent/patient_repository_missing.json") == PatientRepository()


def test_save_and_load_repository_works(tmp_path):
    path = tmp_path / "patient_repository.json"
    repository, patient = create_patient(PatientRepository(), notes="saved")
    repository, session = create_session(repository, patient.patient_id, transcript="saved text")
    save_repository(repository, path=path)

    loaded = load_repository(path=path)
    assert loaded.patients == (patient,)
    assert loaded.sessions == (session,)
    assert json.loads(path.read_text(encoding="utf-8"))["patients"][0]["patient_id"] == "PT-000001"


def test_patient_ids_are_anonymous_numeric_ids():
    repository, patient = create_patient(PatientRepository())
    assert patient.patient_id.startswith("PT-")
    assert patient.patient_id[3:].isdigit()


def test_no_name_field_exists_on_patient_record():
    assert "name" not in patient_record_field_names()
