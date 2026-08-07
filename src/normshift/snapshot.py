"""Document snapshot and content-addressed identity."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from lxml import html

from normshift.model.types import DocumentSnapshot


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_html_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(f"HTML file not found: {path}")
    return path.read_bytes()


def extract_document_version(raw: bytes, path: Path) -> str:
    """Derive a deterministic version label from content, not filename alone."""
    try:
        tree = html.fromstring(raw)
    except Exception:
        return f"sha256:{sha256_bytes(raw)[:12]}"

    # Prefer explicit meta tags when present.
    for name in ("version", "doc-version", "document-version", "spec-version"):
        metas = tree.xpath(f'//meta[@name="{name}"]/@content')
        if metas and str(metas[0]).strip():
            return str(metas[0]).strip()

    # Prefer data-version on root/html/body.
    for attr in ("data-version", "data-spec-version"):
        vals = tree.xpath(f"//*[@{attr}]/@{attr}")
        if vals and str(vals[0]).strip():
            return str(vals[0]).strip()

    # Heading first H1 with trailing version-like token.
    h1s = tree.xpath("//h1")
    if h1s:
        text = " ".join(h1s[0].itertext()).strip()
        m = re.search(r"\bv(?:ersion\s*)?(\d+(?:\.\d+)*)\b", text, re.IGNORECASE)
        if m:
            return m.group(1)

    # Content-addressed fallback (never filename-only identity).
    return f"sha256:{sha256_bytes(raw)[:12]}"


def snapshot_document(path: Path) -> tuple[DocumentSnapshot, bytes]:
    raw = read_html_bytes(path)
    digest = sha256_bytes(raw)
    version = extract_document_version(raw, path)
    snap = DocumentSnapshot(
        path=str(path.as_posix()),
        sha256=digest,
        version=version,
        byte_length=len(raw),
    )
    return snap, raw
