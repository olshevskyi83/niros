#!/usr/bin/env python3
"""Generate or refresh the stored NIROS regression benchmark."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from niros.regression_benchmark import build_benchmark, save_benchmark
from regression_benchmark_runners import collect_all_regression_records

BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "regression_benchmark.json"


def main() -> int:
    records = collect_all_regression_records()
    benchmark = build_benchmark(records)
    save_benchmark(BENCHMARK_PATH, benchmark)
    print(f"Wrote {len(records)} case records to {BENCHMARK_PATH}")
    for suite, means in sorted(benchmark.suite_means.items()):
        print(
            f"  {suite}: patterns={means['patterns']:.3f} "
            f"coverage={means['coverage']:.3f} "
            f"strategy={means['strategy']:.3f} "
            f"scenario={means['scenario']:.3f} "
            f"timeline={means['timeline']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
