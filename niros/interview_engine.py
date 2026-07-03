from enum import Enum

from pydantic import BaseModel

from niros.hypotheses import Hypothesis
from niros.knowledge import KnowledgePattern, PatternLoader
from niros.models import InterviewState
from niros.patterns import PatternTag
from niros.question_ranking import QuestionRankingEngine, format_ranking_debug
from niros.questions import GraphQuestionSuggester, QuestionSuggestion, select_follow_up_questions

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
    def __init__(
        self,
        loader: PatternLoader | None = None,
        question_ranker: QuestionRankingEngine | None = None,
    ) -> None:
        self._loader = loader or PatternLoader()
        self._question_suggester = GraphQuestionSuggester(loader=self._loader)
        self._question_ranker = question_ranker or QuestionRankingEngine()
        self._last_ranked_questions: list | None = None

    def get_last_question_ranking_debug(self) -> str | None:
        if self._last_ranked_questions is None:
            return None
        return format_ranking_debug(self._last_ranked_questions)

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
            related = self._select_related_question(
                primary_tag,
                pattern_tags,
                hypotheses,
            )
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
        selected_pattern, selected_question = self._select_ranked_direct_question(
            primary_tag,
            pattern_tags,
            hypotheses,
        )

        if len(unique_patterns) == 1:
            return InterviewDecision(
                next_phase=current_phase,
                selected_pattern=selected_pattern or primary_tag.canonical_id,
                selected_question=selected_question,
                reason="single_pattern_direct_follow_up",
                confidence=primary_tag.confidence,
            )

        return InterviewDecision(
            next_phase=current_phase,
            selected_pattern=selected_pattern or primary_tag.canonical_id,
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
        pattern_tags: list[PatternTag],
        hypotheses: list[Hypothesis],
    ) -> tuple[str, str, float] | None:
        suggestions = self._question_suggester.suggest(primary_tag)
        related_candidates = [
            suggestion
            for suggestion in suggestions
            if suggestion.reason.startswith("relationship:")
        ]
        ranked = self._question_ranker.rank(
            related_candidates,
            pattern_tags=pattern_tags,
            hypotheses=hypotheses,
        )
        self._last_ranked_questions = ranked
        if not ranked:
            return None

        best = ranked[0]
        return (
            best.source_pattern,
            best.question,
            best.score.graph_priority,
        )

    def _select_ranked_direct_question(
        self,
        primary_tag: PatternTag,
        pattern_tags: list[PatternTag],
        hypotheses: list[Hypothesis],
    ) -> tuple[str | None, str | None]:
        suggestions = self._question_suggester.suggest(primary_tag)
        direct_candidates = [
            suggestion for suggestion in suggestions if suggestion.reason == "matched_pattern"
        ]
        if not direct_candidates:
            direct_questions = select_follow_up_questions(primary_tag, loader=self._loader)
            direct_candidates = [
                QuestionSuggestion(
                    source_pattern=primary_tag.canonical_id,
                    question=question,
                    language=primary_tag.language,
                    reason="matched_pattern",
                    priority=1.0,
                )
                for question in direct_questions
            ]

        ranked = self._question_ranker.rank(
            direct_candidates,
            pattern_tags=pattern_tags,
            hypotheses=hypotheses,
        )
        self._last_ranked_questions = ranked
        if not ranked:
            return None, None

        best = ranked[0]
        return best.source_pattern, best.question

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
