"""Canonicalize platform-only ZIP metadata in a built wheel.

Wheel payloads built from the same source can differ across operating systems
only because Python records its host system in each central-directory
``version made by`` field.  This module parses the ZIP structures strictly and
sets that host byte to the canonical UNIX value without recompressing or
rewriting any member data.
"""

from __future__ import annotations

import hashlib
import io
import os
import stat
import struct
import unicodedata
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

from normshift.io_safety import PathSafetyError, assert_outputs_safe

MAX_WHEEL_BYTES: Final = 64 * 1024 * 1024
MAX_WHEEL_MEMBERS: Final = 4096
MAX_WHEEL_MEMBER_UNCOMPRESSED_BYTES: Final = 16 * 1024 * 1024
MAX_WHEEL_TOTAL_UNCOMPRESSED_BYTES: Final = 64 * 1024 * 1024
MAX_WHEEL_COMPRESSION_RATIO: Final = 1000
CANONICAL_HOST_SYSTEM: Final = 3

_EOCD_SIGNATURE: Final = b"PK\x05\x06"
_CENTRAL_SIGNATURE: Final = b"PK\x01\x02"
_LOCAL_SIGNATURE: Final = b"PK\x03\x04"
_EOCD_FIXED_SIZE: Final = 22
_CENTRAL_FIXED_SIZE: Final = 46
_LOCAL_FIXED_SIZE: Final = 30
_MAX_ZIP_COMMENT: Final = 65_535
_ZIP64_U16: Final = 0xFFFF
_ZIP64_U32: Final = 0xFFFFFFFF
_WINDOWS_FORBIDDEN: Final = frozenset('<>:"|?*')
_WINDOWS_RESERVED: Final = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CLOCK$"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)


class WheelNormalizationError(ValueError):
    """The wheel is unsafe, malformed, unsupported, or not canonicalizable."""


@dataclass(frozen=True)
class WheelNormalizationResult:
    """Summary of one source-to-new-output wheel canonicalization."""

    member_count: int
    fields_changed: int
    input_sha256: str
    output_sha256: str

    @property
    def changed(self) -> bool:
        return self.fields_changed > 0


@dataclass(frozen=True)
class _CentralEntry:
    central_offset: int
    local_offset: int
    version_needed: int
    flags: int
    compression: int
    modified_time: int
    modified_date: int
    crc32: int
    compressed_size: int
    uncompressed_size: int
    name_bytes: bytes
    name: str


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


_FileIdentity = tuple[int, int, int, int, int]


def _file_identity(info: os.stat_result) -> _FileIdentity:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_nlink,
    )


