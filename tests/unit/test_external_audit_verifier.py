from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify_external_audit.py"
SCHEMA = ROOT / "schemas" / "external_audit_v1.schema.json"
COMMIT = "a" * 40
TREE = "b" * 40
VERSION = "0.4.0"
RUN_ID = "20260811T120000Z-final"
ROOTS_INVENTORY_SHA256 = "1" * 64
APPROVED_VOLUME_BINDING_SHA256 = "2" * 64


def _write_json(path: Path, value: dict[str, Any]) -> str:
    serialized = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    raw = (serialized + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _record(path: str) -> dict[str, Any]:
    return {"path": path, "sha256": "0" * 64, "size": 0}


def _package_manifest() -> dict[str, Any]:
    command = {
        "id": "gate",
        "gate": "other",
        "argv": ["normshift", "verify"],
        "cwd": ".",
        "started_at": "2026-08-11T12:00:00Z",
        "finished_at": "2026-08-11T12:00:01Z",
        "required": True,
        "exit_code": 0,
        "log": "pytest_log",
    }
    return {
        "schema_version": "normshift-package-manifest/v1",
        "milestone": "M0",
        "run_id": RUN_ID,
        "package_version": VERSION,
        "package_commit": COMMIT,
        "package_tree": TREE,
        "repository": {
            "url": "https://github.com/taipei49314/NormShift",
            "default_branch": "master",
            "dirty": False,
        },
        "timestamps": {
            "started_at": "2026-08-11T12:00:00Z",
            "finished_at": "2026-08-11T12:00:01Z",
        },
        "environment": {
            "os": "test",
            "architecture": "test",
            "python": "3.12",
            "uv": "0.12.2",
            "git": "2.0",
            "build_frontend": "hatchling",
            "build_backend": {
                "module": "hatchling.build",
                "distribution": "hatchling",
                "version": "1.31.0",
            },
            "source_date_epoch": "1760000000",
            "gate_state_policy": "ephemeral_outside_repository",
            "normshift": VERSION,
        },
        "status": {
            "m0": "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT",
            "m1": "EXPERIMENTAL_NOT_ADJUDICATED",
            "m2": "EXPERIMENTAL_NOT_ADJUDICATED",
            "release": "BLOCKED",
        },
        "m1": {
            "acceptance_evaluated": False,
            "reason": "not evaluated",
            "corpus_refs": [],
            "ground_truth_refs": [],
            "per_class": {},
        },
        "m2": {
            "acceptance_evaluated": False,
            "reason": "not evaluated",
            "corpus_refs": [],
            "ground_truth_refs": [],
            "per_class": {},
        },
        "working_directory_policy": "clean_exact_commit_repository_root",
        "artifacts": {
            name: _record(f"{name}.bin")
            for name in (
                "bundle",
                "source_zip",
                "wheel",
                "sdist",
                "sbom",
                "checksums",
                "audit_contract",
                "manifest_schema",
            )
        },
        "logs": {"pytest_log": _record("pytest.log")},
        "files": {"package_manifest": _record("package-manifest.json")},
        "commands": [dict(command, id=f"gate-{index}") for index in range(8)],
        "counts": {
            "pytest": {
                "collected": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
                "xfailed": 0,
                "xpassed": 0,
                "errors": 0,
                "junit_file": "pytest_log",
            },
            "benchmark": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "cases": [{"id": "b", "passed": True}],
            },
            "measure": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "cases": [{"id": "m", "passed": True}],
                "metrics": {
                    name: {"precision": 1, "recall": 1, "f1": 1}
                    for name in ("extraction", "alignment", "classification")
                },
            },
        },
        "matrices": {
            "r4_r5": {
                "log": "pytest_log",
                "junit_file": "pytest_log",
                "cases": [{"id": "matrix", "expected_exit": "zero", "actual_exit_code": 0}],
            }
        },
        "archive": {
            "prefix": "NormShift/",
            "tracked_file_count": 1,
            "archive_file_count": 1,
            "missing_count": 0,
            "extra_count": 0,
            "duplicate_count": 0,
            "unsafe_count": 0,
            "case_collision_count": 0,
            "blob_equality": True,
        },
        "bundle": {"head": COMMIT, "tree": TREE, "fsck": True},
        "determinism": {
            name: {"first": "pytest_log", "second": "pytest_log", "equal": True}
            for name in ("report_json", "report_markdown", "metrics")
        },
        "replay": {"report_path": "report.json", "source_root": ".", "expected_scope": "FULL"},
        "sbom": {
            "format": "CycloneDX",
            "spec_version": "1.5",
            "generator": {"name": "uv", "version": "0.12.2"},
            "generator_argv": ["uv", "export"],
            "validator": {
                "name": "cyclonedx-python-lib",
                "version": "11.11.0",
                "mode": "strict-offline-1.5",
            },
            "lockfile_sha256": "0" * 64,
            "root": {"name": "normshift", "version": VERSION},
            "inventory": [{"name": "normshift", "version": VERSION, "source": "local"}],
            "distribution_requirements": ["typer"],
            "runtime_requirements_file": "pytest_log",
        },
        "checks": {
            "relocation_verify": True,
            "extracted_archive_verify": True,
            "wheel_smoke": True,
            "sdist_smoke": True,
        },
        "known_limitations": ["bounded test fixture"],
        "unclaimed_scopes": ["production"],
    }


