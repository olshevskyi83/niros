"""Deterministic reasoning-quality audit for synthetic human profiles."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from demo_interview import run_interview_session
from niros.adaptive_assessment_selector import ALL_ASSESSMENT_MODULE_IDS
from niros.assessment_runner import ASSESSMENT_ADAPTIVE, neutral_answers_for_module
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.human_profile_summary import build_human_profile_summary
from niros.intervention_strategy import build_intervention_strategy, render_intervention_strategy
from niros.reasoning_quality_audit import (
    ReasoningAuditArtifacts,
    ReasoningQualityReport,
    audit_reasoning_quality,
    build_intake_for_case,
    discover_synthetic_profile_paths,
    load_bullet_section,
    load_scenario_text,
)
from niros.scenario_blueprint import build_scenario_blueprint, render_scenario_blueprint
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline
from run_niros import build_coverage_from_session, build_fingerprint_from_session

TEST_CASES_DIR = ROOT / "knowledge" / "test_cases"
PROFILE_PATHS = discover_synthetic_profile_paths(TEST_CASES_DIR)

# Minimum scores for the permanent benchmark (deterministic audit thresholds).
MIN_OVERALL_SCORE = 0.55
MIN_COMPLEX_OVERALL_SCORE = 0.50
MIN_COVERAGE_SCORE = 0.45
MIN_CONSISTENCY_SCORE = 0.70
MIN_STRATEGY_COHERENCE_SCORE = 0.45
MIN_SCENARIO_COHERENCE_SCORE = 0.45
MIN_TIMELINE_COHERENCE_SCORE = 0.50


def _adaptive_answers() -> dict[str, dict[str, int]]:
    return {
        module_id: neutral_answers_for_module(module_id)
        for module_id in ALL_ASSESSMENT_MODULE_IDS
    }


def run_reasoning_audit_pipeline(case_path: Path) -> ReasoningAuditArtifacts:
    scenario = load_scenario_text(case_path)
    session = run_interview_session(
        intake_answers=build_intake_for_case(case_path, scenario),
        user_inputs=[scenario],
        turns=1,
        provider="mock",
        language="en",
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_adaptive_answers(),
        print_output=False,
    )

    profile = build_human_profile_summary(session.cumulative_pattern_tags)
    coverage_report = build_coverage_from_session(session)
    fingerprint = build_fingerprint_from_session(session)
    semantic_facts = []
    if session.intake_result is not None:
        semantic_facts = session.intake_result.evidence_store.facts()

    strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage_report,
    )
    report = build_human_profile_report_from_tags(
        session.cumulative_pattern_tags,
        presenting_problem=session.presenting_problem,
        assessment_module_runs=session.assessment_module_runs,
        semantic_facts=semantic_facts,
    )
    blueprint = build_scenario_blueprint(profile, intervention_strategy=strategy)

    return ReasoningAuditArtifacts(
        case_path=case_path,
        detected_pattern_ids={tag.canonical_id for tag in session.cumulative_pattern_tags},
        coverage_report=coverage_report,
        fingerprint=fingerprint,
        strategy=strategy,
        blueprint=blueprint,
        report_text=render_human_profile_report(report),
        strategy_text=render_intervention_strategy(strategy),
        blueprint_text=render_scenario_blueprint(blueprint),
        timeline_text=render_session_timeline(simulate_session(profile)),
        completed_modules=[run.module_id for run in session.assessment_module_runs],
        selected_modules=list(coverage_report.selected_modules),
        expected_patterns=load_bullet_section(case_path, "Expected Patterns"),
        expected_weak_domains=load_bullet_section(case_path, "Expected Weak Domains"),
        expected_assessments=load_bullet_section(case_path, "Expected Assessments"),
        expected_strategy_focus=load_bullet_section(case_path, "Expected Strategy Focus"),
        expected_scenario_themes=load_bullet_section(case_path, "Expected Scenario Themes"),
        expected_timeline_characteristics=load_bullet_section(
            case_path, "Expected Timeline Characteristics"
        ),
        is_complex=case_path.parent.name == "complex",
    )


@pytest.fixture(scope="module")
def reasoning_quality_reports() -> dict[str, ReasoningQualityReport]:
    reports: dict[str, ReasoningQualityReport] = {}
    for case_path in PROFILE_PATHS:
        artifacts = run_reasoning_audit_pipeline(case_path)
        reports[case_path.stem] = audit_reasoning_quality(artifacts)
    return reports


def test_reasoning_quality_covers_all_synthetic_profiles():
    assert len(PROFILE_PATHS) >= 107


@pytest.mark.parametrize("case_path", PROFILE_PATHS, ids=[path.stem for path in PROFILE_PATHS])
def test_reasoning_quality_scores_are_bounded(case_path: Path, reasoning_quality_reports):
    report = reasoning_quality_reports[case_path.stem]
    scores = report.scores

    assert 0.0 <= scores.coverage_score <= 1.0
    assert 0.0 <= scores.consistency_score <= 1.0
    assert 0.0 <= scores.strategy_coherence_score <= 1.0
    assert 0.0 <= scores.scenario_coherence_score <= 1.0
    assert 0.0 <= scores.timeline_coherence_score <= 1.0
    assert 0.0 <= scores.overall_human_understanding_score <= 1.0
    assert report.findings


@pytest.mark.parametrize(
    "case_path",
    [PROFILE_PATHS[0], PROFILE_PATHS[77], PROFILE_PATHS[-1]],
    ids=[PROFILE_PATHS[0].stem, PROFILE_PATHS[77].stem, PROFILE_PATHS[-1].stem],
)
def test_reasoning_quality_pipeline_is_deterministic(case_path: Path):
    first = audit_reasoning_quality(run_reasoning_audit_pipeline(case_path))
    second = audit_reasoning_quality(run_reasoning_audit_pipeline(case_path))

    assert first.scores == second.scores
    assert first.missed_patterns == second.missed_patterns
    assert first.over_assumed_patterns == second.over_assumed_patterns


def test_reasoning_quality_audit_is_purely_deterministic():
    artifacts = run_reasoning_audit_pipeline(PROFILE_PATHS[0])
    first = audit_reasoning_quality(artifacts)
    second = audit_reasoning_quality(artifacts)

    assert first == second


@pytest.mark.parametrize("case_path", PROFILE_PATHS, ids=[path.stem for path in PROFILE_PATHS])
def test_reasoning_quality_meets_minimum_thresholds(case_path: Path, reasoning_quality_reports):
    report = reasoning_quality_reports[case_path.stem]
    scores = report.scores

    assert scores.coverage_score >= MIN_COVERAGE_SCORE, (
        f"{case_path.stem} coverage={scores.coverage_score:.3f} "
        f"missed={report.missed_patterns}"
    )
    assert scores.consistency_score >= MIN_CONSISTENCY_SCORE, report.findings
    assert scores.strategy_coherence_score >= MIN_STRATEGY_COHERENCE_SCORE, report.findings
    assert scores.scenario_coherence_score >= MIN_SCENARIO_COHERENCE_SCORE, report.findings
    assert scores.timeline_coherence_score >= MIN_TIMELINE_COHERENCE_SCORE, report.findings

    minimum_overall = MIN_COMPLEX_OVERALL_SCORE if report.is_complex else MIN_OVERALL_SCORE
    assert scores.overall_human_understanding_score >= minimum_overall, (
        f"{case_path.stem} overall={scores.overall_human_understanding_score:.3f} "
        f"findings={report.findings}"
    )


def test_reasoning_quality_benchmark_summary(reasoning_quality_reports, capsys):
    rows: list[tuple[str, ReasoningQualityReport]] = sorted(
        reasoning_quality_reports.items(),
        key=lambda item: item[1].scores.overall_human_understanding_score,
    )

    print("\n=== NIROS Reasoning Quality Benchmark ===")
    print(
        "case_id | overall | coverage | consistency | strategy | scenario | timeline | missed | over-assumed"
    )
    for case_id, report in rows:
        scores = report.scores
        print(
            f"{case_id} | {scores.overall_human_understanding_score:.3f} | "
            f"{scores.coverage_score:.3f} | {scores.consistency_score:.3f} | "
            f"{scores.strategy_coherence_score:.3f} | {scores.scenario_coherence_score:.3f} | "
            f"{scores.timeline_coherence_score:.3f} | "
            f"{len(report.missed_patterns)} | {len(report.over_assumed_patterns)}"
        )

    complex_reports = [report for report in reasoning_quality_reports.values() if report.is_complex]
    simple_reports = [report for report in reasoning_quality_reports.values() if not report.is_complex]

    def _mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    print(
        f"\nSimple profiles ({len(simple_reports)}): "
        f"mean overall={_mean([r.scores.overall_human_understanding_score for r in simple_reports]):.3f}"
    )
    print(
        f"Complex profiles ({len(complex_reports)}): "
        f"mean overall={_mean([r.scores.overall_human_understanding_score for r in complex_reports]):.3f}"
    )

    captured = capsys.readouterr()
    assert "Reasoning Quality Benchmark" in captured.out
