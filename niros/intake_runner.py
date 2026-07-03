from __future__ import annotations

from dataclasses import dataclass, field

from niros.adaptive_question_targeting import (
    collect_answered_topics,
    extended_blocked_questions,
    is_question_already_asked,
    merged_used_topics,
    register_adaptive_answer,
    select_intake_targeted_question,
)
from niros.evidence import statements_to_evidence
from niros.evidence_store import EvidenceStore
from niros.hypotheses import Hypothesis, generate_hypotheses
from niros.input_language import resolve_input_language
from niros.intake_protocol import (
    DEFAULT_INTAKE_PROTOCOL,
    IntakeProtocol,
    IntakeState,
    build_presenting_problem,
    intake_state_from_answers,
)
from niros.interview_engine import BlueprintPhase, InterviewDecisionEngine
from niros.models import InterviewPhase, SupportedLanguage
from niros.patterns import PatternTag, pattern_tag_evidence_items
from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.state_machine import advance, initial_state
from niros.statements import split_transcript_to_statements
from niros.transcript import Transcript


@dataclass
class IntakeTurnRecord:
    question_id: str
    question: str
    raw_answer: str
    normalized_answer: str
    pattern_tags: list[PatternTag] = field(default_factory=list)
    semantic_result: SemanticInterpretationResult | None = None


@dataclass
class IntakeSessionResult:
    intake_state: IntakeState
    turns: list[IntakeTurnRecord] = field(default_factory=list)
    cumulative_pattern_tags: list[PatternTag] = field(default_factory=list)
    evidence_store: EvidenceStore = field(default_factory=EvidenceStore)


def process_intake_answer(
    *,
    question_id: str,
    raw_answer: str,
    session_id: str,
    normalized_answer: str,
    semantic_result: SemanticInterpretationResult | None = None,
    explicit_language: str | None = None,
    evidence_store: EvidenceStore | None = None,
) -> tuple[list[PatternTag], EvidenceStore]:
    store = evidence_store or EvidenceStore()
    input_language = resolve_input_language(
        raw_text=raw_answer,
        explicit_language=explicit_language,
        semantic_result=semantic_result,
    )
    transcript = Transcript(
        session_id=session_id,
        raw_text=normalized_answer,
        language=input_language,
    )
    statements = split_transcript_to_statements(transcript)
    evidence_items = statements_to_evidence(statements)
    pattern_tags = pattern_tag_evidence_items(
        evidence_items,
        semantic_facts=semantic_result.facts if semantic_result is not None else None,
    )

    if semantic_result is not None:
        for fact in semantic_result.facts:
            store.add_fact(fact)

    return pattern_tags, store


def run_structured_intake(
    *,
    session_id: str,
    answers_by_question_id: dict[str, str] | None = None,
    planned_answers: list[str | None] | None = None,
    language: str | None = None,
    protocol: IntakeProtocol = DEFAULT_INTAKE_PROTOCOL,
    normalize_answer,
    extract_semantic_result=None,
    provider: str = "mock",
) -> IntakeSessionResult:
    answers: dict[str, str] = dict(answers_by_question_id or {})
    question_ids = protocol.question_ids()
    turns: list[IntakeTurnRecord] = []
    cumulative_pattern_tags: list[PatternTag] = []
    evidence_store = EvidenceStore()
    resolved_language = language or "en"

    for index, question_id in enumerate(question_ids):
        if question_id in answers:
            raw_answer = answers[question_id]
        elif planned_answers is not None and index < len(planned_answers) and planned_answers[index] is not None:
            raw_answer = planned_answers[index]
        else:
            break

        question_text = protocol.question_text(question_id, resolved_language)
        semantic_result = None
        if extract_semantic_result is not None and (provider == "openai"):
            semantic_result = extract_semantic_result(raw_answer, provider)

        normalized_answer = normalize_answer(raw_answer)
        pattern_tags, evidence_store = process_intake_answer(
            question_id=question_id,
            raw_answer=raw_answer,
            session_id=session_id,
            normalized_answer=normalized_answer,
            semantic_result=semantic_result,
            explicit_language=language,
            evidence_store=evidence_store,
        )
        answers[question_id] = raw_answer
        cumulative_pattern_tags.extend(pattern_tags)
        turns.append(
            IntakeTurnRecord(
                question_id=question_id,
                question=question_text,
                raw_answer=raw_answer,
                normalized_answer=normalized_answer,
                pattern_tags=pattern_tags,
                semantic_result=semantic_result,
            )
        )

    intake_state = intake_state_from_answers(answers, language=resolved_language)
    return IntakeSessionResult(
        intake_state=intake_state,
        turns=turns,
        cumulative_pattern_tags=_merge_cumulative_pattern_tags(cumulative_pattern_tags),
        evidence_store=evidence_store,
    )


