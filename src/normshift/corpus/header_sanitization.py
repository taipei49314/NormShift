"""Deterministically reduce curator HTTP headers to a non-sensitive allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from normshift.io_safety import write_transaction

SANITIZER_VERSION: Final = "1.0.0"
REPORT_REF: Final = "header-sanitization.json"
REPORT_SHA256: Final = "3db09ebb838adcfa8a122d7b6f8f7a811aff32fd885ccc6385f3c85d3d80a0ae"
MAX_HEADER_BYTES: Final = 1024 * 1024
MAX_FIELD_VALUE_BYTES: Final = 1024
ALLOWED_FIELDS: Final = frozenset(
    {
        "content-encoding",
        "content-length",
        "content-type",
        "etag",
        "last-modified",
        "location",
    }
)
EXPLICITLY_FORBIDDEN_FIELDS: Final = frozenset(
    {
        "authentication-info",
        "authorization",
        "cookie",
        "proxy-authenticate",
        "proxy-authorization",
        "set-cookie",
        "www-authenticate",
        "x-api-key",
        "x-auth-token",
        "x-github-otp",
    }
)
_FIELD_RE: Final = re.compile(rb"^[A-Za-z0-9-]+$")
_STATUS_LINE_RE: Final = re.compile(rb"^HTTP/1\.1 (?:200 OK|301 Moved Permanently)$")
_CONTENT_TYPE_RE: Final = re.compile(
    r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+"
    r"(?:; charset=[a-z0-9!#$&^_.+-]+)?$",
    re.IGNORECASE,
)
_ETAG_RE: Final = re.compile(r'^(?:W/)?"[!#-~]*"$')
_ALLOWED_LOCATIONS: Final = frozenset({"https://www.w3.org/copyright/software-license-2015/"})
_ALLOWED_ENCODINGS: Final = frozenset({"br", "deflate", "gzip", "identity"})
FORBIDDEN_VALUE_MARKERS: Final = (
    b"__cf_" + b"bm",
    b"bear" + b"er ",
    b"bas" + b"ic ",
    b"token=",
    b"api_" + b"key=",
    b"api-" + b"key=",
    b"gh" + b"p_",
    b"gh" + b"o_",
    b"gh" + b"u_",
    b"gh" + b"s_",
    b"gh" + b"r_",
    b"github_" + b"pat_",
    b"xo" + b"xb-",
    b"xo" + b"xp-",
    b"sk" + b"-",
    b"akia",
    b"-----begin " + b"private key-----",
)
HEADER_IDENTITY_BY_OUTPUT: Final[dict[str, tuple[str, int, str, int]]] = {
    "curation-headers/chain/whatwg-mimesniff-review-drafts.headers.txt": (
        "df9321f5817987bd764970af6f5bd21819cca8c8c019e578ba320ff2cae426cc",
        1305,
        "45ea006faf688b7680dba50c2c3f4ca09a61fa34226244039c190e5a7746abf4",
        185,
    ),
    "curation-headers/first/rfc-tls-1.0.headers.txt": (
        "4044df4a16d6452a195807bf0174ce8ecd138eb0ae2365180fa97fa089dc953a",
        697,
        "b86470483a0e1c62fa223dbbe42d3879ebe0499137414d9481782fb7b49fd0cc",
        88,
    ),
    "curation-headers/first/rfc-tls-1.1.headers.txt": (
        "0600930f99e5b8667623c1034012a4a1423d81537f07cfa41350febc26044639",
        696,
        "48028ee479d75b36b50b55079a1adea1d059cc42c9e36785d209b6ba7dd01d03",
        88,
    ),
    "curation-headers/first/rfc-tls-1.2.headers.txt": (
        "1ad6e4e4e02b15cc6f04ef05930c064f1b0c714d451e3eb1d7a99643902c4e0e",
        696,
        "50d73d965ef3e8f988d3a893934c5044abe051de309c327fe5a6241afec1dd64",
        88,
    ),
    "curation-headers/first/w3c-micropub-cr-20161018.headers.txt": (
        "986017dda1ce768dcf65b3ce4b4311e63007fa5b377b2283c516323cbf55a4ee",
        1151,
        "58c77b19cb95e7dc05be56f2f3959e2af4cc6469222c6549ce9b25698692bb5c",
        105,
    ),
    "curation-headers/first/w3c-micropub-pr-20170413.headers.txt": (
        "9fa4d189cd7181f77029e12078bfd4440f88ea7993c4ea0bd2432de7ece43c42",
        1146,
        "cbeccd776c976083c27273148a55c3a2016aefa202e8588fa3e69cf29757c772",
        105,
    ),
    "curation-headers/first/w3c-micropub-rec-20170523.headers.txt": (
        "cbc895b9700bd5ad3bb1a9aff2b75e5387816cc28a1e25c93e6d8214d642f70f",
        1150,
        "fbb98fde04c5f09b75a1d892b9fd0db8f77e26dea814c509ab85eecc17d886af",
        105,
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2023-07.headers.txt": (
        "b86fa828cee6c824d2ec4f7413484914d5886bd4041a2c019d1758ef976c8111",
        419,
        "79f8e4e7998b6ab32b204cdc1977ab88d0e08ad24b09804c332ade28ba52ecc2",
        153,
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2024-07.headers.txt": (
        "8ad8e1537c74abd231c4cbe8a6384a4e0209b2c6e2ff15c2baa168c8f9c7b132",
        419,
        "10d418bba3e0f722346d259de6cca8e0be160e4b3d5b2f373840355c7f09d245",
        153,
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2025-01.headers.txt": (
        "5faa963eedc6857d20371bf7da5302e2584b30ea340a05b51c29bc2373c86bcc",
        419,
        "d95cbfbffff77535d793294c92f896b78f085e982d816830576267071d4e1422",
        153,
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2025-07.headers.txt": (
        "93a3cdb15fadfa75df17e89712112181200fb8ae988112ae4f933f3b5739738b",
        419,
        "aa6d09ec122036f1fb5eee1a12a535f12a3e97711b5e7d535e4e4c2bb337b392",
        153,
    ),
    "curation-headers/license/CC-BY-4.0-legalcode.headers.txt": (
        "00a88da3b3dfbede35febbe96225d187933ade3560109dbb19461580a5e0de0b",
        339,
        "a2e9b04abb3f02cbd52e679b75cf20fe55d52f3078a3a2201b87d55c075ab3db",
        90,
    ),
    "curation-headers/license/IETF-TLP-5.headers.txt": (
        "3c6f334aac7a4bd8dacf337d5eab962a3fda291fc479fefd1c56174975c78fef",
        819,
        "f200a852576aeab81d052f0127ed987bd247443dbd681ffdb5262c8691d8d865",
        59,
    ),
    "curation-headers/license/IETF-TLP-FAQ.headers.txt": (
        "9971d573345574b6c6d5b3934d1f073030f3d2256b455c80d3d1a0ac6c7a4377",
        820,
        "f200a852576aeab81d052f0127ed987bd247443dbd681ffdb5262c8691d8d865",
        59,
    ),
    "curation-headers/license/W3C-Software-Document-License-2015.headers.txt": (
        "4238c064f29759eb562509dc82508e83b2283a8881547c91032ffef2ec740699",
        1944,
        "9d493a57462250214bb7ce1868ce3cf50aaa2e15bbefb12b307369235fd57a4c",
        175,
    ),
    "curation-headers/license/WHATWG-IPR-Policy.headers.txt": (
        "04258566b8d74f327f98a71954943e97a1c4182f0dd82ac90aa52cd6f4ea0e6d",
        417,
        "85f5ec0ee80cbce30638e6388eef5763a61225fb6272d8241ed0402944c52637",
        151,
    ),
    "curation-headers/policy/m1_m2_prereg_v1.headers.txt": (
        "7996089641c62273855039e3f2f9595118f879368e4454201bc7230360aca99f",
        927,
        "3b4789fb35831610590a7ab6d61e43058c925428dde15c21c44340aff629606a",
        157,
    ),
    "curation-headers/replay/micropub-cr.headers.txt": (
        "21aa4b6addae52e257bff349acc9f3b486c13a9b73a1e9483fd4619f97a8ecf2",
        1151,
        "58c77b19cb95e7dc05be56f2f3959e2af4cc6469222c6549ce9b25698692bb5c",
        105,
    ),
    "curation-headers/replay/micropub-pr.headers.txt": (
        "cb8b023f804097c7d2ff6cd5c0c210ae652a621e745eb4505c2413026ef5546f",
        1147,
        "cbeccd776c976083c27273148a55c3a2016aefa202e8588fa3e69cf29757c772",
        105,
    ),
    "curation-headers/replay/micropub-rec.headers.txt": (
        "222ed982234a50ce8d1f0ca429079cd97ca25a8b8004d97cfa0cb3a224c43fc0",
        1149,
        "fbb98fde04c5f09b75a1d892b9fd0db8f77e26dea814c509ab85eecc17d886af",
        105,
    ),
    "curation-headers/replay/mimesniff-2023.headers.txt": (
        "e644676922ffda6bbd47e22201a06f409d9e01540d88c27c819e86df8239e13f",
        419,
        "79f8e4e7998b6ab32b204cdc1977ab88d0e08ad24b09804c332ade28ba52ecc2",
        153,
    ),
    "curation-headers/replay/mimesniff-2024.headers.txt": (
        "26fcf219a91efd530bc9a0f0c799da0af169e7de0c52b93c0adceac316708ab5",
        419,
        "10d418bba3e0f722346d259de6cca8e0be160e4b3d5b2f373840355c7f09d245",
        153,
    ),
    "curation-headers/replay/mimesniff-2025-01.headers.txt": (
        "02c6ceecbe81ef76bbf7546ee89fc5be34a5dca68f4c8937c2b556dce2a95140",
        419,
        "d95cbfbffff77535d793294c92f896b78f085e982d816830576267071d4e1422",
        153,
    ),
    "curation-headers/replay/mimesniff-2025.headers.txt": (
        "1795bc492f4882489c86534057521a456ce6d661e13322dde77ed9783fae6f4c",
        419,
        "aa6d09ec122036f1fb5eee1a12a535f12a3e97711b5e7d535e4e4c2bb337b392",
        153,
    ),
    "curation-headers/replay/rfc2246.headers.txt": (
        "2a8f8959384b601baafc8a845be5378fdca92f2162d094c3df6954d6d531c553",
        697,
        "b86470483a0e1c62fa223dbbe42d3879ebe0499137414d9481782fb7b49fd0cc",
        88,
    ),
    "curation-headers/replay/rfc4346.headers.txt": (
        "6b3844bfc1a0ef1f4bd9dd0b7b5f5c5e5e89b39020a66870455844a1646ecec7",
        697,
        "48028ee479d75b36b50b55079a1adea1d059cc42c9e36785d209b6ba7dd01d03",
        88,
    ),
    "curation-headers/replay/rfc5246.headers.txt": (
        "3910495f9082b82210b777e1a8723d61ede7a6c95a765b3a7e75739078546147",
        697,
        "50d73d965ef3e8f988d3a893934c5044abe051de309c327fe5a6241afec1dd64",
        88,
    ),
}


def _source_ref_for_output(output_ref: str) -> str:
    mappings = (
        ("curation-headers/first/", "http/"),
        ("curation-headers/replay/", "replay-http/"),
        ("curation-headers/license/", "license-evidence/"),
        ("curation-headers/policy/", "policy/"),
    )
    for output_prefix, source_prefix in mappings:
        if output_ref.startswith(output_prefix):
            return source_prefix + output_ref.removeprefix(output_prefix)
    if output_ref == ("curation-headers/chain/whatwg-mimesniff-review-drafts.headers.txt"):
        return "chain-evidence-whatwg-mimesniff-review-drafts.headers.txt"
    raise AssertionError(f"unmapped frozen header output ref: {output_ref}")


HEADER_SOURCE_REF_BY_OUTPUT: Final[dict[str, str]] = {
    output_ref: _source_ref_for_output(output_ref) for output_ref in HEADER_IDENTITY_BY_OUTPUT
}


class HeaderSanitizationError(ValueError):
    """Header input or output violated the frozen sanitizer contract."""


@dataclass(frozen=True)
class HeaderMapping:
    source_ref: str
    output_ref: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_junction(path: Path) -> bool:
    checker = getattr(path, "is_junction", None)
    return bool(checker and checker())


def _read_regular_bounded(path: Path) -> bytes:
    candidate = Path(path)
    if candidate.is_symlink() or _is_junction(candidate):
        raise HeaderSanitizationError(f"header input is a symlink or junction: {candidate}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(candidate, flags)
    except OSError as exc:
        raise HeaderSanitizationError(f"cannot open header input {candidate}: {exc}") from exc
    try:
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink > 1:
                raise HeaderSanitizationError(
                    f"header input is not an unaliased regular file: {candidate}"
                )
            if before.st_size > MAX_HEADER_BYTES:
                raise HeaderSanitizationError(
                    f"header input exceeds {MAX_HEADER_BYTES} bytes: {candidate}"
                )
            data = stream.read(before.st_size + 1)
            after = os.fstat(stream.fileno())
    except HeaderSanitizationError:
        raise
    except OSError as exc:
        raise HeaderSanitizationError(f"cannot read header input {candidate}: {exc}") from exc
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_nlink,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_nlink,
    )
    if identity_before != identity_after or len(data) != before.st_size:
        raise HeaderSanitizationError(f"header input changed during read: {candidate}")
    return data


def _require_canonical_crlf(raw: bytes, *, source_ref: str) -> None:
    if len(raw) > MAX_HEADER_BYTES:
        raise HeaderSanitizationError(
            f"header input exceeds {MAX_HEADER_BYTES} bytes: {source_ref}"
        )
    if b"\x00" in raw:
        raise HeaderSanitizationError(f"NUL byte in header input: {source_ref}")
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\n" in without_crlf or b"\r" in without_crlf:
        raise HeaderSanitizationError(f"header input must use CRLF only: {source_ref}")
    if not raw.endswith(b"\r\n\r\n"):
        raise HeaderSanitizationError(
            f"header input must end with one HTTP blank line: {source_ref}"
        )


def _validate_field_value(name: str, raw_value: bytes, *, source_ref: str) -> None:
    if (
        not raw_value.startswith(b" ")
        or raw_value.startswith(b"  ")
        or raw_value.endswith((b" ", b"\t"))
        or len(raw_value) - 1 > MAX_FIELD_VALUE_BYTES
    ):
        raise HeaderSanitizationError(f"noncanonical or oversized {name} value in {source_ref}")
    value_bytes = raw_value[1:]
    if not value_bytes or any(byte < 0x20 or byte > 0x7E for byte in value_bytes):
        raise HeaderSanitizationError(f"non-printable or empty {name} value in {source_ref}")
    value = value_bytes.decode("ascii")
    lower = value.lower().encode("ascii")
    if any(marker in lower for marker in FORBIDDEN_VALUE_MARKERS):
        raise HeaderSanitizationError(
            f"sensitive-value marker survived sanitization in {source_ref}"
        )
    if name == "content-length":
        if (
            len(value) > 19
            or not value.isascii()
            or not value.isdecimal()
            or int(value) > (2**63 - 1)
        ):
            raise HeaderSanitizationError(f"invalid Content-Length in {source_ref}")
    elif name == "content-type":
        if _CONTENT_TYPE_RE.fullmatch(value) is None:
            raise HeaderSanitizationError(f"invalid Content-Type in {source_ref}")
    elif name == "content-encoding":
        if value.lower() not in _ALLOWED_ENCODINGS:
            raise HeaderSanitizationError(f"invalid Content-Encoding in {source_ref}")
    elif name == "etag":
        if len(value) > 256 or _ETAG_RE.fullmatch(value) is None:
            raise HeaderSanitizationError(f"invalid ETag in {source_ref}")
    elif name == "last-modified":
        try:
            parsed = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT")
        except ValueError as exc:
            raise HeaderSanitizationError(f"invalid Last-Modified in {source_ref}") from exc
        if parsed.strftime("%a, %d %b %Y %H:%M:%S GMT") != value:
            raise HeaderSanitizationError(f"noncanonical Last-Modified in {source_ref}")
    elif name == "location" and value not in _ALLOWED_LOCATIONS:
        raise HeaderSanitizationError(f"non-frozen Location in {source_ref}")


def validate_sanitized_header_bytes(raw: bytes, *, source_ref: str) -> frozenset[str]:
    """Validate the complete fail-closed grammar for a sanitized header artifact."""
    _require_canonical_crlf(raw, source_ref=source_ref)
    payload = raw[:-4]
    if not payload:
        raise HeaderSanitizationError(f"empty sanitized header input: {source_ref}")
    fields: set[str] = set()
    for block_index, block in enumerate(payload.split(b"\r\n\r\n")):
        lines = block.split(b"\r\n")
        status = _STATUS_LINE_RE.fullmatch(lines[0]) if lines else None
        if status is None:
            raise HeaderSanitizationError(
                f"invalid HTTP status line in block {block_index + 1}: {source_ref}"
            )
        block_fields: set[str] = set()
        for line_index, line in enumerate(lines[1:], start=2):
            if not line or line[:1] in {b" ", b"\t"}:
                raise HeaderSanitizationError(
                    f"sanitized header continuation/blank line {line_index} in {source_ref}"
                )
            raw_name, separator, raw_value = line.partition(b":")
            if not separator or _FIELD_RE.fullmatch(raw_name) is None:
                raise HeaderSanitizationError(
                    f"invalid sanitized header line {line_index} in {source_ref}"
                )
            name = raw_name.decode("ascii").lower()
            if name not in ALLOWED_FIELDS or name in block_fields:
                raise HeaderSanitizationError(
                    f"non-allowlisted or duplicate {name} field in {source_ref}"
                )
            _validate_field_value(name, raw_value, source_ref=source_ref)
            block_fields.add(name)
            fields.add(name)
    return frozenset(fields)


def sanitize_header_bytes(
    raw: bytes,
    *,
    source_ref: str,
) -> tuple[bytes, list[str], list[str]]:
    """Return allowlisted CRLF header bytes and removed/retained field names."""
    _require_canonical_crlf(raw, source_ref=source_ref)

    lines = raw.split(b"\r\n")
    output_lines: list[bytes] = []
    removed: set[str] = set()
    retained: set[str] = set()
    for index, line in enumerate(lines):
        if not line:
            output_lines.append(line)
            continue
        if line[:1] in {b" ", b"\t"}:
            continue
        if b":" not in line:
            if not line.startswith(b"HTTP/"):
                raise HeaderSanitizationError(f"non-header line {index + 1} in {source_ref}")
            output_lines.append(line)
            continue
        raw_name, _value = line.split(b":", 1)
        if not _FIELD_RE.fullmatch(raw_name):
            raise HeaderSanitizationError(
                f"invalid header field name on line {index + 1} in {source_ref}"
            )
        name = raw_name.decode("ascii").lower()
        if name in ALLOWED_FIELDS:
            output_lines.append(line)
            retained.add(name)
        else:
            removed.add(name)
    sanitized = b"\r\n".join(output_lines)
    actual_fields = validate_sanitized_header_bytes(sanitized, source_ref=source_ref)
    if actual_fields != retained:
        raise HeaderSanitizationError(
            f"sanitized header field set differs from retained report in {source_ref}"
        )
    return sanitized, sorted(removed), sorted(retained)


def _mappings(source_root: Path) -> tuple[HeaderMapping, ...]:
    records: list[HeaderMapping] = []
    for source in sorted((source_root / "http").glob("*.headers.txt")):
        records.append(
            HeaderMapping(
                source_ref=source.relative_to(source_root).as_posix(),
                output_ref=f"curation-headers/first/{source.name}",
            )
        )
    for source in sorted((source_root / "replay-http").glob("*.headers.txt")):
        records.append(
            HeaderMapping(
                source_ref=source.relative_to(source_root).as_posix(),
                output_ref=f"curation-headers/replay/{source.name}",
            )
        )
    for source in sorted((source_root / "license-evidence").glob("*.headers.txt")):
        records.append(
            HeaderMapping(
                source_ref=source.relative_to(source_root).as_posix(),
                output_ref=f"curation-headers/license/{source.name}",
            )
        )
    records.extend(
        (
            HeaderMapping(
                source_ref="policy/m1_m2_prereg_v1.headers.txt",
                output_ref="curation-headers/policy/m1_m2_prereg_v1.headers.txt",
            ),
            HeaderMapping(
                source_ref="chain-evidence-whatwg-mimesniff-review-drafts.headers.txt",
                output_ref="curation-headers/chain/whatwg-mimesniff-review-drafts.headers.txt",
            ),
        )
    )
    records.sort(key=lambda item: item.output_ref.encode("ascii"))
    source_refs = [record.source_ref for record in records]
    output_refs = [record.output_ref for record in records]
    if len(records) != 27 or len(set(source_refs)) != 27 or len(set(output_refs)) != 27:
        raise HeaderSanitizationError("expected 27 unique source-to-output header mappings")
    if set(output_refs) != set(HEADER_IDENTITY_BY_OUTPUT):
        raise HeaderSanitizationError("header output refs differ from frozen identities")
    if {record.output_ref: record.source_ref for record in records} != (
        HEADER_SOURCE_REF_BY_OUTPUT
    ):
        raise HeaderSanitizationError("header source refs differ from frozen identities")
    discovered = {
        path.relative_to(source_root).as_posix() for path in source_root.rglob("*.headers.txt")
    }
    if discovered != set(source_refs):
        raise HeaderSanitizationError(
            "staging header set differs from frozen mapping: "
            + ", ".join(sorted(discovered ^ set(source_refs)))
        )
    return tuple(records)


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sanitize_header_tree(source_root: Path, output_root: Path) -> dict[str, Any]:
    """Sanitize the exact frozen staging header set into an existing output root."""
    source = Path(source_root).resolve(strict=True)
    output = Path(output_root).resolve(strict=True)
    if source == output or source in output.parents or output in source.parents:
        raise HeaderSanitizationError("source and output roots must be disjoint")

    artifacts: dict[Path, bytes] = {}
    report_files: list[dict[str, Any]] = []
    for mapping in _mappings(source):
        raw = _read_regular_bounded(source / Path(mapping.source_ref))
        expected_original_sha, expected_original_length, expected_sha, expected_length = (
            HEADER_IDENTITY_BY_OUTPUT[mapping.output_ref]
        )
        if len(raw) != expected_original_length or _sha256(raw) != expected_original_sha:
            raise HeaderSanitizationError(
                f"original staging header identity differs: {mapping.source_ref}"
            )
        sanitized, removed, retained = sanitize_header_bytes(
            raw,
            source_ref=mapping.source_ref,
        )
        if len(sanitized) != expected_length or _sha256(sanitized) != expected_sha:
            raise HeaderSanitizationError(
                f"sanitized header identity differs: {mapping.output_ref}"
            )
        artifacts[output / Path(mapping.output_ref)] = sanitized
        report_files.append(
            {
                "source_ref": mapping.source_ref,
                "output_ref": mapping.output_ref,
                "original_sha256": _sha256(raw),
                "original_byte_length": len(raw),
                "sanitized_sha256": _sha256(sanitized),
                "sanitized_byte_length": len(sanitized),
                "removed_field_names": removed,
                "retained_field_names": retained,
            }
        )
    report: dict[str, Any] = {
        "schema_version": "normshift-m1-header-sanitization/v1",
        "sanitizer_version": SANITIZER_VERSION,
        "status": "SANITIZED_ALLOWLIST_HEADER_PROVENANCE_ONLY",
        "allowed_field_names": sorted(ALLOWED_FIELDS),
        "explicitly_forbidden_field_names": sorted(EXPLICITLY_FORBIDDEN_FIELDS),
        "unknown_field_policy": "DROP_ENTIRE_FIELD_AND_CONTINUATIONS",
        "continuation_policy": "DROP_ALL_CONTINUATION_LINES",
        "value_policy": (
            "BOUNDED_PRINTABLE_FIELD_SPECIFIC__FROZEN_LOCATION__CREDENTIAL_MARKER_REJECT"
        ),
        "raw_response_bodies_included": False,
        "sensitive_header_values_included": False,
        "files": report_files,
    }
    report_bytes = _canonical_json(report)
    if _sha256(report_bytes) != REPORT_SHA256:
        raise HeaderSanitizationError("header sanitization report identity differs")
    artifacts[output / REPORT_REF] = report_bytes
    write_transaction(artifacts)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output_root", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run the frozen sanitizer and print a value-free machine-readable summary."""
    args = _parser().parse_args(list(argv) if argv is not None else None)
    report = sanitize_header_tree(args.source_root, args.output_root)
    print(
        json.dumps(
            {
                "file_count": len(report["files"]),
                "sanitizer_version": report["sanitizer_version"],
                "status": report["status"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0
