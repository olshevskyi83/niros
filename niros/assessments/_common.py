from __future__ import annotations

from niros.assessment import AssessmentItem, AssessmentResponse, AssessmentResult, score_assessment

SUPPORTED_LANGUAGES = frozenset({"en", "uk", "ru", "es"})
SCALE_MIN = 1
SCALE_MAX = 5

FORBIDDEN_ITEM_PHRASES: tuple[str, ...] = (
    " diagnosis",
    "diagnose ",
    "disorder",
    "clinical",
    "patholog",
    "depressed",
    "depression",
    " cures ",
    " cure ",
    "psilocybin cures",
    "treatment for ",
    "eligibility",
)


def build_assessment_items(
    specs: tuple[dict[str, object], ...],
    fingerprint_dimension: str,
) -> list[AssessmentItem]:
    return [
        AssessmentItem(
            id=str(spec["id"]),
            text_by_language=dict(spec["text_by_language"]),  # type: ignore[arg-type]
            domain_id=str(spec["domain_id"]),
            scale_min=SCALE_MIN,
            scale_max=SCALE_MAX,
            reverse_scored=bool(spec["reverse_scored"]),
            fingerprint_dimension=fingerprint_dimension,
        )
        for spec in specs
    ]


def get_items_from_specs(
    specs: tuple[dict[str, object], ...],
    fingerprint_dimension: str,
    language: str = "en",
) -> list[AssessmentItem]:
    _ = language if language in SUPPORTED_LANGUAGES else "en"
    return build_assessment_items(specs, fingerprint_dimension)


def score_items(
    items: list[AssessmentItem],
    responses: list[AssessmentResponse],
) -> list[AssessmentResult]:
    return score_assessment(items, responses)


def item_text_for_language(item: AssessmentItem, language: str) -> str:
    lang = language if language in SUPPORTED_LANGUAGES else "en"
    return item.text_by_language.get(lang, item.text_by_language["en"])


def item_has_neutral_wording(item: AssessmentItem) -> bool:
    for text in item.text_by_language.values():
        lowered = text.lower()
        if any(phrase in lowered for phrase in FORBIDDEN_ITEM_PHRASES):
            return False
    return True
