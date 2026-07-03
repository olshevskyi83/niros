from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BigFiveDomain = Literal["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
ItemKeying = Literal["positive", "reverse"]

SCALE_MIN = 1
SCALE_MAX = 5


@dataclass(frozen=True)
class BigFiveItem:
    item_id: str
    domain: BigFiveDomain
    text: str
    keyed: ItemKeying


BIG_FIVE_QUESTIONNAIRE: tuple[BigFiveItem, ...] = (
    BigFiveItem("bf_o_01", "openness", "I enjoy exploring new ideas.", "positive"),
    BigFiveItem("bf_o_02", "openness", "I like trying unfamiliar activities.", "positive"),
    BigFiveItem("bf_o_03", "openness", "I prefer routines and familiar approaches.", "reverse"),
    BigFiveItem("bf_o_04", "openness", "I am not very interested in abstract concepts.", "reverse"),
    BigFiveItem("bf_c_01", "conscientiousness", "I follow through on plans I make.", "positive"),
    BigFiveItem("bf_c_02", "conscientiousness", "I keep my belongings and tasks organized.", "positive"),
    BigFiveItem("bf_c_03", "conscientiousness", "I often leave tasks until the last minute.", "reverse"),
    BigFiveItem("bf_c_04", "conscientiousness", "I find it hard to stick to schedules.", "reverse"),
    BigFiveItem("bf_e_01", "extraversion", "I feel energized around other people.", "positive"),
    BigFiveItem("bf_e_02", "extraversion", "I speak up easily in groups.", "positive"),
    BigFiveItem("bf_e_03", "extraversion", "I prefer quiet time alone to social events.", "reverse"),
    BigFiveItem("bf_e_04", "extraversion", "I rarely seek out lively company.", "reverse"),
    BigFiveItem("bf_a_01", "agreeableness", "I try to be considerate of others' feelings.", "positive"),
    BigFiveItem("bf_a_02", "agreeableness", "I prefer cooperation over competition.", "positive"),
    BigFiveItem("bf_a_03", "agreeableness", "I can be blunt even when it may hurt feelings.", "reverse"),
    BigFiveItem("bf_a_04", "agreeableness", "I find it hard to trust people at first.", "reverse"),
    BigFiveItem("bf_n_01", "neuroticism", "I worry about things that might go wrong.", "positive"),
    BigFiveItem("bf_n_02", "neuroticism", "I get stressed easily when things change.", "positive"),
    BigFiveItem("bf_n_03", "neuroticism", "I stay calm under pressure.", "reverse"),
    BigFiveItem("bf_n_04", "neuroticism", "I rarely feel anxious or upset.", "reverse"),
)


def questionnaire_item_ids() -> tuple[str, ...]:
    return tuple(item.item_id for item in BIG_FIVE_QUESTIONNAIRE)


def items_for_domain(domain: BigFiveDomain) -> tuple[BigFiveItem, ...]:
    return tuple(item for item in BIG_FIVE_QUESTIONNAIRE if item.domain == domain)
