"""Campaign plan validation tests."""

from __future__ import annotations

from pathlib import Path

from normshift.campaign.runner import validate_plan

ROOT = Path(__file__).resolve().parents[2]


def test_foundry_campaign_plan_validates() -> None:
    r = validate_plan(ROOT / "config/campaigns/foundry-24h.json")
    assert r["ok"] is True
    assert r["pairs"] >= 3
    assert r["snapshots"] >= 6
