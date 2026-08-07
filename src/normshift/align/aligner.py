"""Multi-signal cross-version requirement alignment."""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from normshift.model.types import AlignmentScore, Requirement
from normshift.normalize.html_normalize import editorial_normalize, strip_heading_number


@dataclass
class AlignmentPair:
    old: Requirement | None
    new: Requirement | None
    score: AlignmentScore | None


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _round4(x: float) -> float:
    return round(float(x), 4)


def _section_core(path: str) -> str:
    parts = [strip_heading_number(p.strip()) for p in path.split(">")]
    return " > ".join(p.lower() for p in parts if p)


def score_pair(old: Requirement, new: Requirement) -> AlignmentScore:
    """Compute explicit multi-signal alignment score components."""
    text_sim = fuzz.token_set_ratio(old.normalized_text, new.normalized_text) / 100.0
    # Also compare editorial cores for formatting-only drift.
    edit_old = editorial_normalize(old.normalized_text)
    edit_new = editorial_normalize(new.normalized_text)
    editorial_sim = fuzz.ratio(edit_old, edit_new) / 100.0
    text_similarity = max(text_sim, editorial_sim * 0.98)

    if old.modality == new.modality:
        modality_match = 1.0
    elif old.polarity == new.polarity:
        modality_match = 0.4
    else:
        modality_match = 0.0

    sec_old = _section_core(old.section_path)
    sec_new = _section_core(new.section_path)
    if sec_old == sec_new:
        section_similarity = 1.0
    else:
        section_similarity = fuzz.token_set_ratio(sec_old, sec_new) / 100.0

    token_similarity = fuzz.token_sort_ratio(old.normalized_text, new.normalized_text) / 100.0

    aa_old = f"{old.actor or ''} {old.action or ''}".strip()
    aa_new = f"{new.actor or ''} {new.action or ''}".strip()
    if aa_old and aa_new:
        actor_action_similarity = fuzz.token_set_ratio(aa_old, aa_new) / 100.0
    elif not aa_old and not aa_new:
        actor_action_similarity = 0.5
    else:
        actor_action_similarity = 0.2

    # Structural proximity: inverse normalized index distance.
    dist = abs(old.structural_index - new.structural_index)
    structural_proximity = _clamp01(1.0 - (dist / 20.0))

    # Weighted combination — text and actor/action dominate for identity.
    combined = (
        0.40 * text_similarity
        + 0.15 * modality_match
        + 0.10 * section_similarity
        + 0.15 * token_similarity
        + 0.15 * actor_action_similarity
        + 0.05 * structural_proximity
    )

    # Fingerprint exact match boosts heavily.
    if old.fingerprint == new.fingerprint:
        combined = max(combined, 0.99)

    components = {
        "text_similarity": _round4(text_similarity),
        "modality_match": _round4(modality_match),
        "section_similarity": _round4(section_similarity),
        "token_similarity": _round4(token_similarity),
        "actor_action_similarity": _round4(actor_action_similarity),
        "structural_proximity": _round4(structural_proximity),
        "editorial_similarity": _round4(editorial_sim),
    }

    return AlignmentScore(
        text_similarity=_round4(text_similarity),
        modality_match=_round4(modality_match),
        section_similarity=_round4(section_similarity),
        token_similarity=_round4(token_similarity),
        actor_action_similarity=_round4(actor_action_similarity),
        structural_proximity=_round4(structural_proximity),
        combined=_round4(combined),
        components=components,
    )


# Minimum combined score to accept a match. High enough to avoid cross-matching
# highly similar but distinct requirements.
MATCH_THRESHOLD = 0.62
# Ambiguous margin: if top two candidates are too close, leave unmatched / ambiguous.
AMBIGUITY_MARGIN = 0.05


def align_requirements(
    old_reqs: list[Requirement],
    new_reqs: list[Requirement],
) -> list[AlignmentPair]:
    """Greedy multi-signal alignment with ambiguity guard.

    Deterministic: candidates scored for all pairs, sorted by combined desc,
    then old_id, new_id as tie-breakers.
    """
    if not old_reqs and not new_reqs:
        return []

    scored: list[tuple[float, str, str, Requirement, Requirement, AlignmentScore]] = []
    for o in old_reqs:
        for n in new_reqs:
            s = score_pair(o, n)
            scored.append((s.combined, o.requirement_id, n.requirement_id, o, n, s))

    # Sort: highest score first; stable tie-breakers for determinism.
    scored.sort(key=lambda t: (-t[0], t[1], t[2]))

    # Precompute per-old top-2 for ambiguity detection.
    best_for_old: dict[str, list[tuple[float, str]]] = {o.requirement_id: [] for o in old_reqs}
    for combined, oid, nid, _o, _n, _s in scored:
        best_for_old[oid].append((combined, nid))

    matched_old: set[str] = set()
    matched_new: set[str] = set()
    pairs: list[AlignmentPair] = []

    for combined, oid, nid, o, n, s in scored:
        if oid in matched_old or nid in matched_new:
            continue
        if combined < MATCH_THRESHOLD:
            continue

        # Ambiguity: two strong new candidates for same old → do not force match.
        tops = best_for_old.get(oid, [])
        strong = [t for t in tops if t[0] >= MATCH_THRESHOLD]
        if len(strong) >= 2 and (strong[0][0] - strong[1][0]) < AMBIGUITY_MARGIN:
            # Only skip if the second involves a different new id still free.
            contenders = [nid2 for sc, nid2 in strong[:3] if sc >= MATCH_THRESHOLD]
            free_contenders = [c for c in contenders if c not in matched_new]
            if len(free_contenders) >= 2 and strong[0][0] - strong[1][0] < AMBIGUITY_MARGIN:
                continue

        # Additional guard: high token similarity but clearly different actions
        # with identical modality often means distinct similar requirements.
        if (
            s.text_similarity >= 0.85
            and s.actor_action_similarity < 0.75
            and o.action
            and n.action
            and editorial_normalize(o.action) != editorial_normalize(n.action)
            and o.modality == n.modality
            and combined < 0.88
        ):
            continue

        matched_old.add(oid)
        matched_new.add(nid)
        pairs.append(AlignmentPair(old=o, new=n, score=s))

    # Unmatched olds → removals
    for o in sorted(old_reqs, key=lambda r: (r.structural_index, r.requirement_id)):
        if o.requirement_id not in matched_old:
            pairs.append(AlignmentPair(old=o, new=None, score=None))

    # Unmatched news → additions
    for n in sorted(new_reqs, key=lambda r: (r.structural_index, r.requirement_id)):
        if n.requirement_id not in matched_new:
            pairs.append(AlignmentPair(old=None, new=n, score=None))

    # Deterministic pair order
    def pair_key(p: AlignmentPair) -> tuple[int, str, str]:
        oi = p.old.structural_index if p.old else 10_000
        ni = p.new.structural_index if p.new else 10_000
        oid = p.old.requirement_id if p.old else ""
        nid = p.new.requirement_id if p.new else ""
        return (min(oi, ni), oid, nid)

    pairs.sort(key=pair_key)
    return pairs
