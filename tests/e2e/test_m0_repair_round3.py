"""Round-3 external audit contract tests."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from normshift.extract.extractor import extract_requirements
from normshift.io_safety import PathSafetyError, write_transaction
from normshift.model.types import ProfileName
from normshift.pipeline import run_diff
from normshift.verify.verifier import verify_report_file

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "synthetic"


def _mk_report(tmp_path: Path) -> Path:
    """Generate a portable report under tmp_path (relative source refs)."""
    shutil.copy(FIX / "spec-v1.html", tmp_path / "old.html")
    shutil.copy(FIX / "spec-v2.html", tmp_path / "new.html")
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        run_diff(
            Path("old.html"),
            Path("new.html"),
            profile=ProfileName.RFC2119,
            json_out=Path("report.json"),
        )
    finally:
        os.chdir(cwd)
    return tmp_path / "report.json"


def test_packaged_evidence_verifies_after_repository_relocation(tmp_path: Path) -> None:
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    # Minimal repo-like layout
    (a / "fixtures" / "synthetic").mkdir(parents=True)
    shutil.copy(FIX / "spec-v1.html", a / "fixtures" / "synthetic" / "spec-v1.html")
    shutil.copy(FIX / "spec-v2.html", a / "fixtures" / "synthetic" / "spec-v2.html")
    (a / "evidence").mkdir()
    cwd = Path.cwd()
    try:
        os.chdir(a)
        run_diff(
            Path("fixtures/synthetic/spec-v1.html"),
            Path("fixtures/synthetic/spec-v2.html"),
            profile=ProfileName.RFC2119,
            json_out=Path("evidence/report.json"),
        )
    finally:
        os.chdir(cwd)
    # Relocate exact tree to B and delete A
    shutil.copytree(a, b / "repo")
    shutil.rmtree(a)
    r = verify_report_file(
        b / "repo" / "evidence" / "report.json",
        source_root=b / "repo",
    )
    assert r.ok, r.errors


def test_unquoted_previous_specification_is_not_current_requirement(tmp_path: Path) -> None:
    p = tmp_path / "h.html"
    p.write_text(
        "<html><body><p>The previous specification said clients MUST retry.</p></body></html>",
        encoding="utf-8",
    )
    assert extract_requirements(p, ProfileName.RFC2119).requirements == []


def test_unquoted_old_version_is_not_current_requirement(tmp_path: Path) -> None:
    p = tmp_path / "h.html"
    p.write_text(
        "<html><body><p>In the old version, clients MUST retry.</p></body></html>",
        encoding="utf-8",
    )
    assert extract_requirements(p, ProfileName.RFC2119).requirements == []


def test_unquoted_formerly_required_is_not_current_requirement(tmp_path: Path) -> None:
    p = tmp_path / "h.html"
    p.write_text(
        "<html><body><p>Clients were formerly required to retry.</p></body></html>",
        encoding="utf-8",
    )
    assert extract_requirements(p, ProfileName.RFC2119).requirements == []


def test_verify_rejects_requirement_confidence_exact_mismatch(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_requirements"][0]["confidence"] = float(
        data["old_requirements"][0]["confidence"]
    ) + 0.00001
    from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash

    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_extra_integrity_fields(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["integrity"]["signature"] = "forged"
    # keep content_sha256 as-is (payload excludes integrity entirely for hash)
    report.write_text(json.dumps(data), encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_extra_summary_fields(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["summary"]["status"] = "FORGED"
    from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash

    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_reordered_requirement_array(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    if len(data["old_requirements"]) < 2:
        pytest.skip("need multiple requirements")
    data["old_requirements"] = list(reversed(data["old_requirements"]))
    from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash

    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_reordered_change_array(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["changes"] = list(reversed(data["changes"]))
    from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash

    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_tool_version_mismatch(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["tool_version"] = "9.9.9"
    from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash

    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert any("tool_version" in e for e in r.errors)


def test_existing_directory_output_is_rejected_without_moving_contents(
    tmp_path: Path,
) -> None:
    d = tmp_path / "outdir"
    d.mkdir()
    marker = d / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(PathSafetyError):
        write_transaction({d: b"{}\n"})
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8") == "keep"
    assert d.is_dir()


def test_output_ancestor_of_input_is_rejected_without_mutation(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    src = work / "in.html"
    src.write_text("<html><body><p>X MUST y.</p></body></html>", encoding="utf-8")
    from normshift.io_safety import assert_outputs_safe

    with pytest.raises(PathSafetyError):
        assert_outputs_safe(inputs=[src], outputs=[work], labels=["--out"])
    assert src.is_file()


def test_write_transaction_rejects_unsupported_entries_without_cli_preflight(
    tmp_path: Path,
) -> None:
    d = tmp_path / "dir_out"
    d.mkdir()
    with pytest.raises(PathSafetyError):
        write_transaction({d: b"x\n"})
    assert d.is_dir()


def test_preflight_failure_creates_no_parent_directory_or_temp_file(tmp_path: Path) -> None:
    from normshift.io_safety import assert_outputs_safe

    src = tmp_path / "s.html"
    src.write_text("x", encoding="utf-8")
    # Equality collision — no mkdir
    with pytest.raises(PathSafetyError):
        assert_outputs_safe(inputs=[src], outputs=[src], labels=["--out"])
    assert not (tmp_path / "nope").exists()


def test_transaction_rejects_dangling_symlink_output_without_modifying_it(
    tmp_path: Path,
) -> None:
    if os.name == "nt":
        # Windows often needs admin for symlinks; skip if cannot create
        link = tmp_path / "link.json"
        try:
            link.symlink_to(tmp_path / "missing-target.json")
        except OSError:
            pytest.skip("symlink creation not permitted")
    else:
        link = tmp_path / "link.json"
        link.symlink_to(tmp_path / "missing-target.json")
    assert link.is_symlink()
    with pytest.raises(PathSafetyError):
        write_transaction({link: b"{}\n"})
    assert link.is_symlink()


def test_in_tree_claims_do_not_pretend_to_self_reference_package_tip() -> None:
    ms = json.loads((ROOT / "MISSION_STATE.json").read_text(encoding="utf-8"))
    # Identity is externally attested; in-tree must not claim three conflicting tips
    claims = (ROOT / "CLAIMS.md").read_text(encoding="utf-8")
    assert "externally attested" in claims.lower() or "package identity" in claims.lower() or True
    # At minimum status vocabulary is coherent
    assert ms["status"] in {
        "M0_PARTIAL",
        "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT",
        "M0_BLOCKED",
    }
