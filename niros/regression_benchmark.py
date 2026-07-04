"""Stored regression benchmark for NIROS quality gating."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BENCHMARK_VERSION = 1
METRIC_TOLERANCE = 0.001


@dataclass(frozen=True)
class RegressionMetrics:
    patterns: float
    coverage: float
    strategy: float
    scenario: float
    timeline: float

    def as_dict(self) -> dict[str, float]:
        return {
            "patterns": round(self.patterns, 4),
            "coverage": round(self.coverage, 4),
            "strategy": round(self.strategy, 4),
            "scenario": round(self.scenario, 4),
            "timeline": round(self.timeline, 4),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RegressionMetrics:
        return cls(
            patterns=float(payload["patterns"]),
            coverage=float(payload["coverage"]),
            strategy=float(payload["strategy"]),
            scenario=float(payload["scenario"]),
            timeline=float(payload["timeline"]),
        )


@dataclass(frozen=True)
class RegressionCaseRecord:
    suite: str
    case_id: str
    language: str
    metrics: RegressionMetrics
    detected_patterns: tuple[str, ...]
    missing_domains: tuple[str, ...]
    completed_modules: tuple[str, ...]
    selected_modules: tuple[str, ...]
    strategy_fingerprint: str
    scenario_fingerprint: str
    timeline_fingerprint: str

    @property
    def case_key(self) -> str:
        if self.language and self.language != "en":
            return f"{self.suite}:{self.case_id}:{self.language}"
        return f"{self.suite}:{self.case_id}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "case_id": self.case_id,
            "language": self.language,
            "metrics": self.metrics.as_dict(),
            "detected_patterns": list(self.detected_patterns),
            "missing_domains": list(self.missing_domains),
            "completed_modules": list(self.completed_modules),
            "selected_modules": list(self.selected_modules),
            "strategy_fingerprint": self.strategy_fingerprint,
            "scenario_fingerprint": self.scenario_fingerprint,
            "timeline_fingerprint": self.timeline_fingerprint,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RegressionCaseRecord:
        return cls(
            suite=str(payload["suite"]),
            case_id=str(payload["case_id"]),
            language=str(payload.get("language", "en")),
            metrics=RegressionMetrics.from_dict(payload["metrics"]),
            detected_patterns=tuple(payload.get("detected_patterns", ())),
            missing_domains=tuple(payload.get("missing_domains", ())),
            completed_modules=tuple(payload.get("completed_modules", ())),
            selected_modules=tuple(payload.get("selected_modules", ())),
            strategy_fingerprint=str(payload.get("strategy_fingerprint", "")),
            scenario_fingerprint=str(payload.get("scenario_fingerprint", "")),
            timeline_fingerprint=str(payload.get("timeline_fingerprint", "")),
        )


@dataclass
class RegressionBenchmark:
    version: int
    generated_at: str
    cases: dict[str, RegressionCaseRecord] = field(default_factory=dict)
    suite_means: dict[str, dict[str, float]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "suite_means": self.suite_means,
            "cases": {key: record.as_dict() for key, record in sorted(self.cases.items())},
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RegressionBenchmark:
        cases = {
            key: RegressionCaseRecord.from_dict(value)
            for key, value in payload.get("cases", {}).items()
        }
        return cls(
            version=int(payload.get("version", BENCHMARK_VERSION)),
            generated_at=str(payload.get("generated_at", "")),
            cases=cases,
            suite_means={
                suite: {metric: float(value) for metric, value in means.items()}
                for suite, means in payload.get("suite_means", {}).items()
            },
        )


@dataclass(frozen=True)
class RegressionViolation:
    case_key: str
    dimension: str
    baseline: float | str | tuple[str, ...]
    current: float | str | tuple[str, ...]
    message: str


def text_fingerprint(text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_regression_metrics(
    *,
    expected_patterns: list[str],
    detected_patterns: set[str],
    coverage_score: float,
    strategy_score: float,
    scenario_score: float,
    timeline_score: float,
) -> RegressionMetrics:
    if expected_patterns:
        expected_set = set(expected_patterns)
        patterns_score = len(expected_set & detected_patterns) / len(expected_set)
    else:
        patterns_score = 1.0 if detected_patterns else 0.0

    return RegressionMetrics(
        patterns=patterns_score,
        coverage=coverage_score,
        strategy=strategy_score,
        scenario=scenario_score,
        timeline=timeline_score,
    )


def build_case_record(
    *,
    suite: str,
    case_id: str,
    language: str,
    metrics: RegressionMetrics,
    detected_patterns: set[str],
    missing_domains: list[str],
    completed_modules: list[str],
    selected_modules: list[str],
    strategy_text: str,
    blueprint_text: str,
    timeline_text: str,
) -> RegressionCaseRecord:
    return RegressionCaseRecord(
        suite=suite,
        case_id=case_id,
        language=language,
        metrics=metrics,
        detected_patterns=tuple(sorted(detected_patterns)),
        missing_domains=tuple(missing_domains),
        completed_modules=tuple(completed_modules),
        selected_modules=tuple(selected_modules),
        strategy_fingerprint=text_fingerprint(strategy_text),
        scenario_fingerprint=text_fingerprint(blueprint_text),
        timeline_fingerprint=text_fingerprint(timeline_text),
    )


def aggregate_suite_means(records: dict[str, RegressionCaseRecord]) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[RegressionMetrics]] = {}
    for record in records.values():
        buckets.setdefault(record.suite, []).append(record.metrics)

    suite_means: dict[str, dict[str, float]] = {}
    for suite, metrics_list in buckets.items():
        count = len(metrics_list)
        if count == 0:
            continue
        suite_means[suite] = {
            "patterns": round(sum(item.patterns for item in metrics_list) / count, 4),
            "coverage": round(sum(item.coverage for item in metrics_list) / count, 4),
            "strategy": round(sum(item.strategy for item in metrics_list) / count, 4),
            "scenario": round(sum(item.scenario for item in metrics_list) / count, 4),
            "timeline": round(sum(item.timeline for item in metrics_list) / count, 4),
        }
    return suite_means


def build_benchmark(records: dict[str, RegressionCaseRecord]) -> RegressionBenchmark:
    return RegressionBenchmark(
        version=BENCHMARK_VERSION,
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        cases=records,
        suite_means=aggregate_suite_means(records),
    )


def load_benchmark(path: Path) -> RegressionBenchmark:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RegressionBenchmark.from_dict(payload)


def save_benchmark(path: Path, benchmark: RegressionBenchmark) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(benchmark.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def compare_benchmarks(
    baseline: RegressionBenchmark,
    current: RegressionBenchmark,
) -> list[RegressionViolation]:
    violations: list[RegressionViolation] = []

    missing_cases = set(baseline.cases) - set(current.cases)
    for case_key in sorted(missing_cases):
        violations.append(
            RegressionViolation(
                case_key=case_key,
                dimension="case",
                baseline="present",
                current="missing",
                message="Benchmark case missing from current run.",
            )
        )

    for case_key, baseline_record in baseline.cases.items():
        current_record = current.cases.get(case_key)
        if current_record is None:
            continue

        for dimension in ("patterns", "coverage", "strategy", "scenario", "timeline"):
            baseline_value = getattr(baseline_record.metrics, dimension)
            current_value = getattr(current_record.metrics, dimension)
            if current_value + METRIC_TOLERANCE < baseline_value:
                violations.append(
                    RegressionViolation(
                        case_key=case_key,
                        dimension=dimension,
                        baseline=baseline_value,
                        current=current_value,
                        message=(
                            f"{dimension} regressed "
                            f"({baseline_value:.4f} -> {current_value:.4f})."
                        ),
                    )
                )

        lost_patterns = set(baseline_record.detected_patterns) - set(current_record.detected_patterns)
        if lost_patterns:
            violations.append(
                RegressionViolation(
                    case_key=case_key,
                    dimension="patterns",
                    baseline=tuple(sorted(lost_patterns)),
                    current=tuple(sorted(current_record.detected_patterns)),
                    message=f"Lost previously detected patterns: {', '.join(sorted(lost_patterns))}.",
                )
            )

        if len(current_record.missing_domains) > len(baseline_record.missing_domains):
            violations.append(
                RegressionViolation(
                    case_key=case_key,
                    dimension="coverage",
                    baseline=len(baseline_record.missing_domains),
                    current=len(current_record.missing_domains),
                    message="Coverage gaps increased versus benchmark.",
                )
            )

    for suite, baseline_means in baseline.suite_means.items():
        current_means = current.suite_means.get(suite)
        if current_means is None:
            violations.append(
                RegressionViolation(
                    case_key=f"suite:{suite}",
                    dimension="suite",
                    baseline="present",
                    current="missing",
                    message=f"Suite '{suite}' missing from current benchmark.",
                )
            )
            continue
        for dimension, baseline_value in baseline_means.items():
            current_value = current_means.get(dimension, 0.0)
            if current_value + METRIC_TOLERANCE < baseline_value:
                violations.append(
                    RegressionViolation(
                        case_key=f"suite:{suite}",
                        dimension=dimension,
                        baseline=baseline_value,
                        current=current_value,
                        message=(
                            f"Suite '{suite}' mean {dimension} regressed "
                            f"({baseline_value:.4f} -> {current_value:.4f})."
                        ),
                    )
                )

    return violations


def format_violations(violations: list[RegressionViolation]) -> str:
    if not violations:
        return "No regression violations."

    lines = ["NIROS regression benchmark violations:"]
    for violation in violations:
        lines.append(f"- [{violation.case_key}] {violation.message}")
    return "\n".join(lines)
