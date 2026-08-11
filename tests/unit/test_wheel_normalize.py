from __future__ import annotations

import io
import stat
import struct
import zipfile
from pathlib import Path

import pytest

from normshift.audit import wheel_normalize
from normshift.audit.wheel_normalize import (
    WheelNormalizationError,
    assert_canonical_wheel_file,
    normalize_wheel_bytes,
    normalize_wheel_file,
)


def _wheel_bytes(*, host_system: int = 0, duplicate: bool = False) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_STORED) as archive:
        first = zipfile.ZipInfo("normshift/payload.bin")
        first.create_system = host_system
        archive.writestr(first, b"payload-PK\x01\x02-\x00\x00\x00\x00\x00\x00")
        metadata = zipfile.ZipInfo("normshift-1.0.dist-info/METADATA")
        metadata.create_system = host_system
        archive.writestr(metadata, b"Name: normshift\nVersion: 1.0\n")
        if duplicate:
            repeated = zipfile.ZipInfo("normshift/payload.bin")
            repeated.create_system = host_system
            archive.writestr(repeated, b"duplicate")
    return output.getvalue()


def _eocd_offset(raw: bytes) -> int:
    return raw.rindex(b"PK\x05\x06")


def _central_offsets(raw: bytes) -> list[int]:
    end = _eocd_offset(raw)
    count = struct.unpack_from("<H", raw, end + 10)[0]
    cursor = struct.unpack_from("<I", raw, end + 16)[0]
    offsets: list[int] = []
    for _index in range(count):
        offsets.append(cursor)
        name_size, extra_size, comment_size = struct.unpack_from("<3H", raw, cursor + 28)
        cursor += 46 + name_size + extra_size + comment_size
    return offsets


def test_normalizer_changes_only_central_host_bytes_and_is_idempotent() -> None:
    raw = _wheel_bytes(host_system=0)

    normalized, first = normalize_wheel_bytes(raw)
    repeated, second = normalize_wheel_bytes(normalized)

    offsets = _central_offsets(raw)
    changed_offsets = [
        index
        for index, (left, right) in enumerate(zip(raw, normalized, strict=True))
        if left != right
    ]
    assert changed_offsets == [offset + 5 for offset in offsets]
    assert first.member_count == 2
    assert first.fields_changed == 2
    assert first.changed is True
    assert second.fields_changed == 0
    assert repeated == normalized
    with zipfile.ZipFile(io.BytesIO(normalized)) as archive:
        assert archive.read("normshift/payload.bin") == (
            b"payload-PK\x01\x02-\x00\x00\x00\x00\x00\x00"
        )


def test_file_normalizer_writes_new_output_and_check_accepts(tmp_path: Path) -> None:
    raw_wheel = tmp_path / "raw.whl"
    canonical_wheel = tmp_path / "normshift-1.0-py3-none-any.whl"
    raw = _wheel_bytes(host_system=0)
    raw_wheel.write_bytes(raw)

    result = normalize_wheel_file(raw_wheel, canonical_wheel)
    checked = assert_canonical_wheel_file(canonical_wheel)

    assert result.changed is True
    assert checked.changed is False
    assert checked.output_sha256 == result.output_sha256
    assert raw_wheel.read_bytes() == raw


def test_file_normalizer_never_replaces_existing_output(tmp_path: Path) -> None:
    raw_wheel = tmp_path / "raw.whl"
    canonical_wheel = tmp_path / "canonical.whl"
    raw_wheel.write_bytes(_wheel_bytes())
    canonical_wheel.write_bytes(b"concurrent replacement")

    with pytest.raises(WheelNormalizationError, match="already exists|unsafe"):
        normalize_wheel_file(raw_wheel, canonical_wheel)

    assert canonical_wheel.read_bytes() == b"concurrent replacement"


def test_file_normalizer_detects_output_created_after_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_wheel = tmp_path / "raw.whl"
    canonical_wheel = tmp_path / "canonical.whl"
    raw_wheel.write_bytes(_wheel_bytes())
    original_write = wheel_normalize._write_new_regular_file

    def competing_write(path: Path, data: bytes) -> tuple[int, int, int, int, int]:
        path.write_bytes(b"concurrent replacement")
        return original_write(path, data)

    monkeypatch.setattr(wheel_normalize, "_write_new_regular_file", competing_write)
    with pytest.raises(WheelNormalizationError, match="already exists|exclusively create"):
        normalize_wheel_file(raw_wheel, canonical_wheel)

    assert canonical_wheel.read_bytes() == b"concurrent replacement"


