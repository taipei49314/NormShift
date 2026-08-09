from __future__ import annotations

import io
import json
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest

from normshift.audit import package_build
from normshift.audit.package_build import BuildConfig, PackageBuildError


def test_new_run_id_is_unique_and_portable() -> None:
    first = package_build.new_run_id()
    second = package_build.new_run_id()

    assert first != second
    assert package_build.RUN_ID_RE.fullmatch(first)
    assert package_build.RUN_ID_RE.fullmatch(second)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -0.0])
def test_canonical_package_json_rejects_noncanonical_numbers(value: float) -> None:
    with pytest.raises(PackageBuildError, match="non-finite|negative zero"):
        package_build._canonical_json_bytes({"value": value})


@pytest.mark.parametrize(
    "url",
    [
        "https://token@github.com/taipei49314/NormShift.git",
        "https://github.com/taipei49314/NormShift.git?token=secret",
        "https://github.com/taipei49314/NormShift.git#fragment",
        "https://example.test/taipei49314/NormShift.git",
    ],
)
def test_repository_url_rejects_credentials_and_nonpublic_subject(url: str) -> None:
    with pytest.raises(PackageBuildError, match="public NormShift GitHub URL"):
        package_build._normalize_repository_url(url)


def test_repository_url_accepts_only_normshift_public_https_forms() -> None:
    assert package_build._normalize_repository_url(
        "https://github.com/taipei49314/NormShift"
    ) == "https://github.com/taipei49314/NormShift"
    assert package_build._normalize_repository_url(
        "git@github.com:taipei49314/NormShift.git".replace(
            "git@github.com:", "https://github.com/"
        )
    ) == "https://github.com/taipei49314/NormShift.git"


