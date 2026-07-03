import re

from niros.human_profile_report import (
    build_human_profile_report,
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.human_profile_summary import build_human_profile_summary
from niros.models import SupportedLanguage
from niros.patterns import PatternTag

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(is|e|ed|ing)?|disorder|patholog|clinical syndrome|bipolar|"
    r"ptsd|narcissistic personality|borderline personality)\b",
    re.IGNORECASE,
)


def _pattern_tag(
    tag_id: str,
    canonical_id: str,
    matched_text: str,
    confidence: float = 1.0,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-001",
        evidence_id="session-001:evidence:0",
        canonical_id=canonical_id,
        matched_text=matched_text,
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def test_report_builds_from_existing_human_profile_summary():
    tags = [
        _pattern_tag(
            "tag-1",
            "people_pleasing",
            "I try to make everyone happy.",
        ),
        _pattern_tag(
            "tag-2",
            "shame_sensitivity",
            "I often feel embarrassed even when no one is watching.",
        ),
    ]
    summary = build_human_profile_summary(tags)

    report = build_human_profile_report(summary, tags)

    assert report.overview
    assert report.tendencies
    assert report.relationship_patterns
    assert report.self_patterns
    assert report.vulnerabilities


def test_report_includes_expected_detected_patterns():
    tags = [
        _pattern_tag("tag-1", "attachment_anxiety", "I feel anxious when people become distant."),
        _pattern_tag("tag-2", "emotional_suppression", "I push my feelings down so I can keep going."),
    ]
    report = build_human_profile_report_from_tags(tags)

    rendered = render_human_profile_report(report).lower()

    assert "attachment anxiety" in rendered
    assert "emotional suppression" in rendered
    assert report.relationship_patterns
    assert report.emotion_patterns


def test_report_does_not_include_diagnosis_language():
    tags = [
        _pattern_tag("tag-1", "perfectionism", "No matter what I achieve, it never feels good enough."),
        _pattern_tag("tag-2", "rumination", "My mind gets stuck on the same worries."),
    ]
    report = build_human_profile_report_from_tags(tags)
    rendered = render_human_profile_report(report)

    assert "not diagnostic" in rendered.lower()
    assert DIAGNOSIS_PATTERN.search(rendered) is None


def test_report_includes_evidence_references():
    matched_text = "I try to make everyone happy."
    tags = [_pattern_tag("tag-1", "people_pleasing", matched_text)]
    report = build_human_profile_report_from_tags(tags)

    assert any(matched_text in item for item in report.evidence_summary)
    assert "people_pleasing" in report.evidence_summary[0]


def test_empty_profile_is_handled_safely():
    report = build_human_profile_report_from_tags([])

    assert report.overview
    assert report.tendencies == []
    assert report.relationship_patterns == []
    assert report.self_patterns == []
    assert report.emotion_patterns == []
    assert report.vulnerabilities == []
    assert report.strengths
    assert report.open_questions
    assert report.evidence_summary


def test_renderer_returns_readable_text():
    tags = [
        _pattern_tag("tag-1", "conflict_avoidance", "I stay quiet even when I disagree."),
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
    assert "Conflict Avoidance" in rendered