def test_file_normalizer_detects_source_replaced_during_output_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_wheel = tmp_path / "raw.whl"
    canonical_wheel = tmp_path / "canonical.whl"
    raw_wheel.write_bytes(_wheel_bytes())
    original_write = wheel_normalize._write_new_regular_file

    def replacing_source(path: Path, data: bytes) -> tuple[int, int, int, int, int]:
        identity = original_write(path, data)
        raw_wheel.unlink()
        raw_wheel.write_bytes(b"concurrent replacement")
        return identity

    monkeypatch.setattr(wheel_normalize, "_write_new_regular_file", replacing_source)
    with pytest.raises(WheelNormalizationError, match="source wheel path changed"):
        normalize_wheel_file(raw_wheel, canonical_wheel)

    assert raw_wheel.read_bytes() == b"concurrent replacement"


def test_check_rejects_noncanonical_wheel(tmp_path: Path) -> None:
    wheel = tmp_path / "normshift-1.0-py3-none-any.whl"
    wheel.write_bytes(_wheel_bytes(host_system=0))

    with pytest.raises(WheelNormalizationError, match="non-canonical host-system"):
        assert_canonical_wheel_file(wheel)


def test_duplicate_member_is_rejected() -> None:
    with pytest.warns(UserWarning, match="Duplicate name"):
        raw = _wheel_bytes(duplicate=True)

    with pytest.raises(WheelNormalizationError, match="duplicate or aliased"):
        normalize_wheel_bytes(raw)


@pytest.mark.parametrize("name", ["../escape", "CON.txt", "bad?.txt"])
def test_unsafe_or_nonportable_member_name_is_rejected(name: str) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w") as archive:
        archive.writestr(name, b"payload")

    with pytest.raises(WheelNormalizationError, match="wheel member name"):
        normalize_wheel_bytes(output.getvalue())


def test_raw_backslash_member_name_is_rejected_even_on_windows() -> None:
    raw = bytearray(_wheel_bytes())
    first_central = _central_offsets(raw)[0]
    local_offset = struct.unpack_from("<I", raw, first_central + 42)[0]
    central_name_start = first_central + 46
    local_name_start = local_offset + 30
    slash_index = raw[central_name_start:].index(ord("/"))
    raw[central_name_start + slash_index] = ord("\\")
    raw[local_name_start + slash_index] = ord("\\")

    with pytest.raises(WheelNormalizationError, match="unsafe wheel member name"):
        normalize_wheel_bytes(bytes(raw))


