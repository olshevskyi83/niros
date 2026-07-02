from pathlib import Path

import pytest
import yaml

from niros.evidence import statement_to_evidence
from niros.knowledge import PatternLoader
from niros.models import SupportedLanguage
from niros.patterns import PatternTagger
from niros.statements import Statement


def _evidence(raw_text: str, language: SupportedLanguage) -> object:
    statement = Statement(
        session_id="session-001",
        text=raw_text,
        sequence=0,
        language=language,
    )
    return statement_to_evidence(statement)


def test_yaml_matcher_english_match():
    evidence = _evidence(
        "Sometimes I worry people will stop liking me.",
        SupportedLanguage.ENGLISH,
    )

    tags = PatternTagger().tag(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == "fear_of_rejection"
    assert tags[0].matched_text == "I worry people will stop liking me."


def test_yaml_matcher_spanish_match():
    evidence = _evidence(
        "Me preocupa que dejen de quererme.",
        SupportedLanguage.SPANISH,
    )

    tags = PatternTagger().tag(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == "fear_of_rejection"


def test_yaml_matcher_russian_match():
    evidence = _evidence(
        "Мне тревожно, когда кто-то отдаляется.",
        SupportedLanguage.RUSSIAN,
    )

    tags = PatternTagger().tag(evidence)

    assert len(tags) == 1
    assert tags[0].canonical_id == "fear_of_rejection"


def test_yaml_matcher_no_match_returns_empty_list():
    evidence = _evidence("I like music.", SupportedLanguage.ENGLISH)

    assert PatternTagger().tag(evidence) == []


def test_yaml_matcher_missing_language_phrases_returns_empty_list(tmp_path: Path):
    pattern_data = {
        "canonical_id": "english_only_pattern",
        "name": "English Only Pattern",
        "domain": "relationships",
        "definition": "Test pattern.",
        "behavioral_description": "Test behavior.",
        "positive_evidence": ["Example evidence."],
        "negative_evidence": ["Counter evidence."],
        "typical_phrases": {
            "en": ["unique english only phrase"],
        },
        "follow_up_questions": {
            "en": ["Example question?"],
        },
        "related_patterns": [],
        "confidence_rules": {"repeated_evidence": 0.15},
        "interview_priority": 1,
        "therapeutic_relevance": "Test relevance.",
    }
    pattern_path = tmp_path / "english_only_pattern.yaml"
    pattern_path.write_text(yaml.dump(pattern_data), encoding="utf-8")

    evidence = _evidence("unique english only phrase", SupportedLanguage.SPANISH)
    tags = PatternTagger(loader=PatternLoader(patterns_dir=tmp_path)).tag(evidence)

    assert tags == []
