"""Unit tests for change classification."""

from __future__ import annotations

from normshift.align.aligner import AlignmentPair, score_pair
from normshift.classify.classifier import classify_pair
from normshift.model.types import ChangeClassification, Modality, Polarity, Requirement


def _req(
    rid: str,
    text: str,
    modality: Modality,
    *,
    section: str = "A",
    condition: str | None = None,
    exception: str | None = None,
    action: str | None = None,
    idx: int = 0,
) -> Requirement:
    pol = (
        Polarity.NEGATIVE
        if modality in (Modality.MUST_NOT, Modality.SHOULD_NOT)
        else Polarity.AFFIRMATIVE
    )
    return Requirement(
        requirement_id=rid,
        document_sha256="a" * 64,
        document_version="1",
        section_path=section,
        source_locator=f"id:{rid}",
        original_text=text,
        normalized_text=text,
        modality=modality,
        polarity=pol,
        actor="Implementers",
        action=action or text,
        condition=condition,
        exception=exception,
        confidence=0.9,
        extractor_version="0.1.0",
        fingerprint=rid,
        structural_index=idx,
    )


def test_strengthened() -> None:
    old = _req("o", "Implementers SHOULD send ack.", Modality.SHOULD, action="send ack")
    new = _req("n", "Implementers MUST send ack.", Modality.MUST, action="send ack")
    # Same fingerprint family for body-ish - use score
    pair = AlignmentPair(old=old, new=new, score=score_pair(old, new))
    ch = classify_pair(pair)
    assert ch.classification == ChangeClassification.STRENGTHENED


def test_weakened() -> None:
    old = _req("o", "Servers MUST retry.", Modality.MUST, action="retry")
    new = _req("n", "Servers SHOULD retry.", Modality.SHOULD, action="retry")
    pair = AlignmentPair(old=old, new=new, score=score_pair(old, new))
    assert classify_pair(pair).classification == ChangeClassification.WEAKENED


def test_polarity_flip() -> None:
    old = _req("o", "Clients MUST send notice.", Modality.MUST, action="send notice")
    new = _req(
        "n",
        "Clients MUST NOT send notice.",
        Modality.MUST_NOT,
        action="send notice",
    )
    pair = AlignmentPair(old=old, new=new, score=score_pair(old, new))
    assert classify_pair(pair).classification == ChangeClassification.POLARITY_FLIP


def test_exception_added() -> None:
    text_old = "User agents SHOULD cache keys."
    text_new = "User agents SHOULD cache keys unless private mode is active."
    old = _req("o", text_old, Modality.SHOULD, action="cache keys", exception=None)
    new = _req(
        "n",
        text_new,
        Modality.SHOULD,
        action="cache keys",
        exception="unless private mode is active",
    )
    # fingerprints differ; force high text sim via similar text
    pair = AlignmentPair(old=old, new=new, score=score_pair(old, new))
    assert classify_pair(pair).classification == ChangeClassification.EXCEPTION_ADDED


def test_moved() -> None:
    text = "User agents MUST open at most one control channel per origin."
    old = _req("o", text, Modality.MUST, section="Session", action="open channel")
    new = _req("n", text, Modality.MUST, section="Connection", action="open channel")
    # identical fingerprint if same semantic fields — set same fingerprint
    new = new.model_copy(update={"fingerprint": old.fingerprint})
    pair = AlignmentPair(old=old, new=new, score=score_pair(old, new))
    assert classify_pair(pair).classification == ChangeClassification.MOVED
