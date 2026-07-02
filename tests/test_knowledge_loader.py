from pathlib import Path

import pytest
from pydantic import ValidationError

from niros.knowledge import (
    DEFAULT_PATTERNS_DIR,
    KnowledgePattern,
    PatternLoader,
    PatternRelationship,
    PatternRelationType,
)


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


def test_fear_of_rejection_relationships_load_correctly():
    pattern = PatternLoader().load("fear_of_rejection")

    assert len(pattern.relationships) == 4
    people_pleasing_link = next(
        relationship
        for relationship in pattern.relationships
        if relationship.target_pattern == "people_pleasing"
    )
    assert people_pleasing_link.relation_type == PatternRelationType.OFTEN_LEADS_TO
    assert people_pleasing_link.weight == 0.82


def test_people_pleasing_relationships_load_correctly():
    pattern = PatternLoader().load("people_pleasing")

    assert len(pattern.relationships) == 5
    assert any(
        relationship.target_pattern == "conflict_avoidance"
        and relationship.relation_type == PatternRelationType.OFTEN_COEXISTS_WITH
        for relationship in pattern.relationships
    )


def test_pattern_relationship_rejects_invalid_relation_type():
    with pytest.raises(ValidationError):
        PatternRelationship(
            target_pattern="people_pleasing",
            relation_type="invalid_relation",
            weight=0.5,
        )


def test_pattern_relationship_rejects_invalid_weight():
    with pytest.raises(ValidationError):
        PatternRelationship(
            target_pattern="people_pleasing",
            relation_type=PatternRelationType.OFTEN_LEADS_TO,
            weight=1.5,
        )


def test_loader_still_loads_patterns_without_relationships():
    patterns = PatternLoader().load_all()

    assert len(patterns) == 7
    fear_of_disappointing_others = next(
        pattern for pattern in patterns if pattern.canonical_id == "fear_of_disappointing_others"
    )
    assert fear_of_disappointing_others.relationships == []


@pytest.mark.parametrize(
    "canonical_id",
    [
        "conflict_avoidance",
        "attachment_anxiety",
        "boundary_difficulty",
        "trust_difficulty",
    ],
)
def test_new_relationship_patterns_load_successfully(canonical_id: str):
    pattern = PatternLoader().load(canonical_id)

    assert pattern.domain == "relationships"
    assert "en" in pattern.typical_phrases
    assert "es" in pattern.typical_phrases
    assert "ru" in pattern.typical_phrases
    assert len(pattern.relationships) >= 3