def _subject(tmp_path: Path) -> tuple[Path, str, Path, str]:
    manifest_path = tmp_path / "NormShift-0.4.0-run-MANIFEST.json"
    manifest_sha = _write_json(manifest_path, _package_manifest())
    audit_path = tmp_path / "NormShift-0.4.0-run-EXTERNAL-AUDIT.json"
    audit_sha = _write_json(
        audit_path,
        {
            "audited_at_utc": "2026-08-11T12:00:00Z",
            "auditor": {
                "independent_from_implementation": True,
                "reviewer_id": "reviewer-1",
            },
            "findings": {"p0": 0, "p1": 0, "p2": 0},
            "limitations": [],
            "manifest_sha256": manifest_sha,
            "execution_authority": {
                "platform": "windows",
                "filesystem": "NTFS",
                "drive_type": "fixed",
                "local_volume": True,
                "same_volume": True,
                "lock_policy": {
                    "id": "normshift-windows-ntfs-share-deny",
                    "version": "1.0.0",
                },
                "authority_run_id": RUN_ID,
                "preflight_result": "PASS",
                "roots_inventory_sha256": ROOTS_INVENTORY_SHA256,
                "approved_volume_binding_sha256": APPROVED_VOLUME_BINDING_SHA256,
            },
            "package_commit": COMMIT,
            "package_tree": TREE,
            "package_version": VERSION,
            "run_id": RUN_ID,
            "schema_version": "normshift-external-audit/v1",
            "scope": "M0_M1_M2_COMBINED",
            "verdict": "M0_M1_M2_COMBINED_EXTERNAL_AUDIT_PASS",
        },
    )
    return manifest_path, manifest_sha, audit_path, audit_sha


def _run(
    manifest_path: Path,
    manifest_sha: str,
    audit_path: Path,
    audit_sha: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest_path),
            "--audit",
            str(audit_path),
            "--schema",
            str(SCHEMA),
            "--manifest-sha256",
            manifest_sha,
            "--audit-sha256",
            audit_sha,
            "--commit",
            COMMIT,
            "--tree",
            TREE,
            "--version",
            VERSION,
            "--run-id",
            RUN_ID,
            "--roots-inventory-sha256",
            ROOTS_INVENTORY_SHA256,
            "--approved-volume-binding-sha256",
            APPROVED_VOLUME_BINDING_SHA256,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_external_audit_verifier_accepts_one_exact_detached_subject(tmp_path: Path) -> None:
    manifest_path, manifest_sha, audit_path, audit_sha = _subject(tmp_path)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "audit_sha256": audit_sha,
        "manifest_sha256": manifest_sha,
        "ok": True,
        "p0": 0,
        "p1": 0,
        "p2": 0,
        "package_commit": COMMIT,
        "package_tree": TREE,
        "schema_version": "normshift-external-audit/v1",
        "scope": "M0_M1_M2_COMBINED",
        "verdict": "M0_M1_M2_COMBINED_EXTERNAL_AUDIT_PASS",
    }


