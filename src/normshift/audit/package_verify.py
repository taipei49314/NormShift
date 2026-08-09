"""Fail-closed preflight verification for an external NormShift package manifest.

The verifier validates checksummed command envelopes without re-running the build
gates, then independently verifies the Git bundle, Source.zip, distributions,
installed CLI/schema metadata, retained counts/matrices, and relocated report replay.
An ``ok`` result is package preflight only; it never grants an external-audit or
release verdict.
"""

from __future__ import annotations

import ast
import email.policy
import hashlib
import importlib.metadata
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unicodedata
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

from jsonschema import Draft202012Validator, FormatChecker
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

JsonObject = dict[str, Any]

MANIFEST_VERSION = "normshift-package-manifest/v1"
COMMAND_LOG_VERSION = "normshift-command-log/v1"
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_JSON_FILE_BYTES = 32 * 1024 * 1024
MAX_ZIP_MEMBERS = 100_000
MAX_ZIP_FILE_BYTES = 512 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 4 * 1024 * 1024 * 1024
MAX_REPORTED_ERRORS = 32
MAX_ERROR_CHARS = 400
BENCHMARK_REQUIRED_TOTAL = 17
MEASURE_REQUIRED_TOTAL = 15
REQUIRED_GATES = frozenset(
    {
        "dependency_sync",
        "ruff",
        "mypy",
        "pytest",
        "benchmark",
        "measure",
        "diff",
        "verify",
        "r4_r5",
        "bundle",
        "source_archive",
        "build",
        "sbom",
    }
)


def _has_output_option(argv: list[str], prefix: str) -> bool:
    return sum(item.startswith(prefix) and len(item) > len(prefix) for item in argv) == 1


def _gate_argv_is_authoritative(
    gate: str,
    argv: list[str],
    manifest: JsonObject,
) -> bool:
    exact: dict[str, list[str]] = {
        "dependency_sync": ["uv", "sync", "--frozen", "--all-extras", "--dev"],
        "ruff": ["uv", "run", "--frozen", "ruff", "check", "."],
        "mypy": ["uv", "run", "--frozen", "mypy", "src"],
        "benchmark": [
            "uv",
            "run",
            "--frozen",
            "normshift",
            "benchmark",
            "--ground-truth",
            "benchmark/ground_truth.jsonl",
        ],
    }
    if gate in exact:
        return argv == exact[gate]
    if gate == "pytest":
        return (
            len(argv) == 9
            and argv[:8]
            == [
                "uv",
                "run",
                "--frozen",
                "pytest",
                "-q",
                "-rxX",
                "-p",
                "no:cacheprovider",
            ]
            and _has_output_option(argv, "--junitxml=")
        )
    if gate == "r4_r5":
        return (
            len(argv) == 11
            and argv[:8]
            == [
                "uv",
                "run",
                "--frozen",
                "pytest",
                "-q",
                "-rxX",
                "-p",
                "no:cacheprovider",
            ]
            and argv[8:10]
            == [
                "tests/e2e/test_m0_repair_round4.py",
                "tests/e2e/test_m0_repair_round5.py",
            ]
            and _has_output_option(argv, "--junitxml=")
        )
    if gate == "measure":
        return (
            len(argv) == 9
            and argv[:8]
            == [
                "uv",
                "run",
                "--frozen",
                "normshift",
                "measure",
                "--ground-truth",
                "benchmark/measure_suite.jsonl",
                "--out",
            ]
            and bool(argv[8])
        )
    if gate == "diff":
        return (
            len(argv) == 15
            and argv[:7]
            == [
                "uv",
                "run",
                "--frozen",
                "normshift",
                "diff",
                "fixtures/synthetic/spec-v1.html",
                "fixtures/synthetic/spec-v2.html",
            ]
            and argv[7:12] == ["--source-root", ".", "--profile", "rfc2119", "--json"]
            and bool(argv[12])
            and argv[13] == "--markdown"
            and bool(argv[14])
        )
    if gate == "verify":
        return (
            len(argv) == 8
            and argv[:5] == ["uv", "run", "--frozen", "normshift", "verify"]
            and bool(argv[5])
            and argv[6:] == ["--source-root", "."]
        )
    if gate == "bundle":
        return (
            len(argv) == 5
            and argv[:3] == ["git", "bundle", "create"]
            and argv[4] == "HEAD"
        )
    if gate == "source_archive":
        archive = manifest["archive"]
        assert isinstance(archive, dict)
        return (
            len(argv) == 6
            and argv[:3] == ["git", "archive", "--format=zip"]
            and argv[3] == f"--prefix={archive['prefix']}"
            and argv[4].startswith("--output=")
            and argv[5] == manifest["package_commit"]
        )
    if gate == "build":
        return (
            len(argv) == 5
            and argv[:3] == ["uv", "build", "--out-dir"]
            and bool(argv[3])
            and argv[4] == "--no-create-gitignore"
        )
    if gate == "sbom":
        return (
            len(argv) == 11
            and argv[:10]
            == [
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
            ]
            and bool(argv[10])
        )
    return False


class StrictJsonError(ValueError):
    """Raised for duplicate keys or non-standard JSON values."""


@dataclass
class _State:
    errors: list[str] = field(default_factory=list)
    error_count: int = 0
    checks: dict[str, bool] = field(default_factory=dict)

    def fail(self, check: str, message: str) -> None:
        self.error_count += 1
        self.checks[check] = False
        if len(self.errors) < MAX_REPORTED_ERRORS:
            clean = " ".join(str(message).split())
            self.errors.append(f"{check}: {clean[:MAX_ERROR_CHARS]}")

    def pass_check(self, check: str) -> None:
        self.checks.setdefault(check, True)

    def summary(self, *, run_id: str | None, schema_version: str | None) -> JsonObject:
        return {
            "schema_version": schema_version,
            "run_id": run_id,
            "verification_scope": "PACKAGE_PREFLIGHT_ONLY",
            "external_audit_verdict": "NOT_EVALUATED",
            "release_status": "BLOCKED",
            "ok": self.error_count == 0,
            "error_count": self.error_count,
            "errors": self.errors,
            "errors_truncated": self.error_count > len(self.errors),
            "checks": dict(sorted(self.checks.items())),
        }


