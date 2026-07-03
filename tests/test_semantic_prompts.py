from niros.semantic_interpreter.fact_vocabulary import (
    IDENTITY,
    SELF,
    UNCLEAR,
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)
from niros.semantic_interpreter.prompts import (
    build_semantic_extraction_system_prompt,
    build_semantic_extraction_user_prompt,
)


def test_system_prompt_contains_json_only_requirement():
    prompt = build_semantic_extraction_system_prompt()

    assert "valid JSON only" in prompt


def test_system_prompt_forbids_diagnosis():
    prompt = build_semantic_extraction_system_prompt()

    assert "You do not diagnose" in prompt


def test_system_prompt_forbids_pattern_detection():
    prompt = build_semantic_extraction_system_prompt()

    assert "You do not detect NIROS patterns" in prompt


def test_user_prompt_includes_input_text():
    user_text = "I do not really know who I am."

    prompt = build_semantic_extraction_user_prompt(user_text)

    assert user_text in prompt


def test_user_prompt_includes_vocabulary_values():
    prompt = build_semantic_extraction_user_prompt("example")

    assert SELF in prompt
    assert IDENTITY in prompt
    assert UNCLEAR in prompt
    for category in VALID_CATEGORIES:
        assert category in prompt
    for attribute in VALID_ATTRIBUTES:
        assert attribute in prompt
    for value in VALID_VALUES:
        assert value in prompt


def test_user_prompt_includes_required_json_keys():
    prompt = build_semantic_extraction_user_prompt("example")

    assert '"facts"' in prompt
    assert '"category"' in prompt
    assert '"attribute"' in prompt
    assert '"value"' in prompt
    assert '"confidence"' in prompt
    assert '"evidence"' in prompt
    assert '"detected_language"' in prompt
    assert '"warnings"' in prompt
