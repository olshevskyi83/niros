from __future__ import annotations

from dataclasses import dataclass, field

from niros.assessment import AssessmentResult
from niros.assessment_runner import (
    AssessedModuleRun,
    MODULE_TITLES,
    format_assessment_signal,
)
from niros.consistency_engine import (
    analyze_consistency,
    format_consistency_observations,
)
from niros.evidence_store import EvidenceStore
from niros.fingerprint_coverage import (
    FingerprintCoverageAnalyzer,
    FingerprintCoverageReport,
    format_fingerprint_coverage_report,
)
from niros.human_profile_summary import (
    GENERIC_PATTERN_TEXT,
    NO_EVIDENCE_PROFILE_TEXT,
    PATTERN_INTERPRETATIONS,
    build_human_profile_summary,
)
from niros.hypotheses import Hypothesis
from niros.knowledge import KnowledgePattern, PatternLoader
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact

RELATIONSHIPS_DOMAIN = "relationships"
SELF_CONCEPT_DOMAIN = "self_concept"
EMOTION_REGULATION_DOMAIN = "emotion_regulation"

DOMAIN_LABELS = {
    RELATIONSHIPS_DOMAIN: "relationships",
    SELF_CONCEPT_DOMAIN: "self",
    EMOTION_REGULATION_DOMAIN: "emotion regulation",
}

MAX_OPEN_QUESTIONS = 5
MAX_EVIDENCE_ITEMS = 12


@dataclass
class HumanProfileReport:
    overview: str
    presenting_problem: dict[str, str] = field(default_factory=dict)
    tendencies: list[str] = field(default_factory=list)
    relationship_patterns: list[str] = field(default_factory=list)
    self_patterns: list[str] = field(default_factory=list)
    emotion_patterns: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    vulnerabilities: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    consistency_observations: list[str] = field(default_factory=list)
    evidence_summary: list[str] = field(default_factory=list)
    assessment_signals: list[str] = field(default_factory=list)
    fingerprint_coverage: FingerprintCoverageReport | None = None


def build_human_profile_report(
    profile_summary: dict,
    detected_patterns: list[PatternTag],
    hypotheses: list[Hypothesis] | None = None,
    loader: PatternLoader | None = None,
    evidence_store: EvidenceStore | None = None,
    presenting_problem: dict[str, str] | None = None,
    assessment_results: list[AssessmentResult] | None = None,
    assessment_module_runs: list[AssessedModuleRun] | None = None,
    semantic_facts: list[SemanticFact] | None = None,
    fingerprint_coverage_report: FingerprintCoverageReport | None = None,
) -> HumanProfileReport:
    pattern_loader = loader or PatternLoader()
    ranked_pattern_ids = _ranked_pattern_ids(profile_summary, detected_patterns)
    presenting = dict(presenting_problem or {})
    coverage = _build_fingerprint_coverage(
        presenting_problem=presenting,
        detected_patterns=detected_patterns,
        semantic_facts=semantic_facts,
        assessment_module_runs=assessment_module_runs,
        fingerprint_coverage_report=fingerprint_coverage_report,
    )

    if not ranked_pattern_ids:
        empty = _empty_report()
        empty.presenting_problem = presenting
        empty.assessment_signals = _build_assessment_signals(
            assessment_results,
            assessment_module_runs,
        )
        empty.fingerprint_coverage = coverage
        return empty

    patterns = [pattern_loader.load(pattern_id) for pattern_id in ranked_pattern_ids]
    pattern_counts = profile_summary.get("pattern_counts", {})
    domain_patterns = _group_patterns_by_domain(patterns)

    tendencies = [_tendency_line(pattern) for pattern in patterns]
    relationship_patterns = _domain_pattern_lines(domain_patterns[RELATIONSHIPS_DOMAIN], pattern_counts)
    self_patterns = _domain_pattern_lines(domain_patterns[SELF_CONCEPT_DOMAIN], pattern_counts)
    emotion_patterns = _domain_pattern_lines(domain_patterns[EMOTION_REGULATION_DOMAIN], pattern_counts)

    return HumanProfileReport(
        overview=_build_overview(profile_summary, patterns, hypotheses or []),
        presenting_problem=presenting,
        tendencies=tendencies,
        relationship_patterns=relationship_patterns,
        self_patterns=self_patterns,
        emotion_patterns=emotion_patterns,
        strengths=_build_strengths(patterns, domain_patterns),
        vulnerabilities=_build_vulnerabilities(patterns, pattern_counts),
        open_questions=_collect_open_questions(patterns, pattern_loader),
        consistency_observations=_build_consistency_observations(evidence_store),
        evidence_summary=_build_evidence_summary(detected_patterns, pattern_counts),
        assessment_signals=_build_assessment_signals(
            assessment_results,
            assessment_module_runs,
        ),
        fingerprint_coverage=coverage,
    )