def _duplicate_rejector(pairs: list[tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise StrictJsonError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise StrictJsonError(f"non-finite JSON constant: {value}")


def _parse_int(value: str) -> int:
    if value == "-0":
        raise StrictJsonError("negative zero integer token")
    return int(value)


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise StrictJsonError(f"non-finite JSON number: {value}")
    if parsed == 0.0 and math.copysign(1.0, parsed) < 0:
        raise StrictJsonError(f"negative zero JSON number: {value}")
    return parsed


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise StrictJsonError(f"non-finite number at {path}")
    if isinstance(value, float) and value == 0.0 and math.copysign(1.0, value) < 0:
        raise StrictJsonError(f"negative zero at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_non_finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_non_finite(child, f"{path}[{index}]")


def _strict_json_bytes(raw: bytes, *, label: str) -> JsonObject:
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_rejector,
            parse_constant=_reject_constant,
            parse_int=_parse_int,
            parse_float=_parse_float,
        )
        _reject_non_finite(value)
    except (UnicodeDecodeError, json.JSONDecodeError, StrictJsonError) as exc:
        raise StrictJsonError(f"{label}: {exc}") from exc
    if not isinstance(value, dict):
        raise StrictJsonError(f"{label}: top level must be an object")
    return value


def _read_json(path: Path, *, label: str, limit: int) -> JsonObject:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise StrictJsonError(f"{label}: cannot stat file: {exc}") from exc
    if size > limit:
        raise StrictJsonError(f"{label}: file exceeds {limit} byte limit")
    try:
        return _strict_json_bytes(path.read_bytes(), label=label)
    except OSError as exc:
        raise StrictJsonError(f"{label}: cannot read file: {exc}") from exc


def _schema_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "schemas" / name


def _load_schema(name: str) -> JsonObject:
    return _read_json(
        _schema_path(name), label=f"built-in schema {name}", limit=MAX_JSON_FILE_BYTES
    )


def _schema_errors(instance: JsonObject, schema: JsonObject) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        errors.append(f"{path}: {error.message}")
    return errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def _portable_record_path(base: Path, raw: str) -> Path:
    if "\\" in raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ValueError("path must be relative POSIX form")
    pure = PurePosixPath(raw)
    if not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("path contains an empty, dot, or traversal component")
    base_resolved = base.resolve(strict=True)
    candidate = base_resolved.joinpath(*pure.parts)
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError("path resolves outside the manifest directory") from exc
    if os.path.normcase(str(candidate.absolute())) != os.path.normcase(str(resolved)):
        raise ValueError("path traverses a symlink or non-canonical alias")
    if not resolved.is_file() or not stat.S_ISREG(resolved.stat().st_mode):
        raise ValueError("path is not a regular file")
    return resolved


def _verify_file_records(
    manifest: JsonObject,
    manifest_dir: Path,
    state: _State,
) -> dict[tuple[str, str], Path]:
    resolved: dict[tuple[str, str], Path] = {}
    used_paths: dict[str, str] = {}
    for table_name in ("artifacts", "logs", "files"):
        table = manifest[table_name]
        assert isinstance(table, dict)
        for record_id, raw_record in table.items():
            assert isinstance(record_id, str) and isinstance(raw_record, dict)
            label = f"{table_name}.{record_id}"
            try:
                path = _portable_record_path(manifest_dir, str(raw_record["path"]))
            except (OSError, ValueError) as exc:
                state.fail("declared_files", f"{label}: {exc}")
                continue
            collision_key = unicodedata.normalize("NFC", str(raw_record["path"])).casefold()
            previous = used_paths.get(collision_key)
            if previous is not None:
                state.fail("declared_files", f"{label} aliases already declared {previous}")
            else:
                used_paths[collision_key] = label
            try:
                actual_size = path.stat().st_size
                actual_sha = sha256_file(path)
            except OSError as exc:
                state.fail("declared_files", f"{label}: cannot hash: {exc}")
                continue
            if actual_size != raw_record["size"]:
                state.fail(
                    "declared_files",
                    f"{label}: size {actual_size} != declared {raw_record['size']}",
                )
            if actual_sha != raw_record["sha256"]:
                state.fail("declared_files", f"{label}: sha256 mismatch")
            resolved[(table_name, record_id)] = path
    state.pass_check("declared_files")
    return resolved


def _verify_package_tree(
    manifest: JsonObject,
    manifest_path: Path,
    state: _State,
) -> None:
    allowed = {manifest_path.name}
    for table_name in ("artifacts", "logs", "files"):
        table = manifest[table_name]
        assert isinstance(table, dict)
        allowed.update(str(record["path"]) for record in table.values())
    actual: set[str] = set()
    try:
        for path in manifest_path.parent.rglob("*"):
            if path.is_symlink():
                state.fail(
                    "package_tree",
                    f"package directory contains symlink: {path.relative_to(manifest_path.parent)}",
                )
                continue
            if path.is_file():
                actual.add(path.relative_to(manifest_path.parent).as_posix())
    except OSError as exc:
        state.fail("package_tree", f"cannot enumerate package directory: {exc}")
    if actual != allowed:
        missing = sorted(allowed - actual)
        extra = sorted(actual - allowed)
        state.fail(
            "package_tree",
            f"package file set mismatch missing={missing[:5]} extra={extra[:5]}",
        )
    state.pass_check("package_tree")


def _verify_checksums(manifest: JsonObject, checksum_path: Path, state: _State) -> None:
    expected: dict[str, str] = {}
    for table_name in ("artifacts", "logs", "files"):
        table = manifest[table_name]
        assert isinstance(table, dict)
        for record_id, record in table.items():
            assert isinstance(record, dict)
            if table_name == "artifacts" and record_id == "checksums":
                continue
            path = str(record["path"])
            if path in expected:
                state.fail("checksums", f"duplicate declared checksum path: {path}")
            expected[path] = str(record["sha256"])
    try:
        lines = checksum_path.read_text(encoding="utf-8", errors="strict").splitlines()
        observed: dict[str, str] = {}
        observed_paths: list[str] = []
        for line in lines:
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            if match is None:
                raise ValueError(f"malformed checksum line: {line!r}")
            digest, raw_path = match.groups()
            _safe_zip_name(raw_path, directory=False)
            if raw_path in observed:
                raise ValueError(f"duplicate checksum path: {raw_path}")
            observed[raw_path] = digest
            observed_paths.append(raw_path)
        if observed_paths != sorted(observed_paths):
            state.fail("checksums", "checksum paths are not sorted")
        checksum_name = str(manifest["artifacts"]["checksums"]["path"])
        manifest_names = {
            path.name for path in checksum_path.parent.glob("*-MANIFEST.json") if path.is_file()
        }
        if checksum_name in observed or manifest_names & set(observed):
            state.fail("checksums", "checksums must not self-reference or include the manifest")
        if observed != expected:
            missing = sorted(set(expected) - set(observed))
            extra = sorted(set(observed) - set(expected))
            changed = sorted(
                key for key in set(expected) & set(observed) if expected[key] != observed[key]
            )
            state.fail(
                "checksums",
                f"checksum mapping mismatch missing={missing[:5]} extra={extra[:5]} "
                f"changed={changed[:5]}",
            )
    except (OSError, UnicodeError, ValueError) as exc:
        state.fail("checksums", str(exc))
    state.pass_check("checksums")


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    data: bytes | None = None,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=data,
        capture_output=True,
        check=False,
        timeout=timeout,
        env=env,
    )


def _git(repo: Path, *args: str) -> str:
    result = _run(["git", "-C", str(repo), *args])
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace")[-1000:]
        raise RuntimeError(f"git {' '.join(args)} failed ({result.returncode}): {detail}")
    return result.stdout.decode("ascii", errors="strict").strip()


def _normalized_git_remote(raw: str) -> str:
    if raw.startswith("git@github.com:"):
        raw = "https://github.com/" + raw.removeprefix("git@github.com:")
    normalized = raw.rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized.removesuffix(".git")
    return normalized


def _verify_repo_and_bundle(
    repo: Path,
    bundle_path: Path,
    manifest: JsonObject,
    state: _State,
) -> None:
    commit = str(manifest["package_commit"])
    tree = str(manifest["package_tree"])
    repository_claim = manifest["repository"]
    assert isinstance(repository_claim, dict)
    try:
        repo_head = _git(repo, "rev-parse", "--verify", "HEAD")
        repo_tree = _git(repo, "rev-parse", "--verify", "HEAD^{tree}")
        if repo_head != commit:
            state.fail("repository", f"HEAD {repo_head} != package_commit {commit}")
        if repo_tree != tree:
            state.fail("repository", f"tree {repo_tree} != package_tree {tree}")
        status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
        if status:
            state.fail("repository", "worktree is dirty")
        remote_url = _git(repo, "remote", "get-url", "origin")
        if _normalized_git_remote(remote_url) != _normalized_git_remote(
            str(repository_claim["url"])
        ):
            state.fail("repository", "origin URL differs from manifest repository.url")
        default_ref = f"refs/remotes/origin/{repository_claim['default_branch']}^{{commit}}"
        ref_result = _run(["git", "-C", str(repo), "rev-parse", "--verify", default_ref])
        if ref_result.returncode != 0 or (
            ref_result.stdout.decode("ascii", errors="strict").strip() != commit
        ):
            state.fail(
                "repository",
                "origin/default-branch ref does not resolve to package_commit",
            )
    except (OSError, RuntimeError, UnicodeError, subprocess.TimeoutExpired) as exc:
        state.fail("repository", str(exc))
    state.pass_check("repository")

    bundle_info = manifest["bundle"]
    assert isinstance(bundle_info, dict)
    if bundle_info["head"] != commit or bundle_info["tree"] != tree:
        state.fail("bundle", "declared bundle head/tree does not equal package identity")
    try:
        verify = _run(["git", "-C", str(repo), "bundle", "verify", str(bundle_path)])
        if verify.returncode != 0:
            state.fail(
                "bundle",
                "git bundle verify failed: "
                + verify.stderr.decode("utf-8", errors="replace")[-1000:],
            )
        with tempfile.TemporaryDirectory(prefix="normshift-bundle-") as tmp:
            clone = Path(tmp) / "clone"
            cloned = _run(["git", "clone", "--quiet", str(bundle_path), str(clone)])
            if cloned.returncode != 0:
                state.fail(
                    "bundle",
                    "bundle clone failed: "
                    + cloned.stderr.decode("utf-8", errors="replace")[-1000:],
                )
            else:
                clone_head = _git(clone, "rev-parse", "--verify", "HEAD")
                clone_tree = _git(clone, "rev-parse", "--verify", "HEAD^{tree}")
                if clone_head != commit:
                    state.fail("bundle", f"cloned HEAD {clone_head} != {commit}")
                if clone_tree != tree:
                    state.fail("bundle", f"cloned tree {clone_tree} != {tree}")
                fsck = _run(["git", "-C", str(clone), "fsck", "--full", "--strict"])
                if fsck.returncode != 0:
                    state.fail(
                        "bundle",
                        "git fsck --full --strict failed: "
                        + fsck.stderr.decode("utf-8", errors="replace")[-1000:],
                    )
    except (OSError, RuntimeError, UnicodeError, subprocess.TimeoutExpired) as exc:
        state.fail("bundle", str(exc))
    state.pass_check("bundle")


def _zip_member_kind(info: zipfile.ZipInfo) -> str:
    mode = info.external_attr >> 16
    file_type = stat.S_IFMT(mode)
    if info.is_dir() or file_type == stat.S_IFDIR:
        return "directory"
    if file_type in {0, stat.S_IFREG}:
        return "file"
    return "special"


def _safe_zip_name(name: str, *, directory: bool) -> str:
    if not name or "\x00" in name or "\\" in name:
        raise ValueError("empty/NUL/backslash member name")
    if name.startswith(("/", "//")) or re.match(r"^[A-Za-z]:", name):
        raise ValueError("absolute or rooted member name")
    candidate = name[:-1] if directory and name.endswith("/") else name
    parts = candidate.split("/")
    if not candidate or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("empty, dot, or traversal member component")
    if PurePosixPath(candidate).as_posix() != candidate:
        raise ValueError("non-canonical member name")
    return candidate


def _validate_zip_local_header(source: zipfile.ZipFile, info: zipfile.ZipInfo) -> None:
    try:
        with source.open(info):
            pass
    except (NotImplementedError, RuntimeError, zipfile.BadZipFile) as exc:
        raise ValueError(
            f"invalid local ZIP header for {info.orig_filename!r}: {exc}"
        ) from exc


def _git_tree(repo: Path, commit: str) -> dict[str, tuple[str, str]]:
    result = _run(["git", "-C", str(repo), "ls-tree", "-r", "-z", commit])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace")[-1000:])
    entries: dict[str, tuple[str, str]] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, path_bytes = raw.split(b"\t", 1)
        mode, object_type, oid = metadata.decode("ascii").split(" ")
        path = path_bytes.decode("utf-8", errors="strict")
        if object_type != "blob":
            raise RuntimeError(f"unsupported tracked entry type {object_type}: {path}")
        entries[path] = (mode, oid)
    return entries


def _verify_source_zip(
    repo: Path,
    source_zip: Path,
    manifest: JsonObject,
    state: _State,
) -> None:
    archive = manifest["archive"]
    assert isinstance(archive, dict)
    prefix = str(archive["prefix"])
    try:
        tracked = _git_tree(repo, str(manifest["package_commit"]))
        archived: dict[str, zipfile.ZipInfo] = {}
        seen_names: set[str] = set()
        seen_casefold: dict[str, str] = {}
        duplicate_count = 0
        unsafe_count = 0
        case_collision_count = 0
        total_size = 0
        with zipfile.ZipFile(source_zip) as source:
            infos = source.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                raise ValueError(f"archive has more than {MAX_ZIP_MEMBERS} members")
            for info in infos:
                kind = _zip_member_kind(info)
                original_name = info.orig_filename
                try:
                    canonical = _safe_zip_name(original_name, directory=kind == "directory")
                except ValueError as exc:
                    unsafe_count += 1
                    state.fail("source_zip", f"unsafe member {original_name!r}: {exc}")
                    continue
                if original_name in seen_names:
                    duplicate_count += 1
                    state.fail("source_zip", f"duplicate ZIP member: {original_name!r}")
                seen_names.add(original_name)
                folded = unicodedata.normalize("NFC", canonical).casefold()
                previous = seen_casefold.get(folded)
                if previous is not None and previous != canonical:
                    case_collision_count += 1
                    state.fail(
                        "source_zip",
                        f"case/Unicode collision: {previous!r} vs {canonical!r}",
                    )
                else:
                    seen_casefold[folded] = canonical
                if kind == "special":
                    unsafe_count += 1
                    state.fail("source_zip", f"symlink or special member: {original_name!r}")
                    continue
                if info.flag_bits & 0x1:
                    unsafe_count += 1
                    state.fail("source_zip", f"encrypted member: {original_name!r}")
                    continue
                try:
                    _validate_zip_local_header(source, info)
                except ValueError as exc:
                    unsafe_count += 1
                    state.fail("source_zip", str(exc))
                    continue
                prefix_root = prefix.rstrip("/")
                is_root_directory = kind == "directory" and canonical == prefix_root
                if not is_root_directory and not canonical.startswith(prefix_root + "/"):
                    unsafe_count += 1
                    state.fail(
                        "source_zip", f"member lacks canonical prefix {prefix!r}: {canonical!r}"
                    )
                    continue
                if kind == "directory":
                    continue
                if info.file_size > MAX_ZIP_FILE_BYTES:
                    raise ValueError(f"member exceeds size limit: {canonical}")
                total_size += info.file_size
                if total_size > MAX_ZIP_TOTAL_BYTES:
                    raise ValueError("archive uncompressed size exceeds limit")
                relative = canonical[len(prefix) :]
                if not relative:
                    unsafe_count += 1
                    state.fail("source_zip", f"file member equals prefix: {canonical!r}")
                    continue
                archived[relative] = info

            missing = sorted(set(tracked) - set(archived))
            extra = sorted(set(archived) - set(tracked))
            if missing:
                state.fail("source_zip", f"missing tracked files: {missing[:5]}")
            if extra:
                state.fail("source_zip", f"extra archive files: {extra[:5]}")
            for relative in sorted(set(tracked) & set(archived)):
                mode, expected_oid = tracked[relative]
                if mode == "120000":
                    state.fail("source_zip", f"tracked symlink is forbidden: {relative}")
                    continue
                data = source.read(archived[relative])
                blob = _run(["git", "-C", str(repo), "cat-file", "blob", expected_oid])
                if blob.returncode != 0:
                    state.fail("source_zip", f"git cat-file failed for {relative}")
                    continue
                if blob.stdout != data:
                    state.fail("source_zip", f"Git blob mismatch: {relative}")

        actuals = {
            "tracked_file_count": len(tracked),
            "archive_file_count": len(archived),
            "missing_count": len(set(tracked) - set(archived)),
            "extra_count": len(set(archived) - set(tracked)),
            "duplicate_count": duplicate_count,
            "unsafe_count": unsafe_count,
            "case_collision_count": case_collision_count,
        }
        for key, actual in actuals.items():
            if archive[key] != actual:
                state.fail("source_zip", f"archive.{key}={archive[key]} but observed {actual}")
    except (
        OSError,
        RuntimeError,
        UnicodeError,
        ValueError,
        zipfile.BadZipFile,
        subprocess.TimeoutExpired,
    ) as exc:
        state.fail("source_zip", str(exc))
    state.pass_check("source_zip")


def _validate_time_order(start: str, finish: str, *, label: str, state: _State) -> None:
    try:
        if _parse_utc(start) > _parse_utc(finish):
            state.fail("timestamps", f"{label}: started_at is after finished_at")
    except ValueError as exc:
        state.fail("timestamps", f"{label}: invalid timestamp: {exc}")


def _verify_phase_refs(manifest: JsonObject, state: _State) -> None:
    files = manifest["files"]
    assert isinstance(files, dict)
    for phase in ("m1", "m2"):
        scope = manifest[phase]
        assert isinstance(scope, dict)
        for field_name in ("corpus_refs", "ground_truth_refs"):
            refs = scope[field_name]
            assert isinstance(refs, list)
            if len(refs) != len(set(refs)):
                state.fail("phase_scope", f"{phase}.{field_name} contains duplicate IDs")
            for ref in refs:
                if ref not in files:
                    state.fail(
                        "phase_scope", f"{phase}.{field_name} references missing files.{ref}"
                    )
    pytest_counts = manifest["counts"]["pytest"]
    matrix = manifest["matrices"]["r4_r5"]
    sbom = manifest["sbom"]
    for label, ref in (
        ("counts.pytest.junit_file", pytest_counts["junit_file"]),
        ("matrices.r4_r5.junit_file", matrix["junit_file"]),
        ("sbom.runtime_requirements_file", sbom["runtime_requirements_file"]),
    ):
        if ref not in files:
            state.fail("phase_scope", f"{label} references missing files.{ref}")
    state.pass_check("phase_scope")


def _verify_determinism(
    manifest: JsonObject,
    resolved: dict[tuple[str, str], Path],
    state: _State,
) -> None:
    determinism = manifest["determinism"]
    assert isinstance(determinism, dict)
    for name, raw in determinism.items():
        assert isinstance(name, str) and isinstance(raw, dict)
        first_id = str(raw["first"])
        second_id = str(raw["second"])
        if first_id == second_id:
            state.fail("determinism", f"{name}: first and second must be distinct records")
            continue
        first = resolved.get(("files", first_id))
        second = resolved.get(("files", second_id))
        if first is None or second is None:
            state.fail("determinism", f"{name}: missing file reference")
            continue
        try:
            if first.read_bytes() != second.read_bytes():
                state.fail("determinism", f"{name}: retained output bytes differ")
        except OSError as exc:
            state.fail("determinism", f"{name}: cannot compare files: {exc}")
    state.pass_check("determinism")


def _verify_command_records(
    manifest: JsonObject,
    resolved: dict[tuple[str, str], Path],
    state: _State,
) -> dict[str, JsonObject]:
    timestamps = manifest["timestamps"]
    assert isinstance(timestamps, dict)
    _validate_time_order(
        str(timestamps["started_at"]),
        str(timestamps["finished_at"]),
        label="manifest",
        state=state,
    )
    commands = manifest["commands"]
    logs = manifest["logs"]
    assert isinstance(commands, list) and isinstance(logs, dict)
    command_ids: set[str] = set()
    gate_counts: dict[str, int] = {}
    envelopes: dict[str, JsonObject] = {}
    try:
        log_schema = _load_schema("command_log_v1.schema.json")
        Draft202012Validator.check_schema(log_schema)
    except Exception as exc:
        state.fail("commands", f"cannot load command-log schema: {exc}")
        return envelopes

    for raw_command in commands:
        assert isinstance(raw_command, dict)
        command_id = str(raw_command["id"])
        gate = str(raw_command["gate"])
        argv = [str(item) for item in raw_command["argv"]]
        if command_id in command_ids:
            state.fail("commands", f"duplicate command id: {command_id}")
        command_ids.add(command_id)
        gate_counts[gate] = gate_counts.get(gate, 0) + 1
        if raw_command["log"] != command_id:
            state.fail("commands", f"{command_id}: log ID must equal command ID")
        if gate in REQUIRED_GATES and raw_command["cwd"] != ".":
            state.fail(
                "commands",
                f"{command_id}: core gate cwd must be '.' under the declared policy",
            )
        if gate in REQUIRED_GATES and not _gate_argv_is_authoritative(gate, argv, manifest):
            state.fail(
                "commands",
                f"{command_id}: argv does not match the authoritative {gate} gate",
            )
        if raw_command["exit_code"] != 0:
            state.fail("commands", f"{command_id}: required command exit is non-zero")
        _validate_time_order(
            str(raw_command["started_at"]),
            str(raw_command["finished_at"]),
            label=f"command {command_id}",
            state=state,
        )
        log_path = resolved.get(("logs", command_id))
        if log_path is None:
            state.fail("commands", f"{command_id}: missing retained log")
            continue
        try:
            envelope = _read_json(
                log_path,
                label=f"command log {command_id}",
                limit=MAX_JSON_FILE_BYTES,
            )
        except StrictJsonError as exc:
            state.fail("commands", str(exc))
            continue
        for error in _schema_errors(envelope, log_schema):
            state.fail("commands", f"{command_id} {error}")
        comparisons = {
            "command_id": raw_command["id"],
            "gate": raw_command["gate"],
            "required": raw_command["required"],
            "argv": raw_command["argv"],
            "cwd": raw_command["cwd"],
            "started_at": raw_command["started_at"],
            "finished_at": raw_command["finished_at"],
            "exit_code": raw_command["exit_code"],
        }
        for key, expected in comparisons.items():
            if envelope.get(key) != expected:
                state.fail("commands", f"{command_id}: log {key} differs from manifest")
        envelopes[command_id] = envelope

    if set(logs) != command_ids:
        missing = sorted(command_ids - set(logs))
        extra = sorted(set(logs) - command_ids)
        state.fail("commands", f"log/command ID set mismatch missing={missing} extra={extra}")
    for gate in sorted(REQUIRED_GATES):
        count = gate_counts.get(gate, 0)
        if count != 1:
            state.fail("commands", f"required gate {gate!r} occurs {count} times (expected 1)")
    state.pass_check("commands")
    state.pass_check("timestamps")
    return envelopes


def _envelope_for_gate(
    manifest: JsonObject,
    envelopes: dict[str, JsonObject],
    gate: str,
) -> JsonObject | None:
    commands = manifest["commands"]
    assert isinstance(commands, list)
    matches = [item for item in commands if isinstance(item, dict) and item.get("gate") == gate]
    if len(matches) != 1:
        return None
    command_id = str(matches[0]["id"])
    return envelopes.get(command_id)


def _pytest_observed(text: str) -> dict[str, int] | None:
    tail = text[-32768:]
    observed: dict[str, int] = {}
    patterns = {
        "passed": r"(\d+)\s+passed\b",
        "failed": r"(\d+)\s+failed\b",
        "skipped": r"(\d+)\s+skipped\b",
        "xfailed": r"(\d+)\s+xfailed\b",
        "xpassed": r"(\d+)\s+xpassed\b",
        "errors": r"(\d+)\s+errors?\b",
    }
    found_any = False
    for name, pattern in patterns.items():
        matches = re.findall(pattern, tail, flags=re.IGNORECASE)
        observed[name] = int(matches[-1]) if matches else 0
        found_any = found_any or bool(matches)
    if not found_any:
        return None
    collected_matches = re.findall(r"collected\s+(\d+)\s+items?", tail, flags=re.IGNORECASE)
    observed["collected"] = (
        int(collected_matches[-1])
        if collected_matches
        else sum(observed[name] for name in patterns)
    )
    return observed


def _command_text(envelope: JsonObject) -> str:
    return f"{envelope.get('stdout', '')}\n{envelope.get('stderr', '')}"


def _junit_observed(path: Path) -> tuple[dict[str, int], list[str]]:
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise ValueError(f"invalid retained JUnit XML: {exc}") from exc
    counts = {
        "collected": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "errors": 0,
    }
    passed_ids: list[str] = []
    for case in root.iter("testcase"):
        classname = case.attrib.get("classname")
        name = case.attrib.get("name")
        if not classname or not name:
            raise ValueError("JUnit testcase lacks classname/name")
        counts["collected"] += 1
        if case.find("failure") is not None:
            counts["failed"] += 1
        elif case.find("error") is not None:
            counts["errors"] += 1
        elif (skipped := case.find("skipped")) is not None:
            if skipped.attrib.get("type") == "pytest.xfail":
                counts["xfailed"] += 1
            else:
                counts["skipped"] += 1
        else:
            counts["passed"] += 1
            passed_ids.append(f"{classname.replace('.', '/')}.py::{name}")
    return counts, passed_ids


def _verify_counts(
    manifest: JsonObject,
    envelopes: dict[str, JsonObject],
    state: _State,
    resolved: dict[tuple[str, str], Path] | None = None,
) -> None:
    counts = manifest["counts"]
    assert isinstance(counts, dict)
    pytest_counts = counts["pytest"]
    assert isinstance(pytest_counts, dict)
    pytest_envelope = _envelope_for_gate(manifest, envelopes, "pytest")
    if pytest_envelope is None:
        state.fail("counts", "pytest command envelope is unavailable")
    else:
        observed = _pytest_observed(_command_text(pytest_envelope))
        if observed is None:
            state.fail("counts", "pytest summary could not be parsed from retained log")
        else:
            for key in ("collected", "passed", "failed", "skipped", "xfailed", "xpassed", "errors"):
                if pytest_counts[key] != observed[key]:
                    state.fail(
                        "counts",
                        f"pytest {key}={pytest_counts[key]} but log reports {observed[key]}",
                    )
    if pytest_counts["collected"] != pytest_counts["passed"]:
        state.fail("counts", "pytest gate requires every collected test to pass")
    for key in ("failed", "skipped", "xfailed", "xpassed", "errors"):
        if pytest_counts[key] != 0:
            state.fail("counts", f"pytest {key} must be zero")
    if resolved is not None:
        junit_path = resolved.get(("files", str(pytest_counts["junit_file"])))
        if junit_path is None:
            state.fail("counts", "retained complete-suite JUnit file is unavailable")
        else:
            try:
                junit_counts, _ = _junit_observed(junit_path)
                for key in (
                    "collected",
                    "passed",
                    "failed",
                    "skipped",
                    "xfailed",
                    "xpassed",
                    "errors",
                ):
                    if junit_counts[key] != pytest_counts[key]:
                        state.fail(
                            "counts",
                            f"pytest {key} differs from retained JUnit XML",
                        )
            except ValueError as exc:
                state.fail("counts", str(exc))

    benchmark = counts["benchmark"]
    assert isinstance(benchmark, dict)
    _verify_case_count_record(benchmark, label="benchmark", state=state)
    if benchmark["total"] != BENCHMARK_REQUIRED_TOTAL:
        state.fail("counts", f"benchmark must contain {BENCHMARK_REQUIRED_TOTAL} cases")
    benchmark_envelope = _envelope_for_gate(manifest, envelopes, "benchmark")
    if benchmark_envelope is None:
        state.fail("counts", "benchmark command envelope is unavailable")
    else:
        text = _command_text(benchmark_envelope)
        match = re.search(
            r"benchmark:\s*(\d+)/(\d+)\s+passed,\s*(\d+)\s+failed",
            text,
            flags=re.IGNORECASE,
        )
        if match is None:
            state.fail("counts", "benchmark summary could not be parsed")
        else:
            logged_passed, logged_total, logged_failed = map(int, match.groups())
            if (benchmark["passed"], benchmark["total"], benchmark["failed"]) != (
                logged_passed,
                logged_total,
                logged_failed,
            ):
                state.fail("counts", "benchmark counts differ from retained log")
        logged_cases = set(re.findall(r"^\[PASS\]\s+([^:\r\n]+):", text, re.MULTILINE))
        declared_cases = {str(item["id"]) for item in benchmark["cases"]}
        if logged_cases and logged_cases != declared_cases:
            state.fail("counts", "benchmark case IDs differ from retained log")

    measure = counts["measure"]
    assert isinstance(measure, dict)
    _verify_case_count_record(measure, label="measure", state=state)
    if measure["total"] != MEASURE_REQUIRED_TOTAL:
        state.fail("counts", f"measure must contain {MEASURE_REQUIRED_TOTAL} cases")
    measure_envelope = _envelope_for_gate(manifest, envelopes, "measure")
    if measure_envelope is None:
        state.fail("counts", "measure command envelope is unavailable")
    else:
        match = re.search(
            r"measure:\s*(\d+)/(\d+)\s+cases",
            _command_text(measure_envelope),
            flags=re.IGNORECASE,
        )
        if match is None:
            state.fail("counts", "measure summary could not be parsed")
        elif (measure["passed"], measure["total"]) != tuple(map(int, match.groups())):
            state.fail("counts", "measure counts differ from retained log")
    if resolved is not None:
        determinism = manifest["determinism"]
        assert isinstance(determinism, dict)
        metrics_ref = determinism["metrics"]
        assert isinstance(metrics_ref, dict)
        metrics_path = resolved.get(("files", str(metrics_ref["first"])))
        if metrics_path is None:
            state.fail("counts", "retained metrics file is unavailable")
        else:
            try:
                metrics = _read_json(
                    metrics_path,
                    label="retained measure metrics",
                    limit=MAX_JSON_FILE_BYTES,
                )
                raw_cases = metrics.get("case_results")
                if not isinstance(raw_cases, list):
                    raise ValueError("metrics case_results is absent")
                observed_cases = {
                    str(item.get("case_id")): item.get("passed") is True
                    for item in raw_cases
                    if isinstance(item, dict)
                }
                measure_declared_cases = {
                    str(item["id"]): item["passed"] is True for item in measure["cases"]
                }
                if observed_cases != measure_declared_cases:
                    state.fail("counts", "measure cases differ from retained metrics JSON")
                if (
                    metrics.get("case_count") != measure["total"]
                    or metrics.get("cases_passed") != measure["passed"]
                    or metrics.get("cases_failed") != measure["failed"]
                ):
                    state.fail("counts", "measure aggregates differ from retained metrics JSON")
                claimed_metrics = measure["metrics"]
                assert isinstance(claimed_metrics, dict)
                for layer in ("extraction", "alignment", "classification"):
                    actual_layer = metrics.get(layer)
                    if not isinstance(actual_layer, dict):
                        raise ValueError(f"metrics {layer} aggregate is absent")
                    expected_layer = claimed_metrics[layer]
                    assert isinstance(expected_layer, dict)
                    for metric in ("precision", "recall", "f1"):
                        if actual_layer.get(metric) != expected_layer[metric]:
                            state.fail(
                                "counts",
                                f"measure {layer}.{metric} differs from retained metrics JSON",
                            )
            except (OSError, StrictJsonError, ValueError) as exc:
                state.fail("counts", str(exc))
    state.pass_check("counts")


def _verify_case_count_record(record: JsonObject, *, label: str, state: _State) -> None:
    cases = record["cases"]
    assert isinstance(cases, list)
    ids = [str(item["id"]) for item in cases]
    passed = sum(1 for item in cases if item["passed"] is True)
    if len(ids) != len(set(ids)):
        state.fail("counts", f"{label} contains duplicate case IDs")
    if record["total"] != len(cases):
        state.fail("counts", f"{label}.total does not equal case count")
    if record["passed"] != passed or record["failed"] != len(cases) - passed:
        state.fail("counts", f"{label} aggregate counts do not match cases")
    if record["failed"] != 0 or passed != len(cases):
        state.fail("counts", f"{label} has a non-passing case")


def _expected_matrix_ids(repo: Path) -> set[str]:
    expected: set[str] = set()
    for relative in (
        "tests/e2e/test_m0_repair_round4.py",
        "tests/e2e/test_m0_repair_round5.py",
    ):
        path = repo / Path(relative)
        module = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
                "test_"
            ):
                expected.add(f"{relative}::{node.name}")
    return expected


