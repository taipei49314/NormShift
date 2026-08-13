"""NormShift CLI (Typer)."""

from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from re import fullmatch

import typer

from normshift import __version__
from normshift.adapters.errors import AdapterError
from normshift.adapters.registry import load_document
from normshift.benchmark.runner import run_benchmark
from normshift.corpus.acquisition import (
    AcquisitionError,
    CorpusReplayResult,
    acquire_corpus,
    verify_corpus_offline,
)
from normshift.corpus.evidence_inventory import (
    EvidenceInventoryError,
    SourceRecipeEvidenceResult,
    verify_source_recipe_evidence,
)
from normshift.definition_reference_candidates import (
    DefinitionReferenceCandidateError,
    build_definition_reference_candidates,
    definition_reference_candidates_json_bytes,
    verify_definition_reference_candidates_file,
)
from normshift.definition_transitions import (
    DefinitionTransitionError,
    build_definition_transitions,
    definition_transitions_json_bytes,
    verify_definition_transitions_file,
)
from normshift.extract.extractor import extract_from_source
from normshift.governance.verify import (
    GovernanceContractError,
    GovernanceVerificationResult,
    verify_blind_split,
    verify_labeling_governance,
)
from normshift.io_safety import (
    PathSafetyError,
    assert_outputs_safe,
    atomic_write_text,
)
from normshift.lineage import LineageContractError, verify_lineage_graph_file
from normshift.measure.runner import MeasureError, run_measure, write_metrics
from normshift.model.types import AdapterName, ProfileName
from normshift.paths_root import SourceRootError
from normshift.pipeline import run_diff
from normshift.semantic_dimensions import (
    SemanticDimensionsError,
    bind_verified_report_file,
    build_semantic_dimensions,
    parse_semantic_dimensions_bytes,
    read_bounded_regular_file,
    semantic_dimensions_json_bytes,
    verify_semantic_dimensions,
)
from normshift.source import load_immutable_source
from normshift.verify.verifier import verify_report_file

app = typer.Typer(
    name="normshift",
    help="Evidence-backed semantic diff for technical standards.",
    add_completion=False,
    no_args_is_help=True,
)
corpus_app = typer.Typer(
    help="Hash-frozen M1 source acquisition (experimental; not M1 acceptance).",
    no_args_is_help=True,
)
app.add_typer(corpus_app, name="corpus")
governance_app = typer.Typer(
    help="Synthetic-tested labeling and blind-split governance checks (no acceptance claim).",
    no_args_is_help=True,
)
app.add_typer(governance_app, name="governance")
semantic_dimensions_app = typer.Typer(
    help="Experimental M2 semantic-dimension sidecars (not M2 acceptance).",
    no_args_is_help=True,
)
app.add_typer(semantic_dimensions_app, name="semantic-dimensions")
definition_transitions_app = typer.Typer(
    help=(
        "Experimental replay-only adjacent definition transitions "
        "(not M2 acceptance or adjudication)."
    ),
    no_args_is_help=True,
)
app.add_typer(definition_transitions_app, name="definition-transitions")
definition_reference_candidates_app = typer.Typer(
    help="Experimental lexical definition-reference candidates (not semantic verdicts).",
    no_args_is_help=True,
)
app.add_typer(definition_reference_candidates_app, name="definition-reference-candidates")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit(code=0)


