from tests.e2e_interview_runner import (
    assert_scenario_expectations,
    run_multi_turn_interview,
    stable_profile_snapshot,
)
from tests.e2e_interview_scenarios import (
    SCENARIO_HEALTHY,
    SCENARIO_PERFECTIONISM_EMOTION,
    SCENARIO_RELATIONSHIP_ANXIOUS,
)


def test_end_to_end_profile_relationship_anxiety_people_pleasing_shame():
    result = run_multi_turn_interview(SCENARIO_RELATIONSHIP_ANXIOUS)

    assert_scenario_expectations(SCENARIO_RELATIONSHIP_ANXIOUS, result)

    primary_id = result.profile["primary_pattern"]["canonical_id"]
    assert primary_id in {
        "people_pleasing",
        "attachment_anxiety",
        "fear_of_rejection",
        "shame_sensitivity",
    }
    assert "shame_sensitivity" in result.detected_pattern_ids
    assert "people_pleasing" in result.detected_pattern_ids


def test_end_to_end_profile_perfectionism_suppression_rumination():
    result = run_multi_turn_interview(SCENARIO_PERFECTIONISM_EMOTION)

    assert_scenario_expectations(SCENARIO_PERFECTIONISM_EMOTION, result)

    assert "perfectionism" in result.detected_pattern_ids
    assert "emotional_suppression" in result.detected_pattern_ids
    assert "rumination" in result.detected_pattern_ids
    assert result.profile["primary_pattern"]["canonical_id"] in {
        "perfectionism",
        "emotional_suppression",
        "rumination",
    }


def test_end_to_end_profile_healthy_secure_baseline():
    result = run_multi_turn_interview(SCENARIO_HEALTHY)

    assert_scenario_expectations(SCENARIO_HEALTHY, result)
    assert result.detected_pattern_ids == frozenset()
    assert result.hypotheses == []


def test_end_to_end_profiles_are_stable_between_runs():
    scenarios = (
        SCENARIO_RELATIONSHIP_ANXIOUS,
        SCENARIO_PERFECTIONISM_EMOTION,
        SCENARIO_HEALTHY,
    )

    for scenario in scenarios:
        first = stable_profile_snapshot(run_multi_turn_interview(scenario))
        second = stable_profile_snapshot(run_multi_turn_interview(scenario))
        assert first == second
