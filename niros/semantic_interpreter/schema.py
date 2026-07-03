from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from niros.semantic_interpreter.fact_vocabulary import (
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)
from niros.semantic_interpreter.facts import SemanticFact


class SemanticFactPayload(BaseModel):
    category: str
    attribute: str
    value: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {value!r}")
        return value

    @field_validator("attribute")
    @classmethod
    def validate_attribute(cls, value: str) -> str:
        if value not in VALID_ATTRIBUTES:
            raise ValueError(f"Invalid attribute: {value!r}")
        return value

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        if value not in VALID_VALUES:
            raise ValueError(f"Invalid value: {value!r}")
        return value

    def to_semantic_fact(self) -> SemanticFact:
        return SemanticFact(
            category=self.category,
            attribute=self.attribute,
            value=self.value,
            confidence=self.confidence,
            evidence=self.evidence,
        )


class SemanticExtractionPayload(BaseModel):
    facts: list[SemanticFactPayload]
    detected_language: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
