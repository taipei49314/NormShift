"""Strict source-bound verification: strict JSON boundary then full replay."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from normshift import __version__
from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.extract.extractor import extract_from_source
from normshift.model.types import (
    AdapterName,
    ChangeClassification,
    ProfileName,
    Report,
)
from normshift.portable_ref import (
    PortableRefError,
    resolve_declared_under_root,
    validate_portable_ref,
)
from normshift.report.builder import (
    SUPPORTED_SCHEMA_VERSIONS,
    SUPPORTED_TOOL_VERSIONS,
    build_report,
)
from normshift.source import load_immutable_source
from normshift.strict_json import StrictJSONError, deep_require_keys, strict_loads

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
    verification_scope: str = "FULL"  # FULL | CONTENT_ONLY_OVERRIDE


def _load_bundled_schema(name: str) -> dict[str, Any]:
    try:
        pkg = resources.files("normshift") / "schemas" / name
        if pkg.is_file():
            import json

            loaded = json.loads(pkg.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return dict(loaded)
    except Exception:
        pass
    import json

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
    # Same PurePosix grammar for full and override verification
    try:
        ref = validate_portable_ref(declared)
    except PortableRefError as exc:
        raise FileNotFoundError(f"{side} declared source_ref invalid: {exc}") from exc

    if override is not None:
        p = Path(override)
        if not p.is_file():
            raise FileNotFoundError(f"{side} override source not found: {p}")
        # Overrides relocate bytes only; declared logical path is not re-attested
        return p, ref

    if source_root is not None:
        try:
            cand, canonical = resolve_declared_under_root(source_root, ref)
        except PortableRefError as exc:
            raise FileNotFoundError(f"{side}: {exc}") from exc
        return cand, canonical

    # No root: require declared path exists as relative path under CWD and is canonical
    try:
        cand, canonical = resolve_declared_under_root(Path.cwd(), ref)
    except PortableRefError as exc:
        raise FileNotFoundError(
            f"{side} source not found / non-canonical: {declared} "
            f"(provide --source-root or --old-source/--new-source); {exc}"
        ) from exc
    return cand, canonical


def _adapter_from_report(doc_side: Any) -> AdapterName:
    prov = getattr(doc_side, "provenance", None)
    if prov is None:
        return AdapterName.AUTO
    aid = getattr(prov, "adapter_id", None) or ""
    return _ADAPTER_FROM_ID.get(str(aid), AdapterName.AUTO)


def verify_report_file(
    path: Path,
    *,
    source_root: Path | None = None,
    old_source: Path | None = None,
    new_source: Path | None = None,
    require_sources: bool = True,
) -> VerifyResult:
    """Verify a report file; never raises — failures are structured VerifyResult."""
    override_used = old_source is not None or new_source is not None
    scope = "CONTENT_ONLY_OVERRIDE" if override_used else "FULL"
    try:
        return _verify_report_file_impl(
            path,
            source_root=source_root,
            old_source=old_source,
            new_source=new_source,
            require_sources=require_sources,
            override_used=override_used,
            scope=scope,
        )
    except Exception as exc:  # noqa: BLE001 — clean CLI failure, no traceback
        return VerifyResult(
            ok=False,
            errors=[f"Verifier failed closed: {type(exc).__name__}: {exc}"],
            override_used=override_used,
            verification_scope=scope,
        )


def _verify_report_file_impl(
    path: Path,
    *,
    source_root: Path | None,
    old_source: Path | None,
    new_source: Path | None,
    require_sources: bool,
    override_used: bool,
    scope: str,
) -> VerifyResult:
    errors: list[str] = []

    if not path.is_file():
        return VerifyResult(
            ok=False,
            errors=[f"Report file not found: {path}"],
            override_used=override_used,
            verification_scope=scope,
        )

    try:
        raw = path.read_bytes()
        data = strict_loads(raw)
    except (OSError, UnicodeError, StrictJSONError) as exc:
        return VerifyResult(
            ok=False,
            errors=[f"Strict JSON parse failed: {exc}"],
            override_used=override_used,
            verification_scope=scope,
        )

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
        # Non-strict enum decode (JSON strings → enums); primitive coercion is
        # rejected below via complete typed dump equality (string "0.9" ≠ 0.9).
        report = Report.model_validate(data)
    except ValidationError as exc:
        errors.append(f"Pydantic validation failed: {exc}")
        return VerifyResult(
            ok=False, errors=errors, override_used=override_used, verification_scope=scope
        )

    # Canonical submitted equality: field presence + payload bytes before replay
    try:
        dumped = report.model_dump(mode="json")
        deep_require_keys(data, dumped)
        # Encode may fail on unpaired surrogates — clean failure, not traceback
        submitted_bytes = canonical_json_bytes(data)
        dumped_bytes = canonical_json_bytes(dumped)
    except (StrictJSONError, UnicodeError, ValueError, TypeError) as exc:
        errors.append(f"Submitted JSON field presence/type boundary: {exc}")
        return VerifyResult(
            ok=False,
            errors=errors,
            override_used=override_used,
            verification_scope=scope,
        )
    if submitted_bytes != dumped_bytes:
        errors.append(
            "Submitted JSON is not equal to complete typed dump "
            "(coercion, omitted defaults, or non-canonical representation)"
        )

    if report.integrity.alg != "sha256":
        errors.append(f"Unsupported integrity algorithm: {report.integrity.alg}")
    expected_hash = integrity_payload_hash(data)
    if report.integrity.content_sha256 != expected_hash:
        errors.append(
            f"Integrity hash mismatch: reported={report.integrity.content_sha256} "
            f"computed={expected_hash}"
        )

    if report.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"Unsupported schema_version: {report.schema_version}")
    if report.tool_version not in SUPPORTED_TOOL_VERSIONS:
        errors.append(
            f"Unsupported tool_version: {report.tool_version} "
            f"(running verifier is {__version__})"
        )

    if errors:
        return VerifyResult(
            ok=False,
            errors=errors,
            content_sha256=expected_hash,
            override_used=override_used,
            verification_scope=scope,
        )

    if not require_sources:
        return VerifyResult(
            ok=True,
            errors=[],
            content_sha256=expected_hash,
            override_used=override_used,
            verification_scope=scope,
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
        return VerifyResult(
            ok=False,
            errors=[str(exc)],
            content_sha256=expected_hash,
            override_used=override_used,
            verification_scope=scope,
        )

    old_adapter = _adapter_from_report(report.old_document)
    new_adapter = _adapter_from_report(report.new_document)

    try:
        old_src = load_immutable_source(old_fs, adapter=old_adapter, portable_ref=old_ref)
        new_src = load_immutable_source(new_fs, adapter=new_adapter, portable_ref=new_ref)
        profile = (
            report.profile
            if isinstance(report.profile, ProfileName)
            else ProfileName(str(report.profile))
        )
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
        return VerifyResult(
            ok=False,
            errors=[f"Replay pipeline failed: {exc}"],
            content_sha256=expected_hash,
            override_used=override_used,
            verification_scope=scope,
        )

    if override_used:
        # Content-only: rebind declared portable paths for dump compare
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
        live_data = live.model_dump(mode="json")
        live = live.model_copy(
            update={
                "integrity": live.integrity.model_copy(
                    update={"content_sha256": integrity_payload_hash(live_data)}
                )
            }
        )

    # Canonical payload-byte equality (not Python numeric equality: -0.0 == 0.0)
    report_payload = report.model_dump(mode="json")
    live_payload = live.model_dump(mode="json")
    r_wo = {k: v for k, v in report_payload.items() if k != "integrity"}
    l_wo = {k: v for k, v in live_payload.items() if k != "integrity"}
    try:
        r_bytes = canonical_json_bytes(r_wo)
        l_bytes = canonical_json_bytes(l_wo)
    except (UnicodeError, ValueError, TypeError) as exc:
        errors.append(f"Canonical replay encoding failed: {exc}")
        r_bytes = b""
        l_bytes = b"x"
    if r_bytes != l_bytes:
        mismatched = sorted(k for k in set(r_wo) | set(l_wo) if r_wo.get(k) != l_wo.get(k))
        # Also detect signed-zero-only differences hidden by Python equality
        if not mismatched:
            mismatched = ["<canonical-bytes-differ>"]
        detail = ", ".join(mismatched[:12]) if mismatched else "payload"
        errors.append(
            f"Submitted report does not match complete canonical replay "
            f"(mismatched fields: {detail})"
        )

    # Referential invariants
    old_ids = {r.requirement_id for r in report.old_requirements}
    new_ids = {r.requirement_id for r in report.new_requirements}
    if len(old_ids) != len(report.old_requirements):
        errors.append("Duplicate old requirement IDs")
    if len(new_ids) != len(report.new_requirements):
        errors.append("Duplicate new requirement IDs")
    if len([c.change_id for c in report.changes]) != len(
        {c.change_id for c in report.changes}
    ):
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
        verification_scope=scope,
    )
