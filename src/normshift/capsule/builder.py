"""Pair evidence capsule builder."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from normshift.evidence.hashing import canonical_json_bytes
from normshift.extract.extractor import extract_from_source
from normshift.io_safety import atomic_write_bytes, atomic_write_text
from normshift.model.types import AdapterName, ProfileName, Report
from normshift.report.builder import markdown_report_text, report_to_dict
from normshift.source import load_immutable_source


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _adapter(name: str) -> AdapterName:
    return {
        "rfc": AdapterName.RFC,
        "ietf-rfc-html": AdapterName.RFC,
        "w3c": AdapterName.W3C,
        "w3c-html": AdapterName.W3C,
        "whatwg": AdapterName.WHATWG,
        "whatwg-html": AdapterName.WHATWG,
        "html": AdapterName.HTML,
    }.get(name, AdapterName.AUTO)


def _profile(name: str) -> ProfileName:
    return ProfileName.WHATWG if name == "whatwg" else ProfileName.RFC2119


def build_pair_capsule(
    *,
    pair_id: str,
    campaign_id: str,
    old_path: Path,
    new_path: Path,
    old_manifest: dict[str, Any],
    new_manifest: dict[str, Any],
    report: Report,
    adapter: str,
    profile: str,
    out_dir: Path,
    include_bytes: bool,
    source_date_epoch: int | None = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    for sub in ("source", "extracted", "report", "review", "lineage", "replay"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    offline = bool(include_bytes)
    # Source manifests (always)
    atomic_write_text(
        out_dir / "source" / "old.manifest.json",
        canonical_json_bytes(old_manifest).decode("utf-8"),
    )
    atomic_write_text(
        out_dir / "source" / "new.manifest.json",
        canonical_json_bytes(new_manifest).decode("utf-8"),
    )
    if include_bytes:
        atomic_write_bytes(out_dir / "source" / "old.document", old_path.read_bytes())
        atomic_write_bytes(out_dir / "source" / "new.document", new_path.read_bytes())

    ad = _adapter(adapter)
    pr = _profile(profile)
    old_src = load_immutable_source(old_path, adapter=ad)
    new_src = load_immutable_source(new_path, adapter=ad)
    old_doc = extract_from_source(old_src, pr)
    new_doc = extract_from_source(new_src, pr)
    atomic_write_text(
        out_dir / "extracted" / "old.requirements.json",
        canonical_json_bytes(old_doc.model_dump(mode="json")).decode("utf-8"),
    )
    atomic_write_text(
        out_dir / "extracted" / "new.requirements.json",
        canonical_json_bytes(new_doc.model_dump(mode="json")).decode("utf-8"),
    )

    rep_dict = report_to_dict(report)
    rep_bytes = canonical_json_bytes(rep_dict)
    atomic_write_bytes(out_dir / "report" / "report.json", rep_bytes)
    atomic_write_text(out_dir / "report" / "report.md", markdown_report_text(report))

    # empty review/lineage placeholders filled by campaign
    atomic_write_text(out_dir / "review" / "packets.jsonl", "")
    atomic_write_text(out_dir / "lineage" / "candidates.jsonl", "")
    cmds = {
        "verify": [
            "normshift",
            "capsule",
            "verify",
            f"capsules/{pair_id}",
        ],
        "source_date_epoch": source_date_epoch,
    }
    atomic_write_text(
        out_dir / "replay" / "commands.json",
        canonical_json_bytes(cmds).decode("utf-8"),
    )
    atomic_write_text(
        out_dir / "LICENSE_SCOPE.md",
        (
            "# License scope\n\n"
            f"offline_replay={offline}\n"
            f"old redistribution={old_manifest.get('redistribution_status')}\n"
            f"new redistribution={new_manifest.get('redistribution_status')}\n"
            f"old license={old_manifest.get('license_reference')}\n"
            f"new license={new_manifest.get('license_reference')}\n"
        ),
    )
    atomic_write_text(
        out_dir / "LIMITATIONS.md",
        (
            "# Capsule limitations\n\n"
            + (
                "Full offline replay with included bytes.\n"
                if offline
                else "Thin capsule: SOURCE_BYTES_NOT_INCLUDED; offline_replay=false.\n"
            )
            + "All classifications are AUTO proposals.\n"
        ),
    )

    # Hash inventory
    hashes: dict[str, str] = {}
    for p in sorted(out_dir.rglob("*")):
        if p.is_file() and p.name != "hashes.json" and p.name != "capsule.json":
            rel = p.relative_to(out_dir).as_posix()
            hashes[rel] = _sha(p.read_bytes())

    atomic_write_text(
        out_dir / "hashes.json",
        canonical_json_bytes(hashes).decode("utf-8"),
    )
    hashes["hashes.json"] = _sha((out_dir / "hashes.json").read_bytes())

    capsule_id = f"cap_{pair_id}_{hashes.get('report/report.json', '')[:12]}"
    cap = {
        "schema_version": "1.0.0",
        "capsule_id": capsule_id,
        "pair_id": pair_id,
        "campaign_id": campaign_id,
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "label_authority": "AUTO",
        "offline_replay": offline,
        "blocking_reason": None if offline else "SOURCE_BYTES_NOT_INCLUDED",
        "old_snapshot": {
            "content_sha256": old_manifest.get("content_sha256"),
            "source_url": old_manifest.get("source_url"),
            "version_label": old_manifest.get("version_label"),
        },
        "new_snapshot": {
            "content_sha256": new_manifest.get("content_sha256"),
            "source_url": new_manifest.get("source_url"),
            "version_label": new_manifest.get("version_label"),
        },
        "adapter": adapter,
        "profile": profile,
        "extractor_version": __import__("normshift").__version__,
        "aligner_version": __import__("normshift").__version__,
        "classifier_version": __import__("normshift").__version__,
        "report_sha256": hashes.get("report/report.json"),
        "requirements_sha256": {
            "old": hashes.get("extracted/old.requirements.json"),
            "new": hashes.get("extracted/new.requirements.json"),
        },
        "artifact_inventory": sorted(hashes.keys()),
        "license_decision": {
            "include_bytes": include_bytes,
            "old": old_manifest.get("redistribution_status"),
            "new": new_manifest.get("redistribution_status"),
        },
        "known_limitations": [
            "AUTO labels only",
            "Not externally adjudicated",
        ],
    }
    atomic_write_text(
        out_dir / "capsule.json",
        canonical_json_bytes(cap).decode("utf-8"),
    )
    return cap
