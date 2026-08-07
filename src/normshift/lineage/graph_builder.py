"""Build multi-version lineage into LineageStore from document paths."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.extract.extractor import extract_from_source
from normshift.lineage.store import LineageStore
from normshift.model.types import AdapterName, ChangeClassification, ProfileName
from normshift.source import load_immutable_source


def _sid(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]
    return f"{prefix}_{h}"


def build_lineage_from_paths(
    paths: list[Path],
    *,
    store: LineageStore,
    profile: ProfileName = ProfileName.RFC2119,
    adapter: AdapterName = AdapterName.AUTO,
    chain_id: str = "chain",
) -> dict[str, Any]:
    if len(paths) < 2:
        raise ValueError("lineage requires at least two document versions")

    docs = []
    for p in paths:
        src = load_immutable_source(p, adapter=adapter)
        doc = extract_from_source(src, profile)
        docs.append((src, doc))

    store.set_meta("schema_version", "1.0.0")
    store.set_meta("experimental", "true")
    store.set_meta("label_authority", "AUTO")
    store.set_meta("status", "EXPERIMENTAL_NOT_ADJUDICATED")

    # Snapshot + instance nodes
    instances_by_version: list[list[str]] = []
    for src, doc in docs:
        snap_id = _sid("snap", src.sha256, src.display_path)
        store.put_node(
            snap_id,
            "DocumentSnapshot",
            {
                "path": src.display_path,
                "sha256": src.sha256,
                "version": src.document_version,
                "byte_length": src.byte_length,
                "family": src.family.value,
            },
        )
        inst_ids: list[str] = []
        for req in doc.requirements:
            iid = _sid("ri", src.sha256, req.requirement_id)
            store.put_node(
                iid,
                "RequirementInstance",
                {
                    "requirement_id": req.requirement_id,
                    "snapshot_id": snap_id,
                    "modality": req.modality.value,
                    "normalized_text": req.normalized_text,
                    "fingerprint": req.fingerprint,
                    "source_locator": req.source_locator,
                    "document_version": req.document_version,
                },
            )
            store.put_edge(
                _sid("e", "LOCATED_IN", iid, snap_id),
                "LOCATED_IN",
                {"from": iid, "to": snap_id},
            )
            # Lineage id from fingerprint (hypothesized)
            lid = _sid("lin", req.fingerprint)
            store.put_node(
                lid,
                "RequirementLineage",
                {
                    "fingerprint_seed": req.fingerprint,
                    "label_authority": "AUTO",
                },
            )
            store.put_edge(
                _sid("e", "INSTANCE_OF", iid, lid),
                "INSTANCE_OF",
                {"from": iid, "to": lid, "confidence": req.confidence},
            )
            inst_ids.append(iid)
        instances_by_version.append(inst_ids)

    # Pairwise change events
    change_count = 0
    ambiguous = 0
    split_merge = 0
    for i in range(len(docs) - 1):
        old_src, old_doc = docs[i]
        new_src, new_doc = docs[i + 1]
        pairs = align_requirements(old_doc.requirements, new_doc.requirements)
        changes = classify_pairs(pairs)
        for ch in changes:
            change_count += 1
            et = {
                ChangeClassification.STRENGTHENED: "STRENGTHENED_TO",
                ChangeClassification.WEAKENED: "WEAKENED_TO",
                ChangeClassification.POLARITY_FLIP: "POLARITY_FLIPPED_TO",
                ChangeClassification.MOVED: "MOVED_TO",
                ChangeClassification.CONDITION_ADDED: "CONDITION_CHANGED_TO",
                ChangeClassification.CONDITION_REMOVED: "CONDITION_CHANGED_TO",
                ChangeClassification.EXCEPTION_ADDED: "EXCEPTION_CHANGED_TO",
                ChangeClassification.EXCEPTION_REMOVED: "EXCEPTION_CHANGED_TO",
                ChangeClassification.AMBIGUOUS: "AMBIGUOUS_WITH",
                ChangeClassification.UNCHANGED: "SAME_AS",
                ChangeClassification.EDITORIAL: "SAME_AS",
                ChangeClassification.ADDED: "REPLACED_BY",
                ChangeClassification.REMOVED: "REPLACED_BY",
            }.get(ch.classification, "AMBIGUOUS_WITH")
            if ch.classification == ChangeClassification.AMBIGUOUS:
                ambiguous += 1
            eid = _sid("ce", ch.change_id, old_src.sha256, new_src.sha256)
            payload = {
                "change_id": ch.change_id,
                "classification": ch.classification.value,
                "old_requirement_id": ch.old_requirement_id,
                "new_requirement_id": ch.new_requirement_id,
                "old_snapshot_sha256": old_src.sha256,
                "new_snapshot_sha256": new_src.sha256,
                "confidence": ch.confidence,
                "reasons": ch.classification_reasons,
                "uncertainty_state": (
                    "ambiguous"
                    if ch.classification == ChangeClassification.AMBIGUOUS
                    else "proposed"
                ),
                "review_state": "AUTO",
                "label_authority": "AUTO",
                "classifier_version": "0.3.0-expedition",
                "score_components": (
                    ch.alignment_score.model_dump(mode="json")
                    if ch.alignment_score
                    else {}
                ),
            }
            store.put_node(eid, "ChangeEvent", payload)
            store.put_edge(
                _sid("e", et, eid),
                et,
                {
                    "from_change": eid,
                    "old_requirement_id": ch.old_requirement_id,
                    "new_requirement_id": ch.new_requirement_id,
                    **payload,
                },
            )
            if ch.classification == ChangeClassification.AMBIGUOUS:
                aid = _sid("amb", ch.change_id)
                store.put_node(
                    aid,
                    "AmbiguityCase",
                    {
                        "change_event_id": eid,
                        "reasons": ch.classification_reasons,
                        "label_authority": "AUTO",
                    },
                )

    counts = store.counts()
    return {
        "versions": len(docs),
        "change_events": change_count,
        "ambiguous_cases": ambiguous,
        "split_merge_candidates": split_merge,
        "store_counts": counts,
        "chain_id": chain_id,
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
    }