def _verify_matrix(
    repo: Path,
    manifest: JsonObject,
    envelopes: dict[str, JsonObject],
    resolved: dict[tuple[str, str], Path],
    state: _State,
) -> None:
    matrices = manifest["matrices"]
    assert isinstance(matrices, dict)
    matrix = matrices["r4_r5"]
    assert isinstance(matrix, dict)
    cases = matrix["cases"]
    assert isinstance(cases, list)
    declared_ids = [str(item["id"]) for item in cases]
    if len(declared_ids) != len(set(declared_ids)):
        state.fail("matrix", "duplicate R4/R5 matrix case ID")
    try:
        expected_ids = _expected_matrix_ids(repo)
        if set(declared_ids) != expected_ids:
            missing = sorted(expected_ids - set(declared_ids))
            extra = sorted(set(declared_ids) - expected_ids)
            state.fail("matrix", f"R4/R5 matrix incomplete missing={missing[:5]} extra={extra[:5]}")
    except (OSError, SyntaxError, UnicodeError) as exc:
        state.fail("matrix", f"cannot derive required R4/R5 node IDs: {exc}")
    for case in cases:
        expected_exit = case["expected_exit"]
        actual_exit = case["actual_exit_code"]
        if expected_exit == "zero" and actual_exit != 0:
            state.fail("matrix", f"{case['id']}: expected zero exit, got {actual_exit}")
        if expected_exit == "nonzero" and actual_exit == 0:
            state.fail("matrix", f"{case['id']}: expected non-zero exit, got zero")
    matrix_log = str(matrix["log"])
    gate_envelope = _envelope_for_gate(manifest, envelopes, "r4_r5")
    if gate_envelope is None or gate_envelope.get("command_id") != matrix_log:
        state.fail("matrix", "matrix.log does not identify the r4_r5 command envelope")
    elif (observed := _pytest_observed(_command_text(gate_envelope))) is None:
        state.fail("matrix", "R4/R5 pytest summary could not be parsed")
    elif observed["passed"] != len(cases) or observed["collected"] != len(cases):
        state.fail("matrix", "R4/R5 log counts do not match declared complete matrix")
    elif any(observed[key] for key in ("failed", "skipped", "xfailed", "xpassed", "errors")):
        state.fail("matrix", "R4/R5 log includes a non-pass outcome")
    junit_path = resolved.get(("files", str(matrix["junit_file"])))
    if junit_path is None:
        state.fail("matrix", "retained R4/R5 JUnit file is unavailable")
    else:
        try:
            junit_counts, junit_ids = _junit_observed(junit_path)
            if set(junit_ids) != set(declared_ids) or len(junit_ids) != len(declared_ids):
                state.fail("matrix", "R4/R5 JUnit case IDs differ from the manifest")
            if junit_counts["collected"] != len(declared_ids) or junit_counts["passed"] != len(
                declared_ids
            ):
                state.fail("matrix", "R4/R5 JUnit does not contain all-pass outcomes")
            if any(
                junit_counts[key] for key in ("failed", "skipped", "xfailed", "xpassed", "errors")
            ):
                state.fail("matrix", "R4/R5 JUnit includes a non-pass outcome")
        except ValueError as exc:
            state.fail("matrix", str(exc))
    state.pass_check("matrix")


