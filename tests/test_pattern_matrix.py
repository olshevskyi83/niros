"""Pattern Matrix — synthetic pseudo-human regression suite for NIROS.

Each case targets one dominant Human Digital Fingerprint domain and verifies
end-to-end system behavior (patterns, coverage, assessments, profile, strategy,
scenario, timeline) without clinical validation claims.
"""

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
from niros.adaptive_assessment_selector import ALL_ASSESSMENT_MODULE_IDS, select_assessment_modules
from niros.assessment_runner import ASSESSMENT_ADAPTIVE, neutral_answers_for_module
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.human_profile_summary import build_human_profile_summary
from niros.intervention_strategy import build_intervention_strategy, render_intervention_strategy
from niros.scenario_blueprint import build_scenario_blueprint, render_scenario_blueprint
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline
from run_niros import build_coverage_from_session, build_fingerprint_from_session

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(is|e|ed|ing)?|disorder|patholog|clinical syndrome|bipolar|"
    r"ptsd|narcissistic personality|borderline personality)\b",
    re.IGNORECASE,
)

_BASE_INTAKE_TAIL = {
    "duration": "several months",
    "perceived_causes": "ongoing stress and inner struggle",
    "current_impact": "daily emotional burden and reduced functioning",
    "previous_attempts": "talking with friends and journaling",
    "desired_outcome": "understand myself better and feel more stable",
}


@dataclass(frozen=True)
class PatternMatrixCase:
    case_id: str
    domain_label: str
    intake: dict[str, str]
    narrative: str
    expected_pattern_groups: tuple[frozenset[str], ...]
    expected_primary_domain_fragments: tuple[str, ...]
    expected_weak_domain_fragments: tuple[str, ...]
    expected_assessment_fragments: tuple[str, ...]
    strategy_concept_tokens: tuple[str, ...] = ()


CASE_SELF = PatternMatrixCase(
    case_id="domain_self",
    domain_label="Self",
    intake={
        "presenting_problem": "I constantly criticize myself and feel not good enough.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I constantly feel that I am not good enough. deep down I feel I'm not enough. "
        "My inner voice is very critical. I cannot stop criticizing myself after I mess up."
    ),
    expected_pattern_groups=(
        frozenset({"harsh_self_criticism", "unworthiness_signal", "self_worth_instability"}),
    ),
    expected_primary_domain_fragments=("self_domain",),
    expected_weak_domain_fragments=("emotion_regulation", "cognitive", "meaning", "values"),
    expected_assessment_fragments=("self-domain",),
    strategy_concept_tokens=("self", "gentle", "exploratory"),
)

CASE_SHAME = PatternMatrixCase(
    case_id="domain_shame",
    domain_label="Shame",
    intake={
        "presenting_problem": "I feel ashamed of who I am and hide my true self.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I feel ashamed of who I am. People would reject me if they knew the real me. "
        "I often feel embarrassed even when no one is watching. When I make a mistake, "
        "I feel like a failure. I want to hide when I feel I have failed."
    ),
    expected_pattern_groups=(frozenset({"shame_sensitivity"}),),
    expected_primary_domain_fragments=("self_domain",),
    expected_weak_domain_fragments=("emotion_regulation", "cognitive", "meaning", "values"),
    expected_assessment_fragments=("self-domain",),
    strategy_concept_tokens=("self", "shame", "gentle", "exploratory"),
)

CASE_LOW_MOOD = PatternMatrixCase(
    case_id="domain_low_mood",
    domain_label="Low Mood",
    intake={
        "presenting_problem": "I no longer enjoy things and every day feels heavy.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I no longer enjoy things I used to love. Every day feels heavy. "
        "I feel down most of the time. nothing really brings me joy anymore."
    ),
    expected_pattern_groups=(
        frozenset({"anhedonia_signal", "depressed_mood_signal", "low_mood_signal"}),
    ),
    expected_primary_domain_fragments=("low_mood",),
    expected_weak_domain_fragments=("emotion_regulation", "self", "relationships", "cognitive"),
    expected_assessment_fragments=("low-mood",),
    strategy_concept_tokens=("ground", "gentle", "stabil", "mood"),
)

