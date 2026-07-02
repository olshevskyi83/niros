from pathlib import Path

import pytest
import yaml

from niros.knowledge import KnowledgePattern, PatternLoader
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.questions import FollowUpQuestionSelector, select_follow_up_questions


def _pattern_tag(canonical_id: str, language: SupportedLanguage) -> PatternTag:
    return PatternTag(
        id="session-001:evidence:0:tag:fear_of_rejection:0",
        session_id="session-001",
        evidence_id="session-001:evidence:0",
        canonical_id=canonical_id,
        matched_text="example",
        confidence=1.0,
        language=language,
    )


def test_select_follow_up_questions_english():
    tag = _pattern_tag("fear_of_rejection", SupportedLanguage.ENGLISH)

    questions = select_follow_up_questions(tag)

    assert questions == [
        "What do you usually do when you feel someone may reject you?",
        "What signs make you think someone is pulling away?",
        "What would it mean about you if someone rejected you?",
    ]


def test_select_follow_up_questions_spanish():
    tag = _pattern_tag("fear_of_rejection", SupportedLanguage.SPANISH)

    questions = select_follow_up_questions(tag)

    assert len(questions) == 3
    assert questions[0] == "¿Qué sueles hacer cuando sientes que alguien puede rechazarte?"


def test_select_follow_up_questions_russian():
    tag = _pattern_tag("fear_of_rejection", SupportedLanguage.RUSSIAN)

    questions = select_follow_up_questions(tag)

    assert len(questions) == 3
    assert questions[0] == "Что вы обычно делаете, когда чувствуете, что вас могут отвергнуть?"


def test_select_follow_up_questions_unknown_canonical_id_returns_empty_list():
    tag = _pattern_tag("unknown_pattern", SupportedLanguage.ENGLISH)

    assert select_follow_up_questions(tag) == []


def test_select_follow_up_questions_missing_language_returns_empty_list(tmp_path: Path):
    pattern_data = {
        "canonical_id": "english_only_pattern",
        "name": "English Only Pattern",
        "domain": "relationships",
        "definition": "Test pattern.",
        "behavioral_description": "Test behavior.",
        "positive_evidence": ["Example evidence."],
        "negative_evidence": ["Counter evidence."],
        "typical_phrases": {"en": ["example phrase"]},
        "follow_up_questions": {"en": ["Example question?"]},
        "related_patterns": [],
        "confidence_rules": {"repeated_evidence": 0.15},
        "interview_priority": 1,
        "therapeutic_relevance": "Test relevance.",
    }
    pattern_path = tmp_path / "english_only_pattern.yaml"
    pattern_path.write_text(yaml.dump(pattern_data), encoding="utf-8")

    tag = _pattern_tag("english_only_pattern", SupportedLanguage.SPANISH)
    selector = FollowUpQuestionSelector(loader=PatternLoader(patterns_dir=tmp_path))

    assert selector.select(tag) == []
