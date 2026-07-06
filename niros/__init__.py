"""NIROS Human Understanding Engine."""

from niros.intake_readiness import (
    DEFAULT_MINIMUM_REQUIRED_SCORE,
    IntakeReadinessReport,
    build_readiness_report_from_session,
    evaluate_intake_readiness,
)
from niros.information_gain import (
    InformationGainCandidate,
    calculate_information_gain_scores,
    select_highest_information_gain,
)
from niros.intake_session_state import (
    DEFAULT_INTAKE_SESSION_ID,
    IntakeSessionState,
    IntakeTurn,
    add_user_turn,
    build_intake_transcript,
    build_person_fit_profile_from_intake,
    create_intake_session,
)
from niros.clarification_selector import (
    QUESTION_PRIORITY_ORDER,
    QUESTION_STATUS_PENDING,
    ClarificationQuestion,
    select_adaptive_question,
    select_next_clarification_question,
)
from niros.intake_coverage import (
    REQUIRED_COVERAGE_DIMENSIONS,
    IntakeCoverageReport,
    IntakeCoverageState,
    evaluate_intake_coverage,
    update_coverage_from_signals,
)
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
from niros.patient_repository import (
    PATIENT_STATUS_ACTIVE,
    PatientRecord,
    PatientRepository,
    SessionRecord,
    create_patient,
    create_session,
    get_patient,
    list_sessions_for_patient,
    load_repository,
    save_repository,
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
from niros.whisper_adapter import (
    DEFAULT_DEVICE,
    DEFAULT_MODEL_NAME,
    DEFAULT_PROVIDER,
    WhisperAdapterConfig,
    WhisperTranscriptionResult,
    build_whisper_transcription_result,
    transcribe_audio_mock,
)

__all__ = [
    "BlueprintPhase",
    "ClarificationQuestion",
    "DEFAULT_CONFIDENCE",
    "DEFAULT_INTAKE_SESSION_ID",
    "DEFAULT_LANGUAGE",
    "DEFAULT_PROVIDER",
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
    "InformationGainCandidate",
    "IntakeCoverageReport",
    "IntakeCoverageState",
    "IntakeReadinessReport",
    "IntakeSessionState",
    "IntakeTurn",
    "InterviewDecision",
    "InterviewDecisionEngine",
    "InterviewPhase",
    "InterviewState",
    "InvalidTransitionError",
    "NOT_RECOMMENDED",
    "PATIENT_STATUS_ACTIVE",
    "PatternFitReport",
    "PatternFitScore",
    "PersonFitProfile",
    "PatientRecord",
    "PatientRepository",
    "PatternTag",
    "PatternTagger",
    "PatternLoader",
    "QUESTION_PRIORITY_ORDER",
    "QUESTION_STATUS_PENDING",
    "PatternRelationship",
    "PatternRelationType",
    "QuestionSuggestion",
    "RECOMMENDED",
    "REQUIRED_COVERAGE_DIMENSIONS",
    "Statement",
    "SessionRecord",
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
    "WhisperAdapterConfig",
    "WhisperTranscriptionResult",
    "advance",
    "add_user_turn",
    "build_intake_transcript",
    "build_pattern_fit_report",
    "build_person_fit_profile_from_intake",
    "build_readiness_report_from_session",
    "build_strategy_candidate",
    "build_strategy_explanation",
    "build_whisper_transcription_result",
    "calculate_information_gain_scores",
    "create_intake_session",
    "create_patient",
    "create_session",
    "create_transcript_from_text",
    "evaluate_intake_coverage",
    "evaluate_intake_readiness",
    "generate_hypotheses",
    "get_patient",
    "initial_state",
    "list_sessions_for_patient",
    "load_repository",
    "pattern_tag_evidence",
    "pattern_tag_evidence_items",
    "rank_patterns_for_profile",
    "save_repository",
    "select_adaptive_question",
    "select_follow_up_questions",
    "select_highest_information_gain",
    "select_next_clarification_question",
    "score_pattern_fit",
    "split_transcript_to_statements",
    "suggest_next_questions",
    "statement_to_evidence",
    "statements_to_evidence",
    "transcribe_audio_mock",
    "update_coverage_from_signals",
]
