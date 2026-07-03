from __future__ import annotations

from niros.semantic_interpreter.base import SemanticInterpreter, SemanticInterpretationResult
from niros.semantic_interpreter.facts import SemanticFact

MOCK_MAPPINGS: tuple[tuple[str, str], ...] = (
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

MOCK_STATEMENT_FACTS: dict[str, tuple[str, str, str]] = {
    "I do not really know who I am.": ("self", "identity", "unclear"),
    "I probably cannot do this.": ("agency", "self_efficacy", "low"),
    "I am unsure if I am good enough as a person.": ("self", "self_worth", "unstable"),
    "I feel empty or undefined.": ("self", "identity", "unclear"),
}


def _facts_for_statements(statements: list[str]) -> list[SemanticFact]:
    facts: list[SemanticFact] = []

    for statement in statements:
        mapping = MOCK_STATEMENT_FACTS.get(statement)
        if mapping is None:
            continue

        category, attribute, value = mapping
        facts.append(
            SemanticFact(
                category=category,
                attribute=attribute,
                value=value,
                confidence=1.0,
                evidence=statement,
            )
        )

    return facts


class MockSemanticInterpreter(SemanticInterpreter):
    def interpret(self, raw_text: str) -> list[str]:
        stripped = raw_text.strip()
        if not stripped:
            return []

        lowered = stripped.lower()
        outputs: list[str] = []

        for source_phrase, english_statement in MOCK_MAPPINGS:
            if source_phrase.lower() in lowered:
                outputs.append(english_statement)

        if outputs:
            return outputs

        return [stripped]

    def interpret_result(self, raw_text: str) -> SemanticInterpretationResult:
        stripped = raw_text.strip()
        statements = self.interpret(raw_text)
        mapped = bool(stripped) and statements != [stripped]

        return SemanticInterpretationResult(
            raw_text=raw_text,
            canonical_statements=statements,
            facts=_facts_for_statements(statements),
            provider="mock",
            confidence=1.0 if mapped else None,
        )
