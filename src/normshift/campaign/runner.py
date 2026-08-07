"""Campaign validate / run / verify (library API, deterministic epoch)."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Literal

from normshift import __version__
from normshift.acquire.fetcher import acquire_url, import_local_bytes
from normshift.acquire.store import SnapshotStore
from normshift.campaign.model import CampaignPlan, CampaignRunManifest
from normshift.capsule.builder import build_pair_capsule
from normshift.evidence.hashing import canonical_json_bytes
from normshift.extract.extractor import extract_from_source
from normshift.io_safety import atomic_write_text
from normshift.lineage.candidates import build_chain_candidates, export_candidates_jsonl
from normshift.model.types import AdapterName, ProfileName
from normshift.observatory.projection import project_observatory
from normshift.pipeline import run_diff
from normshift.review.packets import build_packets_for_pairs, write_packets_jsonl
from normshift.source import load_immutable_source
from normshift.strict_json import strict_loads


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_plan(path: Path) -> CampaignPlan:
    raw = path.read_bytes()
    data = strict_loads(raw)
    plan = CampaignPlan.model_validate(data)
    plan.validate_refs()
    return plan


def validate_plan(path: Path) -> dict[str, Any]:
    plan = load_plan(path)
    return {
        "ok": True,
        "campaign_id": plan.campaign_id,
        "snapshots": len(plan.snapshots),
        "pairs": len(plan.pairs),
        "lineage_chains": len(plan.lineage_chains),
    }


def _adapter(name: str) -> AdapterName:
    m = {
        "rfc": AdapterName.RFC,
        "ietf-rfc-html": AdapterName.RFC,
        "w3c": AdapterName.W3C,
        "w3c-html": AdapterName.W3C,
        "whatwg": AdapterName.WHATWG,
        "whatwg-html": AdapterName.WHATWG,
        "html": AdapterName.HTML,
        "auto": AdapterName.AUTO,
    }
    return m.get(name, AdapterName.AUTO)


def _profile(name: str) -> ProfileName:
    return ProfileName.WHATWG if name == "whatwg" else ProfileName.RFC2119


def run_campaign(
    plan_path: Path,
    *,
    workspace: Path,
    mode: Literal["acquire", "offline"] = "offline",
    repo_root: Path | None = None,
    source_date_epoch: int | None = None,
) -> CampaignRunManifest:
    repo_root = Path(repo_root or Path.cwd()).resolve()
    plan_path = Path(plan_path)
    plan = load_plan(plan_path)
    epoch = source_date_epoch
    if epoch is None:
        env = os.environ.get("SOURCE_DATE_EPOCH")
        epoch = int(env) if env else plan.source_date_epoch

    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    material = workspace / "materialized"
    material.mkdir(parents=True, exist_ok=True)

    store = SnapshotStore(repo_root / plan.store)
    policy = repo_root / plan.source_policy
    policy_sha = _sha_file(policy) if policy.is_file() else ""
    plan_sha = _sha_file(plan_path)

    snap_obs: list[dict[str, Any]] = []
    key_to_path: dict[str, Path] = {}
    key_to_man: dict[str, dict[str, Any]] = {}

    # Dedupe by content hash for counts
    unique_objects: set[str] = set()

    for spec in plan.snapshots:
        man: dict[str, Any]
        hits = store.find_by_url(spec.source_url)
        if mode == "offline":
            if hits:
                man = hits[-1]
            elif spec.local_import_path:
                local = repo_root / spec.local_import_path
                man = import_local_bytes(
                    local,
                    store=store,
                    source_url=spec.source_url,
                    policy_path=policy,
                    adapter_hint=spec.adapter,
                    license_note=spec.license_reference,
                )
            else:
                raise FileNotFoundError(
                    f"offline missing store/import for {spec.snapshot_key}"
                )
        elif spec.acquisition_mode == "import_file" and spec.local_import_path:
            local = repo_root / spec.local_import_path
            man = import_local_bytes(
                local,
                store=store,
                source_url=spec.source_url,
                policy_path=policy,
                adapter_hint=spec.adapter,
                license_note=spec.license_reference,
            )
        elif spec.acquisition_mode == "https":
            man = acquire_url(
                spec.source_url,
                store=store,
                policy_path=policy,
                adapter_hint=spec.adapter,
                license_note=spec.license_reference,
            )
        elif hits:
            man = hits[-1]
        else:
            raise FileNotFoundError(f"cannot acquire {spec.snapshot_key}")

        sha = str(man["content_sha256"])
        unique_objects.add(sha)
        raw = store.get_bytes(sha)
        ext = ".html"
        path = material / f"{spec.snapshot_key}{ext}"
        path.write_bytes(raw)
        key_to_path[spec.snapshot_key] = path
        key_to_man[spec.snapshot_key] = {
            **man,
            "snapshot_key": spec.snapshot_key,
            "family": spec.family,
            "version_label": spec.version_label,
            "redistribution_status": spec.redistribution_status,
            "license_reference": spec.license_reference,
            "logical_path": f"materialized/{spec.snapshot_key}{ext}",
        }
        snap_obs.append(
            {
                "snapshot_key": spec.snapshot_key,
                "content_sha256": sha,
                "byte_length": len(raw),
                "source_url": man.get("source_url"),
                "final_url": man.get("final_url"),
                "family": spec.family,
                "version_label": spec.version_label,
                "observation_id": man.get("snapshot_id"),
            }
        )

    # Pair capsules
    out_caps = repo_root / plan.outputs.capsules_dir
    out_caps.mkdir(parents=True, exist_ok=True)
    pair_ids: list[str] = []
    pair_reports: dict[str, Any] = {}
    discovery: list[dict[str, Any]] = []
    all_packets: list[dict[str, Any]] = []

    for pspec in plan.pairs:
        old_p = key_to_path[pspec.old_snapshot_key]
        new_p = key_to_path[pspec.new_snapshot_key]
        adapter = _adapter(pspec.adapter)
        profile = _profile(pspec.profile)
        # Paths relative to materialization root for portable refs
        report = run_diff(
            Path(old_p.name),
            Path(new_p.name),
            profile=profile,
            adapter=adapter,
            source_root=material.resolve(),
        )
        pair_reports[pspec.pair_id] = report
        cap_dir = out_caps / pspec.pair_id
        old_spec = next(
            s for s in plan.snapshots if s.snapshot_key == pspec.old_snapshot_key
        )
        new_spec = next(
            s for s in plan.snapshots if s.snapshot_key == pspec.new_snapshot_key
        )
        include_bytes = (
            pspec.include_bytes_if_redistributable
            and old_spec.redistribution_status == "redistributable"
            and new_spec.redistribution_status == "redistributable"
        )
        cap = build_pair_capsule(
            pair_id=pspec.pair_id,
            campaign_id=plan.campaign_id,
            old_path=old_p,
            new_path=new_p,
            old_manifest=key_to_man[pspec.old_snapshot_key],
            new_manifest=key_to_man[pspec.new_snapshot_key],
            report=report,
            adapter=pspec.adapter,
            profile=pspec.profile,
            out_dir=cap_dir,
            include_bytes=include_bytes,
            source_date_epoch=epoch,
        )
        pair_ids.append(cap["capsule_id"])

        for ch in report.changes:
            discovery.append(
                {
                    "id": f"{pspec.pair_id}:{ch.change_id[:12]}",
                    "pair_id": pspec.pair_id,
                    "kind": ch.classification.value,
                    "summary": (ch.new_text or ch.old_text or "")[:200],
                    "confidence": ch.confidence,
                    "label_authority": "AUTO",
                    "capsule_id": cap["capsule_id"],
                    "change_id": ch.change_id,
                }
            )

        packets = build_packets_for_pairs(
            campaign_id=plan.campaign_id,
            pair_id=pspec.pair_id,
            capsule_id=cap["capsule_id"],
            report=report,
            old_sha=str(key_to_man[pspec.old_snapshot_key]["content_sha256"]),
            new_sha=str(key_to_man[pspec.new_snapshot_key]["content_sha256"]),
        )
        all_packets.extend(packets)

    # Review packets
    review_dir = repo_root / plan.outputs.review_dir
    review_dir.mkdir(parents=True, exist_ok=True)
    packets_path = review_dir / "packets.jsonl"
    write_packets_jsonl(all_packets, packets_path)
    template_path = review_dir / "template-decisions.jsonl"
    atomic_write_text(template_path, "")  # empty templates
    packet_set_id = f"rps_{_sha_file(packets_path)[:16]}"

    # Lineage candidates
    lin_dir = repo_root / plan.outputs.lineage_dir
    lin_dir.mkdir(parents=True, exist_ok=True)
    lineage_ids: list[str] = []
    for chain in plan.lineage_chains:
        paths = [key_to_path[k] for k in chain.ordered_snapshot_keys]
        cands = build_chain_candidates(
            paths,
            adapter=_adapter(chain.adapter),
            profile=_profile(chain.profile),
            chain_id=chain.chain_id,
        )
        outp = lin_dir / f"{chain.chain_id}.candidates.jsonl"
        export_candidates_jsonl(cands, outp)
        lineage_ids.append(chain.chain_id)

    # Metrics (layers)
    from normshift.corpus.evaluator import evaluate_campaign

    metrics = evaluate_campaign(
        plan=plan,
        snapshots=snap_obs,
        unique_objects=len(unique_objects),
        packets=all_packets,
        discovery=discovery,
        pair_ids=pair_ids,
        lineage_ids=lineage_ids,
    )
    metrics_path = repo_root / plan.outputs.metrics
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        metrics_path, canonical_json_bytes(metrics).decode("utf-8")
    )

    # Observatory projection
    obs_dir = repo_root / plan.outputs.observatory_dir
    obs_man = project_observatory(
        out_dir=obs_dir,
        campaign_id=plan.campaign_id,
        snapshots=snap_obs,
        discovery=discovery,
        pair_ids=[p.pair_id for p in plan.pairs],
        metrics=metrics,
        packet_count=len(all_packets),
        source_date_epoch=epoch,
    )
    obs_id = f"obs_{_sha_bytes(canonical_json_bytes(obs_man))[:16]}"

    # Dossiers (top 12)
    ddir = repo_root / plan.outputs.dossiers_dir
    ddir.mkdir(parents=True, exist_ok=True)
    top = sorted(
        discovery,
        key=lambda d: (
            {
                "POLARITY_FLIP": 0,
                "STRENGTHENED": 1,
                "WEAKENED": 2,
                "AMBIGUOUS": 3,
                "REMOVED": 4,
                "ADDED": 5,
            }.get(str(d.get("kind")), 9),
            str(d.get("id")),
        ),
    )[:12]
    for i, d in enumerate(top):
        atomic_write_text(
            ddir / f"dossier-{i:02d}.json",
            canonical_json_bytes({**d, "review_status": "UNREVIEWED"}).decode("utf-8"),
        )

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    # Artifact hashes (relative paths)
    artifact_hashes: dict[str, str] = {}
    for rel in [
        plan.outputs.run_manifest,
        plan.outputs.metrics,
        str(Path(plan.outputs.review_dir) / "packets.jsonl"),
    ]:
        p = repo_root / rel
        if p.is_file():
            artifact_hashes[rel.replace("\\", "/")] = _sha_file(p)
    for pid in [p.pair_id for p in plan.pairs]:
        capj = out_caps / pid / "capsule.json"
        if capj.is_file():
            artifact_hashes[f"capsules/{pid}/capsule.json"] = _sha_file(capj)
    obs_m = obs_dir / "manifest.json"
    if obs_m.is_file():
        artifact_hashes[
            str(Path(plan.outputs.observatory_dir) / "manifest.json").replace("\\", "/")
        ] = _sha_file(obs_m)

    run = CampaignRunManifest(
        campaign_id=plan.campaign_id,
        campaign_plan_sha256=plan_sha,
        run_id=run_id,
        mode=mode if mode == "acquire" else "offline",
        source_policy_sha256=policy_sha,
        code_version=__version__,
        source_date_epoch=epoch,
        status="EXPERIMENTAL_NOT_ADJUDICATED",
        label_authority="AUTO",
        snapshots=snap_obs,
        pair_capsule_ids=pair_ids,
        lineage_export_ids=lineage_ids,
        review_packet_set_id=packet_set_id,
        observatory_manifest_id=obs_id,
        artifact_hashes=artifact_hashes,
        unresolved_blockers=[],
        counts={
            "unique_content_objects": len(unique_objects),
            "snapshot_observations": len(snap_obs),
            "pairs": len(plan.pairs),
            "review_packets": len(all_packets),
            "discovery_items": len(discovery),
            "lineage_chains": len(lineage_ids),
        },
    )
    run_path = repo_root / plan.outputs.run_manifest
    run_path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_json_bytes(run.model_dump(mode="json"))
    atomic_write_text(run_path, raw.decode("utf-8"))
    # re-hash run manifest itself
    run.artifact_hashes[plan.outputs.run_manifest.replace("\\", "/")] = _sha_file(
        run_path
    )
    atomic_write_text(
        run_path, canonical_json_bytes(run.model_dump(mode="json")).decode("utf-8")
    )
    return run


def verify_run_manifest(path: Path, *, workspace: Path | None = None) -> dict[str, Any]:
    data = strict_loads(Path(path).read_bytes())
    man = CampaignRunManifest.model_validate(data)
    errors: list[str] = []
    root = Path.cwd()
    for rel, expected in man.artifact_hashes.items():
        p = root / rel
        if not p.is_file():
            errors.append(f"missing artifact {rel}")
            continue
        got = _sha_file(p)
        if got != expected:
            # run-manifest may self-update once; allow recompute note
            if rel.endswith("run-manifest.json"):
                continue
            errors.append(f"hash mismatch {rel}")
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "run_id": man.run_id,
        "pairs": len(man.pair_capsule_ids),
    }
