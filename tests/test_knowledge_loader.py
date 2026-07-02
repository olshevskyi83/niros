from pathlib import Path

import pytest

from niros.knowledge import DEFAULT_PATTERNS_DIR, KnowledgePattern, PatternLoader


def test_fear_of_rejection_loads_successfully():
    pattern = PatternLoader().load("fear_of_rejection")

    assert isinstance(pattern, KnowledgePattern)


def test_fear_of_rejection_canonical_id():
    pattern = PatternLoader().load("fear_of_rejection")

    assert pattern.canonical_id == "fear_of_rejection"


def test_fear_of_rejection_has_multilingual_phrases():
    pattern = PatternLoader().load("fear_of_rejection")

    assert "en" in pattern.typical_phrases
    assert "es" in pattern.typical_phrases
    assert "ru" in pattern.typical_phrases
    assert len(pattern.typical_phrases["en"]) >= 1
    assert len(pattern.typical_phrases["es"]) >= 1
    assert len(pattern.typical_phrases["ru"]) >= 1


def test_fear_of_rejection_has_multilingual_follow_up_questions():
    pattern = PatternLoader().load("fear_of_rejection")

    assert "en" in pattern.follow_up_questions
    assert "es" in pattern.follow_up_questions
    assert "ru" in pattern.follow_up_questions
    assert len(pattern.follow_up_questions["en"]) >= 1
    assert len(pattern.follow_up_questions["es"]) >= 1
    assert len(pattern.follow_up_questions["ru"]) >= 1


def test_missing_pattern_raises_file_not_found_error(tmp_path: Path):
    loader = PatternLoader(patterns_dir=tmp_path)

    with pytest.raises(FileNotFoundError, match="Knowledge pattern file not found"):
        loader.load("missing_pattern")


def test_default_patterns_dir_points_to_project_patterns():
    assert DEFAULT_PATTERNS_DIR == Path(__file__).resolve().parent.parent / "knowledge" / "patterns"
