from niros.evidence import statement_to_evidence
from niros.models import SupportedLanguage
from niros.patterns import PatternTagger
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_pattern_mapping import patterns_for_semantic_fact, semantic_fact_pattern_matches
from niros.statements import Statement


def _detect(raw_text: str, language: SupportedLanguage) -> set[str]:
    statement = Statement(
        session_id="session-grief-001",
        text=raw_text,
        sequence=0,
        language=language,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def test_uk_bereavement_phrase_detects_loss_patterns():
    text = "я думаю це через смерть близької людини"
    detected = _detect(text, SupportedLanguage.UKRAINIAN)

    assert "bereavement_context" in detected
    assert "loss_related_distress" in detected


def test_uk_grief_phrase_detects_grief_signal():
    assert "grief_signal" in _detect("я не можу пережити втрату", SupportedLanguage.UKRAINIAN)


def test_en_bereavement_examples():
    cases = [
        "death of someone close",
        "I lost someone close to me",
        "after my mother died",
        "I cannot process the loss",
        "things got worse after the funeral",
    ]
    for text in cases:
        detected = _detect(text, SupportedLanguage.ENGLISH)
        assert detected.intersection({"bereavement_context", "loss_related_distress", "grief_signal"})


def test_ru_bereavement_examples():
    cases = [
        "смерть близкого человека",
        "я потерял близкого человека",
        "после смерти мамы",
        "я не могу пережить потерю",
        "после похорон мне стало хуже",
    ]
    for text in cases:
        detected = _detect(text, SupportedLanguage.RUSSIAN)
        assert detected.intersection({"bereavement_context", "loss_related_distress", "grief_signal"})


def test_es_bereavement_examples():
    cases = [
        "la muerte de una persona cercana",
        "perdí a alguien cercano",
        "después de la muerte de mi madre",
        "no puedo superar la pérdida",
        "después del funeral empeoré",
    ]
    for text in cases:
        detected = _detect(text, SupportedLanguage.SPANISH)
        assert detected.intersection({"bereavement_context", "loss_related_distress", "grief_signal"})


def test_neutral_sentence_does_not_false_positive():
    neutral_cases = [
        ("I like music.", SupportedLanguage.ENGLISH),
        ("Сьогодні я працюю над проектом.", SupportedLanguage.UKRAINIAN),
        ("Me gusta caminar por la mañana.", SupportedLanguage.SPANISH),
        ("Сегодня хорошая погода.", SupportedLanguage.RUSSIAN),
    ]
    grief_patterns = {"grief_signal", "bereavement_context", "loss_related_distress"}

    for text, language in neutral_cases:
        detected = _detect(text, language)
        assert detected.isdisjoint(grief_patterns)


def test_semantic_fact_mappings_for_grief_and_loss():
    facts = [
        SemanticFact(category="life_event", attribute="bereavement", value="present", evidence="death of someone close"),
        SemanticFact(category="life_event", attribute="loss", value="present", evidence="lost someone close"),
        SemanticFact(category="emotion", attribute="grief", value="present", evidence="I am grieving"),
        SemanticFact(
            category="emotion",
            attribute="loss_related_distress",
            value="present",
            evidence="things got worse after the funeral",
        ),
    ]

    for fact in facts:
        assert fact.is_valid() is True
        assert patterns_for_semantic_fact(fact)

    matches = semantic_fact_pattern_matches(facts)
    detected = {match.canonical_id for match in matches}
    assert "bereavement_context" in detected
    assert "grief_signal" in detected
    assert "loss_related_distress" in detected
