"""Strict source-aware report verification (fail closed)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from normshift.evidence.hashing import evidence_hash, integrity_payload_hash
from normshift.extract.extractor import fingerprint_requirement
from normshift.model.types import ChangeClassification, Report, Requirement


@dataclass
class VerifyResult:
    ok: bool
    errors: list[str]
    content_sha256: str | None = None


def _load_bundled_schema(name: str) -> dict[str, Any]:
    """Load schema from packaged data; fail if missing."""
    # Prefer package data under normshift/schemas
    try:
        pkg = resources.files("normshift") / "schemas" / name
        if pkg.is_file():
            loaded = json.loads(pkg.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return dict(loaded)
    except Exception:
        pass
    # Fallback to repo root schemas for editable installs
    candidates = [
        Path(__file__).resolve().parents[3] / "schemas" / name,
        Path(__file__).resolve().parents[1] / "schemas" / name,
        Path.cwd() / "schemas" / name,
    ]
    for p in candidates:
        if p.is_file():
            loaded = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return dict(loaded)
    raise FileNotFoundError(f"Required schema not found: {name}")


def _resolve_source_path(
    declared: str,
    *,
    source_root: Path | None,
    old_override: Path | None,
    new_override: Path | None,
    side: str,
) -> Path:
    if side == "old" and old_override is not None:
        return Path(old_override)
    if side == "new" and new_override is not None:
        return Path(new_override)
    p = Path(declared)
    if p.is_file():
        return p
    if source_root is not None:
        cand = source_root / declared
        if cand.is_file():
            return cand
        cand2 = source_root / Path(declared).name
        if cand2.is_file():
            return cand2
    # try CWD-relative
    if Path(declared).is_file():
        return Path(declared)
    raise FileNotFoundError(f"Source not found for {side}: {declared}")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _change_id(parts: list[str]) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


def _recompute_evidence_hashes(change: dict[str, Any]) -> list[str]:
    hashes: list[str] = []
    if change.get("old_text"):
        hashes.append(evidence_hash("old_text", str(change["old_text"])))
    if change.get("old_source_locator"):
        hashes.append(evidence_hash("old_locator", str(change["old_source_locator"])))
    if change.get("new_text"):
        hashes.append(evidence_hash("new_text", str(change["new_text"])))
    if change.get("new_source_locator"):
        hashes.append(evidence_hash("new_locator", str(change["new_source_locator"])))
    if change.get("classification"):
        hashes.append(evidence_hash("classification", str(change["classification"])))
    return sorted(set(hashes))


def verify_report_file(
    path: Path,
    *,
    source_root: Path | None = None,
    old_source: Path | None = None,
    new_source: Path | None = None,
    require_sources: bool = True,
) -> VerifyResult:
    errors: list[str] = []
    if not path.is_file():
        return VerifyResult(ok=False, errors=[f"Report file not found: {path}"])

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return VerifyResult(ok=False, errors=[f"Failed to read/parse JSON: {exc}"])

    if not isinstance(data, dict):
        return VerifyResult(ok=False, errors=["Report root must be a JSON object"])

    # Schema (required)
    try:
        schema = _load_bundled_schema("report.schema.json")
    except FileNotFoundError as exc:
        return VerifyResult(ok=False, errors=[str(exc)])

    try:
        import jsonschema

        jsonschema.validate(instance=data, schema=schema)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"JSON Schema validation failed: {exc}")

    try:
        report = Report.model_validate(data)
    except ValidationError as exc:
        errors.append(f"Pydantic validation failed: {exc}")
        return VerifyResult(ok=False, errors=errors)

    # Integrity
    integrity = data.get("integrity") or {}
    if integrity.get("alg") != "sha256":
        errors.append(f"Unsupported or missing integrity algorithm: {integrity.get('alg')}")
    expected = integrity_payload_hash(data)
    actual = integrity.get("content_sha256")
    if not actual:
        errors.append("Missing integrity.content_sha256")
    elif actual != expected:
        errors.append(
            f"Integrity hash mismatch: reported={actual} computed={expected}"
        )

    # Source snapshot checks
    if require_sources:
        for side, doc in (("old", report.old_document), ("new", report.new_document)):
            try:
                src_path = _resolve_source_path(
                    doc.path,
                    source_root=source_root,
                    old_override=old_source,
                    new_override=new_source,
                    side=side,
                )
            except FileNotFoundError as exc:
                errors.append(str(exc))
                continue
            try:
                raw = src_path.read_bytes()
            except OSError as exc:
                errors.append(f"Cannot read {side} source: {exc}")
                continue
            digest = hashlib.sha256(raw).hexdigest()
            if digest != doc.sha256:
                errors.append(
                    f"{side} source SHA-256 mismatch: file={digest} report={doc.sha256}"
                )
            if len(raw) != doc.byte_length:
                errors.append(
                    f"{side} source byte_length mismatch: file={len(raw)} report={doc.byte_length}"
                )
            if doc.provenance is not None:
                if doc.provenance.content_sha256 != doc.sha256:
                    errors.append(f"{side} provenance.content_sha256 disagrees with snapshot")
                if doc.provenance.byte_length != doc.byte_length:
                    errors.append(f"{side} provenance.byte_length disagrees with snapshot")

    # Requirements ownership and uniqueness
    old_by_id = {r.requirement_id: r for r in report.old_requirements}
    new_by_id = {r.requirement_id: r for r in report.new_requirements}
    if len(old_by_id) != len(report.old_requirements):
        errors.append("Duplicate old requirement IDs")
    if len(new_by_id) != len(report.new_requirements):
        errors.append("Duplicate new requirement IDs")

    for r in report.old_requirements:
        if r.document_sha256 != report.old_document.sha256:
            errors.append(
                f"Old requirement {r.requirement_id} document_sha256 mismatch"
            )
        if r.document_version != report.old_document.version:
            errors.append(
                f"Old requirement {r.requirement_id} document_version mismatch"
            )
        _check_requirement_recompute(r, errors, side="old")
    for r in report.new_requirements:
        if r.document_sha256 != report.new_document.sha256:
            errors.append(
                f"New requirement {r.requirement_id} document_sha256 mismatch"
            )
        if r.document_version != report.new_document.version:
            errors.append(
                f"New requirement {r.requirement_id} document_version mismatch"
            )
        _check_requirement_recompute(r, errors, side="new")

    # Changes
    for ch in report.changes:
        oid, nid = ch.old_requirement_id, ch.new_requirement_id
        cls = ch.classification
        if cls == ChangeClassification.ADDED:
            if oid is not None:
                errors.append(f"ADDED change {ch.change_id} must not have old_requirement_id")
            if nid is None or nid not in new_by_id:
                errors.append(f"ADDED change {ch.change_id} missing/invalid new_requirement_id")
        elif cls == ChangeClassification.REMOVED:
            if nid is not None:
                errors.append(f"REMOVED change {ch.change_id} must not have new_requirement_id")
            if oid is None or oid not in old_by_id:
                errors.append(f"REMOVED change {ch.change_id} missing/invalid old_requirement_id")
        else:
            if oid is not None and oid not in old_by_id:
                errors.append(
                    f"Change {ch.change_id} dangling old_requirement_id={oid}"
                )
            if nid is not None and nid not in new_by_id:
                errors.append(
                    f"Change {ch.change_id} dangling new_requirement_id={nid}"
                )

        # Text/locator consistency
        if oid and oid in old_by_id:
            oreq = old_by_id[oid]
            if ch.old_text is not None and ch.old_text != oreq.original_text:
                errors.append(f"Change {ch.change_id} old_text disagrees with requirement")
            if (
                ch.old_source_locator is not None
                and ch.old_source_locator != oreq.source_locator
            ):
                errors.append(f"Change {ch.change_id} old_source_locator disagrees")
        if nid and nid in new_by_id:
            nreq = new_by_id[nid]
            if ch.new_text is not None and ch.new_text != nreq.original_text:
                errors.append(f"Change {ch.change_id} new_text disagrees with requirement")
            if (
                ch.new_source_locator is not None
                and ch.new_source_locator != nreq.source_locator
            ):
                errors.append(f"Change {ch.change_id} new_source_locator disagrees")

        # Modality transition
        if oid and nid and oid in old_by_id and nid in new_by_id:
            expected_mt = f"{old_by_id[oid].modality.value}->{new_by_id[nid].modality.value}"
            if ch.modality_transition and ch.modality_transition != expected_mt:
                errors.append(
                    f"Change {ch.change_id} modality_transition mismatch "
                    f"(report={ch.modality_transition} expected={expected_mt})"
                )

        # Evidence hashes
        ch_dict = ch.model_dump(mode="json")
        expected_hashes = _recompute_evidence_hashes(ch_dict)
        if sorted(ch.evidence_hashes) != expected_hashes:
            errors.append(f"Change {ch.change_id} evidence_hashes mismatch")

        # Change ID
        expected_cid = _change_id(
            [
                cls.value,
                oid or "",
                nid or "",
                old_by_id[oid].normalized_text if oid and oid in old_by_id else "",
                new_by_id[nid].normalized_text if nid and nid in new_by_id else "",
            ]
        )
        # Note: classifier uses original change id algorithm with normalized texts
        # from requirements at classify time — recompute using stored texts
        expected_cid2 = _change_id(
            [
                cls.value,
                oid or "",
                nid or "",
                (
                    old_by_id[oid].normalized_text
                    if oid and oid in old_by_id
                    else (ch.old_text or "")
                ),
                (
                    new_by_id[nid].normalized_text
                    if nid and nid in new_by_id
                    else (ch.new_text or "")
                ),
            ]
        )
        if (
            oid
            and nid
            and oid in old_by_id
            and nid in new_by_id
            and ch.change_id not in {expected_cid, expected_cid2}
        ):
            errors.append(
                f"Change {ch.change_id} ID recompute mismatch (expected {expected_cid2})"
            )

    # Summary recomputation
    summary = report.summary or {}
    if summary.get("old_requirement_count") != len(report.old_requirements):
        errors.append("summary.old_requirement_count mismatch")
    if summary.get("new_requirement_count") != len(report.new_requirements):
        errors.append("summary.new_requirement_count mismatch")
    if summary.get("change_count") != len(report.changes):
        errors.append("summary.change_count mismatch")
    counts = Counter(c.classification.value for c in report.changes)
    reported_counts = summary.get("classification_counts") or {}
    if dict(sorted(counts.items())) != dict(sorted((reported_counts or {}).items())):
        errors.append("summary.classification_counts mismatch")

    ok = len(errors) == 0
    return VerifyResult(ok=ok, errors=errors, content_sha256=expected)


def _check_requirement_recompute(
    r: Requirement, errors: list[str], *, side: str
) -> None:
    fp = fingerprint_requirement(
        r.normalized_text,
        r.modality.value,
        r.actor,
        r.action,
        r.condition,
        r.exception,
    )
    if fp != r.fingerprint:
        errors.append(f"{side} requirement {r.requirement_id} fingerprint mismatch")
