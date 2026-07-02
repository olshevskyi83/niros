from pydantic import BaseModel

from niros.knowledge import KnowledgePattern, PatternLoader
from niros.models import SupportedLanguage
from niros.patterns import PatternTag

DIRECT_QUESTION_PRIORITY = 1.0


class QuestionSuggestion(BaseModel):
    source_pattern: str
    question: str
    language: SupportedLanguage
    reason: str
    priority: float


def select_follow_up_questions(
    tag: PatternTag,
    patterns: list[KnowledgePattern] | None = None,
    *,
    loader: PatternLoader | None = None,
) -> list[str]:
    return FollowUpQuestionSelector(patterns=patterns, loader=loader).select(tag)


def suggest_next_questions(
    tag: PatternTag,
    patterns: list[KnowledgePattern] | None = None,
    *,
    loader: PatternLoader | None = None,
) -> list[QuestionSuggestion]:
    return GraphQuestionSuggester(patterns=patterns, loader=loader).suggest(tag)


class FollowUpQuestionSelector:
    def __init__(
        self,
        patterns: list[KnowledgePattern] | None = None,
        loader: PatternLoader | None = None,
    ) -> None:
        self._patterns = patterns
        self._loader = loader or PatternLoader()

    def select(self, tag: PatternTag) -> list[str]:
        pattern = self._find_pattern(tag.canonical_id)
        if pattern is None:
            return []

        questions = pattern.follow_up_questions.get(tag.language.value)
        if not questions:
            return []

        return list(questions)

    def _find_pattern(self, canonical_id: str) -> KnowledgePattern | None:
        for pattern in self._load_patterns():
            if pattern.canonical_id == canonical_id:
                return pattern
        return None

    def _load_patterns(self) -> list[KnowledgePattern]:
        if self._patterns is not None:
            return self._patterns
        return self._loader.load_all()


class GraphQuestionSuggester:
    def __init__(
        self,
        patterns: list[KnowledgePattern] | None = None,
        loader: PatternLoader | None = None,
    ) -> None:
        self._patterns = patterns
        self._loader = loader or PatternLoader()

    def suggest(self, tag: PatternTag) -> list[QuestionSuggestion]:
        patterns_by_id = {
            pattern.canonical_id: pattern for pattern in self._load_patterns()
        }
        source_pattern = patterns_by_id.get(tag.canonical_id)
        if source_pattern is None:
            return []

        language_key = tag.language.value
        suggestions: list[QuestionSuggestion] = []

        for question in source_pattern.follow_up_questions.get(language_key, []):
            suggestions.append(
                QuestionSuggestion(
                    source_pattern=source_pattern.canonical_id,
                    question=question,
                    language=tag.language,
                    reason="matched_pattern",
                    priority=DIRECT_QUESTION_PRIORITY,
                )
            )

        for relationship in sorted(
            source_pattern.relationships,
            key=lambda relationship: relationship.weight,
            reverse=True,
        ):
            related_pattern = patterns_by_id.get(relationship.target_pattern)
            if related_pattern is None:
                continue

            related_questions = related_pattern.follow_up_questions.get(language_key)
            if not related_questions:
                continue

            reason = f"relationship:{relationship.relation_type.value}"
            for question in related_questions:
                suggestions.append(
                    QuestionSuggestion(
                        source_pattern=related_pattern.canonical_id,
                        question=question,
                        language=tag.language,
                        reason=reason,
                        priority=relationship.weight,
                    )
                )

        return sorted(suggestions, key=lambda suggestion: suggestion.priority, reverse=True)

    def _load_patterns(self) -> list[KnowledgePattern]:
        if self._patterns is not None:
            return self._patterns
        return self._loader.load_all()
