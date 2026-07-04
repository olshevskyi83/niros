"""NIROS regression benchmark quality gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from niros.regression_benchmark import (
    build_benchmark,
    compare_benchmarks,
    format_violations,
    load_benchmark,
    save_benchmark,
)
from regression_benchmark_runners import collect_all_regression_records

BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "regression_benchmark.json"
UPDATE_ENV_VAR = "NIROS_UPDATE_REGRESSION_BENCHMARK"

EXPECTED_SUITE_COUNTS = {
    "pattern_matrix": 12,
    "pseudo_human": 5,
    "multilingual": 48,
    "complex_human": 30,
}


@pytest.fixture(scope="module")
def current_regression_benchmark():
    records = collect_all_regression_records()
    return build_benchmark(records)


def test_regression_benchmark_collects_all_suites(current_regression_benchmark):
    suite_counts: dict[str, int] = {}
    for record in current_regression_benchmark.cases.values():
        suite_counts[record.suite] = suite_counts.get(record.suite, 0) + 1

    assert sum(suite_counts.values()) == sum(EXPECTED_SUITE_COUNTS.values())
    for suite, expected_count in EXPECTED_SUITE_COUNTS.items():
        assert suite_counts.get(suite, 0) == expected_count, suite


def test_regression_benchmark_matches_stored_baseline(current_regression_benchmark):
    if os.environ.get(UPDATE_ENV_VAR) == "1":
        save_benchmark(BENCHMARK_PATH, current_regression_benchmark)
        pytest.skip(f"Updated regression benchmark at {BENCHMARK_PATH}")

    assert BENCHMARK_PATH.is_file(), (
        f"Missing stored benchmark at {BENCHMARK_PATH}. "
        f"Run NIROS_UPDATE_REGRESSION_BENCHMARK=1 pytest tests/test_regression_benchmark.py "
        "to generate it."
    )

    baseline = load_benchmark(BENCHMARK_PATH)
    violations = compare_benchmarks(baseline, current_regression_benchmark)
    assert not violations, format_violations(violations)


def test_regression_benchmark_suite_means_are_stable(current_regression_benchmark):
    if os.environ.get(UPDATE_ENV_VAR) == "1":
        pytest.skip("benchmark update mode")

    baseline = load_benchmark(BENCHMARK_PATH)
    for suite, means in baseline.suite_means.items():
        current_means = current_regression_benchmark.suite_means.get(suite)
        assert current_means is not None, f"Missing suite means for {suite}"
        for dimension, baseline_value in means.items():
            current_value = current_means[dimension]
            assert current_value + 0.001 >= baseline_value, (
                f"Suite {suite} mean {dimension} regressed "
                f"({baseline_value:.4f} -> {current_value:.4f})"
            )


def test_regression_benchmark_summary(current_regression_benchmark, capsys):
    print("\n=== NIROS Regression Benchmark Gate ===")
    print(f"cases: {len(current_regression_benchmark.cases)}")
    for suite in EXPECTED_SUITE_COUNTS:
        means = current_regression_benchmark.suite_means.get(suite, {})
        print(
            f"{suite}: "
            f"patterns={means.get('patterns', 0):.3f} "
            f"coverage={means.get('coverage', 0):.3f} "
            f"strategy={means.get('strategy', 0):.3f} "
            f"scenario={means.get('scenario', 0):.3f} "
            f"timeline={means.get('timeline', 0):.3f}"
        )

    captured = capsys.readouterr()
    assert "Regression Benchmark Gate" in captured.out
