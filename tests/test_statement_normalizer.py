import pytest

from niros.statement_normalizer import normalize_user_input


def test_passthrough_mode_english_psychological_statement_is_trimmed_only():
    raw_text = "  I feel worthless after criticism or rejection.  "

    assert (
        normalize_user_input(raw_text, mode="passthrough")
        == "I feel worthless after criticism or rejection."
    )


def test_passthrough_empty_string_returns_empty_string():
    assert normalize_user_input("", mode="passthrough") == ""


def test_passthrough_whitespace_only_string_returns_empty_string():
    assert normalize_user_input("   \n\t  ", mode="passthrough") == ""


def test_passthrough_non_english_text_passes_through_unchanged():
    raw_text = "Мене тривожать погані сни."

    assert normalize_user_input(raw_text, mode="passthrough") == raw_text


def test_mock_llm_ukrainian_identity_phrase():
    assert (
        normalize_user_input("Я не знаю хто я", mode="mock_llm")
        == "I do not really know who I am."
    )


def test_mock_llm_ukrainian_low_self_efficacy_phrase():
    assert (
        normalize_user_input("Я думаю що нічого не зможу", mode="mock_llm")
        == "I probably cannot do this."
    )


def test_mock_llm_russian_identity_phrase():
    assert (
        normalize_user_input("Я не знаю кто я", mode="mock_llm")
        == "I do not really know who I am."
    )


def test_mock_llm_spanish_self_worth_phrase():
    assert (
        normalize_user_input("Siento que no soy suficiente", mode="mock_llm")
        == "I am unsure if I am good enough as a person."
    )


def test_mock_llm_unknown_phrase_returns_original_text():
    raw_text = "  This phrase has no mapping.  "

    assert normalize_user_input(raw_text, mode="mock_llm") == "This phrase has no mapping."


def test_mock_llm_combined_phrases_return_multiple_english_statements():
    raw_text = "Я не знаю хто я. Я думаю що нічого не зможу."

    assert (
        normalize_user_input(raw_text, mode="mock_llm")
        == "I do not really know who I am. I probably cannot do this."
    )


def test_unsupported_mode_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported normalizer mode"):
        normalize_user_input("example", mode="real_llm")
