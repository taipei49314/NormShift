"""Strict source-bound verification via deterministic pipeline replay."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.evidence.hashing import integrity_payload_hash
from normshift.extract.extractor import extract_from_source
from normshift.model.types import (
    AdapterName,
    Change,
    ChangeClassification,
    ProfileName,
    Report,
    Requirement,
)
from normshift.source import load_immutable_source


@dataclass
class VerifyResult:
    ok: bool
    errors: list[str]
    content_sha256: str | None = None


_ADAPTER_FROM_ID: dict[str, AdapterName] = {
    "normshift.adapters.html": AdapterName.HTML,
    "normshift.adapters.rfc": AdapterName.RFC,
    "normshift.adapters.w3c": AdapterName.W3C,
    "normshift.adapters.whatwg": AdapterName.WHATWG,
    "normshift.adapters.auto": AdapterName.AUTO,
}


def _load_bundled_schema(name: str) -> dict[str, Any]:
    try:
        pkg = resources.files("normshift") / "schemas" / name
        if pkg.is_file():
            loaded = json.loads(pkg.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return dict(loaded)
    except Exception:
        pass
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
    override: Path | None,
    side: str,
) -> Path:
    if override is not None:
        p = Path(override)
        if not p.is_file():
            raise FileNotFoundError(f"{side} override source not found: {p}")
        return p
    declared_path = Path(declared)
    if source_root is not None:
        root = source_root.resolve()
        # Absolute declared path: allow only if it is a file under source_root
        if declared_path.is_absolute():
            try:
                declared_path.resolve().relative_to(root)
            except ValueError as exc:
                raise FileNotFoundError(
                    f"{side} absolute path escapes source-root: {declared}"
                ) from exc
            if declared_path.is_file():
                return declared_path
            raise FileNotFoundError(f"{side} source not found: {declared}")
        cand = (root / declared).resolve()
        try:
            cand.relative_to(root)
        except ValueError as exc:
            raise FileNotFoundError(
                f"{side} path escapes source-root: {declared}"
            ) from exc
        if cand.is_file():
            return cand
        raise FileNotFoundError(
            f"{side} source not found under source-root: {declared}"
        )
    if declared_path.is_file():
        return declared_path
    raise FileNotFoundError(
        f"{side} source not found: {declared} "
        "(provide --source-root or --old-source/--new-source)"
    )


def _adapter_from_report(doc_side: Any) -> AdapterName:
    prov = getattr(doc_side, "provenance", None)
    if prov is None:
        return AdapterName.AUTO
    aid = getattr(prov, "adapter_id", None) or ""
    return _ADAPTER_FROM_ID.get(str(aid), AdapterName.AUTO)


def _req_key(r: Requirement) -> tuple[Any, ...]:
    return (
        r.requirement_id,
        r.document_sha256,
        r.document_version,
        r.section_path,
        r.source_locator,
        r.original_text,
        r.normalized_text,
        r.modality.value,
        r.polarity.value,
        r.actor,
        r.action,
        r.condition,
        r.exception,
        round(r.confidence, 4),
        r.extractor_version,
        r.fingerprint,
        r.structural_index,
    )


def _change_key(c: Change) -> tuple[Any, ...]:
    align = None
    if c.alignment_score is not None:
        align = (
            c.alignment_score.combined,
            c.alignment_score.text_similarity,
            c.alignment_score.modality_match,
            c.alignment_score.section_similarity,
            c.alignment_score.token_similarity,
            c.alignment_score.actor_action_similarity,
            c.alignment_score.structural_proximity,
            tuple(sorted(c.alignment_score.components.items())),
        )
    return (
        c.change_id,
        c.old_requirement_id,
        c.new_requirement_id,
        c.classification.value,
        round(c.confidence, 4),
        tuple(c.classification_reasons),
        c.old_source_locator,
        c.new_source_locator,
        c.old_text,
        c.new_text,
        c.modality_transition,
        tuple(c.evidence_hashes),
        align,
        c.old_section_path,
        c.new_section_path,
    )


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

    integrity = data.get("integrity") or {}
    if integrity.get("alg") != "sha256":
        errors.append(f"Unsupported or missing integrity algorithm: {integrity.get('alg')}")
    expected_hash = integrity_payload_hash(data)
    actual = integrity.get("content_sha256")
    if not actual:
        errors.append("Missing integrity.content_sha256")
    elif actual != expected_hash:
        errors.append(
            f"Integrity hash mismatch: reported={actual} computed={expected_hash}"
        )

    if not require_sources:
        ok = len(errors) == 0
        return VerifyResult(ok=ok, errors=errors, content_sha256=expected_hash)

    # Resolve sources without basename guessing
    try:
        old_path = _resolve_source_path(
            report.old_document.path,
            source_root=source_root,
            override=old_source,
            side="old",
        )
        new_path = _resolve_source_path(
            report.new_document.path,
            source_root=source_root,
            override=new_source,
            side="new",
        )
    except FileNotFoundError as exc:
        errors.append(str(exc))
        return VerifyResult(ok=False, errors=errors, content_sha256=expected_hash)

    old_adapter = _adapter_from_report(report.old_document)
    new_adapter = _adapter_from_report(report.new_document)

    try:
        old_src = load_immutable_source(old_path, adapter=old_adapter)
        new_src = load_immutable_source(new_path, adapter=new_adapter)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to load sources for replay: {exc}")
        return VerifyResult(ok=False, errors=errors, content_sha256=expected_hash)

    # Snapshot / provenance binding
    for side, snap, src in (
        ("old", report.old_document, old_src),
        ("new", report.new_document, new_src),
    ):
        if snap.sha256 != src.sha256:
            errors.append(
                f"{side} source SHA-256 mismatch: file={src.sha256} report={snap.sha256}"
            )
        if snap.byte_length != src.byte_length:
            errors.append(
                f"{side} byte_length mismatch: file={src.byte_length} "
                f"report={snap.byte_length}"
            )
        if snap.version != src.document_version:
            errors.append(
                f"{side} version mismatch: file={src.document_version} "
                f"report={snap.version}"
            )
        if snap.document_family is not None and snap.document_family != src.family:
            errors.append(f"{side} document_family mismatch")
        if snap.provenance is None:
            errors.append(f"{side} provenance missing")
        else:
            if snap.provenance.content_sha256 != src.sha256:
                errors.append(f"{side} provenance.content_sha256 mismatch")
            if snap.provenance.byte_length != src.byte_length:
                errors.append(f"{side} provenance.byte_length mismatch")
            if snap.provenance.adapter_id != src.provenance.adapter_id:
                errors.append(f"{side} provenance.adapter_id mismatch")
            if snap.provenance.normalization_version != src.provenance.normalization_version:
                errors.append(f"{side} provenance.normalization_version mismatch")
            # Provenance paths compared after resolve (relative vs absolute same file)
            try:
                same_local = Path(snap.provenance.local_path).resolve() == Path(
                    src.provenance.local_path
                ).resolve()
            except OSError:
                same_local = snap.provenance.local_path == src.provenance.local_path
            if not same_local:
                errors.append(
                    f"{side} provenance.local_path does not match source load "
                    f"({snap.provenance.local_path!r} vs {src.provenance.local_path!r})"
                )
            if snap.provenance.canonical_source != src.provenance.canonical_source:
                errors.append(f"{side} provenance.canonical_source mismatch")
            if snap.provenance.etag != src.provenance.etag:
                errors.append(f"{side} provenance.etag mismatch")

    # Deterministic extraction replay
    if isinstance(report.profile, ProfileName):
        profile = report.profile
    else:
        profile = ProfileName(report.profile)
    try:
        old_doc = extract_from_source(old_src, profile)
        new_doc = extract_from_source(new_src, profile)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Replay extraction failed: {exc}")
        return VerifyResult(ok=False, errors=errors, content_sha256=expected_hash)

    # Compare full requirement arrays (order-independent multiset of keys)
    old_rep = sorted(_req_key(r) for r in report.old_requirements)
    old_live = sorted(_req_key(r) for r in old_doc.requirements)
    if old_rep != old_live:
        errors.append(
            "Old requirements do not match deterministic replay extraction "
            f"(report={len(old_rep)} replay={len(old_live)})"
        )
    new_rep = sorted(_req_key(r) for r in report.new_requirements)
    new_live = sorted(_req_key(r) for r in new_doc.requirements)
    if new_rep != new_live:
        errors.append(
            "New requirements do not match deterministic replay extraction "
            f"(report={len(new_rep)} replay={len(new_live)})"
        )

    # Unique IDs
    if len({r.requirement_id for r in report.old_requirements}) != len(report.old_requirements):
        errors.append("Duplicate old requirement IDs")
    if len({r.requirement_id for r in report.new_requirements}) != len(report.new_requirements):
        errors.append("Duplicate new requirement IDs")

    # Replay alignment + classification
    pairs = align_requirements(old_doc.requirements, new_doc.requirements)
    live_changes = classify_pairs(pairs)
    live_keys = sorted(_change_key(c) for c in live_changes)
    rep_keys = sorted(_change_key(c) for c in report.changes)
    if live_keys != rep_keys:
        errors.append(
            "Changes do not match deterministic replay alignment/classification "
            f"(report={len(rep_keys)} replay={len(live_keys)})"
        )

    # Referential invariants on report changes
    old_ids = {r.requirement_id for r in report.old_requirements}
    new_ids = {r.requirement_id for r in report.new_requirements}
    change_ids = [c.change_id for c in report.changes]
    if len(change_ids) != len(set(change_ids)):
        errors.append("Duplicate change IDs")

    paired_old_use: list[str] = []
    paired_new_use: list[str] = []
    for ch in report.changes:
        oid, nid = ch.old_requirement_id, ch.new_requirement_id
        cls = ch.classification
        if cls == ChangeClassification.ADDED:
            if oid is not None:
                errors.append(f"ADDED {ch.change_id} must have null old_requirement_id")
            if nid is None or nid not in new_ids:
                errors.append(f"ADDED {ch.change_id} needs valid new_requirement_id")
        elif cls == ChangeClassification.REMOVED:
            if nid is not None:
                errors.append(f"REMOVED {ch.change_id} must have null new_requirement_id")
            if oid is None or oid not in old_ids:
                errors.append(f"REMOVED {ch.change_id} needs valid old_requirement_id")
        else:
            if oid is None or nid is None:
                errors.append(
                    f"Paired class {cls.value} change {ch.change_id} requires both IDs"
                )
            else:
                if oid not in old_ids:
                    errors.append(f"dangling old_requirement_id={oid}")
                if nid not in new_ids:
                    errors.append(f"dangling new_requirement_id={nid}")
                paired_old_use.append(oid)
                paired_new_use.append(nid)

    # One-to-one coverage: no duplicate consumption in ordinary paired classes
    if len(paired_old_use) != len(set(paired_old_use)):
        errors.append("Duplicate old requirement coverage in paired changes")
    if len(paired_new_use) != len(set(paired_new_use)):
        errors.append("Duplicate new requirement coverage in paired changes")

    # Summary
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

    # Live summary must also match
    live_summary_counts = Counter(c.classification.value for c in live_changes)
    summary_mismatch = (
        len(old_doc.requirements) != summary.get("old_requirement_count")
        or len(new_doc.requirements) != summary.get("new_requirement_count")
        or len(live_changes) != summary.get("change_count")
        or dict(sorted(live_summary_counts.items()))
        != dict(sorted((reported_counts or {}).items()))
    )
    if summary_mismatch and "summary" not in " ".join(errors).lower():
        errors.append("summary does not match replayed extraction/classification")

    ok = len(errors) == 0
    return VerifyResult(ok=ok, errors=errors, content_sha256=expected_hash)
