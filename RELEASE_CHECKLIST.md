# Final M0-M2 Release Checklist

This is the fail-closed operational gate for the bounded NormShift M0-M2 release.
It implements the exact-SHA package, clean-room audit, CI, documentation, release,
and completion rules in Sections 8-11 of `NORMSHIFT_TO_100.md`.

Every box is intentionally unchecked in the current repository state. Check a box
only when its durable evidence names the same final release subject. `SKIP`,
`NOT_RUN`, `BLOCKED`, `INCONCLUSIVE`, a missing record, a non-zero exit, an
unexplained non-pass test, or a hash/identity mismatch is a failure and leaves the
release `BLOCKED`. Never backfill PASS from prose or from the historical M0-only
`b3af3dc...` audit.

The verified ancestor delivery foundation from master commit
`f6897f71834a50d2273fda033a72b31254c65935`, tree
`34cde504fab42da8f9423cd1ca226fe492307c36`, and push CI
[run 31462052663](https://github.com/taipei49314/NormShift/actions/runs/31462052663)
proved canonical, byte-identical wheels and sdists across three operating systems.
The final wheel SHA-256 was
`b5ebc295dadb63ab2969185551ca62409e9290d9f9fba41916d188e6a833886d`; the
sdist SHA-256 was
`fb8f1f0add5a752cfa3a070edf0ed984835961b4f93a5c672c0f02ea6b2c4760`.
It checks no box below: the later final subject must rerun every gate and obtain its
own combined detached audit and release evidence.

## 0. Authority and candidate variables

- [ ] The implementer, blind evaluation owner, independent reviewer, and release
      authority are identified, and every role separation required by the frozen
      policy is satisfied.
- [ ] The blind evaluation owner confirms that no implementer had access to final
      holdout membership, gold labels, predictions, or scores before candidate
      freeze.
- [ ] One external empty gate root has been selected outside the checkout; its final
      physical identity is canonical and disjoint, every ancestor is non-reparse,
      and all uv, Python, Ruff, mypy, Hypothesis, pytest, build, and audit state is
      kept there behind identity/size/SHA-256 custody anchors.
- [ ] The candidate SHA, tree, version, run ID, CI run ID, and every evidence root
      are recorded in a release evidence log. No placeholder remains.

Use PowerShell 7+ from a clean clone of the default branch. Set only task-specific
variables; do not repurpose system home variables.

Every file-reading native consumer below receives a newly controlled byte-for-byte
copy, never the mutable source pathname. Release execution authority is deliberately
limited to Windows NTFS: read handles to the source, copy, every copied tree file,
and its directories remain open for the full child process with write/delete sharing
denied. POSIX is fail-closed for lease creation and consumer execution. An open
POSIX descriptor and non-writable pathname do not prevent the same account from
renaming, replacing, or changing the mode of a path-based child input, so they must
never be represented as equivalent release custody. On the supported authority,
identity, link count, size, SHA-256, and complete content inventory are re-read from
the still-open leases before and after the child. A transient replace/use/restore
race therefore cannot become PASS.
For each child, `TMPDIR`, `TEMP`, and `TMP` are simultaneously rebound to the same
physically verified descendant, then restored; managed Python downloads are disabled
and the exact uv/Python/Git/GitHub CLI files and tool directories stay snapshotted.

```powershell
$ErrorActionPreference = "Stop"

function Assert-NativeSuccess([string] $Label) {
  if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit $LASTEXITCODE" }
}

function Assert-ExactDefaultSubject(
    [string] $CandidateSha,
    [string] $FetchedDefaultSha,
    [string] $RemoteDefaultSha,
    [string] $Label) {
  foreach ($Sha in @($CandidateSha, $FetchedDefaultSha, $RemoteDefaultSha)) {
    if ($Sha -notmatch '^[0-9a-f]{40}$') { throw "$Label contains a non-SHA value" }
  }
  if ($CandidateSha -ne $FetchedDefaultSha -or
      $CandidateSha -ne $RemoteDefaultSha) {
    throw "$Label is stale or differs from remote refs/heads/master"
  }
}

function Assert-ExactReleaseSubject(
    [string] $CandidateSha,
    [string] $ReleaseSha,
    [string] $TagSha,
    [string] $FetchedDefaultSha,
    [string] $RemoteDefaultSha) {
  Assert-ExactDefaultSubject $CandidateSha $FetchedDefaultSha `
    $RemoteDefaultSha "final default branch"
  foreach ($Sha in @($ReleaseSha, $TagSha)) {
    if ($Sha -notmatch '^[0-9a-f]{40}$' -or $Sha -ne $CandidateSha) {
      throw "release, annotated tag, and default branch must name one exact SHA"
    }
  }
}

function Get-RemoteMasterSha {
  $GitPath = (Get-Command git -CommandType Application -ErrorAction Stop).Source
  if ($null -ne $GitExecutableSnapshot) {
    $GitPath = $GitExecutableSnapshot.Path
  }
  $Rows = @(& $GitPath ls-remote --heads origin refs/heads/master)
  Assert-NativeSuccess "query remote refs/heads/master"
  if ($Rows.Count -ne 1) { throw "remote refs/heads/master must resolve exactly once" }
  $Match = [regex]::Match(
    $Rows[0], '^([0-9a-f]{40})\trefs/heads/master$')
  if (-not $Match.Success) { throw "remote master response is not canonical" }
  return $Match.Groups[1].Value
}

