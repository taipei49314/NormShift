"""Local HTML file adapter."""

from __future__ import annotations

from pathlib import Path

from normshift.snapshot import snapshot_document


def load_html(path: Path) -> tuple[str, bytes, str, str]:
    """Return (path_str, raw_bytes, sha256, document_version)."""
    snap, raw = snapshot_document(path)
    return snap.path, raw, snap.sha256, snap.version
