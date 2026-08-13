"""End-to-end CLI and integrity tests."""

from __future__ import annotations

import json
import subprocess
import sys
from hashlib import sha256
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
    assert "semantic-dimensions" in result.stdout
    semantic_help = runner.invoke(app, ["semantic-dimensions", "--help"])
    assert semantic_help.exit_code == 0
    assert "prepare-receipt" not in semantic_help.output
    assert "build" in semantic_help.output
    assert "verify" in semantic_help.output
    assert "--json" not in semantic_help.output


def test_cli_version_matches_package() -> None:
    from importlib.metadata import version

    result = _run("--version")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == version("normshift")


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
            "--source-root",
            str(ROOT),
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
            "--source-root",
            str(ROOT),
            "--json",
            str(j2),
        ],
    )
    assert d2.exit_code == 0, d2.output
    assert j1.read_bytes() == j2.read_bytes()

    v_ok = runner.invoke(app, ["verify", str(j1), "--source-root", str(ROOT)])
    assert v_ok.exit_code == 0, v_ok.output

    tampered = json.loads(j1.read_text(encoding="utf-8"))
    tampered["summary"]["change_count"] = 999999
    tp = tmp_path / "tampered.json"
    tp.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
    v_bad = runner.invoke(app, ["verify", str(tp)])
    assert v_bad.exit_code != 0


