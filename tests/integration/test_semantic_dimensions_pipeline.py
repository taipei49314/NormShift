"""Integration coverage against unchanged production M0 diff output."""

from __future__ import annotations

import hashlib
from pathlib import Path

from normshift.model.types import ChangeClassification, ProfileName
from normshift.pipeline import run_diff
from normshift.semantic_dimensions import (
    StructuralForm,
    bind_verified_report_file,
    build_semantic_dimensions,
    canonical_change_sha256,
    create_full_verification_receipt,
    full_verification_receipt_json_bytes,
    semantic_dimensions_json_bytes,
    verify_semantic_dimensions,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "synthetic"


def test_relocation_report_can_be_described_without_changing_primary_m0_event(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "report.json"
    report = run_diff(
        FIXTURES / "case15_relocation_old.html",
        FIXTURES / "case15_relocation_new.html",
        profile=ProfileName.RFC2119,
        source_root=ROOT,
        json_out=report_path,
    )
    primary = next(
        change for change in report.changes if change.classification is ChangeClassification.MOVED
    )
    primary_bytes = primary.model_dump_json()
    receipt = create_full_verification_receipt(report_path, source_root=ROOT)
    receipt_bytes = full_verification_receipt_json_bytes(receipt)
    authority = bind_verified_report_file(
        report_path,
        source_root=ROOT,
        receipt_bytes=receipt_bytes,
        expected_report_file_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        expected_receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
    )

    dimensions = build_semantic_dimensions(
        authority=authority,
        primary_change_id=primary.change_id,
    )

    assert dimensions.change.structural_form is StructuralForm.MOVE_ONLY
    assert dimensions.change.evidence.primary_classification is ChangeClassification.MOVED
    assert dimensions.change.evidence.primary_change_sha256 == canonical_change_sha256(primary)
    assert primary.model_dump_json() == primary_bytes
    verify_semantic_dimensions(
        dimensions,
        authority=authority,
        primary_change_id=primary.change_id,
    )
    assert semantic_dimensions_json_bytes(dimensions).endswith(b"\n")
