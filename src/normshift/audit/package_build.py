"""Build a fail-closed, exact-commit M0 external-audit package.

The authoritative manifest deliberately lives outside the tracked Git tree.  A
candidate is emitted only after the checkout is clean, every required command
passes, deterministic products compare byte-for-byte, and the retained package
products have been hashed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import uuid
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from email.parser import BytesParser
from email.policy import default as email_policy
from pathlib import Path, PurePosixPath
from typing import Any, Final
from urllib.parse import urlsplit
from xml.etree import ElementTree

from normshift.audit.wheel_normalize import (
    WheelNormalizationError,
    assert_canonical_wheel_file,
)

MANIFEST_SCHEMA_VERSION: Final = "normshift-package-manifest/v1"
RUN_ID_RE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,95}$")
SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE: Final = re.compile(r"^[0-9a-f]{40}$")
BENCHMARK_TOTAL: Final = 17
MEASURE_TOTAL: Final = 15
REPLAY_REPORT_PATH: Final = "evidence/m0-repair-round5/report.json"
R4_R5_MODULES: Final = (
    "tests/e2e/test_m0_repair_round4.py",
    "tests/e2e/test_m0_repair_round5.py",
)
SBOM_EXPORT_ARGV: Final = (
    "uv",
    "export",
    "--frozen",
    "--no-dev",
    "--no-editable",
    "--format",
    "cyclonedx1.5",
    "--preview-features",
    "sbom-export",
)


class PackageBuildError(RuntimeError):
    """A required package invariant or command failed."""


@dataclass(frozen=True)
class BuildConfig:
    """Inputs that bind one authoritative package attempt."""

    repo: Path
    output_root: Path
    expected_commit: str
    repository_url: str | None = None
    default_branch: str = "master"
    run_id: str | None = None


@dataclass(frozen=True)
class CommandResult:
    """Captured result of one retained command."""

    id: str
    gate: str
    argv: tuple[str, ...]
    cwd: str
    started_at: str
    finished_at: str
    exit_code: int
    stdout: str
    stderr: str
    log: str
    required: bool

    def manifest_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "gate": self.gate,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "log": self.log,
            "required": self.required,
        }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def new_run_id() -> str:
    """Return a sortable identifier with enough entropy for concurrent builders."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}-{uuid.uuid4().hex[:12]}"


def _canonical_json_bytes(value: Any) -> bytes:
    _reject_noncanonical_numbers(value)
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _reject_noncanonical_numbers(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PackageBuildError(f"non-finite number at {path}")
        if value == 0.0 and math.copysign(1.0, value) < 0:
            raise PackageBuildError(f"negative zero at {path}")
    elif isinstance(value, dict):
        for key, child in value.items():
            _reject_noncanonical_numbers(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_noncanonical_numbers(child, f"{path}[{index}]")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json_bytes(value))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path, root: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    return {"path": relative, "sha256": _sha256_file(path), "size": path.stat().st_size}


def _decode_output(data: bytes) -> str:
    return data.decode("utf-8", errors="backslashreplace")


def _run_raw(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(item) for item in argv],
        cwd=cwd,
        check=False,
        capture_output=True,
    )


def _checked_output(argv: Sequence[str], cwd: Path) -> str:
    result = _run_raw(argv, cwd)
    if result.returncode != 0:
        command = " ".join(str(item) for item in argv)
        stderr = _decode_output(result.stderr).strip()
        raise PackageBuildError(f"command failed during preflight: {command}: {stderr}")
    return _decode_output(result.stdout).strip()


def _git(repo: Path, *args: str) -> str:
    return _checked_output(("git", "-C", str(repo), *args), repo)


class CommandRecorder:
    """Run commands and retain a JSON envelope containing both output streams."""

    def __init__(
        self,
        package_root: Path,
        repo: Path,
        *,
        source_date_epoch: str,
        gate_state_root: Path | None = None,
    ) -> None:
        self.package_root = package_root
        self.repo = repo
        self.results: list[CommandResult] = []
        self._ids: set[str] = set()
        self._base_environment = _isolated_environment(
            source_date_epoch=source_date_epoch,
            gate_state_root=gate_state_root,
        )

    def run(
        self,
        command_id: str,
        gate: str,
        argv: Sequence[str | Path],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        required: bool = True,
    ) -> CommandResult:
        if command_id in self._ids:
            raise PackageBuildError(f"duplicate command id: {command_id}")
        self._ids.add(command_id)
        actual_cwd = (cwd or self.repo).resolve()
        normalized_argv = tuple(str(item) for item in argv)
        started_at = _utc_now()
        completed = subprocess.run(
            list(normalized_argv),
            cwd=actual_cwd,
            env=env if env is not None else self._base_environment,
            check=False,
            capture_output=True,
        )
        finished_at = _utc_now()
        stdout = _decode_output(completed.stdout)
        stderr = _decode_output(completed.stderr)
        cwd_value = "." if actual_cwd == self.repo else str(actual_cwd)
        log_key = command_id
        log_path = self.package_root / "logs" / f"{command_id}.json"
        envelope = {
            "schema_version": "normshift-command-log/v1",
            "command_id": command_id,
            "gate": gate,
            "argv": list(normalized_argv),
            "cwd": cwd_value,
            "started_at": started_at,
            "finished_at": finished_at,
            "required": required,
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
        _write_json(log_path, envelope)
        result = CommandResult(
            id=command_id,
            gate=gate,
            argv=normalized_argv,
            cwd=cwd_value,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            log=log_key,
            required=required,
        )
        self.results.append(result)
        if required and result.exit_code != 0:
            raise PackageBuildError(
                f"required command {command_id!r} failed with exit {result.exit_code}; "
                f"see {log_path}"
            )
        return result


@dataclass(frozen=True)
class CheckoutIdentity:
    commit: str
    tree: str
    repository_url: str


def _normalize_repository_url(raw: str) -> str:
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise PackageBuildError(f"repository URL is invalid: {exc}") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(r"/taipei49314/NormShift(?:\.git)?", parsed.path)
    ):
        raise PackageBuildError(
            "repository URL must be the public NormShift GitHub URL without credentials, "
            "port, query, or fragment"
        )
    return "https://github.com/taipei49314/NormShift"


def _assert_default_branch_subject(repo: Path, default_branch: str, commit: str) -> None:
    if default_branch != "master":
        raise PackageBuildError(
            "the NormShift v1 package contract requires default branch 'master'"
        )
    default_ref = f"refs/remotes/origin/{default_branch}^{{commit}}"
    result = _run_raw(("git", "-C", str(repo), "rev-parse", "--verify", default_ref), repo)
    remote_commit = _decode_output(result.stdout).strip().lower()
    if result.returncode != 0 or remote_commit != commit:
        raise PackageBuildError(
            f"package commit {commit} is not the exact origin/{default_branch} commit"
        )


