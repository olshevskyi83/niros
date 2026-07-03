import pytest

from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.factory import get_semantic_interpreter
from niros.semantic_interpreter.mock import MockSemanticInterpreter
from niros.semantic_interpreter.openai_provider import OpenAISemanticInterpreter


def test_default_provider_is_mock():
    interpreter = get_semantic_interpreter()

    assert isinstance(interpreter, MockSemanticInterpreter)


def test_get_semantic_interpreter_returns_mock_provider():
    interpreter = get_semantic_interpreter("mock")

    assert isinstance(interpreter, MockSemanticInterpreter)


def test_get_semantic_interpreter_returns_openai_provider():
    interpreter = get_semantic_interpreter("openai")

    assert isinstance(interpreter, OpenAISemanticInterpreter)


def test_openai_factory_reads_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-key")

    interpreter = get_semantic_interpreter("openai")

    assert isinstance(interpreter, OpenAISemanticInterpreter)
    assert interpreter.api_key == "test-secret-key"


def test_missing_openai_api_key_does_not_crash(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    interpreter = get_semantic_interpreter("openai")
    result = interpreter.interpret("I do not really know who I am.")

    assert isinstance(result, SemanticInterpretationResult)
    assert result.facts == []
    assert result.warnings == ["openai_client_unavailable"]


def test_get_semantic_interpreter_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unsupported semantic interpreter provider"):
        get_semantic_interpreter("anthropic")


def test_openai_interpret_returns_stub_result(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    interpreter = get_semantic_interpreter("openai")

    result = interpreter.interpret("example")

    assert isinstance(result, SemanticInterpretationResult)
    assert result.warnings == ["openai_client_unavailable"]


def test_openai_interpret_result_delegates_to_interpret(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    interpreter = get_semantic_interpreter("openai")

    result = interpreter.interpret_result("example")

    assert isinstance(result, SemanticInterpretationResult)
    assert result.warnings == ["openai_client_unavailable"]


def test_mock_semantic_interpreter_returns_canonical_statements():
    interpreter = get_semantic_interpreter("mock")

    assert interpreter.interpret("я не розумію себе") == [
        "I do not really know who I am.",
    ]


def test_mock_semantic_interpreter_returns_original_when_unmapped():
    interpreter = get_semantic_interpreter("mock")

    assert interpreter.interpret("  unmapped phrase  ") == ["unmapped phrase"]
