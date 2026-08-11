"""Focused fail-closed tests for the external package verifier."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import warnings
import zipfile
from pathlib import Path

import pytest

from normshift.audit import package_build
from normshift.audit import package_verify as pv

ROOT = Path(__file__).resolve().parents[2]


def _run(*argv: str, cwd: Path | None = None) -> None:
    subprocess.run(argv, cwd=cwd, check=True, capture_output=True)


def _git_fixture(tmp_path: Path) -> tuple[Path, str, str, Path, Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run("git", "init", "-b", "master", cwd=repo)
    _run("git", "config", "user.name", "Verifier Test", cwd=repo)
    _run("git", "config", "user.email", "verifier@example.test", cwd=repo)
    _run("git", "remote", "add", "origin", "https://example.test/normshift", cwd=repo)
    (repo / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
    (repo / "README.md").write_text("exact subject\n", encoding="utf-8")
    for round_number in (4, 5):
        test_file = repo / "tests" / "e2e" / f"test_m0_repair_round{round_number}.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(
            f"def test_round_{round_number}():\n    assert True\n",
            encoding="utf-8",
        )
    _run("git", "add", ".", cwd=repo)
    _run("git", "commit", "-m", "fixture", cwd=repo)
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    _run("git", "update-ref", "refs/remotes/origin/master", commit, cwd=repo)
    tree = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    bundle = tmp_path / "subject.bundle"
    source_zip = tmp_path / "Source.zip"
    prefix = "NormShift-test/"
    _run("git", "bundle", "create", str(bundle), "HEAD", cwd=repo)
    _run(
        "git",
        "archive",
        "--format=zip",
        f"--prefix={prefix}",
        f"--output={source_zip}",
        "HEAD",
        cwd=repo,
    )
    return repo, commit, tree, bundle, source_zip, prefix


def _archive_claim(repo: Path, commit: str, source_zip: Path, prefix: str) -> dict[str, object]:
    tracked = subprocess.check_output(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", commit], text=True
    ).splitlines()
    with zipfile.ZipFile(source_zip) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
    return {
        "prefix": prefix,
        "tracked_file_count": len(tracked),
        "archive_file_count": len(files),
        "missing_count": 0,
        "extra_count": 0,
        "duplicate_count": 0,
        "unsafe_count": 0,
        "case_collision_count": 0,
        "blob_equality": True,
    }


@pytest.mark.parametrize("token", [b"-0", b"-0.0", b"1e999"])
def test_strict_manifest_json_rejects_duplicate_and_noncanonical_numbers(token: bytes) -> None:
    with pytest.raises(pv.StrictJsonError):
        pv._strict_json_bytes(b'{"x":' + token + b"}", label="manifest")
    with pytest.raises(pv.StrictJsonError, match="duplicate"):
        pv._strict_json_bytes(b'{"x":1,"x":1}', label="manifest")


def test_portable_record_path_accepts_relative_base_with_parent_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "package"
    work = tmp_path / "work"
    package.mkdir()
    work.mkdir()
    artifact = package / "artifact.txt"
    artifact.write_text("bound\n", encoding="utf-8")
    monkeypatch.chdir(work)

    resolved = pv._portable_record_path(Path("../package"), "artifact.txt")

    assert resolved == artifact.resolve()


def test_bundle_clone_fsck_head_and_tree(tmp_path: Path) -> None:
    repo, commit, tree, bundle, _, _ = _git_fixture(tmp_path)
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "repository": {
            "url": "https://example.test/normshift",
            "default_branch": "master",
            "dirty": False,
        },
        "bundle": {"head": commit, "tree": tree, "fsck": True},
    }
    state = pv._State()
    pv._verify_repo_and_bundle(repo, bundle, manifest, state)
    assert state.error_count == 0, state.errors
    manifest["package_commit"] = "0" * 40
    manifest["bundle"] = {"head": "0" * 40, "tree": tree, "fsck": True}
    corrupt = pv._State()
    pv._verify_repo_and_bundle(repo, bundle, manifest, corrupt)
    assert corrupt.error_count > 0


def test_repository_identity_normalizes_ssh_origin_and_ignores_local_branch(
    tmp_path: Path,
) -> None:
    repo, commit, tree, bundle, _, _ = _git_fixture(tmp_path)
    _run("git", "switch", "-c", "feature-at-default-sha", cwd=repo)
    _run(
        "git",
        "remote",
        "set-url",
        "origin",
        "git@github.com:taipei49314/NormShift.git",
        cwd=repo,
    )
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "repository": {
            "url": "https://github.com/taipei49314/NormShift",
            "default_branch": "master",
            "dirty": False,
        },
        "bundle": {"head": commit, "tree": tree, "fsck": True},
    }

    state = pv._State()
    pv._verify_repo_and_bundle(repo, bundle, manifest, state)

    assert state.error_count == 0, state.errors


@pytest.mark.parametrize(
    ("remote_url", "manifest_url"),
    [
        (
            "https://github.com/taipei49314/NormShift.git",
            "https://github.com/taipei49314/NormShift",
        ),
        (
            "https://github.com/taipei49314/NormShift",
            "https://github.com/taipei49314/NormShift.git",
        ),
    ],
)
def test_repository_identity_normalizes_https_dot_git_suffix(
    tmp_path: Path,
    remote_url: str,
    manifest_url: str,
) -> None:
    repo, commit, tree, bundle, _, _ = _git_fixture(tmp_path)
    _run("git", "remote", "set-url", "origin", remote_url, cwd=repo)
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "repository": {
            "url": manifest_url,
            "default_branch": "master",
            "dirty": False,
        },
        "bundle": {"head": commit, "tree": tree, "fsck": True},
    }

    state = pv._State()
    pv._verify_repo_and_bundle(repo, bundle, manifest, state)

    assert state.error_count == 0, state.errors


@pytest.mark.parametrize(
    "remote_url",
    [
        "https://token@github.com/taipei49314/NormShift.git",
        "https://github.com:443/taipei49314/NormShift.git",
        "https://github.com/taipei49314/NormShift.git?token=secret",
        "https://github.com/taipei49314/NormShift.git#fragment",
        "https://github.com/taipei49314/NormShift.git.evil",
        "https://github.com/taipei49314/NormShift%2egit",
    ],
)
def test_repository_identity_rejects_remote_url_lookalikes(
    tmp_path: Path,
    remote_url: str,
) -> None:
    repo, commit, tree, bundle, _, _ = _git_fixture(tmp_path)
    _run("git", "remote", "set-url", "origin", remote_url, cwd=repo)
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "repository": {
            "url": "https://github.com/taipei49314/NormShift",
            "default_branch": "master",
            "dirty": False,
        },
        "bundle": {"head": commit, "tree": tree, "fsck": True},
    }

    state = pv._State()
    pv._verify_repo_and_bundle(repo, bundle, manifest, state)

    assert any("origin URL differs" in error for error in state.errors)


def test_repository_identity_rejects_commit_not_at_remote_default(tmp_path: Path) -> None:
    repo, _, _, _, _, _ = _git_fixture(tmp_path)
    _run("git", "switch", "-c", "feature-ahead", cwd=repo)
    _run("git", "commit", "--allow-empty", "-m", "ahead", cwd=repo)
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    tree = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    bundle = tmp_path / "feature.bundle"
    _run("git", "bundle", "create", str(bundle), "HEAD", cwd=repo)
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "repository": {
            "url": "https://example.test/normshift",
            "default_branch": "master",
            "dirty": False,
        },
        "bundle": {"head": commit, "tree": tree, "fsck": True},
    }

    state = pv._State()
    pv._verify_repo_and_bundle(repo, bundle, manifest, state)

    assert any("origin/default-branch" in error for error in state.errors)


@pytest.mark.parametrize(
    "bad_name",
    ["../escape", "/absolute", "NormShift-test/a\\b"],
)
def test_source_zip_rejects_unsafe_paths(tmp_path: Path, bad_name: str) -> None:
    repo, commit, tree, _, source_zip, prefix = _git_fixture(tmp_path)
    with zipfile.ZipFile(source_zip, "a") as archive:
        archive.writestr(bad_name, b"bad")
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "archive": _archive_claim(repo, commit, source_zip, prefix),
    }
    state = pv._State()
    pv._verify_source_zip(repo, source_zip, manifest, state)
    assert state.error_count > 0
    assert any(
        marker in error
        for error in state.errors
        for marker in ("unsafe", "prefix", "extra archive")
    )


def test_safe_zip_name_rejects_literal_backslash() -> None:
    with pytest.raises(ValueError, match="backslash"):
        pv._safe_zip_name("NormShift-test/a\\b", directory=False)


def test_source_zip_rejects_raw_header_backslash_before_windows_normalization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit, tree, _, source_zip, prefix = _git_fixture(tmp_path)
    original = f"{prefix}.gitattributes".encode("ascii")
    tampered = f"{prefix.rstrip('/')}\\.gitattributes".encode("ascii")
    payload = source_zip.read_bytes()
    assert len(original) == len(tampered)
    assert payload.count(original) == 2  # local header + central directory
    source_zip.write_bytes(payload.replace(original, tampered))
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "archive": _archive_claim(repo, commit, source_zip, prefix),
    }
    # Exercise the Windows ZipInfo normalization path on every CI platform.
    monkeypatch.setattr(zipfile.os, "sep", "\\")

    state = pv._State()
    pv._verify_source_zip(repo, source_zip, manifest, state)

    assert state.error_count > 0
    assert any("backslash" in error for error in state.errors)
    destination = tmp_path / "must-not-extract"
    destination.mkdir()
    with pytest.raises(ValueError, match="backslash"):
        pv._extract_preflighted_source(source_zip, destination, prefix)
    with pytest.raises(package_build.PackageBuildError, match="unsafe_count"):
        package_build._inspect_source_archive(source_zip, repo, commit, prefix)


def test_source_zip_rejects_local_and_central_filename_mismatch(tmp_path: Path) -> None:
    repo, commit, tree, _, source_zip, prefix = _git_fixture(tmp_path)
    original = f"{prefix}.gitattributes".encode("ascii")
    tampered = f"{prefix.rstrip('/')}\\.gitattributes".encode("ascii")
    payload = source_zip.read_bytes()
    assert payload.count(original) == 2
    source_zip.write_bytes(payload.replace(original, tampered, 1))
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "archive": _archive_claim(repo, commit, source_zip, prefix),
    }

    state = pv._State()
    pv._verify_source_zip(repo, source_zip, manifest, state)

    assert state.error_count > 0
    assert any("local ZIP header" in error for error in state.errors)


def test_source_zip_accepts_and_extracts_canonical_root_directory(tmp_path: Path) -> None:
    repo, commit, tree, _, source_zip, prefix = _git_fixture(tmp_path)
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "archive": _archive_claim(repo, commit, source_zip, prefix),
    }

    state = pv._State()
    pv._verify_source_zip(repo, source_zip, manifest, state)
    destination = tmp_path / "extracted"
    destination.mkdir()
    extracted = pv._extract_preflighted_source(source_zip, destination, prefix)

    assert state.error_count == 0, state.errors
    assert extracted == destination / prefix.rstrip("/")
    assert (extracted / "README.md").read_text(encoding="utf-8") == "exact subject\n"


def test_source_zip_rejects_duplicate_case_collision_and_symlink(tmp_path: Path) -> None:
    repo, commit, tree, _, source_zip, prefix = _git_fixture(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(source_zip, "a") as archive:
            archive.writestr(f"{prefix}README.md", b"duplicate")
            archive.writestr(f"{prefix}readme.md", b"case collision")
            link = zipfile.ZipInfo(f"{prefix}link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, b"README.md")
    manifest = {
        "package_commit": commit,
        "package_tree": tree,
        "archive": _archive_claim(repo, commit, source_zip, prefix),
    }
    state = pv._State()
    pv._verify_source_zip(repo, source_zip, manifest, state)
    joined = " ".join(state.errors).lower()
    assert "duplicate" in joined
    assert "collision" in joined
    assert "special" in joined or "symlink" in joined


@pytest.mark.parametrize("corrupt_name", ["bundle", "source_zip", "wheel"])
def test_declared_bundle_zip_and_wheel_hash_and_size_are_checked(
    tmp_path: Path, corrupt_name: str
) -> None:
    files: dict[str, dict[str, object]] = {}
    for name in ("bundle", "source_zip", "wheel"):
        path = tmp_path / name
        path.write_bytes(name.encode())
        files[name] = {
            "path": name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": path.stat().st_size,
        }
    manifest = {"artifacts": files, "logs": {}, "files": {}}
    (tmp_path / corrupt_name).write_bytes(b"corrupt")
    state = pv._State()
    pv._verify_file_records(manifest, tmp_path, state)
    assert state.error_count == 2
    assert all(f"artifacts.{corrupt_name}" in error for error in state.errors)


def test_omitted_log_and_false_pytest_count_fail_closed(tmp_path: Path) -> None:
    log = tmp_path / "pytest.json"
    envelope = {
        "schema_version": pv.COMMAND_LOG_VERSION,
        "command_id": "pytest",
        "gate": "pytest",
        "required": True,
        "argv": ["pytest"],
        "cwd": ".",
        "started_at": "2026-08-09T00:00:00Z",
        "finished_at": "2026-08-09T00:00:01Z",
        "exit_code": 0,
        "stdout": "3 passed in 0.01s",
        "stderr": "",
    }
    log.write_text(json.dumps(envelope), encoding="utf-8")
    manifest = {
        "commands": [
            {
                "id": "pytest",
                "gate": "pytest",
                "required": True,
                "argv": ["pytest"],
                "cwd": ".",
                "started_at": "2026-08-09T00:00:00Z",
                "finished_at": "2026-08-09T00:00:01Z",
                "exit_code": 0,
                "log": "pytest",
            }
        ],
        "logs": {},
        "timestamps": {
            "started_at": "2026-08-09T00:00:00Z",
            "finished_at": "2026-08-09T00:00:01Z",
        },
        "counts": {
            "pytest": {
                "collected": 2,
                "passed": 2,
                "failed": 0,
                "skipped": 0,
                "xfailed": 0,
                "xpassed": 0,
                "errors": 0,
            },
            "benchmark": {
                "total": 17,
                "passed": 17,
                "failed": 0,
                "cases": [{"id": f"b{i}", "passed": True} for i in range(17)],
            },
            "measure": {
                "total": 15,
                "passed": 15,
                "failed": 0,
                "cases": [{"id": f"m{i}", "passed": True} for i in range(15)],
                "metrics": {
                    layer: {"precision": 1, "recall": 1, "f1": 1}
                    for layer in ("extraction", "alignment", "classification")
                },
            },
        },
    }
    missing = pv._State()
    pv._verify_command_records(manifest, {}, missing)
    assert missing.error_count > 0
    pv._verify_counts(manifest, {"pytest": envelope}, missing)
    assert any("pytest" in error and "log reports 3" in error for error in missing.errors)


def test_invalid_sbom_and_unavailable_installer_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sbom = tmp_path / "sbom.json"
    sbom.write_text('{"bomFormat":"CycloneDX","components":[]}', encoding="utf-8")
    state = pv._State()
    pv._verify_sbom(
        {"sbom": {}},
        {("artifacts", "sbom"): sbom},
        state,
    )
    assert state.error_count > 0
    monkeypatch.setattr(pv.shutil, "which", lambda _name: None)
    install_state = pv._State()
    pv._verify_installs_and_replay({}, {}, tmp_path / "missing.zip", install_state)
    assert install_state.error_count > 0
    assert install_state.checks["isolated_install"] is False


def test_root_and_packaged_schemas_are_byte_identical() -> None:
    for name in ("package_manifest_v1.schema.json", "command_log_v1.schema.json"):
        assert (ROOT / "schemas" / name).read_bytes() == (
            ROOT / "src" / "normshift" / "schemas" / name
        ).read_bytes()


def test_authoritative_m0_manifest_schema_caps_status_at_pending_audit() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "package_manifest_v1.schema.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["status"]["properties"]["m0"] == {
        "const": "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT"
    }
    assert schema["$defs"]["git_oid"]["pattern"] == "^[0-9a-f]{40}$"


def test_verifier_ok_is_explicitly_preflight_not_external_audit() -> None:
    summary = pv._State().summary(
        run_id="20260809T000000Z-test",
        schema_version=pv.MANIFEST_VERSION,
    )

    assert summary["ok"] is True
    assert summary["verification_scope"] == "PACKAGE_PREFLIGHT_ONLY"
    assert summary["external_audit_verdict"] == "NOT_EVALUATED"
    assert summary["release_status"] == "BLOCKED"


def test_verifier_accepts_builder_path_sorted_checksums(tmp_path: Path) -> None:
    first = tmp_path / "NormShift.txt"
    second = tmp_path / "evidence.txt"
    first.write_bytes(b"a")
    second.write_bytes(b"z")
    checksum = package_build._write_checksums(
        tmp_path,
        "candidate-CHECKSUMS.txt",
        "candidate-MANIFEST.json",
    )
    emitted_paths = [line.split("  ", 1)[1] for line in checksum.read_text().splitlines()]
    assert emitted_paths == sorted(emitted_paths)
    manifest = {
        "artifacts": {
            "checksums": {
                "path": checksum.name,
                "sha256": pv.sha256_file(checksum),
                "size": checksum.stat().st_size,
            }
        },
        "logs": {},
        "files": {
            "first": {
                "path": first.name,
                "sha256": pv.sha256_file(first),
                "size": first.stat().st_size,
            },
            "second": {
                "path": second.name,
                "sha256": pv.sha256_file(second),
                "size": second.stat().st_size,
            },
        },
    }
    state = pv._State()

    pv._verify_checksums(manifest, checksum, state)

    assert state.error_count == 0, state.errors


def test_distribution_install_uses_retained_hashed_runtime_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / "normshift.whl"
    requirements = tmp_path / "runtime-requirements.txt"
    artifact.write_bytes(b"wheel")
    requirements.write_text("dependency==1 --hash=sha256:" + "a" * 64, encoding="utf-8")
    commands: list[list[str]] = []

    def fake_run_checked(
        command: list[str],
        *,
        cwd: Path | None = None,
        timeout: int = 300,
        env: dict[str, str] | None = None,
    ) -> str:
        del cwd, timeout, env
        commands.append(command)
        return ""

    monkeypatch.setattr(pv, "_run_checked", fake_run_checked)

    pv._install_distribution("uv", artifact, requirements, tmp_path / "venv")

    assert commands[1] == [
        "uv",
        "pip",
        "install",
        "--python",
        str(pv._environment_python(tmp_path / "venv")),
        "--require-hashes",
        "--requirements",
        str(requirements),
    ]
    assert commands[2] == [
        "uv",
        "pip",
        "install",
        "--python",
        str(pv._environment_python(tmp_path / "venv")),
        "--no-deps",
        str(artifact),
    ]


def test_required_gate_rejects_fabricated_true_command() -> None:
    manifest = {
        "archive": {"prefix": "NormShift-test/"},
        "package_commit": "a" * 40,
    }

    assert not pv._gate_argv_is_authoritative("pytest", ["true"], manifest)
    assert pv._gate_argv_is_authoritative(
        "ruff",
        ["uv", "run", "--frozen", "ruff", "check", "."],
        manifest,
    )


@pytest.mark.parametrize(
    ("gate", "argv"),
    [
        ("dependency_sync", ["uv", "sync", "--frozen", "--all-extras", "--dev"]),
        ("ruff", ["uv", "run", "--frozen", "ruff", "check", "."]),
        ("mypy", ["uv", "run", "--frozen", "mypy", "src"]),
        (
            "pytest",
            [
                "uv",
                "run",
                "--frozen",
                "pytest",
                "-q",
                "-rxX",
                "-p",
                "no:cacheprovider",
                "--junitxml=C:/x.xml",
            ],
        ),
        (
            "r4_r5",
            [
                "uv",
                "run",
                "--frozen",
                "pytest",
                "-q",
                "-rxX",
                "-p",
                "no:cacheprovider",
                "tests/e2e/test_m0_repair_round4.py",
                "tests/e2e/test_m0_repair_round5.py",
                "--junitxml=C:/x.xml",
            ],
        ),
        (
            "benchmark",
            [
                "uv",
                "run",
                "--frozen",
                "normshift",
                "benchmark",
                "--ground-truth",
                "benchmark/ground_truth.jsonl",
            ],
        ),
        (
            "measure",
            [
                "uv",
                "run",
                "--frozen",
                "normshift",
                "measure",
                "--ground-truth",
                "benchmark/measure_suite.jsonl",
                "--out",
                "C:/metrics.json",
            ],
        ),
        (
            "diff",
            [
                "uv",
                "run",
                "--frozen",
                "normshift",
                "diff",
                "fixtures/synthetic/spec-v1.html",
                "fixtures/synthetic/spec-v2.html",
                "--source-root",
                ".",
                "--profile",
                "rfc2119",
                "--json",
                "C:/report.json",
                "--markdown",
                "C:/report.md",
            ],
        ),
        (
            "verify",
            [
                "uv",
                "run",
                "--frozen",
                "normshift",
                "verify",
                "C:/report.json",
                "--source-root",
                ".",
            ],
        ),
        ("bundle", ["git", "bundle", "create", "C:/subject.bundle", "HEAD"]),
        (
            "source_archive",
            [
                "git",
                "archive",
                "--format=zip",
                "--prefix=NormShift-test/",
                "--output=C:/Source.zip",
                "a" * 40,
            ],
        ),
        ("build", ["uv", "build", "--out-dir", "C:/dist", "--no-create-gitignore"]),
        (
            "sbom",
            [
                "uv",
                "export",
                "--frozen",
                "--no-dev",
                "--no-editable",
                "--format",
                "cyclonedx1.5",
                "--preview-features",
                "sbom-export",
                "--output-file",
                "C:/sbom.json",
            ],
        ),
    ],
)
def test_builder_required_gate_argv_shapes_are_authoritative(
    gate: str,
    argv: list[str],
) -> None:
    manifest = {
        "archive": {"prefix": "NormShift-test/"},
        "package_commit": "a" * 40,
    }

    assert pv._gate_argv_is_authoritative(gate, argv, manifest)


def test_package_tree_rejects_undeclared_sibling_file(tmp_path: Path) -> None:
    manifest_path = tmp_path / "candidate-MANIFEST.json"
    manifest_path.write_text("{}", encoding="utf-8")
    (tmp_path / "undeclared.bin").write_bytes(b"not bound")
    manifest = {"artifacts": {}, "logs": {}, "files": {}}
    state = pv._State()

    pv._verify_package_tree(manifest, manifest_path, state)

    assert state.error_count > 0
    assert any("undeclared.bin" in error for error in state.errors)


def test_distribution_provenance_rejects_bytes_not_rebuilt_from_source_zip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    source_zip = tmp_path / "Source.zip"
    source_zip.write_bytes(b"zip")
    wheel = tmp_path / "normshift-1.2.3-py3-none-any.whl"
    sdist = tmp_path / "normshift-1.2.3.tar.gz"
    wheel.write_bytes(b"candidate-wheel")
    sdist.write_bytes(b"candidate-sdist")

    monkeypatch.setattr(pv.shutil, "which", lambda _name: "uv")
    monkeypatch.setattr(
        pv,
        "_extract_preflighted_source",
        lambda _source, _destination, _prefix: source_root,
    )
    monkeypatch.setattr(pv, "_git", lambda *_args: "1750000000")

    def fake_run_checked(
        command: list[str],
        *,
        cwd: Path | None = None,
        timeout: int = 300,
        env: dict[str, str] | None = None,
    ) -> str:
        del cwd, timeout
        assert env is not None and env["SOURCE_DATE_EPOCH"] == "1750000000"
        output = Path(command[command.index("--out-dir") + 1])
        output.mkdir()
        (output / wheel.name).write_bytes(b"rebuilt-wheel")
        (output / sdist.name).write_bytes(b"rebuilt-sdist")
        return ""

    monkeypatch.setattr(pv, "_run_checked", fake_run_checked)
    canonical_checks: list[Path] = []
    normalized_rebuilds: list[tuple[Path, Path]] = []

    def fake_normalize(source: Path, output: Path) -> None:
        normalized_rebuilds.append((source, output))
        output.write_bytes(source.read_bytes())

    monkeypatch.setattr(pv, "assert_canonical_wheel_file", canonical_checks.append)
    monkeypatch.setattr(pv, "normalize_wheel_file", fake_normalize)
    state = pv._State()
    pv._verify_distribution_provenance(
        source_root,
        {
            "package_commit": "a" * 40,
            "archive": {"prefix": "NormShift-test/"},
            "environment": {"source_date_epoch": "1750000000"},
        },
        {("artifacts", "wheel"): wheel, ("artifacts", "sdist"): sdist},
        source_zip,
        state,
    )

    assert state.error_count == 2
    assert all("differs from the exact Source.zip rebuild" in error for error in state.errors)
    assert canonical_checks == [wheel]
    assert [(source.name, output.name) for source, output in normalized_rebuilds] == [
        (wheel.name, wheel.name)
    ]


def test_sbom_graph_comparison_detects_missing_transitive_component() -> None:
    full = {
        "components": [
            {"name": "direct", "version": "1", "bom-ref": "direct@1"},
            {"name": "transitive", "version": "2", "bom-ref": "transitive@2"},
        ],
        "dependencies": [
            {"ref": "direct@1", "dependsOn": ["transitive@2"]},
            {"ref": "transitive@2"},
        ],
    }
    incomplete = {
        "components": [{"name": "direct", "version": "1", "bom-ref": "direct@1"}],
        "dependencies": [{"ref": "direct@1"}],
    }

    assert pv._normalized_sbom_graph(full) != pv._normalized_sbom_graph(incomplete)
