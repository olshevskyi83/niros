from pathlib import Path

import yaml
from pydantic import BaseModel

DEFAULT_PATTERNS_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "patterns"


class KnowledgePattern(BaseModel):
    canonical_id: str
    name: str
    domain: str
    definition: str
    behavioral_description: str
    positive_evidence: list[str]
    negative_evidence: list[str]
    typical_phrases: dict[str, list[str]]
    follow_up_questions: dict[str, list[str]]
    related_patterns: list[str]
    confidence_rules: dict[str, float]
    interview_priority: int
    therapeutic_relevance: str


class PatternLoader:
    def __init__(self, patterns_dir: Path | None = None) -> None:
        self.patterns_dir = patterns_dir or DEFAULT_PATTERNS_DIR

    def load(self, canonical_id: str) -> KnowledgePattern:
        path = self.patterns_dir / f"{canonical_id}.yaml"
        if not path.is_file():
            raise FileNotFoundError(f"Knowledge pattern file not found: {path}")

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return KnowledgePattern.model_validate(data)

    def load_all(self) -> list[KnowledgePattern]:
        patterns: list[KnowledgePattern] = []
        for path in sorted(self.patterns_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            patterns.append(KnowledgePattern.model_validate(data))
        return patterns
