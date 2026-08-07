"""End-to-end diff pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.extract.extractor import extract_requirements
from normshift.model.types import ProfileName, Report
from normshift.report.builder import build_report, write_json_report, write_markdown_report
from normshift.snapshot import snapshot_document


def run_diff(
    old_path: Path,
    new_path: Path,
    *,
    profile: ProfileName,
    json_out: Path | None = None,
    markdown_out: Path | None = None,
) -> Report:
    old_doc = extract_requirements(old_path, profile)
    new_doc = extract_requirements(new_path, profile)
    old_snap, _ = snapshot_document(old_path)
    new_snap, _ = snapshot_document(new_path)

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

    if json_out is not None:
        write_json_report(report, json_out)
        # Reload integrity from written form
        from normshift.evidence.hashing import integrity_payload_hash
        from normshift.report.builder import report_to_dict

        data = report_to_dict(report)
        report.integrity = {
            "alg": "sha256",
            "content_sha256": integrity_payload_hash(data),
        }
        # Ensure file matches final integrity (write_json_report already sets it).
        write_json_report(report, json_out)

    if markdown_out is not None:
        write_markdown_report(report, markdown_out)

    return report
