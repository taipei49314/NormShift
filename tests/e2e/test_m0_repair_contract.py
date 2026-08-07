"""M0 trust-chain repair contract tests (external audit findings)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from normshift.cli import app
from normshift.evidence.hashing import integrity_payload_hash
from normshift.extract.extractor import extract_requirements
from normshift.measure.scoring import score_classification
from normshift.model.types import ProfileName
from normshift.pipeline import run_diff
from normshift.source import load_immutable_source
from normshift.verify.verifier import verify_report_file

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "synthetic"
runner = CliRunner()


def _fresh_report(tmp_path: Path) -> Path:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    shutil.copy(FIX / "spec-v1.html", old)
    shutil.copy(FIX / "spec-v2.html", new)
    out = tmp_path / "report.json"
    run_diff(
        old, new, profile=ProfileName.RFC2119, json_out=out, source_root=tmp_path
    )
    return out


def test_verify_fails_when_old_source_changes(tmp_path: Path) -> None:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    shutil.copy(FIX / "spec-v1.html", old)
    shutil.copy(FIX / "spec-v2.html", new)
    report = tmp_path / "r.json"
    run_diff(
        old, new, profile=ProfileName.RFC2119, json_out=report, source_root=tmp_path
    )
    assert verify_report_file(report, source_root=tmp_path).ok
    old.write_text(old.read_text(encoding="utf-8") + "\n<!-- mutated -->\n", encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert r.errors


def test_verify_fails_when_new_source_missing(tmp_path: Path) -> None:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    shutil.copy(FIX / "spec-v1.html", old)
    shutil.copy(FIX / "spec-v2.html", new)
    report = tmp_path / "r.json"
    run_diff(
        old, new, profile=ProfileName.RFC2119, json_out=report, source_root=tmp_path
    )
    new.unlink()
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert any("not found" in e.lower() or "Source" in e for e in r.errors)


def test_verify_fails_rehashed_dangling_requirement_reference(tmp_path: Path) -> None:
    report = _fresh_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    paired = next(
        c
        for c in data["changes"]
        if c.get("old_requirement_id") and c.get("new_requirement_id")
    )
    paired["old_requirement_id"] = "deadbeefdeadbeef"
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    from normshift.evidence.hashing import canonical_json_bytes

    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert r.errors


def test_verify_fails_rehashed_wrong_summary(tmp_path: Path) -> None:
    report = _fresh_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["summary"]["change_count"] = 999
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    from normshift.evidence.hashing import canonical_json_bytes

    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert any("summary" in e.lower() for e in r.errors)


def test_verify_recomputes_evidence_hashes(tmp_path: Path) -> None:
    report = _fresh_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["changes"][0]["evidence_hashes"] = ["0" * 64]
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    from normshift.evidence.hashing import canonical_json_bytes

    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    # Replay or evidence integrity must reject the forged hashes
    assert any(
        "evidence" in e.lower() or "changes do not match" in e.lower() or "replay" in e.lower()
        for e in r.errors
    )


def test_diff_rejects_output_equal_old_source(tmp_path: Path) -> None:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    shutil.copy(FIX / "spec-v1.html", old)
    shutil.copy(FIX / "spec-v2.html", new)
    r = runner.invoke(
        app,
        ["diff", str(old), str(new), "--json", str(old)],
    )
    assert r.exit_code != 0
    assert old.read_bytes().startswith(b"<!DOCTYPE") or b"<html" in old.read_bytes().lower()


def test_extract_rejects_output_equal_source(tmp_path: Path) -> None:
    src = tmp_path / "src.html"
    shutil.copy(FIX / "spec-v1.html", src)
    before = src.read_bytes()
    r = runner.invoke(app, ["extract", str(src), "--out", str(src)])
    assert r.exit_code != 0
    assert src.read_bytes() == before


def test_lineage_rejects_output_equal_any_input(tmp_path: Path) -> None:
    v1 = tmp_path / "v1.html"
    v2 = tmp_path / "v2.html"
    shutil.copy(ROOT / "fixtures" / "lineage" / "v1.html", v1)
    shutil.copy(ROOT / "fixtures" / "lineage" / "v2.html", v2)
    before = v1.read_bytes()
    r = runner.invoke(
        app,
        ["lineage", "graph", str(v1), str(v2), "--json", str(v1)],
    )
    assert r.exit_code != 0
    assert v1.read_bytes() == before


def test_measure_rejects_output_equal_ground_truth(tmp_path: Path) -> None:
    suite = tmp_path / "suite.jsonl"
    suite.write_text(
        json.dumps(
            {
                "id": "x",
                "profile": "rfc2119",
                "old": str(FIX / "case01_strengthen_old.html"),
                "new": str(FIX / "case01_strengthen_new.html"),
                "expected_classifications": ["STRENGTHENED"],
                "allow_extra": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    before = suite.read_text(encoding="utf-8")
    r = runner.invoke(
        app,
        ["measure", "--ground-truth", str(suite), "--out", str(suite)],
    )
    assert r.exit_code != 0
    assert suite.read_text(encoding="utf-8") == before


def test_diff_rejects_json_markdown_same_path(tmp_path: Path) -> None:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    out = tmp_path / "same.out"
    shutil.copy(FIX / "spec-v1.html", old)
    shutil.copy(FIX / "spec-v2.html", new)
    r = runner.invoke(
        app,
        [
            "diff",
            str(old),
            str(new),
            "--json",
            str(out),
            "--markdown",
            str(out),
        ],
    )
    assert r.exit_code != 0


def test_failed_second_write_preserves_preexisting_json(tmp_path: Path) -> None:
    """Pre-existing JSON must not be deleted if a later write fails.

    Parent-as-file is rejected in non-mutating preflight (PathSafetyError)
    before any staging; original content is therefore always preserved.
    """
    from normshift.io_safety import PathSafetyError, write_transaction

    preexisting = tmp_path / "out.json"
    preexisting.write_text("ORIGINAL_USER_CONTENT", encoding="utf-8")
    bad_dir = tmp_path / "missing_parent_as_file"
    bad_dir.write_text("block", encoding="utf-8")
    bad_path = bad_dir / "child.md"  # parent is a file → preflight rejects
    with pytest.raises((OSError, PathSafetyError)):
        write_transaction(
            {
                preexisting: b'{"ok": true}\n',
                bad_path: b"# md\n",
            }
        )
    assert preexisting.read_text(encoding="utf-8") == "ORIGINAL_USER_CONTENT"


def test_classification_metrics_count_unexpected_labels_as_fp() -> None:
    m = score_classification(
        ["STRENGTHENED", "ADDED", "REMOVED", "POLARITY_FLIP"],
        ["STRENGTHENED"],
        allow_extra=True,
    )
    assert m.true_positives == 1
    assert m.false_positives == 3
    assert m.false_negatives == 0
    assert m.precision == 0.25
    assert m.recall == 1.0
    assert m.f1 == 0.4
    assert m.case_passed is True  # permissive gate
    assert m.exact_pass is False
    assert m.permissive_pass is True


def test_security_considerations_can_be_normative(tmp_path: Path) -> None:
    p = tmp_path / "sec.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <h2>Security Considerations</h2>
        <p>Clients MUST validate certificates.</p>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert any("validate certificates" in r.normalized_text for r in doc.requirements)


def test_normative_appendix_is_not_blanket_skipped(tmp_path: Path) -> None:
    p = tmp_path / "app.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <h2>Appendix A — Normative Requirements</h2>
        <p data-normative="true">Clients MUST validate certificates.</p>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert any("validate certificates" in r.normalized_text for r in doc.requirements)


def test_inline_code_identifier_preserved_but_code_modal_protected(tmp_path: Path) -> None:
    p1 = tmp_path / "code1.html"
    p1.write_text(
        """<!DOCTYPE html><html><body>
        <p>Clients MUST send the <code>Authorization</code> header.</p>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p1, ProfileName.RFC2119)
    assert doc.requirements
    assert "Authorization" in doc.requirements[0].original_text
    assert "Authorization" in (doc.requirements[0].action or "")

    p2 = tmp_path / "code2.html"
    p2.write_text(
        """<!DOCTYPE html><html><body>
        <p>The word <code>MUST</code> appears only inside code.</p>
        </body></html>""",
        encoding="utf-8",
    )
    doc2 = extract_requirements(p2, ProfileName.RFC2119)
    assert doc2.requirements == []


