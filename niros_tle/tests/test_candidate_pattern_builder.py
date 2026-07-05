"""Tests for Candidate Pattern Builder."""

from __future__ import annotations

import json
from pathlib import Path

from niros_tle.candidate_pattern_builder import (
    CANDIDATE_STATUS,
    CandidatePatternBuilder,
    generate_candidate_id,
)
from niros_tle.meaning_unit_extractor import MeaningUnit


def _meaning_unit(
    *,
    meaning_unit_id: str,
    summary: str,
    psychological_functions: tuple[str, ...],
    language_patterns: tuple[str, ...],
    confidence: str = "medium",
    source_document: str = "act_sample_txt",
    source_family: str = "act",
) -> MeaningUnit:
    return MeaningUnit(
        meaning_unit_id=meaning_unit_id,
        chunk_id="act_sample_txt_0001",
        summary=summary,
        original_span={"start_char": 0, "end_char": 20},
        psychological_functions=psychological_functions,
        language_patterns=language_patterns,
        confidence=confidence,
        metadata={
            "source_document": source_document,
            "source_family": source_family,
        },
    )


def test_single_meaning_unit():
    unit = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
        confidence="high",
    )
    candidates = CandidatePatternBuilder().build((unit,))
    assert len(candidates) == 1
    assert candidates[0].meaning_unit_ids == ("act_sample_txt_0001_mu_001",)
    assert candidates[0].proposed_name == "Acceptance Invitation"


def test_multiple_meaning_units_merge_equivalent_mechanisms():
    first = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance", "defusion"),
        language_patterns=("permission_based", "reframing"),
    )
    second = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_002",
        summary="Encourage noticing thoughts without immediate resistance.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
    )
    candidates = CandidatePatternBuilder().build((second, first))
    assert len(candidates) == 1
    assert set(candidates[0].meaning_unit_ids) == {
        "act_sample_txt_0001_mu_001",
        "act_sample_txt_0001_mu_002",
    }


def test_keep_different_mechanisms_separate():
    acceptance = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
    )
    agency = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_002",
        summary="Support incremental choice toward valued action.",
        psychological_functions=("agency_restoration",),
        language_patterns=("future_orientation",),
    )
    candidates = CandidatePatternBuilder().build((acceptance, agency))
    assert len(candidates) == 2
    names = {candidate.proposed_name for candidate in candidates}
    assert names == {"Acceptance Invitation", "Agency Restoration"}


def test_confidence_preserved():
    units = (
        _meaning_unit(
            meaning_unit_id="act_sample_txt_0001_mu_001",
            summary="Invite allowing thoughts without struggle.",
            psychological_functions=("acceptance",),
            language_patterns=("permission_based",),
            confidence="low",
        ),
        _meaning_unit(
            meaning_unit_id="act_sample_txt_0001_mu_002",
            summary="Encourage noticing thoughts without immediate resistance.",
            psychological_functions=("acceptance",),
            language_patterns=("permission_based",),
            confidence="high",
        ),
    )
    candidates = CandidatePatternBuilder().build(units)
    assert candidates[0].confidence == "high"


def test_evidence_preserved():
    unit = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
    )
    candidate = CandidatePatternBuilder().build((unit,))[0]
    assert candidate.supporting_evidence == (
        {
            "meaning_unit_id": "act_sample_txt_0001_mu_001",
            "summary": "Invite allowing thoughts without struggle.",
        },
    )


def test_deterministic_ids():
    unit = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
    )
    assert generate_candidate_id("act", "acceptance", 1) == "candidate_act_acceptance_001"
    first = CandidatePatternBuilder().build((unit,))
    second = CandidatePatternBuilder().build((unit,))
    assert first[0].candidate_id == second[0].candidate_id


def test_deterministic_output():
    units = (
        _meaning_unit(
            meaning_unit_id="act_sample_txt_0001_mu_002",
            summary="Encourage noticing thoughts without immediate resistance.",
            psychological_functions=("acceptance",),
            language_patterns=("permission_based",),
        ),
        _meaning_unit(
            meaning_unit_id="act_sample_txt_0001_mu_001",
            summary="Invite allowing thoughts without struggle.",
            psychological_functions=("acceptance",),
            language_patterns=("permission_based",),
        ),
    )
    first = CandidatePatternBuilder().build(units)
    second = CandidatePatternBuilder().build(units)
    assert [candidate.to_dict() for candidate in first] == [
        candidate.to_dict() for candidate in second
    ]


def test_status_is_candidate():
    unit = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
    )
    candidate = CandidatePatternBuilder().build((unit,))[0]
    assert candidate.status == CANDIDATE_STATUS


def test_no_copyrighted_text_copied():
    unit = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
    )
    candidate = CandidatePatternBuilder().build((unit,))[0]
    serialized = json.dumps(candidate.to_dict())
    assert "original_span" not in serialized
    assert '"start_char"' not in serialized
    assert unit.summary in serialized


def test_output_written_to_processed_candidate_patterns(tmp_path: Path):
    unit = _meaning_unit(
        meaning_unit_id="act_sample_txt_0001_mu_001",
        summary="Invite allowing thoughts without struggle.",
        psychological_functions=("acceptance",),
        language_patterns=("permission_based",),
    )
    builder = CandidatePatternBuilder(repo_root=tmp_path)
    candidates = builder.build_and_save((unit,))
    output_path = (
        tmp_path
        / "niros_tle"
        / "corpus"
        / "act"
        / "processed"
        / "candidate_patterns"
        / "act_sample_txt.candidate_patterns.json"
    )
    assert output_path.is_file()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["candidate_count"] == len(candidates)


def test_no_niros_core_candidate_pattern_builder_integration():
    repo_root = Path(__file__).resolve().parents[2]
    niros_dir = repo_root / "niros"
    matches = []
    for path in niros_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "candidate_pattern_builder" in text or "CandidatePatternBuilder" in text:
            matches.append(str(path.relative_to(repo_root)))
    assert matches == []
