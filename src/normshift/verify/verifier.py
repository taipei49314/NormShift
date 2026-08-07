"""Strict source-bound verification via full canonical report replay."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from normshift import __version__
from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.evidence.hashing import integrity_payload_hash
from normshift.extract.extractor import extract_from_source
from normshift.model.types import (
    AdapterName,
    ChangeClassification,
    ProfileName,
    Report,
)
from normshift.report.builder import (
    SUPPORTED_SCHEMA_VERSIONS,
    SUPPORTED_TOOL_VERSIONS,
    build_report,
)
from normshift.source import load_immutable_source

_ADAPTER_FROM_ID: dict[str, AdapterName] = {
    "normshift.adapters.html": AdapterName.HTML,
    "normshift.adapters.rfc": AdapterName.RFC,
    "normshift.adapters.w3c": AdapterName.W3C,
    "normshift.adapters.whatwg": AdapterName.WHATWG,
    "normshift.adapters.auto": AdapterName.AUTO,
}


@dataclass
class VerifyResult:
    ok: bool
    errors: list[str]
    content_sha256: str | None = None
    override_used: bool = False


def _load_bundled_schema(name: str) -> dict[str, Any]:
    try:
        pkg = resources.files("normshift") / "schemas" / name
        if pkg.is_file():
            loaded = json.loads(pkg.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return dict(loaded)
    except Exception:
        pass
    for p in (
        Path(__file__).resolve().parents[3] / "schemas" / name,
        Path(__file__).resolve().parents[1] / "schemas" / name,
        Path.cwd() / "schemas" / name,
    ):
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
) -> tuple[Path, str]:
    """Return (filesystem_path, portable_ref used for provenance identity)."""
    if override is not None:
        p = Path(override)
        if not p.is_file():
            raise FileNotFoundError(f"{side} override source not found: {p}")
        # Override relocates identical bytes; portable identity remains declared ref
        return p, declared

    declared_path = Path(declared)
    if source_root is not None:
        root = source_root.resolve()
        if declared_path.is_absolute():
            raise FileNotFoundError(
                f"{side} portable reports must use relative source_ref under "
                f"--source-root, got absolute: {declared}"
            )
        # Reject traversal
        cand = (root / declared).resolve()
        try:
            cand.relative_to(root)
        except ValueError as exc:
            raise FileNotFoundError(
                f"{side} path escapes source-root: {declared}"
            ) from exc
        if not cand.is_file():
            raise FileNotFoundError(
                f"{side} source not found under source-root: {declared}"
            )
        return cand, declared.replace("\\", "/")

    if declared_path.is_file():
        return declared_path, declared.replace("\\", "/")
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


def _canonical_report_dict(report: Report) -> dict[str, Any]:
    """Full typed dump used for exact comparison (order-preserving)."""
    return report.model_dump(mode="json")


def verify_report_file(
    path: Path,
    *,
    source_root: Path | None = None,
    old_source: Path | None = None,
    new_source: Path | None = None,
    require_sources: bool = True,
) -> VerifyResult:
    errors: list[str] = []
    override_used = old_source is not None or new_source is not None

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

    # Integrity digest (unkeyed consistency only)
    if report.integrity.alg != "sha256":
        errors.append(f"Unsupported integrity algorithm: {report.integrity.alg}")
    expected_hash = integrity_payload_hash(data)
    if report.integrity.content_sha256 != expected_hash:
        errors.append(
            f"Integrity hash mismatch: reported={report.integrity.content_sha256} "
            f"computed={expected_hash}"
        )

    # Version compatibility policy
    if report.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"Unsupported schema_version: {report.schema_version}")
    if report.tool_version not in SUPPORTED_TOOL_VERSIONS:
        errors.append(
            f"Unsupported tool_version: {report.tool_version} "
            f"(running verifier is {__version__})"
        )

    if not require_sources:
        ok = len(errors) == 0
        return VerifyResult(
            ok=ok, errors=errors, content_sha256=expected_hash, override_used=override_used
        )

    try:
        old_fs, old_ref = _resolve_source_path(
            report.old_document.path,
            source_root=source_root,
            override=old_source,
            side="old",
        )
        new_fs, new_ref = _resolve_source_path(
            report.new_document.path,
            source_root=source_root,
            override=new_source,
            side="new",
        )
    except FileNotFoundError as exc:
        errors.append(str(exc))
        return VerifyResult(
            ok=False, errors=errors, content_sha256=expected_hash, override_used=override_used
        )

    old_adapter = _adapter_from_report(report.old_document)
    new_adapter = _adapter_from_report(report.new_document)

    try:
        old_src = load_immutable_source(
            old_fs, adapter=old_adapter, portable_ref=old_ref
        )
        new_src = load_immutable_source(
            new_fs, adapter=new_adapter, portable_ref=new_ref
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to load sources for replay: {exc}")
        return VerifyResult(
            ok=False, errors=errors, content_sha256=expected_hash, override_used=override_used
        )

    profile = (
        report.profile
        if isinstance(report.profile, ProfileName)
        else ProfileName(str(report.profile))
    )

    try:
        old_doc = extract_from_source(old_src, profile)
        new_doc = extract_from_source(new_src, profile)
        pairs = align_requirements(old_doc.requirements, new_doc.requirements)
        changes = classify_pairs(pairs)
        live = build_report(
            profile=profile,
            old_document=old_src.to_snapshot(),
            new_document=new_src.to_snapshot(),
            old_requirements=old_doc.requirements,
            new_requirements=new_doc.requirements,
            changes=changes,
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Replay pipeline failed: {exc}")
        return VerifyResult(
            ok=False, errors=errors, content_sha256=expected_hash, override_used=override_used
        )

    # When overrides are used, document paths may differ from portable refs —
    # rebuild expected with report's declared path strings for fair compare of
    # content-bound fields by rebinding snapshot path to declared refs only.
    if override_used:
        live = live.model_copy(
            update={
                "old_document": live.old_document.model_copy(
                    update={
                        "path": report.old_document.path,
                        "provenance": live.old_document.provenance.model_copy(
                            update={"local_path": report.old_document.path}
                        )
                        if live.old_document.provenance
                        else None,
                    }
                ),
                "new_document": live.new_document.model_copy(
                    update={
                        "path": report.new_document.path,
                        "provenance": live.new_document.provenance.model_copy(
                            update={"local_path": report.new_document.path}
                        )
                        if live.new_document.provenance
                        else None,
                    }
                ),
            }
        )
        # Recompute integrity of live after path rebinding for dump compare excluding integrity
        live_data = live.model_dump(mode="json")
        live = live.model_copy(
            update={
                "integrity": live.integrity.model_copy(
                    update={"content_sha256": integrity_payload_hash(live_data)}
                )
            }
        )

    # Complete canonical comparison: exact model dumps except integrity digest may
    # differ only if we compare payload without integrity then check separately.
    report_payload = report.model_dump(mode="json")
    live_payload = live.model_dump(mode="json")
    # Integrity content_sha256 is derived; compare payload excluding integrity,
    # then require integrity.alg and that submitted digest matches submitted payload
    # (already checked) and live payload integrity matches live construction.
    r_wo = {k: v for k, v in report_payload.items() if k != "integrity"}
    l_wo = {k: v for k, v in live_payload.items() if k != "integrity"}
    if r_wo != l_wo:
        errors.append(
            "Submitted report does not match complete canonical replay "
            "(requirements/changes/summary/documents/provenance/order/values)"
        )
        # Helpful narrow diagnostics
        if report_payload.get("old_requirements") != live_payload.get("old_requirements"):
            errors.append("old_requirements mismatch vs replay")
        if report_payload.get("new_requirements") != live_payload.get("new_requirements"):
            errors.append("new_requirements mismatch vs replay")
        if report_payload.get("changes") != live_payload.get("changes"):
            errors.append("changes mismatch vs replay")
        if report_payload.get("summary") != live_payload.get("summary"):
            errors.append("summary mismatch vs replay")
        if report_payload.get("old_document") != live_payload.get("old_document"):
            errors.append("old_document mismatch vs replay")
        if report_payload.get("new_document") != live_payload.get("new_document"):
            errors.append("new_document mismatch vs replay")
        if report_payload.get("tool_version") != live_payload.get("tool_version"):
            errors.append("tool_version mismatch vs running tool")
        if report_payload.get("schema_version") != live_payload.get("schema_version"):
            errors.append("schema_version mismatch vs policy")

    # Referential invariants (defense in depth)
    old_ids = {r.requirement_id for r in report.old_requirements}
    new_ids = {r.requirement_id for r in report.new_requirements}
    if len(old_ids) != len(report.old_requirements):
        errors.append("Duplicate old requirement IDs")
    if len(new_ids) != len(report.new_requirements):
        errors.append("Duplicate new requirement IDs")
    change_ids = [c.change_id for c in report.changes]
    if len(change_ids) != len(set(change_ids)):
        errors.append("Duplicate change IDs")
    paired_old: list[str] = []
    paired_new: list[str] = []
    for ch in report.changes:
        if ch.classification == ChangeClassification.ADDED:
            if ch.old_requirement_id is not None or ch.new_requirement_id not in new_ids:
                errors.append(f"Invalid ADDED change {ch.change_id}")
        elif ch.classification == ChangeClassification.REMOVED:
            if ch.new_requirement_id is not None or ch.old_requirement_id not in old_ids:
                errors.append(f"Invalid REMOVED change {ch.change_id}")
        else:
            if ch.old_requirement_id is None or ch.new_requirement_id is None:
                errors.append(f"Paired class requires both IDs: {ch.change_id}")
            else:
                paired_old.append(ch.old_requirement_id)
                paired_new.append(ch.new_requirement_id)
    if len(paired_old) != len(set(paired_old)) or len(paired_new) != len(set(paired_new)):
        errors.append("Duplicate requirement coverage in paired changes")

    ok = len(errors) == 0
    return VerifyResult(
        ok=ok,
        errors=errors,
        content_sha256=expected_hash,
        override_used=override_used,
    )
