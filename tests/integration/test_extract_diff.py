"""Integration tests for extract + diff pipeline."""

from __future__ import annotations

from pathlib import Path

from normshift.extract.extractor import extract_requirements
from normshift.model.types import ChangeClassification, ProfileName
from normshift.pipeline import run_diff

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "synthetic"


def test_extract_spec_v1_has_requirements() -> None:
    doc = extract_requirements(FIX / "spec-v1.html", ProfileName.RFC2119)
    assert len(doc.requirements) >= 5
    modalities = {r.modality.value for r in doc.requirements}
    assert "MUST" in modalities


def test_codeblocks_extract_nothing() -> None:
    doc = extract_requirements(FIX / "case10_codeblocks.html", ProfileName.RFC2119)
    assert doc.requirements == []


def test_mustard_extract_nothing() -> None:
    doc = extract_requirements(FIX / "case11_mustard.html", ProfileName.RFC2119)
    assert doc.requirements == []


def test_not_required_extract_nothing() -> None:
    doc = extract_requirements(FIX / "case12_not_required.html", ProfileName.RFC2119)
    assert doc.requirements == []


def test_whatwg_lowercase_extracts() -> None:
    doc = extract_requirements(FIX / "case13_whatwg_lower.html", ProfileName.WHATWG)
    assert len(doc.requirements) == 3


def test_strengthen_diff() -> None:
    report = run_diff(
        FIX / "case01_strengthen_old.html",
        FIX / "case01_strengthen_new.html",
        profile=ProfileName.RFC2119,
    )
    classes = {c.classification for c in report.changes}
    assert ChangeClassification.STRENGTHENED in classes


def test_relocation_is_moved_not_remove_add() -> None:
    report = run_diff(
        FIX / "case15_relocation_old.html",
        FIX / "case15_relocation_new.html",
        profile=ProfileName.RFC2119,
    )
    classes = {c.classification for c in report.changes}
    assert ChangeClassification.MOVED in classes
    assert ChangeClassification.ADDED not in classes
    assert ChangeClassification.REMOVED not in classes
