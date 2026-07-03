from __future__ import annotations

from dataclasses import dataclass

ASSESSMENT_RESULTS_TITLE = "=== NIROS Assessment Results ==="
EMPTY_ASSESSMENT_RESULTS_TEXT = (
    f"{ASSESSMENT_RESULTS_TITLE}\n\n"
    "No assessment results are available yet."
)

NEUTRAL_INTERPRETATIONS: frozenset[str] = frozenset({"low", "moderate", "elevated"})

FORBIDDEN_INTERPRETATION_PHRASES: tuple[str, ...] = (
    " diagnosis",
    "diagnose ",
    "disorder",
    "clinical",
    "depressed",
    "depression",
    "anxiety disorder",
    "patholog",
)


@dataclass(frozen=True)
class AssessmentItem:
    id: str
    text_by_language: dict[str, str]
    domain_id: str
    scale_min: int
    scale_max: int
    reverse_scored: bool
    fingerprint_dimension: str


@dataclass(frozen=True)
class AssessmentResponse:
    item_id: str
    value: int


@dataclass(frozen=True)
class AssessmentResult:
    domain_id: str
    score: float
    normalized_score: float
    interpretation: str
    fingerprint_dimension: str


def assessment_result_to_dict(result: AssessmentResult) -> dict[str, str | float]:
    return {
        "domain_id": result.domain_id,
        "score": result.score,
        "normalized_score": result.normalized_score,
        "interpretation": result.interpretation,
        "fingerprint_dimension": result.fingerprint_dimension,
    }


def recode_assessment_response(value: int, item: AssessmentItem) -> int:
    if value < item.scale_min or value > item.scale_max:
        raise ValueError(
            f"Assessment response for {item.id} must be between "
            f"{item.scale_min} and {item.scale_max}."
        )
    if item.reverse_scored:
        return item.scale_min + item.scale_max - value
    return value


def normalize_assessment_score(mean_score: float, scale_min: int, scale_max: int) -> float:
    if scale_max == scale_min:
        return 0.5
    normalized = (mean_score - scale_min) / (scale_max - scale_min)
    return min(1.0, max(0.0, normalized))


def interpret_assessment_score(normalized_score: float) -> str:
    if normalized_score < 1 / 3:
        return "low"
    if normalized_score <= 2 / 3:
        return "moderate"
    return "elevated"


def score_assessment(
    items: list[AssessmentItem],
    responses: list[AssessmentResponse],
) -> list[AssessmentResult]:
    response_map = {response.item_id: response.value for response in responses}
    items_by_domain: dict[str, list[AssessmentItem]] = {}

    for item in items:
        items_by_domain.setdefault(item.domain_id, []).append(item)

    results: list[AssessmentResult] = []
    for domain_id in sorted(items_by_domain):
        domain_items = items_by_domain[domain_id]
        recoded_values: list[int] = []
        fingerprint_dimension = domain_items[0].fingerprint_dimension

        for item in domain_items:
            if item.id not in response_map:
                continue
            recoded_values.append(recode_assessment_response(response_map[item.id], item))
            fingerprint_dimension = item.fingerprint_dimension

        if not recoded_values:
            continue

        scale_min = domain_items[0].scale_min
        scale_max = domain_items[0].scale_max
        mean_score = sum(recoded_values) / len(recoded_values)
        normalized_score = normalize_assessment_score(mean_score, scale_min, scale_max)

        results.append(
            AssessmentResult(
                domain_id=domain_id,
                score=mean_score,
                normalized_score=normalized_score,
                interpretation=interpret_assessment_score(normalized_score),
                fingerprint_dimension=fingerprint_dimension,
            )
        )

    return results


def render_assessment_results(results: list[AssessmentResult]) -> str:
    if not results:
        return EMPTY_ASSESSMENT_RESULTS_TEXT

    lines = [ASSESSMENT_RESULTS_TITLE, ""]
    for result in sorted(results, key=lambda item: item.domain_id):
        lines.extend(
            [
                f"Domain: {result.domain_id}",
                f"Score: {result.score:.2f}",
                f"Level: {result.interpretation}",
                f"Fingerprint dimension: {result.fingerprint_dimension}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def interpretation_is_neutral(interpretation: str) -> bool:
    if interpretation not in NEUTRAL_INTERPRETATIONS:
        return False
    lowered = interpretation.lower()
    return not any(phrase in lowered for phrase in FORBIDDEN_INTERPRETATION_PHRASES)
