from pydantic import BaseModel

from niros.evidence import EvidenceItem
from niros.knowledge import KnowledgePattern, PatternLoader
from niros.models import SupportedLanguage


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
    def __init__(self, loader: PatternLoader | None = None) -> None:
        self.loader = loader or PatternLoader()
        self._patterns: list[KnowledgePattern] | None = None

    def tag(self, evidence: EvidenceItem) -> list[PatternTag]:
        phrases = _phrases_for_language(evidence.language)
        if phrases is None:
            return []

        lowered_text = evidence.raw_text.lower()
        tags: list[PatternTag] = []

        for pattern in self._load_patterns():
            language_phrases = pattern.typical_phrases.get(phrases)
            if not language_phrases:
                continue

            matched_phrase = _first_matching_phrase(language_phrases, lowered_text)
            if matched_phrase is None:
                continue

            tags.append(
                PatternTag(
                    id=_pattern_tag_id(evidence, pattern.canonical_id, len(tags)),
                    session_id=evidence.session_id,
                    evidence_id=evidence.id,
                    canonical_id=pattern.canonical_id,
                    matched_text=matched_phrase,
                    confidence=1.0,
                    language=evidence.language,
                )
            )

        return tags

    def _load_patterns(self) -> list[KnowledgePattern]:
        if self._patterns is None:
            self._patterns = self.loader.load_all()
        return self._patterns


def _phrases_for_language(language: SupportedLanguage) -> str | None:
    return language.value


def _first_matching_phrase(phrases: list[str], lowered_text: str) -> str | None:
    for phrase in phrases:
        if phrase.lower() in lowered_text:
            return phrase
    return None


def _pattern_tag_id(evidence: EvidenceItem, canonical_id: str, index: int) -> str:
    return f"{evidence.id}:tag:{canonical_id}:{index}"