CASE_GRIEF = PatternMatrixCase(
    case_id="domain_grief_loss",
    domain_label="Grief / Loss",
    intake={
        "presenting_problem": "I lost someone important and never recovered emotionally.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I lost someone important and never recovered emotionally. "
        "I lost someone close to me and I am grieving. the grief feels overwhelming. "
        "I cannot get over the loss."
    ),
    expected_pattern_groups=(frozenset({"grief_signal", "bereavement_context", "loss_related_distress"}),),
    expected_primary_domain_fragments=("grief",),
    expected_weak_domain_fragments=("emotion_regulation", "relationships", "cognitive", "meaning"),
    expected_assessment_fragments=("grief-loss",),
    strategy_concept_tokens=("grief", "loss", "ground", "gentle", "meaning"),
)

CASE_MEANING = PatternMatrixCase(
    case_id="domain_meaning_purpose",
    domain_label="Meaning / Purpose",
    intake={
        "presenting_problem": "Everything feels meaningless and I do not know why I am living.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I have no idea why I am living anymore. life feels meaningless. "
        "nothing feels meaningful anymore."
    ),
    expected_pattern_groups=(frozenset({"loss_of_meaning", "hopelessness_signal", "meaning_seeking"}),),
    expected_primary_domain_fragments=("meaning",),
    expected_weak_domain_fragments=("values", "emotion_regulation", "cognitive", "relationships"),
    expected_assessment_fragments=("meaning-purpose", "grief-loss"),
    strategy_concept_tokens=("meaning", "purpose", "exploratory", "gentle"),
)

CASE_RELATIONSHIPS = PatternMatrixCase(
    case_id="domain_relationships",
    domain_label="Relationships",
    intake={
        "presenting_problem": "I want close relationships but never let people get close.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I want close relationships but I never let people get close. "
        "I keep one foot out of relationships. It is hard for me to fully trust people. "
        "I keep emotional distance so I cannot be hurt."
    ),
    expected_pattern_groups=(frozenset({"trust_difficulty", "fear_of_rejection", "attachment_anxiety"}),),
    expected_primary_domain_fragments=("relationships_domain",),
    expected_weak_domain_fragments=("emotion_regulation", "cognitive", "meaning", "values"),
    expected_assessment_fragments=("relationships-domain",),
    strategy_concept_tokens=("relationship", "trust", "connection", "exploratory"),
)

CASE_BELONGING = PatternMatrixCase(
    case_id="domain_belonging",
    domain_label="Belonging",
    intake={
        "presenting_problem": "I always feel like an outsider who does not belong.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I always feel like an outsider. I feel like I do not belong. "
        "I feel disconnected from others. nobody needs me."
    ),
    expected_pattern_groups=(
        frozenset({"social_disconnection_signal", "unworthiness_signal", "social_withdrawal"}),
    ),
    expected_primary_domain_fragments=("relationships_domain", "self_domain"),
    expected_weak_domain_fragments=("emotion_regulation", "meaning", "values", "cognitive"),
    expected_assessment_fragments=("relationships-domain", "self-domain"),
    strategy_concept_tokens=("belong", "connection", "relationship", "exploratory"),
)

CASE_EMOTION_REGULATION = PatternMatrixCase(
    case_id="domain_emotion_regulation",
    domain_label="Emotion Regulation",
    intake={
        "presenting_problem": "I suppress emotions until I suddenly explode.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I suppress every emotion until I suddenly explode. "
        "I push my feelings down so I can keep going. I go numb when too much is happening. "
        "I get overwhelmed by my feelings quickly."
    ),
    expected_pattern_groups=(frozenset({"emotional_suppression", "emotional_overwhelm"}),),
    expected_primary_domain_fragments=("emotion_regulation_domain",),
    expected_weak_domain_fragments=("cognitive", "meaning", "values", "flexibility"),
    expected_assessment_fragments=("emotion-regulation",),
    strategy_concept_tokens=("emotion", "regulation", "ground", "exploratory"),
)

