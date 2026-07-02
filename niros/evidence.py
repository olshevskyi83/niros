from enum import Enum

from pydantic import BaseModel

from niros.models import SupportedLanguage
from niros.statements import Statement


class EvidenceType(str, Enum):
    RAW_STATEMENT = "raw_statement"


class EvidenceSource(str, Enum):
    USER_STATEMENT = "user_statement"


class EvidenceItem(BaseModel):
    id: str
    session_id: str
    statement_id: str
    evidence_type: EvidenceType
    source: EvidenceSource
    canonical_id: str | None = None
    raw_text: str
    confidence: float = 1.0
    language: SupportedLanguage


def statement_to_evidence(statement: Statement) -> EvidenceItem:
    statement_id = _statement_id(statement)
    return EvidenceItem(
        id=_evidence_id(statement),
        session_id=statement.session_id,
        statement_id=statement_id,
        evidence_type=EvidenceType.RAW_STATEMENT,
        source=EvidenceSource.USER_STATEMENT,
        canonical_id=None,
        raw_text=statement.text,
        confidence=1.0,
        language=statement.language,
    )


def statements_to_evidence(statements: list[Statement]) -> list[EvidenceItem]:
    return [statement_to_evidence(statement) for statement in statements]


def _statement_id(statement: Statement) -> str:
    return f"{statement.session_id}:stmt:{statement.sequence}"


def _evidence_id(statement: Statement) -> str:
    return f"{statement.session_id}:evidence:{statement.sequence}"
