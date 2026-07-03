from niros.evidence import statement_to_evidence
from niros.patterns import PatternTagger
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_pattern_mapping import patterns_for_semantic_fact, semantic_fact_pattern_matches
from niros.statements import Statement
from niros.models import SupportedLanguage


def _fact(category: str, attribute: str, value: str, evidence: str) -> SemanticFact:
    return SemanticFact(
        category=category,
        attribute=attribute,
        value=value,
        confidence=0.9,
        evidence=evidence,
    )


def _detect(raw_text: str) -> set[str]:
    statement = Statement(
        session_id="session-clinical-precision",
        text=raw_text,
        sequence=0,
        language=SupportedLanguage.UKRAINIAN,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def test_depression_self_label_maps_to_self_reported_concern():
    text = "мені здається у мене депресія"
    detected_phrase = _detect(text)
    assert "self_reported_depression_concern" in detected_phrase
    assert "depressed_mood_signal" not in detected_phrase

    matches = semantic_fact_pattern_matches(
        [_fact("self", "clinical_label_self_report", "depression", text)]
    )
    assert {match.canonical_id for match in matches} == {"self_reported_depression_concern"}


def test_antidepressant_negative_experience_maps_to_medication_patterns():
    text = "мені призначили антидепресанти, проте від них я себе почував ще гірше"
    detected_phrase = _detect(text)
    assert detected_phrase.intersection(
        {"medication_history", "negative_medication_experience"}
    )
    assert "depressed_mood_signal" not in detected_phrase

    facts = [
        _fact("treatment", "medication_history", "present", "мені призначили антидепресанти"),
        _fact(
            "treatment",
            "negative_medication_experience",
            "present",
            "від них я себе почував ще гірше",
        ),
    ]
    matches = semantic_fact_pattern_matches(facts)
    assert {match.canonical_id for match in matches} == {
        "medication_history",
        "negative_medication_experience",
    }


def test_medication_history_alone_does_not_emit_depressed_mood_signal():
    fact = _fact("treatment", "medication_history", "present", "мені призначили антидепресанти")
    assert patterns_for_semantic_fact(fact) == ["medication_history"]

    matches = semantic_fact_pattern_matches([fact])
    assert "depressed_mood_signal" not in {match.canonical_id for match in matches}


def test_supported_symptoms_can_emit_low_mood_and_depressed_mood_signal():
    facts = [
        _fact("emotion", "reported_low_mood", "present", "настрій дуже низький"),
        _fact("body", "appetite_loss", "present", "їсти не хочеться"),
    ]
    matches = semantic_fact_pattern_matches(facts)
    detected = {match.canonical_id for match in matches}

    assert "low_mood_signal" in detected
    assert "appetite_loss_signal" in detected
    assert "depressed_mood_signal" in detected


def test_reported_low_mood_alone_emits_low_mood_signal_only():
    facts = [_fact("emotion", "reported_low_mood", "present", "настрій дуже низький")]
    matches = semantic_fact_pattern_matches(facts)
    detected = {match.canonical_id for match in matches}

    assert detected == {"low_mood_signal"}


def test_low_treatment_response_maps_to_signal():
    fact = _fact("treatment", "low_response", "present", "терапія не допомогла")
    assert patterns_for_semantic_fact(fact) == ["low_treatment_response_signal"]
