from niros.hypotheses import HypothesisGenerator, HypothesisType, generate_hypotheses
from niros.models import SupportedLanguage
from niros.patterns import PatternTag


def _pattern_tag(
    tag_id: str,
    canonical_id: str,
    session_id: str = "session-001",
    language: SupportedLanguage = SupportedLanguage.ENGLISH,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id=session_id,
        evidence_id=f"{session_id}:evidence:0",
        canonical_id=canonical_id,
        matched_text="example",
        confidence=1.0,
        language=language,
    )


def test_generate_people_pleasing_hypothesis_when_both_patterns_present():
    tags = [
        _pattern_tag("tag-1", "avoidance_conflict"),
        _pattern_tag("tag-2", "fear_of_disappointing_others"),
    ]

    hypotheses = generate_hypotheses(tags)

    assert len(hypotheses) == 1
    hypothesis = hypotheses[0]
    assert hypothesis.canonical_id == "people_pleasing_pattern"
    assert hypothesis.hypothesis_type == HypothesisType.RELATIONAL_PATTERN
    assert hypothesis.confidence == 0.65
    assert hypothesis.supporting_pattern_ids == ["tag-1", "tag-2"]
    assert hypothesis.language == SupportedLanguage.ENGLISH


def test_generate_hypotheses_returns_empty_list_with_only_avoidance_conflict():
    tags = [_pattern_tag("tag-1", "avoidance_conflict")]

    assert generate_hypotheses(tags) == []


def test_generate_hypotheses_returns_empty_list_with_only_fear_pattern():
    tags = [_pattern_tag("tag-1", "fear_of_disappointing_others")]

    assert generate_hypotheses(tags) == []


def test_generate_hypotheses_returns_empty_list_with_no_tags():
    assert generate_hypotheses([]) == []


def test_hypothesis_generator_class():
    tags = [
        _pattern_tag("tag-1", "avoidance_conflict"),
        _pattern_tag("tag-2", "fear_of_disappointing_others"),
    ]

    hypotheses = HypothesisGenerator().generate(tags)

    assert len(hypotheses) == 1
    assert hypotheses[0].id == "session-001:hypothesis:people_pleasing_pattern"
