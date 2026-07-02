from pydantic import BaseModel

from niros.evidence import EvidenceItem
from niros.models import SupportedLanguage

PATTERN_RULES: dict[SupportedLanguage, list[tuple[str, str]]] = {
    SupportedLanguage.ENGLISH: [
        ("avoid conflict", "avoidance_conflict"),
        ("afraid of disappointing people", "fear_of_disappointing_others"),
    ],
    SupportedLanguage.SPANISH: [
        ("evito el conflicto", "avoidance_conflict"),
        ("miedo a decepcionar", "fear_of_disappointing_others"),
    ],
    SupportedLanguage.RUSSIAN: [
        ("избегаю конфликт", "avoidance_conflict"),
        ("боюсь разочаровать", "fear_of_disappointing_others"),
    ],
}


class PatternTag(BaseModel):
    id: str
    session_id: str
    evidence_id: str
    canonical_id: str
    matched_text: str
    confidence: float
    language: SupportedLanguage


def pattern_tag_evidence(evidence: EvidenceItem) -> list[PatternTag]:
    return PatternTagger().tag(evidence)


def pattern_tag_evidence_items(evidence_items: list[EvidenceItem]) -> list[PatternTag]:
    tagger = PatternTagger()
    tags: list[PatternTag] = []
    for evidence in evidence_items:
        tags.extend(tagger.tag(evidence))
    return tags


class PatternTagger:
    def tag(self, evidence: EvidenceItem) -> list[PatternTag]:
        rules = PATTERN_RULES.get(evidence.language, [])
        lowered_text = evidence.raw_text.lower()
        tags: list[PatternTag] = []

        for pattern, canonical_id in rules:
            if pattern not in lowered_text:
                continue

            tags.append(
                PatternTag(
                    id=_pattern_tag_id(evidence, canonical_id, len(tags)),
                    session_id=evidence.session_id,
                    evidence_id=evidence.id,
                    canonical_id=canonical_id,
                    matched_text=pattern,
                    confidence=1.0,
                    language=evidence.language,
                )
            )

        return tags


def _pattern_tag_id(evidence: EvidenceItem, canonical_id: str, index: int) -> str:
    return f"{evidence.id}:tag:{canonical_id}:{index}"
