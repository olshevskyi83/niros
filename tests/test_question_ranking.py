from niros.hypotheses import Hypothesis, HypothesisType
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.question_ranking import QuestionRankingEngine, format_ranking_debug
from niros.questions import QuestionSuggestion


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str = "tag-1",
    sequence: int = 0,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-001",
        evidence_id=f"session-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text="example",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _candidate(
    question: str,
    *,
    source_pattern: str = "fear_of_rejection",
    reason: str = "matched_pattern",
    priority: float = 1.0,
) -> QuestionSuggestion:
    return QuestionSuggestion(
        source_pattern=source_pattern,
        question=question,
        language=SupportedLanguage.ENGLISH,
        reason=reason,
        priority=priority,
    )


def test_questions_are_ranked_deterministically():
    ranker = QuestionRankingEngine()
    candidates = [
        _candidate("Question B"),
        _candidate("Question A"),
        _candidate("Question C"),
    ]

    first = ranker.rank(candidates, pattern_tags=[_pattern_tag("fear_of_rejection")], hypotheses=[])
    second = ranker.rank(candidates, pattern_tags=[_pattern_tag("fear_of_rejection")], hypotheses=[])

    assert [item.question for item in first] == [item.question for item in second]
    assert first[0].question == "Question B"


def test_already_answered_topics_lose_priority():
    ranker = QuestionRankingEngine()
    candidates = [
        _candidate("Fresh topic question?", source_pattern="attachment_anxiety"),
        _candidate("Repeat topic question?", source_pattern="fear_of_rejection"),
    ]
    pattern_tags = [
        _pattern_tag("fear_of_rejection", tag_id="tag-1", sequence=0),
        _pattern_tag("fear_of_rejection", tag_id="tag-2", sequence=1),
        _pattern_tag("fear_of_rejection", tag_id="tag-3", sequence=2),
    ]

    ranked = ranker.rank(
        candidates,
        pattern_tags=pattern_tags,
        hypotheses=[],
        answered_questions=["Repeat topic question?"],
    )

    assert ranked[0].question == "Fresh topic question?"
    assert ranked[-1].question == "Repeat topic question?"
    assert ranked[-1].score.novelty == 0.0
    assert ranked[0].score.novelty > ranked[1].score.novelty


def test_unresolved_hypotheses_increase_priority():
    ranker = QuestionRankingEngine()
    candidates = [
        _candidate(
            "What usually happens for you when you worry someone might be upset with you?",
            source_pattern="people_pleasing",
            reason="relationship:often_leads_to",
            priority=0.82,
        ),
        _candidate(
            "What signs make you think someone is pulling away?",
            source_pattern="fear_of_rejection",
        ),
    ]
    hypotheses = [
        Hypothesis(
            id="session-001:hypothesis:people_pleasing_pattern",
            session_id="session-001",
            hypothesis_type=HypothesisType.RELATIONAL_PATTERN,
            canonical_id="people_pleasing_pattern",
            supporting_pattern_ids=["tag-1"],
            confidence=0.65,
            language=SupportedLanguage.ENGLISH,
        )
    ]

    ranked = ranker.rank(
        candidates,
        pattern_tags=[_pattern_tag("fear_of_rejection")],
        hypotheses=hypotheses,
    )

    assert ranked[0].source_pattern == "people_pleasing"
    assert ranked[0].score.evidence_gap > ranked[1].score.evidence_gap


def test_graph_neighbor_questions_receive_bonus():
    ranker = QuestionRankingEngine()
    candidates = [
        _candidate(
            "Related graph question?",
            source_pattern="people_pleasing",
            reason="relationship:often_leads_to",
            priority=0.82,
        ),
        _candidate("Direct question?", source_pattern="fear_of_rejection"),
    ]

    ranked = ranker.rank(
        candidates,
        pattern_tags=[_pattern_tag("fear_of_rejection")],
        hypotheses=[],
    )

    graph_question = next(item for item in ranked if item.source_pattern == "people_pleasing")
    direct_question = next(item for item in ranked if item.source_pattern == "fear_of_rejection")

    assert graph_question.score.graph_priority == 0.82
    assert direct_question.score.graph_priority == 1.0


def test_ties_remain_stable():
    ranker = QuestionRankingEngine()
    candidates = [
        _candidate("Alpha question?", source_pattern="fear_of_rejection"),
        _candidate("Beta question?", source_pattern="fear_of_rejection"),
        _candidate("Gamma question?", source_pattern="fear_of_rejection"),
    ]

    ranked = ranker.rank(
        candidates,
        pattern_tags=[_pattern_tag("fear_of_rejection")],
        hypotheses=[],
    )

    assert [item.question for item in ranked] == [
        "Alpha question?",
        "Beta question?",
        "Gamma question?",
    ]
    assert ranked[0].score.total_score == ranked[1].score.total_score


def test_debug_output_includes_question_score_and_reason():
    ranker = QuestionRankingEngine()
    ranked = ranker.rank(
        [_candidate("Example question?")],
        pattern_tags=[_pattern_tag("fear_of_rejection")],
        hypotheses=[],
    )

    rendered = format_ranking_debug(ranked)

    assert "Question: Example question?" in rendered
    assert "Score:" in rendered
    assert "Reason:" in rendered
    assert "information_gain=" in rendered
