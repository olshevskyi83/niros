from __future__ import annotations

from dataclasses import dataclass

from niros.semantic_interpreter.facts import SemanticFact


@dataclass(frozen=True)
class SemanticEvidenceEntry:
    fact: SemanticFact
    sequence: int


class EvidenceStore:
    def __init__(self) -> None:
        self._entries: list[SemanticEvidenceEntry] = []

    def add_fact(self, fact: SemanticFact, sequence: int | None = None) -> None:
        next_sequence = len(self._entries) if sequence is None else sequence
        self._entries.append(SemanticEvidenceEntry(fact=fact, sequence=next_sequence))

    @property
    def entries(self) -> tuple[SemanticEvidenceEntry, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