@app.callback()
def root_options(
    version: bool = typer.Option(
        False,
        "--version",
        help="Print the NormShift package version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """NormShift command-line interface."""


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


def _require_external_sha256(value: str, *, label: str) -> None:
    if fullmatch(r"[0-9a-f]{64}", value) is None:
        raise SemanticDimensionsError(f"{label} must be a lowercase SHA-256 digest")


def _write_all_binary_stdout(raw: bytes) -> None:
    """Write exactly ``raw`` to binary stdout or fail without reporting success."""
    stream = typer.get_binary_stream("stdout")
    view = memoryview(raw)
    offset = 0
    while offset < len(view):
        written = stream.write(view[offset:])
        remaining = len(view) - offset
        if type(written) is not int or written <= 0 or written > remaining:
            raise SemanticDimensionsError("binary stdout made invalid write progress")
        offset += written
    stream.flush()


@definition_reference_candidates_app.command("build")
def definition_reference_candidates_build_cmd(
    graph_path: Path = typer.Argument(...),
    documents: list[Path] = typer.Argument(...),
    graph_sha256: str = typer.Option(..., "--graph-sha256"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
) -> None:
    """Write canonical lexical candidate bytes to binary stdout on success only."""
    try:
        graph = verify_lineage_graph_file(
            graph_path,
            graph_sha256=graph_sha256,
            documents=documents,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
        )
        _write_all_binary_stdout(
            definition_reference_candidates_json_bytes(
                build_definition_reference_candidates(graph, graph_file_sha256=graph_sha256)
            )
        )
    except (
        OSError,
        DefinitionReferenceCandidateError,
        LineageContractError,
        SemanticDimensionsError,
    ) as exc:
        typer.echo(f"error: lineage graph replay binding failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@definition_reference_candidates_app.command("verify")
def definition_reference_candidates_verify_cmd(
    candidates_path: Path = typer.Argument(...),
    graph_path: Path = typer.Argument(...),
    documents: list[Path] = typer.Argument(...),
    candidates_sha256: str = typer.Option(..., "--candidates-sha256"),
    graph_sha256: str = typer.Option(..., "--graph-sha256"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
) -> None:
    """Verify lexical candidates through exact graph replay only."""
    try:
        document = verify_definition_reference_candidates_file(
            candidates_path,
            candidates_sha256=candidates_sha256,
            graph_path=graph_path,
            graph_sha256=graph_sha256,
            documents=documents,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
        )
    except (OSError, DefinitionReferenceCandidateError) as exc:
        typer.echo(f"error: lineage graph replay binding failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        "OK DEFINITION_REFERENCE_CANDIDATES_REPLAY_ONLY external_acceptance=false "
        f"integrity_sha256={document.integrity.content_sha256}"
    )


@definition_transitions_app.command("build")
def definition_transitions_build_cmd(
    graph_path: Path = typer.Argument(..., help="Canonical LineageGraph v1 JSON"),
    documents: list[Path] = typer.Argument(..., help="Ordered source document versions (2+)"),
    graph_sha256: str = typer.Option(
        ..., "--graph-sha256", help="Independently held SHA-256 of exact graph bytes"
    ),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
) -> None:
    """Write exact canonical transition bytes to binary stdout on success only."""
    try:
        graph = verify_lineage_graph_file(
            graph_path,
            graph_sha256=graph_sha256,
            documents=documents,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
        )
        document = build_definition_transitions(graph, graph_file_sha256=graph_sha256)
        _write_all_binary_stdout(definition_transitions_json_bytes(document))
    except (
        OSError,
        DefinitionTransitionError,
        LineageContractError,
        SemanticDimensionsError,
    ) as exc:
        typer.echo(f"error: lineage graph replay binding failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@definition_transitions_app.command("verify")
def definition_transitions_verify_cmd(
    transitions_path: Path = typer.Argument(..., help="Canonical DefinitionTransition v1 JSON"),
    graph_path: Path = typer.Argument(..., help="Canonical LineageGraph v1 JSON"),
    documents: list[Path] = typer.Argument(..., help="Ordered source document versions (2+)"),
    transitions_sha256: str = typer.Option(
        ..., "--transitions-sha256", help="Independently held SHA-256 of exact transition bytes"
    ),
    graph_sha256: str = typer.Option(
        ..., "--graph-sha256", help="Independently held SHA-256 of exact graph bytes"
    ),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
) -> None:
    """Verify an experimental transition sidecar by exact graph replay only."""
    try:
        document = verify_definition_transitions_file(
            transitions_path,
            transitions_sha256=transitions_sha256,
            graph_path=graph_path,
            graph_sha256=graph_sha256,
            documents=documents,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
        )
    except (OSError, DefinitionTransitionError) as exc:
        typer.echo(f"error: lineage graph replay binding failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        "OK DEFINITION_TRANSITIONS_REPLAY_ONLY external_acceptance=false "
        "no source custody, adjudication, cross-reference, or indirect-impact claim "
        f"integrity_sha256={document.integrity.content_sha256}"
    )


@semantic_dimensions_app.command("build")
def semantic_dimensions_build_cmd(
    report_path: Path = typer.Argument(..., help="Canonical primary M0 report JSON"),
    primary_change_id: str = typer.Argument(..., help="Exact primary report change ID"),
    receipt_path: Path = typer.Option(..., "--receipt", help="Canonical FULL receipt JSON"),
    report_sha256: str = typer.Option(
        ..., "--report-sha256", help="Independently held SHA-256 of exact report bytes"
    ),
    receipt_sha256: str = typer.Option(
        ..., "--receipt-sha256", help="Independently held SHA-256 of exact receipt bytes"
    ),
    source_root: Path = typer.Option(
        ..., "--source-root", help="Root resolving the report's portable source refs"
    ),
) -> None:
    """Write an experimental canonical semantic sidecar to binary standard output."""
    try:
        _require_external_sha256(report_sha256, label="--report-sha256")
        _require_external_sha256(receipt_sha256, label="--receipt-sha256")
        receipt_bytes = read_bounded_regular_file(
            receipt_path, label="FULL receipt", max_bytes=100_000
        ).raw
        authority = bind_verified_report_file(
            report_path,
            source_root=source_root,
            receipt_bytes=receipt_bytes,
            expected_report_file_sha256=report_sha256,
            expected_receipt_sha256=receipt_sha256,
        )
        document = build_semantic_dimensions(
            authority=authority,
            primary_change_id=primary_change_id,
        )
        raw = semantic_dimensions_json_bytes(document)
        _write_all_binary_stdout(raw)
    except PathSafetyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except (OSError, SemanticDimensionsError) as exc:
        typer.echo(f"error: FULL source-replay binding failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@semantic_dimensions_app.command("verify")
def semantic_dimensions_verify_cmd(
    semantic_path: Path = typer.Argument(..., help="Canonical semantic sidecar JSON"),
    primary_change_id: str = typer.Argument(..., help="Exact primary report change ID"),
    semantic_sha256: str = typer.Option(
        ..., "--semantic-sha256", help="Independently held SHA-256 of exact sidecar bytes"
    ),
    receipt_path: Path = typer.Option(..., "--receipt", help="Canonical FULL receipt JSON"),
    report_sha256: str = typer.Option(
        ..., "--report-sha256", help="Independently held SHA-256 of exact report bytes"
    ),
    receipt_sha256: str = typer.Option(
        ..., "--receipt-sha256", help="Independently held SHA-256 of exact receipt bytes"
    ),
    source_root: Path = typer.Option(
        ..., "--source-root", help="Root resolving the report's portable source refs"
    ),
    report_path: Path = typer.Option(..., "--report", help="Canonical primary M0 report JSON"),
) -> None:
    """Verify a canonical sidecar solely through an anchored FULL source replay."""
    try:
        _require_external_sha256(semantic_sha256, label="--semantic-sha256")
        _require_external_sha256(report_sha256, label="--report-sha256")
        _require_external_sha256(receipt_sha256, label="--receipt-sha256")
        semantic_bytes = read_bounded_regular_file(
            semantic_path,
            label="semantic sidecar",
            max_bytes=1_000_000,
        ).raw
        if sha256(semantic_bytes).hexdigest() != semantic_sha256:
            raise SemanticDimensionsError("semantic sidecar bytes differ from external SHA-256")
        document = parse_semantic_dimensions_bytes(semantic_bytes)
        receipt_bytes = read_bounded_regular_file(
            receipt_path, label="FULL receipt", max_bytes=100_000
        ).raw
        authority = bind_verified_report_file(
            report_path,
            source_root=source_root,
            receipt_bytes=receipt_bytes,
            expected_report_file_sha256=report_sha256,
            expected_receipt_sha256=receipt_sha256,
        )
        verify_semantic_dimensions(
            document,
            authority=authority,
            primary_change_id=primary_change_id,
        )
    except (OSError, SemanticDimensionsError) as exc:
        typer.echo(f"error: FULL source-replay binding failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        "OK experimental semantic-dimensions sidecar verified through FULL source-replay binding "
        f"integrity_sha256={document.integrity_sha256}"
    )


def _echo_corpus_result(result: CorpusReplayResult) -> None:
    typer.echo(
        json.dumps(
            {
                "corpus_id": result.corpus_id,
                "families": list(result.families),
                "manifest_sha256": result.manifest_sha256,
                "mode": result.mode,
                "source_count": result.source_count,
                "status": "EXPERIMENTAL_NOT_ADJUDICATED",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _echo_governance_result(result: GovernanceVerificationResult) -> None:
    typer.echo(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))


@governance_app.command("verify-labeling")
def governance_verify_labeling_cmd(
    packet: Path = typer.Argument(..., help="Canonical neutral labeling packet JSON"),
    packet_sha256: str = typer.Option(
        ..., "--packet-sha256", help="Independently frozen packet SHA-256"
    ),
    source_manifest: Path = typer.Option(
        ..., "--source-manifest", help="Canonical frozen M1 source manifest"
    ),
    submissions_root: Path = typer.Option(
        ..., "--submissions-root", help="Dedicated exact-root independent submissions"
    ),
    ledger: Path = typer.Option(..., "--ledger", help="Canonical adjudication ledger JSON"),
    ledger_sha256: str = typer.Option(
        ..., "--ledger-sha256", help="Independently frozen ledger SHA-256"
    ),
    source_manifest_sha256: str = typer.Option(
        ..., "--source-manifest-sha256", help="Independent source-manifest trust anchor"
    ),
    blind_split_manifest: Path = typer.Option(
        ..., "--blind-split-manifest", help="Canonical frozen blind-split manifest"
    ),
    split_manifest_sha256: str = typer.Option(
        ..., "--split-manifest-sha256", help="Independent blind-split trust anchor"
    ),
    prior_ledger: Path | None = typer.Option(
        None,
        "--prior-ledger",
        help="Required exact prior ledger for a post-freeze correction",
    ),
    prior_ledger_sha256: str | None = typer.Option(
        None,
        "--prior-ledger-sha256",
        help="Independent SHA-256 for --prior-ledger",
    ),
    acceptance_policy: Path = typer.Option(
        Path("acceptance/m1_m2_prereg_v1.json"),
        "--acceptance-policy",
        help="Exact frozen M1/M2 policy",
    ),
) -> None:
    """Verify neutral packets, independent submissions, and retained decisions."""

    try:
        result = verify_labeling_governance(
            packet_path=packet,
            expected_packet_sha256=packet_sha256,
            source_manifest_path=source_manifest,
            submissions_root=submissions_root,
            ledger_path=ledger,
            expected_ledger_sha256=ledger_sha256,
            expected_source_manifest_sha256=source_manifest_sha256,
            blind_split_manifest_path=blind_split_manifest,
            expected_split_manifest_sha256=split_manifest_sha256,
            acceptance_policy_path=acceptance_policy,
            prior_ledger_path=prior_ledger,
            expected_prior_ledger_sha256=prior_ledger_sha256,
        )
    except GovernanceContractError as exc:
        typer.echo(f"error: labeling governance rejected: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary
        typer.echo(f"error: labeling governance failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    _echo_governance_result(result)


@governance_app.command("verify-blind-split")
def governance_verify_blind_split_cmd(
    manifest: Path = typer.Argument(..., help="Canonical blind-split manifest JSON"),
    manifest_sha256: str = typer.Option(
        ..., "--manifest-sha256", help="Independently frozen split-manifest SHA-256"
    ),
    source_manifest: Path = typer.Option(
        ..., "--source-manifest", help="Canonical frozen M1 source manifest"
    ),
    source_manifest_sha256: str = typer.Option(
        ..., "--source-manifest-sha256", help="Independent source-manifest trust anchor"
    ),
    acceptance_policy: Path = typer.Option(
        Path("acceptance/m1_m2_prereg_v1.json"),
        "--acceptance-policy",
        help="Exact frozen M1/M2 policy",
    ),
) -> None:
    """Verify whole-document and whole-lineage blind split governance."""

    try:
        result = verify_blind_split(
            manifest_path=manifest,
            expected_manifest_sha256=manifest_sha256,
            source_manifest_path=source_manifest,
            expected_source_manifest_sha256=source_manifest_sha256,
            acceptance_policy_path=acceptance_policy,
        )
    except GovernanceContractError as exc:
        typer.echo(f"error: blind-split governance rejected: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary
        typer.echo(f"error: blind-split governance failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    _echo_governance_result(result)


def _echo_recipe_evidence_result(result: SourceRecipeEvidenceResult) -> None:
    typer.echo(
        json.dumps(
            {
                "acceptance": "NOT_EVALUATED",
                "corpus_id": result.corpus_id,
                "families": list(result.families),
                "inventory_sha256": result.inventory_sha256,
                "manifest_sha256": result.manifest_sha256,
                "mode": result.mode,
                "source_count": result.source_count,
                "status": "EXPERIMENTAL_NOT_ADJUDICATED",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


@corpus_app.command("acquire")
def corpus_acquire_cmd(
    manifest: Path = typer.Argument(..., help="Strict M1 source manifest JSON"),
    snapshot_root: Path = typer.Option(..., "--snapshot-root", help="Dedicated empty root"),
    manifest_sha256: str = typer.Option(
        ...,
        "--manifest-sha256",
        help="Externally frozen manifest SHA-256",
    ),
    acceptance_policy: Path = typer.Option(
        Path("acceptance/m1_m2_prereg_v1.json"),
        "--acceptance-policy",
        help="Frozen pre-result acceptance policy bound by the manifest",
    ),
    timeout_seconds: float = typer.Option(30.0, "--timeout-seconds", min=0.1, max=300.0),
) -> None:
    """Acquire pinned source bytes; all checks pass before any output is committed."""
    try:
        result = acquire_corpus(
            manifest,
            snapshot_root,
            manifest_sha256=manifest_sha256,
            acceptance_policy_path=acceptance_policy,
            timeout_seconds=timeout_seconds,
        )
    except (AcquisitionError, PathSafetyError) as exc:
        typer.echo(f"error: M1 source acquisition rejected: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary
        typer.echo(f"error: M1 source acquisition failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    _echo_corpus_result(result)


@corpus_app.command("verify-sources")
def corpus_verify_sources_cmd(
    manifest: Path = typer.Argument(..., help="Strict M1 source manifest JSON"),
    snapshot_root: Path = typer.Option(..., "--snapshot-root", help="Dedicated corpus root"),
    manifest_sha256: str = typer.Option(
        ...,
        "--manifest-sha256",
        help="Externally frozen manifest SHA-256",
    ),
    acceptance_policy: Path = typer.Option(
        Path("acceptance/m1_m2_prereg_v1.json"),
        "--acceptance-policy",
        help="Frozen pre-result acceptance policy bound by the manifest",
    ),
) -> None:
    """Verify pinned bytes, receipts, provenance, and adapters with no network access."""
    try:
        result = verify_corpus_offline(
            manifest,
            snapshot_root,
            manifest_sha256=manifest_sha256,
            acceptance_policy_path=acceptance_policy,
        )
    except AcquisitionError as exc:
        typer.echo(f"error: M1 source replay rejected: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary
        typer.echo(f"error: M1 source replay failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    _echo_corpus_result(result)


@corpus_app.command("verify-recipe-evidence")
def corpus_verify_recipe_evidence_cmd(
    evidence_root: Path = typer.Argument(
        ...,
        help="Dedicated exact-root directory containing source recipes only",
    ),
    inventory_sha256: str = typer.Option(
        ...,
        "--inventory-sha256",
        help="Externally frozen SHA-256 of EVIDENCE.sha256",
    ),
    manifest_sha256: str = typer.Option(
        ...,
        "--manifest-sha256",
        help="Externally frozen SHA-256 of source-manifest.json",
    ),
    acceptance_policy: Path = typer.Option(
        Path("acceptance/m1_m2_prereg_v1.json"),
        "--acceptance-policy",
        help="Frozen pre-result acceptance policy bound by the manifest",
    ),
) -> None:
    """Verify the development source-recipe evidence root without network access."""
    try:
        result = verify_source_recipe_evidence(
            evidence_root,
            expected_inventory_sha256=inventory_sha256,
            expected_manifest_sha256=manifest_sha256,
            acceptance_policy_path=acceptance_policy,
        )
    except (AcquisitionError, EvidenceInventoryError) as exc:
        typer.echo(f"error: M1 source-recipe evidence rejected: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary
        typer.echo(f"error: M1 source-recipe evidence failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    _echo_recipe_evidence_result(result)


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
    typer.echo(f"wrote {len(doc.requirements)} requirements ({family}) -> {out}")


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
        f"diff complete: {len(report.old_requirements)}->{len(report.new_requirements)} "
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
        "working_html_sha256": __import__("hashlib").sha256(adapted.working_html).hexdigest(),
    }
    atomic_write_text(
        out,
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
    )
    typer.echo(f"ingested {adapted.family.value} -> {out}")


@app.command("lineage")
def lineage_cmd(
    documents: list[Path] = typer.Argument(..., help="Ordered document versions (2+)"),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
    json_out: Path = typer.Option(..., "--json", help="Lineage graph JSON path"),
) -> None:
    """Build a requirement lineage graph across ordered document versions."""
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
        f"{len(graph.edges)} edges, {len(graph.ambiguity_queue)} ambiguities -> {json_out}"
    )


@app.command("verify-lineage")
def verify_lineage_cmd(
    graph_path: Path = typer.Argument(..., help="Canonical LineageGraph v1 JSON"),
    documents: list[Path] = typer.Argument(..., help="Ordered source document versions (2+)"),
    graph_sha256: str = typer.Option(
        ..., "--graph-sha256", help="Independently held SHA-256 of exact graph bytes"
    ),
    profile: ProfileOpt = typer.Option(ProfileOpt.rfc2119, "--profile"),
    adapter: AdapterOpt = typer.Option(AdapterOpt.auto, "--adapter"),
) -> None:
    """Verify an experimental LineageGraph through an anchored ordered-source replay."""
    try:
        graph = verify_lineage_graph_file(
            graph_path,
            graph_sha256=graph_sha256,
            documents=documents,
            profile=_to_profile(profile),
            adapter=_to_adapter(adapter),
        )
    except (OSError, LineageContractError) as exc:
        typer.echo(f"error: lineage source-replay binding failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        "OK LINEAGE_GRAPH_REPLAY_ONLY external_acceptance=false "
        "exact caller-supplied ordered-source/profile/adapter replay "
        f"integrity_sha256={graph.integrity['content_sha256']}"
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
        f"class_f1={report.classification.get('f1')} -> {out}"
    )
    if not report.ok:
        for c in report.case_results:
            if not c.passed:
                typer.echo(f"  FAIL {c.case_id}: {c.detail}", err=True)
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
