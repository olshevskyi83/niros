from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from demo_interview import run_interview_session
from niros.human_digital_fingerprint import (
    NO_EVIDENCE_PROFILE_TEXT,
    build_human_digital_fingerprint,
)
from niros.intake_protocol import (
    DURATION_ID,
    PRESENTING_PROBLEM_ID,
    build_presenting_problem,
)
from niros.intake_runner import fingerprint_presenting_problem_is_specific
from niros.intervention_strategy import (
    build_intervention_strategy,
    is_high_grounding,
    render_intervention_strategy,
)
from run_niros import build_fingerprint_from_session, run_niros

FULL_INTAKE_ANSWERS = {
    PRESENTING_PROBLEM_ID: "Я прийшов, бо боюся жити і постійно відчуваю страх.",
    DURATION_ID: "Це триває вже кілька років.",
    "perceived_causes": "Мені здається, це почалося після сильного стресу і болю в тілі.",
    "current_impact": "Я не можу нормально працювати, спати і говорити з людьми.",
    "previous_attempts": "Я пробував терапію і медикаменти, але мені мало що допомагає.",
    "desired_outcome": "Я хочу зрозуміти себе і знайти свою пісню.",
}


def test_intake_session_to_intervention_strategy_pipeline():
    session = run_interview_session(
        intake_answers=FULL_INTAKE_ANSWERS,
        user_inputs=["Мені важко довіряти людям на роботі."],
        turns=1,
        provider="mock",
        language="uk",
        print_output=False,
    )

    assert session.intake_result is not None
    assert session.intake_result.intake_state.completed is True

    presenting_problem = build_presenting_problem(session.intake_result.intake_state)
    assert presenting_problem["main_problem"].startswith("Я прийшов")
    assert "знайти свою пісню" in presenting_problem["desired_outcome"]
    assert fingerprint_presenting_problem_is_specific(presenting_problem)

    assert session.cumulative_pattern_tags
    detected_ids = {tag.canonical_id for tag in session.cumulative_pattern_tags}
    assert "existential_fear" in detected_ids
    assert "emotional_distress_signal" in detected_ids

    fingerprint = build_fingerprint_from_session(session)
    assert fingerprint["summary_text"] != NO_EVIDENCE_PROFILE_TEXT
    assert fingerprint["presenting_problem"]["main_problem"]

    strategy = build_intervention_strategy(fingerprint)
    rendered = render_intervention_strategy(strategy)

    assert is_high_grounding(strategy.grounding_priority)
    assert strategy.pacing == "slow"
    assert strategy.cognitive_load == "low"
    assert "=== NIROS Intervention Strategy ===" in rendered


def test_run_niros_renders_strategy_blueprint_and_timeline():
    output = io.StringIO()

    exit_code = run_niros(
        intake_answers=FULL_INTAKE_ANSWERS,
        user_inputs=["Мені важко довіряти людям на роботі."],
        turns=1,
        provider="mock",
        language="uk",
        output_stream=output,
    )

    rendered = output.getvalue()

    assert exit_code == 0
    assert "Structured Intake" in rendered
    assert "=== Human Profile Report ===" in rendered
    assert rendered.index("=== Human Profile Report ===") < rendered.index("=== NIROS Intervention Strategy ===")
    assert rendered.index("=== NIROS Intervention Strategy ===") < rendered.index("Scenario Blueprint")
    assert "Scenario Blueprint" in rendered
    assert "Session Timeline" in rendered
    assert "Grounding priority:" in rendered
    assert "знайти свою пісню" in rendered

    session = run_interview_session(
        intake_answers=FULL_INTAKE_ANSWERS,
        user_inputs=["Мені важко довіряти людям на роботі."],
        turns=1,
        provider="mock",
        language="uk",
        print_output=False,
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=session.cumulative_pattern_tags,
        presenting_problem=session.presenting_problem,
    )
    strategy = build_intervention_strategy(fingerprint)

    assert is_high_grounding(strategy.grounding_priority)
    assert strategy.pacing == "slow"
    assert strategy.cognitive_load == "low"
