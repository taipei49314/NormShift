"""Classify aligned requirement pairs into change types."""

from __future__ import annotations

import hashlib
import re

from normshift.align.aligner import AlignmentPair
from normshift.evidence.hashing import evidence_hash
from normshift.model.types import (
    Change,
    ChangeClassification,
    Modality,
    Requirement,
)
from normshift.normalize.html_normalize import editorial_normalize, strip_heading_number

# Modality strength: higher = stronger obligation (affirmative path).
_STRENGTH: dict[Modality, int] = {
    Modality.MUST: 3,
    Modality.MUST_NOT: 3,
    Modality.SHOULD: 2,
    Modality.SHOULD_NOT: 2,
    Modality.MAY: 1,
}

_POLAR_PAIRS = {
    (Modality.MUST, Modality.MUST_NOT),
    (Modality.MUST_NOT, Modality.MUST),
    (Modality.SHOULD, Modality.SHOULD_NOT),
    (Modality.SHOULD_NOT, Modality.SHOULD),
}


def _section_core(path: str) -> str:
    parts = [strip_heading_number(p.strip()) for p in path.split(">")]
    return " > ".join(p.lower() for p in parts if p)


def _change_id(parts: list[str]) -> str:
    payload = "\x1f".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _modality_transition(old: Requirement | None, new: Requirement | None) -> str | None:
    if old and new:
        return f"{old.modality.value}->{new.modality.value}"
    if old and not new:
        return f"{old.modality.value}->∅"
    if new and not old:
        return f"∅->{new.modality.value}"
    return None


def _norm_field(val: str | None) -> str:
    return editorial_normalize(val) if val else ""


def classify_pair(pair: AlignmentPair) -> Change:
    old, new, score = pair.old, pair.new, pair.score
    reasons: list[str] = []

    if old is None and new is not None:
        return _make_change(
            old=None,
            new=new,
            classification=ChangeClassification.ADDED,
            confidence=0.95,
            reasons=["No aligned prior requirement; treated as addition."],
            score=None,
        )

    if old is not None and new is None:
        return _make_change(
            old=old,
            new=None,
            classification=ChangeClassification.REMOVED,
            confidence=0.95,
            reasons=["No aligned successor requirement; treated as removal."],
            score=None,
        )

    assert old is not None and new is not None

    # Polarity flip takes precedence over strength.
    polar_pair = (old.modality, new.modality) in _POLAR_PAIRS or (
        old.polarity != new.polarity and _core_action_similar(old, new)
    )
    body_supports_flip = _core_action_similar(old, new) or (
        score is not None
        and score.text_similarity >= 0.55
        and score.actor_action_similarity >= 0.5
    )
    if polar_pair and body_supports_flip:
        reasons.append(f"Polarity/modality flip: {old.modality.value} -> {new.modality.value}.")
        return _make_change(
            old=old,
            new=new,
            classification=ChangeClassification.POLARITY_FLIP,
            confidence=0.9,
            reasons=reasons,
            score=score,
        )

    same_editorial = editorial_normalize(old.normalized_text) == editorial_normalize(
        new.normalized_text
    )
    same_section = _section_core(old.section_path) == _section_core(new.section_path)
    same_modality = old.modality == new.modality
    same_fp = old.fingerprint == new.fingerprint

    old_cond, new_cond = _norm_field(old.condition), _norm_field(new.condition)
    old_exc, new_exc = _norm_field(old.exception), _norm_field(new.exception)

    # Exception / condition changes (when body otherwise aligned).
    body_similar = bool(score and score.text_similarity >= 0.7) or same_editorial or same_fp

    if body_similar and same_modality:
        if not old_exc and new_exc:
            reasons.append(f"Exception introduced: {new.exception!r}.")
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.EXCEPTION_ADDED,
                confidence=0.88,
                reasons=reasons,
                score=score,
            )
        if old_exc and not new_exc:
            reasons.append(f"Exception removed: {old.exception!r}.")
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.EXCEPTION_REMOVED,
                confidence=0.88,
                reasons=reasons,
                score=score,
            )
        if old_exc and new_exc and old_exc != new_exc:
            reasons.append("Exception text changed; insufficient specificity → AMBIGUOUS.")
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.AMBIGUOUS,
                confidence=0.55,
                reasons=reasons,
                score=score,
            )

        if not old_cond and new_cond:
            reasons.append(f"Condition introduced: {new.condition!r}.")
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.CONDITION_ADDED,
                confidence=0.88,
                reasons=reasons,
                score=score,
            )
        if old_cond and not new_cond:
            reasons.append(f"Condition removed: {old.condition!r}.")
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.CONDITION_REMOVED,
                confidence=0.88,
                reasons=reasons,
                score=score,
            )
        if old_cond and new_cond and old_cond != new_cond:
            reasons.append("Condition text changed; insufficient specificity → AMBIGUOUS.")
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.AMBIGUOUS,
                confidence=0.55,
                reasons=reasons,
                score=score,
            )

    # Strength transitions (same polarity family preferred).
    if not same_modality and old.polarity == new.polarity:
        so, sn = _STRENGTH[old.modality], _STRENGTH[new.modality]
        if sn > so:
            reasons.append(
                f"Obligation strengthened: {old.modality.value} -> {new.modality.value}."
            )
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.STRENGTHENED,
                confidence=0.92,
                reasons=reasons,
                score=score,
            )
        if sn < so:
            reasons.append(f"Obligation weakened: {old.modality.value} -> {new.modality.value}.")
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.WEAKENED,
                confidence=0.92,
                reasons=reasons,
                score=score,
            )

    # Cross-family strength (e.g., MUST_NOT vs SHOULD) without clear polarity pair.
    if not same_modality and old.polarity != new.polarity:
        reasons.append(
            "Modality and polarity both changed without clear flip pattern → AMBIGUOUS."
        )
        return _make_change(
            old=old,
            new=new,
            classification=ChangeClassification.AMBIGUOUS,
            confidence=0.5,
            reasons=reasons,
            score=score,
        )

    # Same modality path: unchanged / moved / editorial / ambiguous substantive.
    if same_modality:
        if same_fp or (
            same_editorial
            and _norm_field(old.actor) == _norm_field(new.actor)
            and _norm_field(old.action) == _norm_field(new.action)
            and old_cond == new_cond
            and old_exc == new_exc
        ):
            if not same_section:
                reasons.append(
                    "Semantically identical requirement relocated across sections → MOVED."
                )
                return _make_change(
                    old=old,
                    new=new,
                    classification=ChangeClassification.MOVED,
                    confidence=0.93,
                    reasons=reasons,
                    score=score,
                )
            if old.normalized_text == new.normalized_text and same_section:
                reasons.append("Identical normalized text, modality, and section → UNCHANGED.")
                return _make_change(
                    old=old,
                    new=new,
                    classification=ChangeClassification.UNCHANGED,
                    confidence=0.99,
                    reasons=reasons,
                    score=score,
                )
            # Editorial only (whitespace / punctuation / heading numbers).
            reasons.append(
                "Editorial differences only (whitespace/punctuation/formatting) → EDITORIAL."
            )
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.EDITORIAL,
                confidence=0.9,
                reasons=reasons,
                score=score,
            )

        # High similarity but not editorial-equal: ambiguous rather than forced.
        if score and score.combined >= 0.75:
            reasons.append(
                "Aligned with residual non-editorial text differences; "
                "insufficient evidence for a substantive class → AMBIGUOUS."
            )
            return _make_change(
                old=old,
                new=new,
                classification=ChangeClassification.AMBIGUOUS,
                confidence=0.55,
                reasons=reasons,
                score=score,
            )

    reasons.append("Insufficient evidence for a confident classification → AMBIGUOUS.")
    return _make_change(
        old=old,
        new=new,
        classification=ChangeClassification.AMBIGUOUS,
        confidence=0.45,
        reasons=reasons,
        score=score,
    )