@pytest.mark.parametrize(
    "field", ["package_commit", "package_tree", "package_version", "run_id"]
)
def test_external_audit_verifier_rejects_wrong_subject(tmp_path: Path, field: str) -> None:
    manifest_path, manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    replacements = {
        "package_commit": "c" * 40,
        "package_tree": "c" * 40,
        "package_version": "0.4.1",
        "run_id": "different-run-id",
    }
    audit[field] = replacements[field]
    audit_sha = _write_json(audit_path, audit)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "differs from the release subject" in result.stderr


def test_external_audit_verifier_rejects_wrong_external_hash_anchors(tmp_path: Path) -> None:
    manifest_path, manifest_sha, audit_path, audit_sha = _subject(tmp_path)

    wrong_manifest = _run(manifest_path, "0" * 64, audit_path, audit_sha)
    wrong_audit = _run(manifest_path, manifest_sha, audit_path, "0" * 64)

    assert wrong_manifest.returncode == 1
    assert "manifest bytes differ" in wrong_manifest.stderr
    assert wrong_audit.returncode == 1
    assert "audit bytes differ" in wrong_audit.stderr


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("execution_authority", "platform"), "linux"),
        (("execution_authority", "filesystem"), "ext4"),
        (("execution_authority", "drive_type"), "network"),
        (("execution_authority", "lock_policy", "id"), "free-form-lock"),
        (("execution_authority", "lock_policy", "version"), "9.9.9"),
        (("execution_authority", "preflight_result"), "FAIL"),
    ],
)
def test_external_audit_verifier_rejects_free_form_or_nonpassing_authority(
    tmp_path: Path, path: tuple[str, ...], value: str
) -> None:
    manifest_path, manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    target: dict[str, Any] = audit
    for key in path[:-1]:
        child = target[key]
        assert isinstance(child, dict)
        target = child
    target[path[-1]] = value
    audit_sha = _write_json(audit_path, audit)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "schema mismatch" in result.stderr


def test_external_audit_verifier_rejects_free_form_authority_property(tmp_path: Path) -> None:
    manifest_path, manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    authority = audit["execution_authority"]
    assert isinstance(authority, dict)
    authority["unverified_lock_note"] = "trust me"
    audit_sha = _write_json(audit_path, audit)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "schema mismatch" in result.stderr


def test_external_audit_verifier_rejects_missing_or_wrong_authority_run_id(
    tmp_path: Path,
) -> None:
    manifest_path, manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    authority = audit["execution_authority"]
    assert isinstance(authority, dict)
    authority["authority_run_id"] = "20260811T120000Z-other"
    audit_sha = _write_json(audit_path, audit)

    mismatch = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert mismatch.returncode == 1
    assert "execution authority differs" in mismatch.stderr

    del authority["authority_run_id"]
    audit_sha = _write_json(audit_path, audit)
    missing = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert missing.returncode == 1
    assert "schema mismatch" in missing.stderr


@pytest.mark.parametrize(
    "field", ["roots_inventory_sha256", "approved_volume_binding_sha256"]
)
def test_external_audit_verifier_rejects_wrong_anchored_volume_evidence(
    tmp_path: Path, field: str
) -> None:
    manifest_path, manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    authority = audit["execution_authority"]
    assert isinstance(authority, dict)
    authority[field] = "f" * 64
    audit_sha = _write_json(audit_path, audit)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "execution authority differs" in result.stderr