def build_human_profile_report_from_tags(
    detected_patterns: list[PatternTag],
    hypotheses: list[Hypothesis] | None = None,
    loader: PatternLoader | None = None,
    evidence_store: EvidenceStore | None = None,
    presenting_problem: dict[str, str] | None = None,
    assessment_results: list[AssessmentResult] | None = None,
    assessment_module_runs: list[AssessedModuleRun] | None = None,
    semantic_facts: list[SemanticFact] | None = None,
    fingerprint_coverage_report: FingerprintCoverageReport | None = None,
) -> HumanProfileReport:
    profile_summary = build_human_profile_summary(detected_patterns)
    return build_human_profile_report(
        profile_summary,
        detected_patterns,
        hypotheses=hypotheses,
        loader=loader,
        evidence_store=evidence_store,
        presenting_problem=presenting_problem,
        assessment_results=assessment_results,
        assessment_module_runs=assessment_module_runs,
        semantic_facts=semantic_facts,
        fingerprint_coverage_report=fingerprint_coverage_report,
    )


def render_human_profile_report(report: HumanProfileReport) -> str:
    sections = [
        ("Overview", report.overview),
        ("Presenting Problem", _render_presenting_problem_section(report.presenting_problem)),
    ]
    if report.assessment_signals:
        sections.append(
            (
                "Structured Assessment Signals",
                _render_assessment_signals_section(report.assessment_signals),
            )
        )
    if report.fingerprint_coverage is not None:
        sections.append(
            (
                "Human Digital Fingerprint Coverage",
                format_fingerprint_coverage_report(
                    report.fingerprint_coverage,
                    module_titles=MODULE_TITLES,
                ),
            )
        )
    sections.extend(
        [
            ("Main Observed Tendencies", _render_bullet_section(report.tendencies)),
            ("Relationship Patterns", _render_bullet_section(report.relationship_patterns)),
            ("Self-Related Patterns", _render_bullet_section(report.self_patterns)),
            ("Emotion-Related Patterns", _render_bullet_section(report.emotion_patterns)),
            ("Strengths", _render_bullet_section(report.strengths)),
            ("Vulnerabilities", _render_bullet_section(report.vulnerabilities)),
            ("Open Questions for Future Interviews", _render_bullet_section(report.open_questions)),
            ("Consistency observations", _render_bullet_section(report.consistency_observations)),
            ("Evidence Summary", _render_bullet_section(report.evidence_summary)),
        ]
    )

    rendered_sections = [
        f"{title}\n{content}"
        for title, content in sections
    ]
    return "\n\n".join(rendered_sections)


def _empty_report() -> HumanProfileReport:
    return HumanProfileReport(
        overview=NO_EVIDENCE_PROFILE_TEXT,
        strengths=[
            "There is not yet enough interview evidence to describe specific strengths.",
        ],
        open_questions=[
            "What feels most important for you to understand about yourself right now?",
        ],
        evidence_summary=[
            "No pattern-linked evidence has been collected yet.",
        ],
    )


