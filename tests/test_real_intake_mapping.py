import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from demo_interview import run_pipeline
from niros.human_profile_summary import NO_EVIDENCE_PROFILE_TEXT, build_human_profile_summary
from niros.scenario_blueprint import build_scenario_blueprint
from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.facts import SemanticFact
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline


def _fact(category: str, attribute: str, value: str, evidence: str) -> SemanticFact:
    return SemanticFact(
        category=category,
        attribute=attribute,
        value=value,
        confidence=0.9,
        evidence=evidence,
    )


def _run_uk_pipeline(
    text: str,
    *,
    facts: list[SemanticFact] | None = None,
) -> tuple[set[str], SemanticInterpretationResult]:
    semantic = SemanticInterpretationResult(
        raw_text=text,
        canonical_statements=[],
        facts=facts or [],
        detected_language="uk",
        provider="mock",
    )
    pattern_tags, _, _ = run_pipeline(
        text,
        "session-real-intake",
        semantic_result=semantic,
    )
    return {tag.canonical_id for tag in pattern_tags}, semantic


def test_ya_boyusya_zhyty_detects_existential_and_safety_patterns():
    detected, semantic = _run_uk_pipeline("я боюся жити")

    assert semantic.detected_language == "uk"
    assert semantic.raw_text
    assert "existential_fear" in detected
    assert "safety_concern_signal" in detected


def test_nothing_helps_chronic_stress_detects_distress_patterns():
    text = "мені не допомагає нічого, я завжди у стресі"
    detected, _ = _run_uk_pipeline(
        text,
        facts=[
            _fact("emotion", "reported_distress", "elevated", "я завжди у стресі"),
            _fact("emotion", "chronic_stress", "present", "я завжди у стресі"),
            _fact("self", "perceived_helplessness", "present", "мені не допомагає нічого"),
        ],
    )

    assert "emotional_distress_signal" in detected
    assert "chronic_stress_signal" in detected


def test_nightmares_detect_sleep_patterns():
    detected, _ = _run_uk_pipeline("мені постійно сняться погані сни")

    assert detected.intersection({"nightmare_disturbance", "sleep_disruption"})


def test_depression_statement_detects_self_reported_concern():
    detected, _ = _run_uk_pipeline(
        "мені здається у мене депресія",
        facts=[
            _fact("self", "clinical_label_self_report", "depression", "мені здається у мене депресія"),
        ],
    )

    assert "self_reported_depression_concern" in detected
    assert "depressed_mood_signal" not in detected


def test_depression_statement_with_supporting_symptoms_detects_low_mood_cluster():
    detected, _ = _run_uk_pipeline(
        "я відчуваю депресію і майже не сплю",
        facts=[
            _fact("emotion", "reported_low_mood", "present", "я відчуваю депресію"),
            _fact("sleep", "insomnia", "present", "майже не сплю"),
        ],
    )

    assert detected.intersection({"low_mood_signal", "depressed_mood_signal", "insomnia_signal"})


def test_fibromyalgia_fatigue_detects_body_patterns():
    text = "у мене фіброміалгія і я постійно втомлений"
    detected, _ = _run_uk_pipeline(
        text,
        facts=[
            _fact("body", "pain_burden", "present", "у мене фіброміалгія"),
            _fact("body", "reported_fatigue", "present", "я постійно втомлений"),
        ],
    )

    assert "chronic_pain_burden" in detected
    assert "fatigue_burden" in detected


def test_stuttering_detects_speech_patterns():
    text = "я заїкаюсь і боюся говорити з людьми"
    detected, _ = _run_uk_pipeline(
        text,
        facts=[
            _fact("speech", "stuttering", "present", "я заїкаюсь"),
            _fact("emotion", "reported_fear", "elevated", "боюся говорити з людьми"),
        ],
    )

    assert detected.intersection({"speech_anxiety", "communication_avoidance"})


def test_bad_trip_detects_session_concern_patterns():
    detected, _ = _run_uk_pipeline(
        "я боюся поганого тріпу",
        facts=[_fact("session", "fear_of_bad_trip", "present", "я боюся поганого тріпу")],
    )

    assert detected.intersection({"fear_of_bad_trip", "psychedelic_anxiety"})


def test_semantic_distress_fact_maps_without_exact_phrase_match():
    detected, _ = _run_uk_pipeline(
        "мені не допомагає нічого, я завжди у стресі",
        facts=[_fact("emotion", "reported_distress", "elevated", "я завжди у стресі")],
    )

    assert "emotional_distress_signal" in detected


def test_integrated_unworthiness_intake_not_empty_after_q1():
    from niros.adaptive_assessment_selector import SELF_DOMAIN_SHORT, select_assessment_modules
    from niros.patterns import PatternTag
    from niros.models import SupportedLanguage

    q1_text = "я відчуваю себе непотрібним"
    detected, _ = _run_uk_pipeline(q1_text)

    assert detected
    assert detected.intersection({"unworthiness_signal", "self_worth_instability"})

    selection = select_assessment_modules(
        presenting_problem={"main_problem": q1_text, "duration": "близько року"},
        detected_patterns=sorted(detected),
    )
    assert SELF_DOMAIN_SHORT in selection.selected_modules

    pattern_tags = [
        PatternTag(
            id=f"tag-{canonical_id}",
            session_id="session-unworthiness-intake",
            evidence_id="session-unworthiness-intake:evidence:0",
            canonical_id=canonical_id,
            matched_text=q1_text,
            confidence=1.0,
            language=SupportedLanguage.UKRAINIAN,
        )
        for canonical_id in detected
    ]
    profile = build_human_profile_summary(pattern_tags)
    assert profile["primary_pattern"] is not None
    assert profile["profile_text"] != NO_EVIDENCE_PROFILE_TEXT


def test_integrated_three_turn_ukrainian_pipeline():
    turns = [
        (
            "я боюся жити",
            [],
        ),
        (
            "мені не допомагає нічого, я завжди у стресі",
            [
                _fact("emotion", "reported_distress", "elevated", "я завжди у стресі"),
                _fact("emotion", "chronic_stress", "present", "я завжди у стресі"),
                _fact("self", "perceived_helplessness", "present", "мені не допомагає нічого"),
            ],
        ),
        (
            "мені постійно сняться погані сни і я відчуваю депресію",
            [
                _fact("sleep", "nightmares", "present", "мені постійно сняться погані сни"),
                _fact("emotion", "reported_low_mood", "present", "я відчуваю депресію"),
                _fact("emotion", "reported_distress", "present", "я відчуваю депресію"),
            ],
        ),
    ]

    all_tags = []
    for text, facts in turns:
        detected, _ = _run_uk_pipeline(text, facts=facts)
        assert detected, f"Expected detected patterns for turn: {text}"
        pattern_tags, _, _ = run_pipeline(
            text,
            "session-integrated",
            semantic_result=SemanticInterpretationResult(
                raw_text=text,
                canonical_statements=[],
                facts=facts,
                detected_language="uk",
            ),
        )
        all_tags.extend(pattern_tags)

    profile = build_human_profile_summary(all_tags)
    assert profile["primary_pattern"] is not None
    assert profile["profile_text"] != NO_EVIDENCE_PROFILE_TEXT

    blueprint = build_scenario_blueprint(profile)
    assert len(blueprint.exploration_phases) >= 1

    timeline_text = render_session_timeline(simulate_session(profile))
    assert "EXPLORATION" in timeline_text
