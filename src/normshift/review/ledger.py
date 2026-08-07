"""Append-only review ledger validation and merge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from normshift.review.model import ReviewDecision
from normshift.strict_json import strict_loads


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text = Path(path).read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        # strict parse per line via full document
        obj = strict_loads(line.encode("utf-8"))
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{i}: not an object")
        rows.append(obj)
    return rows


def validate_ledger(
    path: Path,
    *,
    known_packet_ids: set[str] | None = None,
    allow_external: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        rows = _load_jsonl(path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "errors": [str(exc)], "count": 0}
    seen: set[str] = set()
    for row in rows:
        try:
            dec = ReviewDecision.model_validate(row)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"invalid decision: {exc}")
            continue
        if dec.decision_id in seen:
            errors.append(f"duplicate decision_id {dec.decision_id}")
        seen.add(dec.decision_id)
        if known_packet_ids is not None and dec.packet_id not in known_packet_ids:
            errors.append(f"unknown packet_id {dec.packet_id}")
        if (
            dec.label_authority in {"EXTERNAL_REVIEW", "EXTERNAL_ADJUDICATION"}
            and not allow_external
        ):
            errors.append(
                f"external authority not allowed without import: {dec.decision_id}"
            )
    return {"ok": len(errors) == 0, "errors": errors, "count": len(rows)}


def merge_ledgers(paths: list[Path], out: Path) -> dict[str, Any]:
    merged: list[dict[str, Any]] = []
    ids: set[str] = set()
    errors: list[str] = []
    for p in paths:
        for row in _load_jsonl(p):
            did = str(row.get("decision_id"))
            if did in ids:
                errors.append(f"duplicate across inputs: {did}")
                continue
            ids.add(did)
            merged.append(row)
    merged.sort(key=lambda r: (int(r.get("sequence", 0)), str(r.get("decision_id"))))
    lines = [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in merged]
    out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return {"ok": len(errors) == 0, "errors": errors, "count": len(merged)}
