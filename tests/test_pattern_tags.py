import pytest

from niros.evidence import (
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
    statement_to_evidence,
    statements_to_evidence,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTagger, pattern_tag_evidence, pattern_tag_evidence_items
from niros.statements import Statement, split_transcript_to_statements
from niros.transcript import Transcript


def _evidence(raw_text: str, language: SupportedLanguage, sequence: int = 0) -> EvidenceItem:
    statement = Statement(
        session_id="session-001",
        text=raw_text,
        sequence=sequence,
        language=language,
    )
    return statement_to_evidence(statement)


def test_pattern_tag_avoidance_conflict():
    evidence = _evidence("I avoid conflict.", SupportedLanguage.ENGLISH)

    tags = pattern_tag_evidence(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == "avoidance_conflict"
    assert tags[0].matched_text == "avoid conflict"
    assert tags[0].confidence == 1.0
    assert tags[0].evidence_id == evidence.id
    assert tags[0].language == SupportedLanguage.ENGLISH


def test_pattern_tag_returns_empty_list_when_no_match():
    evidence = _evidence("I like music.", SupportedLanguage.ENGLISH)

    assert pattern_tag_evidence(evidence) == []


def test_pattern_tag_fear_of_disappointing_others_english():
    evidence = _evidence(
        "I am afraid of disappointing people.",
        SupportedLanguage.ENGLISH,
    )

    tags = pattern_tag_evidence(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == "fear_of_disappointing_others"


@pytest.mark.parametrize(
    ("raw_text", "canonical_id"),
    [
        ("Evito el conflicto siempre.", "avoidance_conflict"),
        ("Tengo miedo a decepcionar a mi familia.", "fear_of_disappointing_others"),
    ],
)
def test_pattern_tag_spanish_rules(raw_text, canonical_id):
    evidence = _evidence(raw_text, SupportedLanguage.SPANISH)

    tags = pattern_tag_evidence(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == canonical_id


@pytest.mark.parametrize(
    ("raw_text", "canonical_id"),
    [
        ("Я часто избегаю конфликт дома.", "avoidance_conflict"),
        ("Я боюсь разочаровать близких.", "fear_of_disappointing_others"),
    ],
)
def test_pattern_tag_russian_rules(raw_text, canonical_id):
    evidence = _evidence(raw_text, SupportedLanguage.RUSSIAN)

    tags = pattern_tag_evidence(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == canonical_id


def test_pattern_tagger_class():
    evidence = _evidence("I avoid conflict.", SupportedLanguage.ENGLISH)

    tags = PatternTagger().tag(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == "avoidance_conflict"


def test_transcript_to_pattern_tags_pipeline():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I am afraid of disappointing people. I avoid conflict.",
        language=SupportedLanguage.ENGLISH,
    )

    statements = split_transcript_to_statements(transcript)
    evidence_items = statements_to_evidence(statements)
    tags = pattern_tag_evidence_items(evidence_items)

    assert len(tags) == 2
    assert {tag.canonical_id for tag in tags} == {
        "fear_of_disappointing_others",
        "avoidance_conflict",
    }
