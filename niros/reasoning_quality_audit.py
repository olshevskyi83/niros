"""Deterministic reasoning-quality audit for NIROS synthetic human profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageReport,
    PATTERN_DOMAIN_HINTS,
)
from niros.intervention_strategy import (
    InterventionStrategy,
    is_high_grounding,
)
from niros.knowledge import PatternLoader
from niros.scenario_blueprint import ScenarioBlueprint

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(is|e|ed|ing)?|disorder|patholog|clinical syndrome|bipolar|"
    r"ptsd|narcissistic personality|borderline personality)\b",
    re.IGNORECASE,
)

NON_DIAGNOSTIC_DISCLAIMERS = (
    "descriptive, not diagnostic",
    "non-diagnostic",
    "without niros assigning a diagnosis",
    "without clinical diagnosis or naming a disorder",
    "not a diagnosis",
    "no diagnosis",
    "naming a disorder",
    "not diagnoses",
)

KB_DOMAIN_TO_FINGERPRINT_FRAGMENTS: dict[str, tuple[str, ...]] = {
    "emotion_regulation": ("emotion_regulation", "low_mood"),
    "relationships": ("relationships",),
    "self_concept": ("self_domain", "self-worth", "self"),
    "meaning_direction": ("meaning", "values_identity", "values"),
    "trauma_stress": ("trauma", "stress"),
    "body_pain": ("pain", "fatigue", "chronic_pain"),
    "fear_safety_distress": ("anxiety", "fear", "panic", "safety"),
    "session_concerns": ("psychedelic", "session"),
    "speech_communication": ("speech", "expression", "stutter"),
}

_BASE_INTAKE_TAIL = {
    "duration": "several months",
    "perceived_causes": "ongoing stress and inner struggle",
    "current_impact": "daily emotional burden and reduced functioning",
    "previous_attempts": "talking with friends and journaling",
    "desired_outcome": "understand myself better and feel more stable",
}

OVERALL_WEIGHTS = {
    "coverage": 0.25,
    "consistency": 0.20,
    "strategy_coherence": 0.20,
    "scenario_coherence": 0.20,
    "timeline_coherence": 0.15,
}


@dataclass(frozen=True)
class ReasoningQualityScores:
    coverage_score: float
    consistency_score: float
    strategy_coherence_score: float
    scenario_coherence_score: float
    timeline_coherence_score: float
    overall_human_understanding_score: float


@dataclass
class ReasoningQualityReport:
    case_id: str
    case_path: str
    is_complex: bool
    detected_patterns: set[str]
    expected_patterns: list[str]
    missed_patterns: tuple[str, ...]
    over_assumed_patterns: tuple[str, ...]
    scores: ReasoningQualityScores
    findings: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class ReasoningAuditArtifacts:
    case_path: Path
    detected_pattern_ids: set[str]
    coverage_report: FingerprintCoverageReport
    fingerprint: dict
    strategy: InterventionStrategy
    blueprint: ScenarioBlueprint
    report_text: str
    strategy_text: str
    blueprint_text: str
    timeline_text: str
    completed_modules: list[str]
    selected_modules: list[str]
    expected_patterns: list[str]
    expected_weak_domains: list[str]
    expected_assessments: list[str]
    expected_strategy_focus: list[str]
    expected_scenario_themes: list[str]
    expected_timeline_characteristics: list[str]
    is_complex: bool


def load_scenario_text(markdown_path: Path) -> str:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    in_scenario = False
    scenario_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == "# Scenario":
            in_scenario = True
            continue
        if in_scenario and stripped.startswith("# "):
            break
        if in_scenario and stripped:
            scenario_lines.append(stripped)

    return " ".join(scenario_lines)


def load_bullet_section(markdown_path: Path, heading: str) -> list[str]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    in_section = False
    items: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == f"# {heading}":
            in_section = True
            continue
        if in_section and stripped.startswith("# "):
            break
        if in_section and stripped.startswith("- "):
            items.append(stripped[2:].strip())

    return items


def load_profile_meta_title(markdown_path: Path) -> str | None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    in_meta = False
    for line in lines:
        stripped = line.strip()
        if stripped == "# Profile Meta":
            in_meta = True
            continue
        if in_meta and stripped.startswith("# "):
            break
        if in_meta and stripped.startswith("- title:"):
            return stripped.split(":", 1)[1].strip()
    return None


def build_intake_for_case(case_path: Path, scenario: str) -> dict[str, str]:
    title = load_profile_meta_title(case_path)
    presenting = title or scenario[:240]
    return {
        "presenting_problem": presenting,
        **_BASE_INTAKE_TAIL,
    }


def discover_synthetic_profile_paths(test_cases_dir: Path) -> list[Path]:
    simple = sorted(test_cases_dir.glob("[0-9]*.md"))
    complex_dir = test_cases_dir / "complex"
    complex_cases = sorted(complex_dir.glob("c*.md")) if complex_dir.is_dir() else []
    return simple + complex_cases


def audit_reasoning_quality(artifacts: ReasoningAuditArtifacts) -> ReasoningQualityReport:
    missed = _missed_patterns(artifacts)
    over_assumed = _over_assumed_patterns(artifacts)

    coverage = _coverage_score(artifacts, missed)
    consistency = _consistency_score(artifacts, over_assumed)
    strategy = _strategy_coherence_score(artifacts)
    scenario = _scenario_coherence_score(artifacts)
    timeline = _timeline_coherence_score(artifacts)

    overall = (
        coverage * OVERALL_WEIGHTS["coverage"]
        + consistency * OVERALL_WEIGHTS["consistency"]
        + strategy * OVERALL_WEIGHTS["strategy_coherence"]
        + scenario * OVERALL_WEIGHTS["scenario_coherence"]
        + timeline * OVERALL_WEIGHTS["timeline_coherence"]
    )

    scores = ReasoningQualityScores(
        coverage_score=round(coverage, 4),
        consistency_score=round(consistency, 4),
        strategy_coherence_score=round(strategy, 4),
        scenario_coherence_score=round(scenario, 4),
        timeline_coherence_score=round(timeline, 4),
        overall_human_understanding_score=round(overall, 4),
    )

    return ReasoningQualityReport(
        case_id=artifacts.case_path.stem,
        case_path=str(artifacts.case_path),
        is_complex=artifacts.is_complex,
        detected_patterns=artifacts.detected_pattern_ids,
        expected_patterns=artifacts.expected_patterns,
        missed_patterns=missed,
        over_assumed_patterns=over_assumed,
        scores=scores,
        findings=_build_findings(artifacts, missed, over_assumed, scores),
    )


def _missed_patterns(artifacts: ReasoningAuditArtifacts) -> tuple[str, ...]:
    if not artifacts.expected_patterns:
        return ()
    return tuple(
        pattern_id
        for pattern_id in artifacts.expected_patterns
        if pattern_id not in artifacts.detected_pattern_ids
    )


def _fingerprint_fragments_for_patterns(pattern_ids: set[str]) -> set[str]:
    fragments: set[str] = set()
    loader = PatternLoader()
    for pattern_id in pattern_ids:
        hints = PATTERN_DOMAIN_HINTS.get(pattern_id, ())
        for domain_id, _weight in hints:
            fragments.add(domain_id)
        try:
            kb_domain = loader.load(pattern_id).domain
        except FileNotFoundError:
            continue
        for fragment in KB_DOMAIN_TO_FINGERPRINT_FRAGMENTS.get(kb_domain, (kb_domain,)):
            fragments.add(fragment)
    return fragments


def _over_assumed_patterns(artifacts: ReasoningAuditArtifacts) -> tuple[str, ...]:
    if not artifacts.expected_patterns:
        return ()

    expected_set = set(artifacts.expected_patterns)
    unexpected = artifacts.detected_pattern_ids - expected_set
    if not unexpected:
        return ()

    allowed_fragments = _fingerprint_fragments_for_patterns(expected_set)
    over_assumed: list[str] = []
    loader = PatternLoader()

    for pattern_id in sorted(unexpected):
        related = False
        for domain_id, _weight in PATTERN_DOMAIN_HINTS.get(pattern_id, ()):
            if any(fragment in domain_id for fragment in allowed_fragments):
                related = True
                break
        if related:
            continue
        try:
            kb_domain = loader.load(pattern_id).domain
        except FileNotFoundError:
            over_assumed.append(pattern_id)
            continue
        kb_fragments = KB_DOMAIN_TO_FINGERPRINT_FRAGMENTS.get(kb_domain, (kb_domain,))
        if any(
            any(allowed in fragment or fragment in allowed for allowed in allowed_fragments)
            for fragment in kb_fragments
        ):
            continue
        over_assumed.append(pattern_id)

    return tuple(over_assumed)


def _coverage_score(artifacts: ReasoningAuditArtifacts, missed: tuple[str, ...]) -> float:
    components: list[float] = []

    if artifacts.expected_patterns:
        hit = len(artifacts.expected_patterns) - len(missed)
        components.append(hit / len(artifacts.expected_patterns))
    else:
        components.append(1.0 if artifacts.detected_pattern_ids else 0.0)

    if artifacts.expected_weak_domains:
        weak_hits = sum(
            1
            for domain in artifacts.expected_weak_domains
            if _domain_is_weak(artifacts.coverage_report, domain)
        )
        components.append(weak_hits / len(artifacts.expected_weak_domains))
    elif artifacts.is_complex:
        components.append(0.0)
    else:
        components.append(1.0 if artifacts.coverage_report.missing_domains else 0.5)

    if artifacts.expected_assessments:
        assessment_hits = sum(
            1
            for module in artifacts.expected_assessments
            if _modules_include(artifacts.completed_modules, module)
            or _modules_include(artifacts.selected_modules, module)
        )
        components.append(assessment_hits / len(artifacts.expected_assessments))
    elif artifacts.is_complex:
        components.append(0.0)
    else:
        components.append(1.0 if artifacts.completed_modules else 0.5)

    if artifacts.expected_patterns:
        evidenced = any(
            _pattern_evidenced_in_coverage(artifacts.coverage_report, pattern_id)
            for pattern_id in artifacts.expected_patterns
            if pattern_id in artifacts.detected_pattern_ids
        )
        components.append(1.0 if evidenced else 0.0)
    else:
        components.append(1.0 if artifacts.detected_pattern_ids else 0.0)

    return sum(components) / len(components)


def _consistency_score(
    artifacts: ReasoningAuditArtifacts,
    over_assumed: tuple[str, ...],
) -> float:
    checks: list[float] = []

    summary = artifacts.fingerprint.get("summary_text", "")
    checks.append(1.0 if summary.strip() else 0.0)

    pattern_counts = artifacts.fingerprint.get("patterns", {}).get("pattern_counts", {})
    if artifacts.detected_pattern_ids:
        aligned = sum(
            1 for pattern_id in artifacts.detected_pattern_ids if pattern_id in pattern_counts
        )
        checks.append(aligned / len(artifacts.detected_pattern_ids))
    else:
        checks.append(0.0)

    combined_text = "\n".join(
        (
            artifacts.report_text,
            artifacts.strategy_text,
            artifacts.blueprint_text,
            artifacts.timeline_text,
            summary,
        )
    )
    checks.append(0.0 if _contains_diagnosis_language(combined_text) else 1.0)

    if artifacts.expected_patterns:
        checks.append(max(0.0, 1.0 - len(over_assumed) / max(len(artifacts.expected_patterns), 1)))
    else:
        checks.append(max(0.0, 1.0 - len(over_assumed) * 0.15))

    profile_patterns = set(pattern_counts.keys())
    if profile_patterns == artifacts.detected_pattern_ids:
        checks.append(1.0)
    elif profile_patterns & artifacts.detected_pattern_ids:
        checks.append(0.5)
    else:
        checks.append(0.0)

    return sum(checks) / len(checks)


def _strategy_coherence_score(artifacts: ReasoningAuditArtifacts) -> float:
    strategy = artifacts.strategy
    checks: list[float] = []

    if is_high_grounding(strategy.grounding_priority):
        checks.append(1.0 if strategy.pacing == "slow" else 0.5)
        checks.append(1.0 if strategy.cognitive_load == "low" else 0.5)
    else:
        checks.append(1.0 if strategy.pacing in {"slow", "moderate", "brisk"} else 0.0)
        checks.append(1.0 if strategy.cognitive_load in {"low", "medium", "high"} else 0.0)

    if strategy.focus_confidence:
        checks.append(1.0)
        if artifacts.expected_strategy_focus:
            focus_hits = sum(
                1
                for item in artifacts.expected_strategy_focus
                if _theme_matches(artifacts.strategy_text, item)
                or _focus_area_matches(strategy, item)
            )
            checks.append(focus_hits / len(artifacts.expected_strategy_focus))
        else:
            detected_fragments = _fingerprint_fragments_for_patterns(artifacts.detected_pattern_ids)
            derived_hits = sum(
                1
                for focus in strategy.focus_confidence
                if any(fragment in focus.focus_area.lower() for fragment in detected_fragments)
                or focus.focus_area == "presenting context"
            )
            checks.append(
                min(1.0, derived_hits / max(len(strategy.focus_confidence), 1))
            )
    else:
        checks.append(0.0)

    if artifacts.expected_weak_domains and strategy.focus_confidence:
        weak_focus_hits = 0
        for domain in artifacts.expected_weak_domains:
            for focus in strategy.focus_confidence:
                if _domain_matches_focus(domain, focus.focus_area):
                    if focus.confidence in {"low", "medium"}:
                        weak_focus_hits += 1
                        break
        checks.append(weak_focus_hits / len(artifacts.expected_weak_domains))
    elif artifacts.is_complex:
        checks.append(0.5)
    else:
        checks.append(1.0 if strategy.coverage_summary is not None else 0.5)

    return sum(checks) / len(checks)


def _scenario_coherence_score(artifacts: ReasoningAuditArtifacts) -> float:
    blueprint = artifacts.blueprint
    checks: list[float] = []

    checks.append(1.0 if blueprint.opening_phase.objective else 0.0)
    checks.append(1.0 if blueprint.integration_phase.objective else 0.0)

    detected = artifacts.detected_pattern_ids
    if detected:
        targeted = {
            pattern_id
            for phase in blueprint.exploration_phases
            for pattern_id in phase.target_patterns
        }
        overlap = len(detected & targeted)
        checks.append(min(1.0, overlap / max(min(len(detected), 3), 1)))
    else:
        checks.append(0.0)

    if artifacts.expected_scenario_themes:
        theme_hits = sum(
            1 for theme in artifacts.expected_scenario_themes if _theme_matches(artifacts.blueprint_text, theme)
        )
        checks.append(theme_hits / len(artifacts.expected_scenario_themes))
    elif blueprint.confidence_phases:
        checks.append(1.0)
    else:
        checks.append(0.5)

    if blueprint.confidence_phases and artifacts.strategy.focus_confidence:
        strategy_focus = {item.focus_area for item in artifacts.strategy.focus_confidence}
        blueprint_focus = {phase.focus for phase in blueprint.confidence_phases}
        overlap = len(strategy_focus & blueprint_focus)
        checks.append(
            overlap / max(len(strategy_focus | blueprint_focus), 1)
        )
    else:
        checks.append(0.5 if artifacts.strategy.focus_confidence else 0.0)

    return sum(checks) / len(checks)


def _timeline_coherence_score(artifacts: ReasoningAuditArtifacts) -> float:
    timeline_text = artifacts.timeline_text.lower()
    checks: list[float] = []

    checks.append(0.0 if "no session events" in timeline_text else 1.0)
    checks.append(1.0 if "opening" in timeline_text else 0.0)
    checks.append(1.0 if "integration" in timeline_text or "closing" in timeline_text else 0.0)

    if artifacts.expected_timeline_characteristics:
        timeline_hits = sum(
            1
            for item in artifacts.expected_timeline_characteristics
            if _theme_matches(timeline_text, item)
            or _theme_matches(artifacts.strategy_text, item)
        )
        checks.append(timeline_hits / len(artifacts.expected_timeline_characteristics))
    else:
        if is_high_grounding(artifacts.strategy.grounding_priority):
            checks.append(1.0 if "stabil" in timeline_text or "opening" in timeline_text else 0.5)
        else:
            checks.append(0.75)

    duration_match = re.search(r"total duration:\s*(\d+)\s*min", timeline_text)
    if duration_match:
        timeline_minutes = int(duration_match.group(1))
        delta = abs(timeline_minutes - artifacts.strategy.suggested_duration)
        checks.append(1.0 if delta <= 15 else 0.5 if delta <= 25 else 0.0)
    else:
        checks.append(0.0)

    return sum(checks) / len(checks)


def _build_findings(
    artifacts: ReasoningAuditArtifacts,
    missed: tuple[str, ...],
    over_assumed: tuple[str, ...],
    scores: ReasoningQualityScores,
) -> tuple[str, ...]:
    findings: list[str] = []

    if missed:
        findings.append(f"Missed expected themes: {', '.join(missed)}")
    if over_assumed:
        findings.append(f"Possible over-assumption: {', '.join(over_assumed)}")
    if scores.coverage_score < 0.7:
        findings.append("Coverage below target — NIROS may not fully understand salient themes.")
    if scores.consistency_score < 0.7:
        findings.append("Fingerprint or output consistency needs review.")
    if scores.strategy_coherence_score < 0.7:
        findings.append("Session strategy may not follow logically from fingerprint coverage.")
    if scores.scenario_coherence_score < 0.7:
        findings.append("Scenario blueprint may not align with strategy and detected patterns.")
    if scores.timeline_coherence_score < 0.7:
        findings.append("Session timeline may not reflect strategy pacing and themes.")
    if not findings:
        findings.append("Reasoning chain appears coherent for this profile.")
    return tuple(findings)


def _domain_is_weak(coverage_report: FingerprintCoverageReport, fragment: str) -> bool:
    missing = set(coverage_report.missing_domains)
    if any(fragment in domain_id for domain_id in missing):
        return True
    for domain_id, domain in coverage_report.domains.items():
        if fragment in domain_id and domain.level in {COVERAGE_LEVEL_UNKNOWN, COVERAGE_LEVEL_PARTIAL}:
            return True
    return False


def _pattern_evidenced_in_coverage(
    coverage_report: FingerprintCoverageReport,
    pattern_id: str,
) -> bool:
    for domain_id, _weight in PATTERN_DOMAIN_HINTS.get(pattern_id, ()):
        domain = coverage_report.domains.get(domain_id)
        if domain is not None and domain.level not in {COVERAGE_LEVEL_UNKNOWN}:
            return True
    return coverage_report.domains.get("patterns", None) is not None


def _modules_include(module_ids: list[str], fragment: str) -> bool:
    return any(fragment in module_id for module_id in module_ids)


def _contains_diagnosis_language(text: str) -> bool:
    lowered = text.lower()
    for phrase in NON_DIAGNOSTIC_DISCLAIMERS:
        lowered = lowered.replace(phrase, "")
    return DIAGNOSIS_PATTERN.search(lowered) is not None


def _theme_matches(text: str, theme: str) -> bool:
    normalized = theme.lower().replace("/", " ").replace("-", " ")
    tokens = [token for token in re.split(r"\s+", normalized) if len(token) > 2]
    if not tokens:
        return True
    haystack = text.lower()
    hits = sum(1 for token in tokens if token in haystack)
    required = max(1, (len(tokens) + 1) // 2)
    return hits >= required


def _focus_area_matches(strategy: InterventionStrategy, expected_focus: str) -> bool:
    expected = expected_focus.lower()
    for item in strategy.focus_confidence:
        if expected in item.focus_area.lower() or item.focus_area.lower() in expected:
            return True
    return False


def _domain_matches_focus(domain_fragment: str, focus_area: str) -> bool:
    domain = domain_fragment.lower().replace("_domain", "").replace("_", " ")
    focus = focus_area.lower()
    return domain in focus or focus in domain or any(
        token in focus for token in domain.split() if len(token) > 3
    )
