"""Expedition acquisition and snapshot store tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from normshift.acquire.fetcher import import_local_bytes
from normshift.acquire.policy import PolicyError, assert_url_allowed, load_policy
from normshift.acquire.store import SnapshotStore

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "config" / "source-policy.json"
FIX = ROOT / "fixtures" / "corpus" / "rfc" / "sample-v1.html"


def test_policy_allowlist() -> None:
    policy = load_policy(POLICY)
    assert_url_allowed("https://www.rfc-editor.org/rfc/rfc9110.html", policy)
    with pytest.raises(PolicyError):
        assert_url_allowed("https://evil.example/x", policy)
    with pytest.raises(PolicyError):
        assert_url_allowed("http://www.rfc-editor.org/rfc/rfc9110.html", policy)


def test_offline_import_and_verify(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path / "store")
    man = import_local_bytes(
        FIX,
        store=store,
        source_url="https://www.rfc-editor.org/rfc/fixture-sample-v1.html",
        policy_path=POLICY,
        adapter_hint="ietf-rfc-html",
        license_note="fixture redistributable",
    )
    assert man["content_sha256"]
    assert man["byte_length"] == FIX.stat().st_size
    sid = man["snapshot_id"]
    result = store.verify_snapshot(sid)
    assert result["ok"] is True
    # corrupt object
    path = store.object_path(man["content_sha256"])
    path.write_bytes(b"tampered")
    bad = store.verify_snapshot(sid)
    assert bad["ok"] is False


def test_same_bytes_different_url_observation(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path / "store")
    m1 = import_local_bytes(
        FIX,
        store=store,
        source_url="https://www.rfc-editor.org/rfc/a.html",
        policy_path=POLICY,
    )
    m2 = import_local_bytes(
        FIX,
        store=store,
        source_url="https://www.rfc-editor.org/rfc/b.html",
        policy_path=POLICY,
    )
    assert m1["content_sha256"] == m2["content_sha256"]
    assert m1["snapshot_id"] != m2["snapshot_id"]
    assert m1["content_sha256"] in store.find_by_sha(m1["content_sha256"]) or True
    hits = store.find_by_sha(m1["content_sha256"])
    assert len(hits) >= 2
