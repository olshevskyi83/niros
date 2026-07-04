from __future__ import annotations

from dataclasses import dataclass, field

from niros.assessment import AssessmentResult
from niros.assessment_domain_map import AssessmentDomain, build_assessment_domain_map
from niros.fingerprint_coverage import (
    FingerprintCoverageAnalyzer,
    FingerprintCoverageReport,
    MODULE_DOMAIN_COVERAGE,
    render_fingerprint_coverage_report,
)
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact

BIG_FIVE_SHORT = "big-five-short"
LOW_MOOD_SHORT = "low-mood-short"
ANXIETY_SHORT = "anxiety-short"
SLEEP_SHORT = "sleep-short"
TRAUMA_STRESS_SHORT = "trauma-stress-short"
GRIEF_LOSS_SHORT = "grief-loss-short"
SUBSTANCE_USE_SHORT = "substance-use-short"
BEHAVIORAL_ADDICTION_SHORT = "behavioral-addiction-short"
PAIN_FATIGUE_SHORT = "pain-fatigue-short"
SPEECH_ANXIETY_SHORT = "speech-anxiety-short"
PSYCHEDELIC_CONCERN_SHORT = "psychedelic-concern-short"
MEANING_PURPOSE_SHORT = "meaning-purpose-short"
SELF_DOMAIN_SHORT = "self-domain-short"
EMOTION_REGULATION_DOMAIN_SHORT = "emotion-regulation-domain-short"
COGNITIVE_PATTERNS_DOMAIN_SHORT = "cognitive-patterns-domain-short"
RELATIONSHIPS_DOMAIN_SHORT = "relationships-domain-short"
VALUES_IDENTITY_DOMAIN_SHORT = "values-identity-domain-short"
EMOTIONAL_FLEXIBILITY_DOMAIN_SHORT = "emotional-flexibility-domain-short"

ALL_ASSESSMENT_MODULE_IDS: tuple[str, ...] = tuple(sorted(MODULE_DOMAIN_COVERAGE))

DEFAULT_MAX_MODULES = 4


@dataclass
class AssessmentSelection:
    selected_modules: list[str] = field(default_factory=list)
    reason_by_module: dict[str, str] = field(default_factory=dict)
    skipped_modules: list[str] = field(default_factory=list)
    coverage_report: FingerprintCoverageReport | None = None


def select_assessment_modules(
    presenting_problem: dict[str, str],
    detected_patterns: list[str] | list[PatternTag],
    assessment_domain_map: dict[str, AssessmentDomain] | None = None,
    *,
    semantic_facts: list[SemanticFact] | None = None,
    completed_assessments: dict[str, list[AssessmentResult]] | None = None,
    max_modules: int = DEFAULT_MAX_MODULES,
) -> AssessmentSelection:
    _ = assessment_domain_map or build_assessment_domain_map()

    report = FingerprintCoverageAnalyzer().analyze(
        presenting_problem=presenting_problem,
        patterns=detected_patterns,
        semantic_facts=semantic_facts,
        completed_assessments=completed_assessments,
        max_modules=max_modules,
    )

    skipped_modules = [
        module_id for module_id in ALL_ASSESSMENT_MODULE_IDS if module_id not in report.selected_modules
    ]

    return AssessmentSelection(
        selected_modules=list(report.selected_modules),
        reason_by_module=dict(report.reason_by_module),
        skipped_modules=skipped_modules,
        coverage_report=report,
    )


def render_assessment_selection_with_coverage(
    selection: AssessmentSelection,
    *,
    module_titles: dict[str, str] | None = None,
) -> str:
    lines: list[str] = []
    if selection.coverage_report is not None:
        lines.append(
            render_fingerprint_coverage_report(
                selection.coverage_report,
                module_titles=module_titles,
            )
        )
        lines.append("")

    lines.append("=== Adaptive Assessment Selection ===")
    lines.append("Selected modules:")
    for module_id in selection.selected_modules:
        title = (module_titles or {}).get(module_id, module_id)
        reason = selection.reason_by_module.get(module_id, "selected for fingerprint coverage")
        lines.append(f"- {title}: {reason}")

    return "\n".join(lines)
