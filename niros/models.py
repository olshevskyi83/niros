from enum import Enum

from pydantic import BaseModel, Field


class InterviewPhase(str, Enum):
    CONSENT = "consent"
    FREE_NARRATIVE = "free_narrative"
    DECLARED_PROBLEM = "declared_problem"
    DOMAIN_SCREENING = "domain_screening"
    HYPOTHESIS_CLARIFICATION = "hypothesis_clarification"
    RISK_SCREENING = "risk_screening"
    PROFILE_GENERATION = "profile_generation"
    HANDOFF = "handoff"


class SupportedLanguage(str, Enum):
    ENGLISH = "en"
    SPANISH = "es"
    RUSSIAN = "ru"


class IcaroLanguage(str, Enum):
    SPANISH = "es"
    QUECHUA = "qu"
    SHIPIBO = "shipibo"
    MAZATEC = "mazatec"


class InterviewState(BaseModel):
    session_id: str
    state: InterviewPhase
    completed_domains: list[str] = Field(default_factory=list)
    current_hypotheses: list[dict] = Field(default_factory=list)
    turn_count: int = 0
    missing_fields: list[str] = Field(default_factory=list)
    risk_status: str | None = None
    next_question_id: str | None = None
    input_language: SupportedLanguage | None = None
    icaro_language: IcaroLanguage | None = None
