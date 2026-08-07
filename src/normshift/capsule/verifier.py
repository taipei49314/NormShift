"""Capsule verification."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from normshift.strict_json import strict_loads


def verify_capsule(capsule_dir: Path) -> dict[str, Any]:
    root = Path(capsule_dir)
    errors: list[str] = []
    cap_path = root / "capsule.json"
    if not cap_path.is_file():
        return {"ok": False, "errors": ["missing capsule.json"]}
    try:
        cap = strict_loads(cap_path.read_bytes())
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "errors": [f"capsule.json parse: {exc}"]}
    if not isinstance(cap, dict):
        return {"ok": False, "errors": ["capsule root not object"]}

    offline = bool(cap.get("offline_replay"))
    if offline and cap.get("blocking_reason"):
        errors.append("full capsule must not set blocking_reason")
    if not offline and cap.get("blocking_reason") != "SOURCE_BYTES_NOT_INCLUDED":
        errors.append("thin capsule must declare SOURCE_BYTES_NOT_INCLUDED")

    hashes_path = root / "hashes.json"
    if not hashes_path.is_file():
        errors.append("missing hashes.json")
        return {"ok": False, "errors": errors}
    try:
        hashes = strict_loads(hashes_path.read_bytes())
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "errors": [f"hashes parse: {exc}"]}
    if not isinstance(hashes, dict):
        return {"ok": False, "errors": ["hashes not object"]}

    for rel, expected in hashes.items():
        if rel in {"hashes.json"}:
            continue
        p = root / rel
        if not p.is_file():
            errors.append(f"missing {rel}")
            continue
        # path escape
        try:
            p.resolve().relative_to(root.resolve())
        except ValueError:
            errors.append(f"escape {rel}")
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != expected:
            errors.append(f"hash mismatch {rel}")
        if "\\" in rel or rel.startswith("/") or ".." in rel.split("/"):
            errors.append(f"illegal logical path {rel}")

    if offline:
        for name in ("source/old.document", "source/new.document"):
            if not (root / name).is_file():
                errors.append(f"full capsule missing {name}")
    else:
        for name in ("source/old.document", "source/new.document"):
            if (root / name).is_file():
                # allowed but then offline should be true ideally — warn as error for honesty
                errors.append(f"thin capsule unexpectedly contains {name}")

    # required structural files
    for req in (
        "source/old.manifest.json",
        "source/new.manifest.json",
        "report/report.json",
        "extracted/old.requirements.json",
        "extracted/new.requirements.json",
    ):
        if not (root / req).is_file():
            errors.append(f"missing required {req}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "capsule_id": cap.get("capsule_id"),
        "offline_replay": offline,
        "pair_id": cap.get("pair_id"),
    }
