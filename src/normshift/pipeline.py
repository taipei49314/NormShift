"""End-to-end diff pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from normshift.adapters.errors import AdapterError
from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.extract.extractor import extract_requirements
from normshift.model.types import AdapterName, ProfileName, Report
from normshift.report.builder import build_report, write_json_report, write_markdown_report
from normshift.snapshot import snapshot_document


def run_diff(
    old_path: Path,
    new_path: Path,
    *,
    profile: ProfileName,
    adapter: AdapterName = AdapterName.AUTO,
    json_out: Path | None = None,
    markdown_out: Path | None = None,
) -> Report:
    """Run diff pipeline. On adapter failure, do not write any output artifacts."""
    try:
        old_doc = extract_requirements(old_path, profile, adapter=adapter)
        new_doc = extract_requirements(new_path, profile, adapter=adapter)
        old_snap, _, _ = snapshot_document(old_path, adapter=adapter)
        new_snap, _, _ = snapshot_document(new_path, adapter=adapter)
    except AdapterError:
        # Fail closed: never leave partial success artifacts.
        if json_out is not None and json_out.is_file():
            # Do not delete user files that pre-existed; only avoid writing new ones.
            pass
        raise

    pairs = align_requirements(old_doc.requirements, new_doc.requirements)
    changes = classify_pairs(pairs)

    report = build_report(
        profile=profile,
        old_document=old_snap,
        new_document=new_snap,
        old_requirements=old_doc.requirements,
        new_requirements=new_doc.requirements,
        changes=changes,
    )

    try:
        if json_out is not None:
            write_json_report(report, json_out)
            from normshift.evidence.hashing import integrity_payload_hash
            from normshift.report.builder import report_to_dict

            data = report_to_dict(report)
            report.integrity = {
                "alg": "sha256",
                "content_sha256": integrity_payload_hash(data),
            }
            write_json_report(report, json_out)

        if markdown_out is not None:
            write_markdown_report(report, markdown_out)
    except Exception:
        # If writing fails mid-way, remove incomplete outputs we created this run.
        import contextlib

        for p in (json_out, markdown_out):
            if p is not None and p.is_file():
                with contextlib.suppress(OSError):
                    p.unlink()
        raise

    return report
