"""NormShift CLI (Typer)."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import typer

from normshift.adapters.errors import AdapterError
from normshift.adapters.registry import load_document
from normshift.benchmark.runner import run_benchmark
from normshift.extract.extractor import extract_from_source
from normshift.io_safety import PathSafetyError, assert_outputs_safe, atomic_write_text
from normshift.measure.runner import MeasureError, run_measure, write_metrics
from normshift.model.types import AdapterName, ProfileName
from normshift.paths_root import SourceRootError
from normshift.pipeline import run_diff
from normshift.source import load_immutable_source
from normshift.verify.verifier import verify_report_file

app = typer.Typer(
    name="normshift",
    help="Evidence-backed semantic diff for technical standards.",
    add_completion=False,
    no_args_is_help=True,
)

# Expedition / foundry sub-apps (experimental)
snapshot_app = typer.Typer(help="Snapshot store commands (expedition)", no_args_is_help=True)
lineage_app = typer.Typer(help="Requirement lineage (expedition)", no_args_is_help=True)
observatory_app = typer.Typer(help="Local observatory (expedition)", no_args_is_help=True)
campaign_app = typer.Typer(help="Declarative campaign engine (foundry)", no_args_is_help=True)
capsule_app = typer.Typer(help="Pair evidence capsules (foundry)", no_args_is_help=True)
review_app = typer.Typer(help="Review packets and ledger (foundry)", no_args_is_help=True)
app.add_typer(snapshot_app, name="snapshot")
app.add_typer(lineage_app, name="lineage")
app.add_typer(observatory_app, name="observatory")
app.add_typer(campaign_app, name="campaign")
app.add_typer(capsule_app, name="capsule")
app.add_typer(review_app, name="review")


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
    try:
        assert_outputs_safe(inputs=[html_path], outputs=[out], labels=["--out"])
    except PathSafetyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if not html_path.is_file():
        typer.echo(f"error: source file not found: {html_path}", err=True)
        raise typer.Exit(code=2)
    try:
        src = load_immutable_source(html_path, adapter=_to_adapter(adapter))
        doc = extract_from_source(src, _to_profile(profile))
    except AdapterError as exc:
        typer.echo(f"error: adapter failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: extraction failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    payload = doc.model_dump(mode="json")
    raw = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    atomic_write_text(out, raw)
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
    source_root: Path | None = typer.Option(
        None,
        "--source-root",
        help=(
            "Root for portable source_ref generation. Sources must resolve under this root; "
            "refs are normalized POSIX paths relative to root. Default: process CWD "
            "(outside-CWD sources fail closed)."
        ),
    ),
) -> None:
    """Diff two document versions and emit evidence-linked reports."""
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
            source_root=source_root,
        )
    except PathSafetyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except SourceRootError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
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
    try:
        assert_outputs_safe(inputs=[source], outputs=[out], labels=["--out"])
    except PathSafetyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if not source.is_file():
        typer.echo(f"error: source file not found: {source}", err=True)
        raise typer.Exit(code=2)
    try:
        adapted = load_document(source, adapter=_to_adapter(adapter))
    except AdapterError as exc:
        typer.echo(f"error: adapter failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    payload = {
        "document_version": adapted.document_version,
        "family": adapted.family.value,
        "provenance": adapted.provenance.model_dump(mode="json"),
        "working_html_sha256": __import__("hashlib")
        .sha256(adapted.working_html)
        .hexdigest(),
    }
    atomic_write_text(
        out,
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
    )
    typer.echo(f"ingested {adapted.family.value} → {out}")


@lineage_app.command("graph")
def lineage_graph_cmd(
    documents: list[Path] = typer.Argument(..., help="Ordered document versions (2+)"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
    json_out: Path = typer.Option(..., "--json", help="Lineage graph JSON path"),
) -> None:
    """Build JSON requirement lineage graph across ordered document versions (M0 path)."""
    if len(documents) < 2:
        typer.echo("error: lineage requires at least two documents", err=True)
        raise typer.Exit(code=2)
    for p in documents:
        if not p.is_file():
            typer.echo(f"error: document not found: {p}", err=True)
            raise typer.Exit(code=2)
    try:
        assert_outputs_safe(
            inputs=list(documents),
            outputs=[json_out],
            labels=["--json"],
        )
        from normshift.lineage.builder import build_lineage_graph, write_lineage_graph

        graph = build_lineage_graph(
            documents,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
        )
        write_lineage_graph(graph, json_out)
    except PathSafetyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except AdapterError as exc:
        typer.echo(f"error: adapter failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: lineage failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"lineage: {len(graph.versions)} versions, {len(graph.nodes)} lineages, "
        f"{len(graph.edges)} edges, {len(graph.ambiguity_queue)} ambiguities → {json_out}"
    )


@app.command("verify")
def verify_cmd(
    report_path: Path = typer.Argument(..., help="JSON report to verify"),
    source_root: Path | None = typer.Option(
        None, "--source-root", help="Root to resolve relative source paths"
    ),
    old_source: Path | None = typer.Option(
        None,
        "--old-source",
        help=(
            "Override old source bytes location. Declared report path is still validated "
            "(must be portable relative). Scope becomes CONTENT_ONLY_OVERRIDE."
        ),
    ),
    new_source: Path | None = typer.Option(
        None,
        "--new-source",
        help=(
            "Override new source bytes location. Declared report path is still validated "
            "(must be portable relative). Scope becomes CONTENT_ONLY_OVERRIDE."
        ),
    ),
) -> None:
    """Strict source-aware integrity verification.

    Exit 0 only when verification succeeds. Machine-readable scope is always printed:
    verification_scope=FULL | verification_scope=CONTENT_ONLY_OVERRIDE.
    Overrides relocate source bytes only; they do not attest the declared logical path.
    """
    result = verify_report_file(
        report_path,
        source_root=source_root,
        old_source=old_source,
        new_source=new_source,
    )
    scope = result.verification_scope
    if result.ok:
        msg = f"OK integrity={result.content_sha256} verification_scope={scope}"
        if result.override_used:
            msg += (
                " (WARNING: source path overrides applied; content-bound replay only; "
                "declared logical path is not re-attested)"
            )
        typer.echo(msg)
        raise typer.Exit(code=0)
    for err in result.errors:
        typer.echo(f"error: {err}", err=True)
    typer.echo(f"verification_scope={scope}", err=True)
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


@app.command("measure")
def measure_cmd(
    ground_truth: Path = typer.Option(
        ...,
        "--ground-truth",
        help="Path to measure suite JSONL (frozen labels)",
    ),
    out: Path = typer.Option(..., "--out", help="Metrics JSON output path"),
) -> None:
    """Score extraction, alignment, and classification against frozen labels."""
    try:
        assert_outputs_safe(
            inputs=[ground_truth],
            outputs=[out],
            labels=["--out"],
        )
    except PathSafetyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    try:
        report = run_measure(ground_truth)
    except MeasureError as exc:
        typer.echo(f"error: measure failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: measure failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    write_metrics(report, out)
    typer.echo(
        f"measure: {report.cases_passed}/{report.case_count} cases, "
        f"extract_f1={report.extraction.get('f1')} "
        f"align_f1={report.alignment.get('f1')} "
        f"class_f1={report.classification.get('f1')} → {out}"
    )
    if not report.ok:
        for c in report.case_results:
            if not c.passed:
                typer.echo(f"  FAIL {c.case_id}: {c.detail}", err=True)
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


@app.command("acquire")
def acquire_cmd(
    url: str = typer.Argument(..., help="Official HTTPS URL (allowlisted)"),
    store: Path = typer.Option(Path(".normshift/store"), "--store"),
    policy: Path = typer.Option(Path("config/source-policy.json"), "--policy"),
    adapter_hint: str | None = typer.Option(None, "--adapter-hint"),
    import_file: Path | None = typer.Option(
        None, "--import-file", help="Offline import bytes as if acquired from URL"
    ),
) -> None:
    """Acquire an official source snapshot into the content-addressed store."""
    from normshift.acquire.fetcher import AcquisitionError, acquire_url, import_local_bytes
    from normshift.acquire.store import SnapshotStore

    try:
        st = SnapshotStore(store)
        if import_file is not None:
            man = import_local_bytes(
                import_file,
                store=st,
                source_url=url,
                policy_path=policy,
                adapter_hint=adapter_hint,
            )
        else:
            man = acquire_url(
                url,
                store=st,
                policy_path=policy,
                adapter_hint=adapter_hint,
            )
    except AcquisitionError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(
        f"acquired {man['snapshot_id']} sha256={man['content_sha256']} "
        f"bytes={man['byte_length']} → {store}"
    )


@app.command("inspect")
def inspect_cmd(
    document: Path = typer.Argument(...),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
) -> None:
    """Inspect a document via adapter diagnostics (expedition)."""
    from normshift.adapters.contract import diagnose_document

    diag = diagnose_document(document, adapter=_to_adapter(adapter))
    typer.echo(json.dumps(diag, indent=2, sort_keys=True, ensure_ascii=False))
    if not diag.get("ok"):
        raise typer.Exit(code=1)


@app.command("adapter")
def adapter_diagnose_cmd(
    document: Path = typer.Argument(...),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    """Adapter diagnose (alias surface for expedition contract)."""
    from normshift.adapters.contract import diagnose_document

    diag = diagnose_document(document, adapter=_to_adapter(adapter))
    text = json.dumps(diag, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if out is not None:
        atomic_write_text(out, text)
        typer.echo(f"wrote diagnostics → {out}")
    else:
        typer.echo(text)
    if not diag.get("ok"):
        raise typer.Exit(code=1)


@snapshot_app.command("show")
def snapshot_show_cmd(
    snapshot_id: str = typer.Argument(...),
    store: Path = typer.Option(Path(".normshift/store"), "--store"),
) -> None:
    from normshift.acquire.store import SnapshotStore, SnapshotStoreError

    try:
        man = SnapshotStore(store).read_manifest(snapshot_id)
    except SnapshotStoreError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(man, indent=2, sort_keys=True, ensure_ascii=False))


@snapshot_app.command("verify")
def snapshot_verify_cmd(
    snapshot_id: str = typer.Argument(...),
    store: Path = typer.Option(Path(".normshift/store"), "--store"),
) -> None:
    from normshift.acquire.store import SnapshotStore, SnapshotStoreError

    try:
        result = SnapshotStore(store).verify_snapshot(snapshot_id)
    except SnapshotStoreError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("ok"):
        raise typer.Exit(code=1)


@snapshot_app.command("export")
def snapshot_export_cmd(
    snapshot_id: str = typer.Argument(...),
    store: Path = typer.Option(Path(".normshift/store"), "--store"),
    out: Path = typer.Option(..., "--out"),
) -> None:
    from normshift.acquire.store import SnapshotStore, SnapshotStoreError

    try:
        path = SnapshotStore(store).export_snapshot(snapshot_id, out)
    except SnapshotStoreError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"exported {snapshot_id} → {path}")


@lineage_app.command("build")
def lineage_build_cmd(
    documents: list[Path] = typer.Argument(..., help="Ordered document versions"),
    db: Path = typer.Option(..., "--db"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
) -> None:
    """Build multi-version lineage into SQLite (expedition)."""
    from normshift.lineage.graph_builder import build_lineage_from_paths
    from normshift.lineage.store import LineageStore

    if len(documents) < 2:
        typer.echo("error: need at least two documents", err=True)
        raise typer.Exit(code=2)
    store = LineageStore(db)
    try:
        summary = build_lineage_from_paths(
            documents,
            store=store,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
        )
    finally:
        store.close()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@lineage_app.command("export")
def lineage_export_cmd(
    db: Path = typer.Option(..., "--db"),
    jsonl: Path = typer.Option(..., "--jsonl"),
) -> None:
    from normshift.lineage.store import LineageStore

    store = LineageStore(db)
    try:
        raw = store.export_jsonl(jsonl)
    finally:
        store.close()
    typer.echo(f"exported {len(raw)} bytes → {jsonl}")


@lineage_app.command("verify")
def lineage_verify_cmd(jsonl: Path = typer.Argument(...)) -> None:
    """Structural verify of lineage JSONL export."""
    if not jsonl.is_file():
        typer.echo(f"error: not found: {jsonl}", err=True)
        raise typer.Exit(code=2)
    nodes = edges = 0
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("record") == "node":
            nodes += 1
        elif obj.get("record") == "edge":
            edges += 1
    typer.echo(json.dumps({"ok": True, "nodes": nodes, "edges": edges}))


@observatory_app.command("build")
def observatory_build_cmd(
    store: Path = typer.Option(Path(".normshift/store"), "--store"),
    out: Path = typer.Option(..., "--out"),
) -> None:
    from normshift.acquire.store import SnapshotStore
    from normshift.observatory.builder import build_observatory

    man = build_observatory(store=SnapshotStore(store), out_dir=out)
    typer.echo(
        f"observatory: snapshots={man['snapshot_count']} "
        f"files={len(man['files'])} → {out}"
    )


@observatory_app.command("verify")
def observatory_verify_cmd(
    manifest: Path = typer.Argument(..., help="site/manifest.json"),
) -> None:
    from normshift.observatory.builder import verify_observatory_manifest

    site = manifest.parent if manifest.name == "manifest.json" else manifest
    result = verify_observatory_manifest(site)
    typer.echo(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("ok"):
        raise typer.Exit(code=1)


@app.command("corpus")
def corpus_verify_cmd(
    catalog: Path = typer.Argument(..., help="corpus/catalog.yaml"),
) -> None:
    """Verify corpus catalog structure (expedition)."""
    if not catalog.is_file():
        typer.echo(f"error: catalog not found: {catalog}", err=True)
        raise typer.Exit(code=2)
    text = catalog.read_text(encoding="utf-8")
    if "pairs:" not in text and "snapshots:" not in text:
        typer.echo("error: catalog missing pairs/snapshots sections", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps({"ok": True, "catalog": str(catalog)}))


@app.command("benchmark-real")
def benchmark_real_cmd(
    root: Path = typer.Option(Path("."), "--root", help="Repository root"),
    out: Path | None = typer.Option(None, "--out", help="Write metrics JSON"),
) -> None:
    """Provisional real-fixture benchmark (AUTO labels — not gold)."""
    from normshift.benchmark.real_runner import run_real_benchmark
    from normshift.evidence.hashing import canonical_json_bytes

    report = run_real_benchmark(root)
    payload = report.to_dict()
    text = canonical_json_bytes(payload).decode("utf-8")
    if out is not None:
        atomic_write_text(out, text)
        typer.echo(f"wrote provisional metrics → {out}")
    for c in report.cases:
        flag = "PASS" if c.passed else "FAIL"
        typer.echo(f"[{flag}] {c.case_id}: {c.detail}")
    typer.echo(
        f"benchmark-real: {report.passed}/{report.total} "
        f"(EXPERIMENTAL_NOT_ADJUDICATED, AUTO labels)"
    )
    if report.passed < report.total:
        raise typer.Exit(code=1)


@observatory_app.command("poll")
def observatory_poll_cmd(
    watchlist: Path = typer.Option(Path("config/watchlist.yaml"), "--watchlist"),
    store: Path = typer.Option(Path(".normshift/store"), "--store"),
    policy: Path = typer.Option(Path("config/source-policy.json"), "--policy"),
    offline_only: bool = typer.Option(
        False, "--offline-only", help="Skip network; only report watchlist status"
    ),
) -> None:
    """Poll watchlist sources into snapshot store (network allowed)."""
    from normshift.acquire.fetcher import AcquisitionError, acquire_url
    from normshift.acquire.store import SnapshotStore

    if not watchlist.is_file():
        typer.echo(f"error: watchlist not found: {watchlist}", err=True)
        raise typer.Exit(code=2)
    text = watchlist.read_text(encoding="utf-8")
    # Minimal parse: lines with official_source:
    urls: list[str] = []
    for line in text.splitlines():
        if "official_source:" in line:
            urls.append(line.split("official_source:", 1)[1].strip())
    st = SnapshotStore(store)
    results: list[dict[str, object]] = []
    for url in urls:
        if offline_only:
            results.append({"url": url, "status": "skipped_offline_only"})
            continue
        try:
            man = acquire_url(url, store=st, policy_path=policy)
            results.append(
                {
                    "url": url,
                    "status": "ok",
                    "snapshot_id": man["snapshot_id"],
                    "sha256": man["content_sha256"],
                    "bytes": man["byte_length"],
                }
            )
        except AcquisitionError as exc:
            results.append({"url": url, "status": "error", "error": str(exc)})
    typer.echo(json.dumps({"results": results, "experimental": True}, indent=2))


@campaign_app.command("validate")
def campaign_validate_cmd(plan: Path = typer.Argument(...)) -> None:
    from normshift.campaign.runner import validate_plan

    try:
        result = validate_plan(plan)
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result, indent=2, sort_keys=True))


@campaign_app.command("run")
def campaign_run_cmd(
    plan: Path = typer.Argument(...),
    workspace: Path = typer.Option(Path(".normshift/foundry-24h"), "--workspace"),
    mode: str = typer.Option("offline", "--mode", help="acquire|offline"),
    source_date_epoch: int | None = typer.Option(None, "--source-date-epoch"),
) -> None:
    from normshift.campaign.runner import run_campaign

    if mode not in {"acquire", "offline"}:
        typer.echo("error: mode must be acquire|offline", err=True)
        raise typer.Exit(code=2)
    try:
        run = run_campaign(
            plan,
            workspace=workspace,
            mode=mode,  # type: ignore[arg-type]
            source_date_epoch=source_date_epoch,
        )
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"error: campaign failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        json.dumps(
            {
                "run_id": run.run_id,
                "campaign_id": run.campaign_id,
                "pairs": len(run.pair_capsule_ids),
                "packets_set": run.review_packet_set_id,
                "counts": run.counts,
                "status": run.status,
            },
            indent=2,
            sort_keys=True,
        )
    )


@campaign_app.command("verify")
def campaign_verify_cmd(
    run_manifest: Path = typer.Argument(...),
    workspace: Path = typer.Option(Path(".normshift/foundry-24h"), "--workspace"),
) -> None:
    from normshift.campaign.runner import verify_run_manifest

    result = verify_run_manifest(run_manifest, workspace=workspace)
    typer.echo(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("ok"):
        raise typer.Exit(code=1)


@capsule_app.command("verify")
def capsule_verify_cmd(capsule_dir: Path = typer.Argument(...)) -> None:
    from normshift.capsule.verifier import verify_capsule

    result = verify_capsule(capsule_dir)
    typer.echo(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("ok"):
        raise typer.Exit(code=1)


@review_app.command("packets")
def review_packets_cmd(
    build: bool = typer.Option(False, "--build"),
    run_manifest: Path | None = typer.Option(None, "--run-manifest"),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    """Build is performed by campaign run; this validates packets file exists."""
    if out and out.is_file():
        n = sum(1 for line in out.read_text(encoding="utf-8").splitlines() if line.strip())
        typer.echo(json.dumps({"ok": True, "packets": n, "path": str(out)}))
        return
    typer.echo("error: use campaign run to build packets; pass --out to count", err=True)
    raise typer.Exit(code=2)


@review_app.command("ledger")
def review_ledger_cmd(
    action: str = typer.Argument(..., help="validate|merge"),
    paths: list[Path] = typer.Argument(...),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    from normshift.review.ledger import merge_ledgers, validate_ledger

    if action == "validate":
        result = validate_ledger(paths[0], allow_external=False)
        typer.echo(json.dumps(result, indent=2))
        if not result.get("ok"):
            raise typer.Exit(code=1)
    elif action == "merge":
        if out is None:
            typer.echo("error: --out required for merge", err=True)
            raise typer.Exit(code=2)
        result = merge_ledgers(paths, out)
        typer.echo(json.dumps(result, indent=2))
        if not result.get("ok"):
            raise typer.Exit(code=1)
    else:
        raise typer.Exit(code=2)


@review_app.command("status")
def review_status_cmd(
    packets: Path = typer.Argument(...),
    decisions: Path | None = typer.Argument(None),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    from normshift.evidence.hashing import canonical_json_bytes
    from normshift.review.status import review_status

    st = review_status(packets, decisions)
    text = canonical_json_bytes(st).decode("utf-8")
    if out:
        atomic_write_text(out, text)
    typer.echo(text)


@app.command("corpus-evaluate")
def corpus_evaluate_cmd(
    campaign_manifest: Path = typer.Option(..., "--campaign-manifest"),
    out: Path = typer.Option(..., "--out"),
) -> None:
    """Re-emit layered metrics from an existing campaign metrics file if present."""
    metrics_guess = Path("artifacts/foundry-24h/metrics.json")
    if metrics_guess.is_file():
        text = metrics_guess.read_text(encoding="utf-8")
        atomic_write_text(out, text if text.endswith("\n") else text + "\n")
        typer.echo(f"wrote layered metrics → {out}")
        return
    typer.echo("error: run campaign first to produce metrics", err=True)
    raise typer.Exit(code=2)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

