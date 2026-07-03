import json

from niros.semantic_interpreter.base import SemanticInterpretationResult
from niros.semantic_interpreter.facts import SemanticFact
from niros.semantic_interpreter.openai_provider import OpenAISemanticInterpreter


def _response_from_content(content: str):
    class FakeMessage:
        pass

    message = FakeMessage()
    message.content = content

    class FakeChoice:
        pass

    choice = FakeChoice()
    choice.message = message

    class FakeResponse:
        choices = [choice]

    return FakeResponse()


def _make_fake_client(*, content: str | None = None, error: Exception | None = None):
    class FakeCompletions:
        call_count = 0

        def create(self, **kwargs):
            FakeCompletions.call_count += 1
            if error is not None:
                raise error
            return _response_from_content(content or "")

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    return FakeClient()


def _make_fake_sequential_client(responses: list[str | Exception]):
    class FakeCompletions:
        call_count = 0

        def create(self, **kwargs):
            index = min(FakeCompletions.call_count, len(responses) - 1)
            response = responses[index]
            FakeCompletions.call_count += 1
            if isinstance(response, Exception):
                raise response
            return _response_from_content(response)

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    return FakeClient()


def _valid_extraction_json() -> str:
    return json.dumps(
        {
            "facts": [
                {
                    "category": "self",
                    "attribute": "identity",
                    "value": "unclear",
                    "confidence": 0.95,
                    "evidence": "I do not really know who I am.",
                }
            ],
            "detected_language": "en",
            "confidence": 0.95,
            "warnings": [],
        }
    )


def _schema_invalid_json() -> str:
    return json.dumps(
        {
            "facts": [
                {
                    "category": "experience",
                    "attribute": "identity",
                    "value": "unclear",
                }
            ],
            "detected_language": "en",
        }
    )


def test_provider_initializes_with_default_model():
    interpreter = OpenAISemanticInterpreter(client=None)

    assert interpreter.model == "gpt-4.1-mini"
    assert interpreter.temperature == 0.0


def test_provider_accepts_custom_model():
    interpreter = OpenAISemanticInterpreter(model="gpt-4.1", temperature=0.2, client=None)

    assert interpreter.model == "gpt-4.1"
    assert interpreter.temperature == 0.2


def test_default_max_retries_is_one():
    interpreter = OpenAISemanticInterpreter(client=None)

    assert interpreter.max_retries == 1


def test_negative_max_retries_becomes_zero():
    interpreter = OpenAISemanticInterpreter(client=None, max_retries=-3)

    assert interpreter.max_retries == 0


def test_build_messages_returns_system_and_user_messages():
    interpreter = OpenAISemanticInterpreter(client=None)
    text = "I do not really know who I am."

    messages = interpreter._build_messages(text)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[0]["content"]
    assert messages[1]["content"]


def test_user_message_contains_input_text():
    interpreter = OpenAISemanticInterpreter(client=None)
    text = "I do not really know who I am."

    messages = interpreter._build_messages(text)

    assert text in messages[1]["content"]


def test_empty_input_returns_empty_input_warning():
    interpreter = OpenAISemanticInterpreter(client=_make_fake_client(content=_valid_extraction_json()))

    result = interpreter.interpret("   ")

    assert result.facts == []
    assert result.canonical_statements == []
    assert result.warnings == ["empty_input"]


def test_missing_client_returns_openai_client_unavailable_warning():
    interpreter = OpenAISemanticInterpreter(client=None)

    result = interpreter.interpret("I do not really know who I am.")

    assert result.facts == []
    assert result.canonical_statements == []
    assert result.warnings == ["openai_client_unavailable"]


def test_valid_response_does_not_retry():
    client = _make_fake_sequential_client([_valid_extraction_json()])
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 1
    assert len(result.facts) == 1


def test_mocked_valid_openai_response_returns_parsed_semantic_fact():
    interpreter = OpenAISemanticInterpreter(client=_make_fake_client(content=_valid_extraction_json()))

    result = interpreter.interpret("I do not really know who I am.")

    assert result.facts == [
        SemanticFact(
            category="self",
            attribute="identity",
            value="unclear",
            confidence=0.95,
            evidence="I do not really know who I am.",
        )
    ]
    assert result.detected_language == "en"
    assert result.confidence == 0.95
    assert result.warnings == []


def test_invalid_json_then_valid_response_retries_and_succeeds():
    client = _make_fake_sequential_client(["{not valid json", _valid_extraction_json()])
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 2
    assert len(result.facts) == 1
    assert result.warnings == []


def test_schema_validation_failed_then_valid_response_retries_and_succeeds():
    client = _make_fake_sequential_client([_schema_invalid_json(), _valid_extraction_json()])
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 2
    assert len(result.facts) == 1
    assert result.warnings == []


def test_empty_response_then_valid_response_retries_and_succeeds():
    client = _make_fake_sequential_client(["", _valid_extraction_json()])
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 2
    assert len(result.facts) == 1
    assert result.warnings == []


def test_exception_then_valid_response_retries_and_succeeds():
    client = _make_fake_sequential_client(
        [RuntimeError("api failure"), _valid_extraction_json()],
    )
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 2
    assert len(result.facts) == 1
    assert result.warnings == []


def test_exception_exhausted_returns_openai_provider_error():
    client = _make_fake_sequential_client(
        [RuntimeError("api failure"), RuntimeError("api failure again")],
    )
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 2
    assert result.facts == []
    assert result.canonical_statements == []
    assert result.warnings == ["openai_provider_error"]


def test_mocked_invalid_json_response_returns_invalid_json_warning():
    client = _make_fake_sequential_client(["{not valid json", "{still not valid json"])
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 2
    assert result.facts == []
    assert result.warnings == ["invalid_json"]


def test_mocked_schema_invalid_response_returns_schema_validation_failed_warning():
    client = _make_fake_sequential_client([_schema_invalid_json(), _schema_invalid_json()])
    interpreter = OpenAISemanticInterpreter(client=client, max_retries=1)

    result = interpreter.interpret("I do not really know who I am.")

    assert client.chat.completions.call_count == 2
    assert result.facts == []
    assert result.warnings == ["schema_validation_failed"]


def test_mocked_openai_exception_returns_openai_provider_error_warning():
    interpreter = OpenAISemanticInterpreter(
        client=_make_fake_client(error=RuntimeError("api failure")),
        max_retries=0,
    )

    result = interpreter.interpret("I do not really know who I am.")

    assert result.facts == []
    assert result.canonical_statements == []
    assert result.warnings == ["openai_provider_error"]


def test_canonical_statements_remains_empty_list():
    interpreter = OpenAISemanticInterpreter(client=_make_fake_client(content=_valid_extraction_json()))

    result = interpreter.interpret("I do not really know who I am.")

    assert result.canonical_statements == []


def test_interpret_returns_semantic_interpretation_result():
    interpreter = OpenAISemanticInterpreter(client=None)

    result = interpreter.interpret("example")

    assert isinstance(result, SemanticInterpretationResult)
