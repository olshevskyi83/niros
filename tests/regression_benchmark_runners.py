"""Collect regression benchmark snapshots across NIROS synthetic human suites."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from niros.reasoning_quality_audit import ReasoningAuditArtifacts, audit_reasoning_quality
from niros.regression_benchmark import (
    RegressionCaseRecord,
    build_case_record,
    build_regression_metrics,
)
from test_end_to_end_pseudo_human_cases import ALL_CASES as PSEUDO_HUMAN_CASES
from test_end_to_end_pseudo_human_cases import run_pseudo_human_pipeline
from test_multilingual_consistency import LANGUAGES, MULTILINGUAL_CASES, run_multilingual_pipeline
from test_pattern_matrix import PATTERN_MATRIX_CASES, run_pattern_matrix_pipeline
from test_reasoning_quality import run_reasoning_audit_pipeline

COMPLEX_CASES_DIR = ROOT / "knowledge" / "test_cases" / "complex"


def _flatten_pattern_groups(groups: tuple[frozenset[str], ...]) -> list[str]:
    patterns: list[str] = []
    for group in groups:
        patterns.extend(sorted(group))
    return sorted(set(patterns))


def _audit_record_from_artifacts(
    *,
    suite: str,
    case_id: str,
    language: str,
    artifacts: ReasoningAuditArtifacts,
) -> RegressionCaseRecord:
    report = audit_reasoning_quality(artifacts)
    metrics = build_regression_metrics(
        expected_patterns=artifacts.expected_patterns,
        detected_patterns=artifacts.detected_pattern_ids,
        coverage_score=report.scores.coverage_score,
        strategy_score=report.scores.strategy_coherence_score,
        scenario_score=report.scores.scenario_coherence_score,
        timeline_score=report.scores.timeline_coherence_score,
    )
    return build_case_record(
        suite=suite,
        case_id=case_id,
        language=language,
        metrics=metrics,
        detected_patterns=artifacts.detected_pattern_ids,
        missing_domains=list(artifacts.coverage_report.missing_domains),
        completed_modules=artifacts.completed_modules,
        selected_modules=artifacts.selected_modules,
        strategy_text=artifacts.strategy_text,
        blueprint_text=artifacts.blueprint_text,
        timeline_text=artifacts.timeline_text,
    )


def _pattern_matrix_to_audit_artifacts(case, artifacts) -> ReasoningAuditArtifacts:
    from niros.scenario_blueprint import build_scenario_blueprint

    blueprint = build_scenario_blueprint(artifacts.profile, intervention_strategy=artifacts.strategy)

    return ReasoningAuditArtifacts(
        case_path=Path(f"pattern_matrix/{case.case_id}.md"),
        detected_pattern_ids=artifacts.detected_pattern_ids,
        coverage_report=artifacts.coverage_report,
        fingerprint=artifacts.fingerprint,
        strategy=artifacts.strategy,
        blueprint=blueprint,
        report_text=artifacts.report_text,
        strategy_text=artifacts.strategy_text,
        blueprint_text=artifacts.blueprint_text,
        timeline_text=artifacts.timeline_text,
        completed_modules=artifacts.completed_modules,
        selected_modules=artifacts.selected_modules,
        expected_patterns=_flatten_pattern_groups(case.expected_pattern_groups),
        expected_weak_domains=[fragment for fragment in case.expected_weak_domain_fragments],
        expected_assessments=[fragment for fragment in case.expected_assessment_fragments],
        expected_strategy_focus=[],
        expected_scenario_themes=list(case.strategy_concept_tokens),
        expected_timeline_characteristics=[],
        is_complex=False,
    )


def _pseudo_human_to_audit_artifacts(case, artifacts) -> ReasoningAuditArtifacts:
    from niros.scenario_blueprint import build_scenario_blueprint

    profile = artifacts.profile
    strategy = artifacts.strategy
    blueprint = build_scenario_blueprint(profile, intervention_strategy=strategy)
    completed_modules = [
        str(item.get("module_id"))
        for item in artifacts.fingerprint.get("assessment_results", [])
        if item.get("module_id")
    ]

    return ReasoningAuditArtifacts(
        case_path=Path(f"pseudo_human/{case.case_id}.md"),
        detected_pattern_ids=artifacts.detected_pattern_ids,
        coverage_report=artifacts.coverage_report,
        fingerprint=artifacts.fingerprint,
        strategy=strategy,
        blueprint=blueprint,
        report_text=artifacts.report_text,
        strategy_text=artifacts.strategy_text,
        blueprint_text=artifacts.blueprint_text,
        timeline_text=artifacts.timeline_text,
        completed_modules=completed_modules,
        selected_modules=artifacts.selected_modules,
        expected_patterns=_flatten_pattern_groups(case.expected_pattern_groups),
        expected_weak_domains=[fragment for fragment in case.expected_weak_domain_fragments],
        expected_assessments=[fragment for fragment in case.expected_module_fragments],
        expected_strategy_focus=[],
        expected_scenario_themes=[],
        expected_timeline_characteristics=[],
        is_complex=False,
    )


def _multilingual_to_audit_artifacts(case, language: str, artifacts) -> ReasoningAuditArtifacts:
    from niros.scenario_blueprint import build_scenario_blueprint

    profile = artifacts.profile
    strategy = artifacts.strategy
    blueprint = build_scenario_blueprint(profile, intervention_strategy=strategy)
    expected_patterns = sorted({pattern for group in case.pattern_families for pattern in group})

    return ReasoningAuditArtifacts(
        case_path=Path(f"multilingual/{case.case_id}_{language}.md"),
        detected_pattern_ids=artifacts.detected_pattern_ids,
        coverage_report=artifacts.coverage_report,
        fingerprint=artifacts.fingerprint,
        strategy=strategy,
        blueprint=blueprint,
        report_text=artifacts.report_text,
        strategy_text=artifacts.strategy_text,
        blueprint_text=artifacts.blueprint_text,
        timeline_text=artifacts.timeline_text,
        completed_modules=artifacts.completed_modules,
        selected_modules=artifacts.selected_modules,
        expected_patterns=expected_patterns,
        expected_weak_domains=[fragment for fragment in case.primary_domain_fragments],
        expected_assessments=[fragment for fragment in case.assessment_fragments],
        expected_strategy_focus=[case.primary_strategy_focus],
        expected_scenario_themes=[],
        expected_timeline_characteristics=[],
        is_complex=False,
    )


def collect_pattern_matrix_records() -> dict[str, RegressionCaseRecord]:
    records: dict[str, RegressionCaseRecord] = {}
    for case in PATTERN_MATRIX_CASES:
        artifacts = run_pattern_matrix_pipeline(case)
        audit_artifacts = _pattern_matrix_to_audit_artifacts(case, artifacts)
        record = _audit_record_from_artifacts(
            suite="pattern_matrix",
            case_id=case.case_id,
            language="en",
            artifacts=audit_artifacts,
        )
        records[record.case_key] = record
    return records


def collect_pseudo_human_records() -> dict[str, RegressionCaseRecord]:
    records: dict[str, RegressionCaseRecord] = {}
    for case in PSEUDO_HUMAN_CASES:
        artifacts = run_pseudo_human_pipeline(case)
        audit_artifacts = _pseudo_human_to_audit_artifacts(case, artifacts)
        record = _audit_record_from_artifacts(
            suite="pseudo_human",
            case_id=case.case_id,
            language=case.language,
            artifacts=audit_artifacts,
        )
        records[record.case_key] = record
    return records


def collect_multilingual_records() -> dict[str, RegressionCaseRecord]:
    records: dict[str, RegressionCaseRecord] = {}
    for case in MULTILINGUAL_CASES:
        for language in LANGUAGES:
            artifacts = run_multilingual_pipeline(case, language)
            audit_artifacts = _multilingual_to_audit_artifacts(case, language, artifacts)
            record = _audit_record_from_artifacts(
                suite="multilingual",
                case_id=case.case_id,
                language=language,
                artifacts=audit_artifacts,
            )
            records[record.case_key] = record
    return records


def collect_complex_human_records() -> dict[str, RegressionCaseRecord]:
    records: dict[str, RegressionCaseRecord] = {}
    for case_path in sorted(COMPLEX_CASES_DIR.glob("c*.md")):
        artifacts = run_reasoning_audit_pipeline(case_path)
        record = _audit_record_from_artifacts(
            suite="complex_human",
            case_id=case_path.stem,
            language="en",
            artifacts=artifacts,
        )
        records[record.case_key] = record
    return records


def collect_all_regression_records() -> dict[str, RegressionCaseRecord]:
    records: dict[str, RegressionCaseRecord] = {}
    for collector in (
        collect_pattern_matrix_records,
        collect_pseudo_human_records,
        collect_multilingual_records,
        collect_complex_human_records,
    ):
        records.update(collector())
    return records
