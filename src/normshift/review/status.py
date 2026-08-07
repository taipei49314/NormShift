"""Review status projection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from normshift.review.ledger import _load_jsonl


def review_status(packets_path: Path, decisions_path: Path | None) -> dict[str, Any]:
    packets = _load_jsonl(packets_path) if packets_path.is_file() else []
    decisions = (
        _load_jsonl(decisions_path)
        if decisions_path and decisions_path.is_file()
        else []
    )
    by_packet: dict[str, list[dict[str, Any]]] = {}
    for d in decisions:
        by_packet.setdefault(str(d.get("packet_id")), []).append(d)

    states = {
        "UNREVIEWED": 0,
        "AGREED": 0,
        "DISAGREED": 0,
        "ABSTAINED": 0,
        "NEEDS_CONTEXT": 0,
        "INVALID": 0,
    }
    detail: list[dict[str, Any]] = []
    for p in packets:
        pid = str(p.get("packet_id"))
        decs = by_packet.get(pid, [])
        if not decs:
            st = "UNREVIEWED"
        else:
            verdicts = {str(d.get("verdict")) for d in decs}
            if "NEEDS_CONTEXT" in verdicts:
                st = "NEEDS_CONTEXT"
            elif verdicts == {"ABSTAIN"}:
                st = "ABSTAINED"
            elif len(verdicts) == 1:
                st = "AGREED"
            else:
                st = "DISAGREED"
        states[st] = states.get(st, 0) + 1
        detail.append({"packet_id": pid, "state": st, "decisions": len(decs)})

    return {
        "schema_version": "1.0.0",
        "packet_count": len(packets),
        "decision_count": len(decisions),
        "states": states,
        "label_authority_note": "AUTO packets; decisions only TEST_FIXTURE or external import",
        "reviewed_metrics_status": (
            "NOT_AVAILABLE"
            if not any(
                d.get("label_authority")
                in {"EXTERNAL_REVIEW", "EXTERNAL_ADJUDICATION"}
                for d in decisions
            )
            else "PARTIAL"
        ),
        "detail_sample": detail[:20],
    }
