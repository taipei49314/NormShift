"""Provisional real benchmark offline."""

from __future__ import annotations

from pathlib import Path

from normshift.benchmark.real_runner import run_real_benchmark

ROOT = Path(__file__).resolve().parents[2]


def test_real_benchmark_offline_fixtures() -> None:
    report = run_real_benchmark(ROOT)
    assert report.total >= 6
    assert report.passed == report.total
    assert report.label_authority == "AUTO"