def _read_regular_file(path: Path) -> tuple[bytes, _FileIdentity]:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise WheelNormalizationError("wheel must be a regular non-symlink file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise WheelNormalizationError(f"cannot open wheel: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise WheelNormalizationError("wheel must be a singly linked regular file")
        if before.st_size > MAX_WHEEL_BYTES:
            raise WheelNormalizationError(f"wheel exceeds {MAX_WHEEL_BYTES} bytes")
        chunks: list[bytes] = []
        remaining = MAX_WHEEL_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise WheelNormalizationError(f"cannot read wheel: {exc}") from exc
    finally:
        os.close(descriptor)
    if len(raw) > MAX_WHEEL_BYTES:
        raise WheelNormalizationError(f"wheel exceeds {MAX_WHEEL_BYTES} bytes")
    identity_before = _file_identity(before)
    identity_after = _file_identity(after)
    if identity_before != identity_after or len(raw) != after.st_size:
        raise WheelNormalizationError("wheel changed while being read")
    try:
        path_after = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise WheelNormalizationError(f"cannot restat wheel: {exc}") from exc
    path_identity = _file_identity(path_after)
    if (
        not stat.S_ISREG(path_after.st_mode)
        or candidate.is_symlink()
        or path_identity != identity_after
    ):
        raise WheelNormalizationError("wheel path identity changed while being read")
    return raw, identity_after


def _path_has_identity(path: Path, expected: _FileIdentity) -> bool:
    candidate = Path(path)
    try:
        current = candidate.stat(follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(current.st_mode)
        and not candidate.is_symlink()
        and _file_identity(current) == expected
    )


def _write_new_regular_file(path: Path, data: bytes) -> _FileIdentity:
    candidate = Path(path)
    if os.path.lexists(candidate):
        raise WheelNormalizationError("canonical wheel output already exists")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(candidate, flags, 0o644)
    except OSError as exc:
        raise WheelNormalizationError(f"cannot exclusively create canonical wheel: {exc}") from exc
    try:
        view = memoryview(data)
        written = 0
        while written < len(view):
            count = os.write(descriptor, view[written:])
            if count <= 0:
                raise WheelNormalizationError("canonical wheel write made no progress")
            written += count
        os.fsync(descriptor)
        final = os.fstat(descriptor)
        if (
            not stat.S_ISREG(final.st_mode)
            or final.st_nlink != 1
            or final.st_size != len(data)
        ):
            raise WheelNormalizationError("canonical wheel output identity is invalid")
        identity = _file_identity(final)
    except OSError as exc:
        raise WheelNormalizationError(f"cannot write canonical wheel: {exc}") from exc
    finally:
        os.close(descriptor)
    if not _path_has_identity(candidate, identity):
        raise WheelNormalizationError("canonical wheel output path changed during write")
    return identity


def _find_eocd(raw: bytes) -> int:
    if len(raw) < _EOCD_FIXED_SIZE:
        raise WheelNormalizationError("wheel is shorter than a ZIP end record")
    start = max(0, len(raw) - _EOCD_FIXED_SIZE - _MAX_ZIP_COMMENT)
    candidates: list[int] = []
    cursor = start
    while True:
        offset = raw.find(_EOCD_SIGNATURE, cursor)
        if offset < 0:
            break
        if offset + _EOCD_FIXED_SIZE <= len(raw):
            comment_size = struct.unpack_from("<H", raw, offset + 20)[0]
            if offset + _EOCD_FIXED_SIZE + comment_size == len(raw):
                candidates.append(offset)
        cursor = offset + 1
    if len(candidates) != 1:
        raise WheelNormalizationError(
            f"wheel must contain one unambiguous ZIP end record; found {len(candidates)}"
        )
    return candidates[0]


def _decode_member_name(raw_name: bytes, flags: int) -> str:
    encoding = "utf-8" if flags & 0x800 else "cp437"
    try:
        name = raw_name.decode(encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise WheelNormalizationError("wheel member name has invalid encoding") from exc
    if not name or "\x00" in name or "\\" in name:
        raise WheelNormalizationError(f"unsafe wheel member name: {name!r}")
    if unicodedata.normalize("NFC", name) != name:
        raise WheelNormalizationError(f"wheel member name is not NFC: {name!r}")
    if name.startswith("/") or (len(name) >= 2 and name[1] == ":"):
        raise WheelNormalizationError(f"absolute wheel member name: {name!r}")
    path_name = name[:-1] if name.endswith("/") else name
    segments = path_name.split("/")
    if not path_name or any(segment in {"", ".", ".."} for segment in segments):
        raise WheelNormalizationError(f"non-canonical wheel member name: {name!r}")
    if PurePosixPath(path_name).as_posix() != path_name:
        raise WheelNormalizationError(f"non-canonical wheel member name: {name!r}")
    if any(ord(character) < 32 or ord(character) == 127 for character in name):
        raise WheelNormalizationError(f"control character in wheel member name: {name!r}")
    if len(name.encode("utf-8")) > 1024:
        raise WheelNormalizationError(f"wheel member name exceeds the byte bound: {name!r}")
    for segment in segments:
        if (
            len(segment.encode("utf-8")) > 240
            or segment.endswith((" ", "."))
            or any(character in _WINDOWS_FORBIDDEN for character in segment)
            or segment.split(".", maxsplit=1)[0].upper() in _WINDOWS_RESERVED
        ):
            raise WheelNormalizationError(f"non-portable wheel member name: {name!r}")
    return name


def _parse_entries(raw: bytes, eocd_offset: int) -> list[_CentralEntry]:
    (
        disk_number,
        central_disk,
        entries_on_disk,
        entries_total,
        central_size,
        central_offset,
        comment_size,
    ) = struct.unpack_from("<4H2IH", raw, eocd_offset + 4)
    if disk_number != 0 or central_disk != 0 or entries_on_disk != entries_total:
        raise WheelNormalizationError("multi-disk ZIP wheels are unsupported")
    if (
        entries_total == _ZIP64_U16
        or central_size == _ZIP64_U32
        or central_offset == _ZIP64_U32
    ):
        raise WheelNormalizationError("ZIP64 wheels are unsupported")
    if entries_total == 0 or entries_total > MAX_WHEEL_MEMBERS:
        raise WheelNormalizationError("wheel member count is empty or exceeds the bound")
    if comment_size != 0:
        raise WheelNormalizationError("wheel archive comments are unsupported")
    if central_offset + central_size != eocd_offset:
        raise WheelNormalizationError("central directory boundaries do not match the ZIP end")

    entries: list[_CentralEntry] = []
    names: set[str] = set()
    paths: dict[str, bool] = {}
    local_offsets: set[int] = set()
    total_uncompressed = 0
    cursor = central_offset
    central_end = central_offset + central_size
    for _index in range(entries_total):
        if cursor + _CENTRAL_FIXED_SIZE > central_end:
            raise WheelNormalizationError("truncated central directory header")
        if raw[cursor : cursor + 4] != _CENTRAL_SIGNATURE:
            raise WheelNormalizationError("invalid central directory signature")
        version_needed = struct.unpack_from("<H", raw, cursor + 6)[0]
        flags = struct.unpack_from("<H", raw, cursor + 8)[0]
        compression = struct.unpack_from("<H", raw, cursor + 10)[0]
        modified_time, modified_date = struct.unpack_from("<2H", raw, cursor + 12)
        crc32 = struct.unpack_from("<I", raw, cursor + 16)[0]
        compressed_size = struct.unpack_from("<I", raw, cursor + 20)[0]
        uncompressed_size = struct.unpack_from("<I", raw, cursor + 24)[0]
        name_size, extra_size, comment_size = struct.unpack_from("<3H", raw, cursor + 28)
        disk_start = struct.unpack_from("<H", raw, cursor + 34)[0]
        external_attributes = struct.unpack_from("<I", raw, cursor + 38)[0]
        local_offset = struct.unpack_from("<I", raw, cursor + 42)[0]
        if (
            compressed_size == _ZIP64_U32
            or uncompressed_size == _ZIP64_U32
            or local_offset == _ZIP64_U32
            or disk_start == _ZIP64_U16
        ):
            raise WheelNormalizationError("ZIP64 wheel entry is unsupported")
        if disk_start != 0:
            raise WheelNormalizationError("wheel entry starts on a different disk")
        if flags & ~0x800:
            raise WheelNormalizationError("wheel entry uses unsupported general-purpose flags")
        if compression not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise WheelNormalizationError("wheel entry uses unsupported compression")
        if uncompressed_size > MAX_WHEEL_MEMBER_UNCOMPRESSED_BYTES:
            raise WheelNormalizationError("wheel member exceeds the uncompressed-size bound")
        total_uncompressed += uncompressed_size
        if total_uncompressed > MAX_WHEEL_TOTAL_UNCOMPRESSED_BYTES:
            raise WheelNormalizationError("wheel exceeds the total uncompressed-size bound")
        if compression == zipfile.ZIP_STORED and compressed_size != uncompressed_size:
            raise WheelNormalizationError("stored wheel member has inconsistent sizes")
        if uncompressed_size > 0 and (
            compressed_size == 0
            or uncompressed_size > compressed_size * MAX_WHEEL_COMPRESSION_RATIO
        ):
            raise WheelNormalizationError("wheel member exceeds the compression-ratio bound")
        if extra_size != 0 or comment_size != 0:
            raise WheelNormalizationError("wheel member extras/comments are unsupported")
        posix_kind = stat.S_IFMT(external_attributes >> 16)
        if posix_kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
            raise WheelNormalizationError("wheel contains a link or special member")
        record_end = cursor + _CENTRAL_FIXED_SIZE + name_size + extra_size + comment_size
        if name_size == 0 or record_end > central_end:
            raise WheelNormalizationError("truncated or nameless central directory entry")
        name_bytes = raw[cursor + _CENTRAL_FIXED_SIZE : cursor + _CENTRAL_FIXED_SIZE + name_size]
        name = _decode_member_name(name_bytes, flags)
        is_directory = name.endswith("/")
        if (posix_kind == stat.S_IFDIR) != is_directory and posix_kind != 0:
            raise WheelNormalizationError(f"wheel member type/name mismatch: {name!r}")
        path_name = name[:-1] if is_directory else name
        alias = unicodedata.normalize("NFKC", path_name).casefold()
        parent_aliases = [
            "/".join(alias.split("/")[:index])
            for index in range(1, len(alias.split("/")))
        ]
        if name in names or alias in paths:
            raise WheelNormalizationError(f"duplicate or aliased wheel member: {name!r}")
        if any(parent in paths and not paths[parent] for parent in parent_aliases):
            raise WheelNormalizationError(f"wheel member descends from a file: {name!r}")
        if not is_directory and any(existing.startswith(f"{alias}/") for existing in paths):
            raise WheelNormalizationError(f"wheel file aliases an existing directory: {name!r}")
        if local_offset in local_offsets:
            raise WheelNormalizationError("multiple wheel members share a local header")
        names.add(name)
        paths[alias] = is_directory
        local_offsets.add(local_offset)
        entries.append(
            _CentralEntry(
                central_offset=cursor,
                local_offset=local_offset,
                version_needed=version_needed,
                flags=flags,
                compression=compression,
                modified_time=modified_time,
                modified_date=modified_date,
                crc32=crc32,
                compressed_size=compressed_size,
                uncompressed_size=uncompressed_size,
                name_bytes=name_bytes,
                name=name,
            )
        )
        cursor = record_end
    if cursor != central_end:
        raise WheelNormalizationError("central directory size/count mismatch")
    return entries


def _validate_local_headers(raw: bytes, entries: list[_CentralEntry], central_offset: int) -> None:
    intervals: list[tuple[int, int, str]] = []
    for entry in entries:
        offset = entry.local_offset
        if offset + _LOCAL_FIXED_SIZE > central_offset:
            raise WheelNormalizationError(f"truncated local header for {entry.name!r}")
        if raw[offset : offset + 4] != _LOCAL_SIGNATURE:
            raise WheelNormalizationError(f"invalid local header for {entry.name!r}")
        version_needed = struct.unpack_from("<H", raw, offset + 4)[0]
        flags, compression = struct.unpack_from("<2H", raw, offset + 6)
        modified_time, modified_date = struct.unpack_from("<2H", raw, offset + 10)
        crc32, compressed_size, uncompressed_size = struct.unpack_from(
            "<3I", raw, offset + 14
        )
        if (
            version_needed != entry.version_needed
            or flags != entry.flags
            or compression != entry.compression
            or modified_time != entry.modified_time
            or modified_date != entry.modified_date
        ):
            raise WheelNormalizationError(f"local/central metadata mismatch: {entry.name!r}")
        if (
            crc32 != entry.crc32
            or compressed_size != entry.compressed_size
            or uncompressed_size != entry.uncompressed_size
        ):
            raise WheelNormalizationError(f"local/central size or CRC mismatch: {entry.name!r}")
        name_size, extra_size = struct.unpack_from("<2H", raw, offset + 26)
        if extra_size != 0:
            raise WheelNormalizationError(f"local wheel extras are unsupported: {entry.name!r}")
        local_name_start = offset + _LOCAL_FIXED_SIZE
        local_name_end = local_name_start + name_size
        data_start = local_name_end + extra_size
        data_end = data_start + entry.compressed_size
        if data_end > central_offset:
            raise WheelNormalizationError(f"member data exceeds central directory: {entry.name!r}")
        if raw[local_name_start:local_name_end] != entry.name_bytes:
            raise WheelNormalizationError(f"local/central member name mismatch: {entry.name!r}")
        intervals.append((offset, data_end, entry.name))
    intervals.sort()
    if intervals[0][0] != 0:
        raise WheelNormalizationError("wheel has an unexpected prefix before its first member")
    for previous, following in zip(intervals, intervals[1:], strict=False):
        if previous[1] != following[0]:
            raise WheelNormalizationError(
                f"wheel member layout has a gap or overlap: {previous[2]!r} and {following[2]!r}"
            )
    if intervals[-1][1] != central_offset:
        raise WheelNormalizationError("wheel has unreferenced bytes before its central directory")


def _validate_zip_payload(raw: bytes, entries: list[_CentralEntry]) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(raw), mode="r") as archive:
            infos = archive.infolist()
            if len(infos) != len(entries):
                raise WheelNormalizationError("ZIP reader member count differs from central data")
            if [info.orig_filename for info in infos] != [entry.name for entry in entries]:
                raise WheelNormalizationError("ZIP reader names differ from raw central names")
            corrupt = archive.testzip()
            if corrupt is not None:
                raise WheelNormalizationError(f"wheel member CRC failed: {corrupt!r}")
    except (EOFError, NotImplementedError, RuntimeError, zipfile.BadZipFile, zlib.error) as exc:
        raise WheelNormalizationError(f"invalid wheel ZIP payload: {exc}") from exc


def normalize_wheel_bytes(raw: bytes) -> tuple[bytes, WheelNormalizationResult]:
    """Return a canonical wheel without changing member payloads or layout."""
    if len(raw) > MAX_WHEEL_BYTES:
        raise WheelNormalizationError(f"wheel exceeds {MAX_WHEEL_BYTES} bytes")
    eocd_offset = _find_eocd(raw)
    entries = _parse_entries(raw, eocd_offset)
    central_offset = struct.unpack_from("<I", raw, eocd_offset + 16)[0]
    _validate_local_headers(raw, entries, central_offset)
    _validate_zip_payload(raw, entries)

    normalized = bytearray(raw)
    changed = 0
    for entry in entries:
        host_offset = entry.central_offset + 5
        if normalized[host_offset] != CANONICAL_HOST_SYSTEM:
            normalized[host_offset] = CANONICAL_HOST_SYSTEM
            changed += 1
    output = bytes(normalized)
    _validate_zip_payload(output, entries)
    return output, WheelNormalizationResult(
        member_count=len(entries),
        fields_changed=changed,
        input_sha256=_sha256(raw),
        output_sha256=_sha256(output),
    )


def normalize_wheel_file(source: Path, output: Path) -> WheelNormalizationResult:
    """Write canonical bytes to one new output without replacing any existing path."""
    source_path = Path(source)
    output_path = Path(output)
    try:
        assert_outputs_safe(inputs=[source_path], outputs=[output_path])
    except PathSafetyError as exc:
        raise WheelNormalizationError(f"unsafe wheel input/output paths: {exc}") from exc
    if os.path.lexists(output_path):
        raise WheelNormalizationError("canonical wheel output already exists")
    raw, source_identity = _read_regular_file(source_path)
    normalized, result = normalize_wheel_bytes(raw)
    output_identity = _write_new_regular_file(output_path, normalized)
    output_raw, verified_output_identity = _read_regular_file(output_path)
    if output_raw != normalized or output_identity != verified_output_identity:
        raise WheelNormalizationError("canonical wheel differs after exclusive write")
    if not _path_has_identity(source_path, source_identity):
        raise WheelNormalizationError("source wheel path changed during normalization")
    return result


def assert_canonical_wheel_file(path: Path) -> WheelNormalizationResult:
    """Validate one wheel and reject non-canonical host-system metadata."""
    raw, _identity = _read_regular_file(Path(path))
    _normalized, result = normalize_wheel_bytes(raw)
    if result.changed:
        raise WheelNormalizationError(
            f"wheel has {result.fields_changed} non-canonical host-system fields"
        )
    return result
