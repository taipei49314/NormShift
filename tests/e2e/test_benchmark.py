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
