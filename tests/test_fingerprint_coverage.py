from niros.adaptive_assessment_selector import (
    BIG_FIVE_SHORT,
    EMOTION_REGULATION_DOMAIN_SHORT,
    GRIEF_LOSS_SHORT,
    SELF_DOMAIN_SHORT,
    SLEEP_SHORT,
    SUBSTANCE_USE_SHORT,
    select_assessment_modules,
)
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_GOOD,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageAnalyzer,
    coverage_level,
    render_fingerprint_coverage_report,
)
from niros.assessment import AssessmentResult
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact


def _tag(canonical_id: str, confidence: float = 1.0) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-fingerprint-coverage",
        evidence_id="session-fingerprint-coverage:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _fact(category: str, attribute: str, value: str, evidence: str) -> SemanticFact:
    return SemanticFact(
        category=category,
        attribute=attribute,
        value=value,
        confidence=0.9,
        evidence=evidence,
    )


def test_coverage_levels():
    assert coverage_level(0.0) == COVERAGE_LEVEL_UNKNOWN
    assert coverage_level(0.30) == COVERAGE_LEVEL_PARTIAL
    assert coverage_level(0.60) == COVERAGE_LEVEL_GOOD
    assert coverage_level(0.95) == COVERAGE_LEVEL_COMPLETE


def test_presenting_problem_coverage_from_intake():
    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={
            "main_problem": "bad sleep",
            "duration": "months",
            "perceived_causes": "stress",
            "current_impact": "fatigue",
            "previous_attempts": "none",
            "desired_outcome": "rest",
        },
        patterns=[],
    )

    assert report.domains["presenting_problem"].coverage == 1.0
    assert report.domains["presenting_problem"].level == COVERAGE_LEVEL_COMPLETE


def test_pattern_coverage_increases_patterns_domain():
    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={},
        patterns=["sleep_disruption", "nightmare_disturbance"],
    )

    assert report.domains["patterns"].coverage > 0.0
    assert report.domains["sleep_nightmares"].coverage >= 0.30


def test_semantic_facts_contribute_to_domain_coverage():
    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={},
        patterns=[],
        semantic_facts=[_fact("self", "unworthiness", "present", "I feel useless")],
    )

    assert report.domains["self_domain"].coverage >= 0.20


def test_completed_assessment_marks_domain_coverage():
    completed = {
        "self-domain-short": [
            AssessmentResult(
                domain_id="self_worth",
                score=4.0,
                normalized_score=0.75,
                interpretation="elevated",
                fingerprint_dimension="self_domain",
            )
        ]
    }
    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={},
        patterns=[],
        completed_assessments=completed,
    )

    assert report.domains["self_domain"].coverage >= 0.75
    assert "self-domain-short" not in report.selected_modules


def test_sleep_social_withdrawal_loss_prioritizes_fingerprint_modules():
    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={
            "main_problem": "bad sleep and feeling alone after a loss",
            "current_impact": "nightmares and avoiding people",
        },
        patterns=[
            _tag("sleep_disruption"),
            _tag("nightmare_disturbance"),
            _tag("social_withdrawal"),
            _tag("grief_signal"),
        ],
        max_modules=4,
    )

    assert report.selected_modules[0] == BIG_FIVE_SHORT
    assert set(report.selected_modules) == {
        BIG_FIVE_SHORT,
        SELF_DOMAIN_SHORT,
        EMOTION_REGULATION_DOMAIN_SHORT,
        GRIEF_LOSS_SHORT,
    }


def test_module_selection_respects_max_module_count():
    selection = select_assessment_modules(
        presenting_problem={"main_problem": "many concerns"},
        detected_patterns=[
            "depressed_mood_signal",
            "generalized_fear",
            "sleep_disruption",
            "accident_context",
            "grief_signal",
            "drug_use_concern",
            "fibromyalgia_signal",
            "psychedelic_anxiety",
        ],
        max_modules=4,
    )

    assert len(selection.selected_modules) == 4
    assert selection.selected_modules[0] == BIG_FIVE_SHORT


def test_information_gain_prefers_missing_domains_over_redundant_modules():
    completed = {
        "big-five-short": [
            AssessmentResult(
                domain_id="openness",
                score=3.0,
                normalized_score=0.5,
                interpretation="moderate",
                fingerprint_dimension="big_five",
            )
        ],
        "self-domain-short": [
            AssessmentResult(
                domain_id="self_worth",
                score=3.0,
                normalized_score=0.5,
                interpretation="moderate",
                fingerprint_dimension="self_domain",
            )
        ],
    }

    selection = select_assessment_modules(
        presenting_problem={"main_problem": "grief after loss"},
        detected_patterns=["grief_signal", "social_withdrawal"],
        completed_assessments=completed,
        max_modules=4,
    )

    assert "big-five-short" not in selection.selected_modules
    assert "self-domain-short" not in selection.selected_modules
    assert GRIEF_LOSS_SHORT in selection.selected_modules


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
    )
    second = select_assessment_modules(
        presenting_problem=presenting_problem,
        detected_patterns=patterns,
    )

    assert first == second


def test_coverage_report_renders_debug_output():
    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "stress"},
        patterns=["sleep_disruption"],
        max_modules=2,
    )
    rendered = render_fingerprint_coverage_report(report)

    assert "===== Fingerprint Coverage =====" in rendered
    assert "Presenting Problem" in rendered
    assert "Big Five" in rendered
    assert "Selected:" in rendered
    assert BIG_FIVE_SHORT in rendered


def test_substance_intake_selects_substance_module_via_coverage_gap():
    selection = select_assessment_modules(
        presenting_problem={
            "main_problem": "cannot control substance use",
            "current_impact": "compulsive drug use",
        },
        detected_patterns=["drug_use_concern", "compulsive_use_signal"],
        max_modules=4,
    )

    assert SUBSTANCE_USE_SHORT in selection.selected_modules


def test_sleep_intake_selects_sleep_module_via_coverage_gap():
    selection = select_assessment_modules(
        presenting_problem={
            "main_problem": "I almost never sleep",
            "current_impact": "bad sleep every night",
        },
        detected_patterns=["sleep_disruption", "insomnia_signal"],
        max_modules=4,
    )

    assert SLEEP_SHORT in selection.selected_modules