def select_adaptive_question(
    *,
    session_id: str,
    cumulative_pattern_tags: list[PatternTag],
    turn_count: int,
    answered_questions: list[str],
    blocked_questions: list[str],
    explicit_language: str | None = None,
    presenting_problem: dict[str, str] | None = None,
    completed_topics: list[str] | None = None,
) -> str | None:
    language = explicit_language or "en"
    intake_context = dict(presenting_problem or {})
    effective_blocked = extended_blocked_questions(
        presenting_problem=intake_context,
        pattern_tags=cumulative_pattern_tags,
        language=language,
        blocked_questions=blocked_questions,
    )
    used_topics = merged_used_topics(
        answered_questions,
        collect_answered_topics(answered_questions),
        completed_topics,
    )

    targeted = select_intake_targeted_question(
        presenting_problem=intake_context,
        pattern_tags=cumulative_pattern_tags,
        language=language,
        answered_questions=answered_questions,
        blocked_questions=effective_blocked,
        answered_topics=used_topics,
        completed_topics=completed_topics,
    )
    if targeted is not None and not is_question_already_asked(targeted, answered_questions):
        return targeted

    hypotheses = generate_hypotheses(cumulative_pattern_tags)
    input_language = (
        SupportedLanguage(explicit_language)
        if explicit_language in {item.value for item in SupportedLanguage}
        else SupportedLanguage.ENGLISH
    )
    interview_state = advance(initial_state(session_id), consent_granted=True)
    interview_state = interview_state.model_copy(
        update={
            "input_language": input_language,
            "turn_count": turn_count,
        }
    )
    decision = InterviewDecisionEngine().decide(
        interview_state,
        cumulative_pattern_tags,
        hypotheses,
        BlueprintPhase.FREE_NARRATIVE,
        answered_questions=answered_questions,
        blocked_questions=effective_blocked,
    )
    selected = decision.selected_question
    if selected is not None and is_question_already_asked(selected, answered_questions):
        return None
    return selected


def run_adaptive_decision(
    *,
    session_id: str,
    raw_text: str,
    normalized_answer: str,
    turn_count: int,
    cumulative_pattern_tags: list[PatternTag],
    answered_questions: list[str],
    blocked_questions: list[str],
    semantic_result: SemanticInterpretationResult | None = None,
    explicit_language: str | None = None,
    presenting_problem: dict[str, str] | None = None,
    completed_topics: list[str] | None = None,
    current_question: str | None = None,
) -> tuple[list[PatternTag], list[Hypothesis], str | None, list[PatternTag]]:
    language = explicit_language or "en"
    intake_context = dict(presenting_problem or {})
    effective_blocked = extended_blocked_questions(
        presenting_problem=intake_context,
        pattern_tags=cumulative_pattern_tags,
        language=language,
        blocked_questions=blocked_questions,
    )
    if current_question is not None:
        register_adaptive_answer(
            current_question,
            raw_text,
            answered_questions=answered_questions,
            completed_topics=completed_topics or [],
        )
    used_topics = merged_used_topics(
        answered_questions,
        collect_answered_topics(answered_questions),
        completed_topics,
    )
    input_language = resolve_input_language(
        raw_text=raw_text,
        explicit_language=explicit_language,
        semantic_result=semantic_result,
    )
    transcript = Transcript(
        session_id=session_id,
        raw_text=normalized_answer,
        language=input_language,
    )
    statements = split_transcript_to_statements(transcript)
    evidence_items = statements_to_evidence(statements)
    turn_pattern_tags = pattern_tag_evidence_items(
        evidence_items,
        semantic_facts=semantic_result.facts if semantic_result is not None else None,
    )
    all_pattern_tags = _merge_cumulative_pattern_tags(cumulative_pattern_tags + turn_pattern_tags)
    hypotheses = generate_hypotheses(all_pattern_tags)
    effective_blocked = extended_blocked_questions(
        presenting_problem=intake_context,
        pattern_tags=all_pattern_tags,
        language=language,
        blocked_questions=blocked_questions,
    )

    targeted = select_intake_targeted_question(
        presenting_problem=intake_context,
        pattern_tags=all_pattern_tags,
        language=language,
        answered_questions=answered_questions,
        blocked_questions=effective_blocked,
        answered_topics=used_topics,
        completed_topics=completed_topics,
    )
    if targeted is not None and not is_question_already_asked(targeted, answered_questions):
        return turn_pattern_tags, hypotheses, targeted, all_pattern_tags

    interview_state = advance(initial_state(session_id), consent_granted=True)
    interview_state = interview_state.model_copy(
        update={
            "input_language": input_language,
            "turn_count": turn_count,
        }
    )
    assert interview_state.state == InterviewPhase.FREE_NARRATIVE

    decision = InterviewDecisionEngine().decide(
        interview_state,
        all_pattern_tags,
        hypotheses,
        BlueprintPhase.FREE_NARRATIVE,
        answered_questions=answered_questions,
        blocked_questions=effective_blocked,
    )
    selected = decision.selected_question
    if selected is not None and is_question_already_asked(selected, answered_questions):
        selected = None
    return turn_pattern_tags, hypotheses, selected, all_pattern_tags


def intake_blocked_questions(protocol: IntakeProtocol, language: str) -> list[str]:
    blocked = protocol.all_question_texts(language)
    blocked.extend(protocol.all_question_texts("en"))
    return blocked


def presenting_problem_is_specific(presenting_problem: dict[str, str]) -> bool:
    main_problem = presenting_problem.get("main_problem", "").strip()
    if len(main_problem) < 12:
        return False
    generic_markers = (
        "tell me a little about yourself",
        "tell me about yourself",
        "nothing",
        "don't know",
        "не знаю",
    )
    lowered = main_problem.lower()
    return not any(marker in lowered for marker in generic_markers)


def fingerprint_presenting_problem_is_specific(presenting_problem: dict[str, str]) -> bool:
    if not presenting_problem_is_specific(presenting_problem):
        return False
    populated_fields = sum(
        1 for value in presenting_problem.values() if value.strip()
    )
    return populated_fields >= 3


def _merge_cumulative_pattern_tags(pattern_tags: list[PatternTag]) -> list[PatternTag]:
    best_by_id: dict[str, PatternTag] = {}
    for tag in pattern_tags:
        current = best_by_id.get(tag.canonical_id)
        if current is None or tag.confidence > current.confidence:
            best_by_id[tag.canonical_id] = tag
    return list(best_by_id.values())
