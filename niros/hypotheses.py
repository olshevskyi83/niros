from enum import Enum

from pydantic import BaseModel

from niros.models import SupportedLanguage
from niros.patterns import PatternTag

PEOPLE_PLEASING_PATTERNS = frozenset(
    {"avoidance_conflict", "fear_of_disappointing_others"}
)


class HypothesisType(str, Enum):
    RELATIONAL_PATTERN = "relational_pattern"


class Hypothesis(BaseModel):
    id: str
    session_id: str
    hypothesis_type: HypothesisType
    canonical_id: str
    supporting_pattern_ids: list[str]
    confidence: float
    language: SupportedLanguage


def generate_hypotheses(pattern_tags: list[PatternTag]) -> list[Hypothesis]:
    return HypothesisGenerator().generate(pattern_tags)


class HypothesisGenerator:
    def generate(self, pattern_tags: list[PatternTag]) -> list[Hypothesis]:
        tags_by_canonical_id = {
            tag.canonical_id: tag
            for tag in pattern_tags
            if tag.canonical_id in PEOPLE_PLEASING_PATTERNS
        }

        if PEOPLE_PLEASING_PATTERNS - tags_by_canonical_id.keys():
            return []

        supporting_tags = [tags_by_canonical_id[canonical_id] for canonical_id in sorted(PEOPLE_PLEASING_PATTERNS)]
        first_tag = supporting_tags[0]

        return [
            Hypothesis(
                id=f"{first_tag.session_id}:hypothesis:people_pleasing_pattern",
                session_id=first_tag.session_id,
                hypothesis_type=HypothesisType.RELATIONAL_PATTERN,
                canonical_id="people_pleasing_pattern",
                supporting_pattern_ids=[tag.id for tag in supporting_tags],
                confidence=0.65,
                language=first_tag.language,
            )
        ]
