#!/usr/bin/env python3
"""Verify a detached combined-audit attestation against external digest anchors."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

MAX_JSON_BYTES = 4 * 1024 * 1024
SHA256_LENGTH = 64
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_MANIFEST_SCHEMA_PATH = ROOT / "schemas" / "package_manifest_v1.schema.json"


class AuditVerificationError(ValueError):
    """The audit, manifest, schema, or external subject binding is invalid."""


def _duplicate_rejector(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditVerificationError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise AuditVerificationError(f"non-finite JSON constant: {value}")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or (parsed == 0.0 and math.copysign(1.0, parsed) < 0):
        raise AuditVerificationError(f"non-canonical JSON number: {value}")
    return parsed


def _bounded_regular_bytes(path: Path, label: str) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise AuditVerificationError(f"cannot inspect {label}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise AuditVerificationError(
            f"{label} must be one regular file with link count exactly one"
        )
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_nlink) != (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_nlink,
            ):
                raise AuditVerificationError(f"{label} identity changed before reading")
            raw = handle.read(MAX_JSON_BYTES + 1)
            if len(raw) > MAX_JSON_BYTES:
                raise AuditVerificationError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
            after_handle = os.fstat(handle.fileno())
    except OSError as exc:
        raise AuditVerificationError(f"cannot read {label}: {exc}") from exc
    try:
        after_path = path.lstat()
    except OSError as exc:
        raise AuditVerificationError(f"cannot re-inspect {label}: {exc}") from exc
    expected_identity = (before.st_dev, before.st_ino, before.st_size, before.st_nlink)
    if (
        (after_handle.st_dev, after_handle.st_ino, after_handle.st_size, after_handle.st_nlink)
        != expected_identity
        or (after_path.st_dev, after_path.st_ino, after_path.st_size, after_path.st_nlink)
        != expected_identity
        or len(raw) != before.st_size
    ):
        raise AuditVerificationError(f"{label} identity or size changed while reading")
    return raw


def _strict_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = _bounded_regular_bytes(path, label)
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_duplicate_rejector,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditVerificationError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditVerificationError(f"{label} top level must be an object")
    return value, raw


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_sha256(value: str, label: str) -> None:
    if len(value) != SHA256_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise AuditVerificationError(f"{label} must be one lowercase SHA-256")


def _schema_errors(instance: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        errors.append(f"{path}: {error.message}")
    return errors


def _canonical_relative_ref(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AuditVerificationError(f"{label} must be one non-empty relative POSIX path")
    if value.startswith(("/", "\\")) or "\\" in value or "\x00" in value:
        raise AuditVerificationError(f"{label} is not a canonical relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise AuditVerificationError(f"{label} is not a canonical relative POSIX path")
    return value


def _manifest_audit_reference(manifest_path: Path, audit_path: Path) -> str:
    try:
        audit_resolved = audit_path.resolve(strict=True)
        manifest_parent = manifest_path.resolve(strict=True).parent
        relative = audit_resolved.relative_to(manifest_parent)
    except (OSError, ValueError) as exc:
        raise AuditVerificationError(
            "detached audit must be a physical descendant of the manifest directory"
        ) from exc
    return _canonical_relative_ref(relative.as_posix(), "detached audit reference")


def _validate_package_manifest(
    manifest: dict[str, Any], manifest_path: Path, audit_path: Path, audit_sha256: str
) -> None:
    package_schema, _ = _strict_json(PACKAGE_MANIFEST_SCHEMA_PATH, "package manifest schema")
    try:
        Draft202012Validator.check_schema(package_schema)
    except Exception as exc:
        raise AuditVerificationError(f"package manifest schema is invalid: {exc}") from exc
    errors = _schema_errors(manifest, package_schema)
    if errors:
        raise AuditVerificationError("package manifest schema mismatch: " + "; ".join(errors[:8]))

    audit_reference = _manifest_audit_reference(manifest_path, audit_path)
    for table_name in ("artifacts", "logs", "files"):
        table = manifest[table_name]
        assert isinstance(table, dict)
        for record_id, record in table.items():
            assert isinstance(record, dict)
            path = _canonical_relative_ref(
                record["path"], f"manifest {table_name}.{record_id}.path"
            )
            digest = record["sha256"]
            assert isinstance(digest, str)
            if path == audit_reference:
                raise AuditVerificationError(
                    "detached audit must not be self-listed by the manifest"
                )
            if digest == audit_sha256:
                raise AuditVerificationError(
                    "detached audit digest must not be self-bound by the manifest"
                )


def verify_external_audit(
    *,
    manifest_path: Path,
    audit_path: Path,
    schema_path: Path,
    manifest_sha256: str,
    audit_sha256: str,
    commit: str,
    tree: str,
    version: str,
    run_id: str,
    roots_inventory_sha256: str,
    approved_volume_binding_sha256: str,
) -> dict[str, Any]:
    """Strictly verify one detached audit and return a bounded success record."""
    _require_sha256(manifest_sha256, "manifest anchor")
    _require_sha256(audit_sha256, "audit anchor")
    _require_sha256(roots_inventory_sha256, "authority roots inventory anchor")
    _require_sha256(approved_volume_binding_sha256, "approved volume binding anchor")
    manifest, manifest_raw = _strict_json(manifest_path, "manifest")
    audit, audit_raw = _strict_json(audit_path, "external audit")
    schema, _schema_raw = _strict_json(schema_path, "external audit schema")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise AuditVerificationError(f"external audit schema is invalid: {exc}") from exc
    errors = _schema_errors(audit, schema)
    if errors:
        raise AuditVerificationError("external audit schema mismatch: " + "; ".join(errors[:8]))
    actual_manifest_sha256 = _sha256(manifest_raw)
    actual_audit_sha256 = _sha256(audit_raw)
    if actual_manifest_sha256 != manifest_sha256:
        raise AuditVerificationError("manifest bytes differ from external digest anchor")
    if actual_audit_sha256 != audit_sha256:
        raise AuditVerificationError("external audit bytes differ from external digest anchor")
    _validate_package_manifest(manifest, manifest_path, audit_path, audit_sha256)
    expected = {
        "package_commit": commit,
        "package_tree": tree,
        "package_version": version,
        "run_id": run_id,
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            raise AuditVerificationError(f"manifest {field} differs from the release subject")
        if audit.get(field) != value:
            raise AuditVerificationError(f"external audit {field} differs from the release subject")
    if audit.get("manifest_sha256") != manifest_sha256:
        raise AuditVerificationError("external audit does not bind the frozen manifest digest")
    execution_authority = audit["execution_authority"]
    assert isinstance(execution_authority, dict)
    expected_authority = {
        "platform": "windows",
        "filesystem": "NTFS",
        "drive_type": "fixed",
        "local_volume": True,
        "same_volume": True,
        "lock_policy": {
            "id": "normshift-windows-ntfs-share-deny",
            "version": "1.0.0",
        },
        "authority_run_id": run_id,
        "preflight_result": "PASS",
        "roots_inventory_sha256": roots_inventory_sha256,
        "approved_volume_binding_sha256": approved_volume_binding_sha256,
    }
    if execution_authority != expected_authority:
        raise AuditVerificationError(
            "external audit execution authority differs from the frozen Windows NTFS policy"
        )
    findings = audit["findings"]
    assert isinstance(findings, dict)
    return {
        "ok": True,
        "schema_version": audit["schema_version"],
        "scope": audit["scope"],
        "verdict": audit["verdict"],
        "package_commit": commit,
        "package_tree": tree,
        "manifest_sha256": manifest_sha256,
        "audit_sha256": audit_sha256,
        "p0": findings["p0"],
        "p1": findings["p1"],
        "p2": findings["p2"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--audit-sha256", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--roots-inventory-sha256", required=True)
    parser.add_argument("--approved-volume-binding-sha256", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point with a controlled, bounded failure surface."""
    args = _parser().parse_args(argv)
    try:
        result = verify_external_audit(
            manifest_path=args.manifest,
            audit_path=args.audit,
            schema_path=args.schema,
            manifest_sha256=args.manifest_sha256,
            audit_sha256=args.audit_sha256,
            commit=args.commit,
            tree=args.tree,
            version=args.version,
            run_id=args.run_id,
            roots_inventory_sha256=args.roots_inventory_sha256,
            approved_volume_binding_sha256=args.approved_volume_binding_sha256,
        )
    except (AuditVerificationError, OSError) as exc:
        print(f"error: {str(exc)[:800]}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
