from niros.knowledge import KnowledgePattern, PatternLoader
from niros.patterns import PatternTag


def select_follow_up_questions(
    tag: PatternTag,
    patterns: list[KnowledgePattern] | None = None,
    *,
    loader: PatternLoader | None = None,
) -> list[str]:
    return FollowUpQuestionSelector(patterns=patterns, loader=loader).select(tag)


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
