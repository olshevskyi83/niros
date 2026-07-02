from __future__ import annotations

MOCK_LLM_MAPPINGS: tuple[tuple[str, str], ...] = (
    ("мене тривожать погані сни", "I have disturbing dreams."),
    ("я не знаю хто я", "I do not really know who I am."),
    ("я не знаю кто я", "I do not really know who I am."),
    ("i cant understand me", "I do not really know who I am."),
    ("i can't understand me", "I do not really know who I am."),
    ("i do not understand myself", "I do not really know who I am."),
    ("я не розумію себе", "I do not really know who I am."),
    ("я себе не розумію", "I do not really know who I am."),
    ("я не понимаю себя", "I do not really know who I am."),
    ("no me entiendo", "I do not really know who I am."),
    ("я думаю що нічого не зможу", "I probably cannot do this."),
    ("siento que no soy suficiente", "I am unsure if I am good enough as a person."),
    ("i am feeling not alive", "I feel empty or undefined."),
    ("i feel not alive", "I feel empty or undefined."),
)

SUPPORTED_MODES = frozenset({"passthrough", "mock_llm"})


def normalize_user_input(raw_text: str, mode: str = "passthrough") -> str:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported normalizer mode: {mode}")

    stripped = raw_text.strip()
    if mode == "passthrough":
        return stripped
    return _mock_llm_interpret(stripped)


def _mock_llm_interpret(stripped: str) -> str:
    if not stripped:
        return ""

    lowered = stripped.lower()
    outputs: list[str] = []

    for source_phrase, english_statement in MOCK_LLM_MAPPINGS:
        if source_phrase.lower() in lowered:
            outputs.append(english_statement)

    if outputs:
        return " ".join(outputs)

    return stripped
