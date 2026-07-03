from __future__ import annotations

from niros.big_five.profile import BigFiveProfile
from niros.big_five.questionnaire import (
    BIG_FIVE_QUESTIONNAIRE,
    SCALE_MAX,
    SCALE_MIN,
    BigFiveDomain,
    BigFiveItem,
    ItemKeying,
)


def recode_item_response(raw: int, keyed: ItemKeying) -> int:
    if raw < SCALE_MIN or raw > SCALE_MAX:
        raise ValueError(f"Big Five answers must be between {SCALE_MIN} and {SCALE_MAX}.")
    if keyed == "reverse":
        return SCALE_MIN + SCALE_MAX - raw
    return raw


def normalize_trait_mean(mean_score: float) -> float:
    normalized = (mean_score - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)
    return min(1.0, max(0.0, normalized))


def score_domain(items: tuple[BigFiveItem, ...], answers: dict[str, int]) -> float:
    recoded: list[int] = []
    for item in items:
        if item.item_id not in answers:
            raise ValueError(f"Missing answer for item {item.item_id}.")
        recoded.append(recode_item_response(answers[item.item_id], item.keyed))

    mean_score = sum(recoded) / len(recoded)
    return normalize_trait_mean(mean_score)


def score_big_five(answers: dict[str, int]) -> BigFiveProfile:
    domain_scores: dict[BigFiveDomain, float] = {}
    for domain in BigFiveProfile.TRAIT_FIELDS:
        items = tuple(item for item in BIG_FIVE_QUESTIONNAIRE if item.domain == domain)
        domain_scores[domain] = score_domain(items, answers)

    return BigFiveProfile(
        openness=domain_scores["openness"],
        conscientiousness=domain_scores["conscientiousness"],
        extraversion=domain_scores["extraversion"],
        agreeableness=domain_scores["agreeableness"],
        neuroticism=domain_scores["neuroticism"],
    )


def score_big_five_from_list(answers: list[int]) -> BigFiveProfile:
    if len(answers) != len(BIG_FIVE_QUESTIONNAIRE):
        raise ValueError(
            f"Expected {len(BIG_FIVE_QUESTIONNAIRE)} answers, received {len(answers)}."
        )

    answer_map = {
        item.item_id: answer
        for item, answer in zip(BIG_FIVE_QUESTIONNAIRE, answers, strict=True)
    }
    return score_big_five(answer_map)