@pytest.mark.parametrize("finding", ["p0", "p1"])
def test_external_audit_verifier_rejects_open_blocking_findings(
    tmp_path: Path,
    finding: str,
) -> None:
    manifest_path, manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["findings"][finding] = 1
    audit_sha = _write_json(audit_path, audit)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "schema mismatch" in result.stderr


def test_external_audit_verifier_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    manifest_path, manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    raw = audit_path.read_text(encoding="utf-8").replace(
        '"scope":"M0_M1_M2_COMBINED"',
        '"scope":"M0_M1_M2_COMBINED","scope":"M0_M1_M2_COMBINED"',
    )
    audit_path.write_text(raw, encoding="utf-8")
    audit_sha = hashlib.sha256(audit_path.read_bytes()).hexdigest()

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "duplicate object key" in result.stderr


def test_external_audit_verifier_rejects_manifest_self_listing(tmp_path: Path) -> None:
    manifest_path, _manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = {"external_audit": _record(audit_path.name)}
    manifest_sha = _write_json(manifest_path, manifest)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["manifest_sha256"] = manifest_sha
    audit_sha = _write_json(audit_path, audit)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "must not be self-listed" in result.stderr


def test_external_audit_verifier_resolves_nested_audit_path_before_self_listing(
    tmp_path: Path,
) -> None:
    manifest_path, _manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    nested = tmp_path / "detached"
    nested.mkdir()
    nested_audit = nested / audit_path.name
    audit_path.replace(nested_audit)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = {"external_audit": _record(f"detached/{nested_audit.name}")}
    manifest_sha = _write_json(manifest_path, manifest)
    audit = json.loads(nested_audit.read_text(encoding="utf-8"))
    audit["manifest_sha256"] = manifest_sha
    audit_sha = _write_json(nested_audit, audit)

    result = _run(manifest_path, manifest_sha, nested_audit, audit_sha)

    assert result.returncode == 1
    assert "must not be self-listed" in result.stderr


def test_external_audit_verifier_rejects_structural_audit_digest_binding(tmp_path: Path) -> None:
    manifest_path, _manifest_sha, audit_path, audit_sha = _subject(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = {
        "bound_digest": {"path": "attestation.txt", "sha256": audit_sha, "size": 0}
    }
    manifest_sha = _write_json(manifest_path, manifest)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "digest must not be self-bound" in result.stderr


def test_external_audit_verifier_requires_the_package_manifest_schema(tmp_path: Path) -> None:
    manifest_path, _manifest_sha, audit_path, _audit_sha = _subject(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["unexpected"] = True
    manifest_sha = _write_json(manifest_path, manifest)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["manifest_sha256"] = manifest_sha
    audit_sha = _write_json(audit_path, audit)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "package manifest schema mismatch" in result.stderr


def test_external_audit_packaged_schema_is_the_exact_authority_copy() -> None:
    packaged_schema = ROOT / "src" / "normshift" / "schemas" / SCHEMA.name

    assert packaged_schema.read_bytes() == SCHEMA.read_bytes()


def test_external_audit_verifier_rejects_multiply_linked_audit(tmp_path: Path) -> None:
    manifest_path, manifest_sha, audit_path, audit_sha = _subject(tmp_path)
    os.link(audit_path, tmp_path / "audit-hardlink.json")

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "link count exactly one" in result.stderr


def test_external_audit_verifier_bounds_json_before_parsing(tmp_path: Path) -> None:
    manifest_path, manifest_sha, audit_path, audit_sha = _subject(tmp_path)
    with manifest_path.open("wb") as handle:
        handle.truncate(4 * 1024 * 1024 + 1)

    result = _run(manifest_path, manifest_sha, audit_path, audit_sha)

    assert result.returncode == 1
    assert "exceeds 4194304 bytes" in result.stderr