CASE_COGNITIVE = PatternMatrixCase(
    case_id="domain_cognitive_patterns",
    domain_label="Cognitive Patterns",
    intake={
        "presenting_problem": "I constantly overthink and cannot stop my thoughts.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I constantly overthink everything and cannot stop. My mind gets stuck on the same worries. "
        "I cannot stop thinking about what might happen. I have to keep my thoughts under control."
    ),
    expected_pattern_groups=(frozenset({"rumination", "mental_overcontrol", "obsessive_thinking_loop"}),),
    expected_primary_domain_fragments=("cognitive_patterns_domain",),
    expected_weak_domain_fragments=("emotion_regulation", "meaning", "values", "flexibility"),
    expected_assessment_fragments=("cognitive-patterns",),
    strategy_concept_tokens=("cognitive", "ground", "exploratory", "ruminat"),
)

CASE_ANXIETY = PatternMatrixCase(
    case_id="domain_anxiety_control",
    domain_label="Anxiety / Control",
    intake={
        "presenting_problem": "I panic when things are not under control.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "If everything is not under control I immediately panic. "
        "I'm afraid of losing control. I need to stay in control. panic hits me out of nowhere."
    ),
    expected_pattern_groups=(
        frozenset({"fear_of_losing_control", "panic_reactivity", "control_resistance", "anxiety_reactivity"}),
    ),
    expected_primary_domain_fragments=("anxiety",),
    expected_weak_domain_fragments=("emotion_regulation", "cognitive", "relationships", "flexibility"),
    expected_assessment_fragments=("anxiety",),
    strategy_concept_tokens=("ground", "control", "anxiety", "exploratory"),
)

CASE_VALUES_IDENTITY = PatternMatrixCase(
    case_id="domain_values_identity",
    domain_label="Values & Identity",
    intake={
        "presenting_problem": "I do not know what matters and feel I live someone else's life.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I don't know what really matters to me anymore. I feel like I am living someone else's life. "
        "I don't know who I am anymore. I feel confused about my identity."
    ),
    expected_pattern_groups=(frozenset({"identity_confusion", "identity_uncertainty", "loss_of_meaning"}),),
    expected_primary_domain_fragments=("values_identity_domain",),
    expected_weak_domain_fragments=("meaning", "emotion_regulation", "cognitive", "relationships"),
    expected_assessment_fragments=("values-identity",),
    strategy_concept_tokens=("values", "identity", "meaning", "exploratory"),
)

CASE_EMOTIONAL_FLEXIBILITY = PatternMatrixCase(
    case_id="domain_emotional_flexibility",
    domain_label="Emotional Flexibility",
    intake={
        "presenting_problem": "I avoid difficult emotions or become completely overwhelmed.",
        **_BASE_INTAKE_TAIL,
    },
    narrative=(
        "I either avoid difficult emotions or become completely overwhelmed. "
        "I avoid situations that might upset me. I get overwhelmed by my feelings quickly. "
        "I resist letting go of control."
    ),
    expected_pattern_groups=(
        frozenset({"emotional_avoidance", "emotional_overwhelm", "control_resistance", "surrender_difficulty"}),
    ),
    expected_primary_domain_fragments=("emotion_regulation_domain", "emotional_flexibility_domain"),
    expected_weak_domain_fragments=("cognitive", "meaning", "values", "relationships"),
    expected_assessment_fragments=("emotional-flexibility", "emotion-regulation"),
    strategy_concept_tokens=("flexib", "emotion", "ground", "exploratory"),
)


PATTERN_MATRIX_CASES: tuple[PatternMatrixCase, ...] = (
    CASE_SELF,
    CASE_SHAME,
    CASE_LOW_MOOD,
    CASE_GRIEF,
    CASE_MEANING,
    CASE_RELATIONSHIPS,
    CASE_BELONGING,
    CASE_EMOTION_REGULATION,
    CASE_COGNITIVE,
    CASE_ANXIETY,
    CASE_VALUES_IDENTITY,
    CASE_EMOTIONAL_FLEXIBILITY,
)