def _assert_clean_exact_checkout(
    config: BuildConfig,
    *,
    reject_ignored: bool = False,
) -> CheckoutIdentity:
    repo = config.repo.resolve()
    if not repo.is_dir():
        raise PackageBuildError(f"repository directory does not exist: {repo}")
    top = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    if top != repo:
        raise PackageBuildError(f"--repo must be the Git worktree root: {top}")
    expected = config.expected_commit.lower()
    if not COMMIT_RE.fullmatch(expected):
        raise PackageBuildError("--commit must be one full lowercase 40-character Git SHA")
    head = _git(repo, "rev-parse", "--verify", "HEAD^{commit}").lower()
    if head != expected:
        raise PackageBuildError(f"checkout HEAD {head} does not equal requested commit {expected}")
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        preview = "\n".join(status.splitlines()[:10])
        raise PackageBuildError(f"exact-subject checkout is dirty:\n{preview}")
    if reject_ignored:
        ignored = _git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored=matching",
        )
        if ignored:
            preview = "\n".join(ignored.splitlines()[:10])
            raise PackageBuildError(
                "exact-subject checkout contains pre-existing ignored state:\n" + preview
            )
    tree = _git(repo, "rev-parse", "HEAD^{tree}").lower()
    remote = config.repository_url or _git(repo, "remote", "get-url", "origin")
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    _assert_default_branch_subject(repo, config.default_branch, head)
    return CheckoutIdentity(
        commit=head,
        tree=tree,
        repository_url=_normalize_repository_url(remote),
    )


def _assert_output_outside_repo(repo: Path, output_root: Path) -> None:
    resolved_repo = repo.resolve()
    resolved_output = output_root.resolve()
    if resolved_output == resolved_repo or resolved_output.is_relative_to(resolved_repo):
        raise PackageBuildError("package output root must be outside the exact checkout")


def _project_metadata(repo: Path) -> tuple[str, str, dict[str, str]]:
    data = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project")
    build_system = data.get("build-system")
    if not isinstance(project, dict) or not isinstance(build_system, dict):
        raise PackageBuildError("pyproject.toml lacks project/build-system tables")
    name = project.get("name")
    version = project.get("version")
    backend = build_system.get("build-backend")
    requirements = build_system.get("requires")
    if name != "normshift" or not isinstance(version, str) or not version:
        raise PackageBuildError("pyproject project identity is not normshift with a version")
    if backend != "hatchling.build" or not isinstance(requirements, list):
        raise PackageBuildError("build backend must be hatchling.build with a pinned requirement")
    pinned = [
        item for item in requirements if isinstance(item, str) and item.startswith("hatchling==")
    ]
    if len(pinned) != 1:
        raise PackageBuildError("uv build requires exactly one pinned hatchling== version")
    backend_version = pinned[0].removeprefix("hatchling==")
    return name, version, {
        "module": backend,
        "distribution": "hatchling",
        "version": backend_version,
    }


@dataclass(frozen=True)
class PytestSummary:
    counts: dict[str, int]
    cases: list[dict[str, Any]]


def _pytest_node_id(classname: str, name: str) -> str:
    module_path = classname.replace(".", "/") + ".py"
    return f"{module_path}::{name}"


def _parse_junit(path: Path, terminal_output: str = "") -> PytestSummary:
    """Parse JUnit itself; terminal output is consulted only for pytest XPASS."""
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise PackageBuildError(f"invalid or missing JUnit XML {path}: {exc}") from exc

    xpass_ids = set(re.findall(r"(?m)^XPASS\s+(\S+)", terminal_output))
    matched_xpass_ids: set[str] = set()
    counts = {
        "collected": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "errors": 0,
    }
    cases: list[dict[str, Any]] = []
    for testcase in root.iter("testcase"):
        name = testcase.attrib.get("name", "")
        classname = testcase.attrib.get("classname", "")
        if not name or not classname:
            raise PackageBuildError("JUnit testcase is missing classname or name")
        node_id = _pytest_node_id(classname, name)
        counts["collected"] += 1
        outcome = "passed"
        if testcase.find("failure") is not None:
            counts["failed"] += 1
            outcome = "failed"
        elif testcase.find("error") is not None:
            counts["errors"] += 1
            outcome = "error"
        else:
            skipped = testcase.find("skipped")
            if skipped is not None:
                if skipped.attrib.get("type") == "pytest.xfail":
                    counts["xfailed"] += 1
                    outcome = "xfailed"
                else:
                    counts["skipped"] += 1
                    outcome = "skipped"
            elif node_id in xpass_ids:
                counts["xpassed"] += 1
                matched_xpass_ids.add(node_id)
                outcome = "xpassed"
            else:
                counts["passed"] += 1
        cases.append({"id": node_id, "outcome": outcome})

    # Pytest's JUnit ``classname`` flattens class names into the dotted module
    # path, so the reconstructed ID above cannot reliably equal terminal IDs
    # such as ``tests/x.py::TestFeature::test_case``.  Any unmatched terminal
    # XPASS must still fail closed instead of being silently counted as passed.
    unmatched_xpasses = xpass_ids - matched_xpass_ids
    if len(unmatched_xpasses) > counts["passed"]:
        raise PackageBuildError("pytest terminal reports more XPASS cases than JUnit passes")
    counts["passed"] -= len(unmatched_xpasses)
    counts["xpassed"] += len(unmatched_xpasses)

    if counts["collected"] == 0:
        raise PackageBuildError("JUnit collected zero tests")
    return PytestSummary(counts=counts, cases=cases)


def _require_clean_pytest(summary: PytestSummary, gate: str) -> None:
    disallowed = ("failed", "skipped", "xfailed", "xpassed", "errors")
    bad = {key: summary.counts[key] for key in disallowed if summary.counts[key] != 0}
    if bad or summary.counts["passed"] != summary.counts["collected"]:
        raise PackageBuildError(f"{gate} JUnit is not an all-pass, no-skip run: {bad}")


