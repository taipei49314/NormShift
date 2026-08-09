"""Benchmark gate test."""

from __future__ import annotations

from pathlib import Path

from normshift.benchmark.runner import run_benchmark

ROOT = Path(__file__).resolve().parents[2]


def test_ground_truth_benchmark() -> None:
    report = run_benchmark(ROOT / "benchmark" / "ground_truth.jsonl")
    failed = [r for r in report.results if not r.passed]
    msg = "\n".join(
        f"{r.case_id}: {r.detail} exp={r.expected} obs={r.observed}" for r in failed
    )
    assert report.ok, msg


def test_benchmark_cli_output_is_cp1252_safe() -> None:
    """Benchmark progress must render on the default non-UTF-8 Windows stream."""
    report = run_benchmark(ROOT / "benchmark" / "ground_truth.jsonl")
    rendered = [f"[PASS] {result.case_id}: {result.detail}" for result in report.results]
    rendered.append(f"benchmark: {report.passed}/{report.total} passed, {report.failed} failed")

    for line in rendered:
        line.encode("cp1252")
