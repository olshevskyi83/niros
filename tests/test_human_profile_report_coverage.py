from niros.assessment import AssessmentResult
from niros.assessment_runner import (
    AssessedModuleRun,
    MODULE_TITLES,
    neutral_answers_for_module,
    run_big_five_short_assessment,
)
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_GOOD,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    COVERAGE_REPORT_DOMAIN_ORDER,
    format_fingerprint_coverage_report,
)
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact


def _pattern_tag(canonical_id: str, matched_text: str) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-coverage-report",
        evidence_id="session-coverage-report:evidence:0",
        canonical_id=canonical_id,
        matched_text=matched_text,
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _full_intake() -> dict[str, str]:
    return {
        "main_problem": "feeling disconnected after loss",
        "duration": "months",
        "perceived_causes": "grief",
        "current_impact": "withdrawal",
        "previous_attempts": "talking with friends",
        "desired_outcome": "feel more like myself",
    }


def test_profile_report_includes_fingerprint_coverage_section():
    report = build_human_profile_report_from_tags(
        [_pattern_tag("social_withdrawal", "I stay home most nights.")],
        presenting_problem=_full_intake(),
    )
    rendered = render_human_profile_report(report)

    assert "Human Digital Fingerprint Coverage" in rendered
    assert report.fingerprint_coverage is not None
    assert "Presenting Problem:" in rendered
    assert "Patterns:" in rendered
    assert "Big Five:" in rendered


def test_profile_report_lists_all_core_fingerprint_domains():
    report = build_human_profile_report_from_tags(
        [_pattern_tag("rumination", "My mind keeps replaying the same worries.")],
        presenting_problem={"main_problem": "stress"},
    )
    rendered = render_human_profile_report(report)

    for domain_id in COVERAGE_REPORT_DOMAIN_ORDER:
        label_fragment = {
            "presenting_problem": "Presenting Problem",
            "patterns": "Patterns:",
            "big_five": "Big Five",
            "self_domain": "Self:",
            "emotion_regulation_domain": "Emotion Regulation",
            "relationships_domain": "Relationships",
            "meaning": "Meaning / Purpose",
            "values_identity_domain": "Values / Identity",
            "cognitive_patterns_domain": "Cognitive Patterns",
            "emotional_flexibility_domain": "Emotional Flexibility",
        }[domain_id]
        assert label_fragment in rendered


def test_profile_report_shows_coverage_levels_and_confidence():
    report = build_human_profile_report_from_tags(
        [_pattern_tag("social_withdrawal", "I avoid people.")],
        presenting_problem=_full_intake(),
    )
    rendered = render_human_profile_report(report)

    assert COVERAGE_LEVEL_COMPLETE in rendered
    assert "confidence:" in rendered
    assert "—" in rendered


def test_profile_report_lists_missing_domains():
    report = build_human_profile_report_from_tags(
        [_pattern_tag("social_withdrawal", "I avoid people.")],
        presenting_problem=_full_intake(),
    )
    rendered = render_human_profile_report(report)

    assert "Missing / weak domains:" in rendered
    assert report.fingerprint_coverage is not None
    for domain_id in report.fingerprint_coverage.missing_domains:
        if domain_id == "emotion_regulation_domain":
            assert "Emotion Regulation" in rendered


def test_completed_domains_are_not_listed_as_missing():
    big_five_results = run_big_five_short_assessment(
        language="en",
        output_stream=__import__("io").StringIO(),
        answers=neutral_answers_for_module("big-five-short"),
        print_output=False,
    )
    self_results = [
        AssessmentResult(
            domain_id="self_worth",
            score=4.0,
            normalized_score=0.75,
            interpretation="elevated",
            fingerprint_dimension="self_domain",
        )
    ]
    report = build_human_profile_report_from_tags(
        [_pattern_tag("social_withdrawal", "I avoid people.")],
        presenting_problem=_full_intake(),
        assessment_module_runs=[
            AssessedModuleRun(module_id="big-five-short", results=big_five_results),
            AssessedModuleRun(module_id="self-domain-short", results=self_results),
        ],
    )
    rendered = render_human_profile_report(report)

    assert report.fingerprint_coverage is not None
    assert "big_five" not in report.fingerprint_coverage.missing_domains
    assert "self_domain" not in report.fingerprint_coverage.missing_domains
    missing_section = rendered.split("Missing / weak domains:", 1)[1].split(
        "Recommended next modules:", 1
    )[0]
    assert "Big Five" not in missing_section
    assert "- Self" not in missing_section
    assert "Self Domain" not in missing_section


def test_profile_report_shows_recommended_modules():
    report = build_human_profile_report_from_tags(
        [_pattern_tag("social_withdrawal", "I avoid people.")],
        presenting_problem=_full_intake(),
    )
    rendered = render_human_profile_report(report)

    assert "Recommended next modules:" in rendered
    assert report.fingerprint_coverage is not None
    for module_id in report.fingerprint_coverage.selected_modules:
        assert MODULE_TITLES[module_id] in rendered


def test_format_fingerprint_coverage_report_is_deterministic():
    report = build_human_profile_report_from_tags(
        [_pattern_tag("grief_signal", "I still miss them every day.")],
        presenting_problem=_full_intake(),
        semantic_facts=[
            SemanticFact(
                category="emotion",
                attribute="grief",
                value="present",
                evidence="still miss them",
            )
        ],
    ).fingerprint_coverage
    assert report is not None

    first = format_fingerprint_coverage_report(report, module_titles=MODULE_TITLES)
    second = format_fingerprint_coverage_report(report, module_titles=MODULE_TITLES)

    assert first == second


def test_existing_profile_sections_remain_compatible():
    tags = [
        _pattern_tag("people_pleasing", "I try to make everyone happy."),
        _pattern_tag("shame_sensitivity", "I feel embarrassed easily."),
    ]
    report = build_human_profile_report_from_tags(tags)
    rendered = render_human_profile_report(report)

    assert "Overview" in rendered
    assert "Main Observed Tendencies" in rendered
    assert "Relationship Patterns" in rendered
    assert "Self-Related Patterns" in rendered
    assert "Emotion-Related Patterns" in rendered
    assert "Strengths" in rendered
    assert "Vulnerabilities" in rendered
    assert "Open Questions for Future Interviews" in rendered
    assert "Evidence Summary" in rendered
    assert "Human Digital Fingerprint Coverage" in rendered


def test_high_coverage_domain_levels_are_reflected():
    report = build_human_profile_report_from_tags(
        [],
        presenting_problem=_full_intake(),
    )
    assert report.fingerprint_coverage is not None
    assert report.fingerprint_coverage.domains["presenting_problem"].level == COVERAGE_LEVEL_COMPLETE

    rendered = render_human_profile_report(report)
    assert "Presenting Problem: 100% — complete" in rendered


def test_semantic_facts_influence_coverage_in_profile_report():
    without = build_human_profile_report_from_tags(
        [_pattern_tag("social_withdrawal", "I avoid people.")],
        presenting_problem={"main_problem": "feeling alone"},
    )
    with_facts = build_human_profile_report_from_tags(
        [_pattern_tag("social_withdrawal", "I avoid people.")],
        presenting_problem={"main_problem": "feeling alone"},
        semantic_facts=[
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="I feel useless",
            )
        ],
    )

    assert without.fingerprint_coverage is not None
    assert with_facts.fingerprint_coverage is not None
    assert (
        with_facts.fingerprint_coverage.domains["self_domain"].coverage
        >= without.fingerprint_coverage.domains["self_domain"].coverage
    )
