"""End-to-end diff pipeline orchestration (single source snapshot per input)."""

from __future__ import annotations

from pathlib import Path

from normshift.adapters.errors import AdapterError
from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.extract.extractor import extract_from_source
from normshift.io_safety import PathSafetyError, assert_outputs_safe, write_transaction
from normshift.model.types import AdapterName, IntegrityEnvelope, ProfileName, Report
from normshift.paths_root import SourceRootError, default_source_root, resolve_under_source_root
from normshift.report.builder import build_report, markdown_report_text, report_to_dict
from normshift.source import ImmutableSource, load_immutable_source


def run_diff(
    old_path: Path,
    new_path: Path,
    *,
    profile: ProfileName,
    adapter: AdapterName = AdapterName.AUTO,
    json_out: Path | None = None,
    markdown_out: Path | None = None,
    old_source: ImmutableSource | None = None,
    new_source: ImmutableSource | None = None,
    source_root: Path | None = None,
) -> Report:
    """Run diff pipeline from single-read sources. Fail closed on path collisions."""
    inputs = [Path(old_path), Path(new_path)]
    if json_out is not None or markdown_out is not None:
        assert_outputs_safe(
            inputs=inputs,
            outputs=[json_out, markdown_out],
            labels=["--json", "--markdown"],
        )

    root = Path(source_root).resolve() if source_root is not None else default_source_root()

    try:
        if old_source is None:
            abs_old, ref_old = resolve_under_source_root(root, Path(old_path))
            old_src = load_immutable_source(
                abs_old, adapter=adapter, portable_ref=ref_old
            )
        else:
            old_src = old_source
        if new_source is None:
            abs_new, ref_new = resolve_under_source_root(root, Path(new_path))
            new_src = load_immutable_source(
                abs_new, adapter=adapter, portable_ref=ref_new
            )
        else:
            new_src = new_source
        old_doc = extract_from_source(old_src, profile)
        new_doc = extract_from_source(new_src, profile)
    except (AdapterError, PathSafetyError, SourceRootError):
        raise

    pairs = align_requirements(old_doc.requirements, new_doc.requirements)
    changes = classify_pairs(pairs)

    report = build_report(
        profile=profile,
        old_document=old_src.to_snapshot(),
        new_document=new_src.to_snapshot(),
        old_requirements=old_doc.requirements,
        new_requirements=new_doc.requirements,
        changes=changes,
    )

    artifacts: dict[Path, bytes] = {}
    if json_out is not None:
        data = report_to_dict(report)
        digest = integrity_payload_hash(data)
        data["integrity"] = {"alg": "sha256", "content_sha256": digest}
        report.integrity = IntegrityEnvelope(alg="sha256", content_sha256=digest)
        artifacts[Path(json_out)] = canonical_json_bytes(data)
    if markdown_out is not None:
        artifacts[Path(markdown_out)] = markdown_report_text(report).encode("utf-8")

    if artifacts:
        write_transaction(artifacts)

    return report
