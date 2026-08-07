"""Build deterministic AUTO review packets from reports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from normshift.io_safety import atomic_write_text
from normshift.model.types import ChangeClassification, Report
from normshift.review.model import ReviewPacket

_PRIORITY = {
    ChangeClassification.POLARITY_FLIP: 0,
    ChangeClassification.STRENGTHENED: 1,
    ChangeClassification.WEAKENED: 2,
    ChangeClassification.CONDITION_ADDED: 3,
    ChangeClassification.CONDITION_REMOVED: 3,
    ChangeClassification.EXCEPTION_ADDED: 4,
    ChangeClassification.EXCEPTION_REMOVED: 4,
    ChangeClassification.AMBIGUOUS: 5,
    ChangeClassification.REMOVED: 6,
    ChangeClassification.ADDED: 7,
    ChangeClassification.MOVED: 8,
    ChangeClassification.UNCHANGED: 9,
    ChangeClassification.EDITORIAL: 9,
}


def _pid(*parts: str) -> str:
    return "pkt_" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]


def build_packets_for_pairs(
    *,
    campaign_id: str,
    pair_id: str,
    capsule_id: str,
    report: Report,
    old_sha: str,
    new_sha: str,
    max_packets: int = 80,
    include_negative_controls: int = 3,
) -> list[dict[str, Any]]:
    changes = list(report.changes)
    ranked = sorted(
        changes,
        key=lambda c: (
            _PRIORITY.get(c.classification, 50),
            -float(c.confidence),
            c.change_id,
        ),
    )
    selected: list[Any] = []
    # always take high priority classes
    for c in ranked:
        if c.classification in {
            ChangeClassification.POLARITY_FLIP,
            ChangeClassification.STRENGTHENED,
            ChangeClassification.WEAKENED,
            ChangeClassification.AMBIGUOUS,
            ChangeClassification.CONDITION_ADDED,
            ChangeClassification.CONDITION_REMOVED,
            ChangeClassification.EXCEPTION_ADDED,
            ChangeClassification.EXCEPTION_REMOVED,
            ChangeClassification.ADDED,
            ChangeClassification.REMOVED,
        }:
            selected.append(c)
    # negative controls
    controls = [
        c
        for c in ranked
        if c.classification
        in {
            ChangeClassification.UNCHANGED,
            ChangeClassification.MOVED,
            ChangeClassification.EDITORIAL,
        }
    ][:include_negative_controls]
    for c in controls:
        if c not in selected:
            selected.append(c)
    # fill
    for c in ranked:
        if len(selected) >= max_packets:
            break
        if c not in selected:
            selected.append(c)

    packets: list[dict[str, Any]] = []
    for c in selected[:max_packets]:
        pkt = ReviewPacket(
            packet_id=_pid(campaign_id, pair_id, c.change_id),
            campaign_id=campaign_id,
            pair_id=pair_id,
            capsule_id=capsule_id,
            change_id=c.change_id,
            proposed_classification=c.classification.value,
            confidence=float(c.confidence),
            old_requirement_id=c.old_requirement_id,
            new_requirement_id=c.new_requirement_id,
            old_text=(c.old_text or "")[:500] or None,
            new_text=(c.new_text or "")[:500] or None,
            old_locator=c.old_source_locator,
            new_locator=c.new_source_locator,
            old_context=(c.old_text or "")[:800] or None,
            new_context=(c.new_text or "")[:800] or None,
            old_snapshot_sha256=old_sha,
            new_snapshot_sha256=new_sha,
            alignment_score_components=(
                c.alignment_score.model_dump(mode="json") if c.alignment_score else {}
            ),
            classification_reasons=list(c.classification_reasons or []),
            alternative_candidates=[],
            ambiguity_state=(
                "ambiguous"
                if c.classification == ChangeClassification.AMBIGUOUS
                else "none"
            ),
            review_questions=[
                "Is the proposed classification correct?",
                "Are the source locators sufficient?",
            ],
            artifact_references=[
                f"capsules/{pair_id}/report/report.json",
            ],
        )
        packets.append(pkt.model_dump(mode="json"))
    return packets


def write_packets_jsonl(packets: list[dict[str, Any]], path: Path) -> None:
    lines = [json.dumps(p, sort_keys=True, ensure_ascii=False) for p in packets]
    atomic_write_text(Path(path), "\n".join(lines) + ("\n" if lines else ""))