def test_symlink_member_is_rejected() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w") as archive:
        link = zipfile.ZipInfo("normshift/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, b"target")

    with pytest.raises(WheelNormalizationError, match="link or special"):
        normalize_wheel_bytes(output.getvalue())


def test_local_and_central_names_must_match() -> None:
    raw = bytearray(_wheel_bytes())
    first_central = _central_offsets(raw)[0]
    local_offset = struct.unpack_from("<I", raw, first_central + 42)[0]
    raw[local_offset + 30] ^= 1

    with pytest.raises(WheelNormalizationError, match="local/central member name mismatch"):
        normalize_wheel_bytes(bytes(raw))


def test_local_and_central_metadata_must_match() -> None:
    raw = bytearray(_wheel_bytes())
    first_central = _central_offsets(raw)[0]
    local_offset = struct.unpack_from("<I", raw, first_central + 42)[0]
    raw[local_offset + 8] ^= 1

    with pytest.raises(WheelNormalizationError, match="local/central metadata mismatch"):
        normalize_wheel_bytes(bytes(raw))


@pytest.mark.parametrize("flag", [0x8, 0x20, 0x40, 0x2000])
def test_data_descriptor_and_encryption_related_flags_are_rejected(flag: int) -> None:
    raw = bytearray(_wheel_bytes())
    first_central = _central_offsets(raw)[0]
    local_offset = struct.unpack_from("<I", raw, first_central + 42)[0]
    struct.pack_into("<H", raw, first_central + 8, flag)
    struct.pack_into("<H", raw, local_offset + 6, flag)

    with pytest.raises(WheelNormalizationError, match="general-purpose flags"):
        normalize_wheel_bytes(bytes(raw))


def test_unreferenced_bytes_before_central_directory_are_rejected() -> None:
    raw = _wheel_bytes()
    old_end = _eocd_offset(raw)
    old_central = struct.unpack_from("<I", raw, old_end + 16)[0]
    blind = b"unreferenced"
    modified = bytearray(raw[:old_central] + blind + raw[old_central:])
    new_end = old_end + len(blind)
    struct.pack_into("<I", modified, new_end + 16, old_central + len(blind))

    with pytest.raises(WheelNormalizationError, match="unreferenced bytes"):
        normalize_wheel_bytes(bytes(modified))


def test_member_and_archive_comments_or_extras_are_rejected() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w") as archive:
        info = zipfile.ZipInfo("normshift/payload.bin")
        info.extra = b"xx"
        archive.writestr(info, b"payload")

    with pytest.raises(WheelNormalizationError, match="extras/comments"):
        normalize_wheel_bytes(output.getvalue())

    raw = bytearray(_wheel_bytes())
    raw.extend(b"x")
    end = _eocd_offset(raw)
    struct.pack_into("<H", raw, end + 20, 1)
    with pytest.raises(WheelNormalizationError, match="archive comments"):
        normalize_wheel_bytes(bytes(raw))


def test_large_compressed_member_is_rejected_before_payload_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("normshift/large.bin", b"0" * (17 * 1024 * 1024))

    def unexpected_payload_validation(_archive: zipfile.ZipFile) -> str | None:
        raise AssertionError("payload validation must not run for an oversized member")

    monkeypatch.setattr(zipfile.ZipFile, "testzip", unexpected_payload_validation)
    with pytest.raises(WheelNormalizationError, match="uncompressed-size bound"):
        normalize_wheel_bytes(output.getvalue())


def test_total_uncompressed_size_is_rejected_before_payload_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("normshift/first.bin", b"0" * 600)
        archive.writestr("normshift/second.bin", b"1" * 600)

    def unexpected_payload_validation(_archive: zipfile.ZipFile) -> str | None:
        raise AssertionError("payload validation must not run over the total size bound")

    monkeypatch.setattr(
        wheel_normalize,
        "MAX_WHEEL_TOTAL_UNCOMPRESSED_BYTES",
        1024,
    )
    monkeypatch.setattr(zipfile.ZipFile, "testzip", unexpected_payload_validation)
    with pytest.raises(WheelNormalizationError, match="total uncompressed-size bound"):
        normalize_wheel_bytes(output.getvalue())


def test_extreme_compression_ratio_is_rejected_before_payload_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("normshift/compressible.bin", b"0" * (1024 * 1024))

    def unexpected_payload_validation(_archive: zipfile.ZipFile) -> str | None:
        raise AssertionError("payload validation must not run over the ratio bound")

    monkeypatch.setattr(zipfile.ZipFile, "testzip", unexpected_payload_validation)
    with pytest.raises(WheelNormalizationError, match="compression-ratio bound"):
        normalize_wheel_bytes(output.getvalue())


@pytest.mark.parametrize(
    ("offset", "value", "message"),
    [
        (4, 1, "multi-disk"),
        (6, 1, "multi-disk"),
        (10, 0xFFFF, "multi-disk|ZIP64"),
        (16, 0xFFFFFFFF, "ZIP64"),
    ],
)
def test_unsupported_end_records_are_rejected(
    offset: int,
    value: int,
    message: str,
) -> None:
    raw = bytearray(_wheel_bytes())
    end = _eocd_offset(raw)
    if value <= 0xFFFF:
        struct.pack_into("<H", raw, end + offset, value)
    else:
        struct.pack_into("<I", raw, end + offset, value)

    with pytest.raises(WheelNormalizationError, match=message):
        normalize_wheel_bytes(bytes(raw))


def test_corrupt_member_payload_is_rejected() -> None:
    raw = bytearray(_wheel_bytes())
    first_central = _central_offsets(raw)[0]
    local_offset = struct.unpack_from("<I", raw, first_central + 42)[0]
    name_size, extra_size = struct.unpack_from("<2H", raw, local_offset + 26)
    raw[local_offset + 30 + name_size + extra_size] ^= 1

    with pytest.raises(WheelNormalizationError, match="CRC failed"):
        normalize_wheel_bytes(bytes(raw))


def test_truncated_central_directory_is_rejected() -> None:
    raw = _wheel_bytes()
    end = _eocd_offset(raw)
    broken = raw[: end - 1] + raw[end:]

    with pytest.raises(WheelNormalizationError, match="boundaries|signature|truncated"):
        normalize_wheel_bytes(broken)
