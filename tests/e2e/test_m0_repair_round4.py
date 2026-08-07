"""Round-4 external audit contract: strict JSON, portable generation, historical, parent-chain."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.extract.extractor import extract_requirements
from normshift.io_safety import PathSafetyError, assert_outputs_safe, write_transaction
from normshift.model.types import ProfileName
from normshift.paths_root import SourceRootError
from normshift.pipeline import run_diff
from normshift.verify.verifier import verify_report_file

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "synthetic"


def _mk_report(tmp_path: Path) -> Path:
    shutil.copy(FIX / "spec-v1.html", tmp_path / "old.html")
    shutil.copy(FIX / "spec-v2.html", tmp_path / "new.html")
    run_diff(
        Path("old.html"),
        Path("new.html"),
        profile=ProfileName.RFC2119,
        json_out=tmp_path / "report.json",
        source_root=tmp_path,
    )
    return tmp_path / "report.json"


def _rewrite(report: Path, mutator) -> None:
    data = json.loads(report.read_text(encoding="utf-8"))
    mutator(data)
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))


def _cli_verify(report: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "normshift", "verify", str(report), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# B. Strict canonical JSON boundary
# ---------------------------------------------------------------------------


def test_verify_rejects_duplicate_top_level_key(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    raw = report.read_text(encoding="utf-8")
    # inject duplicate top-level key via raw bytes (json.loads would collapse)
    raw = raw.rstrip().rstrip("}") + ', "schema_version": "9.9.9"}'
    report.write_text(raw, encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert any("duplicate" in e.lower() or "strict json" in e.lower() for e in r.errors)
    cp = _cli_verify(report, "--source-root", str(tmp_path))
    assert cp.returncode != 0


def test_verify_rejects_duplicate_nested_key(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    text = report.read_text(encoding="utf-8")
    # Duplicate key inside integrity object
    text = text.replace(
        '"integrity": {',
        '"integrity": {"alg": "sha256", ',
        1,
    )
    # may already have alg — force a raw duplicate
    text = re.sub(
        r'"integrity"\s*:\s*\{',
        '"integrity": {"alg": "sha256", ',
        text,
        count=1,
    )
    report.write_text(text, encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_document_byte_length_string(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_document"]["byte_length"] = str(d["old_document"]["byte_length"])

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    cp = _cli_verify(report, "--source-root", str(tmp_path))
    assert cp.returncode != 0


def test_verify_rejects_provenance_byte_length_string(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_document"]["provenance"]["byte_length"] = str(
            d["old_document"]["provenance"]["byte_length"]
        )

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_requirement_confidence_string(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_requirements"][0]["confidence"] = "0.9"

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_requirement_structural_index_string(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_requirements"][0]["structural_index"] = "0"

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_change_confidence_string(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["changes"][0]["confidence"] = "1.0"

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_alignment_float_bool(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    # Find a change with alignment_score
    target = None
    for ch in data["changes"]:
        if ch.get("alignment_score"):
            target = ch
            break
    if target is None:
        pytest.skip("no alignment_score in synthetic report")
    target["alignment_score"]["combined"] = True
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_alignment_float_string(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    target = next((c for c in data["changes"] if c.get("alignment_score")), None)
    if target is None:
        pytest.skip("no alignment_score in synthetic report")
    target["alignment_score"]["text_similarity"] = "0.5"
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_missing_source_ref_mode(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_document"].pop("source_ref_mode", None)

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_missing_structural_index(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_requirements"][0].pop("structural_index", None)

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_missing_null_condition_field(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_requirements"][0].pop("condition", None)

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_missing_empty_fetch_metadata_field(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)

    def mut(d: dict) -> None:
        d["old_document"]["provenance"].pop("fetch_metadata", None)

    _rewrite(report, mut)
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_nan_and_infinity(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    conf = data["old_requirements"][0]["confidence"]
    # Inject non-finite constants as raw JSON text (not via json.dumps)
    base = report.read_text(encoding="utf-8")
    needle = f'"confidence": {conf}'
    if needle not in base:
        needle = f'"confidence":{conf}'
    assert needle in base, "could not locate confidence field for NaN injection"
    report.write_text(base.replace(needle, '"confidence": NaN', 1), encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    joined = " ".join(r.errors).lower()
    assert "strict json" in joined or "non-finite" in joined or "nan" in joined
    report.write_text(base.replace(needle, '"confidence": Infinity', 1), encoding="utf-8")
    r2 = verify_report_file(report, source_root=tmp_path)
    assert not r2.ok


def test_submitted_json_equals_complete_typed_dump_before_replay(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    # Happy path still verifies
    r = verify_report_file(report, source_root=tmp_path)
    assert r.ok, r.errors
    # Omitted default after re-serialize without a defaulted field fails boundary
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_requirements"][0].pop("actor", None)
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r2 = verify_report_file(report, source_root=tmp_path)
    assert not r2.ok


# ---------------------------------------------------------------------------
# C. Portable generation and override scope
# ---------------------------------------------------------------------------


def test_generation_rejects_source_outside_declared_source_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    html_a = "<html><body><p>Clients MUST x.</p></body></html>"
    html_b = "<html><body><p>Clients MUST y.</p></body></html>"
    (outside / "a.html").write_text(html_a, encoding="utf-8")
    (tmp_path / "b.html").write_text(html_b, encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(SourceRootError):
        run_diff(
            outside / "a.html",
            tmp_path / "b.html",
            profile=ProfileName.RFC2119,
            json_out=tmp_path / "r.json",
            source_root=root,
        )


def test_generation_rejects_source_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "secret.html"
    outside.write_text("<html><body><p>Clients MUST hide.</p></body></html>", encoding="utf-8")
    link = root / "escape.html"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted")
    inside = root / "ok.html"
    inside.write_text("<html><body><p>Clients MUST show.</p></body></html>", encoding="utf-8")
    with pytest.raises(SourceRootError):
        run_diff(
            link,
            inside,
            profile=ProfileName.RFC2119,
            json_out=tmp_path / "r.json",
            source_root=root,
        )


def test_generation_never_labels_absolute_ref_source_root_relative(tmp_path: Path) -> None:
    shutil.copy(FIX / "spec-v1.html", tmp_path / "old.html")
    shutil.copy(FIX / "spec-v2.html", tmp_path / "new.html")
    out = tmp_path / "report.json"
    run_diff(
        tmp_path / "old.html",
        tmp_path / "new.html",
        profile=ProfileName.RFC2119,
        json_out=out,
        source_root=tmp_path,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    for side in ("old_document", "new_document"):
        path = data[side]["path"]
        assert data[side]["source_ref_mode"] == "source_root_relative"
        assert not Path(path).is_absolute()
        assert not path.startswith("/")
        assert ":" not in path[:3] or path[1] != ":"
        assert "\\" not in path
        assert data[side]["provenance"]["local_path"] == path


def test_generation_normalizes_relative_posix_source_refs(tmp_path: Path) -> None:
    sub = tmp_path / "docs"
    sub.mkdir()
    shutil.copy(FIX / "spec-v1.html", sub / "old.html")
    shutil.copy(FIX / "spec-v2.html", sub / "new.html")
    out = tmp_path / "report.json"
    run_diff(
        Path("docs/old.html"),
        Path("docs/new.html"),
        profile=ProfileName.RFC2119,
        json_out=out,
        source_root=tmp_path,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["old_document"]["path"] == "docs/old.html"
    assert data["new_document"]["path"] == "docs/new.html"


def test_override_rejects_absolute_declared_source_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    abs_path = str((tmp_path / "old.html").resolve())
    data["old_document"]["path"] = abs_path
    data["old_document"]["provenance"]["local_path"] = abs_path
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok
    assert any("relative" in e.lower() or "absolute" in e.lower() for e in r.errors)


def test_override_rejects_traversal_declared_source_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "../etc/passwd"
    data["old_document"]["provenance"]["local_path"] = "../etc/passwd"
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    report.write_bytes(canonical_json_bytes(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok
    joined = " ".join(r.errors).lower()
    assert (
        "traversal" in joined
        or ".." in joined
        or "portable" in joined
        or "invalid" in joined
    )


def test_override_returns_machine_readable_content_only_scope(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    # Move sources so only overrides find them
    alt = tmp_path / "alt"
    alt.mkdir()
    shutil.copy(tmp_path / "old.html", alt / "old.html")
    shutil.copy(tmp_path / "new.html", alt / "new.html")
    r = verify_report_file(
        report,
        old_source=alt / "old.html",
        new_source=alt / "new.html",
    )
    assert r.ok, r.errors
    assert r.verification_scope == "CONTENT_ONLY_OVERRIDE"
    assert r.override_used is True
    runner = CliRunner()
    from normshift.cli import app

    res = runner.invoke(
        app,
        [
            "verify",
            str(report),
            "--old-source",
            str(alt / "old.html"),
            "--new-source",
            str(alt / "new.html"),
        ],
    )
    assert res.exit_code == 0, res.output
    assert "verification_scope=CONTENT_ONLY_OVERRIDE" in res.output


def test_readme_documents_override_scope_and_exit_semantics() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "verification_scope=FULL" in text
    assert "CONTENT_ONLY_OVERRIDE" in text
    assert "--source-root" in text
    assert "Exit code" in text or "exit" in text.lower()


# ---------------------------------------------------------------------------
# D. Modal-local historical authority
# ---------------------------------------------------------------------------


def _extract_texts(html_body: str) -> list[str]:
    p = Path  # placate linters in helpers used only via tmp files
    del p
    return []


def _req_actions(tmp_path: Path, sentence: str) -> list[str]:
    f = tmp_path / "h.html"
    f.write_text(f"<html><body><p>{sentence}</p></body></html>", encoding="utf-8")
    doc = extract_requirements(f, ProfileName.RFC2119)
    return [(r.modality.value, (r.action or r.normalized_text).lower()) for r in doc.requirements]


def test_previous_spec_single_modal_is_suppressed(tmp_path: Path) -> None:
    assert _req_actions(tmp_path, "The previous specification said clients MUST retry.") == []


def test_previous_spec_coordinated_modals_are_both_suppressed(tmp_path: Path) -> None:
    assert (
        _req_actions(
            tmp_path,
            "The previous specification said clients MUST retry and clients MUST reconnect.",
        )
        == []
    )


def test_current_historical_object_is_extracted(tmp_path: Path) -> None:
    reqs = _req_actions(tmp_path, "Clients MUST retain historical records.")
    assert len(reqs) == 1
    assert reqs[0][0] == "MUST"
    assert "historical" in reqs[0][1] or "retain" in reqs[0][1]


def test_current_historically_adjective_is_extracted(tmp_path: Path) -> None:
    reqs = _req_actions(tmp_path, "The historically insecure protocol MUST be disabled.")
    assert len(reqs) == 1
    assert reqs[0][0] == "MUST"


def test_previous_spec_but_current_must_keeps_current_only(tmp_path: Path) -> None:
    reqs = _req_actions(
        tmp_path,
        "The previous specification said clients SHOULD retry, but clients MUST reconnect.",
    )
    assert len(reqs) == 1
    assert reqs[0][0] == "MUST"
    assert "reconnect" in reqs[0][1]


def test_current_must_then_old_version_keeps_current_only(tmp_path: Path) -> None:
    reqs = _req_actions(
        tmp_path,
        "Clients MUST now abort, although the old version said clients MUST retry.",
    )
    assert len(reqs) == 1
    assert reqs[0][0] == "MUST"
    assert "abort" in reqs[0][1]


def test_incidental_was_required_does_not_hide_current_must(tmp_path: Path) -> None:
    reqs = _req_actions(
        tmp_path,
        "Because low latency was required for interoperability, clients MUST retry.",
    )
    assert len(reqs) == 1
    assert reqs[0][0] == "MUST"
    assert "retry" in reqs[0][1]


def test_previously_modal_is_historical(tmp_path: Path) -> None:
    assert _req_actions(tmp_path, "Previously, clients MUST retry.") == []


def test_historical_sentence_then_current_sentence_keeps_current_only(tmp_path: Path) -> None:
    reqs = _req_actions(
        tmp_path,
        "The previous specification said clients MUST retry. Clients MUST reconnect.",
    )
    assert len(reqs) == 1
    assert reqs[0][0] == "MUST"
    assert "reconnect" in reqs[0][1]


# ---------------------------------------------------------------------------
# E. Transaction parent-chain restoration
# ---------------------------------------------------------------------------


def test_preflight_rejects_output_whose_existing_ancestor_is_file(tmp_path: Path) -> None:
    blocker = tmp_path / "file_not_dir"
    blocker.write_text("x", encoding="utf-8")
    dest = blocker / "child" / "out.json"
    with pytest.raises(PathSafetyError):
        assert_outputs_safe(inputs=[], outputs=[dest])


def test_multi_output_preflight_is_non_mutating_across_all_destinations(tmp_path: Path) -> None:
    good = tmp_path / "a" / "out.json"
    blocker = tmp_path / "file_not_dir"
    blocker.write_text("x", encoding="utf-8")
    bad = blocker / "b" / "out.json"
    before = list(tmp_path.iterdir())
    with pytest.raises(PathSafetyError):
        assert_outputs_safe(inputs=[], outputs=[good, bad])
    # No directories created
    assert list(tmp_path.iterdir()) == before
    assert not (tmp_path / "a").exists()


def test_failed_staging_removes_only_directories_created_by_invocation(tmp_path: Path) -> None:
    pre_existing = tmp_path / "keep"
    pre_existing.mkdir()
    (pre_existing / "sibling.txt").write_text("keep-me", encoding="utf-8")

    dest_new = tmp_path / "created" / "nested" / "out.json"
    dest_fail = tmp_path / "keep" / "out.json"

    def boom(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        # Fail on second commit replace into keep/
        if Path(dst).name == "out.json" and Path(dst).parent.name == "keep":
            raise OSError("forced commit failure")
        os.replace(src, dst)

    with pytest.raises(OSError, match="forced"):
        write_transaction(
            {dest_new: b'{"a":1}\n', dest_fail: b'{"b":2}\n'},
            replace_fn=boom,
        )
    # Invocation-created parent chain must be removed when empty
    assert not (tmp_path / "created").exists()
    # Pre-existing parent must remain with sibling
    assert pre_existing.is_dir()
    assert (pre_existing / "sibling.txt").read_text(encoding="utf-8") == "keep-me"
    assert not dest_fail.exists()
    assert not dest_new.exists()


def test_existing_parent_directories_are_never_removed(tmp_path: Path) -> None:
    parent = tmp_path / "existing_parent"
    parent.mkdir()
    dest = parent / "out.json"
    write_transaction({dest: b"{}\n"})
    assert parent.is_dir()
    assert dest.is_file()


def test_sibling_files_survive_parent_cleanup(tmp_path: Path) -> None:
    parent = tmp_path / "p"
    parent.mkdir()
    sib = parent / "sib.txt"
    sib.write_text("ok", encoding="utf-8")
    # Fail after creating a new nested dir under parent
    nested = parent / "newdir" / "out.json"

    def boom(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        raise OSError("nope")

    with pytest.raises(OSError):
        write_transaction({nested: b"x\n"}, replace_fn=boom)
    assert sib.read_text(encoding="utf-8") == "ok"
    assert parent.is_dir()
    assert not (parent / "newdir").exists()


# ---------------------------------------------------------------------------
# A. Exact package subject / governance (lightweight in-tree)
# ---------------------------------------------------------------------------


def test_external_attestation_contract_has_no_noop_assertion() -> None:
    """Scan round2/round3 governance tests for unconditional truth branches."""
    for name in (
        "tests/e2e/test_m0_repair_round2.py",
        "tests/e2e/test_m0_repair_round3.py",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        # Unconditional truth branches (e.g. `... or True`) must not remain.
        assert re.search(r"\bor\s+True\b", text) is None
        assert re.search(r"\bor\s+true\b", text) is None


def test_no_repository_commit_after_verified_gate() -> None:
    """In-tree rule: when pending external audit, claims use external attestation."""
    ms = json.loads((ROOT / "MISSION_STATE.json").read_text(encoding="utf-8"))
    claims = (ROOT / "CLAIMS.md").read_text(encoding="utf-8").lower()
    if ms.get("status") == "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT":
        assert ms.get("package_identity") == "externally_attested"
        assert "externally attested" in claims or "externally_attested" in claims
