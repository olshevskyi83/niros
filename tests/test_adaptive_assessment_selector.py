from niros.adaptive_assessment_selector import (
    BIG_FIVE_SHORT,
    EMOTION_REGULATION_DOMAIN_SHORT,
    GRIEF_LOSS_SHORT,
    PAIN_FATIGUE_SHORT,
    PSYCHEDELIC_CONCERN_SHORT,
    SELF_DOMAIN_SHORT,
    SLEEP_SHORT,
    SUBSTANCE_USE_SHORT,
    TRAUMA_STRESS_SHORT,
    select_assessment_modules,
)
from niros.assessment_domain_map import build_assessment_domain_map
from niros.models import SupportedLanguage
from niros.patterns import PatternTag


def _tag(canonical_id: str, confidence: float = 1.0) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-assessment-selector",
        evidence_id="session-assessment-selector:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _select(pattern_ids: list[str], presenting_problem: dict[str, str] | None = None):
    return select_assessment_modules(
        presenting_problem=presenting_problem or {},
        detected_patterns=pattern_ids,
        assessment_domain_map=build_assessment_domain_map(),
    )


def test_big_five_always_included():
    selection = _select([])

    assert selection.selected_modules[0] == BIG_FIVE_SHORT
    assert selection.coverage_report is not None
    assert BIG_FIVE_SHORT in selection.reason_by_module


def test_sleep_patterns_select_sleep_short_via_coverage_gap():
    selection = _select(["sleep_disruption", "insomnia_signal"])

    assert SLEEP_SHORT in selection.selected_modules
    assert selection.coverage_report is not None


def test_accident_pattern_selects_trauma_stress_short():
    selection = _select(["accident_context"])

    assert TRAUMA_STRESS_SHORT in selection.selected_modules


def test_substance_patterns_select_substance_use_short():
    selection = _select(["drug_use_concern", "compulsive_use_signal"])

    assert SUBSTANCE_USE_SHORT in selection.selected_modules


def test_fibromyalgia_selects_pain_fatigue_short():
    selection = _select(["fibromyalgia_signal"])

    assert PAIN_FATIGUE_SHORT in selection.selected_modules


def test_psychedelic_anxiety_selects_psychedelic_concern_short():
    selection = _select(["psychedelic_anxiety", "fear_of_bad_trip"])

    assert PSYCHEDELIC_CONCERN_SHORT in selection.selected_modules


def test_grief_and_social_withdrawal_prioritize_core_fingerprint_modules():
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "loss and avoiding people"},
        detected_patterns=["grief_signal", "social_withdrawal", "sleep_disruption"],
        assessment_domain_map=build_assessment_domain_map(),
    )

    assert BIG_FIVE_SHORT in selection.selected_modules
    assert GRIEF_LOSS_SHORT in selection.selected_modules
    assert SELF_DOMAIN_SHORT in selection.selected_modules
    assert EMOTION_REGULATION_DOMAIN_SHORT in selection.selected_modules


def test_module_cap_limits_total_selected_modules():
    selection = _select(
        [
            "depressed_mood_signal",
            "generalized_fear",
            "sleep_disruption",
            "accident_context",
            "grief_signal",
            "drug_use_concern",
            "fibromyalgia_signal",
            "psychedelic_anxiety",
        ]
    )

    assert len(selection.selected_modules) == 4
    assert selection.selected_modules[0] == BIG_FIVE_SHORT


def test_deterministic_output_for_same_inputs():
    patterns = [
        _tag("sleep_disruption", 0.92),
        _tag("social_withdrawal", 0.88),
        _tag("grief_signal", 0.95),
    ]
    presenting_problem = {
        "main_problem": "sleep and loss",
        "current_impact": "nightmares",
    }

    first = select_assessment_modules(
        presenting_problem=presenting_problem,
        detected_patterns=patterns,
        assessment_domain_map=build_assessment_domain_map(),
    )
    second = select_assessment_modules(
        presenting_problem=presenting_problem,
        detected_patterns=patterns,
        assessment_domain_map=build_assessment_domain_map(),
    )

    assert first == second


def test_skipped_modules_excludes_selected_only():
    selection = _select(["accident_context"])

    assert BIG_FIVE_SHORT in selection.selected_modules
    assert TRAUMA_STRESS_SHORT in selection.selected_modules
    assert BIG_FIVE_SHORT not in selection.skipped_modules
    assert TRAUMA_STRESS_SHORT not in selection.skipped_modules
