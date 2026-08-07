"""End-to-end CLI and integrity tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "synthetic"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "normshift.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_module_help() -> None:
    # Prefer installed console script via python -c typer app if module path works
    from typer.testing import CliRunner

    from normshift.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "extract" in result.stdout
    assert "diff" in result.stdout
    assert "verify" in result.stdout
    assert "benchmark" in result.stdout


def test_extract_diff_verify_determinism_tamper(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from normshift.cli import app

    runner = CliRunner()
    req_out = tmp_path / "old.requirements.json"
    r1 = runner.invoke(
        app,
        [
            "extract",
            str(FIX / "spec-v1.html"),
            "--profile",
            "rfc2119",
            "--out",
            str(req_out),
        ],
    )
    assert r1.exit_code == 0, r1.output
    assert req_out.is_file()
    data = json.loads(req_out.read_text(encoding="utf-8"))
    assert len(data["requirements"]) >= 1

    j1 = tmp_path / "r1.json"
    j2 = tmp_path / "r2.json"
    md = tmp_path / "r.md"
    d1 = runner.invoke(
        app,
        [
            "diff",
            str(FIX / "spec-v1.html"),
            str(FIX / "spec-v2.html"),
            "--profile",
            "rfc2119",
            "--json",
            str(j1),
            "--markdown",
            str(md),
        ],
    )
    assert d1.exit_code == 0, d1.output
    d2 = runner.invoke(
        app,
        [
            "diff",
            str(FIX / "spec-v1.html"),
            str(FIX / "spec-v2.html"),
            "--profile",
            "rfc2119",
            "--json",
            str(j2),
        ],
    )
    assert d2.exit_code == 0, d2.output
    assert j1.read_bytes() == j2.read_bytes()

    v_ok = runner.invoke(app, ["verify", str(j1)])
    assert v_ok.exit_code == 0, v_ok.output

    tampered = json.loads(j1.read_text(encoding="utf-8"))
    tampered["summary"]["change_count"] = 999999
    tp = tmp_path / "tampered.json"
    tp.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
    v_bad = runner.invoke(app, ["verify", str(tp)])
    assert v_bad.exit_code != 0


def test_invalid_input_exit_codes() -> None:
    from typer.testing import CliRunner

    from normshift.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["extract", "nope-missing.html", "--out", "x.json"])
    assert r.exit_code != 0
    r2 = runner.invoke(app, ["verify", "nope-missing.json"])
    assert r2.exit_code != 0


@pytest.mark.parametrize(
    "case_old,case_new,expected",
    [
        ("case01_strengthen_old.html", "case01_strengthen_new.html", "STRENGTHENED"),
        ("case02_weaken_old.html", "case02_weaken_new.html", "WEAKENED"),
        ("case03_polarity_old.html", "case03_polarity_new.html", "POLARITY_FLIP"),
        ("case08_exception_old.html", "case08_exception_new.html", "EXCEPTION_ADDED"),
        ("case09_condition_old.html", "case09_condition_new.html", "CONDITION_ADDED"),
    ],
)
def test_adversarial_classes(case_old: str, case_new: str, expected: str) -> None:
    from normshift.model.types import ProfileName
    from normshift.pipeline import run_diff

    report = run_diff(FIX / case_old, FIX / case_new, profile=ProfileName.RFC2119)
    classes = {c.classification.value for c in report.changes}
    assert expected in classes