function Test-IsWindows {
  return [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
}

function Get-WindowsReleaseCustodyVolumeAuthority(
    [string] $Path,
    [string] $Label) {
  if (-not (Test-IsWindows)) {
    throw "$Label requires Windows NTFS custody authority; POSIX path consumers are unsupported"
  }
  $RawPath = $Path.Replace('/', '\')
  if ($RawPath.StartsWith('\\') -or $RawPath.StartsWith('\\?\') -or
      $RawPath.StartsWith('\\.\')) {
    throw "$Label must not use a UNC, device, or extended-length path"
  }
  try {
    $Full = [IO.Path]::GetFullPath($Path)
    $VolumeRoot = [IO.Path]::GetPathRoot($Full)
    if (-not $VolumeRoot) { throw "missing volume root" }
    $Drive = [IO.DriveInfo]::new($VolumeRoot)
  } catch {
    throw "$Label must be on a local Windows NTFS volume"
  }
  if (-not $Drive.IsReady -or $Drive.DriveType -ne [IO.DriveType]::Fixed -or
      $Drive.DriveFormat -cne 'NTFS') {
    throw "$Label must be on a ready fixed local Windows NTFS volume"
  }
  $Probe = $Full
  while (-not (Test-Path -LiteralPath $Probe)) {
    $Probe = [IO.Path]::GetDirectoryName($Probe)
    if (-not $Probe) { throw "$Label has no existing local volume ancestor" }
  }
  Initialize-NormShiftCustodyInterop
  $Native = [NormShift.CustodyNative]::DescribePath($Probe)
  $Match = [regex]::Match([string] $Native.PhysicalId, '^win:([0-9a-f]{8}):')
  if (-not $Match.Success) { throw "$Label has no stable Windows volume identity" }
  return [pscustomobject]@{
    DriveRoot = $Drive.RootDirectory.FullName
    VolumeSerial = $Match.Groups[1].Value
    DriveType = 'fixed'
    Filesystem = 'NTFS'
    LocalVolume = $true
  }
}

function Assert-WindowsReleaseCustodyPathAuthority(
    [string] $Path,
    [object] $Baseline,
    [string] $Label,
    [object] $Observed = $null) {
  if ($null -eq $Observed) {
    $Observed = Get-WindowsReleaseCustodyVolumeAuthority $Path $Label
  }
  if ($null -eq $Baseline -or $Observed.DriveType -cne 'fixed' -or
      $Observed.Filesystem -cne 'NTFS' -or -not $Observed.LocalVolume -or
      $Observed.VolumeSerial -cne $Baseline.VolumeSerial -or
      $Observed.DriveRoot -cne $Baseline.DriveRoot) {
    throw "$Label is not on the approved fixed local Windows NTFS custody volume"
  }
  if ($null -ne $script:CustodyAuthorityRecords) {
    $null = $script:CustodyAuthorityRecords.Add(
      "$Label|$($Observed.DriveType)|$($Observed.Filesystem)|$($Observed.LocalVolume)|same-volume")
  }
}

function Get-CustodyAuthorityEvidenceSha256([object] $Baseline) {
  if ($null -eq $script:CustodyAuthorityRecords) {
    throw 'custody authority records are unavailable'
  }
  $Records = @($script:CustodyAuthorityRecords | Sort-Object -Unique)
  $Inventory = [Text.UTF8Encoding]::new($false).GetBytes(($Records -join "`n") + "`n")
  $Binding = [Text.UTF8Encoding]::new($false).GetBytes(
    "windows|NTFS|fixed|local|$($Baseline.VolumeSerial)|normshift-windows-ntfs-share-deny|1.0.0`n")
  $Hash = [Security.Cryptography.SHA256]::Create()
  try {
    return [pscustomobject]@{
      RootsInventorySha256 = ([Convert]::ToHexString($Hash.ComputeHash($Inventory))).ToLowerInvariant()
      ApprovedVolumeBindingSha256 = ([Convert]::ToHexString($Hash.ComputeHash($Binding))).ToLowerInvariant()
    }
  } finally { $Hash.Dispose() }
}

function Initialize-NormShiftCustodyInterop {
  if ("NormShift.CustodyNative" -as [type]) { return }
  Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace NormShift {
  public sealed class CustodyHandleInfo {
    public string PhysicalId { get; set; }
    public string FinalPath { get; set; }
    public long Size { get; set; }
    public uint LinkCount { get; set; }
    public uint Attributes { get; set; }
    public uint FileType { get; set; }
    public string Sha256 { get; set; }
  }

  public sealed class CustodyFileLease : IDisposable {
    internal FileStream Stream { get; private set; }
    public string Path { get; private set; }
    private readonly long maximumBytes;
    private readonly bool allowEmpty;

    internal CustodyFileLease(
        string path, FileStream stream, long maximumBytes, bool allowEmpty) {
      Path = path;
      Stream = stream;
      this.maximumBytes = maximumBytes;
      this.allowEmpty = allowEmpty;
    }

    public CustodyHandleInfo Snapshot() {
      if (Stream == null) { throw new ObjectDisposedException("CustodyFileLease"); }
      return CustodyNative.DescribeAndHash(Stream, maximumBytes, allowEmpty);
    }

    public CustodyFileLease CopyToNew(string destination) {
      if (Stream == null) { throw new ObjectDisposedException("CustodyFileLease"); }
      CustodyHandleInfo sourceBefore = Snapshot();
      Stream.Position = 0;
      FileStream output = new FileStream(
        destination, FileMode.CreateNew, FileAccess.Write, FileShare.None,
        1048576, FileOptions.SequentialScan);
      try {
        Stream.CopyTo(output, 1048576);
        output.Flush(true);
        output.Dispose();
        output = null;
        CustodyFileLease destinationLease = CustodyNative.OpenReadLease(
          destination, maximumBytes, allowEmpty);
        CustodyHandleInfo copied = destinationLease.Snapshot();
        CustodyHandleInfo sourceAfter = Snapshot();
        if (sourceBefore.PhysicalId != sourceAfter.PhysicalId ||
            sourceBefore.FinalPath != sourceAfter.FinalPath ||
            sourceBefore.Size != sourceAfter.Size ||
            sourceBefore.Sha256 != sourceAfter.Sha256 ||
            copied.Size != sourceBefore.Size || copied.Sha256 != sourceBefore.Sha256) {
          destinationLease.Dispose();
          throw new IOException("custody source changed or sealed copy differs");
        }
        return destinationLease;
      } catch {
        if (output != null) { output.Dispose(); }
        throw;
      }
    }

    public void Dispose() {
      if (Stream != null) {
        Stream.Dispose();
        Stream = null;
      }
    }
  }

  public sealed class CustodyDirectoryLease : IDisposable {
    private SafeFileHandle handle;
    public CustodyHandleInfo Initial { get; private set; }

    internal CustodyDirectoryLease(SafeFileHandle handle, CustodyHandleInfo initial) {
      this.handle = handle;
      Initial = initial;
    }

    public CustodyHandleInfo Snapshot() {
      if (handle == null || handle.IsClosed) {
        throw new ObjectDisposedException("CustodyDirectoryLease");
      }
      return CustodyNative.DescribeHandle(handle);
    }

    public void Dispose() {
      if (handle != null) {
        handle.Dispose();
        handle = null;
      }
    }
  }

  public static class CustodyNative {
    [StructLayout(LayoutKind.Sequential)]
    private struct FileTime {
      public uint Low;
      public uint High;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ByHandleFileInformation {
      public uint Attributes;
      public FileTime CreationTime;
      public FileTime LastAccessTime;
      public FileTime LastWriteTime;
      public uint VolumeSerialNumber;
      public uint FileSizeHigh;
      public uint FileSizeLow;
      public uint NumberOfLinks;
      public uint FileIndexHigh;
      public uint FileIndexLow;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFile(
      string fileName, uint desiredAccess, uint shareMode, IntPtr securityAttributes,
      uint creationDisposition, uint flagsAndAttributes, IntPtr templateFile);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetFileInformationByHandle(
      SafeFileHandle handle, out ByHandleFileInformation information);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint GetFinalPathNameByHandle(
      SafeFileHandle handle, StringBuilder path, uint pathLength, uint flags);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint GetFileType(SafeFileHandle handle);

    private const uint GenericRead = 0x80000000;
    private const uint FileReadAttributes = 0x80;
    private const uint ShareRead = 0x1;
    private const uint ShareWrite = 0x2;
    private const uint ShareDelete = 0x4;
    private const uint OpenExisting = 3;
    private const uint BackupSemantics = 0x02000000;
    private const uint SequentialScan = 0x08000000;

    private static SafeFileHandle OpenHandle(string path, uint access, uint share, uint flags) {
      SafeFileHandle handle = CreateFile(
        path, access, share, IntPtr.Zero, OpenExisting, flags, IntPtr.Zero);
      if (handle.IsInvalid) {
        int error = Marshal.GetLastWin32Error();
        handle.Dispose();
        throw new Win32Exception(error, "cannot open custody path by handle");
      }
      return handle;
    }

    internal static CustodyHandleInfo DescribeHandle(SafeFileHandle handle) {
      ByHandleFileInformation information;
      if (!GetFileInformationByHandle(handle, out information)) {
        throw new Win32Exception(Marshal.GetLastWin32Error(), "cannot read custody identity");
      }
      StringBuilder finalPath = new StringBuilder(32768);
      uint length = GetFinalPathNameByHandle(handle, finalPath, (uint)finalPath.Capacity, 0);
      if (length == 0 || length >= finalPath.Capacity) {
        throw new Win32Exception(Marshal.GetLastWin32Error(), "cannot resolve final custody path");
      }
      ulong fileIndex = ((ulong)information.FileIndexHigh << 32) | information.FileIndexLow;
      ulong fileSize = ((ulong)information.FileSizeHigh << 32) | information.FileSizeLow;
      if (fileSize > Int64.MaxValue) {
        throw new IOException("custody file size exceeds Int64");
      }
      return new CustodyHandleInfo {
        PhysicalId = String.Format("win:{0:x8}:{1:x16}", information.VolumeSerialNumber, fileIndex),
        FinalPath = finalPath.ToString(),
        Size = (long)fileSize,
        LinkCount = information.NumberOfLinks,
        Attributes = information.Attributes,
        FileType = GetFileType(handle),
        Sha256 = null
      };
    }

    internal static CustodyHandleInfo DescribeAndHash(
        FileStream stream, long maximumBytes, bool allowEmpty) {
      CustodyHandleInfo before = DescribeHandle(stream.SafeFileHandle);
      if (before.FileType != 1 || (before.Attributes & 0x10) != 0 ||
          (before.Attributes & 0x400) != 0) {
        throw new IOException("custody asset is not a regular non-reparse disk file");
      }
      if (before.LinkCount != 1) {
        throw new IOException("custody asset link count is not exactly one");
      }
      if (before.Size < 0 || (!allowEmpty && before.Size == 0) ||
          before.Size > maximumBytes) {
        throw new IOException("custody asset is empty or exceeds its byte bound");
      }
      long originalPosition = stream.Position;
      byte[] digest;
      stream.Position = 0;
      using (SHA256 sha256 = SHA256.Create()) {
        digest = sha256.ComputeHash(stream);
      }
      stream.Position = Math.Min(originalPosition, stream.Length);
      CustodyHandleInfo after = DescribeHandle(stream.SafeFileHandle);
      if (before.PhysicalId != after.PhysicalId || before.Size != after.Size ||
          before.LinkCount != after.LinkCount || before.FinalPath != after.FinalPath) {
        throw new IOException("custody asset identity changed while hashing");
      }
      StringBuilder text = new StringBuilder(digest.Length * 2);
      foreach (byte value in digest) { text.Append(value.ToString("x2")); }
      before.Sha256 = text.ToString();
      return before;
    }

    public static CustodyFileLease OpenReadLease(
        string path, long maximumBytes, bool allowEmpty) {
      FileStream stream = new FileStream(
        path, FileMode.Open, FileAccess.Read, FileShare.Read,
        1048576, FileOptions.SequentialScan);
      try {
        CustodyFileLease lease = new CustodyFileLease(
          path, stream, maximumBytes, allowEmpty);
        lease.Snapshot();
        return lease;
      } catch {
        stream.Dispose();
        throw;
      }
    }

    public static CustodyDirectoryLease OpenDirectoryLease(string path) {
      SafeFileHandle handle = OpenHandle(
        path, FileReadAttributes, ShareRead, BackupSemantics);
      try {
        CustodyHandleInfo information = DescribeHandle(handle);
        if ((information.Attributes & 0x10) == 0 ||
            (information.Attributes & 0x400) != 0) {
          throw new IOException("custody directory lease is not a non-reparse directory");
        }
        return new CustodyDirectoryLease(handle, information);
      } catch {
        handle.Dispose();
        throw;
      }
    }

    public static CustodyHandleInfo DescribePath(string path) {
      using (SafeFileHandle handle = OpenHandle(
        path, FileReadAttributes, ShareRead | ShareWrite | ShareDelete, BackupSemantics)) {
        return DescribeHandle(handle);
      }
    }

    public static CustodyHandleInfo SnapshotFile(
        string path, long maximumBytes, bool allowEmpty) {
      using (CustodyFileLease lease = OpenReadLease(path, maximumBytes, allowEmpty)) {
        return lease.Snapshot();
      }
    }
  }
}
'@
}

function ConvertFrom-WindowsHandlePath([string] $Path) {
  if ($Path.StartsWith('\\?\UNC\', [StringComparison]::OrdinalIgnoreCase)) {
    return '\\' + $Path.Substring(8)
  }
  if ($Path.StartsWith('\\?\', [StringComparison]::OrdinalIgnoreCase)) {
    return $Path.Substring(4)
  }
  return $Path
}

function Assert-NoReparsePathComponents(
    [string] $Path,
    [string] $Label) {
  $Full = [IO.Path]::GetFullPath($Path)
  $Root = [IO.Path]::GetPathRoot($Full)
  if (-not $Root) { throw "$Label has no filesystem root" }
  $Current = $Root
  $Remainder = $Full.Substring($Root.Length)
  $Parts = @($Remainder.Split(
    [char[]]@([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar),
    [StringSplitOptions]::RemoveEmptyEntries))
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    $Item = Get-Item -LiteralPath $Current -Force
    if (Test-IsWindows) {
      $LinkType = $Item.PSObject.Properties['LinkType']
      if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
          ($null -ne $LinkType -and
            -not [string]::IsNullOrEmpty([string] $LinkType.Value))) {
        throw "$Label contains a symlink, junction, or other reparse ancestor"
      }
    }
  }
}

function Get-CustodyPathIdentity(
    [string] $Path,
    [string] $Label) {
  $RawPath = $Path.Replace('/', '\')
  if ((Test-IsWindows) -and
      ($RawPath.StartsWith('\\?\') -or $RawPath.StartsWith('\\.\'))) {
    throw "$Label uses a forbidden Windows device or extended-length alias"
  }
  $Full = [IO.Path]::GetFullPath($Path)
  if ($null -ne $script:CustodyVolumeAuthority) {
    Assert-WindowsReleaseCustodyPathAuthority `
      $Full $script:CustodyVolumeAuthority $Label
  }
  Assert-NoReparsePathComponents $Full $Label
  if (Test-IsWindows) {
    Initialize-NormShiftCustodyInterop
    $Native = [NormShift.CustodyNative]::DescribePath($Full)
    $Final = [IO.Path]::GetFullPath((ConvertFrom-WindowsHandlePath $Native.FinalPath))
    if (-not $Full.Equals($Final, [StringComparison]::OrdinalIgnoreCase)) {
      throw "$Label uses an alias-equivalent or non-final Windows path"
    }
    $Kind = if (($Native.Attributes -band 0x10) -ne 0) {
      "directory"
    } elseif ($Native.FileType -eq 1) {
      "regular"
    } else {
      "other"
    }
    return [pscustomobject]@{
      Path = $Full
      FinalPath = $Final
      PhysicalId = $Native.PhysicalId
      LinkCount = [uint64] $Native.LinkCount
      Size = [int64] $Native.Size
      Kind = $Kind
    }
  }
  $Resolved = (Resolve-Path -LiteralPath $Full).ProviderPath
  if ($Resolved -cne $Full) { throw "$Label is not its POSIX final path" }
  $StatLine = (& stat '--printf=%d|%i|%h|%s|%F' -- $Full 2>$null)
  if ($LASTEXITCODE -ne 0) {
    $StatLine = (& stat -f '%d|%i|%l|%z|%HT' $Full 2>$null)
  }
  if ($LASTEXITCODE -ne 0) { throw "$Label POSIX stat failed" }
  $Fields = @($StatLine -split '\|', 5)
  if ($Fields.Count -ne 5 -or $Fields[0] -notmatch '^\d+$' -or
      $Fields[1] -notmatch '^\d+$' -or $Fields[2] -notmatch '^\d+$' -or
      $Fields[3] -notmatch '^\d+$') {
    throw "$Label POSIX stat result is malformed"
  }
  $Type = $Fields[4].Trim().ToLowerInvariant()
  $Kind = if ($Type -eq 'directory') {
    "directory"
  } elseif ($Type -in @('regular file', 'regular empty file')) {
    "regular"
  } else {
    "other"
  }
  return [pscustomobject]@{
    Path = $Full
    FinalPath = $Resolved
    PhysicalId = "posix:$($Fields[0]):$($Fields[1])"
    LinkCount = [uint64] $Fields[2]
    Size = [int64] $Fields[3]
    Kind = $Kind
  }
}

function Get-CustodyDirectorySnapshot(
    [string] $Path,
    [string] $Label) {
  $Identity = Get-CustodyPathIdentity $Path $Label
  if ($Identity.Kind -ne "directory") { throw "$Label is not a physical directory" }
  return [pscustomobject]@{
    Label = $Label
    Path = $Identity.Path
    FinalPath = $Identity.FinalPath
    PhysicalId = $Identity.PhysicalId
  }
}

function Assert-UnchangedDirectorySnapshot(
    [object] $Before,
    [string] $Label) {
  $After = Get-CustodyDirectorySnapshot $Before.Path $Label
  if ($After.PhysicalId -cne $Before.PhysicalId -or
      $After.FinalPath -cne $Before.FinalPath) {
    throw "$Label physical directory identity changed"
  }
}

function Get-CustodyFileSnapshot(
    [string] $Path,
    [string] $Label,
    [int64] $MaximumBytes = 4294967296,
    [bool] $AllowEmpty = $false) {
  $Before = Get-CustodyPathIdentity $Path $Label
  if ($Before.Kind -ne "regular" -or $Before.LinkCount -ne 1 -or
      $Before.Size -lt 0 -or (-not $AllowEmpty -and $Before.Size -eq 0) -or
      $Before.Size -gt $MaximumBytes) {
    throw "$Label must be one bounded regular file with permitted size and link count exactly one"
  }
  $Parent = Get-CustodyPathIdentity ([IO.Path]::GetDirectoryName($Before.Path)) `
    "$Label parent"
  if ($Parent.Kind -ne "directory") { throw "$Label parent is not a directory" }
  if (Test-IsWindows) {
    Initialize-NormShiftCustodyInterop
    $Locked = [NormShift.CustodyNative]::SnapshotFile(
      $Before.Path, $MaximumBytes, $AllowEmpty)
    $LockedFinal = [IO.Path]::GetFullPath(
      (ConvertFrom-WindowsHandlePath $Locked.FinalPath))
    if ($Locked.PhysicalId -cne $Before.PhysicalId -or
        $LockedFinal -cne $Before.FinalPath -or $Locked.Size -ne $Before.Size) {
      throw "$Label path and hashing handle identify different files"
    }
    $Digest = $Locked.Sha256
  } else {
    $Stream = [IO.File]::Open(
      $Before.Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
      $Sha = [Security.Cryptography.SHA256]::Create()
      try { $Digest = [BitConverter]::ToString($Sha.ComputeHash($Stream)).Replace('-', '').ToLowerInvariant() }
      finally { $Sha.Dispose() }
    } finally {
      $Stream.Dispose()
    }
  }
  $After = Get-CustodyPathIdentity $Before.Path $Label
  if ($After.PhysicalId -cne $Before.PhysicalId -or
      $After.FinalPath -cne $Before.FinalPath -or
      $After.Size -ne $Before.Size -or $After.LinkCount -ne 1) {
    throw "$Label identity changed while it was snapshotted"
  }
  return [pscustomobject]@{
    Label = $Label
    Path = $Before.Path
    FinalPath = $Before.FinalPath
    PhysicalId = $Before.PhysicalId
    ParentPhysicalId = $Parent.PhysicalId
    Kind = $Before.Kind
    Size = $Before.Size
    Sha256 = $Digest
    MaximumBytes = $MaximumBytes
    AllowEmpty = $AllowEmpty
  }
}

function Assert-UnchangedFileSnapshot(
    [object] $Before,
    [string] $Label) {
  $After = Get-CustodyFileSnapshot `
    $Before.Path $Label $Before.MaximumBytes $Before.AllowEmpty
  foreach ($Field in @(
      'FinalPath', 'PhysicalId', 'ParentPhysicalId', 'Size', 'Sha256')) {
    if ($After.$Field -cne $Before.$Field) {
      throw "$Label identity, size, or SHA-256 changed"
    }
  }
}

function Get-CustodyTreeSnapshot(
    [string] $Root,
    [string] $Label,
    [int] $MaximumFiles = 100000,
    [int] $MaximumDirectories = 100000,
    [int64] $MaximumTotalBytes = 8589934592) {
  $RootSnapshot = Get-CustodyDirectorySnapshot $Root $Label
  $CollisionSet = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase)
  $Records = [Collections.Generic.List[string]]::new()
  $ContentRecords = [Collections.Generic.List[string]]::new()
  $FileSnapshots = [ordered]@{}
  $DirectorySnapshots = [ordered]@{}
  $Queue = [Collections.Generic.Queue[object]]::new()
  $Queue.Enqueue($RootSnapshot)
  $FileCount = 0
  $DirectoryCount = 0
  $TotalBytes = [int64] 0
  while ($Queue.Count -ne 0) {
    $Directory = $Queue.Dequeue()
    foreach ($Entry in @(Get-ChildItem -LiteralPath $Directory.Path -Force)) {
      $Relative = $Entry.FullName.Substring($RootSnapshot.Path.Length).TrimStart(
        [char[]]@('/', '\')).Replace('\', '/')
      if (-not $Relative -or $Relative.Length -gt 1024 -or
          $Relative -match '[\x00-\x1f|]' -or
          -not $CollisionSet.Add($Relative)) {
        throw "$Label contains an empty, unsafe, overlong, or alias-colliding path"
      }
      if ($Entry.PSIsContainer) {
        $DirectoryCount += 1
        if ($DirectoryCount -gt $MaximumDirectories) {
          throw "$Label exceeds its directory-count bound"
        }
        $ChildDirectory = Get-CustodyDirectorySnapshot `
          $Entry.FullName "$Label directory $Relative"
        $Records.Add("D|$Relative|$($ChildDirectory.PhysicalId)")
        $ContentRecords.Add("D|$Relative")
        $DirectorySnapshots[$Relative] = $ChildDirectory
        $Queue.Enqueue($ChildDirectory)
        continue
      }
      $FileCount += 1
      if ($FileCount -gt $MaximumFiles) {
        throw "$Label exceeds its file-count bound"
      }
      $Snapshot = Get-CustodyFileSnapshot `
        $Entry.FullName "$Label file $Relative" 4294967296 $true
      $TotalBytes += $Snapshot.Size
      if ($TotalBytes -gt $MaximumTotalBytes) {
        throw "$Label exceeds its total-byte bound"
      }
      $Records.Add(
        "F|$Relative|$($Snapshot.PhysicalId)|$($Snapshot.Size)|$($Snapshot.Sha256)")
      $ContentRecords.Add("F|$Relative|$($Snapshot.Size)|$($Snapshot.Sha256)")
      $FileSnapshots[$Relative] = $Snapshot
    }
  }
  $RecordArray = $Records.ToArray()
  [Array]::Sort($RecordArray, [StringComparer]::Ordinal)
  $Inventory = [string]::Join("`n", $RecordArray) + "`n"
  $InventoryBytes = [Text.UTF8Encoding]::new($false).GetBytes($Inventory)
  if ($InventoryBytes.Length -gt 33554432) {
    throw "$Label inventory exceeds its metadata bound"
  }
  $Sha = [Security.Cryptography.SHA256]::Create()
  try {
    $Digest = [BitConverter]::ToString(
      $Sha.ComputeHash($InventoryBytes)).Replace('-', '').ToLowerInvariant()
  } finally {
    $Sha.Dispose()
  }
  $ContentRecordArray = $ContentRecords.ToArray()
  [Array]::Sort($ContentRecordArray, [StringComparer]::Ordinal)
  $ContentInventory = [string]::Join("`n", $ContentRecordArray) + "`n"
  $ContentInventoryBytes = [Text.UTF8Encoding]::new($false).GetBytes($ContentInventory)
  if ($ContentInventoryBytes.Length -gt 33554432) {
    throw "$Label content inventory exceeds its metadata bound"
  }
  $ContentSha = [Security.Cryptography.SHA256]::Create()
  try {
    $ContentDigest = [BitConverter]::ToString(
      $ContentSha.ComputeHash($ContentInventoryBytes)).Replace('-', '').ToLowerInvariant()
  } finally {
    $ContentSha.Dispose()
  }
  return [pscustomobject]@{
    Label = $Label
    Root = $RootSnapshot
    FileCount = $FileCount
    DirectoryCount = $DirectoryCount
    TotalBytes = $TotalBytes
    InventorySha256 = $Digest
    ContentInventorySha256 = $ContentDigest
    FileSnapshots = $FileSnapshots
    DirectorySnapshots = $DirectorySnapshots
    MaximumFiles = $MaximumFiles
    MaximumDirectories = $MaximumDirectories
    MaximumTotalBytes = $MaximumTotalBytes
  }
}

function Assert-UnchangedTreeSnapshot(
    [object] $Before,
    [string] $Label) {
  $After = Get-CustodyTreeSnapshot $Before.Root.Path $Label `
    $Before.MaximumFiles $Before.MaximumDirectories $Before.MaximumTotalBytes
  if ($After.Root.PhysicalId -cne $Before.Root.PhysicalId -or
      $After.Root.FinalPath -cne $Before.Root.FinalPath -or
      $After.FileCount -ne $Before.FileCount -or
      $After.DirectoryCount -ne $Before.DirectoryCount -or
      $After.TotalBytes -ne $Before.TotalBytes -or
      $After.InventorySha256 -cne $Before.InventorySha256 -or
      $After.ContentInventorySha256 -cne $Before.ContentInventorySha256) {
    throw "$Label physical tree identity, size, or SHA-256 inventory changed"
  }
}

function Get-OpenStreamSha256([IO.Stream] $Stream) {
  if (-not $Stream.CanRead -or -not $Stream.CanSeek) {
    throw "custody stream must be readable and seekable"
  }
  $Position = $Stream.Position
  try {
    $Stream.Position = 0
    $Sha = [Security.Cryptography.SHA256]::Create()
    try {
      return [BitConverter]::ToString(
        $Sha.ComputeHash($Stream)).Replace('-', '').ToLowerInvariant()
    } finally {
      $Sha.Dispose()
    }
  } finally {
    $Stream.Position = [Math]::Min($Position, $Stream.Length)
  }
}

function Assert-NativeLeaseMatchesSnapshot(
    [object] $LeaseInformation,
    [object] $Expected,
    [string] $Label) {
  $LeaseFinal = [IO.Path]::GetFullPath(
    (ConvertFrom-WindowsHandlePath $LeaseInformation.FinalPath))
  if ($LeaseInformation.PhysicalId -cne $Expected.PhysicalId -or
      $LeaseFinal -cne $Expected.FinalPath -or
      [int64] $LeaseInformation.Size -ne $Expected.Size -or
      [uint64] $LeaseInformation.LinkCount -ne 1 -or
      $LeaseInformation.Sha256 -cne $Expected.Sha256) {
    throw "$Label open lease differs from its frozen physical identity/size/SHA-256"
  }
}

function New-CustodyFileLeaseSet(
    [string] $Root,
    [Collections.IDictionary] $InputSnapshots,
    [string] $Label) {
  Assert-WindowsReleaseCustodyPathAuthority `
    $Root $script:CustodyVolumeAuthority "$Label file lease root"
  $RootSnapshot = Get-CustodyDirectorySnapshot $Root "$Label root"
  if (@(Get-ChildItem -LiteralPath $RootSnapshot.Path -Force).Count -ne 0) {
    throw "$Label root must be an empty pre-created physical directory"
  }
  if ($InputSnapshots.Count -lt 1 -or $InputSnapshots.Count -gt 128) {
    throw "$Label input count is outside its bound"
  }
  $ConsumerInputs = [ordered]@{}
  $Entries = [Collections.Generic.List[object]]::new()
  $LeafNames = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase)
  $DirectoryLease = $null
  try {
    foreach ($Role in @($InputSnapshots.Keys)) {
      $Expected = $InputSnapshots[$Role]
      Assert-WindowsReleaseCustodyPathAuthority $Expected.Path `
        $script:CustodyVolumeAuthority "$Label source $Role"
      Assert-UnchangedFileSnapshot $Expected "$Label source $Role before sealing"
      $Leaf = [IO.Path]::GetFileName([string] $Expected.Path)
      if (-not $LeafNames.Add($Leaf)) {
        throw "$Label input leaf names collide"
      }
      $Destination = Resolve-StrictChildPath `
        $RootSnapshot.Path $Leaf "$Label sealed $Role"
      if (Test-IsWindows) {
        Initialize-NormShiftCustodyInterop
        $SourceLease = [NormShift.CustodyNative]::OpenReadLease(
          $Expected.Path, $Expected.MaximumBytes, $Expected.AllowEmpty)
        try {
          Assert-NativeLeaseMatchesSnapshot `
            ($SourceLease.Snapshot()) $Expected "$Label source $Role"
          $DestinationLease = $SourceLease.CopyToNew($Destination)
        } catch {
          $SourceLease.Dispose()
          throw
        }
        $DestinationSnapshot = Get-CustodyFileSnapshot `
          $Destination "$Label sealed $Role" `
          $Expected.MaximumBytes $Expected.AllowEmpty
        Assert-NativeLeaseMatchesSnapshot `
          ($DestinationLease.Snapshot()) $DestinationSnapshot `
          "$Label sealed $Role"
        if ($DestinationSnapshot.Size -ne $Expected.Size -or
            $DestinationSnapshot.Sha256 -cne $Expected.Sha256) {
          $DestinationLease.Dispose()
          $SourceLease.Dispose()
          throw "$Label sealed $Role differs from its frozen source bytes"
        }
        $Entry = [pscustomobject]@{
          Role = $Role
          SourceExpected = $Expected
          SourceLease = $SourceLease
          DestinationExpected = $DestinationSnapshot
          DestinationLease = $DestinationLease
          SourceStream = $null
          DestinationStream = $null
        }
      } else {
        throw "$Label requires Windows NTFS custody authority"
      }
      $Entries.Add($Entry)
      $ConsumerInputs[$Role] = $Entry.DestinationExpected
    }

    if (Test-IsWindows) {
      foreach ($Entry in $Entries) {
        $Attributes = [IO.File]::GetAttributes($Entry.DestinationExpected.Path)
        [IO.File]::SetAttributes(
          $Entry.DestinationExpected.Path,
          $Attributes -bor [IO.FileAttributes]::ReadOnly)
      }
      $DirectoryLease = [NormShift.CustodyNative]::OpenDirectoryLease(
        $RootSnapshot.Path)
      if ($DirectoryLease.Initial.PhysicalId -cne $RootSnapshot.PhysicalId) {
        throw "$Label directory lease differs from its frozen physical root"
      }
    } else { throw "$Label requires Windows NTFS custody authority" }
    $TreeSnapshot = Get-CustodyTreeSnapshot $RootSnapshot.Path "$Label sealed tree"
    if ($TreeSnapshot.FileCount -ne $InputSnapshots.Count -or
        $TreeSnapshot.DirectoryCount -ne 0) {
      throw "$Label sealed root has undeclared entries"
    }
    return [pscustomobject]@{
      Label = $Label
      RootSnapshot = $RootSnapshot
      TreeSnapshot = $TreeSnapshot
      Inputs = $ConsumerInputs
      Entries = $Entries
      DirectoryLease = $DirectoryLease
      Closed = $false
    }
  } catch {
    if ($null -ne $DirectoryLease) { $DirectoryLease.Dispose() }
    foreach ($Entry in $Entries) {
      if ($null -ne $Entry.DestinationLease) { $Entry.DestinationLease.Dispose() }
      if ($null -ne $Entry.SourceLease) { $Entry.SourceLease.Dispose() }
      if ($null -ne $Entry.DestinationStream) { $Entry.DestinationStream.Dispose() }
      if ($null -ne $Entry.SourceStream) { $Entry.SourceStream.Dispose() }
    }
    throw
  }
}

function Assert-CustodyFileLeaseSetUnchanged(
    [object] $LeaseSet,
    [string] $Label) {
  if ($LeaseSet.Closed) { throw "$Label lease set is already closed" }
  Assert-UnchangedDirectorySnapshot $LeaseSet.RootSnapshot "$Label root"
  if (Test-IsWindows) {
    $DirectoryAfter = $LeaseSet.DirectoryLease.Snapshot()
    if ($DirectoryAfter.PhysicalId -cne $LeaseSet.RootSnapshot.PhysicalId) {
      throw "$Label directory lease identity changed"
    }
  }
  foreach ($Entry in $LeaseSet.Entries) {
    if (Test-IsWindows) {
      Assert-NativeLeaseMatchesSnapshot `
        ($Entry.SourceLease.Snapshot()) $Entry.SourceExpected `
        "$Label source $($Entry.Role)"
      Assert-NativeLeaseMatchesSnapshot `
        ($Entry.DestinationLease.Snapshot()) $Entry.DestinationExpected `
        "$Label sealed $($Entry.Role)"
    } else { throw "$Label requires Windows NTFS custody authority" }
    Assert-UnchangedFileSnapshot $Entry.SourceExpected `
      "$Label source $($Entry.Role) path"
    Assert-UnchangedFileSnapshot $Entry.DestinationExpected `
      "$Label sealed $($Entry.Role) path"
  }
  Assert-UnchangedTreeSnapshot $LeaseSet.TreeSnapshot "$Label sealed tree"
}

function Close-CustodyFileLeaseSet(
    [object] $LeaseSet,
    [string] $Label) {
  try {
    Assert-CustodyFileLeaseSetUnchanged $LeaseSet $Label
  } finally {
    if ($null -ne $LeaseSet.DirectoryLease) { $LeaseSet.DirectoryLease.Dispose() }
    foreach ($Entry in $LeaseSet.Entries) {
      if ($null -ne $Entry.DestinationLease) { $Entry.DestinationLease.Dispose() }
      if ($null -ne $Entry.SourceLease) { $Entry.SourceLease.Dispose() }
      if ($null -ne $Entry.DestinationStream) { $Entry.DestinationStream.Dispose() }
      if ($null -ne $Entry.SourceStream) { $Entry.SourceStream.Dispose() }
    }
    $LeaseSet.Closed = $true
  }
}

function New-CustodyTreeLease(
    [object] $SourceTreeSnapshot,
    [string] $DestinationRoot,
    [string] $Label) {
  Assert-WindowsReleaseCustodyPathAuthority $SourceTreeSnapshot.Root.Path `
    $script:CustodyVolumeAuthority "$Label source tree"
  Assert-WindowsReleaseCustodyPathAuthority $DestinationRoot `
    $script:CustodyVolumeAuthority "$Label destination tree"
  $DestinationRootSnapshot = Get-CustodyDirectorySnapshot `
    $DestinationRoot "$Label destination root"
  if (@(Get-ChildItem -LiteralPath $DestinationRoot -Force).Count -ne 0) {
    throw "$Label destination root must be empty"
  }
  Assert-UnchangedTreeSnapshot $SourceTreeSnapshot "$Label source before copy"
  foreach ($Entry in @(Get-ChildItem -LiteralPath $SourceTreeSnapshot.Root.Path -Force)) {
    Copy-Item -LiteralPath $Entry.FullName -Destination $DestinationRoot `
      -Recurse -Force
  }
  $CopiedTree = Get-CustodyTreeSnapshot $DestinationRoot "$Label copied tree"
  if ($CopiedTree.FileCount -ne $SourceTreeSnapshot.FileCount -or
      $CopiedTree.DirectoryCount -ne $SourceTreeSnapshot.DirectoryCount -or
      $CopiedTree.TotalBytes -ne $SourceTreeSnapshot.TotalBytes -or
      $CopiedTree.ContentInventorySha256 -cne
        $SourceTreeSnapshot.ContentInventorySha256) {
    throw "$Label controlled copy differs from its frozen source content"
  }
  $FileLeases = [Collections.Generic.List[object]]::new()
  $DirectoryLeases = [Collections.Generic.List[object]]::new()
  try {
    if (Test-IsWindows) {
      Initialize-NormShiftCustodyInterop
      foreach ($Relative in @($CopiedTree.FileSnapshots.Keys)) {
        $Expected = $CopiedTree.FileSnapshots[$Relative]
        $Lease = [NormShift.CustodyNative]::OpenReadLease(
          $Expected.Path, $Expected.MaximumBytes, $Expected.AllowEmpty)
        Assert-NativeLeaseMatchesSnapshot `
          ($Lease.Snapshot()) $Expected "$Label file $Relative"
        $FileLeases.Add([pscustomobject]@{
          Relative = $Relative
          Expected = $Expected
          NativeLease = $Lease
          Stream = $null
        })
      }
      foreach ($DirectorySnapshot in @(
          $CopiedTree.DirectorySnapshots.Values) + @($CopiedTree.Root)) {
        $Lease = [NormShift.CustodyNative]::OpenDirectoryLease(
          $DirectorySnapshot.Path)
        if ($Lease.Initial.PhysicalId -cne $DirectorySnapshot.PhysicalId) {
          $Lease.Dispose()
          throw "$Label directory lease differs from copied tree"
        }
        $DirectoryLeases.Add([pscustomobject]@{
          Expected = $DirectorySnapshot
          NativeLease = $Lease
        })
      }
    } else { throw "$Label requires Windows NTFS custody authority" }
    $SealedTree = Get-CustodyTreeSnapshot $DestinationRoot "$Label sealed tree"
    if ($SealedTree.ContentInventorySha256 -cne $CopiedTree.ContentInventorySha256 -or
        $SealedTree.InventorySha256 -cne $CopiedTree.InventorySha256) {
      throw "$Label copied tree changed while its leases were established"
    }
    Assert-UnchangedTreeSnapshot $SourceTreeSnapshot "$Label source after copy"
    return [pscustomobject]@{
      Label = $Label
      SourceTreeSnapshot = $SourceTreeSnapshot
      TreeSnapshot = $SealedTree
      ConsumerRoot = $SealedTree.Root.Path
      FileLeases = $FileLeases
      DirectoryLeases = $DirectoryLeases
      Closed = $false
    }
  } catch {
    foreach ($Entry in $DirectoryLeases) { $Entry.NativeLease.Dispose() }
    foreach ($Entry in $FileLeases) {
      if ($null -ne $Entry.NativeLease) { $Entry.NativeLease.Dispose() }
      if ($null -ne $Entry.Stream) { $Entry.Stream.Dispose() }
    }
    throw
  }
}

function Assert-CustodyTreeLeaseUnchanged(
    [object] $Lease,
    [string] $Label) {
  if ($Lease.Closed) { throw "$Label tree lease is already closed" }
  foreach ($Entry in $Lease.FileLeases) {
    if (Test-IsWindows) {
      Assert-NativeLeaseMatchesSnapshot `
        ($Entry.NativeLease.Snapshot()) $Entry.Expected `
        "$Label file $($Entry.Relative)"
    } else { throw "$Label requires Windows NTFS custody authority" }
  }
  foreach ($Entry in $Lease.DirectoryLeases) {
    $After = $Entry.NativeLease.Snapshot()
    if ($After.PhysicalId -cne $Entry.Expected.PhysicalId) {
      throw "$Label pinned Windows directory identity changed"
    }
  }
  Assert-UnchangedTreeSnapshot $Lease.TreeSnapshot "$Label sealed tree"
  Assert-UnchangedTreeSnapshot $Lease.SourceTreeSnapshot "$Label source tree"
}

function Close-CustodyTreeLease(
    [object] $Lease,
    [string] $Label) {
  try {
    Assert-CustodyTreeLeaseUnchanged $Lease $Label
  } finally {
    foreach ($Entry in $Lease.DirectoryLeases) { $Entry.NativeLease.Dispose() }
    foreach ($Entry in $Lease.FileLeases) {
      if ($null -ne $Entry.NativeLease) { $Entry.NativeLease.Dispose() }
      if ($null -ne $Entry.Stream) { $Entry.Stream.Dispose() }
    }
    $Lease.Closed = $true
  }
}

function Assert-CustodyConsumerEnvironment(
    [object] $Environment,
    [string] $Label) {
  foreach ($Name in @($Environment.DirectoryVariables.Keys)) {
    $Snapshot = $Environment.DirectoryVariables[$Name]
    $Observed = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if ($Observed -cne $Snapshot.Path) {
      throw "$Label environment variable $Name is not bound to its custody directory"
    }
    $null = Assert-DescendantPath `
      $Environment.RequiredRoot $Observed "$Label $Name"
    Assert-UnchangedDirectorySnapshot $Snapshot "$Label $Name"
  }
  foreach ($Name in @($Environment.FileVariables.Keys)) {
    $Snapshot = $Environment.FileVariables[$Name]
    $Observed = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if ($Observed -cne $Snapshot.Path) {
      throw "$Label environment variable $Name is not bound to its custody file"
    }
    Assert-UnchangedFileSnapshot $Snapshot "$Label $Name"
  }
  foreach ($Name in @($Environment.LiteralVariables.Keys)) {
    if ([Environment]::GetEnvironmentVariable($Name, 'Process') -cne
        [string] $Environment.LiteralVariables[$Name]) {
      throw "$Label literal environment variable $Name differs"
    }
  }
  foreach ($Marker in @($Environment.Markers)) {
    Assert-UnchangedFileSnapshot $Marker "$Label custody marker"
  }
  foreach ($Tree in @($Environment.ToolTreeSnapshots)) {
    Assert-UnchangedTreeSnapshot $Tree "$Label interpreter/tool tree"
  }
}

function Invoke-CustodyConsumer(
    [string] $Label,
    [object] $Environment,
    [scriptblock] $Action,
    [object[]] $FileLeaseSets = @(),
    [object[]] $TreeLeases = @()) {
  Assert-WindowsReleaseCustodyPathAuthority $Environment.RequiredRoot `
    $script:CustodyVolumeAuthority "$Label consumer"
  $Names = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
  foreach ($Name in @($Environment.DirectoryVariables.Keys) +
      @($Environment.FileVariables.Keys) + @($Environment.LiteralVariables.Keys)) {
    $null = $Names.Add([string] $Name)
  }
  $Saved = [ordered]@{}
  foreach ($Name in $Names) {
    $Saved[$Name] = [Environment]::GetEnvironmentVariable($Name, 'Process')
  }
  try {
    foreach ($Name in $Environment.DirectoryVariables.Keys) {
      [Environment]::SetEnvironmentVariable(
        $Name, $Environment.DirectoryVariables[$Name].Path, 'Process')
    }
    foreach ($Name in $Environment.FileVariables.Keys) {
      [Environment]::SetEnvironmentVariable(
        $Name, $Environment.FileVariables[$Name].Path, 'Process')
    }
    foreach ($Name in $Environment.LiteralVariables.Keys) {
      [Environment]::SetEnvironmentVariable(
        $Name, [string] $Environment.LiteralVariables[$Name], 'Process')
    }
    Assert-CustodyConsumerEnvironment $Environment "$Label before"
    foreach ($LeaseSet in $FileLeaseSets) {
      Assert-CustodyFileLeaseSetUnchanged $LeaseSet "$Label input"
    }
    foreach ($Lease in $TreeLeases) {
      Assert-CustodyTreeLeaseUnchanged $Lease "$Label input tree"
    }
    $Result = & $Action
    Assert-CustodyConsumerEnvironment $Environment "$Label after"
    foreach ($LeaseSet in $FileLeaseSets) {
      Assert-CustodyFileLeaseSetUnchanged $LeaseSet "$Label input"
    }
    foreach ($Lease in $TreeLeases) {
      Assert-CustodyTreeLeaseUnchanged $Lease "$Label input tree"
    }
    return $Result
  } finally {
    foreach ($Name in $Names) {
      [Environment]::SetEnvironmentVariable($Name, $Saved[$Name], 'Process')
    }
  }
}

function New-CustodyMarker(
    [string] $Directory,
    [string] $Name,
    [string] $Label,
    [string] $Content = "NormShift custody marker`n") {
  $Path = Resolve-StrictChildPath $Directory $Name $Label
  $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Content)
  $Stream = [IO.File]::Open(
    $Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
  try {
    $Stream.Write($Bytes, 0, $Bytes.Length)
    $Stream.Flush($true)
  } finally {
    $Stream.Dispose()
  }
  return Get-CustodyFileSnapshot $Path $Label 1024
}

function Assert-DisjointRoots(
    [string] $Left,
    [string] $Right,
    [string] $Label) {
  $LeftIdentity = Get-CustodyDirectorySnapshot $Left "$Label left root"
  $RightIdentity = Get-CustodyDirectorySnapshot $Right "$Label right root"
  $Comparison = if (Test-IsWindows) {
    [StringComparison]::OrdinalIgnoreCase
  } else {
    [StringComparison]::Ordinal
  }
  $Separator = [IO.Path]::DirectorySeparatorChar
  if ($LeftIdentity.PhysicalId -ceq $RightIdentity.PhysicalId -or
      $LeftIdentity.FinalPath.Equals($RightIdentity.FinalPath, $Comparison) -or
      $LeftIdentity.FinalPath.StartsWith($RightIdentity.FinalPath + $Separator, $Comparison) -or
      $RightIdentity.FinalPath.StartsWith($LeftIdentity.FinalPath + $Separator, $Comparison)) {
    throw "$Label roots overlap or alias the same physical object"
  }
}

function Assert-DescendantPath(
    [string] $Root,
    [string] $Path,
    [string] $Label) {
  $RootIdentity = Get-CustodyDirectorySnapshot $Root "$Label root"
  $PathFull = [IO.Path]::GetFullPath($Path)
  if ($null -ne $script:CustodyVolumeAuthority) {
    Assert-WindowsReleaseCustodyPathAuthority `
      $PathFull $script:CustodyVolumeAuthority $Label
  }
  $Comparison = if (Test-IsWindows) {
    [StringComparison]::OrdinalIgnoreCase
  } else {
    [StringComparison]::Ordinal
  }
  $Prefix = $RootIdentity.FinalPath.TrimEnd([char[]]@('/', '\')) + `
    [IO.Path]::DirectorySeparatorChar
  if (-not $PathFull.StartsWith($Prefix, $Comparison)) {
    throw "$Label escapes its required physical root"
  }
  if (Test-Path -LiteralPath $PathFull) {
    $PathIdentity = Get-CustodyPathIdentity $PathFull $Label
    if (-not $PathIdentity.FinalPath.StartsWith($Prefix, $Comparison)) {
      throw "$Label resolves outside its required physical root"
    }
  } else {
    $Parent = [IO.Path]::GetDirectoryName($PathFull)
    if (-not $Parent -or -not (Test-Path -LiteralPath $Parent -PathType Container)) {
      throw "$Label parent must already exist under its physical root"
    }
    $ParentIdentity = Get-CustodyDirectorySnapshot $Parent "$Label parent"
    if ($ParentIdentity.PhysicalId -cne $RootIdentity.PhysicalId -and
        -not $ParentIdentity.FinalPath.StartsWith($Prefix, $Comparison)) {
      throw "$Label parent resolves outside its required physical root"
    }
  }
  return $PathFull
}

function Resolve-StrictChildPath(
    [string] $Root,
    [string] $Name,
    [string] $Label) {
  if (-not $Name -or [IO.Path]::IsPathRooted($Name) -or
      $Name.IndexOfAny([char[]]@('/', '\')) -ge 0 -or
      $Name -in @('.', '..') -or [IO.Path]::GetFileName($Name) -cne $Name) {
    throw "$Label is not one fixed leaf name"
  }
  $Child = Assert-DescendantPath $Root (Join-Path $Root $Name) $Label
  if ($null -ne $script:CustodyVolumeAuthority) {
    Assert-WindowsReleaseCustodyPathAuthority `
      $Child $script:CustodyVolumeAuthority $Label
  }
  return $Child
}

function Assert-ExactNameSet(
    [string[]] $Expected,
    [string[]] $Observed,
    [string] $Label) {
  if ($Expected.Count -ne $Observed.Count) {
    throw "$Label count differs: expected $($Expected.Count), got $($Observed.Count)"
  }
  $ExpectedSet = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
  $ObservedSet = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
  foreach ($Name in $Expected) {
    if (-not $ExpectedSet.Add($Name)) { throw "$Label expected names are duplicated" }
  }
  foreach ($Name in $Observed) {
    if (-not $ObservedSet.Add($Name)) { throw "$Label observed names are duplicated" }
  }
  if (-not $ExpectedSet.SetEquals($ObservedSet)) {
    throw "$Label names differ"
  }
}

$script:CustodyAuthorityRecords = [Collections.Generic.List[string]]::new()
$script:CustodyVolumeAuthority = Get-WindowsReleaseCustodyVolumeAuthority `
  (Get-Location).Path "release execution checkout"
Assert-WindowsReleaseCustodyPathAuthority (Get-Location).Path `
  $script:CustodyVolumeAuthority "release execution checkout"
$Repository = "taipei49314/NormShift"
$CheckoutSnapshot = Get-CustodyDirectorySnapshot (Get-Location).Path "checkout"
$Checkout = $CheckoutSnapshot.FinalPath
$AllowedOriginUrls = @(
  "https://github.com/$Repository",
  "https://github.com/$Repository.git",
  "git@github.com:$Repository.git"
)
if (-not $env:NORMSHIFT_GATE_ROOT) { throw "NORMSHIFT_GATE_ROOT is required" }
$GateRootSnapshot = Get-CustodyDirectorySnapshot `
  $env:NORMSHIFT_GATE_ROOT "gate root"
$GateRoot = $GateRootSnapshot.FinalPath
Assert-WindowsReleaseCustodyPathAuthority $GateRoot `
  $script:CustodyVolumeAuthority "gate root"
Assert-DisjointRoots $GateRoot $Checkout "gate/checkout"
if (@(Get-ChildItem -LiteralPath $GateRoot -Force).Count -ne 0) {
  throw "gate root must be empty"
}

$StatePaths = [ordered]@{
  ProjectEnvironment = Resolve-StrictChildPath `
    $GateRoot "project-env" "uv project environment"
  UvCache = Resolve-StrictChildPath $GateRoot "uv-cache" "uv cache"
  Hypothesis = Resolve-StrictChildPath $GateRoot "hypothesis" "Hypothesis state"
  Mypy = Resolve-StrictChildPath $GateRoot "mypy-cache" "mypy state"
  Ruff = Resolve-StrictChildPath $GateRoot "ruff-cache" "Ruff state"
  Python = Resolve-StrictChildPath $GateRoot "python-pycache" "Python bytecode state"
  PythonInstall = Resolve-StrictChildPath `
    $GateRoot "uv-python-install" "uv Python install state"
  UvTools = Resolve-StrictChildPath $GateRoot "uv-tools" "uv tool state"
  UvToolBin = Resolve-StrictChildPath $GateRoot "uv-tool-bin" "uv tool bin state"
  Temporary = Resolve-StrictChildPath $GateRoot "temporary" "temporary state"
}
$StateDirectorySnapshots = [ordered]@{}
$StateMarkerSnapshots = [ordered]@{}
foreach ($StateName in $StatePaths.Keys) {
  New-Item -ItemType Directory -Path $StatePaths[$StateName] | Out-Null
  $DirectorySnapshot = Get-CustodyDirectorySnapshot `
    $StatePaths[$StateName] "$StateName state directory"
  $StateDirectorySnapshots[$StateName] = $DirectorySnapshot
  $StateMarkerSnapshots[$StateName] = New-CustodyMarker `
    $GateRoot ".normshift-$($StateName.ToLowerInvariant()).anchor" `
    "$StateName state binding" `
    "$($DirectorySnapshot.FinalPath)|$($DirectorySnapshot.PhysicalId)`n"
}
$GateRootMarker = New-CustodyMarker `
  $GateRoot ".normshift-gate.anchor" "gate root binding" `
  "$($GateRootSnapshot.FinalPath)|$($GateRootSnapshot.PhysicalId)`n"

$UvCommand = Get-Command uv -CommandType Application -ErrorAction Stop
$UvExecutableSnapshot = Get-CustodyFileSnapshot `
  $UvCommand.Source "preinstalled uv executable" 1073741824
$GitCommand = Get-Command git -CommandType Application -ErrorAction Stop
$GitExecutableSnapshot = Get-CustodyFileSnapshot `
  $GitCommand.Source "preinstalled Git executable" 1073741824
$GhCommand = Get-Command gh -CommandType Application -ErrorAction Stop
$GhExecutableSnapshot = Get-CustodyFileSnapshot `
  $GhCommand.Source "preinstalled GitHub CLI executable" 1073741824
if (-not $env:NORMSHIFT_PYTHON_EXECUTABLE) {
  throw "NORMSHIFT_PYTHON_EXECUTABLE is required; managed Python downloads are forbidden"
}
$PythonExecutableSnapshot = Get-CustodyFileSnapshot `
  $env:NORMSHIFT_PYTHON_EXECUTABLE "preinstalled Python executable" 1073741824
$UvToolDirectoryTreeSnapshot = Get-CustodyTreeSnapshot `
  ([IO.Path]::GetDirectoryName($UvExecutableSnapshot.Path)) `
  "preinstalled uv tool directory"
$PythonToolDirectoryTreeSnapshot = Get-CustodyTreeSnapshot `
  ([IO.Path]::GetDirectoryName($PythonExecutableSnapshot.Path)) `
  "preinstalled Python interpreter directory"
$GitToolDirectoryTreeSnapshot = Get-CustodyTreeSnapshot `
  ([IO.Path]::GetDirectoryName($GitExecutableSnapshot.Path)) `
  "preinstalled Git tool directory"
$GhToolDirectoryTreeSnapshot = Get-CustodyTreeSnapshot `
  ([IO.Path]::GetDirectoryName($GhExecutableSnapshot.Path)) `
  "preinstalled GitHub CLI tool directory"

$GateDirectoryEnvironment = [ordered]@{
  UV_PROJECT_ENVIRONMENT = $StateDirectorySnapshots["ProjectEnvironment"]
  UV_CACHE_DIR = $StateDirectorySnapshots["UvCache"]
  HYPOTHESIS_STORAGE_DIRECTORY = $StateDirectorySnapshots["Hypothesis"]
  MYPY_CACHE_DIR = $StateDirectorySnapshots["Mypy"]
  RUFF_CACHE_DIR = $StateDirectorySnapshots["Ruff"]
  PYTHONPYCACHEPREFIX = $StateDirectorySnapshots["Python"]
  UV_PYTHON_INSTALL_DIR = $StateDirectorySnapshots["PythonInstall"]
  UV_TOOL_DIR = $StateDirectorySnapshots["UvTools"]
  UV_TOOL_BIN_DIR = $StateDirectorySnapshots["UvToolBin"]
  TMPDIR = $StateDirectorySnapshots["Temporary"]
  TEMP = $StateDirectorySnapshots["Temporary"]
  TMP = $StateDirectorySnapshots["Temporary"]
}
$GateConsumerEnvironment = [pscustomobject]@{
  RequiredRoot = $GateRoot
  DirectoryVariables = $GateDirectoryEnvironment
  FileVariables = [ordered]@{ UV_PYTHON = $PythonExecutableSnapshot }
  LiteralVariables = [ordered]@{
    UV_PYTHON_DOWNLOADS = "never"
    PYTHONDONTWRITEBYTECODE = "1"
    PYTHONUTF8 = "1"
    PYTEST_ADDOPTS = "-p no:cacheprovider"
  }
  Markers = @($StateMarkerSnapshots.Values) + @($GateRootMarker)
  ToolTreeSnapshots = @(
    $UvToolDirectoryTreeSnapshot,
    $PythonToolDirectoryTreeSnapshot,
    $GitToolDirectoryTreeSnapshot,
    $GhToolDirectoryTreeSnapshot
  )
}
$SessionEnvironmentNames = [Collections.Generic.HashSet[string]]::new(
  [StringComparer]::Ordinal)
foreach ($Name in @($GateConsumerEnvironment.DirectoryVariables.Keys) +
    @($GateConsumerEnvironment.FileVariables.Keys) +
    @($GateConsumerEnvironment.LiteralVariables.Keys)) {
  $null = $SessionEnvironmentNames.Add([string] $Name)
}
$OriginalSessionEnvironment = [ordered]@{}
foreach ($Name in $SessionEnvironmentNames) {
  $OriginalSessionEnvironment[$Name] = [Environment]::GetEnvironmentVariable(
    $Name, 'Process')
}
foreach ($Name in $GateConsumerEnvironment.DirectoryVariables.Keys) {
  [Environment]::SetEnvironmentVariable(
    $Name, $GateConsumerEnvironment.DirectoryVariables[$Name].Path, 'Process')
}
foreach ($Name in $GateConsumerEnvironment.FileVariables.Keys) {
  [Environment]::SetEnvironmentVariable(
    $Name, $GateConsumerEnvironment.FileVariables[$Name].Path, 'Process')
}
foreach ($Name in $GateConsumerEnvironment.LiteralVariables.Keys) {
  [Environment]::SetEnvironmentVariable(
    $Name, [string] $GateConsumerEnvironment.LiteralVariables[$Name], 'Process')
}
Assert-CustodyConsumerEnvironment $GateConsumerEnvironment `
  "session environment before native consumers"

$OriginUrl = (& $GitExecutableSnapshot.Path remote get-url origin).Trim()
Assert-NativeSuccess "resolve origin URL"
if ($OriginUrl -cnotin $AllowedOriginUrls) {
  throw "origin does not identify the configured release repository"
}

& $GitExecutableSnapshot.Path diff --check
Assert-NativeSuccess "pre-tool git diff --check"
$PreToolCheckoutState = @(
  & $GitExecutableSnapshot.Path status --porcelain=v1 --untracked-files=all --ignored)
Assert-NativeSuccess "pre-tool git status"
if ($PreToolCheckoutState.Count -ne 0) {
  throw "checkout is not fully clean before the first uv invocation"
}

$Candidate = (& $GitExecutableSnapshot.Path rev-parse HEAD).Trim()
Assert-NativeSuccess "resolve candidate"
& $GitExecutableSnapshot.Path fetch --force `
  origin master:refs/remotes/origin/master
Assert-NativeSuccess "refresh origin master for candidate"
$FetchedDefault = (& $GitExecutableSnapshot.Path `
  rev-parse refs/remotes/origin/master).Trim()
Assert-NativeSuccess "resolve fetched origin master"
$RemoteDefault = Get-RemoteMasterSha
Assert-ExactDefaultSubject $Candidate $FetchedDefault $RemoteDefault `
  "candidate default branch"
$Tree = (& $GitExecutableSnapshot.Path show -s --format=%T $Candidate).Trim()
Assert-NativeSuccess "resolve candidate tree"
$CandidateSourceClone = Resolve-StrictChildPath `
  $GateRoot "candidate-source-clone" "candidate source clone"
Invoke-CustodyConsumer "clone exact remote candidate" $GateConsumerEnvironment {
  & $GitExecutableSnapshot.Path clone --no-hardlinks --branch master --single-branch `
    "https://github.com/$Repository.git" $CandidateSourceClone
  Assert-NativeSuccess "clone exact remote candidate"
  & $GitExecutableSnapshot.Path -C $CandidateSourceClone checkout --detach $Candidate
  Assert-NativeSuccess "detach exact remote candidate"
} | Out-Null
$CandidateCloneHead = (& $GitExecutableSnapshot.Path `
  -C $CandidateSourceClone rev-parse HEAD).Trim()
Assert-NativeSuccess "resolve candidate clone HEAD"
$CandidateCloneTree = (& $GitExecutableSnapshot.Path `
  -C $CandidateSourceClone show -s --format=%T HEAD).Trim()
Assert-NativeSuccess "resolve candidate clone tree"
if ($CandidateCloneHead -ne $Candidate -or $CandidateCloneTree -ne $Tree) {
  throw "candidate clone differs from the frozen subject"
}
$CandidateSourceTreeSnapshot = Get-CustodyTreeSnapshot `
  $CandidateSourceClone "candidate source clone"
$CandidateConsumerRoot = Resolve-StrictChildPath `
  $GateRoot "candidate-consumer-tree" "candidate controlled consumer tree"
New-Item -ItemType Directory -Path $CandidateConsumerRoot | Out-Null
$CandidateTreeLease = New-CustodyTreeLease `
  $CandidateSourceTreeSnapshot $CandidateConsumerRoot `
  "candidate controlled consumer tree"
Assert-UnchangedDirectorySnapshot $GateRootSnapshot "gate root before first uv"
Assert-UnchangedFileSnapshot $GateRootMarker "gate root marker before first uv"
foreach ($StateName in $StatePaths.Keys) {
  Assert-UnchangedDirectorySnapshot $StateDirectorySnapshots[$StateName] `
    "$StateName state before first uv"
  Assert-UnchangedFileSnapshot $StateMarkerSnapshots[$StateName] `
    "$StateName binding before first uv"
}
$Version = (Invoke-CustodyConsumer "resolve package version" `
  $GateConsumerEnvironment {
    $ObservedVersion = (& $UvExecutableSnapshot.Path run `
      --project $CandidateTreeLease.ConsumerRoot `
      --frozen python -c `
      'from importlib.metadata import version; print(version("normshift"))').Trim()
    Assert-NativeSuccess "resolve package version"
    $ObservedVersion
  } -TreeLeases @($CandidateTreeLease)).Trim()
Assert-UnchangedDirectorySnapshot $GateRootSnapshot "gate root after first uv"
Assert-UnchangedFileSnapshot $GateRootMarker "gate root marker after first uv"
foreach ($StateName in $StatePaths.Keys) {
  Assert-UnchangedDirectorySnapshot $StateDirectorySnapshots[$StateName] `
    "$StateName state after first uv"
  Assert-UnchangedFileSnapshot $StateMarkerSnapshots[$StateName] `
    "$StateName binding after first uv"
}
$RunId = $env:NORMSHIFT_RUN_ID
$CiRunId = $env:NORMSHIFT_CI_RUN_ID
if ($RunId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$') {
  throw "NORMSHIFT_RUN_ID is missing or unsafe"
}
if ($CiRunId -notmatch '^[0-9]+$') { throw "NORMSHIFT_CI_RUN_ID is required" }
$PackageBase = "NormShift-$Version-$RunId"
if ($PackageBase.Length -gt 128 -or
    $PackageBase -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
  throw "version/run ID cannot form one safe package base"
}
```

## 1. Finish, review, and freeze before blind evaluation

- [ ] All M0-M2 production code, schemas, dependencies, tests, documentation,
      release notes, and the honest `0.x` version are final before candidate freeze.
- [ ] M1 contains at least three actual standards families with immutable source
      provenance and offline replay; development recipe evidence is not counted as
      the blind corpus or acceptance evidence.
- [ ] M2 implements persistent identity, split, merge, moved-and-rewritten,
      actor/action/object/scope/modality/polarity/condition/exception dimensions,
      definitions/cross-references, ambiguity, export, and complete evidence trace.
- [ ] Frozen labels/cases remain intact; no expected result, threshold, support
      floor, or fixture was deleted, weakened, relabeled, or replaced with
      case-specific production code after a failure.
- [ ] Every final scorer input, runtime dependency, schema, script, package-version
      file, and policy byte is frozen in a new exact scorer manifest after the last
      relevant change. A detached reviewer approval records its SHA-256 before any
      final prediction or score is exposed.
- [ ] Independent review reports zero open P0/P1 findings. Accepted P2+ limitations
      are recorded without contradicting release claims.
- [ ] All phase PRs are reviewed and merged; no stale repair PR remains open.
- [ ] A fresh clone of exact `origin/master` is clean, `git diff --check` exits zero,
      and status includes no tracked, untracked, or ignored checkout state.
- [ ] The release candidate commit and tree are frozen. No tracked commit is made
      after the exact-subject gates begin; any byte change restarts this checklist.

```powershell
& $GitExecutableSnapshot.Path diff --check
Assert-NativeSuccess "git diff --check"
$CheckoutState = @(& $GitExecutableSnapshot.Path `
  status --porcelain=v1 --untracked-files=all --ignored)
Assert-NativeSuccess "git status"
if ($CheckoutState.Count -ne 0) { throw "checkout is not fully clean" }
```

## 2. Exact-SHA Linux, Windows, and macOS CI

- [ ] The required `push` CI run names `$Candidate`, concludes `success`, and has
      exactly one successful required job for Ubuntu, Windows, and macOS on Python
      3.12.
- [ ] Each platform performs frozen sync, Ruff, strict mypy, full pytest with
      explicit counts and no unexplained skip/xfail/xpass, M0 R4/R5 matrices,
      benchmark, measure, two-run replay determinism, distribution build/install,
      CLI/schema smoke, source/adaptor/graph gates, and strict SBOM validation.
- [ ] M1 actual-family replay and its fail-closed matrix run on the release SHA; a
      development recipe-only check does not satisfy this box.
- [ ] M2 lineage and semantic-dimension benchmarks report all pre-registered
      per-class metrics and minimum supports on the release SHA.
- [ ] No required job or step uses `continue-on-error`, and every required GitHub
      check has zero failure/error annotations.
- [ ] The cross-platform distribution byte equality job passes on the candidate;
      each retained wheel passes canonical checking, and the three final wheel
      SHA-256 values and three final sdist SHA-256 values each collapse to one value.
- [ ] All three retained CI artifacts were downloaded, safely enumerated, hashed,
      and matched to the exact job, SHA, tree, counts, logs, and products recorded
      in the authoritative manifest.

```powershell
$Run = & $GhExecutableSnapshot.Path run view $CiRunId --repo $Repository `
  --json event,headSha,status,conclusion,jobs,url | ConvertFrom-Json
Assert-NativeSuccess "read CI run"
if ($Run.event -ne "push" -or $Run.headSha -ne $Candidate -or
    $Run.status -ne "completed" -or $Run.conclusion -ne "success") {
  throw "CI run is not a successful push run for the candidate"
}
$RequiredJobs = @(
  "deterministic-gates (ubuntu-latest)",
  "deterministic-gates (windows-latest)",
  "deterministic-gates (macos-latest)",
  "cross-platform distribution byte equality"
)
foreach ($Name in $RequiredJobs) {
  $Matches = @($Run.jobs | Where-Object { $_.name -eq $Name })
  if ($Matches.Count -ne 1 -or $Matches[0].conclusion -ne "success") {
    throw "missing or non-pass required job: $Name"
  }
}
```

## 3. Internal deterministic M0 gates on the candidate

- [ ] Frozen dependency sync, Ruff, strict mypy, and full pytest all exit zero; the
      parsed test record has no failures, errors, skips, xfails, or xpasses.
- [ ] Every R4/R5 regression and adversarial case passes, and the retained test ID
      inventory exactly matches the manifest matrix.
- [ ] The 17-case benchmark and 15-case measure suites pass, with raw cases, parsed
      counts, metrics, and hashes retained.
- [ ] Diff and FULL verify replay pass twice in separate external directories; JSON,
      Markdown, metrics, graph, and other claimed deterministic products are byte
      identical where the contract requires determinism.
- [ ] Relocation, traversal, symlink/junction/hardlink, archive alias, duplicate key,
      canonical-number, overwrite/rollback, and tamper negatives all fail closed.

```powershell
Invoke-CustodyConsumer "internal deterministic gates" `
  $GateConsumerEnvironment {
  Push-Location $CandidateTreeLease.ConsumerRoot
  try {
    & $UvExecutableSnapshot.Path sync --frozen --all-extras --dev
    Assert-NativeSuccess "frozen sync"
    & $UvExecutableSnapshot.Path run --frozen ruff check .
    Assert-NativeSuccess "Ruff"
    & $UvExecutableSnapshot.Path run --frozen mypy --no-incremental src
    Assert-NativeSuccess "mypy"
    & $UvExecutableSnapshot.Path run --frozen pytest -q -ra --color=no `
      "--junitxml=$(Join-Path $GateRoot 'pytest.xml')"
    Assert-NativeSuccess "full pytest"
    & $UvExecutableSnapshot.Path run --frozen pytest -q -ra --color=no `
      tests/e2e/test_m0_repair_round4.py tests/e2e/test_m0_repair_round5.py `
      "--junitxml=$(Join-Path $GateRoot 'm0-r4-r5.xml')"
    Assert-NativeSuccess "M0 R4/R5"
    & $UvExecutableSnapshot.Path run --frozen normshift benchmark `
      --ground-truth benchmark/ground_truth.jsonl
    Assert-NativeSuccess "M0 benchmark"
    & $UvExecutableSnapshot.Path run --frozen normshift measure `
      --ground-truth benchmark/measure_suite.jsonl `
      --out (Join-Path $GateRoot "metrics.json")
    Assert-NativeSuccess "M0 measure"
  } finally {
    Pop-Location
  }
} -TreeLeases @($CandidateTreeLease) | Out-Null
```

## 4. M1 real-source, blind-governance, and acceptance gates

The independent evaluation owner supplies all `NORMSHIFT_M1_*` paths and trust
anchors below. They must be outside the implementer's custody where the frozen
policy requires secrecy. Missing variables or inaccessible evidence are `BLOCKED`,
not permission to substitute development recipes or synthetic labels.

- [ ] The independently frozen M1 source manifest covers RFC, W3C, and WHATWG with
      the required actual versions, official immutable identity, reviewed license,
      raw hash/length, provenance, adapter/profile, and replay bindings.
- [ ] Network acquisition into an empty exact root and a separate network-free
      replay both exit zero; every redirect, receipt, body, metadata, inventory,
      adapter identity, and negative failure matrix is retained and hash-bound.
- [ ] Neutral labeling packets, independent submissions, retained adjudication
      history, corrections, and source bindings pass governance verification.
- [ ] The independently created blind split keeps whole documents/lineages isolated,
      meets every family/chain rule, is frozen before prediction start, and is not
      disclosed to implementation authors.
- [ ] M1 scoring uses the exact independently approved policy and scorer manifest.
      Every required class meets its non-zero actual-source support floor and frozen
      precision/recall/F1 threshold; no aggregate score hides a class failure.
- [ ] Raw inputs and the canonical M1 result are retained so a separate reviewer can
      recompute every count and metric. Scorer output is evidence, not audit authority.
- [ ] A separate reviewer returns durable `M1 PASS` for the same final commit/tree,
      policy/scorer bytes, source manifest, blind inputs, predictions, and result.

```powershell
$M1Manifest = $env:NORMSHIFT_M1_SOURCE_MANIFEST
$M1ManifestHash = $env:NORMSHIFT_M1_SOURCE_MANIFEST_SHA256
$Policy = $env:NORMSHIFT_ACCEPTANCE_POLICY
$ScorerManifest = $env:NORMSHIFT_SCORER_MANIFEST
$ScorerManifestHash = $env:NORMSHIFT_SCORER_MANIFEST_SHA256
$BlindSplitManifest = $env:NORMSHIFT_BLIND_SPLIT_MANIFEST
$BlindSplitHash = $env:NORMSHIFT_BLIND_SPLIT_SHA256
$LabelingPacket = $env:NORMSHIFT_LABELING_PACKET
$LabelingPacketHash = $env:NORMSHIFT_LABELING_PACKET_SHA256
$SubmissionsRoot = $env:NORMSHIFT_SUBMISSIONS_ROOT
$DecisionLedger = $env:NORMSHIFT_DECISION_LEDGER
$DecisionLedgerHash = $env:NORMSHIFT_DECISION_LEDGER_SHA256
$BlindGold = $env:NORMSHIFT_BLIND_GOLD
$BlindPredictions = $env:NORMSHIFT_BLIND_PREDICTIONS
$BlindSourceRoot = $env:NORMSHIFT_BLIND_SOURCE_ROOT
foreach ($Value in @($M1Manifest, $M1ManifestHash, $Policy,
    $ScorerManifest, $ScorerManifestHash, $BlindSplitManifest, $BlindSplitHash,
    $LabelingPacket, $LabelingPacketHash, $SubmissionsRoot, $DecisionLedger,
    $DecisionLedgerHash, $BlindGold, $BlindPredictions, $BlindSourceRoot)) {
  if (-not $Value) { throw "required M1 evidence variable is missing" }
}

$AcceptanceInputRoot = Resolve-StrictChildPath `
  $GateRoot "acceptance-inputs" "acceptance input custody root"
New-Item -ItemType Directory -Path $AcceptanceInputRoot | Out-Null
$AcceptanceInputSnapshots = [ordered]@{
  M1Manifest = Get-CustodyFileSnapshot $M1Manifest "M1 source manifest"
  Policy = Get-CustodyFileSnapshot $Policy "acceptance policy"
  ScorerManifest = Get-CustodyFileSnapshot $ScorerManifest "scorer manifest"
  BlindSplitManifest = Get-CustodyFileSnapshot `
    $BlindSplitManifest "blind split manifest"
  LabelingPacket = Get-CustodyFileSnapshot $LabelingPacket "labeling packet"
  DecisionLedger = Get-CustodyFileSnapshot $DecisionLedger "decision ledger"
  BlindGold = Get-CustodyFileSnapshot $BlindGold "blind gold input"
  BlindPredictions = Get-CustodyFileSnapshot `
    $BlindPredictions "blind predictions input"
}
$AcceptanceInputLeaseSet = New-CustodyFileLeaseSet `
  $AcceptanceInputRoot $AcceptanceInputSnapshots "acceptance inputs"
$PinnedM1Manifest = $AcceptanceInputLeaseSet.Inputs["M1Manifest"].Path
$PinnedPolicy = $AcceptanceInputLeaseSet.Inputs["Policy"].Path
$PinnedScorerManifest = $AcceptanceInputLeaseSet.Inputs["ScorerManifest"].Path
$PinnedBlindSplitManifest = `
  $AcceptanceInputLeaseSet.Inputs["BlindSplitManifest"].Path
$PinnedLabelingPacket = $AcceptanceInputLeaseSet.Inputs["LabelingPacket"].Path
$PinnedDecisionLedger = $AcceptanceInputLeaseSet.Inputs["DecisionLedger"].Path
$PinnedBlindGold = $AcceptanceInputLeaseSet.Inputs["BlindGold"].Path
$PinnedBlindPredictions = $AcceptanceInputLeaseSet.Inputs["BlindPredictions"].Path

$SubmissionsTreeSnapshot = Get-CustodyTreeSnapshot `
  $SubmissionsRoot "independent submissions root"
$PinnedSubmissionsRoot = Resolve-StrictChildPath `
  $GateRoot "pinned-submissions" "controlled submissions root"
New-Item -ItemType Directory -Path $PinnedSubmissionsRoot | Out-Null
$SubmissionsTreeLease = New-CustodyTreeLease `
  $SubmissionsTreeSnapshot $PinnedSubmissionsRoot "controlled submissions"
$BlindSourceTreeSnapshot = Get-CustodyTreeSnapshot `
  $BlindSourceRoot "independent blind source root"
$PinnedBlindSourceRoot = Resolve-StrictChildPath `
  $GateRoot "pinned-blind-sources" "controlled blind source root"
New-Item -ItemType Directory -Path $PinnedBlindSourceRoot | Out-Null
$BlindSourceTreeLease = New-CustodyTreeLease `
  $BlindSourceTreeSnapshot $PinnedBlindSourceRoot "controlled blind sources"
$M1AcquisitionRoot = Resolve-StrictChildPath `
  $GateRoot "m1-acquisition" "controlled M1 acquisition root"
$M1ResultOutputRoot = Resolve-StrictChildPath `
  $GateRoot "m1-result" "controlled M1 result root"
$M2ResultOutputRoot = Resolve-StrictChildPath `
  $GateRoot "m2-result" "controlled M2 result root"
foreach ($OutputRoot in @(
    $M1AcquisitionRoot,
    $M1ResultOutputRoot,
    $M2ResultOutputRoot)) {
  New-Item -ItemType Directory -Path $OutputRoot | Out-Null
  $null = Get-CustodyDirectorySnapshot $OutputRoot "controlled acceptance output root"
}

Invoke-CustodyConsumer "M1 acquisition consumer" $GateConsumerEnvironment {
  Push-Location $CandidateTreeLease.ConsumerRoot
  try {
    & $UvExecutableSnapshot.Path run --frozen normshift corpus acquire $PinnedM1Manifest `
      --snapshot-root $M1AcquisitionRoot --manifest-sha256 $M1ManifestHash `
      --acceptance-policy $PinnedPolicy
    Assert-NativeSuccess "M1 acquisition"
  } finally {
    Pop-Location
  }
} -FileLeaseSets @($AcceptanceInputLeaseSet) -TreeLeases @(
  $CandidateTreeLease,
  $SubmissionsTreeLease,
  $BlindSourceTreeLease
) | Out-Null
$M1SnapshotTreeSnapshot = Get-CustodyTreeSnapshot `
  $M1AcquisitionRoot "M1 acquired snapshot root"
$PinnedM1SnapshotRoot = Resolve-StrictChildPath `
  $GateRoot "pinned-m1-snapshot" "controlled M1 snapshot root"
New-Item -ItemType Directory -Path $PinnedM1SnapshotRoot | Out-Null
$M1SnapshotTreeLease = New-CustodyTreeLease `
  $M1SnapshotTreeSnapshot $PinnedM1SnapshotRoot "controlled M1 snapshot"

Invoke-CustodyConsumer "M1 acceptance consumers" $GateConsumerEnvironment {
  Push-Location $CandidateTreeLease.ConsumerRoot
  try {
    & $UvExecutableSnapshot.Path run --frozen normshift corpus verify-sources `
      $PinnedM1Manifest `
      --snapshot-root $M1SnapshotTreeLease.ConsumerRoot `
      --manifest-sha256 $M1ManifestHash --acceptance-policy $PinnedPolicy
    Assert-NativeSuccess "M1 offline replay"

    & $UvExecutableSnapshot.Path run --frozen normshift governance `
      verify-blind-split `
      $PinnedBlindSplitManifest --manifest-sha256 $BlindSplitHash `
      --source-manifest $PinnedM1Manifest `
      --source-manifest-sha256 $M1ManifestHash `
      --acceptance-policy $PinnedPolicy
    Assert-NativeSuccess "blind split governance"

    & $UvExecutableSnapshot.Path run --frozen normshift governance `
      verify-labeling `
      $PinnedLabelingPacket --packet-sha256 $LabelingPacketHash `
      --source-manifest $PinnedM1Manifest `
      --source-manifest-sha256 $M1ManifestHash `
      --submissions-root $SubmissionsTreeLease.ConsumerRoot `
      --ledger $PinnedDecisionLedger --ledger-sha256 $DecisionLedgerHash `
      --blind-split-manifest $PinnedBlindSplitManifest `
      --split-manifest-sha256 $BlindSplitHash `
      --acceptance-policy $PinnedPolicy
    Assert-NativeSuccess "labeling governance"

    & $UvExecutableSnapshot.Path run --frozen python `
      scripts/score_acceptance.py `
      --policy $PinnedPolicy --gold $PinnedBlindGold `
      --predictions $PinnedBlindPredictions `
      --scorer-manifest $PinnedScorerManifest `
      --scorer-manifest-sha256 $ScorerManifestHash `
      --source-root $BlindSourceTreeLease.ConsumerRoot `
      --required-phase M1 `
      --output-root $M1ResultOutputRoot
    Assert-NativeSuccess "M1 frozen scoring"
  } finally {
    Pop-Location
  }
} -FileLeaseSets @($AcceptanceInputLeaseSet) -TreeLeases @(
  $CandidateTreeLease,
  $M1SnapshotTreeLease,
  $SubmissionsTreeLease,
  $BlindSourceTreeLease
) | Out-Null
$M1ResultTreeSnapshot = Get-CustodyTreeSnapshot `
  $M1ResultOutputRoot "controlled M1 result"
```

## 5. M2 lineage and semantic acceptance gates

- [ ] Each real RFC, W3C, and WHATWG chain has at least three whole versions where
      required, with stable document/requirement/lineage identity and no train/test
      document or lineage leakage.
- [ ] Split, merge, move-only, rewrite-only, moved-and-rewritten, add/remove,
      ambiguity, definition, and cross-reference behavior is represented by frozen
      real and synthetic adversarial cases.
- [ ] Actor, action, object, scope, modality, polarity, condition, and exception
      change dimensions use conservative unknown/ambiguous outcomes and bind exact
      old/new requirement IDs, hashes, locators, and sources.
- [ ] Graph export is deterministic, schema-valid, and internally complete; every
      node/edge/evidence reference resolves exactly, and tamper/orphan/collision/
      cycle/ordering negatives fail closed.
- [ ] M2 scoring uses the exact approved policy/scorer and independently controlled
      blind data. Every pre-registered class and slot meets its non-zero support and
      precision/recall/F1 gate; no aggregate result masks a failure.
- [ ] Raw M2 sources, gold, predictions, graph outputs, and canonical result are
      retained and independently recomputable.
- [ ] A separate reviewer returns durable `M2 PASS` for the same final subject and
      also confirms M0 and M1 remain passing within that subject.

```powershell
Invoke-CustodyConsumer "M2 acceptance consumer" $GateConsumerEnvironment {
  Push-Location $CandidateTreeLease.ConsumerRoot
  try {
    & $UvExecutableSnapshot.Path run --frozen python `
      scripts/score_acceptance.py `
      --policy $PinnedPolicy --gold $PinnedBlindGold `
      --predictions $PinnedBlindPredictions `
      --scorer-manifest $PinnedScorerManifest `
      --scorer-manifest-sha256 $ScorerManifestHash `
      --source-root $BlindSourceTreeLease.ConsumerRoot `
      --required-phase M2 `
      --output-root $M2ResultOutputRoot
    Assert-NativeSuccess "M2 frozen scoring"
  } finally {
    Pop-Location
  }
} -FileLeaseSets @($AcceptanceInputLeaseSet) -TreeLeases @(
  $CandidateTreeLease,
  $M1SnapshotTreeLease,
  $SubmissionsTreeLease,
  $BlindSourceTreeLease
) | Out-Null
$M2ResultTreeSnapshot = Get-CustodyTreeSnapshot `
  $M2ResultOutputRoot "controlled M2 result"
Close-CustodyTreeLease $M1SnapshotTreeLease "controlled M1 snapshot"
Close-CustodyTreeLease $SubmissionsTreeLease "controlled submissions"
Close-CustodyTreeLease $BlindSourceTreeLease "controlled blind sources"
Close-CustodyFileLeaseSet $AcceptanceInputLeaseSet "acceptance inputs"
```

## 6. Exact-SHA authoritative package

- [ ] The package builder, manifest schema, and external verifier have been extended
      and tested to bind the final M1/M2 source, blind-governance, per-class/support,
      graph, and audit inputs. The historical M0-only package format is insufficient.
- [ ] One clean exact checkout builds one Git bundle and one canonical-prefix
      Source.zip from `$Candidate`, plus one wheel, one sdist, and one strict
      CycloneDX SBOM. No tracked commit follows the gate.
- [ ] One complete authoritative pre-audit manifest records the exact commit/tree,
      version, run ID, tools/platforms, commands/exit codes/log hashes, parsed counts,
      every M0/M1/M2 matrix and metric/support result, source/ground-truth hashes,
      known limitations, and all artifact sizes/hashes.
- [ ] The manifest has a strict versioned schema, rejects duplicate/unknown critical
      fields, contains no absent-field success defaults, and caps pre-audit milestone
      status at `M*_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.
- [ ] Exactly these required products exist and are hash-bound: bundle, Source.zip,
      wheel, sdist, SBOM, manifest, checksums, and audit contract.
- [ ] Bundle `git fsck --full --strict`, bundle-clone HEAD/tree, archive raw-name
      safety, canonical prefix, tracked file set, blob equality, relocation replay,
      extracted-archive replay, wheel/sdist isolated install, CLI/schema smoke, and
      SBOM-to-lock/distribution inventory all pass.
- [ ] Package-verifier corruption tests reject changed/omitted manifest fields,
      false counts, changed labels, wrong commit/tree, altered bundle/archive/
      distribution, duplicate/unsafe paths, omitted logs, and mismatched SBOM.
- [ ] Running the external package verifier from an unrelated directory exits zero
      with `PACKAGE_PREFLIGHT_ONLY`; that result is not mislabeled as external PASS.

```powershell
$PackageOutputRoot = Resolve-StrictChildPath `
  $GateRoot "authoritative-package-output" "package output root"
New-Item -ItemType Directory -Path $PackageOutputRoot | Out-Null
$PackageOutputSnapshot = Get-CustodyDirectorySnapshot `
  $PackageOutputRoot "package output root"
$PackageOutputMarker = New-CustodyMarker `
  $PackageOutputRoot ".normshift-package-output.anchor" "package output binding" `
  "$($PackageOutputSnapshot.FinalPath)|$($PackageOutputSnapshot.PhysicalId)`n"
$Builder = Assert-DescendantPath $CandidateTreeLease.ConsumerRoot `
  (Join-Path $CandidateTreeLease.ConsumerRoot `
    "scripts/build_authoritative_package.py") `
  "authoritative package builder"
$BuilderSnapshot = Get-CustodyFileSnapshot $Builder "authoritative package builder"
Invoke-CustodyConsumer "authoritative package build" $GateConsumerEnvironment {
  Push-Location $CandidateTreeLease.ConsumerRoot
  try {
    & $UvExecutableSnapshot.Path run --frozen python $Builder `
      --repo $CandidateTreeLease.ConsumerRoot `
      --output-root $PackageOutputRoot --commit $Candidate `
      --repository-url "https://github.com/taipei49314/NormShift" `
      --default-branch master --run-id $RunId
    Assert-NativeSuccess "authoritative package build"
  } finally {
    Pop-Location
  }
} -TreeLeases @($CandidateTreeLease) | Out-Null
Assert-UnchangedFileSnapshot $BuilderSnapshot "package builder after use"
Assert-UnchangedDirectorySnapshot $PackageOutputSnapshot "package output after build"
Assert-UnchangedFileSnapshot $PackageOutputMarker "package output binding after build"

$PackageRoot = Assert-DescendantPath $PackageOutputRoot `
  (Join-Path $PackageOutputRoot $PackageBase) "authoritative package root"
$PackageRootSnapshot = Get-CustodyDirectorySnapshot `
  $PackageRoot "authoritative package root"
$PackageTreeSnapshot = Get-CustodyTreeSnapshot `
  $PackageRoot "authoritative package before preflight"
$ManifestPath = Resolve-StrictChildPath `
  $PackageRoot "$PackageBase-MANIFEST.json" "authoritative manifest"
$BundlePath = Resolve-StrictChildPath `
  $PackageRoot "$PackageBase.bundle" "authoritative bundle"
$SourceZipPath = Resolve-StrictChildPath `
  $PackageRoot "$PackageBase-Source.zip" "authoritative Source.zip"
$ManifestSnapshot = Get-CustodyFileSnapshot $ManifestPath "authoritative manifest"
$BundleSnapshot = Get-CustodyFileSnapshot $BundlePath "authoritative bundle"
$SourceZipSnapshot = Get-CustodyFileSnapshot $SourceZipPath "authoritative Source.zip"

$PackageConsumerRoot = Resolve-StrictChildPath `
  $GateRoot "package-consumer-tree" "controlled package consumer tree"
New-Item -ItemType Directory -Path $PackageConsumerRoot | Out-Null
$PackageTreeLease = New-CustodyTreeLease `
  $PackageTreeSnapshot $PackageConsumerRoot "controlled package consumer tree"
$PinnedManifestPath = Resolve-StrictChildPath `
  $PackageTreeLease.ConsumerRoot "$PackageBase-MANIFEST.json" `
  "pinned authoritative manifest"
$PinnedBundlePath = Resolve-StrictChildPath `
  $PackageTreeLease.ConsumerRoot "$PackageBase.bundle" `
  "pinned authoritative bundle"
$PinnedSourceZipPath = Resolve-StrictChildPath `
  $PackageTreeLease.ConsumerRoot "$PackageBase-Source.zip" `
  "pinned authoritative Source.zip"
$AuditClone = Resolve-StrictChildPath `
  $GateRoot "package-preflight-clone" "package preflight clone"
Invoke-CustodyConsumer "clone package preflight subject" $GateConsumerEnvironment {
  & $GitExecutableSnapshot.Path clone --no-hardlinks --branch master --single-branch `
    "https://github.com/$Repository.git" $AuditClone
  Assert-NativeSuccess "clone exact public candidate for package preflight"
  & $GitExecutableSnapshot.Path -C $AuditClone checkout --detach $Candidate
  Assert-NativeSuccess "detach package preflight clone at candidate"
} | Out-Null
$AuditCloneSnapshot = Get-CustodyDirectorySnapshot `
  $AuditClone "package preflight clone"
$AuditCloneTreeSnapshot = Get-CustodyTreeSnapshot `
  $AuditClone "package preflight clone tree"
$AuditCloneConsumerRoot = Resolve-StrictChildPath `
  $GateRoot "package-preflight-consumer-tree" `
  "controlled package preflight clone"
New-Item -ItemType Directory -Path $AuditCloneConsumerRoot | Out-Null
$AuditCloneTreeLease = New-CustodyTreeLease `
  $AuditCloneTreeSnapshot $AuditCloneConsumerRoot `
  "controlled package preflight clone"
$Verifier = Assert-DescendantPath $AuditCloneTreeLease.ConsumerRoot `
  (Join-Path $AuditCloneTreeLease.ConsumerRoot `
    "scripts/external_package_verify.py") `
  "pinned external package verifier"
$VerifierSnapshot = Get-CustodyFileSnapshot $Verifier "pinned external package verifier"
$PreflightWorkRoot = Resolve-StrictChildPath `
  $GateRoot "package-preflight-work" "package preflight work root"
New-Item -ItemType Directory -Path $PreflightWorkRoot | Out-Null
$PreflightWorkSnapshot = Get-CustodyDirectorySnapshot `
  $PreflightWorkRoot "package preflight work root"
$PreflightWorkMarker = New-CustodyMarker `
  $PreflightWorkRoot ".normshift-preflight.anchor" "package preflight work binding"
Invoke-CustodyConsumer "external package preflight" $GateConsumerEnvironment {
  Push-Location $PreflightWorkRoot
  try {
    & $UvExecutableSnapshot.Path run `
      --project $AuditCloneTreeLease.ConsumerRoot --frozen python `
      $Verifier `
      --repo $AuditCloneTreeLease.ConsumerRoot `
      --manifest $PinnedManifestPath `
      --bundle $PinnedBundlePath `
      --source-zip $PinnedSourceZipPath
    Assert-NativeSuccess "external package preflight"
  } finally {
    Pop-Location
  }
} -TreeLeases @($AuditCloneTreeLease, $PackageTreeLease) | Out-Null
Assert-UnchangedFileSnapshot $VerifierSnapshot "external verifier after preflight"
Assert-UnchangedFileSnapshot $ManifestSnapshot "manifest after preflight"
Assert-UnchangedFileSnapshot $BundleSnapshot "bundle after preflight"
Assert-UnchangedFileSnapshot $SourceZipSnapshot "Source.zip after preflight"
Assert-UnchangedTreeSnapshot $PackageTreeSnapshot "package tree after preflight"
Assert-CustodyTreeLeaseUnchanged $PackageTreeLease `
  "controlled package tree after preflight"
Assert-UnchangedDirectorySnapshot $AuditCloneSnapshot "preflight clone after verifier"
Assert-UnchangedTreeSnapshot $AuditCloneTreeSnapshot "preflight clone tree after verifier"
Assert-UnchangedDirectorySnapshot $PreflightWorkSnapshot "preflight work after verifier"
Assert-UnchangedFileSnapshot $PreflightWorkMarker "preflight work binding after verifier"
Close-CustodyTreeLease $AuditCloneTreeLease `
  "controlled package preflight clone"
Close-CustodyTreeLease $PackageTreeLease `
  "controlled package tree after preflight handoff"
foreach ($StateName in $StatePaths.Keys) {
  Assert-UnchangedDirectorySnapshot $StateDirectorySnapshots[$StateName] `
    "$StateName state after package preflight"
  Assert-UnchangedFileSnapshot $StateMarkerSnapshots[$StateName] `
    "$StateName binding after package preflight"
}
```

## 7. Detached clean-room external audit

- [ ] The candidate manifest is frozen before reviewer handoff. The reviewer receives
      only the declared package/public exact commit, audit contract, and frozen
      expected inputs, not the implementer's working tree or editable environment.
- [ ] The reviewer first verifies hashes, clones the bundle, extracts Source.zip to
      an unrelated path, creates fresh Python 3.12 environments, and reruns frozen
      sync, Ruff, mypy, full tests, M0 matrices/replay, M1 actual-family/failure
      matrices, M2 graph/metrics, two-location determinism, wheel/sdist smoke, and
      SBOM/package verification.
- [ ] External evidence includes both Linux and Windows execution. macOS is covered
      by exact-SHA CI; an unavailable optional clean-room macOS run is not claimed.
- [ ] The reviewer independently recomputes every published count, per-class support,
      precision, recall, F1, graph result, and artifact hash from retained raw inputs.
- [ ] The detached JSON audit strictly validates against
      `schemas/external_audit_v1.schema.json` and records the externally frozen
      manifest SHA-256, run ID, commit/tree/version, exact P0/P1/P2 counts,
      limitations, and one combined M0/M1/M2 verdict. Its structured
      `execution_authority` is exactly `windows` / `NTFS`, lock policy
      `normshift-windows-ntfs-share-deny` version `1.0.0`, the same authority run
      ID, fixed/local/same-volume `true` state, and preflight result `PASS`; no
      free-form substitute is accepted. It binds SHA-256 inventories of every
      approved custody-root check and its non-exported volume-serial policy binding,
      rather than exposing a machine-specific serial. The old package-manifest
      `environment.os` records a build environment only and is not release-execution
      authority.
- [ ] The combined exact-subject verdict is PASS with P0=0, P1=0, no missing required
      gate, no false success, no subject/hash mismatch, and no changed expected label.
- [ ] The audit output remains detached and is not added into or used to rewrite the
      frozen pre-audit manifest. Its hash is recorded for release attachment.

Any failure invalidates the candidate. Fix through a new reviewed PR, choose a new
SHA/run ID, rebuild every affected product, and repeat the full audit. Never patch an
audited candidate or move a tag.

## 8. Documentation and release publication

- [ ] `README.md`, `CLAIMS.md`, `MISSION_STATE.json`, `DECISIONS.md`, North Star and
      evidence docs, threat/security/licensing docs, `CHANGELOG.md`, package metadata,
      CLI, schemas, audit, and release notes agree on exact status, version, subject,
      capabilities, exclusions, and limitations.
- [ ] Historical R4/R5 failures and the exact `b3af3dc...` M0 audit remain
      discoverable as history; neither is edited into a verdict for the final SHA.
- [ ] The final release language is bounded to deterministic local M0-M2 tooling and
      explicitly excludes M3+, hosted/production operation, universal standards
      coverage, cryptographic authenticity, and unmeasured real-world accuracy or
      adoption.
- [ ] One annotated tag is created only after the detached PASS. The tag object peels
      to `$Candidate`, which equals the audited manifest commit and default SHA.
- [ ] The tag/release workflow and exact release CI are green; no tag is moved and no
      prior release/tag is rewritten or deleted.
- [ ] One non-draft software release is published from one sealed audited physical
      root only, using independent `NORMSHIFT_MANIFEST_SHA256` and
      `NORMSHIFT_EXTERNAL_AUDIT_SHA256` trust anchors, with the bounded release notes
      and exactly the audited wheel, sdist, Source.zip, bundle, SBOM, manifest,
      checksums, audit contract, and detached external audit attached.

```powershell
& $GitExecutableSnapshot.Path fetch --force `
  origin master:refs/remotes/origin/master
Assert-NativeSuccess "refresh origin master before publication"
$PublicationFetchedDefault = (& $GitExecutableSnapshot.Path `
  rev-parse refs/remotes/origin/master).Trim()
Assert-NativeSuccess "resolve publication origin master"
$PublicationRemoteDefault = Get-RemoteMasterSha
Assert-ExactDefaultSubject $Candidate $PublicationFetchedDefault `
  $PublicationRemoteDefault "publication default branch"

$ExpectedReleaseAssetNames = [ordered]@{
  Wheel = "normshift-$Version-py3-none-any.whl"
  Sdist = "normshift-$Version.tar.gz"
  SourceZip = "$PackageBase-Source.zip"
  Bundle = "$PackageBase.bundle"
  Sbom = "normshift-$Version-sbom.cdx.json"
  Manifest = "$PackageBase-MANIFEST.json"
  Checksums = "$PackageBase-CHECKSUMS.txt"
  AuditContract = "$PackageBase-AUDIT-CONTRACT.md"
  ExternalAudit = "$PackageBase-EXTERNAL-AUDIT.json"
}
if ($ExpectedReleaseAssetNames.Count -ne 9) {
  throw "the fixed release asset inventory must contain exactly nine names"
}

if (-not $env:NORMSHIFT_SEALED_AUDITED_ROOT) {
  throw "NORMSHIFT_SEALED_AUDITED_ROOT is required"
}
$SealedRootSnapshot = Get-CustodyDirectorySnapshot `
  $env:NORMSHIFT_SEALED_AUDITED_ROOT "sealed audited root"
if ($SealedRootSnapshot.PhysicalId -cne $PackageRootSnapshot.PhysicalId -or
    $SealedRootSnapshot.FinalPath -cne $PackageRootSnapshot.FinalPath) {
  throw "sealed audited root differs from the preflighted package root"
}
$SealedTreeSnapshot = Get-CustodyTreeSnapshot `
  $SealedRootSnapshot.Path "sealed audited publication tree"
$PublicationConsumerRoot = Resolve-StrictChildPath `
  $GateRoot "publication-consumer-tree" "controlled publication input tree"
New-Item -ItemType Directory -Path $PublicationConsumerRoot | Out-Null
$PublicationTreeLease = New-CustodyTreeLease `
  $SealedTreeSnapshot $PublicationConsumerRoot `
  "controlled publication input tree"

$ManifestAnchor = [string] $env:NORMSHIFT_MANIFEST_SHA256
$ExternalAuditAnchor = [string] $env:NORMSHIFT_EXTERNAL_AUDIT_SHA256
if ($ManifestAnchor -notmatch '^[0-9a-f]{64}$' -or
    $ExternalAuditAnchor -notmatch '^[0-9a-f]{64}$') {
  throw "external manifest and audit SHA-256 trust anchors are required"
}

$ReleaseAssetSources = [ordered]@{}
$ReleaseAssetSnapshots = [ordered]@{}
$ReleaseAssetPaths = @()
$ReleaseAssetNameSet = [Collections.Generic.HashSet[string]]::new(
  [StringComparer]::OrdinalIgnoreCase)
foreach ($Role in @($ExpectedReleaseAssetNames.Keys)) {
  $ExpectedName = [string] $ExpectedReleaseAssetNames[$Role]
  $Source = Resolve-StrictChildPath `
    $PublicationTreeLease.ConsumerRoot $ExpectedName `
    "pinned sealed release asset $Role"
  $Snapshot = Get-CustodyFileSnapshot $Source "sealed release asset $Role"
  if (-not $ReleaseAssetNameSet.Add($ExpectedName)) {
    throw "release asset names collide across platforms"
  }
  $ReleaseAssetSources[$Role] = $Source
  $ReleaseAssetSnapshots[$Role] = $Snapshot
  $ReleaseAssetPaths += $Source
}
if ($ReleaseAssetPaths.Count -ne 9) {
  throw "release publication requires exactly nine asset paths"
}

$ManifestSnapshot = $ReleaseAssetSnapshots["Manifest"]
$ExternalAuditSnapshot = $ReleaseAssetSnapshots["ExternalAudit"]
if ($ManifestSnapshot.Sha256 -cne $ManifestAnchor) {
  throw "sealed manifest differs from NORMSHIFT_MANIFEST_SHA256"
}
if ($ExternalAuditSnapshot.Sha256 -cne $ExternalAuditAnchor) {
  throw "sealed external audit differs from NORMSHIFT_EXTERNAL_AUDIT_SHA256"
}

$ManifestDocument = Get-Content -LiteralPath $ManifestSnapshot.Path `
  -Raw | ConvertFrom-Json -Depth 100
Assert-UnchangedFileSnapshot $ManifestSnapshot "manifest after identity parse"
if ($ManifestDocument.package_commit -ne $Candidate -or
    $ManifestDocument.package_tree -ne $Tree -or
    $ManifestDocument.package_version -ne $Version -or
    $ManifestDocument.run_id -ne $RunId) {
  throw "release manifest identity differs from the candidate"
}
$ManifestArtifactRoles = [ordered]@{
  Bundle = "bundle"
  SourceZip = "source_zip"
  Wheel = "wheel"
  Sdist = "sdist"
  Sbom = "sbom"
  Checksums = "checksums"
  AuditContract = "audit_contract"
}
foreach ($Role in $ManifestArtifactRoles.Keys) {
  $ManifestKey = $ManifestArtifactRoles[$Role]
  $Record = $ManifestDocument.artifacts.$ManifestKey
  $Snapshot = $ReleaseAssetSnapshots[$Role]
  if ($null -eq $Record -or $Record.path -cne $ExpectedReleaseAssetNames[$Role] -or
      $Record.sha256 -cne $Snapshot.Sha256 -or
      [int64] $Record.size -ne $Snapshot.Size) {
    throw "release asset $Role differs from the authoritative manifest inventory"
  }
}

$ReleaseNotes = Resolve-StrictChildPath $PublicationTreeLease.ConsumerRoot `
  "$PackageBase-RELEASE-NOTES.md" "sealed release notes"
$ReleaseNotesSnapshot = Get-CustodyFileSnapshot $ReleaseNotes "sealed release notes"
$PublicationAuditClone = Resolve-StrictChildPath `
  $GateRoot "publication-audit-clone" "publication bundle clone"
Invoke-CustodyConsumer "clone publication bundle" $GateConsumerEnvironment {
  & $GitExecutableSnapshot.Path clone --no-hardlinks `
    $ReleaseAssetSources["Bundle"] `
    $PublicationAuditClone
  Assert-NativeSuccess "clone publication bundle"
} -TreeLeases @($PublicationTreeLease) | Out-Null
$PublicationCloneHead = (& $GitExecutableSnapshot.Path `
  -C $PublicationAuditClone rev-parse HEAD).Trim()
Assert-NativeSuccess "resolve publication clone HEAD"
$PublicationCloneTree = (& $GitExecutableSnapshot.Path `
  -C $PublicationAuditClone show -s --format=%T HEAD).Trim()
Assert-NativeSuccess "resolve publication clone tree"
if ($PublicationCloneHead -ne $Candidate -or $PublicationCloneTree -ne $Tree) {
  throw "publication bundle clone differs from the frozen release subject"
}
$PublicationAuditCloneTreeSnapshot = Get-CustodyTreeSnapshot `
  $PublicationAuditClone "publication bundle clone"
$PublicationAuditConsumerRoot = Resolve-StrictChildPath `
  $GateRoot "publication-audit-consumer-tree" `
  "controlled publication verifier tree"
New-Item -ItemType Directory -Path $PublicationAuditConsumerRoot | Out-Null
$PublicationAuditTreeLease = New-CustodyTreeLease `
  $PublicationAuditCloneTreeSnapshot $PublicationAuditConsumerRoot `
  "controlled publication verifier tree"
$AuditVerifier = Assert-DescendantPath $PublicationAuditTreeLease.ConsumerRoot `
  (Join-Path $PublicationAuditTreeLease.ConsumerRoot `
    "scripts/verify_external_audit.py") `
  "pinned external audit trust-anchor verifier"
$AuditSchema = Assert-DescendantPath $PublicationAuditTreeLease.ConsumerRoot `
  (Join-Path $PublicationAuditTreeLease.ConsumerRoot `
    "schemas/external_audit_v1.schema.json") `
  "pinned external audit schema"
$AuditVerifierSnapshot = Get-CustodyFileSnapshot `
  $AuditVerifier "external audit trust-anchor verifier"
$AuditSchemaSnapshot = Get-CustodyFileSnapshot $AuditSchema "external audit schema"
$AuthorityEvidence = Get-CustodyAuthorityEvidenceSha256 `
  $script:CustodyVolumeAuthority
$AuditVerificationJson = (Invoke-CustodyConsumer `
  "verify detached external audit trust anchors before tag" `
  $GateConsumerEnvironment {
    (& $UvExecutableSnapshot.Path run `
      --project $PublicationAuditTreeLease.ConsumerRoot --frozen python `
      $AuditVerifier `
      --manifest $ManifestSnapshot.Path `
      --audit $ExternalAuditSnapshot.Path `
      --schema $AuditSchemaSnapshot.Path `
      --manifest-sha256 $ManifestAnchor `
      --audit-sha256 $ExternalAuditAnchor `
      --roots-inventory-sha256 $AuthorityEvidence.RootsInventorySha256 `
      --approved-volume-binding-sha256 `
        $AuthorityEvidence.ApprovedVolumeBindingSha256 `
      --commit $Candidate --tree $Tree --version $Version --run-id $RunId |
      Out-String).Trim()
    Assert-NativeSuccess "verify detached external audit trust anchors before tag"
  } -TreeLeases @($PublicationTreeLease, $PublicationAuditTreeLease)).Trim()
$AuditVerification = $AuditVerificationJson | ConvertFrom-Json -Depth 20
if ($AuditVerification.ok -ne $true -or $AuditVerification.p0 -ne 0 -or
    $AuditVerification.p1 -ne 0 -or
    $AuditVerification.verdict -cne
      "M0_M1_M2_COMBINED_EXTERNAL_AUDIT_PASS") {
  throw "detached audit does not authorize a combined release"
}
Assert-UnchangedFileSnapshot $ManifestSnapshot "manifest after audit verification"
Assert-UnchangedFileSnapshot $ExternalAuditSnapshot `
  "external audit after trust-anchor verification"
Assert-UnchangedFileSnapshot $AuditVerifierSnapshot "audit verifier after use"
Assert-UnchangedFileSnapshot $AuditSchemaSnapshot "audit schema after use"
Assert-UnchangedTreeSnapshot $SealedTreeSnapshot `
  "sealed audited tree before tag creation"
foreach ($StateName in $StatePaths.Keys) {
  Assert-UnchangedDirectorySnapshot $StateDirectorySnapshots[$StateName] `
    "$StateName state before tag creation"
  Assert-UnchangedFileSnapshot $StateMarkerSnapshots[$StateName] `
    "$StateName binding before tag creation"
}

$Tag = "v$Version"
& $GitExecutableSnapshot.Path tag -a $Tag $Candidate -m "NormShift $Version"
Assert-NativeSuccess "create annotated tag"
if ((& $GitExecutableSnapshot.Path cat-file -t $Tag).Trim() -ne "tag") {
  throw "tag is not annotated"
}
$Peeled = (& $GitExecutableSnapshot.Path rev-list -n 1 $Tag).Trim()
Assert-NativeSuccess "peel tag"
if ($Peeled -ne $Candidate) { throw "tag does not point to audited candidate" }
& $GitExecutableSnapshot.Path push origin $Tag
Assert-NativeSuccess "push annotated tag"

Invoke-CustodyConsumer "publish GitHub release" $GateConsumerEnvironment {
  & $GhExecutableSnapshot.Path release create $Tag `
    --repo $Repository --verify-tag `
    --target $Candidate --title "NormShift $Version" `
    --notes-file $ReleaseNotes @ReleaseAssetPaths
  Assert-NativeSuccess "publish release"
} -TreeLeases @($PublicationTreeLease) | Out-Null
foreach ($Role in $ReleaseAssetSnapshots.Keys) {
  Assert-UnchangedFileSnapshot $ReleaseAssetSnapshots[$Role] `
    "release asset $Role after publication"
}
Assert-UnchangedFileSnapshot $ReleaseNotesSnapshot "release notes after publication"
Assert-UnchangedFileSnapshot $AuditVerifierSnapshot `
  "audit verifier after publication"
Assert-UnchangedFileSnapshot $AuditSchemaSnapshot "audit schema after publication"
Assert-UnchangedTreeSnapshot $SealedTreeSnapshot `
  "sealed audited tree after publication"
Close-CustodyTreeLease $PublicationAuditTreeLease `
  "controlled publication verifier tree"
Close-CustodyTreeLease $PublicationTreeLease `
  "controlled publication input tree"
```

## 9. Download every release asset and reverify

- [ ] A new empty directory outside all implementation/audit/package roots is used;
      every release asset is downloaded from GitHub, not copied from staging.
- [ ] The downloaded asset name/count set exactly matches the release and manifest;
      all sizes and SHA-256 values match the authoritative inventories.
- [ ] The downloaded audit bundle and every archive pass raw-name, duplicate,
      traversal, rooted-path, backslash, case-collision, local/central-name, CRC,
      symlink, and special-entry safety checks before extraction.
- [ ] The downloaded bundle, Source.zip, manifest, wheel, sdist, SBOM, and checksums
      pass the external package verifier from unrelated fresh paths.
- [ ] The downloaded wheel and sdist each install into a new isolated environment
      outside the source tree; `pip check`, metadata/version, entry point, packaged
      schemas, `normshift --version`, help, diff, and FULL report verification pass.
- [ ] The downloaded SBOM is strict-schema-valid, non-placeholder, and exactly agrees
      with the lockfile plus downloaded wheel/sdist package/dependency inventory.
- [ ] The GitHub release tag object is annotated, peels to the manifest commit, equals
      default SHA, and its release/tag CI run is green.
- [ ] Download-only commands, outputs, hashes, install logs, and smoke results are
      retained as final release evidence.

The block below accepts one path authority only:
`NORMSHIFT_RELEASE_DOWNLOAD_ROOT`. It derives all nine fixed asset paths beneath
that new root; per-asset downloaded path overrides are forbidden. GitHub's release
inventory must provide a lowercase SHA-256 digest and exact size for every asset,
the package artifacts must independently match the downloaded manifest records, and
the same two external digest anchors must validate the detached audit a second time.
All bundle clones, package/audit verifiers, environments, temporary directories, and
their immutable consumer copies are physical descendants of that one download root.

```powershell
if (-not $env:NORMSHIFT_RELEASE_DOWNLOAD_ROOT) {
  throw "NORMSHIFT_RELEASE_DOWNLOAD_ROOT is required"
}
$DownloadRawPath = $env:NORMSHIFT_RELEASE_DOWNLOAD_ROOT.Replace('/', '\')
if ((Test-IsWindows) -and
    ($DownloadRawPath.StartsWith('\\?\') -or $DownloadRawPath.StartsWith('\\.\'))) {
  throw "download root uses a forbidden Windows device or extended-length alias"
}
$DownloadRoot = [IO.Path]::GetFullPath($env:NORMSHIFT_RELEASE_DOWNLOAD_ROOT)
if (Test-Path -LiteralPath $DownloadRoot) {
  throw "download root must not already exist"
}
$DownloadParent = [IO.Path]::GetDirectoryName($DownloadRoot)
if (-not $DownloadParent -or
    -not (Test-Path -LiteralPath $DownloadParent -PathType Container)) {
  throw "download root parent must already exist"
}
Assert-WindowsReleaseCustodyPathAuthority $DownloadParent `
  $script:CustodyVolumeAuthority "download root parent"
Assert-WindowsReleaseCustodyPathAuthority $DownloadRoot `
  $script:CustodyVolumeAuthority "download root"
$DownloadParentSnapshot = Get-CustodyDirectorySnapshot `
  $DownloadParent "download root parent"
New-Item -ItemType Directory -Path $DownloadRoot | Out-Null
$DownloadRootSnapshot = Get-CustodyDirectorySnapshot `
  $env:NORMSHIFT_RELEASE_DOWNLOAD_ROOT "download root"
$DownloadRoot = $DownloadRootSnapshot.FinalPath
$DownloadAssetRoot = Resolve-StrictChildPath `
  $DownloadRoot "release-assets" "downloaded release asset root"
New-Item -ItemType Directory -Path $DownloadAssetRoot | Out-Null
$DownloadAssetRootSnapshot = Get-CustodyDirectorySnapshot `
  $DownloadAssetRoot "downloaded release asset root"
$DownloadRootMarker = New-CustodyMarker `
  $DownloadRoot ".normshift-download.anchor" "download root binding" `
  "$($DownloadRootSnapshot.FinalPath)|$($DownloadRootSnapshot.PhysicalId)`n"
$DownloadStateRoot = Resolve-StrictChildPath `
  $DownloadRoot "verification-state" "download verification state root"
New-Item -ItemType Directory -Path $DownloadStateRoot | Out-Null
$DownloadStateRootSnapshot = Get-CustodyDirectorySnapshot `
  $DownloadStateRoot "download verification state root"
$DownloadStatePaths = [ordered]@{
  ProjectEnvironment = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "project-env") "download uv environment"
  UvCache = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "uv-cache") "download uv cache"
  Hypothesis = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "hypothesis") "download hypothesis state"
  Mypy = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "mypy-cache") "download mypy state"
  Ruff = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "ruff-cache") "download Ruff state"
  Python = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "python-pycache") "download Python state"
  PythonInstall = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "uv-python-install") `
    "download uv Python install state"
  UvTools = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "uv-tools") "download uv tool state"
  UvToolBin = Assert-DescendantPath $DownloadRoot `
    (Join-Path $DownloadStateRoot "uv-tool-bin") "download uv tool bin state"
}
$DownloadStateDirectorySnapshots = [ordered]@{}
$DownloadStateMarkerSnapshots = [ordered]@{}
foreach ($StateName in $DownloadStatePaths.Keys) {
  New-Item -ItemType Directory -Path $DownloadStatePaths[$StateName] | Out-Null
  $DirectorySnapshot = Get-CustodyDirectorySnapshot `
    $DownloadStatePaths[$StateName] "download $StateName state"
  $DownloadStateDirectorySnapshots[$StateName] = $DirectorySnapshot
  $DownloadStateMarkerSnapshots[$StateName] = New-CustodyMarker `
    $DownloadStateRoot ".normshift-$($StateName.ToLowerInvariant()).anchor" `
    "download $StateName state binding" `
    "$($DirectorySnapshot.FinalPath)|$($DirectorySnapshot.PhysicalId)`n"
}
$DownloadTempRoot = Resolve-StrictChildPath `
  $DownloadRoot "verification-temp" "download verifier temporary root"
New-Item -ItemType Directory -Path $DownloadTempRoot | Out-Null
$DownloadTempSnapshot = Get-CustodyDirectorySnapshot `
  $DownloadTempRoot "download verifier temporary root"
$DownloadTempMarker = New-CustodyMarker `
  $DownloadTempRoot ".normshift-temporary.anchor" `
  "download verifier temporary binding"
$DownloadDirectoryEnvironment = [ordered]@{
  UV_PROJECT_ENVIRONMENT = $DownloadStateDirectorySnapshots["ProjectEnvironment"]
  UV_CACHE_DIR = $DownloadStateDirectorySnapshots["UvCache"]
  HYPOTHESIS_STORAGE_DIRECTORY = $DownloadStateDirectorySnapshots["Hypothesis"]
  MYPY_CACHE_DIR = $DownloadStateDirectorySnapshots["Mypy"]
  RUFF_CACHE_DIR = $DownloadStateDirectorySnapshots["Ruff"]
  PYTHONPYCACHEPREFIX = $DownloadStateDirectorySnapshots["Python"]
  UV_PYTHON_INSTALL_DIR = $DownloadStateDirectorySnapshots["PythonInstall"]
  UV_TOOL_DIR = $DownloadStateDirectorySnapshots["UvTools"]
  UV_TOOL_BIN_DIR = $DownloadStateDirectorySnapshots["UvToolBin"]
  TMPDIR = $DownloadTempSnapshot
  TEMP = $DownloadTempSnapshot
  TMP = $DownloadTempSnapshot
}
$DownloadConsumerEnvironment = [pscustomobject]@{
  RequiredRoot = $DownloadRoot
  DirectoryVariables = $DownloadDirectoryEnvironment
  FileVariables = [ordered]@{ UV_PYTHON = $PythonExecutableSnapshot }
  LiteralVariables = [ordered]@{
    UV_PYTHON_DOWNLOADS = "never"
    PYTHONDONTWRITEBYTECODE = "1"
    PYTHONUTF8 = "1"
    PYTEST_ADDOPTS = "-p no:cacheprovider"
  }
  Markers = @($DownloadStateMarkerSnapshots.Values) + @(
    $DownloadRootMarker,
    $DownloadTempMarker
  )
  ToolTreeSnapshots = @(
    $UvToolDirectoryTreeSnapshot,
    $PythonToolDirectoryTreeSnapshot,
    $GitToolDirectoryTreeSnapshot,
    $GhToolDirectoryTreeSnapshot
  )
}
$DownloadManifestAnchor = [string] $env:NORMSHIFT_MANIFEST_SHA256
$DownloadAuditAnchor = [string] $env:NORMSHIFT_EXTERNAL_AUDIT_SHA256
if ($DownloadManifestAnchor -notmatch '^[0-9a-f]{64}$' -or
    $DownloadAuditAnchor -notmatch '^[0-9a-f]{64}$' -or
    $DownloadManifestAnchor -cne $ManifestAnchor -or
    $DownloadAuditAnchor -cne $ExternalAuditAnchor) {
  throw "download verification requires the unchanged external digest trust anchors"
}
foreach ($RequiredRoot in @($Checkout, $GateRoot, $PackageRoot)) {
  if (-not $RequiredRoot) { throw "a pre-download custody root is missing" }
  Assert-DisjointRoots $DownloadRoot $RequiredRoot "download/custody"
}

$PackageBase = "NormShift-$Version-$RunId"
$ExpectedReleaseAssetNames = [ordered]@{
  Wheel = "normshift-$Version-py3-none-any.whl"
  Sdist = "normshift-$Version.tar.gz"
  SourceZip = "$PackageBase-Source.zip"
  Bundle = "$PackageBase.bundle"
  Sbom = "normshift-$Version-sbom.cdx.json"
  Manifest = "$PackageBase-MANIFEST.json"
  Checksums = "$PackageBase-CHECKSUMS.txt"
  AuditContract = "$PackageBase-AUDIT-CONTRACT.md"
  ExternalAudit = "$PackageBase-EXTERNAL-AUDIT.json"
}
$ExpectedAssetNames = @($ExpectedReleaseAssetNames.Values)
if ($ExpectedReleaseAssetNames.Count -ne 9 -or $ExpectedAssetNames.Count -ne 9) {
  throw "download verification requires exactly nine fixed asset names"
}

$ReleaseJson = Invoke-CustodyConsumer `
  "read published release inventory" $DownloadConsumerEnvironment {
    & $GhExecutableSnapshot.Path api --method GET `
      "repos/$Repository/releases/tags/$Tag"
    Assert-NativeSuccess "read published release inventory"
  }
$ReleaseRecord = $ReleaseJson | ConvertFrom-Json -Depth 100
if ($ReleaseRecord.tag_name -cne $Tag -or $ReleaseRecord.draft -ne $false -or
    $ReleaseRecord.prerelease -ne $false -or
    $ReleaseRecord.target_commitish -ne $Candidate) {
  throw "published release identity differs from the candidate/tag"
}
$ReleaseInventory = @($ReleaseRecord.assets)
$ReleaseAssetNames = @($ReleaseInventory | ForEach-Object { [string] $_.name })
Assert-ExactNameSet -Expected $ExpectedAssetNames `
  -Observed $ReleaseAssetNames -Label "GitHub release asset inventory"

Invoke-CustodyConsumer "download GitHub release assets" $DownloadConsumerEnvironment {
  & $GhExecutableSnapshot.Path release download $Tag `
    --repo $Repository --dir $DownloadAssetRoot
  Assert-NativeSuccess "download release assets"
} | Out-Null
Assert-UnchangedDirectorySnapshot $DownloadParentSnapshot `
  "download root parent after GitHub download"
Assert-UnchangedDirectorySnapshot $DownloadRootSnapshot `
  "download root after GitHub download"
$DownloadedEntries = @(Get-ChildItem -LiteralPath $DownloadAssetRoot -Force)
if ($DownloadedEntries.Count -ne 9 -or
    @($DownloadedEntries | Where-Object { -not $_.PSIsContainer }).Count -ne 9 -or
    @($DownloadedEntries | Where-Object {
      ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
    }).Count -ne 0) {
  throw "download root must contain exactly nine top-level asset files"
}
$DownloadedNames = @($DownloadedEntries | ForEach-Object { $_.Name })
Assert-ExactNameSet -Expected $ExpectedAssetNames `
  -Observed $DownloadedNames -Label "downloaded release assets"

$DownloadedAssets = [ordered]@{}
$DownloadedAssetSnapshots = [ordered]@{}
foreach ($Role in $ExpectedReleaseAssetNames.Keys) {
  $Name = [string] $ExpectedReleaseAssetNames[$Role]
  $Path = Resolve-StrictChildPath $DownloadAssetRoot $Name "downloaded $Role"
  $DownloadedAssets[$Role] = $Path
  $DownloadedAssetSnapshots[$Role] = Get-CustodyFileSnapshot `
    $Path "downloaded release asset $Role"
}

foreach ($Asset in $ReleaseInventory) {
  $Name = [string] $Asset.name
  $Matches = @($ReleaseInventory | Where-Object { $_.name -ceq $Name })
  if ($Matches.Count -ne 1 -or $Asset.state -cne "uploaded" -or
      $Asset.digest -notmatch '^sha256:[0-9a-f]{64}$') {
    throw "release inventory entry is duplicate, incomplete, or lacks SHA-256: $Name"
  }
  $Path = Resolve-StrictChildPath $DownloadAssetRoot $Name "release inventory asset"
  $Role = @($ExpectedReleaseAssetNames.Keys | Where-Object {
    $ExpectedReleaseAssetNames[$_] -ceq $Name
  })
  if ($Role.Count -ne 1) { throw "release inventory role is ambiguous: $Name" }
  $Snapshot = $DownloadedAssetSnapshots[$Role[0]]
  if ($Snapshot.Path -cne $Path -or
      $Snapshot.Sha256 -cne $Asset.digest.Substring(7) -or
      $Snapshot.Size -ne [int64] $Asset.size) {
    throw "downloaded asset differs from the GitHub release inventory: $Name"
  }
}

$DownloadedAssetTreeSnapshot = Get-CustodyTreeSnapshot `
  $DownloadAssetRoot "downloaded release asset tree"
if ($DownloadedAssetTreeSnapshot.FileCount -ne 9 -or
    $DownloadedAssetTreeSnapshot.DirectoryCount -ne 0) {
  throw "downloaded release asset tree must contain exactly nine files"
}
$DownloadAssetConsumerRoot = Resolve-StrictChildPath `
  $DownloadRoot "release-asset-consumer-tree" `
  "controlled downloaded release asset tree"
New-Item -ItemType Directory -Path $DownloadAssetConsumerRoot | Out-Null
$DownloadedAssetTreeLease = New-CustodyTreeLease `
  $DownloadedAssetTreeSnapshot $DownloadAssetConsumerRoot `
  "controlled downloaded release asset tree"
$DownloadedConsumerAssets = [ordered]@{}
$DownloadedConsumerAssetSnapshots = [ordered]@{}
foreach ($Role in $ExpectedReleaseAssetNames.Keys) {
  $Name = [string] $ExpectedReleaseAssetNames[$Role]
  $Path = Resolve-StrictChildPath `
    $DownloadedAssetTreeLease.ConsumerRoot $Name "pinned downloaded $Role"
  $DownloadedConsumerAssets[$Role] = $Path
  $DownloadedConsumerAssetSnapshots[$Role] = Get-CustodyFileSnapshot `
    $Path "pinned downloaded release asset $Role"
  if ($DownloadedConsumerAssetSnapshots[$Role].Sha256 -cne
        $DownloadedAssetSnapshots[$Role].Sha256 -or
      $DownloadedConsumerAssetSnapshots[$Role].Size -ne
        $DownloadedAssetSnapshots[$Role].Size) {
    throw "pinned downloaded $Role differs from its release download"
  }
}

$DownloadedManifest = $DownloadedConsumerAssets["Manifest"]
$DownloadedManifestSnapshot = $DownloadedConsumerAssetSnapshots["Manifest"]
$DownloadedAuditSnapshot = $DownloadedConsumerAssetSnapshots["ExternalAudit"]
if ($DownloadedManifestSnapshot.Sha256 -cne $DownloadManifestAnchor -or
    $DownloadedAuditSnapshot.Sha256 -cne $DownloadAuditAnchor) {
  throw "downloaded manifest or detached audit differs from its external trust anchor"
}
$DownloadedManifestDocument = Get-Content -LiteralPath $DownloadedManifest `
  -Raw | ConvertFrom-Json -Depth 100
Assert-UnchangedFileSnapshot $DownloadedManifestSnapshot `
  "downloaded manifest after identity parse"
if ($DownloadedManifestDocument.package_commit -ne $Candidate -or
    $DownloadedManifestDocument.package_tree -ne $Tree -or
    $DownloadedManifestDocument.package_version -ne $Version -or
    $DownloadedManifestDocument.run_id -ne $RunId) {
  throw "downloaded manifest identity differs from the release subject"
}
$ManifestArtifactRoles = [ordered]@{
  Bundle = "bundle"
  SourceZip = "source_zip"
  Wheel = "wheel"
  Sdist = "sdist"
  Sbom = "sbom"
  Checksums = "checksums"
  AuditContract = "audit_contract"
}
foreach ($Role in $ManifestArtifactRoles.Keys) {
  $ManifestKey = $ManifestArtifactRoles[$Role]
  $Record = $DownloadedManifestDocument.artifacts.$ManifestKey
  $Snapshot = $DownloadedAssetSnapshots[$Role]
  if ($null -eq $Record -or $Record.path -cne $ExpectedReleaseAssetNames[$Role] -or
      $Record.sha256 -cne $Snapshot.Sha256 -or
      [int64] $Record.size -ne $Snapshot.Size) {
    throw "downloaded $Role differs from the authoritative manifest inventory"
  }
}

$DownloadAuditClone = Resolve-StrictChildPath `
  $DownloadRoot "bundle-clone" "download bundle clone"
Assert-UnchangedFileSnapshot $DownloadedAssetSnapshots["Bundle"] `
  "downloaded bundle before clone"
Invoke-CustodyConsumer "clone downloaded bundle" $DownloadConsumerEnvironment {
  & $GitExecutableSnapshot.Path clone --no-hardlinks `
    $DownloadedConsumerAssets["Bundle"] `
    $DownloadAuditClone
  Assert-NativeSuccess "clone downloaded bundle"
} -TreeLeases @($DownloadedAssetTreeLease) | Out-Null
Assert-UnchangedFileSnapshot $DownloadedAssetSnapshots["Bundle"] `
  "downloaded bundle after clone"
Assert-UnchangedDirectorySnapshot $DownloadRootSnapshot `
  "download root after bundle clone"
Assert-UnchangedFileSnapshot $DownloadRootMarker `
  "download root binding after bundle clone"
$DownloadCloneSnapshot = Get-CustodyDirectorySnapshot `
  $DownloadAuditClone "download bundle clone"
$DownloadCloneTreeSnapshot = Get-CustodyTreeSnapshot `
  $DownloadAuditClone "download bundle clone tree"
$DownloadCloneConsumerRoot = Assert-DescendantPath $DownloadRoot `
  (Join-Path $DownloadRoot "bundle-clone-consumer-tree") `
  "controlled download bundle clone"
New-Item -ItemType Directory -Path $DownloadCloneConsumerRoot | Out-Null
$DownloadCloneTreeLease = New-CustodyTreeLease `
  $DownloadCloneTreeSnapshot $DownloadCloneConsumerRoot `
  "controlled download bundle clone"
$DownloadCloneHeadPath = Assert-DescendantPath $DownloadRoot `
  (Join-Path $DownloadCloneTreeLease.ConsumerRoot ".git/HEAD") `
  "download clone HEAD"
$DownloadCloneHeadSnapshot = Get-CustodyFileSnapshot `
  $DownloadCloneHeadPath "download clone HEAD"
Invoke-CustodyConsumer "fsck downloaded bundle" $DownloadConsumerEnvironment {
  & $GitExecutableSnapshot.Path -C `
    $DownloadCloneTreeLease.ConsumerRoot fsck --full --strict
  Assert-NativeSuccess "fsck downloaded bundle"
} -TreeLeases @($DownloadCloneTreeLease) | Out-Null
Assert-UnchangedDirectorySnapshot $DownloadCloneSnapshot `
  "download clone after fsck"
Assert-UnchangedTreeSnapshot $DownloadCloneTreeSnapshot `
  "download clone tree after fsck"
Assert-UnchangedFileSnapshot $DownloadCloneHeadSnapshot `
  "download clone HEAD after fsck"
$DownloadCloneHead = (& $GitExecutableSnapshot.Path `
  -C $DownloadCloneTreeLease.ConsumerRoot `
  rev-parse HEAD).Trim()
Assert-NativeSuccess "resolve downloaded clone HEAD"
$DownloadCloneTree = (& $GitExecutableSnapshot.Path `
  -C $DownloadCloneTreeLease.ConsumerRoot `
  show -s --format=%T HEAD).Trim()
Assert-NativeSuccess "resolve downloaded clone tree"
if ($DownloadCloneHead -ne $Candidate -or $DownloadCloneTree -ne $Tree) {
  throw "downloaded bundle clone differs from the release subject"
}
$DownloadVerifier = Assert-DescendantPath $DownloadRoot `
  (Join-Path $DownloadCloneTreeLease.ConsumerRoot `
    "scripts/external_package_verify.py") `
  "downloaded external verifier"
$DownloadVerifierSnapshot = Get-CustodyFileSnapshot `
  $DownloadVerifier "downloaded external verifier"
$DownloadAuditVerifier = Assert-DescendantPath $DownloadRoot `
  (Join-Path $DownloadCloneTreeLease.ConsumerRoot `
    "scripts/verify_external_audit.py") `
  "downloaded audit trust-anchor verifier"
$DownloadAuditSchema = Assert-DescendantPath $DownloadRoot `
  (Join-Path $DownloadCloneTreeLease.ConsumerRoot `
    "schemas/external_audit_v1.schema.json") `
  "downloaded external audit schema"
$DownloadAuditVerifierSnapshot = Get-CustodyFileSnapshot `
  $DownloadAuditVerifier "downloaded audit trust-anchor verifier"
$DownloadAuditSchemaSnapshot = Get-CustodyFileSnapshot `
  $DownloadAuditSchema "downloaded external audit schema"
$DownloadWorkRoot = Resolve-StrictChildPath `
  $DownloadRoot "verification-work" "download verification work"
New-Item -ItemType Directory -Path $DownloadWorkRoot | Out-Null
$DownloadWorkSnapshot = Get-CustodyDirectorySnapshot `
  $DownloadWorkRoot "download verification work"
$DownloadWorkMarker = New-CustodyMarker `
  $DownloadWorkRoot ".normshift-work.anchor" "download verification work binding"
foreach ($Role in $DownloadedAssetSnapshots.Keys) {
  Assert-UnchangedFileSnapshot $DownloadedAssetSnapshots[$Role] `
    "downloaded $Role before package verifier"
}
Assert-UnchangedDirectorySnapshot $DownloadTempSnapshot `
  "download TMPDIR before package verifier"
Assert-UnchangedFileSnapshot $DownloadTempMarker `
  "download TMPDIR binding before package verifier"
foreach ($StateName in $DownloadStatePaths.Keys) {
  Assert-UnchangedDirectorySnapshot $DownloadStateDirectorySnapshots[$StateName] `
    "download $StateName state before package verifier"
  Assert-UnchangedFileSnapshot $DownloadStateMarkerSnapshots[$StateName] `
    "download $StateName binding before package verifier"
}
Invoke-CustodyConsumer "downloaded package preflight" `
  $DownloadConsumerEnvironment {
  Push-Location $DownloadWorkRoot
  try {
    & $UvExecutableSnapshot.Path run `
      --project $DownloadCloneTreeLease.ConsumerRoot --frozen python `
      $DownloadVerifier `
      --repo $DownloadCloneTreeLease.ConsumerRoot `
      --manifest $DownloadedConsumerAssets["Manifest"] `
      --bundle $DownloadedConsumerAssets["Bundle"] `
      --source-zip $DownloadedConsumerAssets["SourceZip"]
    Assert-NativeSuccess "downloaded package preflight"
  } finally {
    Pop-Location
  }
} -TreeLeases @($DownloadCloneTreeLease, $DownloadedAssetTreeLease) | Out-Null
foreach ($Role in $DownloadedAssetSnapshots.Keys) {
  Assert-UnchangedFileSnapshot $DownloadedAssetSnapshots[$Role] `
    "downloaded $Role after package verifier"
}
Assert-UnchangedFileSnapshot $DownloadVerifierSnapshot `
  "downloaded external verifier after use"
Assert-UnchangedDirectorySnapshot $DownloadCloneSnapshot `
  "download clone after package verifier"
Assert-UnchangedTreeSnapshot $DownloadCloneTreeSnapshot `
  "download clone tree after package verifier"
Assert-UnchangedFileSnapshot $DownloadCloneHeadSnapshot `
  "download clone HEAD after package verifier"
Assert-UnchangedDirectorySnapshot $DownloadWorkSnapshot `
  "download verification work after package verifier"
Assert-UnchangedFileSnapshot $DownloadWorkMarker `
  "download verification work binding after package verifier"
Assert-UnchangedDirectorySnapshot $DownloadTempSnapshot `
  "download TMPDIR after package verifier"
Assert-UnchangedFileSnapshot $DownloadTempMarker `
  "download TMPDIR binding after package verifier"
foreach ($StateName in $DownloadStatePaths.Keys) {
  Assert-UnchangedDirectorySnapshot $DownloadStateDirectorySnapshots[$StateName] `
    "download $StateName state after package verifier"
  Assert-UnchangedFileSnapshot $DownloadStateMarkerSnapshots[$StateName] `
    "download $StateName binding after package verifier"
}

$DownloadedAuditVerificationJson = (Invoke-CustodyConsumer `
  "reverify downloaded detached audit trust anchors" `
  $DownloadConsumerEnvironment {
    (& $UvExecutableSnapshot.Path run `
      --project $DownloadCloneTreeLease.ConsumerRoot --frozen python `
      $DownloadAuditVerifier `
      --manifest $DownloadedManifestSnapshot.Path `
      --audit $DownloadedAuditSnapshot.Path `
      --schema $DownloadAuditSchemaSnapshot.Path `
      --manifest-sha256 $DownloadManifestAnchor `
      --audit-sha256 $DownloadAuditAnchor `
      --roots-inventory-sha256 $AuthorityEvidence.RootsInventorySha256 `
      --approved-volume-binding-sha256 `
        $AuthorityEvidence.ApprovedVolumeBindingSha256 `
      --commit $Candidate --tree $Tree --version $Version --run-id $RunId |
      Out-String).Trim()
    Assert-NativeSuccess "reverify downloaded detached audit trust anchors"
  } -TreeLeases @(
    $DownloadCloneTreeLease,
    $DownloadedAssetTreeLease
  )).Trim()
$DownloadedAuditVerification = $DownloadedAuditVerificationJson | `
  ConvertFrom-Json -Depth 20
if ($DownloadedAuditVerification.ok -ne $true -or
    $DownloadedAuditVerification.p0 -ne 0 -or
    $DownloadedAuditVerification.p1 -ne 0 -or
    $DownloadedAuditVerification.verdict -cne
      "M0_M1_M2_COMBINED_EXTERNAL_AUDIT_PASS") {
  throw "downloaded detached audit does not authorize the combined release"
}
Assert-UnchangedFileSnapshot $DownloadedManifestSnapshot `
  "downloaded manifest after audit trust verification"
Assert-UnchangedFileSnapshot $DownloadedAuditSnapshot `
  "downloaded audit after trust verification"
Assert-UnchangedFileSnapshot $DownloadAuditVerifierSnapshot `
  "downloaded audit verifier after use"
Assert-UnchangedFileSnapshot $DownloadAuditSchemaSnapshot `
  "downloaded audit schema after use"
Assert-UnchangedDirectorySnapshot $DownloadTempSnapshot `
  "download TMPDIR after audit verification"
Assert-UnchangedFileSnapshot $DownloadTempMarker `
  "download TMPDIR binding after audit verification"

& $GitExecutableSnapshot.Path fetch --force `
  origin master:refs/remotes/origin/master
Assert-NativeSuccess "refresh origin master for final release verification"
$FinalFetchedDefault = (& $GitExecutableSnapshot.Path `
  rev-parse refs/remotes/origin/master).Trim()
Assert-NativeSuccess "resolve final fetched origin master"
$FinalRemoteDefault = Get-RemoteMasterSha
$RemoteTagRows = @(& $GitExecutableSnapshot.Path `
  ls-remote --tags origin "refs/tags/$Tag^{}")
Assert-NativeSuccess "resolve remote peeled tag"
if ($RemoteTagRows.Count -ne 1) { throw "annotated tag must peel exactly once" }
$RemoteTagFields = @($RemoteTagRows[0] -split "`t")
if ($RemoteTagFields.Count -ne 2 -or
    $RemoteTagFields[0] -notmatch '^[0-9a-f]{40}$' -or
    $RemoteTagFields[1] -cne "refs/tags/$Tag^{}") {
  throw "remote peeled tag response is not canonical"
}
$RemoteTag = $RemoteTagFields[0]
$ReleaseSha = [string] $ReleaseRecord.target_commitish
Assert-ExactReleaseSubject $Candidate $ReleaseSha $RemoteTag `
  $FinalFetchedDefault $FinalRemoteDefault
foreach ($Role in $DownloadedAssetSnapshots.Keys) {
  Assert-UnchangedFileSnapshot $DownloadedAssetSnapshots[$Role] `
    "downloaded $Role at final subject check"
}
Assert-UnchangedDirectorySnapshot $DownloadParentSnapshot `
  "download parent at final subject check"
Assert-UnchangedDirectorySnapshot $DownloadRootSnapshot `
  "download root at final subject check"
Assert-UnchangedFileSnapshot $DownloadRootMarker `
  "download root binding at final subject check"
Assert-UnchangedDirectorySnapshot $DownloadCloneSnapshot `
  "download clone at final subject check"
Assert-UnchangedTreeSnapshot $DownloadCloneTreeSnapshot `
  "download clone tree at final subject check"
Assert-UnchangedFileSnapshot $DownloadVerifierSnapshot `
  "download package verifier at final subject check"
Assert-UnchangedFileSnapshot $DownloadAuditVerifierSnapshot `
  "download audit verifier at final subject check"
Assert-UnchangedFileSnapshot $DownloadAuditSchemaSnapshot `
  "download audit schema at final subject check"
Assert-UnchangedDirectorySnapshot $DownloadTempSnapshot `
  "download TMPDIR at final subject check"
Assert-UnchangedFileSnapshot $DownloadTempMarker `
  "download TMPDIR binding at final subject check"
foreach ($StateName in $DownloadStatePaths.Keys) {
  Assert-UnchangedDirectorySnapshot $DownloadStateDirectorySnapshots[$StateName] `
    "download $StateName state at final subject check"
  Assert-UnchangedFileSnapshot $DownloadStateMarkerSnapshots[$StateName] `
    "download $StateName binding at final subject check"
}
Close-CustodyTreeLease $DownloadCloneTreeLease `
  "controlled downloaded bundle clone at final subject check"
Close-CustodyTreeLease $DownloadedAssetTreeLease `
  "controlled downloaded release assets at final subject check"
Close-CustodyTreeLease $CandidateTreeLease `
  "controlled candidate tree at final subject check"
foreach ($Name in $SessionEnvironmentNames) {
  [Environment]::SetEnvironmentVariable(
    $Name, $OriginalSessionEnvironment[$Name], 'Process')
}
```

## 10. Genuinely complete handoff

- [ ] Every box above and every Section 11 definition-of-done item is true for the
      same final release subject; none depends on a different commit, local-only
      artifact, expired unavailable record, or historical M0-only verdict.
- [ ] The final handoff records the completion score, M0/M1/M2/delivery breakdown,
      merged SHA/tree, exact CI URL/jobs, test counts, per-class/support metrics,
      source/label/graph evidence hashes, package/manifest/SBOM hashes, detached
      audit URL/hash/verdict, annotated tag, release URL/assets, download reverify
      results, and honest residual limitations.
- [ ] `MISSION_STATE.json` was finalized before candidate freeze and accurately
      records its pre-audit cap plus the detached post-freeze authority rule. No
      post-audit tracked status edit was made; the detached audit, annotated tag,
      release record, and download evidence carry the later subject-bound verdict.

Until then, report the actual incomplete state and next executable gate. Code
complete, CI green, package preflight, external audit, and release publication are
separate gates; none alone means 100%.
