from niros.evidence import statements_to_evidence
from niros.hypotheses import generate_hypotheses
from niros.interview_engine import BlueprintPhase, InterviewDecisionEngine
from niros.knowledge import PatternLoader
from niros.models import InterviewPhase, SupportedLanguage
from niros.patterns import pattern_tag_evidence_items
from niros.state_machine import advance, initial_state
from niros.statements import split_transcript_to_statements
from niros.transcript import Transcript

RAW_TEXT = "I worry people will stop liking me. I try to make everyone happy."
SESSION_ID = "session-e2e-001"


def test_end_to_end_mvp_pipeline_from_text_to_interview_decision():
    transcript = Transcript(
        session_id=SESSION_ID,
        raw_text=RAW_TEXT,
        language=SupportedLanguage.ENGLISH,
    )

    assert transcript.raw_text == RAW_TEXT
    assert transcript.language == SupportedLanguage.ENGLISH

    statements = split_transcript_to_statements(transcript)

    assert len(statements) == 2
    assert statements[0].text == "I worry people will stop liking me."
    assert statements[1].text == "I try to make everyone happy."

    evidence_items = statements_to_evidence(statements)

    assert len(evidence_items) == 2
    assert all(item.session_id == SESSION_ID for item in evidence_items)
    assert all(item.raw_text for item in evidence_items)

    pattern_tags = pattern_tag_evidence_items(evidence_items)

    assert len(pattern_tags) >= 1
    canonical_ids = {tag.canonical_id for tag in pattern_tags}
    assert "fear_of_rejection" in canonical_ids

    people_pleasing = PatternLoader().load("people_pleasing")
    people_pleasing_phrases = people_pleasing.typical_phrases["en"]
    if any(phrase.lower() in RAW_TEXT.lower() for phrase in people_pleasing_phrases):
        assert "people_pleasing" in canonical_ids

    hypotheses = generate_hypotheses(pattern_tags)

    interview_state = advance(initial_state(SESSION_ID), consent_granted=True)
    interview_state = interview_state.model_copy(
        update={
            "input_language": SupportedLanguage.ENGLISH,
            "turn_count": 0,
        }
    )
    assert interview_state.state == InterviewPhase.FREE_NARRATIVE

    decision = InterviewDecisionEngine().decide(
        interview_state,
        pattern_tags,
        hypotheses,
        BlueprintPhase.FREE_NARRATIVE,
    )

    assert decision.selected_question
    assert decision.reason
    assert decision.next_phase == BlueprintPhase.FREE_NARRATIVE
    assert decision.selected_pattern in canonical_ids