def test_actor_is_never_taken_from_post_modal_object(tmp_path: Path) -> None:
    p = tmp_path / "actor.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <p>A proxy MUST forward messages to clients.</p>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert doc.requirements
    assert doc.requirements[0].actor is None or doc.requirements[0].actor.lower() != "clients"
    # Prefer proxy when recognized
    if doc.requirements[0].actor:
        assert "proxy" in doc.requirements[0].actor.lower()


def test_historical_blockquote_not_current_requirement(tmp_path: Path) -> None:
    p = tmp_path / "quote.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <blockquote>
          <p>The previous specification said clients MUST retry.</p>
        </blockquote>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert doc.requirements == []


def test_pipeline_uses_single_source_snapshot(tmp_path: Path) -> None:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    shutil.copy(FIX / "case01_strengthen_old.html", old)
    shutil.copy(FIX / "case01_strengthen_new.html", new)
    old_src = load_immutable_source(old)
    new_src = load_immutable_source(new)
    # Mutate filesystem after snapshot
    old.write_text(old.read_text(encoding="utf-8") + "\n<p>EXTRA MUST die.</p>\n", encoding="utf-8")
    report = run_diff(
        old,
        new,
        profile=ProfileName.RFC2119,
        old_source=old_src,
        new_source=new_src,
        json_out=tmp_path / "r.json",
    )
    # Snapshot hash must still match original snapshot, not mutated file
    assert report.old_document.sha256 == old_src.sha256
    assert report.old_document.sha256 != __import__("hashlib").sha256(old.read_bytes()).hexdigest()
    # Requirements tied to snapshot hash
    assert all(r.document_sha256 == old_src.sha256 for r in report.old_requirements)
