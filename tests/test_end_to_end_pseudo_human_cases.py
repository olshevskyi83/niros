from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from demo_interview import run_interview_session
from niros.adaptive_assessment_selector import select_assessment_modules
from niros.assessment_runner import ASSESSMENT_ADAPTIVE, neutral_answers_for_module
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.human_profile_summary import build_human_profile_summary
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    STRATEGY_CONFIDENCE_MEDIUM,
    build_intervention_strategy,
    is_high_grounding,
    render_intervention_strategy,
)
from niros.scenario_blueprint import build_scenario_blueprint, render_scenario_blueprint
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline
from run_niros import build_coverage_from_session, build_fingerprint_from_session

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(is|e|ed|ing)?|disorder|patholog|clinical syndrome|bipolar|"
    r"ptsd|narcissistic personality|borderline personality)\b",
    re.IGNORECASE,
)

ADAPTIVE_MODULE_IDS = (
    "big-five-short",
    "grief-loss-short",
    "low-mood-short",
    "emotion-regulation-domain-short",
    "self-domain-short",
    "relationships-domain-short",
    "values-identity-domain-short",
    "meaning-purpose-short",
    "cognitive-patterns-domain-short",
    "anxiety-short",
    "emotional-flexibility-domain-short",
)


@dataclass(frozen=True)
class PseudoHumanCase:
    case_id: str
    language: str
    intake: dict[str, str]
    narrative: str
    expected_pattern_groups: tuple[frozenset[str], ...]
    expected_weak_domain_fragments: tuple[str, ...]
    expected_module_fragments: tuple[str, ...]


CASE_LOW_MOOD_LOSS = PseudoHumanCase(
    case_id="low_mood_loss_withdrawal",
    language="en",
    intake={
        "presenting_problem": "I lost someone close to me last year and feel empty and disconnected.",
        "duration": "about a year",
        "perceived_causes": "grief after the loss",
        "current_impact": "tired, disconnected from people, low mood most days",
        "previous_attempts": "talking with friends",
        "desired_outcome": "feel more like myself and find meaning again",
    },
    narrative=(
        "I lost someone close to me last year. Since then I feel empty, tired, "
        "disconnected from people, and I do not really know what I want anymore. "
        "I am grieving and socially withdrawn."
    ),
    expected_pattern_groups=(
        frozenset(
            {
                "grief_signal",
                "bereavement_context",
                "loss_related_distress",
                "social_withdrawal",
                "social_disconnection_signal",
                "loss_of_meaning",
            }
        ),
    ),
    expected_weak_domain_fragments=("emotion_regulation", "relationships", "meaning", "values"),
    expected_module_fragments=("emotion-regulation",),
)


CASE_SHAME_SELF_CRITICISM = PseudoHumanCase(
    case_id="shame_self_criticism",
    language="uk",
    intake={
        "presenting_problem": "Я постійно себе критикую і мені соромно за себе.",
        "duration": "кілька років",
        "perceived_causes": "внутрішня критика і сором",
        "current_impact": "не відчуваю себе гідним хороших речей",
        "previous_attempts": "намагався бути кращим",
        "desired_outcome": "більше прийняття себе",
    },
    narrative=(
        "Я постійно себе критикую. Навіть коли все нормально, я відчуваю, що зі мною "
        "щось не так. не відчуваю себе гідним хороших речей. My inner voice is very "
        "critical. I often feel embarrassed even when no one is watching."
    ),
    expected_pattern_groups=(
        frozenset(
            {
                "shame_sensitivity",
                "harsh_self_criticism",
                "unworthiness_signal",
            }
        ),
    ),
    expected_weak_domain_fragments=("meaning", "values", "cognitive", "emotion_regulation"),
    expected_module_fragments=("emotion-regulation", "cognitive"),
)


