from niros.consistency_engine import (
    AMBIGUITY,
    CONTRADICTION,
    EVOLVING_BELIEF,
    analyze_consistency,
    format_consistency_observations,
)
from niros.evidence_store import EvidenceStore
from niros.human_profile_report import build_human_profile_report_from_tags
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact


def _pattern_tag(canonical_id: str, matched_text: str) -> PatternTag:
    return PatternTag(
        id="tag-1",
        session_id="session-001",
        evidence_id="session-001:evidence:0",
        canonical_id=canonical_id,
        matched_text=matched_text,
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _fact(
    attribute: str,
    value: str,
    *,
    confidence: float = 0.9,
    evidence: str = "sample evidence",
    category: str = "relationships",
) -> SemanticFact:
    return SemanticFact(
        category=category,
        attribute=attribute,
        value=value,
        confidence=confidence,
        evidence=evidence,
    )


def _store(*facts: tuple[SemanticFact, int]) -> EvidenceStore:
    store = EvidenceStore()
    for fact, sequence in facts:
        store.add_fact(fact, sequence=sequence)
    return store


def test_contradiction_detection():
    store = _store(
        (_fact("trust", "low", evidence="I do not trust people easily."), 0),
        (_fact("trust", "high", evidence="I trust my close friends completely."), 1),
    )

    issues = analyze_consistency(store)

    assert len(issues) == 1
    assert issues[0].type == CONTRADICTION
    assert issues[0].attribute == "trust"
    assert {issues[0].old_value, issues[0].new_value} == {"low", "high"}
    assert issues[0].severity == "high"


def test_ambiguity_detection():
    store = _store(
        (
            _fact(
                "self_worth",
                "unclear",
                confidence=0.5,
                evidence="Sometimes I feel okay, sometimes not.",
                category="self_concept",
            ),
            0,
        ),
        (
            _fact(
                "self_worth",
                "low",
                confidence=0.5,
                evidence="I often feel not good enough.",
                category="self_concept",
            ),
            1,
        ),
    )

    issues = analyze_consistency(store)

    assert len(issues) == 1
    assert issues[0].type == AMBIGUITY
    assert issues[0].attribute == "self_worth"
    assert issues[0].severity == "medium"


def test_evolving_belief_detection():
    store = _store(
        (_fact("trust", "high", evidence="I used to trust people quickly."), 0),
        (_fact("trust", "high", evidence="I believed people were mostly good."), 1),
        (_fact("trust", "low", evidence="Now I keep my guard up."), 2),
        (_fact("trust", "low", evidence="I rarely open up anymore."), 3),
    )

    issues = analyze_consistency(store)

    assert len(issues) == 1
    assert issues[0].type == EVOLVING_BELIEF
    assert issues[0].attribute == "trust"
    assert issues[0].old_value == "high"
    assert issues[0].new_value == "low"
    assert issues[0].severity == "low"


def test_repeated_identical_evidence_produces_no_issue():
    store = _store(
        (_fact("trust", "low", evidence="I do not trust people easily."), 0),
        (_fact("trust", "low", evidence="I stay guarded around others."), 1),
        (_fact("trust", "low", evidence="Trust has to be earned slowly."), 2),
    )

    issues = analyze_consistency(store)

    assert issues == []


def test_deterministic_output():
    store = _store(
        (_fact("trust", "low"), 0),
        (_fact("trust", "high"), 1),
        (_fact("self_worth", "unclear", confidence=0.5, category="self_concept"), 2),
        (_fact("self_worth", "low", confidence=0.5, category="self_concept"), 3),
    )

    first = analyze_consistency(store)
    second = analyze_consistency(store)

    assert first == second


def test_format_consistency_observations():
    store = _store(
        (_fact("trust", "high", evidence="I used to trust people quickly."), 0),
        (_fact("trust", "high", evidence="I believed people were mostly good."), 1),
        (_fact("trust", "low", evidence="Now I keep my guard up."), 2),
        (_fact("trust", "low", evidence="I rarely open up anymore."), 3),
    )

    observations = format_consistency_observations(analyze_consistency(store))

    assert observations == ["Trust statements became more negative during the interview."]


def test_human_profile_report_includes_consistency_observations():
    store = _store(
        (_fact("trust", "low"), 0),
        (_fact("trust", "high"), 1),
    )

    report = build_human_profile_report_from_tags(
        [
            _pattern_tag(
                "trust_difficulty",
                "I do not trust people easily.",
            )
        ],
        evidence_store=store,
    )

    assert any("inconsistent" in line.lower() for line in report.consistency_observations)