def _parse_benchmark(stdout: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for match in re.finditer(r"(?m)^\[(PASS|FAIL)\]\s+([^:]+):\s*(.*)$", stdout):
        cases.append(
            {
                "id": match.group(2).strip(),
                "passed": match.group(1) == "PASS",
            }
        )
    summary = re.search(r"(?m)^benchmark:\s+(\d+)/(\d+) passed,\s+(\d+) failed\s*$", stdout)
    if summary is None:
        raise PackageBuildError("benchmark output has no parseable final summary")
    passed, total, failed = (int(value) for value in summary.groups())
    if total != BENCHMARK_TOTAL or passed != total or failed != 0:
        raise PackageBuildError(
            f"benchmark gate requires {BENCHMARK_TOTAL}/{BENCHMARK_TOTAL}; "
            f"observed {passed}/{total} with {failed} failed"
        )
    if len(cases) != total or any(not case["passed"] for case in cases):
        raise PackageBuildError("benchmark per-case output does not match its all-pass summary")
    if len({str(case["id"]) for case in cases}) != total:
        raise PackageBuildError("benchmark case IDs are missing or duplicated")
    return {"total": total, "passed": passed, "failed": failed, "cases": cases}


def _parse_measure(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise PackageBuildError(f"invalid or missing measure metrics {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PackageBuildError("measure metrics root is not an object")
    total = payload.get("case_count")
    passed = payload.get("cases_passed")
    failed = payload.get("cases_failed")
    raw_cases = payload.get("case_results")
    if (total, passed, failed) != (MEASURE_TOTAL, MEASURE_TOTAL, 0):
        raise PackageBuildError(
            f"measure gate requires {MEASURE_TOTAL}/{MEASURE_TOTAL}; "
            f"observed passed={passed!r} total={total!r} failed={failed!r}"
        )
    if not isinstance(raw_cases, list) or len(raw_cases) != MEASURE_TOTAL:
        raise PackageBuildError("measure case_results does not contain exactly 15 cases")
    cases: list[dict[str, Any]] = []
    for item in raw_cases:
        if not isinstance(item, dict) or not isinstance(item.get("case_id"), str):
            raise PackageBuildError("measure case result lacks a string case_id")
        if item.get("passed") is not True:
            raise PackageBuildError(f"measure case did not pass: {item.get('case_id')}")
        cases.append(
            {
                "id": item["case_id"],
                "passed": True,
            }
        )
    if len({str(case["id"]) for case in cases}) != MEASURE_TOTAL:
        raise PackageBuildError("measure case IDs are missing or duplicated")
    metrics_by_layer: dict[str, Any] = {}
    for layer in ("extraction", "alignment", "classification"):
        metrics = payload.get(layer)
        if not isinstance(metrics, dict):
            raise PackageBuildError(f"measure metrics lacks aggregate {layer} results")
        selected = {key: metrics.get(key) for key in ("precision", "recall", "f1")}
        if not all(isinstance(value, (int, float)) for value in selected.values()):
            raise PackageBuildError(f"measure aggregate {layer} lacks precision/recall/f1")
        metrics_by_layer[layer] = selected
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "cases": cases,
        "metrics": metrics_by_layer,
    }


def _require_identical(first: Path, second: Path, label: str) -> None:
    if first.read_bytes() != second.read_bytes():
        raise PackageBuildError(f"two-run determinism failed for {label}")


def _normalize_lock_source(source: Any) -> str:
    if not isinstance(source, dict) or not source:
        raise PackageBuildError("uv.lock package has no structured source")
    parts: list[str] = []
    for key, value in sorted(source.items()):
        if not isinstance(key, str) or not isinstance(value, (str, int, float, bool)):
            raise PackageBuildError("uv.lock package source is not scalar and normalizable")
        parts.append(f"{key}:{value}")
    return ";".join(parts)


def _validate_and_join_sbom(
    sbom_path: Path,
    lock_path: Path,
    project_name: str,
    project_version: str,
    generator_argv: Sequence[str],
) -> dict[str, Any]:
    try:
        sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
        lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, OSError) as exc:
        raise PackageBuildError(f"cannot parse SBOM/uv.lock: {exc}") from exc
    if not isinstance(sbom, dict) or sbom.get("bomFormat") != "CycloneDX":
        raise PackageBuildError("SBOM is not CycloneDX JSON")
    if sbom.get("specVersion") != "1.5":
        raise PackageBuildError("SBOM is not CycloneDX 1.5")
    metadata = sbom.get("metadata")
    if not isinstance(metadata, dict):
        raise PackageBuildError("SBOM metadata is missing")
    root_component = metadata.get("component")
    if not isinstance(root_component, dict):
        raise PackageBuildError("SBOM root component is missing")
    if (root_component.get("name"), root_component.get("version")) != (
        project_name,
        project_version,
    ):
        raise PackageBuildError("SBOM root component does not match package identity")
    tools = metadata.get("tools")
    if not isinstance(tools, list) or len(tools) == 0:
        raise PackageBuildError("SBOM has no generator identity")
    generator = next(
        (item for item in tools if isinstance(item, dict) and item.get("name") == "uv"),
        None,
    )
    if not isinstance(generator, dict) or not isinstance(generator.get("version"), str):
        raise PackageBuildError("SBOM does not identify the uv generator version")

    packages = lock.get("package")
    if not isinstance(packages, list):
        raise PackageBuildError("uv.lock has no package inventory")
    lock_index: dict[tuple[str, str], set[str]] = {}
    for package in packages:
        if not isinstance(package, dict):
            continue
        name = package.get("name")
        version = package.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            continue
        source = _normalize_lock_source(package.get("source"))
        lock_index.setdefault((name, version), set()).add(source)

    components = sbom.get("components")
    if not isinstance(components, list) or not components:
        raise PackageBuildError("SBOM dependency inventory is empty")
    inventory: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for component in components:
        if not isinstance(component, dict):
            raise PackageBuildError("SBOM component is not an object")
        name = component.get("name")
        version = component.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise PackageBuildError("SBOM component lacks name/version")
        key = (name, version)
        if key in seen:
            raise PackageBuildError(f"SBOM repeats component {name}=={version}")
        seen.add(key)
        sources = lock_index.get(key)
        if sources is None or len(sources) != 1:
            raise PackageBuildError(
                f"SBOM component {name}=={version} has no unique uv.lock source"
            )
        inventory.append({"name": name, "version": version, "source": next(iter(sources))})
    inventory.sort(key=lambda item: (item["name"], item["version"], item["source"]))
    return {
        "format": "CycloneDX",
        "spec_version": "1.5",
        "generator": {
            "name": str(generator["name"]),
            "version": str(generator["version"]),
        },
        "generator_argv": list(generator_argv),
        "validator": {
            "name": "cyclonedx-python-lib",
            "version": "11.11.0",
            "mode": "strict-offline-1.5",
        },
        "lockfile_sha256": _sha256_file(lock_path),
        "root": {"name": project_name, "version": project_version},
        "inventory": inventory,
    }


def _validate_sbom_schema(sbom_path: Path) -> None:
    try:
        from cyclonedx.schema import SchemaVersion
        from cyclonedx.validation.json import JsonStrictValidator
    except ImportError as exc:
        raise PackageBuildError(
            "cyclonedx-python-lib[validation]==11.11.0 is required for SBOM validation"
        ) from exc
    validator = JsonStrictValidator(SchemaVersion.V1_5)
    validation = validator.validate_str(sbom_path.read_text(encoding="utf-8"), all_errors=True)
    if validation is not None:
        errors = [str(item) for item in validation]
        raise PackageBuildError(f"CycloneDX 1.5 strict validation failed: {errors[:5]}")


def _read_git_tree(repo: Path, commit: str) -> dict[str, tuple[str, str]]:
    result = _run_raw(("git", "-C", str(repo), "ls-tree", "-r", "-z", commit), repo)
    if result.returncode != 0:
        raise PackageBuildError(f"git ls-tree failed: {_decode_output(result.stderr).strip()}")
    entries: dict[str, tuple[str, str]] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, path_bytes = raw.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split(" ", 2)
            path = path_bytes.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise PackageBuildError("git ls-tree returned an unparseable entry") from exc
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise PackageBuildError(f"source archive cannot contain special Git entry: {path}")
        if path in entries:
            raise PackageBuildError(f"git tree repeats path: {path}")
        entries[path] = (mode, object_id)
    if not entries:
        raise PackageBuildError("Git tree has no tracked files")
    return entries


def _git_blob(repo: Path, object_id: str) -> bytes:
    result = _run_raw(("git", "-C", str(repo), "cat-file", "blob", object_id), repo)
    if result.returncode != 0:
        raise PackageBuildError(
            f"cannot read Git blob {object_id}: {_decode_output(result.stderr).strip()}"
        )
    return result.stdout


def _safe_zip_member(name: str, prefix: str) -> tuple[bool, str | None]:
    if "\\" in name or "\x00" in name or not name.startswith(prefix):
        return False, None
    relative = name[len(prefix) :]
    if relative == "":
        return name.endswith("/"), None
    path = PurePosixPath(relative.rstrip("/"))
    if (
        relative.startswith("/")
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        return False, None
    canonical = path.as_posix() + ("/" if relative.endswith("/") else "")
    if canonical != relative:
        return False, None
    return True, None if relative.endswith("/") else path.as_posix()


def _inspect_source_archive(
    source_zip: Path,
    repo: Path,
    commit: str,
    prefix: str,
) -> dict[str, Any]:
    tracked = _read_git_tree(repo, commit)
    duplicate_count = 0
    unsafe_count = 0
    case_collision_count = 0
    archive_files: dict[str, zipfile.ZipInfo] = {}
    seen_names: set[str] = set()
    casefold_names: dict[str, str] = {}
    with zipfile.ZipFile(source_zip) as archive:
        for info in archive.infolist():
            original_name = info.orig_filename
            if original_name in seen_names:
                duplicate_count += 1
            seen_names.add(original_name)
            folded = original_name.casefold()
            previous = casefold_names.get(folded)
            if previous is not None and previous != original_name:
                case_collision_count += 1
            else:
                casefold_names[folded] = original_name
            safe, relative = _safe_zip_member(original_name, prefix)
            mode = (info.external_attr >> 16) & 0xFFFF
            kind = stat.S_IFMT(mode)
            if not safe or kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                unsafe_count += 1
                continue
            try:
                with archive.open(info):
                    pass
            except (NotImplementedError, RuntimeError, zipfile.BadZipFile):
                unsafe_count += 1
                continue
            if relative is not None:
                archive_files[relative] = info

        tracked_paths = set(tracked)
        archived_paths = set(archive_files)
        missing = sorted(tracked_paths - archived_paths)
        extra = sorted(archived_paths - tracked_paths)
        blob_equality = not missing and not extra
        if blob_equality:
            for relative in sorted(tracked_paths):
                info = archive_files[relative]
                expected = _git_blob(repo, tracked[relative][1])
                if archive.read(info) != expected:
                    blob_equality = False
                    break

    result = {
        "prefix": prefix,
        "tracked_file_count": len(tracked),
        "archive_file_count": len(archive_files),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "duplicate_count": duplicate_count,
        "unsafe_count": unsafe_count,
        "case_collision_count": case_collision_count,
        "blob_equality": blob_equality,
    }
    if (
        any(
            (
                result["missing_count"],
                result["extra_count"],
                result["duplicate_count"],
                result["unsafe_count"],
                result["case_collision_count"],
            )
        )
        or not blob_equality
    ):
        raise PackageBuildError(f"source archive does not exactly represent Git: {result}")
    return result


def _extract_source_archive(source_zip: Path, destination: Path, prefix: str) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(source_zip) as archive:
        archive.extractall(destination)
    root = destination / prefix.rstrip("/")
    if not root.is_dir():
        raise PackageBuildError("extracted source archive has no canonical prefix directory")
    return root


def _copy_frozen_inputs(repo: Path, package_root: Path) -> None:
    destination = package_root / "frozen-inputs"
    roots = (
        Path("benchmark"),
        Path("fixtures"),
        Path("schemas"),
        Path("evidence/m1"),
        Path("evidence/m2"),
    )
    for root in roots:
        source_root = repo / root
        if not source_root.is_dir():
            raise PackageBuildError(f"required frozen input directory is missing: {root}")
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative = source.relative_to(repo)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    shutil.copyfile(repo / "uv.lock", destination / "uv.lock")


def _write_checksums(package_root: Path, output_name: str, manifest_name: str) -> Path:
    checksum_path = package_root / output_name
    lines: list[str] = []
    records = [
        (path.relative_to(package_root).as_posix(), path)
        for path in package_root.rglob("*")
        if path.is_file()
    ]
    for relative, path in sorted(records, key=lambda item: item[0]):
        if relative in {output_name, manifest_name}:
            continue
        lines.append(f"{_sha256_file(path)}  {relative}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return checksum_path


def _file_id(relative_path: str) -> str:
    return f"file.{_sha256_bytes(relative_path.encode('utf-8'))}"


def _records_under(package_root: Path, relative_root: str) -> dict[str, dict[str, Any]]:
    root = package_root / relative_root
    if not root.is_dir():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(package_root).as_posix()
        record_id = "lockfile" if relative == "frozen-inputs/uv.lock" else _file_id(relative)
        records[record_id] = _file_record(path, package_root)
    return records


def _runtime_inventory_blocks(
    files: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    m1_refs = sorted(
        record_id
        for record_id, record in files.items()
        if any(marker in f"/{record['path']}" for marker in ("/fixtures/corpus/", "/evidence/m1/"))
    )
    m2_refs = sorted(
        record_id
        for record_id, record in files.items()
        if any(marker in f"/{record['path']}" for marker in ("/fixtures/lineage/", "/evidence/m2/"))
    )
    return (
        {
            "acceptance_evaluated": False,
            "reason": (
                "Structure-faithful excerpts are retained but M1 has no frozen, "
                "independently adjudicated real-standards acceptance corpus."
            ),
            "corpus_refs": m1_refs,
            "ground_truth_refs": [],
            "per_class": {},
        },
        {
            "acceptance_evaluated": False,
            "reason": (
                "Synthetic lineage evidence is retained but M2 is not externally adjudicated."
            ),
            "corpus_refs": m2_refs,
            "ground_truth_refs": [],
            "per_class": {},
        },
    )


@dataclass(frozen=True)
class GateEvidence:
    pytest: PytestSummary
    pytest_junit: Path
    matrix: PytestSummary
    matrix_junit: Path
    benchmark: dict[str, Any]
    measure: dict[str, Any]
    determinism: dict[str, Any]
    report_one: Path


def _run_required_product_gates(
    recorder: CommandRecorder,
    repo: Path,
    package_root: Path,
) -> GateEvidence:
    junit_dir = package_root / "evidence" / "junit"
    run_one = package_root / "evidence" / "run-1"
    run_two = package_root / "evidence" / "run-2"
    junit_dir.mkdir(parents=True, exist_ok=True)
    run_one.mkdir(parents=True, exist_ok=True)
    run_two.mkdir(parents=True, exist_ok=True)

    recorder.run(
        "dependency_sync",
        "dependency_sync",
        ("uv", "sync", "--frozen", "--all-extras", "--dev"),
    )
    recorder.run("ruff", "ruff", ("uv", "run", "--frozen", "ruff", "check", "."))
    recorder.run("mypy", "mypy", ("uv", "run", "--frozen", "mypy", "src"))

    pytest_xml = junit_dir / "pytest.xml"
    pytest_result = recorder.run(
        "pytest",
        "pytest",
        (
            "uv",
            "run",
            "--frozen",
            "pytest",
            "-q",
            "-rxX",
            "-p",
            "no:cacheprovider",
            f"--junitxml={pytest_xml}",
        ),
    )
    pytest_summary = _parse_junit(
        pytest_xml,
        pytest_result.stdout + "\n" + pytest_result.stderr,
    )
    _require_clean_pytest(pytest_summary, "complete pytest")

    matrix_xml = junit_dir / "r4-r5.xml"
    matrix_result = recorder.run(
        "r4_r5",
        "r4_r5",
        (
            "uv",
            "run",
            "--frozen",
            "pytest",
            "-q",
            "-rxX",
            "-p",
            "no:cacheprovider",
            *R4_R5_MODULES,
            f"--junitxml={matrix_xml}",
        ),
    )
    matrix_summary = _parse_junit(
        matrix_xml,
        matrix_result.stdout + "\n" + matrix_result.stderr,
    )
    _require_clean_pytest(matrix_summary, "R4/R5 matrix")
    matrix_prefixes = (
        "tests/e2e/test_m0_repair_round4.py::",
        "tests/e2e/test_m0_repair_round5.py::",
    )
    if not all(case["id"].startswith(matrix_prefixes) for case in matrix_summary.cases):
        raise PackageBuildError("R4/R5 JUnit contains an unexpected test node ID")

    benchmark_result = recorder.run(
        "benchmark",
        "benchmark",
        (
            "uv",
            "run",
            "--frozen",
            "normshift",
            "benchmark",
            "--ground-truth",
            "benchmark/ground_truth.jsonl",
        ),
    )
    benchmark = _parse_benchmark(benchmark_result.stdout)

    def run_products(
        suffix: str,
        destination: Path,
        command_suffix: str,
    ) -> tuple[Path, Path, Path]:
        metrics = destination / "metrics.json"
        report_json = destination / "report.json"
        report_md = destination / "report.md"
        recorder.run(
            f"measure{command_suffix}",
            "measure" if not command_suffix else "other",
            (
                "uv",
                "run",
                "--frozen",
                "normshift",
                "measure",
                "--ground-truth",
                "benchmark/measure_suite.jsonl",
                "--out",
                metrics,
            ),
        )
        recorder.run(
            f"diff{command_suffix}",
            "diff" if not command_suffix else "other",
            (
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
                report_json,
                "--markdown",
                report_md,
            ),
        )
        verify = recorder.run(
            f"verify{command_suffix}",
            "verify" if not command_suffix else "other",
            (
                "uv",
                "run",
                "--frozen",
                "normshift",
                "verify",
                report_json,
                "--source-root",
                ".",
            ),
        )
        if "verification_scope=FULL" not in verify.stdout:
            raise PackageBuildError(f"{suffix} verify did not report verification_scope=FULL")
        return report_json, report_md, metrics

    first = run_products("run-1", run_one, "")
    second = run_products("run-2", run_two, "_run_2")
    measure = _parse_measure(first[2])
    second_measure = _parse_measure(second[2])
    if measure != second_measure:
        raise PackageBuildError("two measure runs produced different parsed results")
    labels = ("report_json", "report_markdown", "metrics")
    for label, first_path, second_path in zip(labels, first, second, strict=True):
        _require_identical(first_path, second_path, label)
    determinism = {
        label: {
            "first": first_path.relative_to(package_root).as_posix(),
            "second": second_path.relative_to(package_root).as_posix(),
            "equal": True,
        }
        for label, first_path, second_path in zip(labels, first, second, strict=True)
    }
    return GateEvidence(
        pytest=pytest_summary,
        pytest_junit=pytest_xml,
        matrix=matrix_summary,
        matrix_junit=matrix_xml,
        benchmark=benchmark,
        measure=measure,
        determinism=determinism,
        report_one=first[0],
    )


def _require_full_verify(result: CommandResult, label: str) -> None:
    if result.exit_code != 0 or "verification_scope=FULL" not in result.stdout:
        raise PackageBuildError(f"{label} did not complete FULL verification")


def _run_relocation_check(
    recorder: CommandRecorder,
    repo: Path,
    report: Path,
) -> bool:
    with tempfile.TemporaryDirectory(prefix="normshift-relocation-") as temp_name:
        root = Path(temp_name)
        source_dir = root / "fixtures" / "synthetic"
        source_dir.mkdir(parents=True)
        for name in ("spec-v1.html", "spec-v2.html"):
            shutil.copyfile(repo / "fixtures" / "synthetic" / name, source_dir / name)
        relocated_report = root / "report.json"
        shutil.copyfile(report, relocated_report)
        result = recorder.run(
            "relocation_verify",
            "relocation_verify",
            (
                "uv",
                "run",
                "--frozen",
                "normshift",
                "verify",
                relocated_report,
                "--source-root",
                root,
            ),
        )
        _require_full_verify(result, "unrelated relocation")
    return True


@dataclass(frozen=True)
class GitProducts:
    bundle: Path
    source_zip: Path
    bundle_evidence: dict[str, Any]
    archive_evidence: dict[str, Any]


def _build_git_products(
    recorder: CommandRecorder,
    repo: Path,
    package_root: Path,
    package_base: str,
    commit: str,
    tree: str,
) -> GitProducts:
    bundle = package_root / f"{package_base}.bundle"
    recorder.run(
        "bundle_create",
        "bundle",
        ("git", "bundle", "create", bundle, "HEAD"),
    )
    recorder.run(
        "bundle_verify",
        "other",
        ("git", "bundle", "verify", bundle),
    )
    heads = recorder.run(
        "bundle_heads",
        "other",
        ("git", "bundle", "list-heads", bundle),
    )
    expected_head_line = f"{commit} HEAD"
    if heads.stdout.strip() != expected_head_line:
        raise PackageBuildError(f"bundle exposes the wrong sole HEAD: {heads.stdout.strip()!r}")
    clone_head = ""
    clone_tree = ""
    with tempfile.TemporaryDirectory(
        prefix="normshift-bundle-clone-",
        ignore_cleanup_errors=True,
    ) as temp_name:
        clone = Path(temp_name) / "repo.git"
        recorder.run(
            "bundle_clone",
            "other",
            ("git", "clone", "--bare", "--no-hardlinks", bundle, clone),
        )
        clone_head = recorder.run(
            "bundle_clone_head",
            "other",
            ("git", "-C", clone, "rev-parse", "HEAD"),
        ).stdout.strip()
        clone_tree = recorder.run(
            "bundle_clone_tree",
            "other",
            ("git", "-C", clone, "rev-parse", "HEAD^{tree}"),
        ).stdout.strip()
        recorder.run(
            "bundle_fsck",
            "other",
            ("git", "-C", clone, "fsck", "--full", "--strict"),
        )
    if (clone_head, clone_tree) != (commit, tree):
        raise PackageBuildError("bundle clone HEAD/tree does not match the exact package subject")

    prefix = f"{package_base}/"
    source_zip = package_root / f"{package_base}-Source.zip"
    recorder.run(
        "source_archive",
        "source_archive",
        (
            "git",
            "archive",
            "--format=zip",
            f"--prefix={prefix}",
            f"--output={source_zip}",
            commit,
        ),
    )
    archive_evidence = _inspect_source_archive(source_zip, repo, commit, prefix)
    return GitProducts(
        bundle=bundle,
        source_zip=source_zip,
        bundle_evidence={"head": clone_head, "tree": clone_tree, "fsck": True},
        archive_evidence=archive_evidence,
    )


def _run_extracted_archive_check(
    recorder: CommandRecorder,
    source_zip: Path,
    prefix: str,
) -> bool:
    with tempfile.TemporaryDirectory(prefix="normshift-source-extract-") as temp_name:
        extracted = _extract_source_archive(source_zip, Path(temp_name) / "source", prefix)
        extracted_report = extracted / REPLAY_REPORT_PATH
        if not extracted_report.is_file():
            raise PackageBuildError(f"source archive lacks replay report: {REPLAY_REPORT_PATH}")
        result = recorder.run(
            "extracted_archive_verify",
            "extracted_archive_verify",
            (
                "uv",
                "run",
                "--frozen",
                "normshift",
                "verify",
                extracted_report,
                "--source-root",
                extracted,
            ),
        )
        _require_full_verify(result, "extracted source archive")
    return True


@dataclass(frozen=True)
class DistributionProducts:
    wheel: Path
    sdist: Path
    sbom: Path
    runtime_requirements: Path
    distribution_requirements: Path
    sbom_evidence: dict[str, Any]


def _metadata_requires_dist(artifact: Path) -> list[str]:
    raw: bytes
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                raise PackageBuildError(f"wheel has {len(names)} METADATA files")
            raw = archive.read(names[0])
    elif artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact, mode="r:gz") as archive:
            members = [
                member
                for member in archive.getmembers()
                if member.isfile() and member.name.endswith("/PKG-INFO")
            ]
            if len(members) != 1:
                raise PackageBuildError(f"sdist has {len(members)} PKG-INFO files")
            stream = archive.extractfile(members[0])
            if stream is None:
                raise PackageBuildError("cannot read sdist PKG-INFO")
            raw = stream.read()
    else:
        raise PackageBuildError(f"unsupported distribution artifact: {artifact.name}")
    message = BytesParser(policy=email_policy).parsebytes(raw)
    return list(message.get_all("Requires-Dist", []))


def _normalized_requirement(raw: str) -> dict[str, Any]:
    try:
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name

        requirement = Requirement(raw)
    except (ImportError, ValueError) as exc:
        raise PackageBuildError(f"invalid Requires-Dist value {raw!r}: {exc}") from exc
    return {
        "name": canonicalize_name(requirement.name),
        "extras": sorted(requirement.extras),
        "specifier": str(requirement.specifier),
        "url": requirement.url,
        "marker": str(requirement.marker) if requirement.marker is not None else None,
    }


def _requirement_sort_key(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _render_requirement(item: dict[str, Any]) -> str:
    extras = item["extras"]
    rendered = str(item["name"])
    if extras:
        rendered += f"[{','.join(str(extra) for extra in extras)}]"
    if item["url"] is not None:
        rendered += f" @ {item['url']}"
    else:
        rendered += str(item["specifier"])
    if item["marker"] is not None:
        rendered += f"; {item['marker']}"
    return rendered


def _validate_distribution_requirements(
    repo: Path,
    wheel: Path,
    sdist: Path,
    sbom_evidence: dict[str, Any],
    output: Path,
) -> list[str]:
    wheel_requirements = sorted(
        (_normalized_requirement(raw) for raw in _metadata_requires_dist(wheel)),
        key=_requirement_sort_key,
    )
    sdist_requirements = sorted(
        (_normalized_requirement(raw) for raw in _metadata_requires_dist(sdist)),
        key=_requirement_sort_key,
    )
    if wheel_requirements != sdist_requirements:
        raise PackageBuildError("wheel and sdist Requires-Dist metadata differ")

    pyproject = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject.get("project")
    dependencies = project.get("dependencies") if isinstance(project, dict) else None
    if not isinstance(dependencies, list) or not all(
        isinstance(item, str) for item in dependencies
    ):
        raise PackageBuildError("pyproject runtime dependencies are missing or invalid")
    expected_runtime = sorted(
        (_normalized_requirement(raw) for raw in dependencies),
        key=_requirement_sort_key,
    )
    actual_runtime = [
        item
        for item in wheel_requirements
        if item["marker"] is None or "extra ==" not in str(item["marker"])
    ]
    if actual_runtime != expected_runtime:
        raise PackageBuildError("distribution runtime Requires-Dist differs from pyproject")

    raw_inventory = sbom_evidence.get("inventory")
    if not isinstance(raw_inventory, list):
        raise PackageBuildError("SBOM inventory is unavailable for Requires-Dist join")
    inventory_names = {
        re.sub(r"[-_.]+", "-", str(item.get("name", ""))).lower()
        for item in raw_inventory
        if isinstance(item, dict)
    }
    missing = sorted(
        str(item["name"]) for item in actual_runtime if str(item["name"]) not in inventory_names
    )
    if missing:
        raise PackageBuildError(
            f"distribution Requires-Dist names missing from frozen lock/SBOM: {missing}"
        )
    _write_json(
        output,
        {
            "wheel_equals_sdist": True,
            "runtime_equals_pyproject": True,
            "runtime_joined_to_lock_sbom": True,
            "runtime": actual_runtime,
            "all_requires_dist": wheel_requirements,
        },
    )
    return [_render_requirement(item) for item in actual_runtime]


def _build_distributions_and_sbom(
    recorder: CommandRecorder,
    repo: Path,
    package_root: Path,
    project_name: str,
    version: str,
) -> DistributionProducts:
    raw_dist_dir = package_root / "_raw-build-dist"
    canonical_dist_dir = package_root / "_build-dist"
    raw_dist_dir.mkdir()
    canonical_dist_dir.mkdir()
    recorder.run(
        "build_distributions",
        "build",
        ("uv", "build", "--out-dir", raw_dist_dir, "--no-create-gitignore"),
    )
    raw_wheel = raw_dist_dir / f"{project_name}-{version}-py3-none-any.whl"
    raw_sdist = raw_dist_dir / f"{project_name}-{version}.tar.gz"
    wheels = sorted(raw_dist_dir.glob("*.whl"))
    sdists = sorted(raw_dist_dir.glob("*.tar.gz"))
    if wheels != [raw_wheel] or sdists != [raw_sdist]:
        raise PackageBuildError(
            "uv build did not emit exactly the canonical wheel and sdist names: "
            f"wheels={wheels}, sdists={sdists}"
        )
    expected_wheel = canonical_dist_dir / raw_wheel.name
    recorder.run(
        "normalize_wheel",
        "other",
        (
            sys.executable,
            "-B",
            repo / "scripts" / "normalize_wheel.py",
            raw_wheel,
            "--output",
            expected_wheel,
        ),
    )
    try:
        assert_canonical_wheel_file(expected_wheel)
    except WheelNormalizationError as exc:
        raise PackageBuildError(f"built wheel was not canonicalized: {exc}") from exc
    wheel = package_root / expected_wheel.name
    sdist = package_root / raw_sdist.name
    shutil.move(expected_wheel, wheel)
    shutil.move(raw_sdist, sdist)
    raw_wheel.unlink()
    raw_dist_dir.rmdir()
    canonical_dist_dir.rmdir()

    sbom = package_root / f"{project_name}-{version}-sbom.cdx.json"
    sbom_argv = (*SBOM_EXPORT_ARGV, "--output-file", str(sbom))
    recorder.run("sbom_export", "sbom", sbom_argv)
    _validate_sbom_schema(sbom)
    validation_code = (
        "from pathlib import Path; "
        "from cyclonedx import __version__; "
        "from cyclonedx.schema import SchemaVersion; "
        "from cyclonedx.validation.json import JsonStrictValidator; "
        "import sys; "
        "r=JsonStrictValidator(SchemaVersion.V1_5).validate_str("
        "Path(sys.argv[1]).read_text(encoding='utf-8'),all_errors=True); "
        "print(f'cyclonedx-python-lib={__version__}'); "
        "sys.exit(0 if r is None else 1)"
    )
    validator = recorder.run(
        "sbom_validate",
        "other",
        ("uv", "run", "--frozen", "python", "-c", validation_code, sbom),
    )
    if validator.stdout.strip() != "cyclonedx-python-lib=11.11.0":
        raise PackageBuildError("unexpected CycloneDX validator version")
    sbom_evidence = _validate_and_join_sbom(
        sbom,
        repo / "uv.lock",
        project_name,
        version,
        sbom_argv,
    )
    distribution_requirements = package_root / "evidence" / "distribution-requirements.json"
    distribution_requirement_values = _validate_distribution_requirements(
        repo,
        wheel,
        sdist,
        sbom_evidence,
        distribution_requirements,
    )
    sbom_evidence["distribution_requirements"] = distribution_requirement_values

    runtime_requirements = package_root / "runtime-requirements.txt"
    recorder.run(
        "runtime_lock_export",
        "other",
        (
            "uv",
            "export",
            "--frozen",
            "--no-dev",
            "--no-editable",
            "--no-emit-project",
            "--format",
            "requirements.txt",
            "--output-file",
            runtime_requirements,
        ),
    )
    return DistributionProducts(
        wheel=wheel,
        sdist=sdist,
        sbom=sbom,
        runtime_requirements=runtime_requirements,
        distribution_requirements=distribution_requirements,
        sbom_evidence=sbom_evidence,
    )


def _isolated_environment(
    *,
    source_date_epoch: str | None = None,
    gate_state_root: Path | None = None,
) -> dict[str, str]:
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
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if source_date_epoch is not None:
        env["SOURCE_DATE_EPOCH"] = source_date_epoch
    if gate_state_root is not None:
        state_root = gate_state_root.resolve()
        env["HYPOTHESIS_STORAGE_DIRECTORY"] = str(state_root / "hypothesis")
        env["MYPY_CACHE_DIR"] = str(state_root / "mypy")
        env["RUFF_CACHE_DIR"] = str(state_root / "ruff")
        env["UV_PROJECT_ENVIRONMENT"] = str(state_root / "venv")
    return env


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _run_distribution_smoke(
    recorder: CommandRecorder,
    repo: Path,
    artifact: Path,
    runtime_requirements: Path,
    version: str,
    kind: str,
) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"normshift-{kind}-smoke-") as temp_name:
        root = Path(temp_name)
        source_dir = root / "fixtures" / "synthetic"
        source_dir.mkdir(parents=True)
        for name in ("spec-v1.html", "spec-v2.html"):
            shutil.copyfile(repo / "fixtures" / "synthetic" / name, source_dir / name)
        venv = root / "venv"
        env = _isolated_environment()
        recorder.run(
            f"{kind}_venv",
            f"{kind}_smoke",
            ("uv", "venv", "--python", "3.12", venv),
            env=env,
        )
        python = _venv_python(venv)
        recorder.run(
            f"{kind}_locked_dependencies",
            f"{kind}_smoke",
            (
                "uv",
                "pip",
                "install",
                "--python",
                python,
                "--require-hashes",
                "--requirements",
                runtime_requirements,
            ),
            env=env,
        )
        recorder.run(
            f"{kind}_install",
            f"{kind}_smoke",
            ("uv", "pip", "install", "--python", python, "--no-deps", artifact),
            env=env,
        )
        metadata_code = (
            "from importlib.metadata import entry_points, version; "
            "from importlib.resources import files; "
            "import sys; "
            f"assert version('normshift') == {version!r}; "
            "assert any(e.name == 'normshift' for e in "
            "entry_points(group='console_scripts')); "
            "r=files('normshift.schemas'); "
            "assert all(r.joinpath(n).is_file() for n in "
            "('report.schema.json','change.schema.json','requirement.schema.json',"
            "'package_manifest_v1.schema.json','command_log_v1.schema.json',"
            "'m1_source_manifest_v1.schema.json')); "
            "print('metadata-entrypoint-schemas=PASS')"
        )
        metadata = recorder.run(
            f"{kind}_metadata",
            f"{kind}_smoke",
            (python, "-c", metadata_code),
            env=env,
        )
        if metadata.stdout.strip() != "metadata-entrypoint-schemas=PASS":
            raise PackageBuildError(f"{kind} metadata/schema smoke did not report PASS")
        version_result = recorder.run(
            f"{kind}_version",
            f"{kind}_smoke",
            (python, "-m", "normshift", "--version"),
            env=env,
        )
        if version not in version_result.stdout:
            raise PackageBuildError(f"{kind} CLI version does not identify {version}")
        recorder.run(
            f"{kind}_help",
            f"{kind}_smoke",
            (python, "-m", "normshift", "--help"),
            env=env,
        )
        report = root / "report.json"
        markdown = root / "report.md"
        recorder.run(
            f"{kind}_diff",
            f"{kind}_smoke",
            (
                python,
                "-m",
                "normshift",
                "diff",
                source_dir / "spec-v1.html",
                source_dir / "spec-v2.html",
                "--source-root",
                root,
                "--profile",
                "rfc2119",
                "--json",
                report,
                "--markdown",
                markdown,
            ),
            env=env,
        )
        verify = recorder.run(
            f"{kind}_verify",
            f"{kind}_smoke",
            (
                python,
                "-m",
                "normshift",
                "verify",
                report,
                "--source-root",
                root,
            ),
            env=env,
        )
        _require_full_verify(verify, f"isolated {kind}")
    return True


def _validate_json_document(document: dict[str, Any], schema_path: Path, label: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise PackageBuildError("jsonschema is required to validate package documents") from exc
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise PackageBuildError(f"cannot parse {label} schema: {exc}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda item: list(item.path),
    )
    if errors:
        rendered = [
            f"{'.'.join(str(part) for part in error.path)}: {error.message}" for error in errors
        ]
        raise PackageBuildError(f"{label} does not validate: {rendered[:10]}")


def _log_records(recorder: CommandRecorder) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for result in recorder.results:
        path = recorder.package_root / "logs" / f"{result.id}.json"
        records[result.id] = _file_record(path, recorder.package_root)
    return records


def _determinism_file_refs(
    determinism: dict[str, Any],
    files: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    by_path = {str(record["path"]): record_id for record_id, record in files.items()}
    converted: dict[str, Any] = {}
    for label, comparison in determinism.items():
        if not isinstance(comparison, dict):
            raise PackageBuildError(f"invalid determinism comparison: {label}")
        first_path = str(comparison.get("first"))
        second_path = str(comparison.get("second"))
        if first_path not in by_path or second_path not in by_path:
            raise PackageBuildError(f"determinism files are not retained: {label}")
        converted[label] = {
            "first": by_path[first_path],
            "second": by_path[second_path],
            "equal": comparison.get("equal") is True,
        }
    return converted


def _matrix_cases(summary: PytestSummary) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for case in summary.cases:
        outcome = case.get("outcome")
        cases.append(
            {
                "id": str(case["id"]),
                "expected_exit": "zero",
                "actual_exit_code": 0 if outcome == "passed" else 1,
            }
        )
    return cases


def _failed_attempt_path(staging: Path, failure_path: Path, error: BaseException) -> Path:
    try:
        _write_json(
            staging / "BUILD-FAILED.json",
            {"failed_at": _utc_now(), "error_type": type(error).__name__, "error": str(error)},
        )
        staging.replace(failure_path)
        return failure_path
    except OSError:
        return staging


def build_authoritative_package(config: BuildConfig) -> Path:
    """Build and return one authoritative package directory.

    No MANIFEST is written until every command and package invariant passes.  A
    failed attempt is retained with ``BUILD-FAILED.json`` and cannot be mistaken
    for an authoritative candidate.
    """
    repo = config.repo.resolve()
    output_root = config.output_root.resolve()
    _assert_output_outside_repo(repo, output_root)
    identity = _assert_clean_exact_checkout(config, reject_ignored=True)
    project_name, version, build_backend = _project_metadata(repo)
    source_date_epoch = _git(repo, "show", "-s", "--format=%ct", identity.commit)
    if not re.fullmatch(r"[1-9][0-9]{8,11}", source_date_epoch):
        raise PackageBuildError("package commit has an invalid SOURCE_DATE_EPOCH")
    run_id = config.run_id or new_run_id()
    if not RUN_ID_RE.fullmatch(run_id):
        raise PackageBuildError("run ID contains unsafe characters or has an invalid length")
    package_base = f"NormShift-{version}-{run_id}"
    if len(package_base) > 128 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", package_base):
        raise PackageBuildError("package version/run ID cannot form a canonical archive prefix")
    output_root.mkdir(parents=True, exist_ok=True)
    final_path = output_root / package_base
    failure_path = output_root / f"{package_base}-FAILED"
    if final_path.exists() or failure_path.exists():
        raise PackageBuildError(f"run ID already exists under output root: {run_id}")

    staging = Path(tempfile.mkdtemp(prefix=f".{package_base}-", dir=output_root))
    started_at = _utc_now()
    gate_state = tempfile.TemporaryDirectory(prefix="normshift-gate-state-")
    recorder = CommandRecorder(
        staging,
        repo,
        source_date_epoch=source_date_epoch,
        gate_state_root=Path(gate_state.name),
    )
    manifest_name = f"{package_base}-MANIFEST.json"
    checksums_name = f"{package_base}-CHECKSUMS.txt"
    try:
        contract_source = repo / "docs" / "M0_AUDIT_CONTRACT.md"
        manifest_schema_source = repo / "schemas" / "package_manifest_v1.schema.json"
        command_log_schema = repo / "schemas" / "command_log_v1.schema.json"
        for required_path in (contract_source, manifest_schema_source, command_log_schema):
            if not required_path.is_file():
                raise PackageBuildError(
                    f"required tracked package contract is missing: {required_path}"
                )

        audit_contract = staging / f"{package_base}-AUDIT-CONTRACT.md"
        manifest_schema = staging / f"{package_base}-MANIFEST.schema.json"
        shutil.copyfile(contract_source, audit_contract)
        shutil.copyfile(manifest_schema_source, manifest_schema)
        _copy_frozen_inputs(repo, staging)

        gate_evidence = _run_required_product_gates(recorder, repo, staging)
        relocation_verify = _run_relocation_check(recorder, repo, gate_evidence.report_one)
        git_products = _build_git_products(
            recorder,
            repo,
            staging,
            package_base,
            identity.commit,
            identity.tree,
        )
        extracted_archive_verify = _run_extracted_archive_check(
            recorder,
            git_products.source_zip,
            git_products.archive_evidence["prefix"],
        )
        distributions = _build_distributions_and_sbom(
            recorder,
            repo,
            staging,
            project_name,
            version,
        )
        wheel_smoke = _run_distribution_smoke(
            recorder,
            repo,
            distributions.wheel,
            distributions.runtime_requirements,
            version,
            "wheel",
        )
        sdist_smoke = _run_distribution_smoke(
            recorder,
            repo,
            distributions.sdist,
            distributions.runtime_requirements,
            version,
            "sdist",
        )

        post_identity = _assert_clean_exact_checkout(config, reject_ignored=True)
        if post_identity != identity:
            raise PackageBuildError("checkout identity changed while package gates were running")

        checksums = _write_checksums(staging, checksums_name, manifest_name)
        logs = _log_records(recorder)
        files = _records_under(staging, "evidence")
        files.update(_records_under(staging, "frozen-inputs"))
        runtime_path = distributions.runtime_requirements.relative_to(staging).as_posix()
        runtime_record_id = _file_id(runtime_path)
        files[runtime_record_id] = _file_record(distributions.runtime_requirements, staging)
        distributions.sbom_evidence["runtime_requirements_file"] = runtime_record_id
        pytest_junit_id = _file_id(gate_evidence.pytest_junit.relative_to(staging).as_posix())
        matrix_junit_id = _file_id(gate_evidence.matrix_junit.relative_to(staging).as_posix())
        if pytest_junit_id not in files or matrix_junit_id not in files:
            raise PackageBuildError("retained JUnit evidence is missing from file records")
        determinism = _determinism_file_refs(gate_evidence.determinism, files)
        m1, m2 = _runtime_inventory_blocks(files)

        log_schema = json.loads(command_log_schema.read_text(encoding="utf-8"))
        for result in recorder.results:
            log_path = staging / str(logs[result.id]["path"])
            log_document = json.loads(log_path.read_text(encoding="utf-8"))
            _validate_json_document(log_document, command_log_schema, "command log")
        if not isinstance(log_schema, dict):
            raise PackageBuildError("command log schema is not an object")

        finished_at = _utc_now()
        manifest: dict[str, Any] = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "milestone": "M0",
            "run_id": run_id,
            "package_version": version,
            "package_commit": identity.commit,
            "package_tree": identity.tree,
            "repository": {
                "url": identity.repository_url,
                "default_branch": config.default_branch,
                "dirty": False,
            },
            "timestamps": {"started_at": started_at, "finished_at": finished_at},
            "environment": {
                "os": platform.platform(),
                "architecture": platform.machine(),
                "python": platform.python_version(),
                "uv": _checked_output(("uv", "--version"), repo),
                "git": _checked_output(("git", "--version"), repo),
                "build_frontend": "uv build",
                "build_backend": build_backend,
                "source_date_epoch": source_date_epoch,
                "gate_state_policy": "ephemeral_outside_repository",
                "normshift": version,
            },
            "status": {
                "m0": "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT",
                "m1": "EXPERIMENTAL_NOT_ADJUDICATED",
                "m2": "EXPERIMENTAL_NOT_ADJUDICATED",
                "release": "BLOCKED",
            },
            "m1": m1,
            "m2": m2,
            "working_directory_policy": "clean_exact_commit_repository_root",
            "artifacts": {
                "bundle": _file_record(git_products.bundle, staging),
                "source_zip": _file_record(git_products.source_zip, staging),
                "wheel": _file_record(distributions.wheel, staging),
                "sdist": _file_record(distributions.sdist, staging),
                "sbom": _file_record(distributions.sbom, staging),
                "checksums": _file_record(checksums, staging),
                "audit_contract": _file_record(audit_contract, staging),
                "manifest_schema": _file_record(manifest_schema, staging),
            },
            "logs": logs,
            "files": files,
            "commands": [result.manifest_record() for result in recorder.results],
            "counts": {
                "pytest": {
                    **gate_evidence.pytest.counts,
                    "junit_file": pytest_junit_id,
                },
                "benchmark": gate_evidence.benchmark,
                "measure": gate_evidence.measure,
            },
            "matrices": {
                "r4_r5": {
                    "log": "r4_r5",
                    "junit_file": matrix_junit_id,
                    "cases": _matrix_cases(gate_evidence.matrix),
                }
            },
            "archive": git_products.archive_evidence,
            "bundle": git_products.bundle_evidence,
            "determinism": determinism,
            "sbom": distributions.sbom_evidence,
            "replay": {
                "report_path": REPLAY_REPORT_PATH,
                "source_root": ".",
                "expected_scope": "FULL",
            },
            "checks": {
                "relocation_verify": relocation_verify,
                "extracted_archive_verify": extracted_archive_verify,
                "wheel_smoke": wheel_smoke,
                "sdist_smoke": sdist_smoke,
            },
            "known_limitations": [
                (
                    "M0 classification is a deterministic bounded taxonomy, not full "
                    "natural-language understanding."
                ),
                "The package is pending a detached clean-room external audit of these exact bytes.",
            ],
            "unclaimed_scopes": [
                "M1 and M2 external acceptance",
                "production readiness, hosted-service operation, adoption, or universal accuracy",
                "cryptographic authenticity or signer identity",
            ],
        }
        _validate_json_document(manifest, manifest_schema_source, "package manifest")
        _write_json(staging / manifest_name, manifest)
        staging.replace(final_path)
        return final_path
    except BaseException as exc:
        retained = _failed_attempt_path(staging, failure_path, exc)
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise PackageBuildError(
            f"package attempt failed; diagnostics retained at {retained}: {exc}"
        ) from exc
    finally:
        gate_state.cleanup()
