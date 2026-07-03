from pathlib import Path

from niros.evidence import statement_to_evidence, statements_to_evidence
from niros.hypotheses import generate_hypotheses
from niros.interview_engine import BlueprintPhase, InterviewDecisionEngine
from niros.models import InterviewPhase, SupportedLanguage
from niros.patterns import PatternTagger, pattern_tag_evidence_items
from niros.semantic_interpreter.fact_vocabulary import (
    BODY,
    BODY_TRUST,
    CHANGE_DESIRE,
    MEANING,
    MEANING_SENSE,
    PAIN_BURDEN,
    REPORTED_DISTRESS,
    REPORTED_FEAR,
    SAFETY,
    SAFETY_FEELING,
    SESSION,
    SESSION_OPENNESS,
    SPEECH,
    SPEECH_COMFORT,
    TRAUMA,
    TRAUMA_STRESS,
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)
from niros.semantic_interpreter.facts import SemanticFact
from niros.state_machine import advance, initial_state
from niros.statements import Statement, split_transcript_to_statements
from niros.transcript import Transcript

TEST_CASES_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "test_cases"

INTAKE_PATTERN_IDS = frozenset(
    {
        "existential_fear",
        "generalized_fear",
        "emotional_distress_signal",
        "safety_concern_signal",
        "panic_reactivity",
        "fear_of_losing_control",
        "fear_of_death",
        "fear_of_going_crazy",
        "psychedelic_anxiety",
        "surrender_difficulty",
        "control_resistance",
        "fear_of_bad_trip",
        "fear_of_body_sensations",
        "trust_in_facilitator_difficulty",
        "spiritual_openness",
        "spiritual_resistance",
        "meaning_seeking",
        "mystical_expectation",
        "integration_need",
        "hypervigilance",
        "emotional_numbing",
        "intrusive_memories",
        "avoidance_of_triggers",
        "startle_sensitivity",
        "chronic_tension",
        "dissociation_signal",
        "shame_after_vulnerability",
        "chronic_pain_burden",
        "fatigue_burden",
        "body_sensitivity",
        "pain_fear_cycle",
        "symptom_unpredictability",
        "sleep_disruption",
        "somatic_anxiety",
        "body_trust_difficulty",
        "activity_avoidance_due_to_pain",
        "frustration_with_medical_system",
        "speech_anxiety",
        "fear_of_speaking",
        "communication_avoidance",
        "shame_about_speech",
        "anticipation_anxiety",
        "social_visibility_fear",
        "loss_of_control_in_speech",
        "self_expression_block",
        "hopelessness_signal",
        "chronic_stress_signal",
        "depressed_mood_signal",
        "loss_of_meaning",
        "identity_confusion",
        "life_transition_distress",
        "inner_conflict",
        "desire_for_change",
        "search_for_self_understanding",
    }
)


