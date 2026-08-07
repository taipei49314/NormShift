"""Adapter protocol and shared load result."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from normshift.model.types import AdapterName, DocumentFamily, Provenance

ADAPTER_VERSION = "1.0.0"
NORMALIZATION_VERSION = "1.0.0"


@dataclass(frozen=True)
class AdaptedDocument:
    """Result of a successful adapter load (local, offline)."""

    path: Path
    raw_bytes: bytes
    working_html: bytes
    provenance: Provenance
    document_version: str
    family: DocumentFamily


class SourceAdapter(Protocol):
    adapter_id: str
    family: DocumentFamily

    def can_handle(self, path: Path, raw: bytes) -> bool: ...

    def load(self, path: Path, raw: bytes) -> AdaptedDocument: ...


def load_sidecar_meta(path: Path) -> dict[str, str]:
    """Load optional ``<file>.meta.json`` provenance sidecar (offline)."""
    import json

    candidates = [
        path.with_suffix(path.suffix + ".meta.json"),
        Path(str(path) + ".meta.json"),
        path.parent / f"{path.name}.meta.json",
    ]
    for cand in candidates:
        if cand.is_file():
            data = json.loads(cand.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {}
            return {str(k): str(v) for k, v in data.items() if v is not None}
    return {}


def build_provenance(
    *,
    path: Path,
    raw: bytes,
    family: DocumentFamily,
    adapter_id: str,
    content_type: str,
    sidecar: dict[str, str] | None = None,
) -> Provenance:
    import hashlib

    side = sidecar if sidecar is not None else load_sidecar_meta(path)
    digest = hashlib.sha256(raw).hexdigest()
    fetch_meta = {
        k: v
        for k, v in side.items()
        if k
        not in {
            "canonical_source",
            "etag",
            "last_modified",
            "content_type",
            "document_family",
        }
    }
    return Provenance(
        document_family=family,
        adapter_id=adapter_id,
        adapter_version=ADAPTER_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        content_type=side.get("content_type", content_type),
        content_sha256=digest,
        byte_length=len(raw),
        local_path=str(path.resolve().as_posix()),
        canonical_source=side.get("canonical_source"),
        etag=side.get("etag"),
        last_modified=side.get("last_modified"),
        fetch_metadata=dict(sorted(fetch_meta.items())),
    )


def adapter_name_to_id(name: AdapterName) -> str:
    return f"normshift.adapters.{name.value}"
