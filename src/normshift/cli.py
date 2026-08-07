"""NormShift CLI (Typer)."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import typer

from normshift.benchmark.runner import run_benchmark
from normshift.extract.extractor import extract_requirements
from normshift.model.types import ProfileName
from normshift.pipeline import run_diff
from normshift.verify.verifier import verify_report_file

app = typer.Typer(
    name="normshift",
    help="Evidence-backed semantic diff for technical standards (local HTML M0).",
    add_completion=False,
    no_args_is_help=True,
)


class ProfileOpt(StrEnum):
    rfc2119 = "rfc2119"
    whatwg = "whatwg"


def _to_profile(p: ProfileOpt) -> ProfileName:
    return ProfileName(p.value)


@app.command("extract")
def extract_cmd(
    html_path: Path = typer.Argument(..., exists=False, readable=False, help="Local HTML file"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile", help="Keyword profile"),
    out: Path = typer.Option(..., "--out", help="Output requirements JSON path"),
) -> None:
    """Extract normative requirements from a local HTML file."""
    if not html_path.is_file():
        typer.echo(f"error: HTML file not found: {html_path}", err=True)
        raise typer.Exit(code=2)
    try:
        prof = _to_profile(profile)
        doc = extract_requirements(html_path, prof)
    except ValueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: extraction failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = doc.model_dump(mode="json")
    raw = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    out.write_text(raw, encoding="utf-8")
    typer.echo(f"wrote {len(doc.requirements)} requirements → {out}")


@app.command("diff")
def diff_cmd(
    old_html: Path = typer.Argument(..., help="Old HTML file"),
    new_html: Path = typer.Argument(..., help="New HTML file"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    json_out: Path | None = typer.Option(None, "--json", help="JSON report path"),
    markdown_out: Path | None = typer.Option(None, "--markdown", help="Markdown report path"),
) -> None:
    """Diff two HTML versions and emit evidence-linked reports."""
    if not old_html.is_file():
        typer.echo(f"error: old HTML not found: {old_html}", err=True)
        raise typer.Exit(code=2)
    if not new_html.is_file():
        typer.echo(f"error: new HTML not found: {new_html}", err=True)
        raise typer.Exit(code=2)
    if json_out is None and markdown_out is None:
        typer.echo("error: provide --json and/or --markdown output path", err=True)
        raise typer.Exit(code=2)

    try:
        report = run_diff(
            old_html,
            new_html,
            profile=_to_profile(profile),
            json_out=json_out,
            markdown_out=markdown_out,
        )
    except ValueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: diff failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"diff complete: {len(report.old_requirements)}→{len(report.new_requirements)} "
        f"requirements, {len(report.changes)} changes"
    )


@app.command("verify")
def verify_cmd(
    report_path: Path = typer.Argument(..., help="JSON report to verify"),
) -> None:
    """Verify report integrity and schema conformance."""
    result = verify_report_file(report_path)
    if result.ok:
        typer.echo(f"OK integrity={result.content_sha256}")
        raise typer.Exit(code=0)
    for err in result.errors:
        typer.echo(f"error: {err}", err=True)
    raise typer.Exit(code=1)


@app.command("benchmark")
def benchmark_cmd(
    ground_truth: Path = typer.Option(
        ...,
        "--ground-truth",
        help="Path to ground_truth.jsonl",
    ),
) -> None:
    """Run fixed adversarial benchmark cases."""
    if not ground_truth.is_file():
        typer.echo(f"error: ground truth not found: {ground_truth}", err=True)
        raise typer.Exit(code=2)
    try:
        report = run_benchmark(ground_truth)
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: benchmark failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        typer.echo(f"[{status}] {r.case_id}: {r.detail}")
        if not r.passed:
            typer.echo(f"         expected={r.expected} observed={r.observed}")

    typer.echo(f"benchmark: {report.passed}/{report.total} passed, {report.failed} failed")
    if not report.ok:
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