def _normal_requirements(values: list[str]) -> list[str]:
    runtime: list[str] = []
    for value in values:
        requirement = Requirement(value)
        if requirement.marker is not None and "extra" in str(requirement.marker):
            continue
        rendered: str = str(canonicalize_name(requirement.name))
        if requirement.extras:
            rendered += f"[{','.join(sorted(requirement.extras))}]"
        if requirement.url is not None:
            rendered += f" @ {requirement.url}"
        else:
            rendered += str(requirement.specifier)
        if requirement.marker is not None:
            rendered += f"; {requirement.marker}"
        runtime.append(rendered)
    return sorted(runtime)


def _lock_source(source: object) -> str:
    if not isinstance(source, dict) or not source:
        raise ValueError(f"unsupported uv.lock source: {source!r}")
    parts: list[str] = []
    for key, value in sorted(source.items()):
        if not isinstance(key, str) or not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"invalid uv.lock source: {source!r}")
        parts.append(f"{key}:{value}")
    return ";".join(parts)


def _lock_component_sources(lock_path: Path) -> dict[tuple[str, str], str]:
    lock_data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    packages = lock_data.get("package")
    if not isinstance(packages, list):
        raise ValueError("lockfile has no package inventory")
    inventory: dict[tuple[str, str], str] = {}
    for item in packages:
        if not isinstance(item, dict):
            raise ValueError("lockfile package is not an object")
        name = item.get("name")
        version = item.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise ValueError("lockfile package lacks name/version")
        key = (canonicalize_name(name), version)
        source = _lock_source(item.get("source"))
        previous = inventory.get(key)
        if previous is not None and previous != source:
            raise ValueError(f"ambiguous lock sources for {key}")
        inventory[key] = source
    return inventory