CASE_ANXIETY_RUMINATION = PseudoHumanCase(
    case_id="anxiety_control_rumination",
    language="en",
    intake={
        "presenting_problem": (
            "Ich denke ständig über alles nach und habe Angst Fehler zu machen."
        ),
        "duration": "seit Monaten",
        "perceived_causes": "Stress und Kontrollbedürfnis",
        "current_impact": "Grübeln, innere Anspannung, schwer abschalten",
        "previous_attempts": "Meditation",
        "desired_outcome": "mehr Ruhe und Flexibilität",
    },
    narrative=(
        "My mind gets stuck on the same worries. I cannot stop thinking about what "
        "might happen. I have to keep my thoughts under control and I try to control "
        "everything."
    ),
    expected_pattern_groups=(
        frozenset({"rumination", "mental_overcontrol", "anxiety_reactivity", "control_resistance"}),
    ),
    expected_weak_domain_fragments=("emotion_regulation", "cognitive", "meaning", "values"),
    expected_module_fragments=("cognitive", "emotion-regulation"),
)


CASE_RELATIONSHIP_BELONGING = PseudoHumanCase(
    case_id="relationship_belonging",
    language="es",
    intake={
        "presenting_problem": "Siento que no pertenezco a ningún lugar.",
        "duration": "varios meses",
        "perceived_causes": "experiencias de rechazo y desconfianza",
        "current_impact": "me cuesta confiar y me alejo cuando alguien se acerca",
        "previous_attempts": "hablar con amigos",
        "desired_outcome": "sentir conexión y pertenencia",
    },
    narrative=(
        "Siento que no pertenezco a ningún lugar. Me cuesta confiar en la gente y "
        "cuando alguien se acerca, me cierro o me alejo."
    ),
    expected_pattern_groups=(
        frozenset(
            {
                "social_disconnection_signal",
                "trust_difficulty",
                "social_withdrawal",
                "attachment_anxiety",
            }
        ),
    ),
    expected_weak_domain_fragments=("meaning", "values", "emotion_regulation", "cognitive"),
    expected_module_fragments=("emotion-regulation", "cognitive"),
)


CASE_VALUES_IDENTITY = PseudoHumanCase(
    case_id="values_identity_confusion",
    language="en",
    intake={
        "presenting_problem": "I feel like I am living someone else's life.",
        "duration": "a few years",
        "perceived_causes": "achievement without personal alignment",
        "current_impact": "identity confusion and unclear values",
        "previous_attempts": "career changes",
        "desired_outcome": "clarity about what matters and who I am",
    },
    narrative=(
        "I have achieved some things, but I feel like I am living someone else's life. "
        "I do not know what actually matters to me or who I really am. "
        "I do not know who I am anymore. I feel confused about my identity."
    ),
    expected_pattern_groups=(
        frozenset({"identity_confusion", "identity_uncertainty", "loss_of_meaning", "meaning_seeking"}),
    ),
    expected_weak_domain_fragments=("values", "meaning", "emotion_regulation", "cognitive"),
    expected_module_fragments=("values-identity", "meaning-purpose", "cognitive", "emotion-regulation"),
)


ALL_CASES = (
    CASE_LOW_MOOD_LOSS,
    CASE_SHAME_SELF_CRITICISM,
    CASE_ANXIETY_RUMINATION,
    CASE_RELATIONSHIP_BELONGING,
    CASE_VALUES_IDENTITY,
)


@dataclass
class PipelineArtifacts:
    case: PseudoHumanCase
    profile: dict
    coverage_report: object
    fingerprint: dict
    strategy: object
    report_text: str
    strategy_text: str
    blueprint_text: str
    timeline_text: str
    selected_modules: list[str]
    detected_pattern_ids: set[str]


def _adaptive_answers() -> dict[str, dict[str, int]]:
    return {module_id: neutral_answers_for_module(module_id) for module_id in ADAPTIVE_MODULE_IDS}


def run_pseudo_human_pipeline(case: PseudoHumanCase) -> PipelineArtifacts:
    session = run_interview_session(
        intake_answers=case.intake,
        user_inputs=[case.narrative],
        turns=1,
        provider="mock",
        language=case.language,
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_adaptive_answers(),
        print_output=False,
    )

    profile = build_human_profile_summary(session.cumulative_pattern_tags)
    coverage_report = build_coverage_from_session(session)
    fingerprint = build_fingerprint_from_session(session)
    semantic_facts = None
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
    report_text = render_human_profile_report(report)
    strategy_text = render_intervention_strategy(strategy)
    blueprint = build_scenario_blueprint(profile, intervention_strategy=strategy)
    blueprint_text = render_scenario_blueprint(blueprint)
    timeline_text = render_session_timeline(simulate_session(profile))

    selection = select_assessment_modules(
        presenting_problem=session.presenting_problem,
        detected_patterns=session.cumulative_pattern_tags,
        semantic_facts=semantic_facts,
        completed_assessments={
            run.module_id: list(run.results) for run in session.assessment_module_runs
        },
    )

    return PipelineArtifacts(
        case=case,
        profile=profile,
        coverage_report=coverage_report,
        fingerprint=fingerprint,
        strategy=strategy,
        report_text=report_text,
        strategy_text=strategy_text,
        blueprint_text=blueprint_text,
        timeline_text=timeline_text,
        selected_modules=list(selection.selected_modules),
        detected_pattern_ids={tag.canonical_id for tag in session.cumulative_pattern_tags},
    )


