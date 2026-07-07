"""Tests for Knowledge Factory domain separation."""

from __future__ import annotations

from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_UNKNOWN,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
    ctpc_pattern_relative_path,
    infer_knowledge_domain,
    is_compilable_knowledge_domain,
    is_tle_runtime_eligible_domain,
    knowledge_domain_label,
    normalize_review_knowledge_domain,
)


def test_infer_maria_sabina_as_vocal_icaro() -> None:
    assert (
        infer_knowledge_domain(
            source_id="maria_sabina_chants",
            txt_path="incoming/maria_sabina_batch_001.txt",
        )
        == KNOWLEDGE_DOMAIN_VOCAL_ICARO
    )


def test_infer_psychotherapy_source_as_tle() -> None:
    assert (
        infer_knowledge_domain(source_id="act_workbook", txt_path="incoming/act.txt")
        == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    )


def test_default_infer_without_hints_is_vocal_icaro() -> None:
    assert infer_knowledge_domain(source_id="source_generic") == KNOWLEDGE_DOMAIN_VOCAL_ICARO


def test_normalize_unknown_and_supported_domains() -> None:
    assert normalize_review_knowledge_domain(None) == KNOWLEDGE_DOMAIN_UNKNOWN
    assert normalize_review_knowledge_domain("") == KNOWLEDGE_DOMAIN_UNKNOWN
    assert normalize_review_knowledge_domain("unknown") == KNOWLEDGE_DOMAIN_UNKNOWN
    assert (
        normalize_review_knowledge_domain("psychotherapy_tle")
        == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
    )
    assert normalize_review_knowledge_domain("vocal_icaro") == KNOWLEDGE_DOMAIN_VOCAL_ICARO


def test_compilable_and_tle_eligibility() -> None:
    assert is_compilable_knowledge_domain(KNOWLEDGE_DOMAIN_UNKNOWN) is False
    assert is_compilable_knowledge_domain(KNOWLEDGE_DOMAIN_VOCAL_ICARO) is True
    assert is_compilable_knowledge_domain(KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE) is True
    assert is_tle_runtime_eligible_domain(KNOWLEDGE_DOMAIN_VOCAL_ICARO) is False
    assert is_tle_runtime_eligible_domain(KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE) is True


def test_ctpc_pattern_relative_path_uses_domain_subfolder() -> None:
    assert (
        ctpc_pattern_relative_path(
            KNOWLEDGE_DOMAIN_VOCAL_ICARO,
            "ctp_from_extraction_001",
        )
        == "vocal_icaro/ctp_from_extraction_001.json"
    )
    assert (
        ctpc_pattern_relative_path(
            KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
            "ctp_from_extraction_002",
        )
        == "psychotherapy_tle/ctp_from_extraction_002.json"
    )


def test_knowledge_domain_labels() -> None:
    assert knowledge_domain_label(KNOWLEDGE_DOMAIN_VOCAL_ICARO) == "Vocal / Icaro"
    assert knowledge_domain_label(KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE) == "Psychotherapy / TLE"
    assert knowledge_domain_label(KNOWLEDGE_DOMAIN_UNKNOWN) == "unknown"
