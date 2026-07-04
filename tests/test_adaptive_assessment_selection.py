from niros.adaptive_assessment_selector import (
    BIG_FIVE_SHORT,
    DEFAULT_MAX_MODULES,
    EMOTION_REGULATION_DOMAIN_SHORT,
    GRIEF_LOSS_SHORT,
    SELF_DOMAIN_SHORT,
    select_assessment_modules,
)
from niros.assessment import AssessmentResult
from niros.assessment_runner import (
    MODULE_TITLES,
    completed_assessments_from_answers,
    render_adaptive_assessment_selection,
    run_adaptive_assessments,
)
from niros.assessments.registry import get_assessment_module_items
from niros.fingerprint_coverage import FingerprintCoverageAnalyzer
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact


def _tag(canonical_id: str, confidence: float = 1.0) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-adaptive-selection",
        evidence_id="session-adaptive-selection:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _completed(module_id: str, fingerprint_dimension: str) -> dict[str, list[AssessmentResult]]:
    return {
        module_id: [
            AssessmentResult(
                domain_id="sample",
                score=3.0,
                normalized_score=0.5,
                interpretation="moderate",
                fingerprint_dimension=fingerprint_dimension,
            )
        ]
    }


def test_selection_uses_coverage_engine_report():
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "feeling alone after loss"},
        detected_patterns=[_tag("grief_signal"), _tag("social_withdrawal")],
        semantic_facts=[
            SemanticFact(
                category="emotion",
                attribute="grief",
                value="present",
                evidence="after loss",
            )
        ],
    )

    assert selection.coverage_report is not None
    assert selection.selected_modules
    assert selection.reason_by_module
    assert selection.coverage_report.missing_domains
    assert len(selection.selected_modules) <= DEFAULT_MAX_MODULES


def test_completed_assessments_are_reused_not_reselected():
    completed = {
        **_completed("big-five-short", "big_five"),
        **_completed("self-domain-short", "self_domain"),
    }
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "grief after loss"},
        detected_patterns=[_tag("grief_signal")],
        completed_assessments=completed,
    )

    assert "big-five-short" not in selection.selected_modules
    assert "self-domain-short" not in selection.selected_modules
    assert GRIEF_LOSS_SHORT in selection.selected_modules


def test_run_adaptive_does_not_duplicate_completed_modules():
    completed = _completed("big-five-short", "big_five")
    runs = run_adaptive_assessments(
        presenting_problem={"main_problem": "grief after loss"},
        detected_patterns=[_tag("grief_signal"), _tag("social_withdrawal")],
        completed_assessments=completed,
        answers_by_module={},
        print_output=False,
    )

    module_ids = [run.module_id for run in runs]
    assert module_ids.count("big-five-short") == 1


def test_max_four_modules_selected():
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "many overlapping concerns"},
        detected_patterns=[
            _tag("depressed_mood_signal"),
            _tag("generalized_fear"),
            _tag("sleep_disruption"),
            _tag("grief_signal"),
            _tag("drug_use_concern"),
        ],
    )

    assert len(selection.selected_modules) <= 4


def test_high_coverage_domains_reduce_symptom_module_priority():
    completed = {
        "grief-loss-short": [
            AssessmentResult(
                domain_id="grief",
                score=4.5,
                normalized_score=0.9,
                interpretation="elevated",
                fingerprint_dimension="grief_loss_bereavement",
            )
        ]
    }
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "grief after loss"},
        detected_patterns=[_tag("grief_signal")],
        completed_assessments=completed,
    )

    assert GRIEF_LOSS_SHORT not in selection.selected_modules


def test_missing_domains_are_prioritized_in_selection():
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "avoiding people after breakup"},
        detected_patterns=[_tag("social_withdrawal"), _tag("relationship_breakup_context")],
    )

    report = selection.coverage_report
    assert report is not None
    assert "self_domain" in report.missing_domains or report.domains["self_domain"].coverage < 0.5
    assert SELF_DOMAIN_SHORT in selection.selected_modules or EMOTION_REGULATION_DOMAIN_SHORT in selection.selected_modules


def test_deterministic_selection_output():
    patterns = [_tag("sleep_disruption"), _tag("grief_signal")]
    intake = {"main_problem": "sleep and loss", "current_impact": "nightmares"}

    first = select_assessment_modules(
        presenting_problem=intake,
        detected_patterns=patterns,
    )
    second = select_assessment_modules(
        presenting_problem=intake,
        detected_patterns=patterns,
    )

    assert first == second


def test_debug_report_renders_coverage_levels_and_module_titles():
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "feeling unwanted"},
        detected_patterns=[_tag("unworthiness_signal")],
    )
    rendered = render_adaptive_assessment_selection(selection)

    assert "===== Fingerprint Coverage =====" in rendered
    assert "% partial" in rendered or "% unknown" in rendered or "% good" in rendered or "% complete" in rendered
    assert "Selected modules:" in rendered
    assert MODULE_TITLES[BIG_FIVE_SHORT] in rendered


def test_semantic_facts_influence_coverage_analysis():
    without_facts = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "I feel useless"},
        patterns=[],
    )
    with_facts = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "I feel useless"},
        patterns=[],
        semantic_facts=[
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="I feel useless",
            )
        ],
    )

    assert with_facts.domains["self_domain"].coverage >= without_facts.domains["self_domain"].coverage


def test_completed_assessments_from_answers_builds_scores():
    item_ids = {item.id for item in get_assessment_module_items("big-five-short")}
    answers = completed_assessments_from_answers(
        {"big-five-short": {item_id: 3 for item_id in item_ids}},
        language="en",
    )

    assert "big-five-short" in answers
    assert answers["big-five-short"]
