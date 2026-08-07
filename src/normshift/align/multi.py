"""Multiplicity-aware alignment: 1-1 primary, then strict split/merge."""

from __future__ import annotations

from dataclasses import dataclass, field

from normshift.align.aligner import AlignmentPair, align_requirements, score_pair
from normshift.model.types import Requirement
from normshift.normalize.html_normalize import editorial_normalize

# Secondary links for split/merge.
SPLIT_SECONDARY = 0.60
MERGE_SECONDARY = 0.60


@dataclass
class MultiAlignment:
    """Primary 1-1 pairs plus optional split/merge secondary links."""

    primary: list[AlignmentPair] = field(default_factory=list)
    # old_id -> list of (new_req, score) including all children of a split
    splits: dict[str, list[tuple[Requirement, float]]] = field(default_factory=dict)
    # new_id -> list of (old_req, score) parents of a merge
    merges: dict[str, list[tuple[Requirement, float]]] = field(default_factory=dict)
    ambiguity: list[dict[str, object]] = field(default_factory=list)


def _action_core(req: Requirement) -> str:
    base = req.action or req.normalized_text
    return editorial_normalize(base)


def align_with_multiplicity(
    old_reqs: list[Requirement],
    new_reqs: list[Requirement],
) -> MultiAlignment:
    """Greedy 1-1 first; attach split/merge only under strict guards."""
    primary = align_requirements(old_reqs, new_reqs)
    result = MultiAlignment(primary=primary)

    matched_old = {p.old.requirement_id for p in primary if p.old and p.new}
    matched_new = {p.new.requirement_id for p in primary if p.old and p.new}
    primary_new_for_old: dict[str, Requirement] = {
        p.old.requirement_id: p.new for p in primary if p.old and p.new
    }
    primary_score_for_old: dict[str, float] = {
        p.old.requirement_id: (p.score.combined if p.score else 0.0)
        for p in primary
        if p.old and p.new
    }

    # Precompute all pair scores
    pair_score: dict[tuple[str, str], float] = {}
    for o in old_reqs:
        for n in new_reqs:
            pair_score[(o.requirement_id, n.requirement_id)] = score_pair(o, n).combined

    # --- SPLIT detection (strict) ---
    # Case A: one old matched to primary new, plus additional *unmatched* news that
    # score highly with this old and not better with another unmatched-capable old.
    # Case B: one old unmatched, 2+ unmatched news score highly with it.
    for o in old_reqs:
        scores_to_new: list[tuple[Requirement, float]] = []
        for n in new_reqs:
            sc = pair_score[(o.requirement_id, n.requirement_id)]
            if sc >= SPLIT_SECONDARY:
                scores_to_new.append((n, sc))
        scores_to_new.sort(key=lambda t: (-t[1], t[0].requirement_id))

        if len(scores_to_new) < 2:
            continue

        # Prefer news for which this old is the best old partner.
        exclusive: list[tuple[Requirement, float]] = []
        for n, sc in scores_to_new:
            best_old_score = max(
                pair_score[(oo.requirement_id, n.requirement_id)] for oo in old_reqs
            )
            # Allow small epsilon
            if sc >= best_old_score - 0.02:
                exclusive.append((n, sc))

        if len(exclusive) < 2:
            continue

        # Require action cores to differ among children (not near-duplicates)
        cores = [_action_core(n) for n, _ in exclusive]
        if len(set(cores)) < 2:
            continue

        # If strong exclusive 1-1 and second candidate is far weaker, not a split
        if o.requirement_id in primary_score_for_old:
            top = exclusive[0][1]
            second = exclusive[1][1]
            # Strong unique primary: top much higher and top is the primary match
            primary_new = primary_new_for_old[o.requirement_id]
            if (
                exclusive[0][0].requirement_id == primary_new.requirement_id
                and top - second > 0.12
                and top >= 0.85
            ):
                continue

        # For matched olds: require at least one secondary unmatched new
        if o.requirement_id in matched_old:
            secondaries = [
                (n, sc)
                for n, sc in exclusive
                if n.requirement_id not in matched_new
                or n.requirement_id == primary_new_for_old[o.requirement_id].requirement_id
            ]
            unmatched_extra = [x for x in secondaries if x[0].requirement_id not in matched_new]
            if not unmatched_extra:
                continue
            # Build child list: primary + extras
            children: list[tuple[Requirement, float]] = []
            pnew = primary_new_for_old[o.requirement_id]
            children.append((pnew, primary_score_for_old[o.requirement_id]))
            for n, sc in exclusive:
                if n.requirement_id == pnew.requirement_id:
                    continue
                if n.requirement_id in matched_new:
                    continue
                children.append((n, sc))
            if len(children) >= 2:
                result.splits[o.requirement_id] = children
        else:
            # Unmatched old with 2+ exclusive news (unmatched)
            children = [
                (n, sc) for n, sc in exclusive if n.requirement_id not in matched_new
            ]
            if len(children) >= 2:
                result.splits[o.requirement_id] = children

    # --- MERGE detection (strict) ---
    for n in new_reqs:
        scores_to_old: list[tuple[Requirement, float]] = []
        for o in old_reqs:
            sc = pair_score[(o.requirement_id, n.requirement_id)]
            if sc >= MERGE_SECONDARY:
                scores_to_old.append((o, sc))
        scores_to_old.sort(key=lambda t: (-t[1], t[0].requirement_id))
        if len(scores_to_old) < 2:
            continue

        exclusive_o: list[tuple[Requirement, float]] = []
        for o, sc in scores_to_old:
            best_new = max(pair_score[(o.requirement_id, nn.requirement_id)] for nn in new_reqs)
            if sc >= best_new - 0.02:
                exclusive_o.append((o, sc))
        if len(exclusive_o) < 2:
            continue

        cores = [_action_core(o) for o, _ in exclusive_o]
        if len(set(cores)) < 2:
            continue

        # Prefer merges where scores are close when new already has a primary.
        if n.requirement_id in matched_new and exclusive_o[0][1] - exclusive_o[1][1] > 0.15:
            continue
        result.merges[n.requirement_id] = exclusive_o

        if exclusive_o[0][1] - exclusive_o[1][1] < 0.04:
            result.ambiguity.append(
                {
                    "kind": "competing_merge_candidates",
                    "new": n.requirement_id,
                    "olds": [o.requirement_id for o, _ in exclusive_o[:3]],
                    "scores": [sc for _, sc in exclusive_o[:3]],
                }
            )

    return result
