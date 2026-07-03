from __future__ import annotations

from dataclasses import dataclass

from niros.semantic_interpreter.fact_vocabulary import (
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)


@dataclass
class SemanticFact:
    category: str
    attribute: str
    value: str
    confidence: float | None = None
    evidence: str | None = None

    def is_valid(self) -> bool:
        return (
            self.category in VALID_CATEGORIES
            and self.attribute in VALID_ATTRIBUTES
            and self.value in VALID_VALUES
        )
