"""Unit tests for alignment guards."""

from __future__ import annotations

from normshift.align.aligner import align_requirements
from normshift.model.types import Modality, Polarity, Requirement


def _req(rid: str, text: str, action: str, idx: int) -> Requirement:
    return Requirement(
        requirement_id=rid,
        document_sha256="b" * 64,
        document_version="1",
        section_path="Routing",
        source_locator=f"id:{rid}",
        original_text=text,
        normalized_text=text,
        modality=Modality.MUST,
        polarity=Polarity.AFFIRMATIVE,
        actor="Implementers",
        action=action,
        condition=None,
        exception=None,
        confidence=0.9,
        extractor_version="0.1.0",
        fingerprint=rid,
        structural_index=idx,
    )


def test_similar_requirements_not_cross_matched() -> None:
    a = _req(
        "a",
        "Implementers MUST reject unknown critical extensions.",
        "reject unknown critical extensions",
        0,
    )
    b = _req(
        "b",
        "Implementers MUST accept unknown non-critical extensions.",
        "accept unknown non-critical extensions",
        1,
    )
    a2 = a.model_copy(update={"requirement_id": "a2", "fingerprint": "a2"})
    b2 = b.model_copy(update={"requirement_id": "b2", "fingerprint": "b2"})
    pairs = align_requirements([a, b], [a2, b2])
    matched = [(p.old.requirement_id, p.new.requirement_id) for p in pairs if p.old and p.new]
    # Prefer identity-like matches, not a->b2
    assert ("a", "a2") in matched
    assert ("b", "b2") in matched
    assert ("a", "b2") not in matched
    assert ("b", "a2") not in matched
