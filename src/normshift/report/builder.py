"""Build evidence-linked JSON and Markdown reports."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from normshift import __version__
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.model.types import (
    Change,
    DocumentSnapshot,
    IntegrityEnvelope,
    ProfileName,
    Report,
    ReportSummary,
    Requirement,
)

SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0.0"})
SUPPORTED_TOOL_VERSIONS = frozenset({__version__})


def build_report(
    *,
    profile: ProfileName,
    old_document: DocumentSnapshot,
    new_document: DocumentSnapshot,
    old_requirements: list[Requirement],
    new_requirements: list[Requirement],
    changes: list[Change],
) -> Report:
    counts = Counter(c.classification.value for c in changes)
    summary = ReportSummary(
        old_requirement_count=len(old_requirements),
        new_requirement_count=len(new_requirements),
        change_count=len(changes),
        classification_counts=dict(sorted(counts.items())),
    )
    report = Report(
        schema_version="1.0.0",
        tool_version=__version__,
        profile=profile,
        old_document=old_document,
        new_document=new_document,
        old_requirements=old_requirements,
        new_requirements=new_requirements,
        changes=changes,
        summary=summary,
        integrity=IntegrityEnvelope(alg="sha256", content_sha256=""),
    )
    data = report.model_dump(mode="json")
    digest = integrity_payload_hash(data)
    report.integrity = IntegrityEnvelope(alg="sha256", content_sha256=digest)
    return report


def report_to_dict(report: Report) -> dict[str, Any]:
    return report.model_dump(mode="json")


def write_json_report(report: Report, path: Path) -> str:
    from normshift.io_safety import atomic_write_bytes

    data = report_to_dict(report)
    digest = integrity_payload_hash(data)
    data["integrity"] = {"alg": "sha256", "content_sha256": digest}
    raw = canonical_json_bytes(data)
    atomic_write_bytes(path, raw)
    return hashlib_sha256(raw)


def hashlib_sha256(raw: bytes) -> str:
    import hashlib

    return hashlib.sha256(raw).hexdigest()


def markdown_report_text(report: Report) -> str:
    lines: list[str] = []
    lines.append("# NormShift Diff Report")
    lines.append("")
    lines.append(f"- Tool version: `{report.tool_version}`")
    lines.append(f"- Profile: `{report.profile.value}`")
    lines.append(f"- Schema version: `{report.schema_version}`")
    lines.append(
        f"- Integrity: `{report.integrity.alg}` `{report.integrity.content_sha256}`"
    )
    lines.append("")
    lines.append("## Documents")
    lines.append("")
    lines.append("| Side | Path | Version | SHA-256 | Bytes |")
    lines.append("|------|------|---------|---------|-------|")
    for label, doc in (("old", report.old_document), ("new", report.new_document)):
        lines.append(
            f"| {label} | `{doc.path}` | `{doc.version}` | `{doc.sha256}` | {doc.byte_length} |"
        )
    lines.append("")
    lines.append("### Provenance")
    lines.append("")
    for label, doc in (("old", report.old_document), ("new", report.new_document)):
        prov = doc.provenance
        if prov is None:
            lines.append(f"- {label}: _(none)_")
            continue
        lines.append(
            f"- **{label}**: family=`{prov.document_family.value}` "
            f"adapter=`{prov.adapter_id}`@{prov.adapter_version} "
            f"type=`{prov.content_type}`"
        )
        if prov.canonical_source:
            lines.append(f"  - canonical: `{prov.canonical_source}`")
        if prov.etag:
            lines.append(f"  - etag: `{prov.etag}`")
        lines.append(f"  - local_path (portable): `{prov.local_path}`")

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Old requirements: **{report.summary.old_requirement_count}**")
    lines.append(f"- New requirements: **{report.summary.new_requirement_count}**")
    lines.append(f"- Changes: **{report.summary.change_count}**")
    lines.append("")
    lines.append("### Classification counts")
    lines.append("")
    counts = report.summary.classification_counts
    if counts:
        for k, v in counts.items():
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Changes")
    lines.append("")
    for ch in report.changes:
        lines.append(f"### `{ch.classification.value}` — `{ch.change_id}`")
        lines.append("")
        lines.append(f"- Confidence: `{ch.confidence}`")
        lines.append(f"- Modality transition: `{ch.modality_transition}`")
        if ch.old_requirement_id:
            lines.append(f"- Old requirement: `{ch.old_requirement_id}`")
        if ch.new_requirement_id:
            lines.append(f"- New requirement: `{ch.new_requirement_id}`")
        if ch.old_section_path:
            lines.append(f"- Old section: {ch.old_section_path}")
        if ch.new_section_path:
            lines.append(f"- New section: {ch.new_section_path}")
        if ch.old_source_locator:
            lines.append(f"- Old locator: `{ch.old_source_locator}`")
        if ch.new_source_locator:
            lines.append(f"- New locator: `{ch.new_source_locator}`")
        if ch.old_text:
            lines.append(f"- Old text: {ch.old_text}")
        if ch.new_text:
            lines.append(f"- New text: {ch.new_text}")
        if ch.classification_reasons:
            lines.append("- Reasons:")
            for r in ch.classification_reasons:
                lines.append(f"  - {r}")
        if ch.alignment_score is not None:
            s = ch.alignment_score
            lines.append("- Alignment score components:")
            lines.append(f"  - combined: `{s.combined}`")
            for key, val in sorted(s.components.items()):
                lines.append(f"  - {key}: `{val}`")
        if ch.evidence_hashes:
            lines.append("- Evidence hashes:")
            for h in ch.evidence_hashes:
                lines.append(f"  - `{h}`")
        lines.append("")

    return "\n".join(lines)


def write_markdown_report(report: Report, path: Path) -> None:
    from normshift.io_safety import atomic_write_text

    atomic_write_text(path, markdown_report_text(report))
