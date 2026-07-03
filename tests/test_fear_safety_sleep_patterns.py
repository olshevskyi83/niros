from pathlib import Path

from niros.evidence import statement_to_evidence, statements_to_evidence
from niros.hypotheses import generate_hypotheses
from niros.interview_engine import BlueprintPhase, InterviewDecisionEngine
from niros.models import InterviewPhase, SupportedLanguage
from niros.patterns import PatternTagger, pattern_tag_evidence_items
from niros.state_machine import advance, initial_state
from niros.statements import Statement, split_transcript_to_statements
from niros.transcript import Transcript

TEST_CASES_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "test_cases"

FEAR_SAFETY_SLEEP_PATTERNS = frozenset(
    {
        "existential_fear",
        "generalized_fear",
        "nightmare_disturbance",
        "safety_concern_signal",
        "emotional_distress_signal",
    }
)


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


def run_human_case_pipeline(
    case_path: Path,
    session_id: str,
) -> tuple[set[str], set[str], list, object]:
    raw_text = load_scenario_text(case_path)

    transcript = Transcript(
        session_id=session_id,
        raw_text=raw_text,
        language=SupportedLanguage.ENGLISH,
    )

    statements = split_transcript_to_statements(transcript)
    evidence_items = statements_to_evidence(statements)
    pattern_tags = pattern_tag_evidence_items(evidence_items)
    hypotheses = generate_hypotheses(pattern_tags)

    interview_state = advance(initial_state(session_id), consent_granted=True)
    interview_state = interview_state.model_copy(
        update={
            "input_language": SupportedLanguage.ENGLISH,
            "turn_count": 0,
        }
    )
    assert interview_state.state == InterviewPhase.FREE_NARRATIVE

    decision = InterviewDecisionEngine().decide(
        interview_state,
        pattern_tags,
        hypotheses,
        BlueprintPhase.FREE_NARRATIVE,
    )

    canonical_ids = {tag.canonical_id for tag in pattern_tags}
    hypothesis_ids = {hypothesis.canonical_id for hypothesis in hypotheses}
    return canonical_ids, hypothesis_ids, pattern_tags, decision