def test_semantic_dimensions_cli_emits_canonical_sidecar_from_full_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from typer.testing import CliRunner

    import normshift.cli as cli_module
    from normshift.cli import app
    from normshift.semantic_dimensions import (
        SemanticDimensionsError,
        create_full_verification_receipt,
        full_verification_receipt_json_bytes,
        parse_semantic_dimensions_bytes,
        semantic_dimensions_json_bytes,
    )

    runner = CliRunner()
    report_path = tmp_path / "report.json"
    diff = runner.invoke(
        app,
        [
            "diff",
            str(FIX / "case15_relocation_old.html"),
            str(FIX / "case15_relocation_new.html"),
            "--source-root",
            str(ROOT),
            "--json",
            str(report_path),
        ],
    )
    assert diff.exit_code == 0, diff.output
    primary_change_id = json.loads(report_path.read_text(encoding="utf-8"))["changes"][0][
        "change_id"
    ]

    receipt_path = tmp_path / "full-receipt.json"
    # Synthetic test preparation uses the library only; production CLI never
    # creates a receipt that the same caller can immediately consume.
    receipt_path.write_bytes(
        full_verification_receipt_json_bytes(
            create_full_verification_receipt(report_path, source_root=ROOT)
        )
    )

    sidecar_path = tmp_path / "dimensions.json"
    build_args = [
        "semantic-dimensions",
        "build",
        str(report_path),
        primary_change_id,
        "--receipt",
        str(receipt_path),
        "--report-sha256",
        sha256(report_path.read_bytes()).hexdigest(),
        "--receipt-sha256",
        sha256(receipt_path.read_bytes()).hexdigest(),
        "--source-root",
        str(ROOT),
    ]
    built = runner.invoke(app, build_args)
    assert built.exit_code == 0, built.output
    first = built.stdout_bytes
    assert first == semantic_dimensions_json_bytes(parse_semantic_dimensions_bytes(first))
    assert (
        parse_semantic_dimensions_bytes(first).change.evidence.authority_kind
        == "FULL_REPORT_REPLAY"
    )
    subprocess_capture = subprocess.run(
        [sys.executable, "-m", "normshift.cli", *build_args],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    assert subprocess_capture.returncode == 0, subprocess_capture.stderr.decode("utf-8")
    assert subprocess_capture.stdout == first

    def oversized_serializer(_: object) -> bytes:
        raise SemanticDimensionsError("semantic dimension document exceeds size limit")

    with monkeypatch.context() as context:
        context.setattr(cli_module, "semantic_dimensions_json_bytes", oversized_serializer)
        oversized = runner.invoke(app, build_args)
    assert oversized.exit_code == 1
    assert oversized.stdout_bytes == b""
    assert "exceeds size limit" in oversized.output
    sidecar_path.write_bytes(first)

    verified = runner.invoke(
        app,
        [
            "semantic-dimensions",
            "verify",
            str(sidecar_path),
            primary_change_id,
            "--semantic-sha256",
            sha256(first).hexdigest(),
            "--receipt",
            str(receipt_path),
            "--report-sha256",
            sha256(report_path.read_bytes()).hexdigest(),
            "--receipt-sha256",
            sha256(receipt_path.read_bytes()).hexdigest(),
            "--source-root",
            str(ROOT),
            "--report",
            str(report_path),
        ],
    )
    assert verified.exit_code == 0, verified.output
    assert "FULL source-replay binding" in verified.output

    rebuilt = runner.invoke(app, build_args)
    assert rebuilt.exit_code == 0, rebuilt.output
    assert rebuilt.stdout_bytes == first

    class ShortWritingStream:
        def __init__(self) -> None:
            self.captured = bytearray()
            self.flushed = False

        def write(self, value: memoryview) -> int:
            written = min(7, len(value))
            self.captured.extend(value[:written])
            return written

        def flush(self) -> None:
            self.flushed = True

    short_stream = ShortWritingStream()
    monkeypatch.setattr(cli_module.typer, "get_binary_stream", lambda _: short_stream)
    short_written = runner.invoke(app, build_args)
    assert short_written.exit_code == 0, short_written.output
    assert short_stream.flushed
    assert bytes(short_stream.captured) == first

    class ZeroProgressAfterPrefixStream:
        def __init__(self) -> None:
            self.captured = bytearray()
            self.calls = 0

        def write(self, value: memoryview) -> int:
            self.calls += 1
            if self.calls == 1:
                self.captured.extend(value[:1])
                return 1
            return 0

        def flush(self) -> None:
            raise AssertionError("a failed stream must not be flushed")

    zero_stream = ZeroProgressAfterPrefixStream()
    monkeypatch.setattr(cli_module.typer, "get_binary_stream", lambda _: zero_stream)
    zero_progress = runner.invoke(app, build_args)
    assert zero_progress.exit_code == 1
    assert bytes(zero_stream.captured) == first[:1]
    assert "FULL source-replay binding failed" in zero_progress.output

    class FlushFailingStream:
        def __init__(self) -> None:
            self.captured = bytearray()

        def write(self, value: memoryview) -> int:
            self.captured.extend(value)
            return len(value)

        def flush(self) -> None:
            raise OSError("injected flush failure")

    flush_stream = FlushFailingStream()
    monkeypatch.setattr(cli_module.typer, "get_binary_stream", lambda _: flush_stream)
    flush_failure = runner.invoke(app, build_args)
    assert flush_failure.exit_code == 1
    assert bytes(flush_stream.captured) == first
    assert "injected flush failure" in flush_failure.output

    invalid_digest = build_args.copy()
    digest_index = invalid_digest.index("--receipt-sha256") + 1
    invalid_digest[digest_index] = "0" * 64
    rejected = runner.invoke(app, invalid_digest)
    assert rejected.exit_code == 1
    assert "FULL source-replay binding failed" in rejected.output
    assert rejected.stdout_bytes == b""

    bad_sidecar_digest = runner.invoke(
        app,
        [
            "semantic-dimensions",
            "verify",
            str(sidecar_path),
            primary_change_id,
            "--semantic-sha256",
            "0" * 64,
            "--receipt",
            str(receipt_path),
            "--report-sha256",
            sha256(report_path.read_bytes()).hexdigest(),
            "--receipt-sha256",
            sha256(receipt_path.read_bytes()).hexdigest(),
            "--source-root",
            str(ROOT),
            "--report",
            str(report_path),
        ],
    )
    assert bad_sidecar_digest.exit_code == 1
    assert "semantic sidecar bytes differ" in bad_sidecar_digest.output


def test_semantic_dimensions_build_requires_preexisting_receipt(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from normshift.cli import app

    source_root = tmp_path / "sources"
    source_root.mkdir()
    result = CliRunner().invoke(
        app,
        [
            "semantic-dimensions",
            "build",
            str(source_root / "report.json"),
            "change",
            "--receipt",
            str(source_root / "missing-receipt.json"),
            "--report-sha256",
            "0" * 64,
            "--receipt-sha256",
            "0" * 64,
            "--source-root",
            str(source_root),
        ],
    )
    assert result.exit_code == 1
    assert "FULL source-replay binding failed" in result.output
    assert result.stdout_bytes == b""


@pytest.mark.parametrize(
    "forbidden_option",
    [
        "--old-source",
        "--new-source",
        "--content-only",
        "--role",
        "--object-span",
        "--scope-span",
        "--span",
    ],
)
def test_semantic_dimensions_cli_rejects_content_only_and_span_options(
    forbidden_option: str,
) -> None:
    from typer.testing import CliRunner

    from normshift.cli import app

    result = CliRunner().invoke(
        app,
        [
            "semantic-dimensions",
            "build",
            "report.json",
            "change",
            "--receipt",
            "receipt.json",
            "--report-sha256",
            "0" * 64,
            "--receipt-sha256",
            "0" * 64,
            "--source-root",
            ".",
            forbidden_option,
            "unavailable",
        ],
    )
    assert result.exit_code == 2
    assert "No such option" in result.output


def test_semantic_dimensions_verify_rejects_malformed_sidecar_before_full_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    import normshift.cli as cli_module
    from normshift.cli import app

    sidecar = tmp_path / "malformed.json"
    sidecar.write_bytes(b"{}\n")
    called = False

    def unexpected_bind(*args: object, **kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("FULL replay must not run for malformed sidecar")

    monkeypatch.setattr(cli_module, "bind_verified_report_file", unexpected_bind)
    result = CliRunner().invoke(
        app,
        [
            "semantic-dimensions",
            "verify",
            str(sidecar),
            "change",
            "--semantic-sha256",
            sha256(sidecar.read_bytes()).hexdigest(),
            "--receipt",
            str(tmp_path / "receipt.json"),
            "--report",
            str(tmp_path / "report.json"),
            "--report-sha256",
            "0" * 64,
            "--receipt-sha256",
            "0" * 64,
            "--source-root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 1
    assert "invalid semantic dimension document" in result.output
    assert not called


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

    report = run_diff(
        FIX / case_old,
        FIX / case_new,
        profile=ProfileName.RFC2119,
        source_root=ROOT,
    )
    classes = {c.classification.value for c in report.changes}
    assert expected in classes
