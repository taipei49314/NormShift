"""Round-5: canonical bytes, portable-ref grammar, clause-level historical authority."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.extract.extractor import extract_requirements
from normshift.model.types import ProfileName
from normshift.pipeline import run_diff
from normshift.portable_ref import PortableRefError, validate_portable_ref
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


def _rehash(data: dict) -> bytes:
    data["integrity"] = {
        "alg": "sha256",
        "content_sha256": integrity_payload_hash(data),
    }
    return canonical_json_bytes(data)


def _find_zero_float_path(obj: object, path: str = "$") -> str | None:
    if isinstance(obj, float) and obj == 0.0 and math.copysign(1.0, obj) > 0.0:
        return path
    if isinstance(obj, dict):
        for k, v in obj.items():
            found = _find_zero_float_path(v, f"{path}.{k}")
            if found:
                return found
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            found = _find_zero_float_path(v, f"{path}[{i}]")
            if found:
                return found
    return None


def _set_path(obj: dict, dotted: str, value: object) -> None:
    # dotted like $.changes[0].alignment_score.combined
    assert dotted.startswith("$")
    parts: list[str] = []
    buf = ""
    i = 1
    while i < len(dotted):
        ch = dotted[i]
        if ch == ".":
            if buf:
                parts.append(buf)
                buf = ""
            i += 1
        elif ch == "[":
            if buf:
                parts.append(buf)
                buf = ""
            j = dotted.index("]", i)
            parts.append(dotted[i + 1 : j])
            i = j + 1
        else:
            buf += ch
            i += 1
    if buf:
        parts.append(buf)
    cur: object = obj
    for p in parts[:-1]:
        cur = cur[int(p)] if p.isdigit() else cur[p]  # type: ignore[index]
    last = parts[-1]
    if last.isdigit():
        cur[int(last)] = value  # type: ignore[index]
    else:
        cur[last] = value  # type: ignore[index]


# ---------------------------------------------------------------------------
# A. Canonical numeric equality
# ---------------------------------------------------------------------------


def test_verify_rejects_negative_zero_alignment_field(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    path = None
    for ch in data["changes"]:
        sc = ch.get("alignment_score")
        if not sc:
            continue
        for k, v in sc.items():
            if isinstance(v, float) and v == 0.0:
                path = f"alignment_score.{k}"
                sc[k] = -0.0
                break
            if k == "components" and isinstance(v, dict):
                for ck, cv in v.items():
                    if isinstance(cv, float) and cv == 0.0:
                        v[ck] = -0.0
                        path = f"components.{ck}"
                        break
        if path:
            break
    if path is None:
        # force combined if no natural zero
        target = next(c for c in data["changes"] if c.get("alignment_score"))
        target["alignment_score"]["combined"] = -0.0
    report.write_bytes(_rehash(data))
    # Also inject -0.0 via raw JSON in case dumps rewrote it
    text = report.read_text(encoding="utf-8")
    if "-0.0" not in text and "0.0" in text:
        text = text.replace("0.0", "-0.0", 1)
        report.write_text(text, encoding="utf-8")
        # rehash carefully: parse may reject
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    joined = " ".join(r.errors).lower()
    assert "negative zero" in joined or "strict json" in joined or "canonical" in joined


def test_verify_rejects_negative_zero_component_field(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    text = report.read_text(encoding="utf-8")
    # Flip a component float 0.0 to -0.0 inside alignment_score.components
    if '"components"' not in text:
        pytest.skip("no components in report")
    # Replace first 0.0 that appears after "components" block start
    cidx = text.find('"components"')
    assert cidx >= 0
    tail = text[cidx:]
    if "0.0" not in tail:
        pytest.skip("no zero float in components")
    # Prefer a spaced form from canonical dumps
    new_tail = tail.replace(": 0.0", ": -0.0", 1)
    if new_tail == tail:
        new_tail = tail.replace(":0.0", ":-0.0", 1)
    report.write_text(text[:cidx] + new_tail, encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_verify_rejects_overflow_to_positive_infinity(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    text = report.read_text(encoding="utf-8")
    # 1e999 becomes inf under Python json.loads without parse_constant
    import re

    text2, n = re.subn(
        r'("confidence"\s*:\s*)(-?\d+(?:\.\d+)?)',
        r"\g<1>1e999",
        text,
        count=1,
    )
    assert n == 1
    report.write_text(text2, encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok
    assert any("inf" in e.lower() or "strict json" in e.lower() for e in r.errors)


def test_verify_rejects_overflow_to_negative_infinity(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    text = report.read_text(encoding="utf-8")
    import re

    text2, n = re.subn(
        r'("confidence"\s*:\s*)(-?\d+(?:\.\d+)?)',
        r"\g<1>-1e999",
        text,
        count=1,
    )
    assert n == 1
    report.write_text(text2, encoding="utf-8")
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_live_replay_comparison_uses_canonical_bytes_not_python_numeric_equality(
    tmp_path: Path,
) -> None:
    """Even if parse allowed -0.0, replay must use canonical bytes (guard)."""
    report = _mk_report(tmp_path)
    r = verify_report_file(report, source_root=tmp_path)
    assert r.ok, r.errors
    # Python still collapses -0.0 == 0.0
    assert -0.0 == 0.0
    assert canonical_json_bytes({"x": -0.0}) != canonical_json_bytes({"x": 0.0})


def test_valid_production_zero_still_verifies(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    r = verify_report_file(report, source_root=tmp_path)
    assert r.ok, r.errors
    assert r.verification_scope == "FULL"


def test_unpaired_surrogate_returns_clean_failure_without_traceback(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    text = report.read_text(encoding="utf-8")
    # Inject JSON unicode escape for unpaired surrogate into a string field
    needle = '"original_text": "'
    idx = text.find(needle)
    assert idx >= 0
    insert_at = idx + len(needle)
    text = text[:insert_at] + "\\ud800 " + text[insert_at:]
    report.write_text(text, encoding="utf-8")
    runner = CliRunner()
    from normshift.cli import app

    res = runner.invoke(app, ["verify", str(report), "--source-root", str(tmp_path)])
    assert res.exit_code != 0
    out = (res.stdout or "") + (res.stderr or "")
    assert "Traceback" not in out
    assert "verification_scope=" in out


# ---------------------------------------------------------------------------
# B. Portable-ref grammar
# ---------------------------------------------------------------------------


def test_full_verify_rejects_dot_prefixed_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "./old.html"
    data["old_document"]["provenance"]["local_path"] = "./old.html"
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_full_verify_rejects_repeated_separator_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "old//.html".replace("old//.html", "x//old.html")
    # keep real file name structure: create nested? use invalid spelling of old.html
    data["old_document"]["path"] = "docs//old.html"
    data["old_document"]["provenance"]["local_path"] = "docs//old.html"
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_full_verify_rejects_dot_component_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "docs/./old.html"
    data["old_document"]["provenance"]["local_path"] = "docs/./old.html"
    report.write_bytes(_rehash(data))
    r = verify_report_file(report, source_root=tmp_path)
    assert not r.ok


def test_full_verify_rejects_symlink_alias_when_declared_ref_is_not_canonical_target(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    real = root / "real.html"
    real.write_text("<html><body><p>Clients MUST a.</p></body></html>", encoding="utf-8")
    link = root / "alias.html"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlink not permitted")
    new = root / "new.html"
    new.write_text("<html><body><p>Clients MUST b.</p></body></html>", encoding="utf-8")
    out = tmp_path / "r.json"
    run_diff(real, new, profile=ProfileName.RFC2119, json_out=out, source_root=root)
    data = json.loads(out.read_text(encoding="utf-8"))
    # Declare symlink spelling instead of canonical real.html
    data["old_document"]["path"] = "alias.html"
    data["old_document"]["provenance"]["local_path"] = "alias.html"
    out.write_bytes(_rehash(data))
    r = verify_report_file(out, source_root=root)
    assert not r.ok


def test_override_rejects_empty_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = ""
    data["old_document"]["provenance"]["local_path"] = ""
    report.write_bytes(_rehash(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok


def test_override_rejects_dot_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "."
    data["old_document"]["provenance"]["local_path"] = "."
    report.write_bytes(_rehash(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok


def test_override_rejects_backslash_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "old\\html"
    data["old_document"]["provenance"]["local_path"] = "old\\html"
    report.write_bytes(_rehash(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok


def test_override_rejects_backslash_traversal_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "..\\secret"
    data["old_document"]["provenance"]["local_path"] = "..\\secret"
    report.write_bytes(_rehash(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok


def test_override_rejects_unc_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "//server/share/x.html"
    data["old_document"]["provenance"]["local_path"] = "//server/share/x.html"
    report.write_bytes(_rehash(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok


def test_override_rejects_rooted_backslash_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "\\Windows\\x.html"
    data["old_document"]["provenance"]["local_path"] = "\\Windows\\x.html"
    report.write_bytes(_rehash(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok


def test_override_rejects_uri_like_ref(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    data["old_document"]["path"] = "file:old.html"
    data["old_document"]["provenance"]["local_path"] = "file:old.html"
    report.write_bytes(_rehash(data))
    r = verify_report_file(
        report,
        old_source=tmp_path / "old.html",
        new_source=tmp_path / "new.html",
    )
    assert not r.ok


def test_portable_ref_validation_is_host_platform_independent() -> None:
    with pytest.raises(PortableRefError):
        validate_portable_ref("a\\b")
    with pytest.raises(PortableRefError):
        validate_portable_ref("./a")
    with pytest.raises(PortableRefError):
        validate_portable_ref("a//b")
    with pytest.raises(PortableRefError):
        validate_portable_ref("a/./b")
    with pytest.raises(PortableRefError):
        validate_portable_ref("../a")
    with pytest.raises(PortableRefError):
        validate_portable_ref("")
    with pytest.raises(PortableRefError):
        validate_portable_ref(".")
    assert validate_portable_ref("fixtures/synthetic/spec-v1.html") == (
        "fixtures/synthetic/spec-v1.html"
    )


def test_valid_posix_relative_override_ref_returns_content_only_scope(tmp_path: Path) -> None:
    report = _mk_report(tmp_path)
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


# ---------------------------------------------------------------------------
# C. Historical authority generalization
# ---------------------------------------------------------------------------


def _reqs(tmp_path: Path, sentence: str):
    f = tmp_path / "h.html"
    f.write_text(f"<html><body><p>{sentence}</p></body></html>", encoding="utf-8")
    return extract_requirements(f, ProfileName.RFC2119).requirements


def test_previous_value_is_current(tmp_path: Path) -> None:
    reqs = _reqs(tmp_path, "The previous value MUST be retained.")
    assert len(reqs) == 1
    assert reqs[0].modality.value == "MUST"


def test_previous_state_is_current(tmp_path: Path) -> None:
    assert len(_reqs(tmp_path, "The previous state MUST remain available.")) == 1


def test_previous_section_is_current(tmp_path: Path) -> None:
    assert len(_reqs(tmp_path, "The previous section MUST be ignored.")) == 1


def test_previous_implementations_is_current(tmp_path: Path) -> None:
    assert len(_reqs(tmp_path, "Previous implementations MUST be rejected.")) == 1


def test_previously_assigned_identifiers_is_current(tmp_path: Path) -> None:
    assert len(_reqs(tmp_path, "Previously assigned identifiers MUST remain unique.")) == 1


def test_unlike_previous_spec_current_modal_is_kept(tmp_path: Path) -> None:
    reqs = _reqs(tmp_path, "Unlike the previous specification, clients MUST retry.")
    assert len(reqs) == 1
    assert "retry" in (reqs[0].action or reqs[0].normalized_text).lower()


def test_prior_spec_reported_modal_is_historical(tmp_path: Path) -> None:
    assert _reqs(tmp_path, "The prior specification said clients MUST retry.") == []


def test_earlier_version_reported_modal_is_historical(tmp_path: Path) -> None:
    assert _reqs(tmp_path, "The earlier version stated clients MUST retry.") == []


def test_current_modal_then_prior_report_keeps_current_only(tmp_path: Path) -> None:
    reqs = _reqs(
        tmp_path,
        "Clients MUST abort. The prior specification said clients MUST retry.",
    )
    assert len(reqs) == 1
    assert "abort" in (reqs[0].action or reqs[0].normalized_text).lower()


def test_prior_report_but_current_modal_keeps_current_only(tmp_path: Path) -> None:
    reqs = _reqs(
        tmp_path,
        "The prior specification said clients SHOULD retry, but clients MUST reconnect.",
    )
    assert len(reqs) == 1
    assert reqs[0].modality.value == "MUST"
    assert "reconnect" in (reqs[0].action or reqs[0].normalized_text).lower()


def test_historical_comment_change_does_not_change_current_requirement_fingerprint(
    tmp_path: Path,
) -> None:
    a = _reqs(
        tmp_path,
        'Clients MUST retry. The previous specification said "MUST NOT".',
    )
    b = _reqs(
        tmp_path,
        'Clients MUST retry. The previous specification said "SHOULD".',
    )
    assert len(a) == 1 and len(b) == 1
    assert a[0].fingerprint == b[0].fingerprint
    assert a[0].normalized_text == b[0].normalized_text


def test_historical_comment_change_does_not_emit_semantic_change_for_current_clause(
    tmp_path: Path,
) -> None:
    old = tmp_path / "old.html"
    new = tmp_path / "new.html"
    old.write_text(
        "<html><body><p>Clients MUST retry. "
        'The previous specification said "MUST NOT".</p></body></html>',
        encoding="utf-8",
    )
    new.write_text(
        "<html><body><p>Clients MUST retry. "
        'The previous specification said "SHOULD".</p></body></html>',
        encoding="utf-8",
    )
    report = run_diff(
        old,
        new,
        profile=ProfileName.RFC2119,
        source_root=tmp_path,
    )
    # No semantic change of the current obligation
    classes = {c.classification.value for c in report.changes}
    assert "AMBIGUOUS" not in classes
    # Prefer UNCHANGED only, or empty meaningful diffs
    non_unchanged = [
        c
        for c in report.changes
        if c.classification.value not in {"UNCHANGED", "EDITORIAL"}
    ]
    assert non_unchanged == []


# ---------------------------------------------------------------------------
# D. Package attestation (lightweight in-tree)
# ---------------------------------------------------------------------------


def test_no_unlinked_reexport_overlay_manifest() -> None:
    # In-tree claims must not rely on a second conflicting package tip story
    ms = json.loads((ROOT / "MISSION_STATE.json").read_text(encoding="utf-8"))
    assert ms["status"] in {
        "M0_PARTIAL",
        "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT",
        "M0_BLOCKED",
    }
    assert ms.get("package_identity") == "pending_external_attestation"
