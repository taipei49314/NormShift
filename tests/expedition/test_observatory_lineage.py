"""Expedition lineage store + offline observatory tests."""

from __future__ import annotations

from pathlib import Path

from normshift.acquire.fetcher import import_local_bytes
from normshift.acquire.store import SnapshotStore
from normshift.lineage.graph_builder import build_lineage_from_paths
from normshift.lineage.store import LineageStore
from normshift.model.types import AdapterName, ProfileName
from normshift.observatory.builder import build_observatory, verify_observatory_manifest

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "config" / "source-policy.json"
LIN = ROOT / "fixtures" / "lineage"


def test_lineage_jsonl_deterministic(tmp_path: Path) -> None:
    db = tmp_path / "lin.db"
    store = LineageStore(db)
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    try:
        summary = build_lineage_from_paths(
            paths,
            store=store,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
        a = store.export_jsonl(tmp_path / "a.jsonl")
        b = store.export_jsonl(tmp_path / "b.jsonl")
    finally:
        store.close()
    assert a == b
    assert summary["versions"] == 3
    assert summary["store_counts"]["nodes"] > 0


def test_observatory_offline_build_and_verify(tmp_path: Path) -> None:
    st = SnapshotStore(tmp_path / "store")
    import_local_bytes(
        LIN / "v1.html",
        store=st,
        source_url="https://www.rfc-editor.org/rfc/obs-v1.html",
        policy_path=POLICY,
    )
    site = tmp_path / "site"
    man1 = build_observatory(
        store=st,
        out_dir=site,
        discovery=[
            {
                "id": "d1",
                "kind": "STRENGTHENED",
                "summary": "PROVISIONAL example discovery item",
                "evidence": "fixtures/lineage",
                "snapshot_hashes": [],
            }
        ],
    )
    man2 = build_observatory(
        store=st,
        out_dir=tmp_path / "site2",
        discovery=[
            {
                "id": "d1",
                "kind": "STRENGTHENED",
                "summary": "PROVISIONAL example discovery item",
                "evidence": "fixtures/lineage",
                "snapshot_hashes": [],
            }
        ],
    )
    # deterministic file set (timestamps differ — compare file hashes excluding generated_at)
    assert man1["snapshot_count"] == man2["snapshot_count"]
    assert man1["files"].keys() == man2["files"].keys()
    v = verify_observatory_manifest(site)
    assert v["ok"], v
    # tamper
    (site / "index.html").write_text("tampered", encoding="utf-8")
    bad = verify_observatory_manifest(site)
    assert bad["ok"] is False