def _assert_no_diagnosis_language(*texts: str) -> None:
    combined = "\n".join(texts).lower()
    assert DIAGNOSIS_PATTERN.search(combined) is None
    assert "disorder" not in combined
    assert "clinical syndrome" not in combined


def _assert_core_pipeline(artifacts: PipelineArtifacts) -> None:
    assert artifacts.profile
    assert artifacts.coverage_report is not None
    assert artifacts.coverage_report.missing_domains
    assert artifacts.fingerprint["summary_text"]
    assert artifacts.strategy is not None
    assert artifacts.selected_modules
    assert len(artifacts.selected_modules) <= 4

    assert "Human Digital Fingerprint Coverage" in artifacts.report_text
    assert "=== NIROS Intervention Strategy ===" in artifacts.strategy_text
    assert "Scenario Blueprint" in artifacts.blueprint_text
    assert artifacts.timeline_text.strip()
    assert "Opening" in artifacts.timeline_text or "opening" in artifacts.timeline_text.lower()

    _assert_no_diagnosis_language(
        artifacts.report_text,
        artifacts.strategy_text,
        artifacts.blueprint_text,
        artifacts.timeline_text,
    )


def _patterns_match_groups(
    detected: set[str],
    groups: tuple[frozenset[str], ...],
) -> bool:
    return all(detected & group for group in groups)


def _domain_is_weak(coverage_report, fragment: str) -> bool:
    missing = set(coverage_report.missing_domains)
    if any(fragment in domain_id for domain_id in missing):
        return True
    for domain_id, domain in coverage_report.domains.items():
        if fragment in domain_id and domain.level in {"unknown", "partial"}:
            return True
    return False


def _modules_include(selected_modules: list[str], fragment: str) -> bool:
    return any(fragment in module_id for module_id in selected_modules)


@pytest.mark.parametrize("case", ALL_CASES, ids=[case.case_id for case in ALL_CASES])
def test_pseudo_human_case_runs_full_pipeline(case: PseudoHumanCase):
    artifacts = run_pseudo_human_pipeline(case)
    _assert_core_pipeline(artifacts)


@pytest.mark.parametrize("case", ALL_CASES, ids=[case.case_id for case in ALL_CASES])
def test_pseudo_human_case_detects_expected_pattern_signals(case: PseudoHumanCase):
    artifacts = run_pseudo_human_pipeline(case)
    assert _patterns_match_groups(artifacts.detected_pattern_ids, case.expected_pattern_groups)


@pytest.mark.parametrize("case", ALL_CASES, ids=[case.case_id for case in ALL_CASES])
def test_pseudo_human_case_detects_weak_fingerprint_domains(case: PseudoHumanCase):
    artifacts = run_pseudo_human_pipeline(case)
    assert any(
        _domain_is_weak(artifacts.coverage_report, fragment)
        for fragment in case.expected_weak_domain_fragments
    )


@pytest.mark.parametrize("case", ALL_CASES, ids=[case.case_id for case in ALL_CASES])
def test_pseudo_human_case_selects_coverage_gap_modules(case: PseudoHumanCase):
    artifacts = run_pseudo_human_pipeline(case)
    assert any(
        _modules_include(artifacts.selected_modules, fragment)
        for fragment in case.expected_module_fragments
    )