def _core_action_similar(old: Requirement, new: Requirement) -> bool:
    a = _norm_field(old.action) or editorial_normalize(
        re.sub(
            r"\b(must\s+not|shall\s+not|should\s+not|must|shall|should|may|required)\b",
            " ",
            old.normalized_text,
            flags=re.IGNORECASE,
        )
    )
    b = _norm_field(new.action) or editorial_normalize(
        re.sub(
            r"\b(must\s+not|shall\s+not|should\s+not|must|shall|should|may|required)\b",
            " ",
            new.normalized_text,
            flags=re.IGNORECASE,
        )
    )
    if not a or not b:
        return False
    # Simple token overlap
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return False
    overlap = len(ta & tb) / max(len(ta | tb), 1)
    return overlap >= 0.5


def _make_change(
    *,
    old: Requirement | None,
    new: Requirement | None,
    classification: ChangeClassification,
    confidence: float,
    reasons: list[str],
    score: object,
) -> Change:
    from normshift.model.types import AlignmentScore

    oid = old.requirement_id if old else ""
    nid = new.requirement_id if new else ""
    old_txt = old.normalized_text if old else ""
    new_txt = new.normalized_text if new else ""
    cid = _change_id([classification.value, oid, nid, old_txt, new_txt])

    hashes: list[str] = []
    if old:
        hashes.append(evidence_hash("old_text", old.original_text))
        hashes.append(evidence_hash("old_locator", old.source_locator))
    if new:
        hashes.append(evidence_hash("new_text", new.original_text))
        hashes.append(evidence_hash("new_locator", new.source_locator))
    hashes.append(evidence_hash("classification", classification.value))
    hashes = sorted(set(hashes))

    align: AlignmentScore | None = score if isinstance(score, AlignmentScore) else None

    return Change(
        change_id=cid,
        old_requirement_id=old.requirement_id if old else None,
        new_requirement_id=new.requirement_id if new else None,
        classification=classification,
        confidence=round(confidence, 4),
        classification_reasons=reasons,
        old_source_locator=old.source_locator if old else None,
        new_source_locator=new.source_locator if new else None,
        old_text=old.original_text if old else None,
        new_text=new.original_text if new else None,
        modality_transition=_modality_transition(old, new),
        evidence_hashes=hashes,
        alignment_score=align,
        old_section_path=old.section_path if old else None,
        new_section_path=new.section_path if new else None,
    )


def classify_pairs(pairs: list[AlignmentPair]) -> list[Change]:
    changes = [classify_pair(p) for p in pairs]
    changes.sort(
        key=lambda c: (
            c.classification.value,
            c.old_requirement_id or "",
            c.new_requirement_id or "",
            c.change_id,
        )
    )
    return changes
