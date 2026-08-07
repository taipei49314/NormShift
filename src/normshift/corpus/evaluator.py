"""Three-layer corpus metrics (never score AUTO as gold)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from normshift.campaign.model import CampaignPlan


def evaluate_campaign(
    *,
    plan: CampaignPlan,
    snapshots: list[dict[str, Any]],
    unique_objects: int,
    packets: list[dict[str, Any]],
    discovery: list[dict[str, Any]],
    pair_ids: list[str],
    lineage_ids: list[str],
) -> dict[str, Any]:
    real_pairs = [
        p
        for p in plan.pairs
        if not p.pair_id.startswith("fixture") and "fixture" not in p.pair_id
    ]
    synth_pairs = [p for p in plan.pairs if p not in real_pairs]
    # redistributable synthetic imports
    synth_snaps = [s for s in plan.snapshots if s.family == "synthetic"]
    real_snaps = [s for s in plan.snapshots if s.family != "synthetic"]

    class_counts = Counter(str(d.get("kind")) for d in discovery)
    packet_classes = Counter(str(p.get("proposed_classification")) for p in packets)

    return {
        "schema_version": "1.0.0",
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "layer_a_synthetic_gold": {
            "note": "Use frozen fixture gold suite via `normshift benchmark`",
            "status": "SEPARATE_COMMAND",
            "synthetic_pairs_in_campaign": len(synth_pairs),
            "synthetic_snapshots_in_campaign": len(synth_snaps),
        },
        "layer_b_real_provisional": {
            "label_authority": "AUTO",
            "unique_content_objects": unique_objects,
            "snapshot_observations": len(snapshots),
            "logical_versions": len({s.get("version_label") for s in snapshots}),
            "real_pair_count": len(real_pairs),
            "synthetic_pair_count": len(synth_pairs),
            "pair_capsule_ids": pair_ids,
            "discovery_items": len(discovery),
            "auto_change_proposals_by_class": dict(sorted(class_counts.items())),
            "review_packets": len(packets),
            "review_packets_by_class": dict(sorted(packet_classes.items())),
            "lineage_chains": lineage_ids,
            "ambiguity_rate": (
                class_counts.get("AMBIGUOUS", 0) / len(discovery) if discovery else 0.0
            ),
            "accuracy_metrics": "NOT_COMPUTED_AUTO_IS_NOT_GOLD",
        },
        "layer_c_externally_reviewed": {
            "status": "NOT_AVAILABLE",
            "reason": "NO_EXTERNAL_REVIEW_ARTIFACT",
        },
        "inventory": {
            "real_snapshots_planned": len(real_snaps),
            "synthetic_snapshots_planned": len(synth_snaps),
        },
    }