def _ranked_pattern_ids(profile_summary: dict, detected_patterns: list[PatternTag]) -> list[str]:
    if not detected_patterns:
        return []

    ranked: list[str] = []
    primary = profile_summary.get("primary_pattern")
    if primary is not None:
        ranked.append(primary["canonical_id"])

    for pattern in profile_summary.get("secondary_patterns", []):
        canonical_id = pattern["canonical_id"]
        if canonical_id not in ranked:
            ranked.append(canonical_id)

    for tag in detected_patterns:
        if tag.canonical_id not in ranked:
            ranked.append(tag.canonical_id)

    return ranked


def _group_patterns_by_domain(
    patterns: list[KnowledgePattern],
) -> dict[str, list[KnowledgePattern]]:
    grouped = {
        RELATIONSHIPS_DOMAIN: [],
        SELF_CONCEPT_DOMAIN: [],
        EMOTION_REGULATION_DOMAIN: [],
    }
    for pattern in patterns:
        if pattern.domain in grouped:
            grouped[pattern.domain].append(pattern)
    return grouped


def _tendency_line(pattern: KnowledgePattern) -> str:
    interpretation = PATTERN_INTERPRETATIONS.get(pattern.canonical_id, GENERIC_PATTERN_TEXT)
    return f"Observed tendency ({pattern.name}): {interpretation}"


def _domain_pattern_lines(
    patterns: list[KnowledgePattern],
    pattern_counts: dict[str, int],
) -> list[str]:
    if not patterns:
        return []

    lines: list[str] = []
    for pattern in patterns:
        count = pattern_counts.get(pattern.canonical_id, 0)
        lines.append(
            f"{pattern.name} ({count} reference{'s' if count != 1 else ''}): "
            f"{pattern.behavioral_description}"
        )
    return lines


def _build_overview(
    profile_summary: dict,
    patterns: list[KnowledgePattern],
    hypotheses: list[Hypothesis],
) -> str:
    primary = profile_summary["primary_pattern"]
    assert primary is not None

    primary_pattern = patterns[0]
    overview_parts = [
        "This report summarizes observed tendencies from the interview. "
        "It is descriptive, not diagnostic.",
        (
            f"The strongest recurring theme was {primary['name']} "
            f"({primary['count']} reference{'s' if primary['count'] != 1 else ''})."
        ),
        primary_pattern.behavioral_description,
    ]

    if len(patterns) > 1:
        other_names = ", ".join(pattern.name for pattern in patterns[1:3])
        overview_parts.append(f"Additional themes also appeared, including {other_names}.")

    if hypotheses:
        hypothesis_names = ", ".join(sorted({hypothesis.canonical_id for hypothesis in hypotheses}))
        overview_parts.append(
            f"Working hypotheses under review include: {hypothesis_names}."
        )

    return " ".join(overview_parts)


def _build_strengths(
    patterns: list[KnowledgePattern],
    domain_patterns: dict[str, list[KnowledgePattern]],
) -> list[str]:
    strengths = [
        "The person described personal experience in their own words during the interview.",
    ]

    for domain, label in DOMAIN_LABELS.items():
        if not domain_patterns[domain]:
            strengths.append(f"No strong recurring evidence was noted in {label} during this interview.")

    if len(patterns) == 1:
        strengths.append(
            "Some experiences were named clearly even where a recurring theme also appeared."
        )

    return strengths


def _build_vulnerabilities(
    patterns: list[KnowledgePattern],
    pattern_counts: dict[str, int],
) -> list[str]:
    vulnerabilities: list[str] = []
    for pattern in patterns:
        count = pattern_counts.get(pattern.canonical_id, 0)
        interpretation = PATTERN_INTERPRETATIONS.get(pattern.canonical_id, GENERIC_PATTERN_TEXT)
        vulnerabilities.append(
            f"Worth gentle exploration ({pattern.name}, {count} reference"
            f"{'s' if count != 1 else ''}): {interpretation}"
        )
    return vulnerabilities


def _build_consistency_observations(
    evidence_store: EvidenceStore | None,
) -> list[str]:
    if evidence_store is None or len(evidence_store) == 0:
        return []
    issues = analyze_consistency(evidence_store)
    return format_consistency_observations(issues)


