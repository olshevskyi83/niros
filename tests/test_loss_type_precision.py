from niros.evidence import statement_to_evidence
from niros.models import SupportedLanguage
from niros.patterns import PatternTagger
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_pattern_mapping import patterns_for_semantic_fact, semantic_fact_pattern_matches
from niros.statements import Statement


def _detect(raw_text: str, language: SupportedLanguage) -> set[str]:
    statement = Statement(
        session_id="session-loss-type",
        text=raw_text,
        sequence=0,
        language=language,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def test_uk_breakup_detects_relationship_breakup_not_bereavement():
    detected = _detect("я розійшовся з партнеркою", SupportedLanguage.UKRAINIAN)

    assert "relationship_breakup_context" in detected
    assert "bereavement_context" not in detected


def test_uk_abandonment_detects_abandonment_wound_signal():
    assert "abandonment_wound_signal" in _detect(
        "мене покинула дівчина",
        SupportedLanguage.UKRAINIAN,
    )


def test_uk_bereavement_death_phrase_detects_bereavement_context():
    assert "bereavement_context" in _detect(
        "після смерті близької людини",
        SupportedLanguage.UKRAINIAN,
    )


def test_en_breakup_examples():
    cases = [
        ("I broke up with my partner", {"relationship_breakup_context"}),
        ("my girlfriend left me", {"abandonment_wound_signal"}),
        ("after the breakup", {"relationship_breakup_context"}),
        ("we separated", {"relationship_breakup_context"}),
        ("my partner abandoned me", {"abandonment_wound_signal"}),
    ]
    for text, expected in cases:
        detected = _detect(text, SupportedLanguage.ENGLISH)
        assert detected.intersection(expected), text
        assert "bereavement_context" not in detected, text


def test_ru_breakup_examples():
    cases = [
        "я расстался с партнершей",
        "меня бросила девушка",
        "после расставания",
        "мы разошлись",
        "партнер меня оставил",
    ]
    for text in cases:
        detected = _detect(text, SupportedLanguage.RUSSIAN)
        assert detected.intersection(
            {
                "relationship_breakup_context",
                "attachment_loss_signal",
                "separation_distress",
                "abandonment_wound_signal",
            }
        ), text
        assert "bereavement_context" not in detected, text


def test_es_breakup_examples():
    cases = [
        "terminé con mi pareja",
        "mi pareja me dejó",
        "después de la ruptura",
        "nos separamos",
        "me abandonó mi pareja",
    ]
    for text in cases:
        detected = _detect(text, SupportedLanguage.SPANISH)
        assert detected.intersection(
            {
                "relationship_breakup_context",
                "attachment_loss_signal",
                "separation_distress",
                "abandonment_wound_signal",
            }
        ), text
        assert "bereavement_context" not in detected, text


def test_semantic_breakup_facts_do_not_emit_bereavement():
    facts = [
        SemanticFact(
            category="relationship",
            attribute="breakup",
            value="present",
            evidence="I broke up with my partner",
        ),
        SemanticFact(
            category="relationship",
            attribute="abandonment",
            value="present",
            evidence="my girlfriend left me",
        ),
    ]
    matches = semantic_fact_pattern_matches(facts)
    detected = {match.canonical_id for match in matches}
    assert "relationship_breakup_context" in detected
    assert "abandonment_wound_signal" in detected
    assert "bereavement_context" not in detected


def test_semantic_bereavement_fact_maps_only_to_bereavement_context():
    fact = SemanticFact(
        category="life_event",
        attribute="bereavement",
        value="present",
        evidence="after my mother died",
    )
    assert "bereavement_context" in patterns_for_semantic_fact(fact)


def test_semantic_loss_fact_does_not_map_to_bereavement_context():
    fact = SemanticFact(
        category="life_event",
        attribute="loss",
        value="present",
        evidence="I cannot process the loss",
    )
    patterns = patterns_for_semantic_fact(fact)
    assert "loss_related_distress" in patterns or "grief_signal" in patterns
    assert "bereavement_context" not in patterns
