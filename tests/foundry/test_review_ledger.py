"""Review ledger rejects implementer external authority."""

from __future__ import annotations

import json
from pathlib import Path

from normshift.review.ledger import validate_ledger


def test_rejects_external_authority_from_agent(tmp_path: Path) -> None:
    p = tmp_path / "d.jsonl"
    row = {
        "decision_id": "d1",
        "packet_id": "pkt_x",
        "reviewer_id": "agent",
        "reviewer_role": "implementer",
        "sequence": 1,
        "source_snapshot_hashes": ["a", "b"],
        "verdict": "ACCEPT_PROPOSAL",
        "reason": "nope",
        "label_authority": "EXTERNAL_REVIEW",
    }
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    r = validate_ledger(p, known_packet_ids={"pkt_x"}, allow_external=False)
    assert r["ok"] is False


def test_accepts_test_fixture(tmp_path: Path) -> None:
    p = tmp_path / "d.jsonl"
    row = {
        "decision_id": "d1",
        "packet_id": "pkt_x",
        "reviewer_id": "test",
        "reviewer_role": "test",
        "sequence": 1,
        "source_snapshot_hashes": ["a", "b"],
        "verdict": "ACCEPT_PROPOSAL",
        "reason": "fixture",
        "label_authority": "TEST_FIXTURE",
    }
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    r = validate_ledger(p, known_packet_ids={"pkt_x"}, allow_external=False)
    assert r["ok"] is True
