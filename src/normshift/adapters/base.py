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
    # Provisional portable path; load_immutable_source rebinds when portable_ref is known.
    portable = provisional_portable_ref(path)
    return Provenance(
        document_family=family,
        adapter_id=adapter_id,
        adapter_version=ADAPTER_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        content_type=side.get("content_type", content_type),
        content_sha256=digest,
        byte_length=len(raw),
        local_path=portable,
        canonical_source=side.get("canonical_source"),
        etag=side.get("etag"),
        last_modified=side.get("last_modified"),
        fetch_metadata=dict(sorted(fetch_meta.items())),
    )


def provisional_portable_ref(path: Path) -> str:
    """Best-effort POSIX ref for adapter-internal provenance (never absolute)."""
    p = Path(path)
    if not p.is_absolute():
        return p.as_posix().replace("\\", "/")
    try:
        return p.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        # Outside CWD: basename only as provisional (must be rebound for reports).
        return p.name


def portable_source_ref(path: Path) -> str:
    """Return a normalized POSIX path suitable for --source-root resolution.

    Never returns an absolute path. Outside-CWD absolute paths fail closed.
    Prefer passing ``portable_ref`` from ``resolve_under_source_root``.
    """
    from normshift.paths_root import SourceRootError, default_source_root, resolve_under_source_root

    try:
        _abs, ref = resolve_under_source_root(default_source_root(), Path(path))
        return ref
    except SourceRootError as exc:
        raise ValueError(str(exc)) from exc


def adapter_name_to_id(name: AdapterName) -> str:
    return f"normshift.adapters.{name.value}"
