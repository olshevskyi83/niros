from pathlib import Path

from niros.evidence import statements_to_evidence
from niros.hypotheses import generate_hypotheses
from niros.interview_engine import BlueprintPhase, InterviewDecisionEngine
from niros.models import InterviewPhase, SupportedLanguage
from niros.patterns import pattern_tag_evidence_items
from niros.state_machine import advance, initial_state
from niros.statements import split_transcript_to_statements
from niros.transcript import Transcript

TEST_CASES_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "test_cases"


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


def test_human_case_001_people_pleasing_conflict_avoidance():
    case_path = TEST_CASES_DIR / "001_people_pleasing_conflict_avoidance.md"
    raw_text = load_scenario_text(case_path)
    expected_patterns = load_bullet_section(case_path, "Expected Patterns")
    expected_hypotheses = load_bullet_section(case_path, "Expected Hypotheses")

    transcript = Transcript(
        session_id="session-human-001",
        raw_text=raw_text,
        language=SupportedLanguage.ENGLISH,
    )

    statements = split_transcript_to_statements(transcript)
    evidence_items = statements_to_evidence(statements)
    pattern_tags = pattern_tag_evidence_items(evidence_items)
    hypotheses = generate_hypotheses(pattern_tags)

    canonical_ids = {tag.canonical_id for tag in pattern_tags}
    hypothesis_ids = {hypothesis.canonical_id for hypothesis in hypotheses}

    for pattern_id in expected_patterns:
        assert pattern_id in canonical_ids

    for hypothesis_id in expected_hypotheses:
        assert hypothesis_id in hypothesis_ids

    interview_state = advance(initial_state("session-human-001"), consent_granted=True)
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

    assert decision.selected_question
    assert decision.reason