@pytest.mark.parametrize("case", ALL_CASES, ids=[case.case_id for case in ALL_CASES])
def test_pseudo_human_case_is_deterministic(case: PseudoHumanCase):
    first = run_pseudo_human_pipeline(case)
    second = run_pseudo_human_pipeline(case)

    assert first.detected_pattern_ids == second.detected_pattern_ids
    assert first.selected_modules == second.selected_modules
    assert first.report_text == second.report_text
    assert first.strategy_text == second.strategy_text
    assert first.blueprint_text == second.blueprint_text
    assert first.timeline_text == second.timeline_text


def test_case_low_mood_loss_strategy_is_gentle_and_stabilizing():
    artifacts = run_pseudo_human_pipeline(CASE_LOW_MOOD_LOSS)
    strategy = artifacts.strategy

    assert is_high_grounding(strategy.grounding_priority) or strategy.pacing == "slow"
    combined = f"{artifacts.strategy_text}\n{artifacts.blueprint_text}".lower()
    assert any(
        token in combined
        for token in ("ground", "meaning", "grief", "stabil", "integration")
    )


def test_case_shame_self_criticism_uses_gentle_self_framing():
    artifacts = run_pseudo_human_pipeline(CASE_SHAME_SELF_CRITICISM)
    strategy = artifacts.strategy

    self_focus = next(
        item for item in strategy.focus_confidence if item.focus_area == "self-worth / self-criticism"
    )
    assert self_focus.confidence in {STRATEGY_CONFIDENCE_LOW, STRATEGY_CONFIDENCE_MEDIUM}
    combined = f"{artifacts.strategy_text}\n{artifacts.blueprint_text}".lower()
    assert any(
        token in combined
        for token in ("self", "gentle", "exploratory", "clarification", "self-worth")
    )


def test_case_anxiety_rumination_strategy_emphasizes_grounding_and_flexibility():
    artifacts = run_pseudo_human_pipeline(CASE_ANXIETY_RUMINATION)
    strategy = artifacts.strategy
    combined = f"{artifacts.strategy_text}\n{artifacts.blueprint_text}".lower()

    assert _modules_include(artifacts.selected_modules, "cognitive")
    assert any(token in combined for token in ("ground", "cognitive", "emotion regulation", "exploratory"))


def test_case_relationship_belonging_keeps_non_forceful_relational_framing():
    artifacts = run_pseudo_human_pipeline(CASE_RELATIONSHIP_BELONGING)
    combined = f"{artifacts.strategy_text}\n{artifacts.blueprint_text}".lower()

    assert _patterns_match_groups(
        artifacts.detected_pattern_ids,
        CASE_RELATIONSHIP_BELONGING.expected_pattern_groups,
    )
    assert any(
        token in combined
        for token in ("relationship", "connection", "trust", "belong", "exploratory", "gentle")
    )


def test_case_values_identity_focuses_on_values_clarification():
    artifacts = run_pseudo_human_pipeline(CASE_VALUES_IDENTITY)
    strategy = artifacts.strategy
    combined = f"{artifacts.strategy_text}\n{artifacts.blueprint_text}".lower()

    assert _modules_include(artifacts.selected_modules, "values-identity") or _modules_include(
        artifacts.selected_modules,
        "meaning-purpose",
    )
    meaning_focus = next(
        item for item in strategy.focus_confidence if item.focus_area == "meaning / purpose"
    )
    assert meaning_focus.confidence in {
        STRATEGY_CONFIDENCE_LOW,
        STRATEGY_CONFIDENCE_MEDIUM,
        STRATEGY_CONFIDENCE_HIGH,
    }
    assert any(token in combined for token in ("meaning", "values", "identity", "exploratory", "gentle"))


@pytest.mark.parametrize(
    ("case", "language_marker"),
    [
        (CASE_LOW_MOOD_LOSS, "lost someone"),
        (CASE_SHAME_SELF_CRITICISM, "критикую"),
        (CASE_ANXIETY_RUMINATION, "ständig"),
        (CASE_RELATIONSHIP_BELONGING, "pertenezco"),
        (CASE_VALUES_IDENTITY, "someone else's life"),
    ],
    ids=[case.case_id for case in ALL_CASES],
)
def test_multilingual_inputs_do_not_break_pipeline(case: PseudoHumanCase, language_marker: str):
    artifacts = run_pseudo_human_pipeline(case)
    _assert_core_pipeline(artifacts)
    assert language_marker.lower() in case.narrative.lower() or language_marker.lower() in str(case.intake).lower()
