"""Verify report integrity and basic schema conformance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from normshift.evidence.hashing import integrity_payload_hash
from normshift.model.types import Report


@dataclass
class VerifyResult:
    ok: bool
    errors: list[str]
    content_sha256: str | None = None


def _load_schema(name: str) -> dict[str, Any] | None:
    # schemas/ lives at repo root relative to package.
    candidates = [
        Path(__file__).resolve().parents[3] / "schemas" / name,
        Path.cwd() / "schemas" / name,
    ]
    for p in candidates:
        if p.is_file():
            loaded: object = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return dict(loaded)
            return None
    return None


def verify_report_file(path: Path) -> VerifyResult:
    errors: list[str] = []
    if not path.is_file():
        return VerifyResult(ok=False, errors=[f"Report file not found: {path}"])

    try:
        raw_text = path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return VerifyResult(ok=False, errors=[f"Failed to read/parse JSON: {exc}"])

    if not isinstance(data, dict):
        return VerifyResult(ok=False, errors=["Report root must be a JSON object"])

    # Pydantic structural validation.
    try:
        Report.model_validate(data)
    except ValidationError as exc:
        errors.append(f"Pydantic validation failed: {exc}")

    # Optional JSON Schema if present.
    schema = _load_schema("report.schema.json")
    if schema is not None:
        try:
            import jsonschema

            jsonschema.validate(instance=data, schema=schema)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"JSON Schema validation failed: {exc}")

    expected = integrity_payload_hash(data)
    integrity = data.get("integrity") or {}
    actual = integrity.get("content_sha256")
    if not actual:
        errors.append("Missing integrity.content_sha256")
    elif actual != expected:
        errors.append(
            f"Integrity hash mismatch: reported={actual} computed={expected} "
            "(possible tampering or non-canonical mutation)"
        )

    if integrity.get("alg") not in (None, "sha256"):
        errors.append(f"Unsupported integrity algorithm: {integrity.get('alg')}")

    ok = len(errors) == 0
    return VerifyResult(ok=ok, errors=errors, content_sha256=expected)
