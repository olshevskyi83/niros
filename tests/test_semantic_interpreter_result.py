from niros.semantic_interpreter.factory import get_semantic_interpreter


def test_interpret_result_contains_raw_text():
    interpreter = get_semantic_interpreter("mock")
    raw_text = "я не розумію себе"

    result = interpreter.interpret_result(raw_text)

    assert result.raw_text == raw_text


def test_interpret_result_contains_canonical_statements():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("я не розумію себе")

    assert result.canonical_statements == ["I do not really know who I am."]


def test_interpret_result_provider_is_mock():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("я не розумію себе")

    assert result.provider == "mock"


def test_interpret_result_mapped_input_confidence_is_one():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("я не розумію себе")

    assert result.confidence == 1.0


def test_interpret_result_unmapped_input_preserves_original_statement():
    interpreter = get_semantic_interpreter("mock")
    raw_text = "  unmapped phrase  "

    result = interpreter.interpret_result(raw_text)

    assert result.canonical_statements == ["unmapped phrase"]
    assert result.confidence is None


def test_interpret_result_warnings_default_to_empty_list():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("я не розумію себе")

    assert result.warnings == []


def test_interpret_result_contains_facts():
    interpreter = get_semantic_interpreter("mock")

    result = interpreter.interpret_result("я не розумію себе")

    assert len(result.facts) == 1
    assert result.facts[0].category == "self"
    assert result.facts[0].attribute == "identity"
