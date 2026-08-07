"""Document snapshot and content-addressed identity via adapters."""

from __future__ import annotations

import hashlib
from pathlib import Path

from normshift.adapters.base import AdaptedDocument
from normshift.adapters.registry import load_document
from normshift.model.types import AdapterName, DocumentSnapshot


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def snapshot_from_adapted(adapted: AdaptedDocument) -> DocumentSnapshot:
    return DocumentSnapshot(
        path=str(adapted.path.as_posix()),
        sha256=adapted.provenance.content_sha256,
        version=adapted.document_version,
        byte_length=adapted.provenance.byte_length,
        provenance=adapted.provenance,
        document_family=adapted.family,
    )


def snapshot_document(
    path: Path,
    adapter: AdapterName = AdapterName.AUTO,
) -> tuple[DocumentSnapshot, bytes, AdaptedDocument]:
    """Load via adapter; return snapshot, working HTML bytes, and adapted doc.

    ``sha256`` is always over raw source bytes (immutable snapshot identity),
    not over chrome-stripped working HTML.
    """
    adapted = load_document(path, adapter=adapter)
    snap = snapshot_from_adapted(adapted)
    return snap, adapted.working_html, adapted