def _detect(raw_text: str, language: SupportedLanguage) -> set[str]:
    statement = Statement(
        session_id="session-fear-safety-001",
        text=raw_text,
        sequence=0,
        language=language,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def test_ukrainian_existential_fear_and_safety_signal():
    detected = _detect("я боюся жити", SupportedLanguage.UKRAINIAN)

    assert "existential_fear" in detected
    assert "safety_concern_signal" in detected


def test_ukrainian_generalized_fear_or_emotional_distress():
    detected = _detect("мені страшно", SupportedLanguage.UKRAINIAN)

    assert "generalized_fear" in detected or "emotional_distress_signal" in detected


def test_ukrainian_nightmare_disturbance():
    detected = _detect("мені сняться погані сни", SupportedLanguage.UKRAINIAN)

    assert "nightmare_disturbance" in detected


def test_english_existential_fear_and_safety_signal():
    detected = _detect("I'm afraid to live.", SupportedLanguage.ENGLISH)

    assert "existential_fear" in detected
    assert "safety_concern_signal" in detected


def test_english_generalized_fear_or_emotional_distress():
    detected = _detect("I feel scared and I don't know why.", SupportedLanguage.ENGLISH)

    assert "generalized_fear" in detected or "emotional_distress_signal" in detected


def test_english_nightmare_disturbance():
    detected = _detect("I have bad dreams.", SupportedLanguage.ENGLISH)

    assert "nightmare_disturbance" in detected


def test_spanish_existential_fear_and_safety_signal():
    detected = _detect("tengo miedo de vivir", SupportedLanguage.SPANISH)

    assert "existential_fear" in detected
    assert "safety_concern_signal" in detected


def test_spanish_generalized_fear_or_emotional_distress():
    detected = _detect("tengo miedo sin saber por qué", SupportedLanguage.SPANISH)

    assert "generalized_fear" in detected or "emotional_distress_signal" in detected


def test_spanish_nightmare_disturbance():
    detected = _detect("tengo pesadillas que me despiertan", SupportedLanguage.SPANISH)

    assert "nightmare_disturbance" in detected


def test_russian_existential_fear_and_safety_signal():
    detected = _detect("я боюсь жить", SupportedLanguage.RUSSIAN)

    assert "existential_fear" in detected
    assert "safety_concern_signal" in detected


def test_russian_generalized_fear_or_emotional_distress():
    detected = _detect("мне страшно", SupportedLanguage.RUSSIAN)

    assert "generalized_fear" in detected or "emotional_distress_signal" in detected


def test_russian_nightmare_disturbance():
    detected = _detect("мне снятся плохие сны", SupportedLanguage.RUSSIAN)

    assert "nightmare_disturbance" in detected


def test_no_false_positives_on_neutral_statements():
    neutral_cases = [
        ("I like music.", SupportedLanguage.ENGLISH),
        ("Сьогодні я працюю над проектом.", SupportedLanguage.UKRAINIAN),
        ("Me gusta caminar por la mañana.", SupportedLanguage.SPANISH),
        ("Сегодня хорошая погода.", SupportedLanguage.RUSSIAN),
    ]

    for raw_text, language in neutral_cases:
        detected = _detect(raw_text, language)
        assert detected.isdisjoint(FEAR_SAFETY_SLEEP_PATTERNS)


def test_integrated_human_case_detects_all_fear_safety_sleep_patterns():
    case_path = TEST_CASES_DIR / "023_fear_safety_sleep_integrated.md"
    expected_patterns = load_bullet_section(case_path, "Expected Patterns")

    canonical_ids, _hypothesis_ids, _pattern_tags, decision = run_human_case_pipeline(
        case_path,
        "session-fear-safety-integrated",
    )

    for pattern_id in expected_patterns:
        assert pattern_id in canonical_ids

    assert decision.selected_question
    assert decision.reason


def test_human_case_existential_fear():
    case_path = TEST_CASES_DIR / "018_existential_fear.md"
    expected_patterns = load_bullet_section(case_path, "Expected Patterns")

    canonical_ids, _, _, _ = run_human_case_pipeline(case_path, "session-fear-018")

    for pattern_id in expected_patterns:
        assert pattern_id in canonical_ids


def test_human_case_generalized_fear():
    case_path = TEST_CASES_DIR / "019_generalized_fear.md"
    expected_patterns = load_bullet_section(case_path, "Expected Patterns")

    canonical_ids, _, _, _ = run_human_case_pipeline(case_path, "session-fear-019")

    for pattern_id in expected_patterns:
        assert pattern_id in canonical_ids


def test_human_case_nightmare_disturbance():
    case_path = TEST_CASES_DIR / "020_nightmare_disturbance.md"
    expected_patterns = load_bullet_section(case_path, "Expected Patterns")

    canonical_ids, _, _, _ = run_human_case_pipeline(case_path, "session-fear-020")

    for pattern_id in expected_patterns:
        assert pattern_id in canonical_ids


def test_human_case_safety_concern_signal():
    case_path = TEST_CASES_DIR / "021_safety_concern_signal.md"
    expected_patterns = load_bullet_section(case_path, "Expected Patterns")

    canonical_ids, _, _, _ = run_human_case_pipeline(case_path, "session-fear-021")

    for pattern_id in expected_patterns:
        assert pattern_id in canonical_ids


def test_human_case_emotional_distress_signal():
    case_path = TEST_CASES_DIR / "022_emotional_distress_signal.md"
    expected_patterns = load_bullet_section(case_path, "Expected Patterns")

    canonical_ids, _, _, _ = run_human_case_pipeline(case_path, "session-fear-022")

    for pattern_id in expected_patterns:
        assert pattern_id in canonical_ids


def test_detection_is_deterministic():
    first = _detect("мені страшно", SupportedLanguage.UKRAINIAN)
    second = _detect("мені страшно", SupportedLanguage.UKRAINIAN)

    assert first == second


def test_integrated_scenario_text_is_loaded():
    case_path = TEST_CASES_DIR / "023_fear_safety_sleep_integrated.md"
    scenario = load_scenario_text(case_path)

    assert "I'm afraid to live." in scenario
    assert "I have bad dreams." in scenario
