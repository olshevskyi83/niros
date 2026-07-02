from pathlib import Path

import pytest
import yaml

from niros.knowledge import KnowledgePattern, PatternLoader, PatternRelationship, PatternRelationType
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.questions import GraphQuestionSuggester, suggest_next_questions


def _pattern_tag(canonical_id: str, language: SupportedLanguage) -> PatternTag:
    return PatternTag(
        id="session-001:evidence:0:tag:test:0",
        session_id="session-001",
        evidence_id="session-001:evidence:0",
        canonical_id=canonical_id,
        matched_text="example",
        confidence=1.0,
        language=language,
    )


def test_suggest_next_questions_returns_direct_questions():
    tag = _pattern_tag("fear_of_rejection", SupportedLanguage.ENGLISH)

    suggestions = suggest_next_questions(tag)

    direct = [suggestion for suggestion in suggestions if suggestion.reason == "matched_pattern"]
    assert len(direct) == 3
    assert all(suggestion.priority == 1.0 for suggestion in direct)
    assert all(suggestion.source_pattern == "fear_of_rejection" for suggestion in direct)
    assert direct[0].question.startswith("What do you usually do")


def test_suggest_next_questions_returns_related_pattern_questions():
    tag = _pattern_tag("fear_of_rejection", SupportedLanguage.ENGLISH)

    suggestions = suggest_next_questions(tag)

    related = [
        suggestion
        for suggestion in suggestions
        if suggestion.source_pattern == "people_pleasing"
    ]
    assert len(related) == 4
    assert all(suggestion.reason == "relationship:often_leads_to" for suggestion in related)


def test_suggest_next_questions_sorts_related_questions_by_weight():
    tag = _pattern_tag("fear_of_rejection", SupportedLanguage.ENGLISH)

    suggestions = suggest_next_questions(tag)

    related_priorities = [
        suggestion.priority
        for suggestion in suggestions
        if suggestion.reason.startswith("relationship:")
    ]
    assert related_priorities == sorted(related_priorities, reverse=True)
    assert related_priorities[0] == 0.82
    assert related_priorities[-1] == 0.68


def test_suggest_next_questions_skips_missing_related_pattern(tmp_path: Path):
    source_pattern = KnowledgePattern(
        canonical_id="source_pattern",
        name="Source Pattern",
        domain="relationships",
        definition="Source definition.",
        behavioral_description="Source behavior.",
        positive_evidence=["Evidence."],
        negative_evidence=["Counter evidence."],
        typical_phrases={"en": ["source phrase"]},
        follow_up_questions={"en": ["Direct question?"]},
        related_patterns=["missing_pattern"],
        relationships=[
            PatternRelationship(
                target_pattern="missing_pattern",
                relation_type=PatternRelationType.OFTEN_LEADS_TO,
                weight=0.9,
            )
        ],
        confidence_rules={"repeated_evidence": 0.15},
        interview_priority=1,
        therapeutic_relevance="Test relevance.",
    )
    (tmp_path / "source_pattern.yaml").write_text(
        yaml.dump(source_pattern.model_dump(mode="json")),
        encoding="utf-8",
    )

    tag = _pattern_tag("source_pattern", SupportedLanguage.ENGLISH)
    suggestions = GraphQuestionSuggester(loader=PatternLoader(patterns_dir=tmp_path)).suggest(tag)

    assert len(suggestions) == 1
    assert suggestions[0].reason == "matched_pattern"


def test_suggest_next_questions_skips_missing_language(tmp_path: Path):
    related_pattern = KnowledgePattern(
        canonical_id="related_pattern",
        name="Related Pattern",
        domain="relationships",
        definition="Related definition.",
        behavioral_description="Related behavior.",
        positive_evidence=["Evidence."],
        negative_evidence=["Counter evidence."],
        typical_phrases={"en": ["related phrase"]},
        follow_up_questions={"en": ["Related question?"]},
        related_patterns=[],
        confidence_rules={"repeated_evidence": 0.15},
        interview_priority=1,
        therapeutic_relevance="Test relevance.",
    )
    source_pattern = KnowledgePattern(
        canonical_id="source_pattern",
        name="Source Pattern",
        domain="relationships",
        definition="Source definition.",
        behavioral_description="Source behavior.",
        positive_evidence=["Evidence."],
        negative_evidence=["Counter evidence."],
        typical_phrases={"en": ["source phrase"], "es": ["frase fuente"]},
        follow_up_questions={"en": ["Direct question?"]},
        related_patterns=["related_pattern"],
        relationships=[
            PatternRelationship(
                target_pattern="related_pattern",
                relation_type=PatternRelationType.OFTEN_COEXISTS_WITH,
                weight=0.75,
            )
        ],
        confidence_rules={"repeated_evidence": 0.15},
        interview_priority=1,
        therapeutic_relevance="Test relevance.",
    )
    (tmp_path / "source_pattern.yaml").write_text(
        yaml.dump(source_pattern.model_dump(mode="json")),
        encoding="utf-8",
    )
    (tmp_path / "related_pattern.yaml").write_text(
        yaml.dump(related_pattern.model_dump(mode="json")),
        encoding="utf-8",
    )

    tag = _pattern_tag("source_pattern", SupportedLanguage.SPANISH)
    suggestions = GraphQuestionSuggester(loader=PatternLoader(patterns_dir=tmp_path)).suggest(tag)

    assert suggestions == []
