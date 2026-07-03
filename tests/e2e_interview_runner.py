from __future__ import annotations

from dataclasses import dataclass, field

from niros.evidence import statements_to_evidence
from niros.human_profile_summary import NO_EVIDENCE_PROFILE_TEXT, build_human_profile_summary
from niros.hypotheses import Hypothesis, generate_hypotheses
from niros.interview_engine import BlueprintPhase, InterviewDecision, InterviewDecisionEngine
from niros.models import InterviewPhase, SupportedLanguage
from niros.patterns import PatternTag, pattern_tag_evidence_items
from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.factory import get_semantic_interpreter
from niros.state_machine import advance, initial_state
from niros.statements import split_transcript_to_statements
from niros.statement_normalizer import normalize_user_input
from niros.transcript import Transcript

from tests.e2e_interview_scenarios import EndToEndScenario


@dataclass
class TurnResult:
    turn_index: int
    raw_text: str
    normalized_text: str
    semantic_result: SemanticInterpretationResult
    pattern_tags: list[PatternTag]
    decision: InterviewDecision


@dataclass
class InterviewRunResult:
    session_id: str
    turns: list[TurnResult] = field(default_factory=list)
    all_pattern_tags: list[PatternTag] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    profile: dict = field(default_factory=dict)
    detected_pattern_ids: frozenset[str] = frozenset()
    follow_up_questions: list[str] = field(default_factory=list)


def run_multi_turn_interview(
    scenario: EndToEndScenario,
    *,
    provider: str = "mock",
    normalizer_mode: str = "passthrough",
    current_phase: BlueprintPhase = BlueprintPhase.FREE_NARRATIVE,
) -> InterviewRunResult:
    interpreter = get_semantic_interpreter(provider)
    engine = InterviewDecisionEngine()
    interview_state = advance(initial_state(scenario.session_id), consent_granted=True)
    interview_state = interview_state.model_copy(
        update={
            "input_language": SupportedLanguage.ENGLISH,
            "turn_count": 0,
        }
    )
    assert interview_state.state == InterviewPhase.FREE_NARRATIVE

    all_pattern_tags: list[PatternTag] = []
    turn_results: list[TurnResult] = []
    follow_up_questions: list[str] = []

    for turn_index, raw_text in enumerate(scenario.turns, start=1):
        semantic_result = interpreter.interpret_result(raw_text)
        normalized_text = normalize_user_input(
            raw_text,
            mode=normalizer_mode,
            provider=provider,
        )

        transcript = Transcript(
            session_id=scenario.session_id,
            raw_text=normalized_text,
            language=SupportedLanguage.ENGLISH,
        )
        statements = split_transcript_to_statements(transcript)
        evidence_items = statements_to_evidence(statements)
        turn_tags = pattern_tag_evidence_items(evidence_items)
        all_pattern_tags.extend(turn_tags)

        hypotheses = generate_hypotheses(all_pattern_tags)
        decision = engine.decide(
            interview_state,
            all_pattern_tags,
            hypotheses,
            current_phase,
        )

        if decision.selected_question:
            follow_up_questions.append(decision.selected_question)

        turn_results.append(
            TurnResult(
                turn_index=turn_index,
                raw_text=raw_text,
                normalized_text=normalized_text,
                semantic_result=semantic_result,
                pattern_tags=turn_tags,
                decision=decision,
            )
        )
        interview_state = interview_state.model_copy(update={"turn_count": turn_index})

    profile = build_human_profile_summary(all_pattern_tags)
    final_hypotheses = generate_hypotheses(all_pattern_tags)

    return InterviewRunResult(
        session_id=scenario.session_id,
        turns=turn_results,
        all_pattern_tags=all_pattern_tags,
        hypotheses=final_hypotheses,
        profile=profile,
        detected_pattern_ids=frozenset(tag.canonical_id for tag in all_pattern_tags),
        follow_up_questions=follow_up_questions,
    )


def assert_scenario_expectations(scenario: EndToEndScenario, result: InterviewRunResult) -> None:
    assert len(result.turns) == len(scenario.turns)
    assert 30 <= len(scenario.turns) <= 50

    for turn in result.turns:
        assert isinstance(turn.semantic_result, SemanticInterpretationResult)
        assert turn.semantic_result.raw_text == turn.raw_text
        for fact in turn.semantic_result.facts:
            assert fact.is_valid() is True
        assert turn.decision.selected_question is not None
        assert turn.decision.reason

    for expected_pattern in scenario.expected_patterns:
        assert expected_pattern in result.detected_pattern_ids

    forbidden_hits = scenario.forbidden_patterns & result.detected_pattern_ids
    assert not forbidden_hits, f"Unexpected patterns detected: {sorted(forbidden_hits)}"

    hypothesis_ids = [hypothesis.id for hypothesis in result.hypotheses]
    assert len(hypothesis_ids) == len(set(hypothesis_ids))

    for expected_hypothesis_id in scenario.expected_hypothesis_ids:
        assert any(
            expected_hypothesis_id in hypothesis.id for hypothesis in result.hypotheses
        )

    if scenario.expect_profile_evidence:
        assert result.profile["primary_pattern"] is not None
        assert result.profile["profile_text"] != NO_EVIDENCE_PROFILE_TEXT
        primary_id = result.profile["primary_pattern"]["canonical_id"]
        assert primary_id in scenario.expected_patterns
        secondary_ids = {
            pattern["canonical_id"] for pattern in result.profile["secondary_patterns"]
        }
        assert secondary_ids.issubset(result.detected_pattern_ids)
    else:
        assert result.profile["primary_pattern"] is None
        assert result.profile["profile_text"] == NO_EVIDENCE_PROFILE_TEXT

    if scenario.minimum_follow_up_questions:
        assert len(result.follow_up_questions) >= scenario.minimum_follow_up_questions
        assert any("?" in question for question in result.follow_up_questions)


def stable_profile_snapshot(result: InterviewRunResult) -> dict:
    return {
        "detected_pattern_ids": sorted(result.detected_pattern_ids),
        "primary_pattern": (
            result.profile["primary_pattern"]["canonical_id"]
            if result.profile["primary_pattern"]
            else None
        ),
        "secondary_patterns": [
            pattern["canonical_id"] for pattern in result.profile["secondary_patterns"]
        ],
        "profile_text": result.profile["profile_text"],
        "hypothesis_ids": sorted(hypothesis.id for hypothesis in result.hypotheses),
    }
