"""NormShift CLI (Typer)."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import typer

from normshift.adapters.errors import AdapterError
from normshift.adapters.registry import load_document
from normshift.benchmark.runner import run_benchmark
from normshift.extract.extractor import extract_requirements
from normshift.model.types import AdapterName, ProfileName
from normshift.pipeline import run_diff
from normshift.verify.verifier import verify_report_file

app = typer.Typer(
    name="normshift",
    help="Evidence-backed semantic diff for technical standards.",
    add_completion=False,
    no_args_is_help=True,
)


class ProfileOpt(StrEnum):
    rfc2119 = "rfc2119"
    whatwg = "whatwg"


class AdapterOpt(StrEnum):
    auto = "auto"
    html = "html"
    rfc = "rfc"
    w3c = "w3c"
    whatwg = "whatwg"


def _to_profile(p: ProfileOpt) -> ProfileName:
    return ProfileName(p.value)


def _to_adapter(a: AdapterOpt) -> AdapterName:
    return AdapterName(a.value)


@app.command("extract")
def extract_cmd(
    html_path: Path = typer.Argument(..., help="Local HTML/XML file"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile", help="Keyword profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter", help="Source adapter"),
    out: Path = typer.Option(..., "--out", help="Output requirements JSON path"),
) -> None:
    """Extract normative requirements from a local document."""
    if not html_path.is_file():
        typer.echo(f"error: source file not found: {html_path}", err=True)
        raise typer.Exit(code=2)
    try:
        doc = extract_requirements(
            html_path,
            _to_profile(profile),
            adapter=_to_adapter(adapter),
        )
    except AdapterError as exc:
        typer.echo(f"error: adapter failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc
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
    family = doc.document_family.value if doc.document_family else "unknown"
    typer.echo(f"wrote {len(doc.requirements)} requirements ({family}) → {out}")


@app.command("diff")
def diff_cmd(
    old_html: Path = typer.Argument(..., help="Old document"),
    new_html: Path = typer.Argument(..., help="New document"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
    json_out: Path | None = typer.Option(None, "--json", help="JSON report path"),
    markdown_out: Path | None = typer.Option(None, "--markdown", help="Markdown report path"),
) -> None:
    """Diff two document versions and emit evidence-linked reports."""
    if not old_html.is_file():
        typer.echo(f"error: old document not found: {old_html}", err=True)
        raise typer.Exit(code=2)
    if not new_html.is_file():
        typer.echo(f"error: new document not found: {new_html}", err=True)
        raise typer.Exit(code=2)
    if json_out is None and markdown_out is None:
        typer.echo("error: provide --json and/or --markdown output path", err=True)
        raise typer.Exit(code=2)

    try:
        report = run_diff(
            old_html,
            new_html,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
            json_out=json_out,
            markdown_out=markdown_out,
        )
    except AdapterError as exc:
        typer.echo(f"error: adapter failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc
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


@app.command("ingest")
def ingest_cmd(
    source: Path = typer.Argument(..., help="Local source file"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
    out: Path = typer.Option(..., "--out", help="Provenance JSON path"),
) -> None:
    """Load a document through an adapter and write immutable provenance."""
    if not source.is_file():
        typer.echo(f"error: source file not found: {source}", err=True)
        raise typer.Exit(code=2)
    try:
        adapted = load_document(source, adapter=_to_adapter(adapter))
    except AdapterError as exc:
        typer.echo(f"error: adapter failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "document_version": adapted.document_version,
        "family": adapted.family.value,
        "provenance": adapted.provenance.model_dump(mode="json"),
        "working_html_sha256": __import__("hashlib")
        .sha256(adapted.working_html)
        .hexdigest(),
    }
    out.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    typer.echo(f"ingested {adapted.family.value} → {out}")


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