def _wheel_metadata(path: Path) -> tuple[str, str, list[str], str]:
    with zipfile.ZipFile(path) as wheel:
        names = wheel.namelist()
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        entry_names = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
        if len(metadata_names) != 1 or len(entry_names) != 1:
            raise ValueError("wheel must contain one METADATA and one entry_points.txt")
        for schema_name in (
            "normshift/schemas/package_manifest_v1.schema.json",
            "normshift/schemas/command_log_v1.schema.json",
        ):
            if schema_name not in names:
                raise ValueError(f"wheel omits packaged schema {schema_name}")
        message = BytesParser(policy=email.policy.default).parsebytes(wheel.read(metadata_names[0]))
        entry_points = wheel.read(entry_names[0]).decode("utf-8", errors="strict")
    name = str(message.get("Name", ""))
    version = str(message.get("Version", ""))
    requirements = _normal_requirements(list(message.get_all("Requires-Dist", [])))
    return name, version, requirements, entry_points


def _safe_tar_name(name: str) -> None:
    _safe_zip_name(name.rstrip("/"), directory=False)


def _sdist_metadata(path: Path) -> tuple[str, str, list[str]]:
    with tarfile.open(path, mode="r:*") as source:
        members = source.getmembers()
        if len(members) > MAX_ZIP_MEMBERS:
            raise ValueError("sdist has too many entries")
        metadata_members: list[tarfile.TarInfo] = []
        for member in members:
            _safe_tar_name(member.name)
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError(f"sdist contains link/special entry: {member.name}")
            if member.name.endswith("/PKG-INFO"):
                metadata_members.append(member)
        if len(metadata_members) != 1:
            raise ValueError("sdist must contain one top-level PKG-INFO")
        handle = source.extractfile(metadata_members[0])
        if handle is None:
            raise ValueError("cannot read sdist PKG-INFO")
        raw = handle.read(MAX_JSON_FILE_BYTES + 1)
        if len(raw) > MAX_JSON_FILE_BYTES:
            raise ValueError("sdist PKG-INFO exceeds size limit")
    message = BytesParser(policy=email.policy.default).parsebytes(raw)
    name = str(message.get("Name", ""))
    version = str(message.get("Version", ""))
    requirements = _normal_requirements(list(message.get_all("Requires-Dist", [])))
    return name, version, requirements


