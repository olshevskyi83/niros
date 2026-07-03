from __future__ import annotations

from dataclasses import dataclass, field

NEUTRAL_FILLERS = [
    "Work has been fairly steady this month.",
    "I have been sleeping normally most nights.",
    "I spent time with a friend over the weekend.",
    "The commute has been manageable lately.",
    "I cooked dinner and listened to music.",
    "I took a short walk after lunch today.",
    "I finished a few ordinary tasks at home.",
    "The weather has been mild this week.",
    "I read a book chapter before bed.",
    "I ran some errands in the neighborhood.",
]


def _interleave(pattern_phrases: list[str], fillers: list[str], count: int) -> list[str]:
    turns: list[str] = []
    pattern_index = 0
    filler_index = 0

    for turn_number in range(count):
        if turn_number % 4 == 3:
            turns.append(fillers[filler_index % len(fillers)])
            filler_index += 1
        else:
            turns.append(pattern_phrases[pattern_index % len(pattern_phrases)])
            pattern_index += 1

    return turns


SCENARIO_RELATIONSHIP_ANXIOUS_TURNS = _interleave(
    [
        "I worry people will stop liking me.",
        "I feel anxious when people become distant.",
        "I often need reassurance that they still care about me.",
        "When someone I care about does not reply, I start thinking something is wrong.",
        "I check messages again and again.",
        "I try to make everyone happy.",
        "I find it hard to say no when people ask me for something.",
        "I put others before myself.",
        "I worry about letting people down.",
        "I hate disappointing people.",
        "I stay quiet even when I disagree.",
        "I often keep quiet just to avoid conflict.",
        "When I make a mistake, I feel like a failure.",
        "I often feel embarrassed even when no one is watching.",
        "Sometimes I want to disappear when I think I have let someone down.",
    ],
    NEUTRAL_FILLERS,
    40,
)

SCENARIO_PERFECTIONISM_EMOTION_TURNS = _interleave(
    [
        "No matter what I achieve, it never feels good enough.",
        "I delay starting tasks because I am afraid the result will not be perfect.",
        "One mistake makes me feel like something is wrong with me.",
        "I cannot rest after achieving something because it never feels good enough.",
        "I quickly dismiss my achievements and move on.",
        "I push my feelings down so I can keep going.",
        "I try not to feel anything when things get hard.",
        "I keep my emotions to myself.",
        "I go numb when too much is happening.",
        "My mind gets stuck on the same worries.",
        "I keep going over the same problems in my head.",
        "I cannot stop thinking about what might happen.",
        "My thoughts loop and I cannot switch them off.",
    ],
    NEUTRAL_FILLERS,
    40,
)

SCENARIO_HEALTHY_TURNS = _interleave(
    [
        "I usually give people space to respond in their own time.",
        "I can say no when I need to without much guilt.",
        "I feel steady in close relationships most weeks.",
        "Disagreements feel uncomfortable but manageable.",
        "I can name what I feel before I react.",
        "I recover fairly quickly after a hard day.",
        "I trust my close friends unless they show me otherwise.",
        "I do not need constant reassurance to feel connected.",
        "Rest after work helps me feel balanced.",
        "I can hear feedback without collapsing inside.",
        "I notice stress early and adjust my schedule.",
        "I feel comfortable being myself around people I trust.",
    ],
    NEUTRAL_FILLERS,
    40,
)


@dataclass(frozen=True)
class EndToEndScenario:
    name: str
    session_id: str
    turns: list[str]
    expected_patterns: frozenset[str]
    forbidden_patterns: frozenset[str]
    expected_hypothesis_ids: frozenset[str] = field(default_factory=frozenset)
    expect_profile_evidence: bool = True
    minimum_follow_up_questions: int = 5


SCENARIO_RELATIONSHIP_ANXIOUS = EndToEndScenario(
    name="relationship_anxiety_people_pleasing_shame",
    session_id="e2e-profile-relationship-001",
    turns=SCENARIO_RELATIONSHIP_ANXIOUS_TURNS,
    expected_patterns=frozenset(
        {
            "attachment_anxiety",
            "fear_of_rejection",
            "people_pleasing",
            "fear_of_disappointing_others",
            "shame_sensitivity",
            "conflict_avoidance",
        }
    ),
    forbidden_patterns=frozenset(
        {
            "perfectionism",
            "emotional_suppression",
            "rumination",
            "identity_uncertainty",
            "low_self_efficacy",
        }
    ),
    expected_hypothesis_ids=frozenset({"people_pleasing_pattern"}),
)

SCENARIO_PERFECTIONISM_EMOTION = EndToEndScenario(
    name="perfectionism_suppression_rumination",
    session_id="e2e-profile-perfectionism-001",
    turns=SCENARIO_PERFECTIONISM_EMOTION_TURNS,
    expected_patterns=frozenset(
        {
            "perfectionism",
            "emotional_suppression",
            "rumination",
        }
    ),
    forbidden_patterns=frozenset(
        {
            "attachment_anxiety",
            "people_pleasing",
            "identity_uncertainty",
            "trust_difficulty",
        }
    ),
)

SCENARIO_HEALTHY = EndToEndScenario(
    name="healthy_secure_profile",
    session_id="e2e-profile-healthy-001",
    turns=SCENARIO_HEALTHY_TURNS,
    expected_patterns=frozenset(),
    forbidden_patterns=frozenset(
        {
            "attachment_anxiety",
            "fear_of_rejection",
            "people_pleasing",
            "shame_sensitivity",
            "conflict_avoidance",
            "perfectionism",
            "emotional_suppression",
            "rumination",
            "emotional_overwhelm",
            "emotional_avoidance",
            "anxiety_reactivity",
            "identity_uncertainty",
            "self_worth_instability",
            "harsh_self_criticism",
            "low_self_efficacy",
        }
    ),
    expect_profile_evidence=False,
    minimum_follow_up_questions=0,
)

ALL_SCENARIOS = (
    SCENARIO_RELATIONSHIP_ANXIOUS,
    SCENARIO_PERFECTIONISM_EMOTION,
    SCENARIO_HEALTHY,
)
