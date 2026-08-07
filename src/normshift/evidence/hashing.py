"""Deterministic hashing for evidence and report integrity."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def evidence_hash(kind: str, value: str) -> str:
    payload = f"{kind}\x1f{value}".encode()
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """Stable JSON encoding for byte-identical reports."""
    return json.dumps(
        obj,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
        separators=(",", ": "),
    ).encode("utf-8") + b"\n"


def integrity_payload_hash(report_dict: dict[str, Any]) -> str:
    """Hash report contents excluding the integrity field itself."""
    payload = {k: v for k, v in report_dict.items() if k != "integrity"}
    raw = canonical_json_bytes(payload)
    return hashlib.sha256(raw).hexdigest()
