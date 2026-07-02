from niros.evidence import (
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
    statement_to_evidence,
    statements_to_evidence,
)
from niros.models import SupportedLanguage
from niros.statements import Statement, split_transcript_to_statements
from niros.transcript import Transcript


def test_statement_to_evidence_example():
    statement = Statement(
        session_id="session-001",
        text="I avoid conflict.",
        sequence=1,
        language=SupportedLanguage.ENGLISH,
    )

    evidence = statement_to_evidence(statement)

    assert evidence.evidence_type == EvidenceType.RAW_STATEMENT
    assert evidence.source == EvidenceSource.USER_STATEMENT
    assert evidence.canonical_id is None
    assert evidence.raw_text == "I avoid conflict."
    assert evidence.confidence == 1.0
    assert evidence.session_id == "session-001"
    assert evidence.statement_id == "session-001:stmt:1"
    assert evidence.language == SupportedLanguage.ENGLISH
    assert evidence.id == "session-001:evidence:1"


def test_statements_to_evidence_preserves_language():
    statements = [
        Statement(
            session_id="session-001",
            text="Me siento agotado.",
            sequence=0,
            language=SupportedLanguage.SPANISH,
        ),
        Statement(
            session_id="session-001",
            text="No duermo bien.",
            sequence=1,
            language=SupportedLanguage.SPANISH,
        ),
    ]

    evidence_items = statements_to_evidence(statements)

    assert len(evidence_items) == 2
    assert all(item.language == SupportedLanguage.SPANISH for item in evidence_items)
    assert [item.raw_text for item in evidence_items] == [
        "Me siento agotado.",
        "No duermo bien.",
    ]


def test_transcript_to_statements_to_evidence_pipeline():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I am afraid of disappointing people. I avoid conflict.",
        language=SupportedLanguage.ENGLISH,
    )

    statements = split_transcript_to_statements(transcript)
    evidence_items = statements_to_evidence(statements)

    assert len(evidence_items) == 2
    assert evidence_items[0].raw_text == "I am afraid of disappointing people."
    assert evidence_items[1].raw_text == "I avoid conflict."
    assert all(item.evidence_type == EvidenceType.RAW_STATEMENT for item in evidence_items)
    assert all(item.source == EvidenceSource.USER_STATEMENT for item in evidence_items)
    assert all(item.canonical_id is None for item in evidence_items)
    assert all(item.confidence == 1.0 for item in evidence_items)
