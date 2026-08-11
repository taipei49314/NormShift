#!/usr/bin/env python3
"""Freeze the exact scorer source/schema/canonicalizer/test inventory."""

from __future__ import annotations

import hashlib
import platform
import sys
from pathlib import Path

import pydantic

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from normshift.acceptance.models import ScorerManifest  # noqa: E402
from normshift.acceptance.scorer import (  # noqa: E402
    POLICY_ID,
    POLICY_SHA256,
    REQUIRED_SCORER_FILES,
    SCORER_ID,
    bounded_read_regular_file,
)
from normshift.evidence.hashing import canonical_json_bytes  # noqa: E402
from normshift.io_safety import write_transaction  # noqa: E402
from normshift.portable_ref import resolve_declared_under_root  # noqa: E402


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    records: list[dict[str, object]] = []
    for ref in sorted(REQUIRED_SCORER_FILES):
        path, _ = resolve_declared_under_root(ROOT, ref)
        raw = bounded_read_regular_file(
            path,
            f"scorer authority file {ref}",
            max_bytes=8 * 1024 * 1024,
        )
        records.append({"path": ref, "sha256": _sha256(raw), "bytes": len(raw)})
    manifest = ScorerManifest.model_validate(
        {
            "kind": "normshift-acceptance-scorer-manifest",
            "schema_version": "1.0.0",
            "scorer_id": SCORER_ID,
            "policy_id": POLICY_ID,
            "policy_sha256": POLICY_SHA256,
            "frozen_before_blind_evaluation": True,
            "runtime": {
                "python_implementation": platform.python_implementation(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "pydantic_version": pydantic.__version__,
            },
            "files": records,
        }
    )
    raw = canonical_json_bytes(manifest.model_dump(mode="json"))
    digest = _sha256(raw)
    manifest_path = ROOT / "acceptance" / "scorer_v1_manifest.json"
    sidecar_path = ROOT / "acceptance" / "scorer_v1_manifest.json.sha256"
    write_transaction(
        {
            manifest_path: raw,
            sidecar_path: f"{digest}  scorer_v1_manifest.json\n".encode("ascii"),
        }
    )
    print(digest)


if __name__ == "__main__":
    main()