def _detect(raw_text: str, language: SupportedLanguage) -> set[str]:
    statement = Statement(
        session_id="session-intake-001",
        text=raw_text,
        sequence=0,
        language=language,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def load_scenario_text(markdown_path: Path) -> str:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    in_scenario = False
    scenario_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == "# Scenario":
            in_scenario = True
            continue
        if in_scenario and stripped.startswith("# "):
            break
        if in_scenario and stripped:
            scenario_lines.append(stripped)

    return " ".join(scenario_lines)


def load_bullet_section(markdown_path: Path, heading: str) -> list[str]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    in_section = False
    items: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == f"# {heading}":
            in_section = True
            continue
        if in_section and stripped.startswith("# "):
            break
        if in_section and stripped.startswith("- "):
            items.append(stripped[2:].strip())

    return items


def run_human_case_pipeline(case_path: Path, session_id: str) -> set[str]:
    raw_text = load_scenario_text(case_path)
    transcript = Transcript(
        session_id=session_id,
        raw_text=raw_text,
        language=SupportedLanguage.ENGLISH,
    )
    statements = split_transcript_to_statements(transcript)
    pattern_tags = pattern_tag_evidence_items(statements_to_evidence(statements))
    return {tag.canonical_id for tag in pattern_tags}


def test_semantic_vocabulary_includes_intake_domains():
    for category in (SAFETY, BODY, SPEECH, SESSION, TRAUMA, MEANING):
        assert category in VALID_CATEGORIES

    for attribute in (
        REPORTED_FEAR,
        REPORTED_DISTRESS,
        SAFETY_FEELING,
        PAIN_BURDEN,
        BODY_TRUST,
        SPEECH_COMFORT,
        SESSION_OPENNESS,
        TRAUMA_STRESS,
        MEANING_SENSE,
        CHANGE_DESIRE,
    ):
        assert attribute in VALID_ATTRIBUTES

    for value in ("elevated", "seeking", "resistant", "open", "blocked"):
        assert value in VALID_VALUES


def test_intake_semantic_fact_validation():
    fact = SemanticFact(
        category=SAFETY,
        attribute=REPORTED_FEAR,
        value="elevated",
        evidence="I'm afraid to live.",
    )
    assert fact.is_valid() is True


def test_ukrainian_high_distress_inputs():
    assert "existential_fear" in _detect("я боюся жити", SupportedLanguage.UKRAINIAN)
    assert "safety_concern_signal" in _detect("я боюся жити", SupportedLanguage.UKRAINIAN)

    scared = _detect("мені страшно", SupportedLanguage.UKRAINIAN)
    assert "generalized_fear" in scared or "emotional_distress_signal" in scared

    assert "fear_of_losing_control" in _detect(
        "я боюся втратити контроль", SupportedLanguage.UKRAINIAN
    )


def test_fibromyalgia_style_body_pain_statements():
    assert "chronic_pain_burden" in _detect(
        "моє тіло постійно болить", SupportedLanguage.UKRAINIAN
    )
    assert "chronic_pain_burden" in _detect(
        "my body hurts all the time", SupportedLanguage.ENGLISH
    )
    assert "symptom_unpredictability" in _detect(
        "my symptoms are unpredictable", SupportedLanguage.ENGLISH
    )
    assert "frustration_with_medical_system" in _detect(
        "doctors don't understand my pain", SupportedLanguage.ENGLISH
    )


def test_stuttering_related_speech_statements():
    assert "shame_about_speech" in _detect(
        "заікаюся і мені соромно", SupportedLanguage.UKRAINIAN
    )
    assert "fear_of_speaking" in _detect(
        "I'm afraid to speak in front of people", SupportedLanguage.ENGLISH
    )
    assert "speech_anxiety" in _detect(
        "me pongo ansioso cuando tengo que hablar", SupportedLanguage.SPANISH
    )
    assert "loss_of_control_in_speech" in _detect(
        "слова застревают и я panic", SupportedLanguage.RUSSIAN
    )


def test_psychedelic_concern_statements():
    assert "psychedelic_anxiety" in _detect(
        "I'm anxious about the ceremony", SupportedLanguage.ENGLISH
    )
    assert "fear_of_bad_trip" in _detect(
        "я боюся поганого досвіду", SupportedLanguage.UKRAINIAN
    )
    assert "integration_need" in _detect(
        "necesito ayuda para integrar la experiencia", SupportedLanguage.SPANISH
    )
    assert "surrender_difficulty" in _detect(
        "мне трудно отпустить контроль", SupportedLanguage.RUSSIAN
    )


def test_multilingual_meaning_and_trauma_signals():
    assert "loss_of_meaning" in _detect("life feels meaningless", SupportedLanguage.ENGLISH)
    assert "hypervigilance" in _detect("я постійно напоготові", SupportedLanguage.UKRAINIAN)
    assert "intrusive_memories" in _detect(
        "vuelven recuerdos no deseados", SupportedLanguage.SPANISH
    )
    assert "hopelessness_signal" in _detect("я чувствую hopeless", SupportedLanguage.RUSSIAN)


def test_neutral_statements_do_not_false_positive():
    neutral_cases = [
        ("I like music.", SupportedLanguage.ENGLISH),
        ("Сьогодні я працюю над проектом.", SupportedLanguage.UKRAINIAN),
        ("Me gusta caminar por la mañana.", SupportedLanguage.SPANISH),
        ("Сегодня хорошая погода.", SupportedLanguage.RUSSIAN),
        ("I had a normal day at work.", SupportedLanguage.ENGLISH),
    ]

    for raw_text, language in neutral_cases:
        detected = _detect(raw_text, language)
        assert detected.isdisjoint(INTAKE_PATTERN_IDS)


def test_integrated_domain_scenarios_detect_expected_patterns():
    integrated_cases = [
        "024_fear_safety_distress_integrated.md",
        "025_session_concerns_integrated.md",
        "026_trauma_stress_integrated.md",
        "027_body_pain_integrated.md",
        "028_speech_communication_integrated.md",
        "029_meaning_direction_integrated.md",
    ]

    for index, filename in enumerate(integrated_cases, start=1):
        case_path = TEST_CASES_DIR / filename
        expected_patterns = load_bullet_section(case_path, "Expected Patterns")
        detected = run_human_case_pipeline(case_path, f"session-intake-integrated-{index:03d}")

        for pattern_id in expected_patterns:
            assert pattern_id in detected


def test_sample_human_cases_for_new_patterns():
    sample_cases = [
        ("030_panic_reactivity.md", "panic_reactivity"),
        ("037_fear_of_bad_trip.md", "fear_of_bad_trip"),
        ("045_hypervigilance.md", "hypervigilance"),
        ("053_chronic_pain_burden.md", "chronic_pain_burden"),
        ("063_speech_anxiety.md", "speech_anxiety"),
        ("071_hopelessness_signal.md", "hopelessness_signal"),
    ]

    for filename, pattern_id in sample_cases:
        detected = run_human_case_pipeline(
            TEST_CASES_DIR / filename,
            f"session-intake-{pattern_id}",
        )
        assert pattern_id in detected


def test_detection_is_deterministic():
    first = _detect("я боюся жити", SupportedLanguage.UKRAINIAN)
    second = _detect("я боюся жити", SupportedLanguage.UKRAINIAN)
    assert first == second
