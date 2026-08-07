"""Primary continuity + split/merge candidate generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from normshift.align.aligner import align_requirements
from normshift.classify.classifier import classify_pairs
from normshift.extract.extractor import extract_from_source
from normshift.io_safety import atomic_write_text
from normshift.model.types import AdapterName, ChangeClassification, ProfileName
from normshift.source import load_immutable_source


def _cid(*parts: str) -> str:
    return "lc_" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:18]


def build_chain_candidates(
    paths: list[Path],
    *,
    adapter: AdapterName,
    profile: ProfileName,
    chain_id: str,
) -> list[dict[str, Any]]:
    docs = []
    for p in paths:
        src = load_immutable_source(p, adapter=adapter)
        doc = extract_from_source(src, profile)
        docs.append((src, doc))

    out: list[dict[str, Any]] = []
    # instance index per version
    for i in range(len(docs) - 1):
        old_src, old_doc = docs[i]
        new_src, new_doc = docs[i + 1]
        pairs = align_requirements(old_doc.requirements, new_doc.requirements)
        changes = classify_pairs(pairs)

        # Map old id -> list of new ids from pair alignments
        from collections import defaultdict

        old_to_news: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
        new_to_olds: dict[str, list[tuple[str, float, str]]] = defaultdict(list)

        for ch in changes:
            cls = ch.classification.value
            if ch.old_requirement_id and ch.new_requirement_id:
                cont = cls not in {
                    ChangeClassification.AMBIGUOUS.value,
                    ChangeClassification.ADDED.value,
                    ChangeClassification.REMOVED.value,
                }
                if cont or cls == ChangeClassification.AMBIGUOUS.value:
                    old_to_news[ch.old_requirement_id].append(
                        (ch.new_requirement_id, float(ch.confidence), cls)
                    )
                    new_to_olds[ch.new_requirement_id].append(
                        (ch.old_requirement_id, float(ch.confidence), cls)
                    )
                out.append(
                    {
                        "candidate_id": _cid(
                            chain_id, "edge", ch.change_id, old_src.sha256
                        ),
                        "kind": "CONTINUITY" if cont else "AMBIGUOUS_LINK",
                        "chain_id": chain_id,
                        "old_instance_id": ch.old_requirement_id,
                        "new_instance_ids": [ch.new_requirement_id],
                        "classification": cls,
                        "confidence": ch.confidence,
                        "label_authority": "AUTO",
                        "review_state": "AUTO",
                        "old_snapshot_sha256": old_src.sha256,
                        "new_snapshot_sha256": new_src.sha256,
                        "rationale": list(ch.classification_reasons or []),
                        "score_components": (
                            ch.alignment_score.model_dump(mode="json")
                            if ch.alignment_score
                            else {}
                        ),
                    }
                )

        # Split: one old → multiple high-confidence new
        for oid, news in old_to_news.items():
            # near neighbors: multiple news with conf >= 0.4
            near = [n for n in news if n[1] >= 0.4]
            if len(near) >= 2:
                out.append(
                    {
                        "candidate_id": _cid(chain_id, "split", oid, new_src.sha256),
                        "kind": "SPLIT",
                        "chain_id": chain_id,
                        "old_instance_id": oid,
                        "new_instance_ids": sorted({n[0] for n in near}),
                        "classification": "SPLIT_CANDIDATE",
                        "confidence": sum(n[1] for n in near) / len(near),
                        "label_authority": "AUTO",
                        "review_state": "AUTO",
                        "old_snapshot_sha256": old_src.sha256,
                        "new_snapshot_sha256": new_src.sha256,
                        "rationale": [
                            "multiple plausible successors",
                            f"near_count={len(near)}",
                        ],
                        "score_components": {
                            "successors": [
                                {"id": n[0], "confidence": n[1], "class": n[2]}
                                for n in near
                            ]
                        },
                    }
                )

        # Merge: multiple old → one new
        for nid, olds in new_to_olds.items():
            near = [o for o in olds if o[1] >= 0.4]
            if len(near) >= 2:
                out.append(
                    {
                        "candidate_id": _cid(chain_id, "merge", nid, old_src.sha256),
                        "kind": "MERGE",
                        "chain_id": chain_id,
                        "old_instance_ids": sorted({o[0] for o in near}),
                        "new_instance_id": nid,
                        "new_instance_ids": [nid],
                        "classification": "MERGE_CANDIDATE",
                        "confidence": sum(o[1] for o in near) / len(near),
                        "label_authority": "AUTO",
                        "review_state": "AUTO",
                        "old_snapshot_sha256": old_src.sha256,
                        "new_snapshot_sha256": new_src.sha256,
                        "rationale": [
                            "multiple plausible predecessors",
                            f"near_count={len(near)}",
                        ],
                        "score_components": {
                            "predecessors": [
                                {"id": o[0], "confidence": o[1], "class": o[2]}
                                for o in near
                            ]
                        },
                    }
                )

    out.sort(key=lambda x: x["candidate_id"])
    return out


def export_candidates_jsonl(cands: list[dict[str, Any]], path: Path) -> bytes:
    lines = [json.dumps(c, sort_keys=True, ensure_ascii=False) for c in cands]
    raw = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    atomic_write_text(path, raw.decode("utf-8"))
    return raw
