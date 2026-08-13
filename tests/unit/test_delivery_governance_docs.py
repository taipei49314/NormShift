from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_COMMIT = "b3af3dc26e64a3399545d179731222f6e87213c9"
HISTORICAL_TREE = "c629e2d51fc5219514d6068a90d3453725bd8010"
HISTORICAL_MANIFEST = "7e95576f71fd061fc010c542b7f91dc67075cd2c7bd8bfd2b801f90c846625db"
HISTORICAL_AUDIT = "88127b2a0d5985e4e00f392f031fdce7c3cc8281bdec2fb118e7fe86d83f2aac"
CURRENT_BASELINE_COMMIT = "f6897f71834a50d2273fda033a72b31254c65935"
CURRENT_BASELINE_TREE = "34cde504fab42da8f9423cd1ca226fe492307c36"
CURRENT_CI_URL = "https://github.com/taipei49314/NormShift/actions/runs/31462052663"
CURRENT_WHEEL_SHA256 = "b5ebc295dadb63ab2969185551ca62409e9290d9f9fba41916d188e6a833886d"
CURRENT_SDIST_SHA256 = "fb8f1f0add5a752cfa3a070edf0ed984835961b4f93a5c672c0f02ea6b2c4760"
EVIDENCE_URL = (
    "https://github.com/taipei49314/NormShift/releases/tag/"
    "m0-audit-20260809-b3af3dc"
)


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _powershell_blocks() -> list[str]:
    return re.findall(
        r"^```powershell\r?\n(.*?)^```\s*$",
        _text("RELEASE_CHECKLIST.md"),
        flags=re.MULTILINE | re.DOTALL,
    )


def _pwsh() -> str:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    assert executable is not None, "PowerShell is required to validate the release contract"
    return executable