def _verify_distribution_metadata(
    repo: Path,
    manifest: JsonObject,
    resolved: dict[tuple[str, str], Path],
    state: _State,
) -> None:
    wheel = resolved.get(("artifacts", "wheel"))
    sdist = resolved.get(("artifacts", "sdist"))
    if wheel is None or sdist is None:
        state.fail("distribution_metadata", "wheel or sdist artifact is unavailable")
        return
    sbom_claim = manifest["sbom"]
    assert isinstance(sbom_claim, dict)
    declared = sbom_claim["distribution_requirements"]
    assert isinstance(declared, list)
    try:
        wheel_name, wheel_version, wheel_requirements, entry_points = _wheel_metadata(wheel)
        sdist_name, sdist_version, sdist_requirements = _sdist_metadata(sdist)
        expected_version = str(manifest["package_version"])
        if (
            canonicalize_name(wheel_name) != "normshift"
            or canonicalize_name(sdist_name) != "normshift"
        ):
            state.fail("distribution_metadata", "wheel/sdist root name is not normshift")
        if wheel_version != expected_version or sdist_version != expected_version:
            state.fail("distribution_metadata", "wheel/sdist version differs from manifest")
        if "normshift = normshift.cli:app" not in entry_points:
            state.fail("distribution_metadata", "wheel omits the normshift console entry point")
        if wheel_requirements != sdist_requirements:
            state.fail("distribution_metadata", "wheel and sdist Requires-Dist differ")
        if list(declared) != sorted(set(declared)):
            state.fail("distribution_metadata", "declared requirements must be sorted and unique")
        if wheel_requirements != list(declared):
            state.fail("distribution_metadata", "distribution requirements differ from manifest")

        pyproject = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
        raw_project = pyproject.get("project")
        if not isinstance(raw_project, dict):
            raise ValueError("pyproject.toml has no project table")
        dependencies = raw_project.get("dependencies")
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) for item in dependencies
        ):
            raise ValueError("pyproject runtime dependencies are not a string list")
        project_requirements = _normal_requirements(dependencies)
        if project_requirements != wheel_requirements:
            state.fail(
                "distribution_metadata", "pyproject runtime dependencies differ from distributions"
            )

        lock_path = resolved.get(("files", "lockfile"))
        if lock_path is None:
            state.fail("distribution_metadata", "files.lockfile is required")
        else:
            locked_names = {name for name, _ in _lock_component_sources(lock_path)}
            direct_names = {
                canonicalize_name(Requirement(item).name) for item in wheel_requirements
            }
            missing_lock = sorted(direct_names - locked_names)
            if missing_lock:
                state.fail(
                    "distribution_metadata", f"direct dependencies absent from lock: {missing_lock}"
                )
    except (
        OSError,
        UnicodeError,
        ValueError,
        KeyError,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as exc:
        state.fail("distribution_metadata", str(exc))
    state.pass_check("distribution_metadata")


def _normalized_sbom_graph(sbom: JsonObject) -> tuple[list[str], list[tuple[str, tuple[str, ...]]]]:
    components = sbom.get("components")
    dependencies = sbom.get("dependencies")
    if not isinstance(components, list) or not isinstance(dependencies, list):
        raise ValueError("SBOM components/dependencies graph is absent")
    normalized_components = sorted(
        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for item in components
        if isinstance(item, dict)
    )
    if len(normalized_components) != len(components):
        raise ValueError("SBOM contains a non-object component")
    normalized_dependencies: list[tuple[str, tuple[str, ...]]] = []
    for item in dependencies:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            raise ValueError("SBOM contains an invalid dependency node")
        depends_on = item.get("dependsOn", [])
        if not isinstance(depends_on, list) or not all(
            isinstance(value, str) for value in depends_on
        ):
            raise ValueError("SBOM dependency node has invalid dependsOn values")
        normalized_dependencies.append((str(item["ref"]), tuple(sorted(depends_on))))
    return normalized_components, sorted(normalized_dependencies)


def _verify_sbom(
    manifest: JsonObject,
    resolved: dict[tuple[str, str], Path],
    state: _State,
    repo: Path | None = None,
) -> None:
    sbom_path = resolved.get(("artifacts", "sbom"))
    if sbom_path is None:
        state.fail("sbom", "SBOM artifact is unavailable")
        return
    claim = manifest["sbom"]
    assert isinstance(claim, dict)
    try:
        raw = sbom_path.read_bytes()
        if len(raw) > MAX_JSON_FILE_BYTES:
            raise ValueError("SBOM exceeds validation size limit")
        sbom = _strict_json_bytes(raw, label="CycloneDX SBOM")
        from cyclonedx.schema import SchemaVersion
        from cyclonedx.validation.json import JsonStrictValidator

        validation_error = JsonStrictValidator(SchemaVersion.V1_5).validate_str(
            raw.decode("utf-8", errors="strict")
        )
        if validation_error is not None:
            state.fail("sbom", f"CycloneDX 1.5 strict validation failed: {validation_error}")
        if (
            sbom.get("bomFormat") != claim["format"]
            or sbom.get("specVersion") != claim["spec_version"]
        ):
            state.fail("sbom", "CycloneDX format/specVersion differs from manifest")
        metadata = sbom.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError("SBOM metadata object is missing")
        root = metadata.get("component")
        if not isinstance(root, dict):
            raise ValueError("SBOM root component is missing")
        root_claim = claim["root"]
        assert isinstance(root_claim, dict)
        if root.get("name") != root_claim["name"] or root.get("version") != root_claim["version"]:
            state.fail("sbom", "SBOM root name/version differs from manifest")
        if root_claim["version"] != manifest["package_version"]:
            state.fail("sbom", "manifest SBOM root version differs from package_version")
        components = sbom.get("components")
        if not isinstance(components, list) or not components:
            raise ValueError("SBOM components inventory is empty")
        lock_path = resolved.get(("files", "lockfile"))
        if lock_path is None:
            raise ValueError("files.lockfile is required")
        lock_inventory = _lock_component_sources(lock_path)
        actual_inventory: list[tuple[str, str, str]] = []
        for component in components:
            if not isinstance(component, dict):
                raise ValueError("SBOM component is not an object")
            name = component.get("name")
            version = component.get("version")
            purl = component.get("purl")
            if not all(isinstance(item, str) and item for item in (name, version, purl)):
                raise ValueError("SBOM component lacks name/version/purl")
            assert isinstance(name, str)
            assert isinstance(version, str)
            key = (canonicalize_name(name), version)
            source = lock_inventory.get(key)
            if source is None:
                raise ValueError(f"SBOM component is absent from lockfile: {name} {version}")
            actual_inventory.append((name, version, source))
        if len(actual_inventory) != len(set(actual_inventory)):
            state.fail("sbom", "SBOM contains duplicate component inventory rows")
        inventory_claim = claim["inventory"]
        assert isinstance(inventory_claim, list)
        declared_inventory = [
            (str(item["name"]), str(item["version"]), str(item["source"]))
            for item in inventory_claim
        ]
        if declared_inventory != sorted(declared_inventory):
            state.fail("sbom", "manifest SBOM inventory must be sorted")
        if sorted(actual_inventory) != declared_inventory:
            state.fail("sbom", "CycloneDX component inventory differs from manifest")
        inventory_names = {canonicalize_name(name) for name, _, _ in actual_inventory}
        direct_names = {
            canonicalize_name(Requirement(item).name) for item in claim["distribution_requirements"]
        }
        if missing := sorted(direct_names - inventory_names):
            state.fail("sbom", f"direct dependencies absent from SBOM inventory: {missing}")
        lock_hash = sha256_file(lock_path)
        if lock_hash != claim["lockfile_sha256"]:
            state.fail("sbom", "SBOM lockfile_sha256 differs from retained lockfile")
        validator_claim = claim["validator"]
        assert isinstance(validator_claim, dict)
        actual_validator_version = importlib.metadata.version("cyclonedx-python-lib")
        if actual_validator_version != validator_claim["version"]:
            state.fail("sbom", "CycloneDX validator version differs from manifest")
        generator_claim = claim["generator"]
        assert isinstance(generator_claim, dict)
        tools = metadata.get("tools")
        if not isinstance(tools, list) or not any(
            isinstance(tool, dict)
            and tool.get("name") == generator_claim["name"]
            and tool.get("version") == generator_claim["version"]
            for tool in tools
        ):
            state.fail("sbom", "SBOM generator identity differs from manifest")
        if repo is not None:
            uv = shutil.which("uv")
            if uv is None:
                raise ValueError("uv is unavailable for frozen SBOM graph replay")
            with tempfile.TemporaryDirectory(prefix="normshift-sbom-replay-") as raw_tmp:
                replay_path = Path(raw_tmp) / "sbom.cdx.json"
                _run_checked(
                    [
                        uv,
                        "export",
                        "--frozen",
                        "--no-dev",
                        "--no-editable",
                        "--format",
                        "cyclonedx1.5",
                        "--preview-features",
                        "sbom-export",
                        "--output-file",
                        str(replay_path),
                    ],
                    cwd=repo,
                    timeout=600,
                    env=_subprocess_environment(),
                )
                replayed = _read_json(
                    replay_path,
                    label="fresh frozen CycloneDX SBOM",
                    limit=MAX_JSON_FILE_BYTES,
                )
                if _normalized_sbom_graph(sbom) != _normalized_sbom_graph(replayed):
                    state.fail("sbom", "SBOM runtime graph differs from a fresh frozen export")
    except (
        OSError,
        ImportError,
        RuntimeError,
        UnicodeError,
        ValueError,
        KeyError,
        StrictJsonError,
        subprocess.TimeoutExpired,
    ) as exc:
        state.fail("sbom", str(exc))
    state.pass_check("sbom")


def _environment_python(environment: Path) -> Path:
    return (
        environment / "Scripts" / "python.exe"
        if os.name == "nt"
        else environment / "bin" / "python"
    )


def _environment_entrypoint(environment: Path) -> Path:
    return (
        environment / "Scripts" / "normshift.exe"
        if os.name == "nt"
        else environment / "bin" / "normshift"
    )


def _subprocess_environment(*, source_date_epoch: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "COVERAGE_PROCESS_START",
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "UV_PROJECT_ENVIRONMENT",
        "VIRTUAL_ENV",
    ):
        env.pop(name, None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUTF8"] = "1"
    if source_date_epoch is not None:
        env["SOURCE_DATE_EPOCH"] = source_date_epoch
    return env


def _run_checked(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> str:
    result = _run(command, cwd=cwd, timeout=timeout, env=env)
    if result.returncode != 0:
        stdout = result.stdout.decode("utf-8", errors="replace")[-1000:]
        stderr = result.stderr.decode("utf-8", errors="replace")[-1000:]
        raise RuntimeError(
            f"command failed ({result.returncode}): {command!r}; "
            f"stdout={stdout!r}; stderr={stderr!r}"
        )
    return result.stdout.decode("utf-8", errors="strict")


def _install_distribution(
    uv: str,
    artifact: Path,
    runtime_requirements: Path,
    environment: Path,
) -> tuple[Path, Path]:
    env = _subprocess_environment()
    _run_checked(
        [uv, "venv", "--python", sys.executable, "--no-project", str(environment)],
        timeout=300,
        env=env,
    )
    python = _environment_python(environment)
    _run_checked(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(python),
            "--require-hashes",
            "--requirements",
            str(runtime_requirements),
        ],
        timeout=600,
        env=env,
    )
    _run_checked(
        [uv, "pip", "install", "--python", str(python), "--no-deps", str(artifact)],
        timeout=600,
        env=env,
    )
    entrypoint = _environment_entrypoint(environment)
    return python, entrypoint


def _verify_distribution_provenance(
    repo: Path,
    manifest: JsonObject,
    resolved: dict[tuple[str, str], Path],
    source_zip: Path,
    state: _State,
) -> None:
    uv = shutil.which("uv")
    wheel = resolved.get(("artifacts", "wheel"))
    sdist = resolved.get(("artifacts", "sdist"))
    if uv is None or wheel is None or sdist is None:
        state.fail("distribution_provenance", "uv, wheel, or sdist is unavailable")
        return
    archive = manifest["archive"]
    environment = manifest["environment"]
    assert isinstance(archive, dict) and isinstance(environment, dict)
    try:
        source_date_epoch = _git(
            repo,
            "show",
            "-s",
            "--format=%ct",
            str(manifest["package_commit"]),
        )
        if source_date_epoch != environment["source_date_epoch"]:
            raise ValueError("manifest SOURCE_DATE_EPOCH differs from the package commit")
        with tempfile.TemporaryDirectory(prefix="normshift-rebuild-") as raw_tmp:
            tmp = Path(raw_tmp)
            source_root = _extract_preflighted_source(
                source_zip,
                tmp / "source",
                str(archive["prefix"]),
            )
            output = tmp / "dist"
            _run_checked(
                [uv, "build", "--out-dir", str(output), "--no-create-gitignore"],
                cwd=source_root,
                timeout=900,
                env=_subprocess_environment(source_date_epoch=source_date_epoch),
            )
            rebuilt = sorted(path for path in output.iterdir() if path.is_file())
            expected_names = sorted((wheel.name, sdist.name))
            if [path.name for path in rebuilt] != expected_names:
                raise RuntimeError(
                    "exact Source.zip rebuild emitted unexpected distribution set: "
                    f"{[path.name for path in rebuilt]}"
                )
            for candidate in (wheel, sdist):
                rebuilt_path = output / candidate.name
                if (
                    rebuilt_path.stat().st_size != candidate.stat().st_size
                    or sha256_file(rebuilt_path) != sha256_file(candidate)
                ):
                    state.fail(
                        "distribution_provenance",
                        f"{candidate.name} differs from the exact Source.zip rebuild",
                    )
    except (
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
        subprocess.TimeoutExpired,
    ) as exc:
        state.fail("distribution_provenance", str(exc))
    state.pass_check("distribution_provenance")


def _runtime_smoke(python: Path, entrypoint: Path, expected_version: str) -> None:
    code = (
        "import importlib.metadata as m; import importlib.resources as r; "
        "assert m.version('normshift') == "
        + repr(expected_version)
        + "; eps=m.entry_points(group='console_scripts'); "
        "assert any(e.name=='normshift' and e.value=='normshift.cli:app' for e in eps); "
        "base=r.files('normshift.schemas'); "
        "assert base.joinpath('package_manifest_v1.schema.json').is_file(); "
        "assert base.joinpath('command_log_v1.schema.json').is_file()"
    )
    _run_checked([str(python), "-I", "-c", code])
    if not entrypoint.is_file():
        raise RuntimeError(f"installed console entry point is missing: {entrypoint}")
    _run_checked([str(entrypoint), "--help"])
    version_output = _run_checked([str(entrypoint), "--version"]).strip()
    if version_output != expected_version:
        raise RuntimeError(
            f"installed --version {version_output!r} != manifest {expected_version!r}"
        )


def _distribution_diff_verify(
    entrypoint: Path,
    source_root: Path,
    output_dir: Path,
    expected_scope: str,
) -> None:
    old_source = source_root / "fixtures" / "synthetic" / "spec-v1.html"
    new_source = source_root / "fixtures" / "synthetic" / "spec-v2.html"
    if not old_source.is_file() or not new_source.is_file():
        raise RuntimeError("Source.zip lacks the fixed isolated-smoke source fixtures")
    output_dir.mkdir(parents=True)
    report = output_dir / "report.json"
    _run_checked(
        [
            str(entrypoint),
            "diff",
            str(old_source),
            str(new_source),
            "--source-root",
            str(source_root),
            "--profile",
            "rfc2119",
            "--json",
            str(report),
        ],
        cwd=output_dir,
    )
    output = _run_checked(
        [
            str(entrypoint),
            "verify",
            str(report),
            "--source-root",
            str(source_root),
        ],
        cwd=output_dir,
    )
    if f"verification_scope={expected_scope}" not in output:
        raise RuntimeError("isolated distribution-generated report did not FULL-verify")


def _extract_preflighted_source(source_zip: Path, destination: Path, prefix: str) -> Path:
    with zipfile.ZipFile(source_zip) as source:
        for info in source.infolist():
            kind = _zip_member_kind(info)
            original_name = info.orig_filename
            canonical = _safe_zip_name(original_name, directory=kind == "directory")
            if kind == "special" or info.flag_bits & 0x1:
                raise ValueError(f"archive became unsafe before extraction: {original_name!r}")
            _validate_zip_local_header(source, info)
            prefix_root = prefix.rstrip("/")
            is_root_directory = kind == "directory" and canonical == prefix_root
            if not is_root_directory and not canonical.startswith(prefix_root + "/"):
                raise ValueError(f"archive became unsafe before extraction: {original_name!r}")
        source.extractall(destination)
    root = destination / prefix.rstrip("/")
    if not root.is_dir():
        raise ValueError("canonical source prefix was not extracted")
    return root


def _verify_installs_and_replay(
    manifest: JsonObject,
    resolved: dict[tuple[str, str], Path],
    source_zip: Path,
    state: _State,
) -> None:
    uv = shutil.which("uv")
    if uv is None:
        state.fail("isolated_install", "uv executable is unavailable")
        return
    wheel = resolved.get(("artifacts", "wheel"))
    sdist = resolved.get(("artifacts", "sdist"))
    if wheel is None or sdist is None:
        state.fail("isolated_install", "wheel or sdist artifact is unavailable")
        return
    sbom_claim = manifest["sbom"]
    assert isinstance(sbom_claim, dict)
    runtime_requirements = resolved.get(
        ("files", str(sbom_claim["runtime_requirements_file"]))
    )
    if runtime_requirements is None:
        state.fail("isolated_install", "retained hashed runtime requirements are unavailable")
        return
    expected_version = str(manifest["package_version"])
    archive = manifest["archive"]
    replay = manifest["replay"]
    assert isinstance(archive, dict) and isinstance(replay, dict)
    try:
        with tempfile.TemporaryDirectory(prefix="normshift-install-") as raw_tmp:
            tmp = Path(raw_tmp)
            wheel_python, wheel_entry = _install_distribution(
                uv,
                wheel,
                runtime_requirements,
                tmp / "wheel-env",
            )
            sdist_python, sdist_entry = _install_distribution(
                uv,
                sdist,
                runtime_requirements,
                tmp / "sdist-env",
            )
            _runtime_smoke(wheel_python, wheel_entry, expected_version)
            _runtime_smoke(sdist_python, sdist_entry, expected_version)
            extracted_root = _extract_preflighted_source(
                source_zip,
                tmp / "extracted",
                str(archive["prefix"]),
            )
            replay_path = extracted_root.joinpath(*PurePosixPath(str(replay["report_path"])).parts)
            if not replay_path.is_file():
                raise ValueError(
                    f"replay report is absent from Source.zip: {replay['report_path']}"
                )
            for kind, entrypoint in (("wheel", wheel_entry), ("sdist", sdist_entry)):
                _distribution_diff_verify(
                    entrypoint,
                    extracted_root,
                    tmp / f"{kind}-generated",
                    str(replay["expected_scope"]),
                )
                output = _run_checked(
                    [
                        str(entrypoint),
                        "verify",
                        str(replay_path),
                        "--source-root",
                        str(extracted_root),
                    ],
                    cwd=tmp,
                )
                if f"verification_scope={replay['expected_scope']}" not in output:
                    raise RuntimeError(
                        f"{kind} extracted Source.zip replay did not report expected scope"
                    )
            relocated = tmp / "unrelated" / "relocated-source"
            relocated.parent.mkdir()
            shutil.copytree(extracted_root, relocated)
            relocated_report = relocated.joinpath(*PurePosixPath(str(replay["report_path"])).parts)
            for kind, entrypoint in (("wheel", wheel_entry), ("sdist", sdist_entry)):
                output = _run_checked(
                    [
                        str(entrypoint),
                        "verify",
                        str(relocated_report),
                        "--source-root",
                        str(relocated),
                    ],
                    cwd=tmp / "unrelated",
                )
                if f"verification_scope={replay['expected_scope']}" not in output:
                    raise RuntimeError(f"{kind} relocated replay did not report expected scope")
    except (
        OSError,
        RuntimeError,
        UnicodeError,
        ValueError,
        zipfile.BadZipFile,
        subprocess.TimeoutExpired,
    ) as exc:
        state.fail("isolated_install", str(exc))
        state.fail("replay", str(exc))
    state.pass_check("isolated_install")
    state.pass_check("replay")


def verify_package(
    *,
    repo: Path,
    manifest_path: Path,
    bundle_path: Path,
    source_zip_path: Path,
) -> JsonObject:
    """Verify one package and return a bounded machine-readable result."""
    state = _State()
    try:
        repo = repo.resolve(strict=True)
        manifest_path = manifest_path.resolve(strict=True)
        bundle_path = bundle_path.resolve(strict=True)
        source_zip_path = source_zip_path.resolve(strict=True)
    except OSError as exc:
        state.fail("input_paths", f"cannot resolve package input: {exc}")
        return state.summary(run_id=None, schema_version=None)
    manifest: JsonObject
    try:
        manifest = _read_json(
            manifest_path,
            label="manifest",
            limit=MAX_MANIFEST_BYTES,
        )
    except StrictJsonError as exc:
        state.fail("manifest", str(exc))
        return state.summary(run_id=None, schema_version=None)

    run_id_value = manifest.get("run_id")
    schema_value = manifest.get("schema_version")
    run_id = run_id_value if isinstance(run_id_value, str) else None
    schema_version = schema_value if isinstance(schema_value, str) else None
    if schema_version != MANIFEST_VERSION:
        state.fail("manifest", f"unsupported schema_version: {schema_version!r}")
        return state.summary(run_id=run_id, schema_version=schema_version)
    try:
        schema = _load_schema("package_manifest_v1.schema.json")
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # schema is trusted package data, but fail closed
        state.fail("manifest_schema", f"cannot load built-in schema: {exc}")
        return state.summary(run_id=run_id, schema_version=schema_version)
    validation_errors = _schema_errors(manifest, schema)
    for error in validation_errors:
        state.fail("manifest_schema", error)
    if validation_errors:
        return state.summary(run_id=run_id, schema_version=schema_version)
    state.pass_check("manifest")
    state.pass_check("manifest_schema")

    resolved = _verify_file_records(manifest, manifest_path.parent, state)
    _verify_package_tree(manifest, manifest_path, state)
    expected_bundle = resolved.get(("artifacts", "bundle"))
    expected_source = resolved.get(("artifacts", "source_zip"))
    try:
        if expected_bundle is None or bundle_path.resolve(strict=True) != expected_bundle:
            state.fail("declared_files", "--bundle does not identify artifacts.bundle")
    except OSError as exc:
        state.fail("declared_files", f"cannot resolve --bundle: {exc}")
    try:
        if expected_source is None or source_zip_path.resolve(strict=True) != expected_source:
            state.fail("declared_files", "--source-zip does not identify artifacts.source_zip")
    except OSError as exc:
        state.fail("declared_files", f"cannot resolve --source-zip: {exc}")

    packaged_schema = resolved.get(("artifacts", "manifest_schema"))
    try:
        if (
            packaged_schema is None
            or packaged_schema.read_bytes()
            != _schema_path("package_manifest_v1.schema.json").read_bytes()
        ):
            state.fail("manifest_schema", "declared manifest_schema differs from verifier schema")
    except OSError as exc:
        state.fail("manifest_schema", f"cannot compare declared schema: {exc}")
    checksum_path = resolved.get(("artifacts", "checksums"))
    if checksum_path is None:
        state.fail("checksums", "declared checksums artifact is unavailable")
    else:
        _verify_checksums(manifest, checksum_path, state)

    _verify_phase_refs(manifest, state)
    _verify_determinism(manifest, resolved, state)
    envelopes = _verify_command_records(manifest, resolved, state)
    _verify_counts(manifest, envelopes, state, resolved)
    _verify_matrix(repo, manifest, envelopes, resolved, state)

    if state.error_count == 0:
        _verify_repo_and_bundle(repo, bundle_path, manifest, state)
        _verify_source_zip(repo, source_zip_path, manifest, state)
    if state.error_count == 0:
        _verify_distribution_provenance(
            repo,
            manifest,
            resolved,
            source_zip_path.resolve(),
            state,
        )
    if state.error_count == 0:
        _verify_distribution_metadata(repo.resolve(), manifest, resolved, state)
        _verify_sbom(manifest, resolved, state, repo.resolve())
    if state.error_count == 0:
        _verify_installs_and_replay(manifest, resolved, source_zip_path.resolve(), state)

    return state.summary(run_id=run_id, schema_version=schema_version)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point used by ``scripts/external_package_verify.py``."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = verify_package(
            repo=args.repo,
            manifest_path=args.manifest,
            bundle_path=args.bundle,
            source_zip_path=args.source_zip,
        )
    except Exception as exc:  # defensive CLI boundary; never expose a traceback
        state = _State()
        state.fail("internal", f"controlled verifier failure: {type(exc).__name__}: {exc}")
        summary = state.summary(run_id=None, schema_version=None)
    print(json.dumps(summary, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0 if summary["ok"] is True else 1