def _collect_open_questions(
    patterns: list[KnowledgePattern],
    loader: PatternLoader,
) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()

    for pattern in patterns:
        loaded = loader.load(pattern.canonical_id)
        english_questions = loaded.follow_up_questions.get("en", [])
        if not english_questions:
            continue
        question = english_questions[0]
        if question in seen:
            continue
        seen.add(question)
        questions.append(question)
        if len(questions) >= MAX_OPEN_QUESTIONS:
            break

    return questions


def _build_evidence_summary(
    detected_patterns: list[PatternTag],
    pattern_counts: dict[str, int],
) -> list[str]:
    if not detected_patterns:
        return []

    evidence_lines: list[str] = []
    seen: set[tuple[str, str]] = set()

    for tag in detected_patterns:
        key = (tag.canonical_id, tag.matched_text)
        if key in seen:
            continue
        seen.add(key)
        count = pattern_counts.get(tag.canonical_id, 0)
        evidence_lines.append(
            f"{tag.canonical_id} ({count} total reference{'s' if count != 1 else ''}): "
            f"\"{tag.matched_text}\""
        )
        if len(evidence_lines) >= MAX_EVIDENCE_ITEMS:
            break

    return evidence_lines


def _completed_assessments_from_module_runs(
    assessment_module_runs: list[AssessedModuleRun] | None,
) -> dict[str, list[AssessmentResult]]:
    if not assessment_module_runs:
        return {}
    return {run.module_id: list(run.results) for run in assessment_module_runs}


def _build_fingerprint_coverage(
    *,
    presenting_problem: dict[str, str],
    detected_patterns: list[PatternTag],
    semantic_facts: list[SemanticFact] | None,
    assessment_module_runs: list[AssessedModuleRun] | None,
    fingerprint_coverage_report: FingerprintCoverageReport | None,
) -> FingerprintCoverageReport:
    if fingerprint_coverage_report is not None:
        return fingerprint_coverage_report
    return FingerprintCoverageAnalyzer().analyze(
        presenting_problem=presenting_problem,
        patterns=detected_patterns,
        semantic_facts=semantic_facts,
        completed_assessments=_completed_assessments_from_module_runs(assessment_module_runs),
    )


def _build_assessment_signals(
    assessment_results: list[AssessmentResult] | None,
    assessment_module_runs: list[AssessedModuleRun] | None = None,
) -> list[str]:
    if assessment_module_runs:
        lines: list[str] = []
        for run in assessment_module_runs:
            title = MODULE_TITLES.get(run.module_id, run.module_id)
            lines.append(f"{title}:")
            for result in sorted(run.results, key=lambda item: item.domain_id):
                lines.append(format_assessment_signal(result, module_id=run.module_id))
        return lines

    if not assessment_results:
        return []
    return [format_assessment_signal(result) for result in assessment_results]


def _render_assessment_signals_section(items: list[str]) -> str:
    if not items:
        return "- None noted yet."

    rendered: list[str] = []
    for item in items:
        if item.endswith(":"):
            rendered.append(item)
        else:
            rendered.append(f"- {item}")
    return "\n".join(rendered)


def _render_bullet_section(items: list[str]) -> str:
    if not items:
        return "- None noted yet."
    return "\n".join(f"- {item}" for item in items)


def _render_presenting_problem_section(presenting_problem: dict[str, str]) -> str:
    labels = {
        "main_problem": "Main problem",
        "duration": "Duration",
        "perceived_causes": "Perceived causes",
        "current_impact": "Current impact",
        "previous_attempts": "Previous attempts",
        "desired_outcome": "Desired outcome",
    }
    if not presenting_problem:
        return "- None noted yet."

    lines: list[str] = []
    for key, label in labels.items():
        value = presenting_problem.get(key, "").strip()
        if value:
            lines.append(f"- {label}: {value}")

    if not lines:
        return "- None noted yet."
    return "\n".join(lines)