def _run_release_helper_probe(
    probe: str,
    environment_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    blocks = _powershell_blocks()
    environment = os.environ.copy()
    if environment_overrides:
        environment.update(environment_overrides)
    harness = r"""
$Source = Get-Content -LiteralPath $env:NORMSHIFT_RELEASE_AUTHORITY_PATH -Raw
$Tokens = $null
$Errors = $null
$Ast = [System.Management.Automation.Language.Parser]::ParseInput(
  $Source, [ref] $Tokens, [ref] $Errors)
if ($Errors.Count -ne 0) {
  $Errors | ForEach-Object { [Console]::Error.WriteLine($_.Message) }
  exit 2
}
$Functions = $Ast.FindAll(
  { param($Node)
    $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] },
  $true)
$FunctionSource = ($Functions | ForEach-Object { $_.Extent.Text }) -join "`n"
Invoke-Expression $FunctionSource
"""
    with tempfile.TemporaryDirectory(prefix="normshift-release-authority-") as temp_name:
        authority_path = Path(temp_name) / "authority.ps1"
        authority_path.write_text(blocks[0], encoding="utf-8")
        environment["NORMSHIFT_RELEASE_AUTHORITY_PATH"] = str(authority_path)
        return subprocess.run(
            [
                _pwsh(),
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                harness + probe,
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )


def _run_release_authority(
    environment_overrides: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    authority = _powershell_blocks()[0]
    environment = os.environ.copy()
    environment.update(environment_overrides)
    with tempfile.TemporaryDirectory(prefix="normshift-release-authority-main-") as temp_name:
        authority_path = Path(temp_name) / "authority.ps1"
        authority_path.write_text(authority, encoding="utf-8")
        return subprocess.run(
            [_pwsh(), "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(authority_path)],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )


def test_mission_state_separates_historical_audit_from_current_subject() -> None:
    state = json.loads(_text("MISSION_STATE.json"))

    assert state["status"] == "M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT"
    assert state["package_identity"] == "pending_external_attestation"
    assert state["last_verified_commit"] is None
    assert state["release_status"] == "BLOCKED"

    audit = state["historical_external_audit"]
    assert audit["scope"] == "M0_ONLY"
    assert audit["verdict"] == "M0_EXTERNAL_AUDIT_PASS"
    assert audit["commit"] == HISTORICAL_COMMIT
    assert audit["tree"] == HISTORICAL_TREE
    assert audit["manifest_sha256"] == HISTORICAL_MANIFEST
    assert audit["audit_sha256"] == HISTORICAL_AUDIT
    assert audit["evidence_release"] == EVIDENCE_URL
    assert audit["m1"] == "NOT_ADJUDICATED"
    assert audit["m2"] == "NOT_ADJUDICATED"
    assert audit["release"] == "BLOCKED"
    assert audit["inheritance"] == "NON_TRANSITIVE_TO_DESCENDANT_COMMITS"

    baseline = state["verified_ancestor_internal_baseline"]
    assert baseline["commit"] == CURRENT_BASELINE_COMMIT
    assert baseline["tree"] == CURRENT_BASELINE_TREE
    assert baseline["ci_run"] == CURRENT_CI_URL
    assert baseline["ci_conclusion"] == "success"
    assert baseline["subject_relationship"] == (
        "ANCESTOR_DELIVERY_EVIDENCE_ONLY_NOT_CURRENT_EXACT_SUBJECT"
    )
    foundation = baseline["delivery_foundation"]
    assert foundation["status"] == "INTERNAL_CI_PASS_NOT_EXTERNAL_ACCEPTANCE"
    assert foundation["canonical_wheel_sha256"] == CURRENT_WHEEL_SHA256
    assert foundation["sdist_sha256"] == CURRENT_SDIST_SHA256
    assert foundation["artifact_count"] == 3
    assert foundation["authority"] == (
        "DELIVERY_FOUNDATION_ONLY_NOT_COMBINED_AUDIT_OR_RELEASE"
    )

    milestones = state["milestones"]
    assert milestones["m1"] == "EXPERIMENTAL_NOT_ADJUDICATED"
    assert milestones["m2"] == "EXPERIMENTAL_NOT_ADJUDICATED"
    assert milestones["final_combined_subject"] == "NOT_FROZEN"
    assert milestones["release"] == "BLOCKED"

    m2_foundations = state["implemented_experimental_foundations"]["m2"]
    assert any("LineageGraph v1 exact replay" in item for item in m2_foundations)
    assert any("DefinitionTransition v1" in item for item in m2_foundations)
    assert any("DefinitionReferenceCandidate v1" in item for item in m2_foundations)
    assert any(
        "do not assert semantic cross-references or indirect impact" in item
        for item in m2_foundations
    )
    assert "external authorities" in state["next_action"]
    assert "Stop general semantic feature expansion" in state["next_action"]
    assert {
        "docs/M2_DEFINITION_TRANSITIONS_FOUNDATION.md",
        "docs/M2_DEFINITION_REFERENCE_CANDIDATES.md",
    }.issubset(state["verified_artifacts"])


def test_public_status_documents_share_the_subject_boundary() -> None:
    claims = _text("CLAIMS.md")
    changelog = _text("CHANGELOG.md")
    decisions = _text("DECISIONS.md")
    readme = _text("README.md")

    for document in (claims, changelog, decisions):
        assert HISTORICAL_COMMIT in document
        assert HISTORICAL_MANIFEST in document
        assert "M0_EXTERNAL_AUDIT_PASS" in document
    for document in (claims, changelog, readme):
        assert "EXPERIMENTAL_NOT_ADJUDICATED" in document
        assert "BLOCKED" in document
    assert EVIDENCE_URL in claims
    assert EVIDENCE_URL in changelog
    assert EVIDENCE_URL in decisions
    assert "non-transitive" in claims.lower()
    assert "does **not** transplant" in decisions
    assert "exact-subject audit and final software release remain **BLOCKED**" in readme


def test_delivery_foundation_is_exact_and_not_release_authority() -> None:
    documents = {
        name: _text(name)
        for name in (
            "CHANGELOG.md",
            "CLAIMS.md",
            "DECISIONS.md",
            "RELEASE_CHECKLIST.md",
        )
    }

    for document in documents.values():
        assert CURRENT_BASELINE_COMMIT in document
        assert CURRENT_BASELINE_TREE in document
        assert CURRENT_CI_URL in document
        assert CURRENT_WHEEL_SHA256 in document
        assert CURRENT_SDIST_SHA256 in document
    assert "Internal delivery foundation only" in documents["CLAIMS.md"]
    assert "not a combined audit or release verdict" in documents["CHANGELOG.md"]
    assert "It checks no box below" in documents["RELEASE_CHECKLIST.md"]


def test_release_checklist_is_unchecked_and_covers_every_final_gate() -> None:
    checklist = _text("RELEASE_CHECKLIST.md")

    assert re.search(r"^\s*- \[[xX]\]", checklist, flags=re.MULTILINE) is None
    assert len(re.findall(r"^\s*- \[ \]", checklist, flags=re.MULTILINE)) == 71
    assert len(_powershell_blocks()) == 9

    required_terms = (
        "ubuntu-latest",
        "windows-latest",
        "macos-latest",
        "per-class",
        "minimum support",
        "blind split",
        "detached clean-room external audit",
        "authoritative pre-audit manifest",
        "Source.zip",
        "CycloneDX SBOM",
        "wheel and sdist",
        "annotated tag",
        "Download every release asset",
        "downloaded wheel and sdist",
        "M0 R4/R5",
        "M1 actual-family",
        "M2 lineage",
        "cross-platform distribution byte equality",
        "canonical checking",
    )
    for term in required_terms:
        assert term.casefold() in checklist.casefold(), term


def test_all_nine_release_powershell_blocks_parse() -> None:
    parser = r"""
$Source = [Console]::In.ReadToEnd()
$Tokens = $null
$Errors = $null
[void] [System.Management.Automation.Language.Parser]::ParseInput(
  $Source, [ref] $Tokens, [ref] $Errors)
if ($Errors.Count -ne 0) {
  $Errors | ForEach-Object { [Console]::Error.WriteLine($_.Message) }
  exit 1
}
"""
    blocks = _powershell_blocks()
    assert len(blocks) == 9
    for index, block in enumerate(blocks, start=1):
        result = subprocess.run(
            [_pwsh(), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", parser],
            cwd=ROOT,
            input=block,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"PowerShell block {index}: {result.stderr}"


def test_release_authority_refuses_posix_before_gate_writes_or_child_argv(
    tmp_path: Path,
) -> None:
    authority = _powershell_blocks()[0]
    baseline = "$script:CustodyVolumeAuthority = Get-WindowsReleaseCustodyVolumeAuthority"
    assert authority.index(baseline) < authority.index('$Repository = "taipei49314/NormShift"')
    assert authority.index(baseline) < authority.index("New-Item -ItemType Directory")
    download = _powershell_blocks()[-1]
    download_preflight = "Assert-WindowsReleaseCustodyPathAuthority $DownloadParent"
    assert download.index(download_preflight) < download.index(
        "New-Item -ItemType Directory -Path $DownloadRoot"
    )

    if os.name == "nt":
        return

    gate_root = tmp_path / "empty-gate-root"
    gate_root.mkdir()
    command_log = tmp_path / "unexpected-child-argv.log"
    tool_root = tmp_path / "tools"
    tool_root.mkdir()
    for name in ("uv", "git", "gh", "python"):
        tool = tool_root / name
        tool.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "$@" >> "{command_log.as_posix()}"\nexit 99\n',
            encoding="utf-8",
        )
        tool.chmod(0o700)
    result = _run_release_authority(
        {
            "NORMSHIFT_GATE_ROOT": str(gate_root),
            "PATH": str(tool_root) + os.pathsep + os.environ["PATH"],
        }
    )

    assert result.returncode != 0
    assert "requires Windows NTFS custody authority" in result.stderr
    assert list(gate_root.iterdir()) == []
    assert not command_log.exists(), "POSIX preflight must run before any child argv"


def test_volume_authority_rejects_unc_and_declares_fixed_same_volume_policy() -> None:
    probe = r'''
function Test-IsWindows { return $true }
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
Assert-Rejected {
  Get-WindowsReleaseCustodyVolumeAuthority '\\server\share\gate' "UNC probe"
} "UNC custody root"
Assert-Rejected {
  Get-WindowsReleaseCustodyVolumeAuthority '\\?\C:\gate' "device probe"
} "device custody root"
$Baseline = [pscustomobject]@{
  DriveRoot = 'C:'; VolumeSerial = '11111111'; DriveType = 'fixed'
  Filesystem = 'NTFS'; LocalVolume = $true
}
$Network = [pscustomobject]@{
  DriveRoot = 'Z:'; VolumeSerial = '11111111'; DriveType = 'network'
  Filesystem = 'NTFS'; LocalVolume = $false
}
$SecondFixed = [pscustomobject]@{
  DriveRoot = 'D:'; VolumeSerial = '22222222'; DriveType = 'fixed'
  Filesystem = 'NTFS'; LocalVolume = $true
}
$RootMismatch = [pscustomobject]@{
  DriveRoot = 'D:'; VolumeSerial = '11111111'; DriveType = 'fixed'
  Filesystem = 'NTFS'; LocalVolume = $true
}
Assert-Rejected {
  Assert-WindowsReleaseCustodyPathAuthority 'Z:\gate' $Baseline "network probe" $Network
} "mapped network custody root"
Assert-Rejected {
  Assert-WindowsReleaseCustodyPathAuthority 'D:\gate' $Baseline "second fixed probe" $SecondFixed
} "second fixed custody volume"
Assert-Rejected {
  Assert-WindowsReleaseCustodyPathAuthority 'D:\gate' $Baseline "root mismatch probe" $RootMismatch
} "same serial different drive root"
'''
    result = _run_release_helper_probe(probe)

    assert result.returncode == 0, result.stderr
    authority = _powershell_blocks()[0]
    assert "DriveType -ne [IO.DriveType]::Fixed" in authority
    assert "VolumeSerial -cne $Baseline.VolumeSerial" in authority
    assert "DriveRoot -cne $Baseline.DriveRoot" in authority
    assert "same-volume" in authority


def test_release_contract_externalizes_state_before_first_uv_and_refreshes_remote() -> None:
    authority, publication, download = (
        _powershell_blocks()[0],
        _powershell_blocks()[-2],
        _powershell_blocks()[-1],
    )
    first_uv = authority.index("& $UvExecutableSnapshot.Path")
    for binding in (
        "UV_PROJECT_ENVIRONMENT = $StateDirectorySnapshots",
        "UV_CACHE_DIR = $StateDirectorySnapshots",
        "HYPOTHESIS_STORAGE_DIRECTORY = $StateDirectorySnapshots",
        "MYPY_CACHE_DIR = $StateDirectorySnapshots",
        "RUFF_CACHE_DIR = $StateDirectorySnapshots",
        "PYTHONPYCACHEPREFIX = $StateDirectorySnapshots",
        "UV_PYTHON_INSTALL_DIR = $StateDirectorySnapshots",
        "UV_TOOL_DIR = $StateDirectorySnapshots",
        "UV_TOOL_BIN_DIR = $StateDirectorySnapshots",
        "TMPDIR = $StateDirectorySnapshots",
        "TEMP = $StateDirectorySnapshots",
        "TMP = $StateDirectorySnapshots",
        'UV_PYTHON_DOWNLOADS = "never"',
        "UV_PYTHON = $PythonExecutableSnapshot",
    ):
        assert authority.index(binding) < first_uv
    assert authority.index("$GitExecutableSnapshot.Path diff --check") < first_uv
    assert authority.index("status --porcelain=v1 --untracked-files=all --ignored") < first_uv
    assert "NORMSHIFT_PYTHON_EXECUTABLE is required" in authority
    assert "Invoke-CustodyConsumer \"resolve package version\"" in authority
    assert "preinstalled uv tool directory" in authority
    assert "preinstalled Python interpreter directory" in authority

    for checkpoint in (authority, publication, download):
        assert re.search(
            r"GitExecutableSnapshot\.Path fetch --force\s+`?\s*origin master",
            checkpoint,
        )
        assert "Get-RemoteMasterSha" in checkpoint
    assert "$GitPath ls-remote --heads origin refs/heads/master" in authority
    assert "GitExecutableSnapshot.Path remote get-url origin" in authority
    assert "origin does not identify the configured release repository" in authority
    assert "rev-parse origin/master" not in _text("RELEASE_CHECKLIST.md")
    assert "Assert-ExactReleaseSubject" in download
    assert "$ReleaseRecord.target_commitish" in download


def test_download_release_contract_has_one_fixed_rooted_nine_asset_inventory() -> None:
    checklist = _text("RELEASE_CHECKLIST.md")
    publication, download = _powershell_blocks()[-2:]

    assert "NORMSHIFT_DOWNLOADED_" not in checklist
    assert "$ExpectedReleaseAssetNames.Count -ne 9" in publication
    assert "$ExpectedReleaseAssetNames.Count -ne 9" in download
    assert "$DownloadedEntries.Count -ne 9" in download
    assert "Assert-DisjointRoots $DownloadRoot" in download
    assert "$DownloadRootSnapshot = Get-CustodyDirectorySnapshot" in download
    assert "Resolve-StrictChildPath $DownloadAssetRoot" in download
    assert "--project $DownloadCloneTreeLease.ConsumerRoot" in download
    assert "$DownloadVerifier = Assert-DescendantPath $DownloadRoot" in download
    assert "TMPDIR = $DownloadTempSnapshot" in download
    assert "TEMP = $DownloadTempSnapshot" in download
    assert "TMP = $DownloadTempSnapshot" in download
    assert 'UV_PYTHON_DOWNLOADS = "never"' in download
    assert "UV_PYTHON_INSTALL_DIR" in download
    assert "Get-CustodyFileSnapshot" in download
    assert "Assert-UnchangedFileSnapshot $DownloadVerifierSnapshot" in download
    assert "$Asset.digest.Substring(7)" in download
    assert "$DownloadedManifestDocument.artifacts.$ManifestKey" in download
    assert "$GitExecutableSnapshot.Path clone --no-hardlinks" in download
    assert "NORMSHIFT_SEALED_AUDITED_ROOT" in publication
    assert "NORMSHIFT_MANIFEST_SHA256" in publication
    assert "NORMSHIFT_EXTERNAL_AUDIT_SHA256" in publication
    assert "NORMSHIFT_MANIFEST_SHA256" in download
    assert "NORMSHIFT_EXTERNAL_AUDIT_SHA256" in download
    for forbidden in (
        "NORMSHIFT_WHEEL",
        "NORMSHIFT_SDIST",
        "NORMSHIFT_SOURCE_ZIP",
        "NORMSHIFT_BUNDLE",
        "NORMSHIFT_SBOM",
        "NORMSHIFT_MANIFEST",
        "NORMSHIFT_CHECKSUMS",
        "NORMSHIFT_AUDIT_CONTRACT",
        "NORMSHIFT_EXTERNAL_AUDIT",
        "NORMSHIFT_RELEASE_NOTES",
    ):
        assert re.search(rf"\$env:{forbidden}(?![A-Z0-9_])", publication) is None
    for role in (
        "Wheel",
        "Sdist",
        "SourceZip",
        "Bundle",
        "Sbom",
        "Manifest",
        "Checksums",
        "AuditContract",
        "ExternalAudit",
    ):
        assert f"  {role} = " in publication
        assert f"  {role} = " in download


def test_release_custody_contract_binds_physical_identity_and_consumer_rechecks() -> None:
    checklist = _text("RELEASE_CHECKLIST.md")
    authority, package, publication, download = (
        _powershell_blocks()[0],
        _powershell_blocks()[6],
        _powershell_blocks()[-2],
        _powershell_blocks()[-1],
    )

    for term in (
        "GetFinalPathNameByHandle",
        "VolumeSerialNumber",
        "FileIndexHigh",
        "posix:$($Fields[0]):$($Fields[1])",
        "link count exactly one",
        "forbidden Windows device or extended-length alias",
        "symlink, junction, or other reparse ancestor",
        "Get-CustodyTreeSnapshot",
        "Assert-UnchangedFileSnapshot",
        "Assert-UnchangedDirectorySnapshot",
        "OpenReadLease",
        "FileShare.Read",
        "OpenDirectoryLease",
        "New-CustodyTreeLease",
        "Invoke-CustodyConsumer",
        "controlled copy",
        "Get-WindowsReleaseCustodyVolumeAuthority",
        "Assert-WindowsReleaseCustodyPathAuthority",
        "DriveType -ne [IO.DriveType]::Fixed",
        "VolumeSerial -cne $Baseline.VolumeSerial",
        "must not use a UNC, device, or extended-length path",
        "RootsInventorySha256",
        "ApprovedVolumeBindingSha256",
        "POSIX path consumers are unsupported",
        "$Type -in @('regular file', 'regular empty file')",
    ):
        assert term in authority
    assert "$GitExecutableSnapshot.Path clone --no-hardlinks" in package
    assert "Get-CustodyTreeSnapshot" in publication
    for term in (
        "DownloadRootSnapshot",
        "DownloadTempSnapshot",
        "DownloadTempMarker",
        "DownloadCloneSnapshot",
        "DownloadCloneTreeSnapshot",
        "DownloadVerifierSnapshot",
        "DownloadAuditVerifierSnapshot",
        "DownloadedAuditSnapshot",
        "DownloadedAssetTreeLease",
        "DownloadCloneTreeLease",
        "DownloadConsumerEnvironment",
    ):
        assert term in download

    package_consumer = "-TreeLeases @($AuditCloneTreeLease, $PackageTreeLease)"
    assert package_consumer in package
    assert "-TreeLeases @($PublicationTreeLease)" in publication
    assert "$GhExecutableSnapshot.Path release create" in publication
    assert "$GitExecutableSnapshot.Path clone --no-hardlinks" in publication
    assert '$ReleaseAssetSources["Bundle"]' in publication
    assert "controlled publication input tree" in publication
    assert "chmod 'a-w'" not in authority

    for term in (
        "New-CustodyFileLeaseSet",
        "acceptance input custody root",
        "$PinnedM1Manifest",
        "$PinnedPolicy",
        "$PinnedScorerManifest",
        "$PinnedBlindSplitManifest",
        "$PinnedLabelingPacket",
        "$PinnedDecisionLedger",
        "$PinnedBlindGold",
        "$PinnedBlindPredictions",
        "controlled submissions",
        "controlled blind sources",
        "controlled M1 snapshot",
        "controlled M1 acquisition root",
        "controlled M1 result root",
        "controlled M2 result root",
        "Close-CustodyFileLeaseSet $AcceptanceInputLeaseSet",
    ):
        assert term in checklist
    m1_consumer = _powershell_blocks()[4].split(
        'Invoke-CustodyConsumer "M1 acceptance consumers"', 1
    )[1]
    m2_consumer = _powershell_blocks()[5]
    assert "--snapshot-root $M1AcquisitionRoot" in _powershell_blocks()[4]
    assert "--output-root $M1ResultOutputRoot" in m1_consumer
    assert "--output-root $M2ResultOutputRoot" in m2_consumer
    for mutable_reference in (
        "$env:NORMSHIFT_BLIND_GOLD",
        "$env:NORMSHIFT_BLIND_PREDICTIONS",
        "$env:NORMSHIFT_BLIND_SOURCE_ROOT",
        "$env:NORMSHIFT_SUBMISSIONS_ROOT",
        "$env:NORMSHIFT_LABELING_PACKET",
        "$env:NORMSHIFT_DECISION_LEDGER",
    ):
        assert mutable_reference not in m1_consumer
        assert mutable_reference not in m2_consumer


def test_release_path_helpers_reject_escape_and_overlapping_download_root() -> None:
    probe = r"""
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
$ProbeBase = Join-Path ([IO.Path]::GetTempPath()) `
  ("normshift-root-contract-" + [guid]::NewGuid().ToString("N"))
$Root = Join-Path $ProbeBase "root"
$Outside = Join-Path $ProbeBase "outside"
New-Item -ItemType Directory -Path $Root | Out-Null
New-Item -ItemType Directory -Path $Outside | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Root "download") | Out-Null
$Expected = [IO.Path]::GetFullPath((Join-Path $Root "asset.whl"))
$Observed = Resolve-StrictChildPath $Root "asset.whl" "valid asset"
if ($Observed -cne $Expected) { throw "valid rooted child changed" }
Assert-Rejected { Resolve-StrictChildPath $Root "../escape" "parent escape" } "parent"
Assert-Rejected { Resolve-StrictChildPath $Root "sub/file" "nested escape" } "slash"
Assert-Rejected { Resolve-StrictChildPath $Root "sub\file" "nested escape" } "backslash"
Assert-Rejected { Resolve-StrictChildPath $Root $Outside "absolute escape" } "absolute"
Assert-Rejected { Assert-DescendantPath $Root $Outside "outside path" } "descendant"
Assert-Rejected {
  Assert-DisjointRoots (Join-Path $Root "download") $Root "download/custody"
} "overlapping download root"
"""
    result = _run_release_helper_probe(probe)
    assert result.returncode == 0, result.stderr


def test_physical_custody_rejects_alias_junction_and_hardlink_without_skip(
    tmp_path: Path,
) -> None:
    probe = r"""
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
$Root = Join-Path $env:NORMSHIFT_PROBE_ROOT "physical-root"
$Target = Join-Path $env:NORMSHIFT_PROBE_ROOT "junction-target"
New-Item -ItemType Directory -Path $Root | Out-Null
New-Item -ItemType Directory -Path $Target | Out-Null
$Regular = Join-Path $Root "regular.bin"
[IO.File]::WriteAllBytes($Regular, [byte[]](1, 2, 3, 4))
$Snapshot = Get-CustodyFileSnapshot $Regular "regular physical asset" 16
if ($Snapshot.PhysicalId -notmatch '^(win|posix):') {
  throw "physical asset lacks a platform identity"
}
$Empty = Join-Path $Root "empty.bin"
[IO.File]::WriteAllBytes($Empty, [byte[]]::new(0))
$EmptySnapshot = Get-CustodyFileSnapshot $Empty "empty physical asset" 16 $true
if ($EmptySnapshot.Kind -ne "regular" -or $EmptySnapshot.Size -ne 0 -or
    $EmptySnapshot.AllowEmpty -ne $true) {
  throw "empty regular file does not retain explicit custody permission"
}
if (Test-IsWindows) {
  $Extended = '\\?\' + $Root
  Assert-Rejected {
    Get-CustodyDirectorySnapshot $Extended "extended alias"
  } "Windows extended alias"
  $Junction = Join-Path $Root "junction"
  New-Item -ItemType Junction -Path $Junction -Target $Target | Out-Null
} else {
  $Junction = Join-Path $Root "junction"
  New-Item -ItemType SymbolicLink -Path $Junction -Target $Target | Out-Null
}
$TargetFile = Join-Path $Target "subject.bin"
[IO.File]::WriteAllBytes($TargetFile, [byte[]](5, 6, 7, 8))
Assert-Rejected {
  Get-CustodyFileSnapshot (Join-Path $Junction "subject.bin") "junction ancestor" 16
} "junction ancestor"
$Hardlink = Join-Path $Root "hardlink.bin"
New-Item -ItemType HardLink -Path $Hardlink -Target $Regular | Out-Null
Assert-Rejected {
  Get-CustodyFileSnapshot $Regular "multiply linked asset" 16
} "hardlink asset"
"""
    result = _run_release_helper_probe(
        probe,
        {"NORMSHIFT_PROBE_ROOT": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr


def test_physical_snapshot_rejects_same_length_content_mutation(tmp_path: Path) -> None:
    probe = r"""
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
$Root = Join-Path $env:NORMSHIFT_PROBE_ROOT "mutation-root"
New-Item -ItemType Directory -Path $Root | Out-Null
$Subject = Join-Path $Root "subject.bin"
[IO.File]::WriteAllBytes($Subject, [Text.Encoding]::ASCII.GetBytes("AAAA"))
$Before = Get-CustodyFileSnapshot $Subject "same-length subject" 16
[IO.File]::WriteAllBytes($Subject, [Text.Encoding]::ASCII.GetBytes("BBBB"))
Assert-Rejected {
  Assert-UnchangedFileSnapshot $Before "same-length subject"
} "same-length mutation"
"""
    result = _run_release_helper_probe(
        probe,
        {"NORMSHIFT_PROBE_ROOT": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr


def test_pinned_consumer_copy_blocks_transient_atomic_replacement_without_skip(
    tmp_path: Path,
) -> None:
    probe = r"""
$Root = Join-Path $env:NORMSHIFT_PROBE_ROOT "pinned-consumer"
$SourceRoot = Join-Path $Root "source"
$LeaseRoot = Join-Path $Root "lease"
New-Item -ItemType Directory -Path $SourceRoot -Force | Out-Null
New-Item -ItemType Directory -Path $LeaseRoot | Out-Null
$Source = Join-Path $SourceRoot "subject.bin"
[IO.File]::WriteAllBytes($Source, [Text.Encoding]::ASCII.GetBytes("ORIGINAL"))
$SourceSnapshot = Get-CustodyFileSnapshot $Source "consumer source" 64
$EmptySource = Join-Path $SourceRoot "empty.bin"
[IO.File]::WriteAllBytes($EmptySource, [byte[]]::new(0))
$EmptySnapshot = Get-CustodyFileSnapshot $EmptySource "consumer empty source" 64 $true
$Inputs = [ordered]@{ Subject = $SourceSnapshot; Empty = $EmptySnapshot }
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
if (-not (Test-IsWindows)) {
  Assert-Rejected {
    New-CustodyFileLeaseSet $LeaseRoot $Inputs "unsupported POSIX consumer"
  } "POSIX lease authority"
  if ([IO.File]::ReadAllText($Source) -cne "ORIGINAL" -or
      @(Get-ChildItem -LiteralPath $LeaseRoot -Force).Count -ne 0) {
    throw "POSIX authority refusal changed consumer inputs"
  }
} else {
$script:CustodyVolumeAuthority = Get-WindowsReleaseCustodyVolumeAuthority `
  $Root "Windows consumer probe"
$LeaseSet = New-CustodyFileLeaseSet $LeaseRoot $Inputs "consumer race"
try {
  $Pinned = $LeaseSet.Inputs["Subject"].Path
  if ($LeaseSet.Inputs["Empty"].AllowEmpty -ne $true -or
      [IO.File]::ReadAllBytes($LeaseSet.Inputs["Empty"].Path).Length -ne 0) {
    throw "zero-byte input was not preserved by the Windows custody lease"
  }
  $Replacement = Join-Path $Root "replacement.bin"
  $Backup = Join-Path $Root "pinned-backup.bin"
  [IO.File]::WriteAllBytes(
    $Replacement, [Text.Encoding]::ASCII.GetBytes("MALICIOUS"))
  $Job = Start-Job -ArgumentList $Pinned, $Replacement, $Backup -ScriptBlock {
    param($PinnedPath, $ReplacementPath, $BackupPath)
    $ErrorActionPreference = "Stop"
    try {
      Move-Item -LiteralPath $PinnedPath -Destination $BackupPath -Force -ErrorAction Stop
      Copy-Item -LiteralPath $ReplacementPath -Destination $PinnedPath -Force -ErrorAction Stop
      Remove-Item -LiteralPath $PinnedPath -Force -ErrorAction Stop
      Move-Item -LiteralPath $BackupPath -Destination $PinnedPath -Force -ErrorAction Stop
      "REPLACED"
    } catch {
      "BLOCKED"
    }
  }
  $null = Wait-Job $Job
  $Attack = (Receive-Job $Job | Out-String).Trim()
  Remove-Job $Job
  if ($Attack -cne "BLOCKED") {
    throw "atomic replacement was not denied while the consumer lease was held"
  }
  foreach ($Consumer in @("gh release", "git clone", "package", "audit")) {
    $Observed = [IO.File]::ReadAllText($Pinned)
    if ($Observed -cne "ORIGINAL") {
      throw "$Consumer consumed bytes outside the pinned immutable copy"
    }
    Assert-CustodyFileLeaseSetUnchanged $LeaseSet "$Consumer race"
  }
  Assert-CustodyFileLeaseSetUnchanged $LeaseSet "consumer race before close"
} finally {
  Close-CustodyFileLeaseSet $LeaseSet "consumer race"
  [IO.File]::SetAttributes(
    $LeaseSet.Inputs["Subject"].Path, [IO.FileAttributes]::Normal)
  [IO.File]::SetAttributes(
    $LeaseSet.Inputs["Empty"].Path, [IO.FileAttributes]::Normal)
}
}
"""
    result = _run_release_helper_probe(
        probe,
        {"NORMSHIFT_PROBE_ROOT": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr


def test_consumer_environment_binds_all_windows_temp_aliases_and_restores(
    tmp_path: Path,
) -> None:
    probe = r"""
$Root = Join-Path $env:NORMSHIFT_PROBE_ROOT "consumer-environment"
$Temporary = Join-Path $Root "temporary"
$State = Join-Path $Root "state"
New-Item -ItemType Directory -Path $Temporary -Force | Out-Null
New-Item -ItemType Directory -Path $State | Out-Null
$TemporarySnapshot = Get-CustodyDirectorySnapshot $Temporary "temporary"
$StateSnapshot = Get-CustodyDirectorySnapshot $State "state"
$TemporaryMarker = New-CustodyMarker `
  $Temporary ".temporary.anchor" "temporary marker"
$StateMarker = New-CustodyMarker $State ".state.anchor" "state marker"
$Tool = Join-Path $Root "python.exe"
[IO.File]::WriteAllBytes($Tool, [Text.Encoding]::ASCII.GetBytes("tool"))
$ToolSnapshot = Get-CustodyFileSnapshot $Tool "tool" 16
$Environment = [pscustomobject]@{
  RequiredRoot = $Root
  DirectoryVariables = [ordered]@{
    TMPDIR = $TemporarySnapshot
    TEMP = $TemporarySnapshot
    TMP = $TemporarySnapshot
    UV_PROJECT_ENVIRONMENT = $StateSnapshot
    UV_CACHE_DIR = $StateSnapshot
    HYPOTHESIS_STORAGE_DIRECTORY = $StateSnapshot
    MYPY_CACHE_DIR = $StateSnapshot
    RUFF_CACHE_DIR = $StateSnapshot
    PYTHONPYCACHEPREFIX = $StateSnapshot
    UV_PYTHON_INSTALL_DIR = $StateSnapshot
    UV_TOOL_DIR = $StateSnapshot
    UV_TOOL_BIN_DIR = $StateSnapshot
  }
  FileVariables = [ordered]@{ UV_PYTHON = $ToolSnapshot }
  LiteralVariables = [ordered]@{ UV_PYTHON_DOWNLOADS = "never" }
  Markers = @($TemporaryMarker, $StateMarker)
  ToolTreeSnapshots = @()
}
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
if (-not (Test-IsWindows)) {
  $ActionRan = $false
  Assert-Rejected {
    Invoke-CustodyConsumer "unsupported POSIX consumer" $Environment {
      $script:ActionRan = $true
    }
  } "POSIX consumer authority"
  if ($ActionRan) { throw "POSIX consumer action ran after authority refusal" }
} else {
$script:CustodyVolumeAuthority = Get-WindowsReleaseCustodyVolumeAuthority `
  $Root "Windows environment probe"
$Original = [ordered]@{}
foreach ($Name in @("TMPDIR", "TEMP", "TMP")) {
  $Original[$Name] = [Environment]::GetEnvironmentVariable($Name, "Process")
  [Environment]::SetEnvironmentVariable($Name, "sentinel-$Name", "Process")
}
try {
  Invoke-CustodyConsumer "environment probe" $Environment {
    $Observed = @($env:TMPDIR, $env:TEMP, $env:TMP)
    if (@($Observed | Where-Object { $_ -cne $TemporarySnapshot.Path }).Count -ne 0) {
      throw "TMPDIR/TEMP/TMP are not simultaneously bound"
    }
    $RuntimeTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $ExpectedTemp = $TemporarySnapshot.FinalPath.TrimEnd([char[]]@('/', '\')) + `
      [IO.Path]::DirectorySeparatorChar
    if (-not $RuntimeTemp.StartsWith($ExpectedTemp,
        $(if (Test-IsWindows) {
          [StringComparison]::OrdinalIgnoreCase
        } else {
          [StringComparison]::Ordinal
        }))) {
      throw "runtime temporary path is outside its physical custody root"
    }
  } | Out-Null
  foreach ($Name in @("TMPDIR", "TEMP", "TMP")) {
    if ([Environment]::GetEnvironmentVariable($Name, "Process") -cne
        "sentinel-$Name") {
      throw "$Name was not restored after the consumer"
    }
  }
} finally {
  foreach ($Name in @("TMPDIR", "TEMP", "TMP")) {
    [Environment]::SetEnvironmentVariable($Name, $Original[$Name], "Process")
  }
}
}
"""
    result = _run_release_helper_probe(
        probe,
        {"NORMSHIFT_PROBE_ROOT": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr


def test_controlled_tree_lease_is_readable_by_child_and_denies_race(
    tmp_path: Path,
) -> None:
    probe = r"""
$Root = Join-Path $env:NORMSHIFT_PROBE_ROOT "tree-consumer"
$SourceRoot = Join-Path $Root "source"
$DestinationRoot = Join-Path $Root "controlled"
New-Item -ItemType Directory -Path $SourceRoot -Force | Out-Null
New-Item -ItemType Directory -Path $DestinationRoot | Out-Null
$Source = Join-Path $SourceRoot "subject.txt"
[IO.File]::WriteAllText($Source, "ORIGINAL", [Text.UTF8Encoding]::new($false))
$Empty = Join-Path $SourceRoot "empty.txt"
[IO.File]::WriteAllBytes($Empty, [byte[]]::new(0))
$SourceTree = Get-CustodyTreeSnapshot $SourceRoot "tree source"
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
if (-not (Test-IsWindows)) {
  Assert-Rejected {
    New-CustodyTreeLease $SourceTree $DestinationRoot "unsupported POSIX tree consumer"
  } "POSIX tree lease authority"
  if ([IO.File]::ReadAllText($Source) -cne "ORIGINAL" -or
      @(Get-ChildItem -LiteralPath $DestinationRoot -Force).Count -ne 0) {
    throw "POSIX tree authority refusal changed consumer inputs"
  }
} else {
$script:CustodyVolumeAuthority = Get-WindowsReleaseCustodyVolumeAuthority `
  $Root "Windows tree consumer probe"
$Lease = New-CustodyTreeLease $SourceTree $DestinationRoot "tree consumer"
try {
  $Pinned = Join-Path $Lease.ConsumerRoot "subject.txt"
  $PinnedEmpty = Join-Path $Lease.ConsumerRoot "empty.txt"
  if ([IO.File]::ReadAllBytes($PinnedEmpty).Length -ne 0) {
    throw "zero-byte tree input was not preserved by the Windows custody lease"
  }
  $Replacement = Join-Path $Root "replacement.txt"
  $Backup = Join-Path $Root "backup.txt"
  [IO.File]::WriteAllText(
    $Replacement, "MALICIOUS", [Text.UTF8Encoding]::new($false))
  $Job = Start-Job -ArgumentList $Pinned, $Replacement, $Backup -ScriptBlock {
    param($PinnedPath, $ReplacementPath, $BackupPath)
    $ErrorActionPreference = "Stop"
    try {
      Move-Item -LiteralPath $PinnedPath -Destination $BackupPath -Force -ErrorAction Stop
      Copy-Item -LiteralPath $ReplacementPath -Destination $PinnedPath -Force -ErrorAction Stop
      Remove-Item -LiteralPath $PinnedPath -Force -ErrorAction Stop
      Move-Item -LiteralPath $BackupPath -Destination $PinnedPath -Force -ErrorAction Stop
      "REPLACED"
    } catch {
      "BLOCKED"
    }
  }
  $null = Wait-Job $Job
  $Attack = (Receive-Job $Job | Out-String).Trim()
  Remove-Job $Job
  if ($Attack -cne "BLOCKED") {
    throw "controlled tree allowed an atomic replacement race"
  }
  Assert-CustodyTreeLeaseUnchanged $Lease "tree consumer after denied race"
  $Harness = Join-Path $Root "read-pinned-input.ps1"
  [IO.File]::WriteAllText($Harness, @'
param([Parameter(Mandatory = $true)][string] $InputPath)
[IO.File]::ReadAllText($InputPath)
'@, [Text.UTF8Encoding]::new($false))
  $PowerShellPath = (Get-Process -Id $PID).Path
  foreach ($Consumer in @("gh release", "git clone", "package", "audit")) {
    $Observed = (& $PowerShellPath -NoLogo -NoProfile -NonInteractive `
      -File $Harness -InputPath $Pinned).Trim()
    Assert-NativeSuccess "$Consumer child argv read"
    if ($Observed -cne "ORIGINAL") {
      throw "$Consumer child did not consume the pinned controlled tree argv"
    }
    Assert-CustodyTreeLeaseUnchanged $Lease "$Consumer child argv"
  }
  Assert-CustodyTreeLeaseUnchanged $Lease "tree consumer before close"
} finally {
  Close-CustodyTreeLease $Lease "tree consumer"
  [IO.File]::SetAttributes($Pinned, [IO.FileAttributes]::Normal)
  [IO.File]::SetAttributes($PinnedEmpty, [IO.FileAttributes]::Normal)
}
}
"""
    result = _run_release_helper_probe(
        probe,
        {"NORMSHIFT_PROBE_ROOT": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr


def test_clone_verifier_tmpdir_and_state_identity_races_fail_closed(tmp_path: Path) -> None:
    probe = r"""
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
$Root = Join-Path $env:NORMSHIFT_PROBE_ROOT "race-root"
$Clone = Join-Path $Root "clone"
$State = Join-Path $Root "state"
$Temporary = Join-Path $Root "temporary"
New-Item -ItemType Directory -Path $Clone -Force | Out-Null
New-Item -ItemType Directory -Path $State | Out-Null
New-Item -ItemType Directory -Path $Temporary | Out-Null
$CloneBefore = Get-CustodyDirectorySnapshot $Clone "clone"
$StateBefore = Get-CustodyDirectorySnapshot $State "state"
$TemporaryBefore = Get-CustodyDirectorySnapshot $Temporary "TMPDIR"
$StateMarker = New-CustodyMarker $State ".state.anchor" "state marker"
$TemporaryMarker = New-CustodyMarker $Temporary ".temporary.anchor" "TMPDIR marker"
$Verifier = Join-Path $Clone "verifier.py"
[IO.File]::WriteAllBytes($Verifier, [Text.Encoding]::ASCII.GetBytes("print('ok')`n"))
$EmptyFile = Join-Path $Clone "empty.txt"
[IO.File]::WriteAllBytes($EmptyFile, [byte[]]::new(0))
$EmptyDirectory = Join-Path $Clone "empty-directory"
New-Item -ItemType Directory -Path $EmptyDirectory | Out-Null
$CloneTreeBefore = Get-CustodyTreeSnapshot $Clone "clone tree"
if ($CloneTreeBefore.FileSnapshots["empty.txt"].AllowEmpty -ne $true) {
  throw "controlled tree snapshots must retain zero-byte AllowEmpty custody"
}
$VerifierBefore = Get-CustodyFileSnapshot $Verifier "verifier" 1024

$Replacement = Join-Path $Clone "old-verifier.py"
Move-Item -LiteralPath $Verifier -Destination $Replacement
[IO.File]::WriteAllBytes($Verifier, [Text.Encoding]::ASCII.GetBytes("print('ok')`n"))
Assert-Rejected {
  Assert-UnchangedFileSnapshot $VerifierBefore "verifier"
} "verifier replacement race"

$TemporaryBytes = [byte[]]::new([int] $TemporaryMarker.Size)
for ($Index = 0; $Index -lt $TemporaryBytes.Length; $Index++) {
  $TemporaryBytes[$Index] = 88
}
[IO.File]::WriteAllBytes($TemporaryMarker.Path, $TemporaryBytes)
Assert-Rejected {
  Assert-UnchangedFileSnapshot $TemporaryMarker "TMPDIR marker"
} "TMPDIR marker race"

Move-Item -LiteralPath $EmptyDirectory -Destination `
  (Join-Path $Root "old-empty-directory")
New-Item -ItemType Directory -Path $EmptyDirectory | Out-Null
Assert-Rejected {
  Assert-UnchangedTreeSnapshot $CloneTreeBefore "clone tree"
} "empty clone directory identity race"

Move-Item -LiteralPath $Clone -Destination (Join-Path $Root "old-clone")
New-Item -ItemType Directory -Path $Clone | Out-Null
Assert-Rejected {
  Assert-UnchangedDirectorySnapshot $CloneBefore "clone"
} "clone identity race"

Move-Item -LiteralPath $State -Destination (Join-Path $Root "old-state")
New-Item -ItemType Directory -Path $State | Out-Null
Assert-Rejected {
  Assert-UnchangedDirectorySnapshot $StateBefore "state"
} "state identity race"
Assert-UnchangedDirectorySnapshot $TemporaryBefore "TMPDIR"
"""
    result = _run_release_helper_probe(
        probe,
        {"NORMSHIFT_PROBE_ROOT": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr


def test_release_subject_helpers_reject_stale_origin_and_remote_advance() -> None:
    probe = r"""
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
$A = [string]::new('a', 40)
$B = [string]::new('b', 40)
Assert-ExactDefaultSubject $A $A $A "valid default"
Assert-Rejected { Assert-ExactDefaultSubject $A $A $B "stale origin" } "stale origin"
Assert-Rejected { Assert-ExactDefaultSubject $A $B $B "remote advance" } "remote advance"
Assert-ExactReleaseSubject $A $A $A $A $A
Assert-Rejected {
  Assert-ExactReleaseSubject $A $B $A $A $A
} "release SHA mismatch"
Assert-Rejected {
  Assert-ExactReleaseSubject $A $A $B $A $A
} "tag SHA mismatch"
Assert-Rejected {
  Assert-ExactReleaseSubject $A $A $A $A $B
} "final default SHA mismatch"
"""
    result = _run_release_helper_probe(probe)
    assert result.returncode == 0, result.stderr


def test_release_name_set_helper_rejects_extra_missing_case_and_duplicates() -> None:
    probe = r"""
function Assert-Rejected([scriptblock] $Action, [string] $Label) {
  $Rejected = $false
  try { & $Action | Out-Null } catch { $Rejected = $true }
  if (-not $Rejected) { throw "$Label was accepted" }
}
$Expected = @("bundle", "manifest", "wheel")
Assert-ExactNameSet -Expected $Expected `
  -Observed @("bundle", "manifest", "wheel") -Label "valid inventory"
Assert-Rejected {
  Assert-ExactNameSet -Expected $Expected `
    -Observed @("bundle", "manifest", "wheel", "extra") -Label "extra"
} "extra asset"
Assert-Rejected {
  Assert-ExactNameSet -Expected $Expected `
    -Observed @("bundle", "manifest") -Label "missing"
} "missing asset"
Assert-Rejected {
  Assert-ExactNameSet -Expected $Expected `
    -Observed @("Bundle", "manifest", "wheel") -Label "case"
} "case alias"
Assert-Rejected {
  Assert-ExactNameSet -Expected $Expected `
    -Observed @("bundle", "bundle", "wheel") -Label "duplicate"
} "duplicate asset"
"""
    result = _run_release_helper_probe(probe)
    assert result.returncode == 0, result.stderr


def test_security_contact_uses_only_the_configured_repository_route() -> None:
    security = _text("SECURITY.md")

    assert "https://github.com/taipei49314/NormShift/issues/new" in security
    assert "private vulnerability reporting is not configured" in security
    assert "Security contact request" in security
    assert "mailto:" not in security.casefold()
    assert re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", security) is None
