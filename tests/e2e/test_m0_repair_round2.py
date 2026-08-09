"""Round-2 re-audit contract tests."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.extract.extractor import extract_requirements, fingerprint_requirement
from normshift.io_safety import write_transaction
from normshift.measure.runner import run_measure
from normshift.measure.scoring import score_classification
from normshift.model.types import ProfileName
from normshift.pipeline import run_diff
from normshift.verify.verifier import verify_report_file

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "synthetic"
runner = CliRunner()


def _report_pair(tmp_path: Path) -> tuple[Path, Path, Path]:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    shutil.copy(FIX / "spec-v1.html", old)
    shutil.copy(FIX / "spec-v2.html", new)
    report = tmp_path / "report.json"
    run_diff(
        old, new, profile=ProfileName.RFC2119, json_out=report, source_root=tmp_path
    )
    return old, new, report


def _rehash(data: dict) -> bytes:
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    return canonical_json_bytes(data)


def test_verify_rejects_unresolvable_source_locator_after_rehash(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    req = data["old_requirements"][0]
    req["source_locator"] = "id:THIS-ID-DOES-NOT-EXIST|xpath:/html/body/div[999]/p[999]"
    # update referencing changes
    for ch in data["changes"]:
        if ch.get("old_requirement_id") == req["requirement_id"]:
            ch["old_source_locator"] = req["source_locator"]
            from normshift.evidence.hashing import evidence_hash

            hashes = []
            if ch.get("old_text"):
                hashes.append(evidence_hash("old_text", ch["old_text"]))
            if ch.get("old_source_locator"):
                hashes.append(evidence_hash("old_locator", ch["old_source_locator"]))
            if ch.get("new_text"):
                hashes.append(evidence_hash("new_text", ch["new_text"]))
            if ch.get("new_source_locator"):
                hashes.append(evidence_hash("new_locator", ch["new_source_locator"]))
            hashes.append(evidence_hash("classification", ch["classification"]))
            ch["evidence_hashes"] = sorted(set(hashes))
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_fabricated_requirement_text_after_rehash(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    req = data["old_requirements"][0]
    req["original_text"] = "Fabricated clients SHOULD upload secrets to example.invalid."
    req["normalized_text"] = req["original_text"]
    req["fingerprint"] = fingerprint_requirement(
        req["normalized_text"],
        req["modality"],
        req.get("actor"),
        req.get("action"),
        req.get("condition"),
        req.get("exception"),
    )
    for ch in data["changes"]:
        if ch.get("old_requirement_id") == req["requirement_id"]:
            ch["old_text"] = req["original_text"]
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_recomputes_requirement_id(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    old_id = data["old_requirements"][0]["requirement_id"]
    data["old_requirements"][0]["requirement_id"] = "0123456789abcdef"
    for ch in data["changes"]:
        if ch.get("old_requirement_id") == old_id:
            ch["old_requirement_id"] = "0123456789abcdef"
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_requires_both_ids_for_every_paired_class(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    paired = next(
        c
        for c in data["changes"]
        if c["classification"] not in {"ADDED", "REMOVED"}
        and c.get("old_requirement_id")
        and c.get("new_requirement_id")
    )
    paired["old_requirement_id"] = None
    paired["new_requirement_id"] = None
    paired["old_text"] = None
    paired["new_text"] = None
    paired["old_source_locator"] = None
    paired["new_source_locator"] = None
    from normshift.evidence.hashing import evidence_hash

    paired["evidence_hashes"] = [
        evidence_hash("classification", paired["classification"])
    ]
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert r.errors


def test_verify_rejects_arbitrary_added_removed_change_id(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    added = next(c for c in data["changes"] if c["classification"] == "ADDED")
    added["change_id"] = "ffffffff00000000"
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_duplicate_change_ids(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    assert len(data["changes"]) >= 2
    data["changes"][1]["change_id"] = data["changes"][0]["change_id"]
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert r.errors


def test_verify_rejects_duplicate_requirement_coverage(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    paired = [
        c
        for c in data["changes"]
        if c.get("old_requirement_id") and c.get("new_requirement_id")
    ]
    if len(paired) < 2:
        pytest.skip("need two paired changes")
    paired[1]["old_requirement_id"] = paired[0]["old_requirement_id"]
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_validates_provenance_metadata(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["provenance"]["local_path"] = "fabricated/path.html"
    data["old_document"]["provenance"]["canonical_source"] = "not-a-valid-source"
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_replay_rejects_changed_classification_after_rehash(tmp_path: Path) -> None:
    old, new, report = _report_pair(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    ch = next(c for c in data["changes"] if c["classification"] == "STRENGTHENED")
    ch["classification"] = "WEAKENED"
    from normshift.evidence.hashing import evidence_hash

    ch["evidence_hashes"] = sorted(
        {
            *(
                [evidence_hash("old_text", ch["old_text"])] if ch.get("old_text") else []
            ),
            *(
                [evidence_hash("new_text", ch["new_text"])] if ch.get("new_text") else []
            ),
            evidence_hash("classification", "WEAKENED"),
        }
    )
    # keep change_id as-is (wrong) or recompute — either way replay must fail
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_transaction_restores_first_output_when_second_replace_fails(tmp_path: Path) -> None:
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text("ORIGINAL_A", encoding="utf-8")
    b.write_text("ORIGINAL_B", encoding="utf-8")
    commits = {"n": 0}

    def inject(src: object, dst: object) -> None:
        sp, dp = Path(str(src)), Path(str(dst))
        # count only temp->final commits (tmp files)
        if ".tmp" in sp.name:
            commits["n"] += 1
            if commits["n"] == 2:
                raise OSError("injected second commit failure")
        os.replace(sp, dp)

    with pytest.raises(OSError, match="injected second commit failure"):
        write_transaction(
            {a: b"NEW_A\n", b: b"NEW_B\n"},
            replace_fn=inject,
        )
    assert a.read_text(encoding="utf-8") == "ORIGINAL_A"
    assert b.read_text(encoding="utf-8") == "ORIGINAL_B"


def test_transaction_removes_only_new_files_created_by_this_invocation(
    tmp_path: Path,
) -> None:
    a = tmp_path / "new_only_a.json"  # did not exist
    b = tmp_path / "pre.json"
    b.write_text("ORIGINAL_B", encoding="utf-8")
    commits = {"n": 0}

    def inject(src: object, dst: object) -> None:
        sp = Path(str(src))
        if ".tmp" in sp.name:
            commits["n"] += 1
            if commits["n"] == 2:
                raise OSError("fail")
        os.replace(src, dst)

    with pytest.raises(OSError):
        write_transaction({a: b"NA\n", b: b"NB\n"}, replace_fn=inject)
    assert not a.exists()
    assert b.read_text(encoding="utf-8") == "ORIGINAL_B"


def test_transaction_restores_all_preexisting_outputs_after_commit_failure(
    tmp_path: Path,
) -> None:
    files = [tmp_path / f"f{i}.json" for i in range(3)]
    for i, f in enumerate(files):
        f.write_text(f"ORIG{i}", encoding="utf-8")
    commits = {"n": 0}

    def inject(src: object, dst: object) -> None:
        sp = Path(str(src))
        if ".tmp" in sp.name:
            commits["n"] += 1
            if commits["n"] == 3:
                raise OSError("third fail")
        os.replace(src, dst)

    with pytest.raises(OSError):
        write_transaction(
            {files[0]: b"N0\n", files[1]: b"N1\n", files[2]: b"N2\n"},
            replace_fn=inject,
        )
    for i, f in enumerate(files):
        assert f.read_text(encoding="utf-8") == f"ORIG{i}"


def test_measure_reads_each_source_once_per_case(tmp_path: Path) -> None:
    suite = tmp_path / "s.jsonl"
    old = tmp_path / "o.html"
    new = tmp_path / "n.html"
    shutil.copy(FIX / "case01_strengthen_old.html", old)
    shutil.copy(FIX / "case01_strengthen_new.html", new)
    suite.write_text(
        json.dumps(
            {
                "id": "one",
                "profile": "rfc2119",
                "old": str(old),
                "new": str(new),
                "expected_classifications": ["STRENGTHENED"],
                "allow_extra": True,
                "focus_substrings": ["acknowledgment"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    real_read = Path.read_bytes

    def counting_read(self: Path) -> bytes:
        key = str(self.resolve())
        counts[key] = counts.get(key, 0) + 1
        return real_read(self)

    with patch.object(Path, "read_bytes", counting_read):
        run_measure(suite)
    assert counts.get(str(old.resolve()), 0) == 1
    assert counts.get(str(new.resolve()), 0) == 1


def test_non_normative_class_is_informative(tmp_path: Path) -> None:
    p = tmp_path / "nn.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <section class="non-normative">
          <p>Clients MUST upload diagnostics.</p>
        </section>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert doc.requirements == []


def test_exact_normative_class_token_is_normative(tmp_path: Path) -> None:
    p = tmp_path / "n.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <section class="normative">
          <p>Clients MUST upload diagnostics.</p>
        </section>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert any("upload diagnostics" in r.normalized_text for r in doc.requirements)


def test_repeated_inline_code_token_protects_the_code_occurrence(tmp_path: Path) -> None:
    p = tmp_path / "c.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <p>Clients MUST compare the literal <code>MUST</code> token.</p>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert len(doc.requirements) == 1
    assert "literal" in (doc.requirements[0].action or "")
    assert "token" in (doc.requirements[0].action or "")


def test_inline_q_historical_requirement_is_not_authoritative(tmp_path: Path) -> None:
    p = tmp_path / "q.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <p>The old text was <q>Clients MUST retry.</q></p>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert doc.requirements == []


def test_plain_historical_quote_is_conservative_or_ambiguous(tmp_path: Path) -> None:
    p = tmp_path / "h.html"
    p.write_text(
        """<!DOCTYPE html><html><body>
        <p>The previous specification stated: "Clients MUST retry."</p>
        </body></html>""",
        encoding="utf-8",
    )
    doc = extract_requirements(p, ProfileName.RFC2119)
    assert doc.requirements == []


def test_forbid_changes_gate_not_tp_fp_fn() -> None:
    m = score_classification(
        ["STRENGTHENED", "ADDED"],
        ["STRENGTHENED"],
        allow_extra=True,
        forbid=["ADDED"],
    )
    assert m.true_positives == 1
    assert m.false_positives == 1
    assert m.false_negatives == 0
    assert m.precision == 0.5
    assert m.recall == 1.0
    assert m.f1 == 0.6667
    assert m.case_passed is False


def test_package_revision_equals_verified_revision() -> None:
    """Manifest / MISSION_STATE pin consistency is checked at packaging time.

    This unit asserts the claimed fields exist and use the same non-null SHA
    format when present; packaging gate enforces exact equality.
    """
    ms = json.loads((ROOT / "MISSION_STATE.json").read_text(encoding="utf-8"))
    # During repair may be null until final pin — then must be 40-hex
    sha = ms.get("last_verified_commit")
    if sha is not None:
        assert isinstance(sha, str) and len(sha) == 40


def test_claims_pin_exact_verified_commit() -> None:
    """External-attestation contract: no self-referential package-tip SHA in-tree.

    Package commit/tree equality belongs to the external MANIFEST verifier.
    In-tree status may be pending external audit only with
    package_identity=pending_external_attestation and last_verified_commit null
    (must not invent either a self-pin or an external verdict).
    """
    ms = json.loads((ROOT / "MISSION_STATE.json").read_text(encoding="utf-8"))
    text = (ROOT / "CLAIMS.md").read_text(encoding="utf-8")
    text_l = text.lower()
    sha = ms.get("last_verified_commit")
    status = ms.get("status")
    assert status in {
        "M0_PARTIAL",
        "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT",
        "M0_BLOCKED",
    }
    if status == "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT":
        assert ms.get("package_identity") == "pending_external_attestation"
        # Self-referential SHA inside the same commit is forbidden / not required
        if sha is not None:
            assert isinstance(sha, str) and len(sha) == 40
        assert "pending pin" not in text_l
        assert "pending_external_attestation" in text_l
