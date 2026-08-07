"""Capsule verify on fixture outputs."""

from __future__ import annotations

from pathlib import Path

from normshift.capsule.builder import build_pair_capsule
from normshift.capsule.verifier import verify_capsule
from normshift.model.types import AdapterName, ProfileName
from normshift.pipeline import run_diff

ROOT = Path(__file__).resolve().parents[2]


def test_fixture_capsule_full_offline(tmp_path: Path) -> None:
    old = ROOT / "fixtures/corpus/rfc/sample-v1.html"
    new = ROOT / "fixtures/corpus/rfc/sample-v2.html"
    report = run_diff(
        old, new, profile=ProfileName.RFC2119, adapter=AdapterName.RFC, source_root=ROOT
    )
    man = {
        "content_sha256": report.old_document.sha256,
        "source_url": "https://example.invalid/old",
        "version_label": "v1",
        "redistribution_status": "redistributable",
        "license_reference": "fixture",
    }
    man2 = {
        "content_sha256": report.new_document.sha256,
        "source_url": "https://example.invalid/new",
        "version_label": "v2",
        "redistribution_status": "redistributable",
        "license_reference": "fixture",
    }
    out = tmp_path / "cap"
    cap = build_pair_capsule(
        pair_id="fixture-rfc",
        campaign_id="test",
        old_path=old,
        new_path=new,
        old_manifest=man,
        new_manifest=man2,
        report=report,
        adapter="rfc",
        profile="rfc2119",
        out_dir=out,
        include_bytes=True,
        source_date_epoch=1700000000,
    )
    assert cap["offline_replay"] is True
    v = verify_capsule(out)
    assert v["ok"], v


def test_thin_capsule_blocks_offline_claim(tmp_path: Path) -> None:
    old = ROOT / "fixtures/corpus/rfc/sample-v1.html"
    new = ROOT / "fixtures/corpus/rfc/sample-v2.html"
    report = run_diff(
        old, new, profile=ProfileName.RFC2119, adapter=AdapterName.RFC, source_root=ROOT
    )
    man = {
        "content_sha256": report.old_document.sha256,
        "source_url": "https://example.invalid/old",
        "version_label": "v1",
        "redistribution_status": "unknown_fail_closed",
        "license_reference": "unknown",
    }
    man2 = dict(man)
    man2["content_sha256"] = report.new_document.sha256
    out = tmp_path / "thin"
    cap = build_pair_capsule(
        pair_id="thin",
        campaign_id="test",
        old_path=old,
        new_path=new,
        old_manifest=man,
        new_manifest=man2,
        report=report,
        adapter="rfc",
        profile="rfc2119",
        out_dir=out,
        include_bytes=False,
    )
    assert cap["offline_replay"] is False
    assert cap["blocking_reason"] == "SOURCE_BYTES_NOT_INCLUDED"
    v = verify_capsule(out)
    assert v["ok"], v
