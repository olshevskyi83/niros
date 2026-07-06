"""NIROS Human Understanding Engine."""

from niros.evidence import (
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
    statement_to_evidence,
    statements_to_evidence,
)
from niros.hypotheses import Hypothesis, HypothesisGenerator, HypothesisType, generate_hypotheses
from niros.interview_engine import (
    BlueprintPhase,
    InterviewDecision,
    InterviewDecisionEngine,
)
from niros.knowledge import KnowledgePattern, PatternLoader, PatternRelationship, PatternRelationType
from niros.models import (
    IcaroLanguage,
    InterviewPhase,
    InterviewState,
    SupportedLanguage,
)
from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PatternFitReport,
    PatternFitScore,
    PersonFitProfile,
)
from niros.pattern_person_fit_ranking import rank_patterns_for_profile
from niros.pattern_person_fit_report import build_pattern_fit_report
from niros.pattern_person_fit_scoring import score_pattern_fit
from niros.patterns import (
    PatternTag,
    PatternTagger,
    pattern_tag_evidence,
    pattern_tag_evidence_items,
)
from niros.questions import (
    FollowUpQuestionSelector,
    GraphQuestionSuggester,
    QuestionSuggestion,
    select_follow_up_questions,
    suggest_next_questions,
)
from niros.state_machine import InvalidTransitionError, advance, initial_state
from niros.statements import (
    Statement,
    UnsupportedModalityError,
    split_transcript_to_statements,
)
from niros.strategy_candidate_builder import (
    DEFAULT_STRATEGY_ID,
    DRAFT_STRATEGY_STATUS,
    StrategyCandidate,
    build_strategy_candidate,
)
from niros.strategy_explanation import (
    StrategyExplanation,
    StrategyExplanationItem,
    build_strategy_explanation,
)
from niros.transcript import InputModality, Transcript
from niros.voice_transcript import (
    DEFAULT_CONFIDENCE,
    DEFAULT_LANGUAGE,
    DEFAULT_SESSION_ID,
    DEFAULT_SOURCE,
    TRANSCRIPT_STATUS_TRANSCRIBED,
    VoiceInput as VoiceTranscriptInput,
    VoiceTranscript,
    create_transcript_from_text,
)

__all__ = [
    "BlueprintPhase",
    "DEFAULT_CONFIDENCE",
    "DEFAULT_LANGUAGE",
    "DEFAULT_SESSION_ID",
    "DEFAULT_SOURCE",
    "DEFAULT_STRATEGY_ID",
    "DRAFT_STRATEGY_STATUS",
    "EvidenceItem",
    "EvidenceSource",
    "EvidenceType",
    "FollowUpQuestionSelector",
    "GraphQuestionSuggester",
    "Hypothesis",
    "HypothesisGenerator",
    "HypothesisType",
    "IcaroLanguage",
    "KnowledgePattern",
    "InputModality",
    "InterviewDecision",
    "InterviewDecisionEngine",
    "InterviewPhase",
    "InterviewState",
    "InvalidTransitionError",
    "NOT_RECOMMENDED",
    "PatternFitReport",
    "PatternFitScore",
    "PersonFitProfile",
    "PatternTag",
    "PatternTagger",
    "PatternLoader",
    "PatternRelationship",
    "PatternRelationType",
    "QuestionSuggestion",
    "RECOMMENDED",
    "Statement",
    "StrategyCandidate",
    "StrategyExplanation",
    "StrategyExplanationItem",
    "SupportedLanguage",
    "TRANSCRIPT_STATUS_TRANSCRIBED",
    "Transcript",
    "UnsupportedModalityError",
    "USE_WITH_CAUTION",
    "VoiceTranscript",
    "VoiceTranscriptInput",
    "advance",
    "build_pattern_fit_report",
    "build_strategy_candidate",
    "build_strategy_explanation",
    "create_transcript_from_text",
    "generate_hypotheses",
    "initial_state",
    "pattern_tag_evidence",
    "pattern_tag_evidence_items",
    "rank_patterns_for_profile",
    "select_follow_up_questions",
    "score_pattern_fit",
    "split_transcript_to_statements",
    "suggest_next_questions",
    "statement_to_evidence",
    "statements_to_evidence",
]
