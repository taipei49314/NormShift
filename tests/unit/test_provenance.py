"""Provenance sidecar and snapshot identity."""

from __future__ import annotations

from pathlib import Path

from normshift.adapters.base import load_sidecar_meta
from normshift.adapters.registry import load_document
from normshift.model.types import AdapterName

ROOT = Path(__file__).resolve().parents[2]


def test_sidecar_loaded() -> None:
    path = ROOT / "fixtures" / "corpus" / "rfc" / "sample-v1.html"
    meta = load_sidecar_meta(path)
    assert meta.get("canonical_source")
    assert meta.get("etag")


def test_raw_hash_stable() -> None:
    path = ROOT / "fixtures" / "corpus" / "rfc" / "sample-v1.html"
    a = load_document(path, adapter=AdapterName.RFC)
    b = load_document(path, adapter=AdapterName.RFC)
    assert a.provenance.content_sha256 == b.provenance.content_sha256
    import hashlib

    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert a.provenance.content_sha256 == expected