def test_default_branch_subject_requires_exact_remote_default_sha(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    commit = "a" * 40

    def fake_run_raw(
        argv: object,
        cwd: Path,
    ) -> subprocess.CompletedProcess[bytes]:
        del argv, cwd
        return subprocess.CompletedProcess([], 0, ("b" * 40).encode(), b"")

    monkeypatch.setattr(package_build, "_run_raw", fake_run_raw)
    with pytest.raises(PackageBuildError, match="not the exact origin/master commit"):
        package_build._assert_default_branch_subject(tmp_path, "master", commit)


def test_default_branch_subject_rejects_noncontract_branch(tmp_path: Path) -> None:
    with pytest.raises(PackageBuildError, match="requires default branch 'master'"):
        package_build._assert_default_branch_subject(tmp_path, "main", "a" * 40)


def test_exact_checkout_rejects_dirty_tree(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit = "a" * 40

    def fake_git(_repo: Path, *args: str) -> str:
        command = " ".join(args)
        if command == "rev-parse --show-toplevel":
            return str(repo)
        if command == "rev-parse --verify HEAD^{commit}":
            return commit
        if command == "status --porcelain=v1 --untracked-files=all":
            return "?? untracked.txt"
        raise AssertionError(command)

    monkeypatch.setattr(package_build, "_git", fake_git)
    config = BuildConfig(repo=repo, output_root=tmp_path / "out", expected_commit=commit)
    with pytest.raises(PackageBuildError, match="dirty"):
        package_build._assert_clean_exact_checkout(config)


def test_exact_checkout_requires_requested_full_sha(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def fake_git(_repo: Path, *args: str) -> str:
        if args == ("rev-parse", "--show-toplevel"):
            return str(repo)
        raise AssertionError(args)

    monkeypatch.setattr(package_build, "_git", fake_git)
    config = BuildConfig(repo=repo, output_root=tmp_path / "out", expected_commit="abc")
    with pytest.raises(PackageBuildError, match="full lowercase 40-character"):
        package_build._assert_clean_exact_checkout(config)


def test_exact_checkout_rejects_preexisting_ignored_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit = "a" * 40

    def fake_git(_repo: Path, *args: str) -> str:
        command = " ".join(args)
        if command == "rev-parse --show-toplevel":
            return str(repo)
        if command == "rev-parse --verify HEAD^{commit}":
            return commit
        if command == "status --porcelain=v1 --untracked-files=all":
            return ""
        if command == "status --porcelain=v1 --untracked-files=all --ignored=matching":
            return "!! .venv/"
        if command == "rev-parse HEAD^{tree}":
            return "b" * 40
        if command == "remote get-url origin":
            return "https://example.test/normshift"
        raise AssertionError(command)

    monkeypatch.setattr(package_build, "_git", fake_git)
    config = BuildConfig(repo=repo, output_root=tmp_path / "out", expected_commit=commit)

    with pytest.raises(PackageBuildError, match="ignored state"):
        package_build._assert_clean_exact_checkout(config, reject_ignored=True)


def test_output_root_must_be_outside_checkout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(PackageBuildError, match="outside"):
        package_build._assert_output_outside_repo(repo, repo / "candidate")


def test_project_metadata_records_backend_module_and_version(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "normshift"
version = "1.2.3"
[build-system]
requires = ["hatchling==1.31.0"]
build-backend = "hatchling.build"
""".lstrip(),
        encoding="utf-8",
    )

    assert package_build._project_metadata(tmp_path) == (
        "normshift",
        "1.2.3",
        {
            "module": "hatchling.build",
            "distribution": "hatchling",
            "version": "1.31.0",
        },
    )


def test_command_recorder_retains_both_streams_and_timestamps(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    package = tmp_path / "package"
    repo.mkdir()
    package.mkdir()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        del args, kwargs
        return subprocess.CompletedProcess(["tool"], 0, b"output\n", b"warning\n")

    monkeypatch.setattr(package_build.subprocess, "run", fake_run)
    recorder = package_build.CommandRecorder(package, repo, source_date_epoch="1750000000")
    result = recorder.run("gate", "other", ("tool", "--flag"))
    log = json.loads((package / "logs" / "gate.json").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert result.required is True
    assert log["schema_version"] == "normshift-command-log/v1"
    assert log["command_id"] == "gate"
    assert log["stdout"] == "output\n"
    assert log["stderr"] == "warning\n"
    assert log["started_at"].endswith("Z")
    assert log["finished_at"].endswith("Z")


def test_command_recorder_sanitizes_inherited_python_and_pytest_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    package = tmp_path / "package"
    repo.mkdir()
    package.mkdir()
    captured: dict[str, str] = {}
    for name in (
        "PYTHONHOME",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "COVERAGE_PROCESS_START",
        "UV_PROJECT_ENVIRONMENT",
    ):
        monkeypatch.setenv(name, "host-controlled")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        del args
        captured.update(kwargs["env"])
        return subprocess.CompletedProcess(["tool"], 0, b"", b"")

    monkeypatch.setattr(package_build.subprocess, "run", fake_run)
    package_build.CommandRecorder(package, repo, source_date_epoch="1750000000").run(
        "gate", "other", ("tool",)
    )

    for name in (
        "PYTHONHOME",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "COVERAGE_PROCESS_START",
        "UV_PROJECT_ENVIRONMENT",
    ):
        assert name not in captured
    assert captured["PYTHONNOUSERSITE"] == "1"
    assert captured["PYTHONUTF8"] == "1"
    assert captured["SOURCE_DATE_EPOCH"] == "1750000000"


def test_command_recorder_redirects_all_gate_state_outside_repo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    package = tmp_path / "package"
    state = tmp_path / "gate-state"
    repo.mkdir()
    package.mkdir()
    captured: dict[str, str] = {}

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        del args
        captured.update(kwargs["env"])
        return subprocess.CompletedProcess(["tool"], 0, b"", b"")

    monkeypatch.setattr(package_build.subprocess, "run", fake_run)
    package_build.CommandRecorder(
        package,
        repo,
        source_date_epoch="1750000000",
        gate_state_root=state,
    ).run("gate", "other", ("tool",))

    assert captured["UV_PROJECT_ENVIRONMENT"] == str(state / "venv")
    assert captured["HYPOTHESIS_STORAGE_DIRECTORY"] == str(state / "hypothesis")
    assert captured["MYPY_CACHE_DIR"] == str(state / "mypy")
    assert captured["RUFF_CACHE_DIR"] == str(state / "ruff")
    assert "PYTEST_ADDOPTS" not in captured
    assert captured["PYTHONDONTWRITEBYTECODE"] == "1"


def test_command_recorder_fails_closed_after_writing_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    package = tmp_path / "package"
    repo.mkdir()
    package.mkdir()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        del args, kwargs
        return subprocess.CompletedProcess(["tool"], 9, b"", b"failure")

    monkeypatch.setattr(package_build.subprocess, "run", fake_run)
    recorder = package_build.CommandRecorder(package, repo, source_date_epoch="1750000000")
    with pytest.raises(PackageBuildError, match="exit 9"):
        recorder.run("bad_gate", "other", ("tool",))
    assert (package / "logs" / "bad_gate.json").is_file()


def test_junit_counts_passes_and_preserves_node_id(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """<?xml version="1.0"?>
<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0">
<testcase classname="tests.e2e.test_m0_repair_round5" name="test_signed_zero" />
</testsuite></testsuites>""",
        encoding="utf-8",
    )

    summary = package_build._parse_junit(junit)
    package_build._require_clean_pytest(summary, "matrix")

    assert summary.counts == {
        "collected": 1,
        "passed": 1,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "errors": 0,
    }
    assert summary.cases == [
        {
            "id": "tests/e2e/test_m0_repair_round5.py::test_signed_zero",
            "outcome": "passed",
        }
    ]


@pytest.mark.parametrize(
    ("skipped_type", "count_name"),
    [("pytest.skip", "skipped"), ("pytest.xfail", "xfailed")],
)
def test_junit_rejects_skip_and_xfail(
    tmp_path: Path,
    skipped_type: str,
    count_name: str,
) -> None:
    junit = tmp_path / f"{count_name}.xml"
    junit.write_text(
        "<testsuite><testcase classname=\"tests.x\" name=\"test_y\">"
        f"<skipped type=\"{skipped_type}\" /></testcase></testsuite>",
        encoding="utf-8",
    )
    summary = package_build._parse_junit(junit)
    assert summary.counts[count_name] == 1
    with pytest.raises(PackageBuildError, match="no-skip"):
        package_build._require_clean_pytest(summary, "pytest")


def test_junit_rejects_xpass_from_pytest_terminal_summary(tmp_path: Path) -> None:
    junit = tmp_path / "xpass.xml"
    junit.write_text(
        "<testsuite><testcase classname=\"tests.x\" name=\"test_y\" /></testsuite>",
        encoding="utf-8",
    )
    summary = package_build._parse_junit(junit, "XPASS tests/x.py::test_y reason\n")
    assert summary.counts["xpassed"] == 1
    with pytest.raises(PackageBuildError, match="xpassed"):
        package_build._require_clean_pytest(summary, "pytest")


def test_junit_rejects_class_xpass_with_flattened_classname(tmp_path: Path) -> None:
    junit = tmp_path / "class-xpass.xml"
    junit.write_text(
        '<testsuite><testcase classname="tests.x.TestFeature" name="test_y" /></testsuite>',
        encoding="utf-8",
    )
    terminal = "XPASS tests/x.py::TestFeature::test_y reason\n"

    summary = package_build._parse_junit(junit, terminal)

    assert summary.counts["passed"] == 0
    assert summary.counts["xpassed"] == 1
    with pytest.raises(PackageBuildError, match="xpassed"):
        package_build._require_clean_pytest(summary, "pytest")


def test_benchmark_parser_requires_exact_17_cases() -> None:
    case_lines = [f"[PASS] case-{index:02}: ok" for index in range(17)]
    output = "\n".join([*case_lines, "benchmark: 17/17 passed, 0 failed"])
    parsed = package_build._parse_benchmark(output)

    assert parsed["total"] == 17
    assert parsed["passed"] == 17
    assert len(parsed["cases"]) == 17
    assert set(parsed["cases"][0]) == {"id", "passed"}


def test_measure_parser_requires_exact_15_and_records_layer_metrics(tmp_path: Path) -> None:
    path = tmp_path / "metrics.json"
    metric = {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    path.write_text(
        json.dumps(
            {
                "case_count": 15,
                "cases_passed": 15,
                "cases_failed": 0,
                "case_results": [
                    {"case_id": f"case-{index:02}", "passed": True} for index in range(15)
                ],
                "extraction": metric,
                "alignment": metric,
                "classification": {**metric, "case_pass_rate": 1.0},
            }
        ),
        encoding="utf-8",
    )

    parsed = package_build._parse_measure(path)

    assert parsed["total"] == 15
    assert parsed["metrics"] == {
        "extraction": metric,
        "alignment": metric,
        "classification": metric,
    }
    assert set(parsed["cases"][0]) == {"id", "passed"}


def test_sbom_inventory_is_joined_to_exact_uv_lock_sources(tmp_path: Path) -> None:
    sbom_path = tmp_path / "sbom.json"
    lock_path = tmp_path / "uv.lock"
    sbom_path.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.5",
                "metadata": {
                    "tools": [{"name": "uv", "version": "0.12.2"}],
                    "component": {"name": "normshift", "version": "0.3.2"},
                },
                "components": [{"name": "typer", "version": "0.27.1"}],
            }
        ),
        encoding="utf-8",
    )
    lock_path.write_text(
        """version = 1
[[package]]
name = "typer"
version = "0.27.1"
source = { registry = "https://pypi.org/simple" }
""",
        encoding="utf-8",
    )
    argv = [*package_build.SBOM_EXPORT_ARGV, "--output-file", str(sbom_path)]

    evidence = package_build._validate_and_join_sbom(
        sbom_path,
        lock_path,
        "normshift",
        "0.3.2",
        argv,
    )

    assert evidence["generator_argv"] == argv
    assert evidence["inventory"] == [
        {
            "name": "typer",
            "version": "0.27.1",
            "source": "registry:https://pypi.org/simple",
        }
    ]
    assert re.fullmatch(r"[0-9a-f]{64}", evidence["lockfile_sha256"])


def test_distribution_requirements_match_wheel_sdist_pyproject_and_lock(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "normshift"\nversion = "1.2.3"\n'
        'dependencies = ["typer>=0.12", "lxml>=5"]\n',
        encoding="utf-8",
    )
    metadata = (
        b"Metadata-Version: 2.4\nName: normshift\nVersion: 1.2.3\n"
        b"Requires-Dist: typer>=0.12\nRequires-Dist: lxml>=5\n\n"
    )
    wheel = tmp_path / "normshift-1.2.3-py3-none-any.whl"
    with zipfile.ZipFile(wheel, mode="w") as archive:
        archive.writestr("normshift-1.2.3.dist-info/METADATA", metadata)
    sdist = tmp_path / "normshift-1.2.3.tar.gz"
    with tarfile.open(sdist, mode="w:gz") as archive:
        info = tarfile.TarInfo("normshift-1.2.3/PKG-INFO")
        info.size = len(metadata)
        archive.addfile(info, io.BytesIO(metadata))
    output = tmp_path / "requirements.json"

    package_build._validate_distribution_requirements(
        repo,
        wheel,
        sdist,
        {"inventory": [{"name": "typer"}, {"name": "lxml"}]},
        output,
    )

    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["wheel_equals_sdist"] is True
    assert evidence["runtime_equals_pyproject"] is True
    assert evidence["runtime_joined_to_lock_sbom"] is True
    assert [item["name"] for item in evidence["runtime"]] == ["lxml", "typer"]


def test_checksums_exclude_manifest_and_checksum_self(tmp_path: Path) -> None:
    (tmp_path / "artifact.bin").write_bytes(b"artifact")
    (tmp_path / "candidate-MANIFEST.json").write_text("{}", encoding="utf-8")
    checksum = package_build._write_checksums(
        tmp_path,
        "candidate-CHECKSUMS.txt",
        "candidate-MANIFEST.json",
    )
    text = checksum.read_text(encoding="utf-8")

    assert "artifact.bin" in text
    assert "MANIFEST" not in text
    assert "CHECKSUMS" not in text


def test_file_record_ids_are_safe_and_scope_refs_resolve(tmp_path: Path) -> None:
    corpus = tmp_path / "frozen-inputs" / "fixtures" / "corpus" / "rfc"
    lineage = tmp_path / "frozen-inputs" / "fixtures" / "lineage"
    corpus.mkdir(parents=True)
    lineage.mkdir(parents=True)
    (corpus / "sample.html").write_text("rfc", encoding="utf-8")
    (lineage / "v1.html").write_text("v1", encoding="utf-8")
    (tmp_path / "frozen-inputs" / "uv.lock").write_text("version = 1\n", encoding="utf-8")

    files = package_build._records_under(tmp_path, "frozen-inputs")
    m1, m2 = package_build._runtime_inventory_blocks(files)

    assert "lockfile" in files
    assert all(
        record_id == "lockfile" or re.fullmatch(r"file\.[0-9a-f]{64}", record_id)
        for record_id in files
    )
    assert m1["corpus_refs"] and set(m1["corpus_refs"]) <= set(files)
    assert m2["corpus_refs"] and set(m2["corpus_refs"]) <= set(files)
    assert m1["acceptance_evaluated"] is False
    assert m2["acceptance_evaluated"] is False


@pytest.mark.parametrize(
    "member",
    ["/absolute", "prefix/../escape", "prefix/a\\b", "wrong/file", "prefix/a//b"],
)
def test_zip_member_grammar_rejects_unsafe_names(member: str) -> None:
    safe, _ = package_build._safe_zip_member(member, "prefix/")
    assert safe is False
