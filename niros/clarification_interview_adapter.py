"""Adapter from ClarificationPlan to Adaptive Interview questions.

Optional layer only — does not replace existing interview logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from niros.adaptive_question_targeting import is_question_already_asked
from niros.clarification_engine_v2 import (
    FORBIDDEN_CLARIFICATION_PHRASES,
    NEED_HIGH,
    NEED_LOW,
    NEED_MEDIUM,
    ClarificationPlan,
    ClarificationQuestion,
)

SOURCE_CLARIFICATION_ENGINE_V2 = "clarification_engine_v2"
DEFAULT_MAX_CLARIFICATION_QUESTIONS = 2

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


@dataclass(frozen=True)
class ClarificationInterviewQuestion:
    question: str
    source: str
    target_signal: str
    target_domain: str
    priority: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "question": self.question,
            "source": self.source,
            "target_signal": self.target_signal,
            "target_domain": self.target_domain,
            "priority": self.priority,
            "reason": self.reason,
        }


@dataclass
class ClarificationInterviewContext:
    answered_questions: list[str] = field(default_factory=list)
    blocked_questions: list[str] = field(default_factory=list)
    pending_interview_questions: list[str] = field(default_factory=list)
    clarification_questions_asked: int = 0


class ClarificationInterviewAdapter:
    """Convert ClarificationPlan items into interview-ready clarification questions."""

    def __init__(self, *, max_clarification_questions: int = DEFAULT_MAX_CLARIFICATION_QUESTIONS) -> None:
        self.max_clarification_questions = max_clarification_questions

    def adapt(
        self,
        plan: ClarificationPlan | None,
        context: ClarificationInterviewContext,
    ) -> tuple[ClarificationInterviewQuestion, ...]:
        if not self._should_use_plan(plan):
            return ()

        assert plan is not None

        asked_count = context.clarification_questions_asked
        if asked_count >= self.max_clarification_questions:
            return ()

        adapted: list[ClarificationInterviewQuestion] = []
        seen: set[str] = set()
        remaining_budget = self.max_clarification_questions - asked_count

        for item in _ordered_plan_questions(plan):
            if len(adapted) >= remaining_budget:
                break
            normalized = _normalize_question(item.question)
            if normalized in seen:
                continue
            if self._should_skip_question(item.question, context):
                continue
            seen.add(normalized)
            adapted.append(_to_interview_question(item))

        return tuple(adapted)

    def select_next_question(
        self,
        plan: ClarificationPlan | None,
        context: ClarificationInterviewContext,
    ) -> ClarificationInterviewQuestion | None:
        adapted = self.adapt(plan, context)
        if not adapted:
            return None
        return adapted[0]

    def _should_use_plan(self, plan: ClarificationPlan | None) -> bool:
        if plan is None:
            return False
        if not plan.questions:
            return False
        if plan.overall_need_for_clarification in {NEED_MEDIUM, NEED_HIGH}:
            return True
        if any(item.priority == "high" for item in plan.questions):
            return True
        return False

    def _should_skip_question(self, question: str, context: ClarificationInterviewContext) -> bool:
        if is_question_already_asked(question, context.answered_questions):
            return True
        normalized = _normalize_question(question)
        blocked = {_normalize_question(item) for item in context.blocked_questions}
        if normalized in blocked:
            return True
        pending = {_normalize_question(item) for item in context.pending_interview_questions}
        if normalized in pending:
            return True
        lowered = question.lower()
        for phrase in FORBIDDEN_CLARIFICATION_PHRASES:
            if phrase in lowered:
                return True
        return False

    @staticmethod
    def clarification_precedes_generic_follow_up() -> bool:
        return True


def select_clarification_interview_question(
    plan: ClarificationPlan | None,
    *,
    answered_questions: list[str],
    blocked_questions: list[str],
    pending_interview_questions: list[str] | None = None,
    max_clarification_questions: int = DEFAULT_MAX_CLARIFICATION_QUESTIONS,
) -> str | None:
    if plan is None:
        return None

    context = ClarificationInterviewContext(
        answered_questions=list(answered_questions),
        blocked_questions=list(blocked_questions),
        pending_interview_questions=list(pending_interview_questions or []),
        clarification_questions_asked=count_clarification_questions_asked(plan, answered_questions),
    )
    selected = ClarificationInterviewAdapter(
        max_clarification_questions=max_clarification_questions,
    ).select_next_question(plan, context)
    if selected is None:
        return None
    return selected.question


def count_clarification_questions_asked(
    plan: ClarificationPlan,
    answered_questions: list[str],
) -> int:
    plan_questions = {_normalize_question(item.question) for item in plan.questions}
    return sum(
        1 for question in answered_questions if _normalize_question(question) in plan_questions
    )


def compare_interview_question_priority(
    clarification: ClarificationInterviewQuestion,
    *,
    generic_follow_up: str,
    assessment_style_follow_up: str | None = None,
) -> bool:
    """Clarification should precede generic and assessment-style follow-ups."""
    del generic_follow_up, assessment_style_follow_up
    return clarification.source == SOURCE_CLARIFICATION_ENGINE_V2


def _ordered_plan_questions(plan: ClarificationPlan) -> tuple[ClarificationQuestion, ...]:
    return tuple(
        sorted(
            plan.questions,
            key=lambda item: (PRIORITY_RANK.get(item.priority, 9), -item.expected_information_gain, item.id),
        )
    )


def _to_interview_question(item: ClarificationQuestion) -> ClarificationInterviewQuestion:
    return ClarificationInterviewQuestion(
        question=_humanize_question(item.question),
        source=SOURCE_CLARIFICATION_ENGINE_V2,
        target_signal=item.target_signal,
        target_domain=item.target_domain,
        priority=item.priority,
        reason=item.reason,
    )


def _humanize_question(question: str) -> str:
    stripped = question.strip()
    if not stripped:
        return stripped
    if stripped.lower().startswith("clarify "):
        return stripped.replace("Clarify ", "Can you say more about ", 1)
    return stripped


def _normalize_question(text: str) -> str:
    return " ".join(text.lower().split())
