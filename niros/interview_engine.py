from enum import Enum

from pydantic import BaseModel

from niros.hypotheses import Hypothesis
from niros.knowledge import KnowledgePattern, PatternLoader
from niros.models import InterviewState
from niros.patterns import PatternTag
from niros.questions import GraphQuestionSuggester, select_follow_up_questions

HIGH_CONFIDENCE_THRESHOLD = 0.65
MIN_TURNS_FOR_PHASE_ADVANCE = 2
MIN_TAGS_FOR_PHASE_ADVANCE = 2


class BlueprintPhase(str, Enum):
    CONSENT = "consent"
    FREE_NARRATIVE = "free_narrative"
    LIFE_STORY = "life_story"
    RELATIONSHIPS = "relationships"
    FAMILY = "family"
    SELF = "self"
    EMOTIONS = "emotions"
    STRESS_COPING = "stress_coping"
    VALUES_MEANING = "values_meaning"
    CLOSING_REFLECTION = "closing_reflection"


BLUEPRINT_SEQUENCE: list[BlueprintPhase] = [
    BlueprintPhase.CONSENT,
    BlueprintPhase.FREE_NARRATIVE,
    BlueprintPhase.LIFE_STORY,
    BlueprintPhase.RELATIONSHIPS,
    BlueprintPhase.FAMILY,
    BlueprintPhase.SELF,
    BlueprintPhase.EMOTIONS,
    BlueprintPhase.STRESS_COPING,
    BlueprintPhase.VALUES_MEANING,
    BlueprintPhase.CLOSING_REFLECTION,
]

PHASE_OPENERS: dict[BlueprintPhase, str] = {
    BlueprintPhase.FREE_NARRATIVE: "Tell me what brought you here today.",
    BlueprintPhase.LIFE_STORY: "What moments from your life feel most connected to what you are going through now?",
    BlueprintPhase.RELATIONSHIPS: "How do important relationships show up in what you have been experiencing?",
    BlueprintPhase.FAMILY: "What role does family play in the way you handle difficulty?",
    BlueprintPhase.SELF: "How do you usually see yourself when things become hard?",
    BlueprintPhase.EMOTIONS: "What emotions have been most present for you lately?",
    BlueprintPhase.STRESS_COPING: "What happens for you when stress starts to build?",
    BlueprintPhase.VALUES_MEANING: "What matters most to you right now?",
    BlueprintPhase.CLOSING_REFLECTION: "What feels most important for us to have understood today?",
}


class InterviewDecision(BaseModel):
    next_phase: BlueprintPhase
    selected_pattern: str | None
    selected_question: str | None
    reason: str
    confidence: float


class InterviewDecisionEngine:
    def __init__(self, loader: PatternLoader | None = None) -> None:
        self._loader = loader or PatternLoader()
        self._question_suggester = GraphQuestionSuggester(loader=self._loader)

    def decide(
        self,
        interview_state: InterviewState,
        pattern_tags: list[PatternTag],
        hypotheses: list[Hypothesis],
        current_phase: BlueprintPhase,
    ) -> InterviewDecision:
        if not pattern_tags:
            return InterviewDecision(
                next_phase=BlueprintPhase.FREE_NARRATIVE,
                selected_pattern=None,
                selected_question=PHASE_OPENERS[BlueprintPhase.FREE_NARRATIVE],
                reason="no_patterns_continue_narrative",
                confidence=0.0,
            )

        if self._has_enough_evidence(interview_state, pattern_tags, hypotheses):
            next_phase = self._next_blueprint_phase(current_phase)
            patterns = self._loader.load_all()
            primary_tag = _select_primary_tag(pattern_tags, patterns)
            return InterviewDecision(
                next_phase=next_phase,
                selected_pattern=primary_tag.canonical_id,
                selected_question=PHASE_OPENERS.get(next_phase),
                reason="enough_evidence_advance_blueprint",
                confidence=_max_hypothesis_confidence(hypotheses),
            )

        patterns = self._loader.load_all()
        primary_tag = _select_primary_tag(pattern_tags, patterns)
        max_confidence = _max_hypothesis_confidence(hypotheses)

        if max_confidence >= HIGH_CONFIDENCE_THRESHOLD:
            related = self._select_related_question(primary_tag)
            if related is not None:
                pattern_id, question, priority = related
                return InterviewDecision(
                    next_phase=current_phase,
                    selected_pattern=pattern_id,
                    selected_question=question,
                    reason="high_confidence_related_pattern",
                    confidence=max_confidence,
                )

        unique_patterns = _unique_pattern_ids(pattern_tags)
        direct_questions = select_follow_up_questions(primary_tag, loader=self._loader)
        selected_question = _pick_question(direct_questions, interview_state.turn_count)

        if len(unique_patterns) == 1:
            return InterviewDecision(
                next_phase=current_phase,
                selected_pattern=primary_tag.canonical_id,
                selected_question=selected_question,
                reason="single_pattern_direct_follow_up",
                confidence=primary_tag.confidence,
            )

        return InterviewDecision(
            next_phase=current_phase,
            selected_pattern=primary_tag.canonical_id,
            selected_question=selected_question,
            reason="low_confidence_continue_pattern",
            confidence=max_confidence or primary_tag.confidence,
        )

    def _has_enough_evidence(
        self,
        interview_state: InterviewState,
        pattern_tags: list[PatternTag],
        hypotheses: list[Hypothesis],
    ) -> bool:
        if interview_state.turn_count < MIN_TURNS_FOR_PHASE_ADVANCE:
            return False
        if len(pattern_tags) < MIN_TAGS_FOR_PHASE_ADVANCE:
            return False
        return _max_hypothesis_confidence(hypotheses) >= HIGH_CONFIDENCE_THRESHOLD

    def _select_related_question(
        self,
        primary_tag: PatternTag,
    ) -> tuple[str, str, float] | None:
        suggestions = self._question_suggester.suggest(primary_tag)
        for suggestion in suggestions:
            if suggestion.reason.startswith("relationship:"):
                return (
                    suggestion.source_pattern,
                    suggestion.question,
                    suggestion.priority,
                )
        return None

    def _next_blueprint_phase(self, current_phase: BlueprintPhase) -> BlueprintPhase:
        try:
            index = BLUEPRINT_SEQUENCE.index(current_phase)
        except ValueError:
            return BlueprintPhase.FREE_NARRATIVE

        if index >= len(BLUEPRINT_SEQUENCE) - 1:
            return current_phase

        return BLUEPRINT_SEQUENCE[index + 1]


def _unique_pattern_ids(pattern_tags: list[PatternTag]) -> set[str]:
    return {tag.canonical_id for tag in pattern_tags}


def _select_primary_tag(
    pattern_tags: list[PatternTag],
    patterns: list[KnowledgePattern],
) -> PatternTag:
    priorities = {pattern.canonical_id: pattern.interview_priority for pattern in patterns}
    return max(
        pattern_tags,
        key=lambda tag: (priorities.get(tag.canonical_id, 0), tag.confidence),
    )


def _max_hypothesis_confidence(hypotheses: list[Hypothesis]) -> float:
    if not hypotheses:
        return 0.0
    return max(hypothesis.confidence for hypothesis in hypotheses)


def _pick_question(questions: list[str], turn_count: int) -> str | None:
    if not questions:
        return None
    return questions[turn_count % len(questions)]
