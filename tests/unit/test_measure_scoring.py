"""Unit tests for pure measurement scorers."""

from __future__ import annotations

from pathlib import Path

from normshift.evidence.hashing import canonical_json_bytes
from normshift.measure.runner import MeasureError, run_measure, write_metrics
from normshift.measure.scoring import (
    AlignmentGoldItem,
    AlignmentPrediction,
    ExtractionGoldItem,
    ExtractionPrediction,
    score_alignment,
    score_classification,
    score_extraction,
)


def test_extraction_perfect_and_empty() -> None:
    gold = [ExtractionGoldItem(contains="ack", modality="MUST")]
    pred = [ExtractionPrediction(text="MUST send ack", modality="MUST")]
    m = score_extraction(pred, gold)
    assert m.f1 == 1.0
    empty = score_extraction([], [])
    assert empty.f1 == 1.0
    leak = score_extraction([ExtractionPrediction("mustard", "MAY")], [])
    assert leak.f1 == 0.0


def test_alignment_prf() -> None:
    gold = [AlignmentGoldItem(old_contains="send", new_contains="send", aligned=True)]
    pred = [AlignmentPrediction(old_text="MUST send", new_text="MUST send x", aligned=True)]
    m = score_alignment(pred, gold)
    assert m.recall == 1.0


def test_classification_forbid() -> None:
    m = score_classification(
        ["STRENGTHENED", "ADDED"],
        ["STRENGTHENED"],
        allow_extra=True,
        forbid=["ADDED"],
    )
    assert m.case_passed is False


def test_classification_expected_subset() -> None:
    m = score_classification(
        ["STRENGTHENED", "UNCHANGED"],
        ["STRENGTHENED"],
        allow_extra=True,
    )
    assert m.case_passed is True
    assert m.recall == 1.0


def test_dual_run_identical_metrics(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    suite = root / "benchmark" / "measure_suite.jsonl"
    r1 = run_measure(suite)
    r2 = run_measure(suite)
    p1 = tmp_path / "m1.json"
    p2 = tmp_path / "m2.json"
    write_metrics(r1, p1)
    write_metrics(r2, p2)
    assert p1.read_bytes() == p2.read_bytes()
    assert r1.extraction["f1"] >= 0.0
    assert r2.alignment["f1"] >= 0.0
    assert "f1" in r1.classification
    # Canonical encoding stable
    assert canonical_json_bytes(r1.to_dict()) == canonical_json_bytes(r2.to_dict())


def test_measure_missing_ground_truth() -> None:
    try:
        run_measure(Path("does-not-exist-measure.jsonl"))
        raise AssertionError("expected MeasureError")
    except MeasureError:
        pass


def test_measure_empty_suite(tmp_path: Path) -> None:
    empty = tmp_path / "empty.jsonl"
    empty.write_text("\n", encoding="utf-8")
    try:
        run_measure(empty)
        raise AssertionError("expected MeasureError")
    except MeasureError:
        pass