PATTERN_MATRIX_DOMAIN_LABELS = frozenset(case.domain_label for case in PATTERN_MATRIX_CASES)


@dataclass
class PatternMatrixArtifacts:
    case: PatternMatrixCase
    profile: dict
    coverage_report: object
    fingerprint: dict
    strategy: object
    report_text: str
    strategy_text: str
    blueprint_text: str
    timeline_text: str
    selected_modules: list[str]
    completed_modules: list[str]
    detected_pattern_ids: set[str]
    semantic_fact_count: int


def _adaptive_answers() -> dict[str, dict[str, int]]:
    return {
        module_id: neutral_answers_for_module(module_id)
        for module_id in ALL_ASSESSMENT_MODULE_IDS
    }


def run_pattern_matrix_pipeline(case: PatternMatrixCase) -> PatternMatrixArtifacts:
    session = run_interview_session(
        intake_answers=case.intake,
        user_inputs=[case.narrative],
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
    report_text = render_human_profile_report(report)
    strategy_text = render_intervention_strategy(strategy)
    blueprint = build_scenario_blueprint(profile, intervention_strategy=strategy)
    blueprint_text = render_scenario_blueprint(blueprint)
    timeline_text = render_session_timeline(simulate_session(profile))

    completed_modules = [run.module_id for run in session.assessment_module_runs]
    selection = select_assessment_modules(
        presenting_problem=session.presenting_problem,
        detected_patterns=session.cumulative_pattern_tags,
        semantic_facts=semantic_facts,
        completed_assessments={
            run.module_id: list(run.results) for run in session.assessment_module_runs
        },
    )

    return PatternMatrixArtifacts(
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
        completed_modules=completed_modules,
        detected_pattern_ids={tag.canonical_id for tag in session.cumulative_pattern_tags},
        semantic_fact_count=len(semantic_facts),
    )


def _assert_no_diagnosis_language(*texts: str) -> None:
    combined = "\n".join(texts).lower()
    sanitized = re.sub(
        r"(descriptive, not diagnostic|non-diagnostic|without niros assigning a diagnosis|"
        r"without clinical diagnosis or naming a disorder|not a diagnosis|no diagnosis|"
        r"naming a disorder)",
        "",
        combined,
    )
    assert DIAGNOSIS_PATTERN.search(sanitized) is None
    assert "disorder" not in sanitized
    assert "clinical syndrome" not in sanitized


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


def _domain_is_evidenced(coverage_report, fragment: str) -> bool:
    for domain_id, domain in coverage_report.domains.items():
        if fragment in domain_id and domain.level in {"partial", "good", "complete"}:
            return True
    return False


def _modules_include(module_ids: list[str], fragment: str) -> bool:
    return any(fragment in module_id for module_id in module_ids)


def _assessment_covers_domain(completed_modules: list[str], selected_modules: list[str], fragment: str) -> bool:
    return _modules_include(completed_modules, fragment) or _modules_include(selected_modules, fragment)


def _assert_core_pipeline(artifacts: PatternMatrixArtifacts) -> None:
    assert artifacts.detected_pattern_ids, f"{artifacts.case.case_id} produced no pattern signals"
    assert artifacts.profile
    assert artifacts.coverage_report is not None
    assert artifacts.coverage_report.missing_domains
    assert artifacts.fingerprint["summary_text"]
    assert artifacts.strategy is not None
    assert artifacts.completed_modules
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


def test_pattern_matrix_covers_twelve_dominant_domains():
    assert len(PATTERN_MATRIX_CASES) == 12
    assert PATTERN_MATRIX_DOMAIN_LABELS == {
        "Self",
        "Shame",
        "Low Mood",
        "Grief / Loss",
        "Meaning / Purpose",
        "Relationships",
        "Belonging",
        "Emotion Regulation",
        "Cognitive Patterns",
        "Anxiety / Control",
        "Values & Identity",
        "Emotional Flexibility",
    }


@pytest.mark.parametrize("case", PATTERN_MATRIX_CASES, ids=[case.case_id for case in PATTERN_MATRIX_CASES])
def test_pattern_matrix_case_runs_full_pipeline(case: PatternMatrixCase):
    artifacts = run_pattern_matrix_pipeline(case)
    _assert_core_pipeline(artifacts)


@pytest.mark.parametrize("case", PATTERN_MATRIX_CASES, ids=[case.case_id for case in PATTERN_MATRIX_CASES])
def test_pattern_matrix_case_detects_expected_patterns(case: PatternMatrixCase):
    artifacts = run_pattern_matrix_pipeline(case)
    assert _patterns_match_groups(artifacts.detected_pattern_ids, case.expected_pattern_groups)


@pytest.mark.parametrize("case", PATTERN_MATRIX_CASES, ids=[case.case_id for case in PATTERN_MATRIX_CASES])
def test_pattern_matrix_case_evidences_primary_domain(case: PatternMatrixCase):
    artifacts = run_pattern_matrix_pipeline(case)
    assert any(
        _domain_is_evidenced(artifacts.coverage_report, fragment)
        for fragment in case.expected_primary_domain_fragments
    )


@pytest.mark.parametrize("case", PATTERN_MATRIX_CASES, ids=[case.case_id for case in PATTERN_MATRIX_CASES])
def test_pattern_matrix_case_detects_coverage_gaps(case: PatternMatrixCase):
    artifacts = run_pattern_matrix_pipeline(case)
    assert any(
        _domain_is_weak(artifacts.coverage_report, fragment)
        for fragment in case.expected_weak_domain_fragments
    )


@pytest.mark.parametrize("case", PATTERN_MATRIX_CASES, ids=[case.case_id for case in PATTERN_MATRIX_CASES])
def test_pattern_matrix_case_selects_domain_assessment(case: PatternMatrixCase):
    artifacts = run_pattern_matrix_pipeline(case)
    assert any(
        _assessment_covers_domain(
            artifacts.completed_modules,
            artifacts.selected_modules,
            fragment,
        )
        for fragment in case.expected_assessment_fragments
    )


@pytest.mark.parametrize("case", PATTERN_MATRIX_CASES, ids=[case.case_id for case in PATTERN_MATRIX_CASES])
def test_pattern_matrix_case_is_deterministic(case: PatternMatrixCase):
    first = run_pattern_matrix_pipeline(case)
    second = run_pattern_matrix_pipeline(case)

    assert first.detected_pattern_ids == second.detected_pattern_ids
    assert first.completed_modules == second.completed_modules
    assert first.selected_modules == second.selected_modules
    assert first.report_text == second.report_text
    assert first.strategy_text == second.strategy_text
    assert first.blueprint_text == second.blueprint_text
    assert first.timeline_text == second.timeline_text


@pytest.mark.parametrize("case", PATTERN_MATRIX_CASES, ids=[case.case_id for case in PATTERN_MATRIX_CASES])
def test_pattern_matrix_case_strategy_reflects_domain(case: PatternMatrixCase):
    if not case.strategy_concept_tokens:
        pytest.skip("no strategy concept tokens configured")

    artifacts = run_pattern_matrix_pipeline(case)
    combined = f"{artifacts.strategy_text}\n{artifacts.blueprint_text}".lower()
    assert any(token in combined for token in case.strategy_concept_tokens)


def test_pattern_matrix_self_case_prioritizes_self_worth_signals():
    artifacts = run_pattern_matrix_pipeline(CASE_SELF)
    assert artifacts.detected_pattern_ids & {"harsh_self_criticism", "unworthiness_signal"}
    assert _assessment_covers_domain(
        artifacts.completed_modules,
        artifacts.selected_modules,
        "self-domain",
    )


def test_pattern_matrix_grief_case_links_loss_to_meaning_gaps():
    artifacts = run_pattern_matrix_pipeline(CASE_GRIEF)
    assert "grief_signal" in artifacts.detected_pattern_ids
    assert _domain_is_evidenced(artifacts.coverage_report, "grief")
    assert _assessment_covers_domain(
        artifacts.completed_modules,
        artifacts.selected_modules,
        "grief-loss",
    )
