"""Fail-closed exact-root inventory for source-recipe evidence.

The inventory deliberately excludes itself and its digest sidecar.  Callers
must supply the inventory digest from an independent trust anchor; the sidecar
is then checked as a portable, human-readable copy of that same digest.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from normshift.corpus.acquisition import SourceManifest, load_source_manifest
from normshift.corpus.header_sanitization import (
    ALLOWED_FIELDS,
    EXPLICITLY_FORBIDDEN_FIELDS,
    HEADER_IDENTITY_BY_OUTPUT,
    HEADER_SOURCE_REF_BY_OUTPUT,
    REPORT_SHA256,
    SANITIZER_VERSION,
    HeaderSanitizationError,
    validate_sanitized_header_bytes,
)
from normshift.portable_ref import PortableRefError, validate_portable_ref
from normshift.strict_json import StrictJSONError, strict_loads

INVENTORY_REF: Final = "EVIDENCE.sha256"
INVENTORY_SIDECAR_REF: Final = "EVIDENCE.sha256.sha256"
SOURCE_MANIFEST_REF: Final = "source-manifest.json"
LICENSE_INVENTORY_REF: Final = "license-inventory.json"
CURATOR_INVENTORY_REF: Final = "curator/SOURCE-INVENTORY.json"
CURATOR_REPORT_REF: Final = "curator/SOURCE-CURATION-REPORT.md"
CURATOR_LICENSE_INVENTORY_REF: Final = "curator/LICENSE-INVENTORY.md"
CURATION_PROVENANCE_REF: Final = "curation-provenance.json"
HEADER_SANITIZATION_REF: Final = "header-sanitization.json"
README_REF: Final = "README.md"
MAX_INVENTORY_BYTES: Final = 1024 * 1024
MAX_SIDECAR_BYTES: Final = 256
MAX_CONTENT_FILE_BYTES: Final = 8 * 1024 * 1024
MAX_TOTAL_FILE_BYTES: Final = 32 * 1024 * 1024
MAX_ENTRY_COUNT: Final = 512
MAX_DEPTH: Final = 16
MAX_REF_BYTES: Final = 1024
MAX_SEGMENT_BYTES: Final = 255
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_INVENTORY_LINE_RE: Final = re.compile(r"^([0-9a-f]{64})  ([A-Za-z0-9._/-]+)$")
_SEGMENT_RE: Final = re.compile(r"^[A-Za-z0-9._-]+$")
_WINDOWS_RESERVED: Final = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}
_CURATOR_INVENTORY_SHA256: Final = (
    "d8f7c0a91c9b821fde0381ef94f8c8df5ef7289fa5b8f14825a16285cbe716ac"
)
_CURATOR_REPORT_SHA256: Final = "81f38f3e8b547efc401f0e5664ab7257c2bb38849eac3d11dc5e25df36411d0b"
_CURATOR_LICENSE_INVENTORY_SHA256: Final = (
    "6d003272c1307bd08778e0951b76f70d0dd52d6f32d2c1388bfdf5b1238a0702"
)
_CURATOR_PARTIAL_CHECKSUM_SHA256: Final = (
    "1bbf5757bb9a2b81db3f05c790ea81be250b5ff6d3c47891ee29aa13900f6883"
)
_REJECTED_HELPER_SHA256: Final = "fbda25dc5b25701673e734884de4b06b752946ea49b9e2c9fed397190043ef81"
_README_SHA256: Final = "ed112c855b02c84dc7991fb75ddce89cdf8391221b5b5d1beca26391d0c52f0c"
_FIXED_NON_HEADER_CONTENT_REFS: Final = frozenset(
    {
        README_REF,
        CURATION_PROVENANCE_REF,
        CURATOR_LICENSE_INVENTORY_REF,
        CURATOR_REPORT_REF,
        CURATOR_INVENTORY_REF,
        HEADER_SANITIZATION_REF,
        LICENSE_INVENTORY_REF,
        SOURCE_MANIFEST_REF,
    }
)
_CURATOR_WHATWG_REDISTRIBUTION_BASIS: Final = (
    "The Review Draft footer and WHATWG IPR Policy section 7.1.1 license Review "
    "Drafts under CC BY 4.0. Full raw HTML is redistributed under CC BY; "
    "source-code portions have a separate BSD 3-Clause option."
)
_RECIPE_WHATWG_REDISTRIBUTION_BASIS: Final = (
    "The Review Draft footer and WHATWG IPR Policy section 7.1.1 license Review "
    "Drafts under CC BY 4.0. If a later authorized acquisition is redistributed, "
    "full raw HTML would be distributed under CC BY; source-code portions have a "
    "separate BSD 3-Clause option."
)


class EvidenceInventoryError(ValueError):
    """The source-recipe evidence root could not be proven exact."""


@dataclass(frozen=True)
class EvidenceInventoryResult:
    inventory_sha256: str
    content_file_count: int
    total_content_bytes: int
    content_refs: tuple[str, ...]
    root_state_sha256: str


@dataclass(frozen=True)
class SourceRecipeEvidenceResult:
    inventory_sha256: str
    manifest_sha256: str
    corpus_id: str
    source_count: int
    families: tuple[str, ...]
    mode: str = "DEVELOPMENT_RECIPE_EVIDENCE_VERIFIED"


@dataclass(frozen=True)
class _EntryState:
    kind: str
    device: int
    inode: int
    size: int
    modified_ns: int
    links: int


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_junction(path: Path) -> bool:
    checker = getattr(path, "is_junction", None)
    return bool(checker and checker())


def _is_reparse_point(info: os.stat_result) -> bool:
    attributes = getattr(info, "st_file_attributes", 0)
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(flag and attributes & flag)


def _validate_evidence_ref(value: str, *, label: str) -> str:
    try:
        ref = validate_portable_ref(value)
    except PortableRefError as exc:
        raise EvidenceInventoryError(f"{label}: {exc}") from exc
    if len(ref.encode("utf-8")) > MAX_REF_BYTES:
        raise EvidenceInventoryError(f"{label}: ref exceeds {MAX_REF_BYTES} UTF-8 bytes")
    for segment in ref.split("/"):
        if len(segment.encode("utf-8")) > MAX_SEGMENT_BYTES:
            raise EvidenceInventoryError(
                f"{label}: segment exceeds {MAX_SEGMENT_BYTES} UTF-8 bytes"
            )
        if unicodedata.normalize("NFC", segment) != segment:
            raise EvidenceInventoryError(f"{label}: segment must use Unicode NFC")
        if not _SEGMENT_RE.fullmatch(segment):
            raise EvidenceInventoryError(
                f"{label}: segment must use conservative portable ASCII: {segment!r}"
            )
        if segment.endswith((".", " ")):
            raise EvidenceInventoryError(f"{label}: Windows-unsafe segment {segment!r}")
        if segment.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
            raise EvidenceInventoryError(f"{label}: reserved Windows segment {segment!r}")
    return ref


def _absolute_unaliased_root(root: Path) -> Path:
    candidate = Path(root)
    if candidate.is_symlink() or _is_junction(candidate):
        raise EvidenceInventoryError(f"evidence root must not be a symlink or junction: {root}")
    try:
        before = candidate.lstat()
    except OSError as exc:
        raise EvidenceInventoryError(f"cannot stat evidence root: {exc}") from exc
    if not stat.S_ISDIR(before.st_mode) or _is_reparse_point(before):
        raise EvidenceInventoryError(f"evidence root must be a directory: {root}")
    try:
        absolute = Path(os.path.abspath(candidate))
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise EvidenceInventoryError(f"cannot resolve evidence root: {exc}") from exc
    if os.path.normcase(str(absolute)) != os.path.normcase(str(resolved)):
        raise EvidenceInventoryError("evidence root path contains a filesystem alias")
    try:
        after = candidate.lstat()
    except OSError as exc:
        raise EvidenceInventoryError(f"cannot restat evidence root: {exc}") from exc
    if not stat.S_ISDIR(after.st_mode) or _is_reparse_point(after):
        raise EvidenceInventoryError("evidence root became a reparse point")
    identity_before = (before.st_dev, before.st_ino, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_mtime_ns)
    if identity_before != identity_after:
        raise EvidenceInventoryError("evidence root changed during path validation")
    return resolved


def _entry_state(info: os.stat_result, *, kind: str) -> _EntryState:
    return _EntryState(
        kind=kind,
        device=info.st_dev,
        inode=info.st_ino,
        size=info.st_size,
        modified_ns=info.st_mtime_ns,
        links=info.st_nlink,
    )


def _scan_root(root: Path) -> dict[str, _EntryState]:
    states: dict[str, _EntryState] = {}
    aliases: dict[str, str] = {}
    file_identities: dict[tuple[int, int], str] = {}
    total_file_bytes = 0

    def walk(directory: Path, prefix: str, depth: int) -> None:
        nonlocal total_file_bytes
        if depth > MAX_DEPTH:
            raise EvidenceInventoryError(f"evidence root exceeds maximum depth {MAX_DEPTH}")
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name.encode("utf-8"))
        except (OSError, UnicodeError) as exc:
            raise EvidenceInventoryError(f"cannot enumerate evidence root: {exc}") from exc
        for entry in entries:
            ref = f"{prefix}/{entry.name}" if prefix else entry.name
            _validate_evidence_ref(ref, label="evidence entry")
            alias = unicodedata.normalize("NFKC", ref).casefold()
            previous_alias = aliases.get(alias)
            if previous_alias is not None and previous_alias != ref:
                raise EvidenceInventoryError(
                    f"portable evidence path alias collision: {ref!r} vs {previous_alias!r}"
                )
            aliases[alias] = ref
            path = directory / entry.name
            if entry.is_symlink() or _is_junction(path):
                raise EvidenceInventoryError(
                    f"symlink or junction is forbidden in evidence root: {ref}"
                )
            try:
                # Path.stat provides complete file identity on Windows; the
                # DirEntry fast-stat result can report zero device/inode/link
                # values and cannot anchor the subsequent descriptor read.
                info = path.stat(follow_symlinks=False)
            except OSError as exc:
                raise EvidenceInventoryError(f"cannot stat evidence entry {ref}: {exc}") from exc
            if _is_reparse_point(info):
                raise EvidenceInventoryError(f"reparse point is forbidden: {ref}")
            if stat.S_ISDIR(info.st_mode):
                states[ref] = _entry_state(info, kind="directory")
                walk(path, ref, depth + 1)
            elif stat.S_ISREG(info.st_mode):
                if info.st_nlink > 1:
                    raise EvidenceInventoryError(
                        f"hard-linked evidence file is forbidden: {ref} (links={info.st_nlink})"
                    )
                identity = (info.st_dev, info.st_ino)
                if info.st_ino != 0:
                    previous_identity = file_identities.get(identity)
                    if previous_identity is not None:
                        raise EvidenceInventoryError(
                            f"evidence file alias: {ref!r} and {previous_identity!r}"
                        )
                    file_identities[identity] = ref
                states[ref] = _entry_state(info, kind="file")
                total_file_bytes += info.st_size
            else:
                raise EvidenceInventoryError(f"special evidence entry is forbidden: {ref}")
            if len(states) > MAX_ENTRY_COUNT:
                raise EvidenceInventoryError(
                    f"evidence root exceeds maximum {MAX_ENTRY_COUNT} entries"
                )
            if total_file_bytes > MAX_TOTAL_FILE_BYTES:
                raise EvidenceInventoryError(
                    f"evidence root exceeds maximum {MAX_TOTAL_FILE_BYTES} file bytes"
                )

    walk(root, "", 1)
    return states


def _read_regular_bounded(
    root: Path,
    ref: str,
    state: _EntryState,
    *,
    max_bytes: int,
) -> bytes:
    if state.kind != "file":
        raise EvidenceInventoryError(f"evidence ref is not a regular file: {ref}")
    if state.size > max_bytes:
        raise EvidenceInventoryError(f"evidence file {ref} exceeds {max_bytes} bytes")
    path = root / Path(ref)
    if path.is_symlink() or _is_junction(path):
        raise EvidenceInventoryError(f"evidence file is a symlink or junction: {ref}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise EvidenceInventoryError(f"cannot open evidence file {ref}: {exc}") from exc
    try:
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink > 1 or _is_reparse_point(before):
                raise EvidenceInventoryError(
                    f"evidence file is not an unaliased regular file: {ref}"
                )
            expected = (
                state.device,
                state.inode,
                state.size,
                state.modified_ns,
                state.links,
            )
            observed = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_nlink,
            )
            if observed != expected:
                raise EvidenceInventoryError(f"evidence file changed before read: {ref}")
            data = stream.read(state.size + 1)
            after = os.fstat(stream.fileno())
    except EvidenceInventoryError:
        raise
    except OSError as exc:
        raise EvidenceInventoryError(f"cannot read evidence file {ref}: {exc}") from exc
    final_observed = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_nlink,
    )
    if final_observed != expected or len(data) != state.size:
        raise EvidenceInventoryError(f"evidence file changed during bounded read: {ref}")
    try:
        path_after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise EvidenceInventoryError(f"cannot restat evidence file {ref}: {exc}") from exc
    if _is_reparse_point(path_after):
        raise EvidenceInventoryError(f"evidence path became a reparse point: {ref}")
    path_observed = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
        path_after.st_nlink,
    )
    if path_observed != expected:
        raise EvidenceInventoryError(f"evidence path changed during bounded read: {ref}")
    return data


def _parse_inventory(raw: bytes) -> tuple[tuple[str, str], ...]:
    try:
        text = raw.decode("ascii")
    except UnicodeError as exc:
        raise EvidenceInventoryError(f"inventory must be ASCII: {exc}") from exc
    if not text or not text.endswith("\n"):
        raise EvidenceInventoryError("inventory must be non-empty and newline-terminated")
    lines = text.removesuffix("\n").split("\n")
    records: list[tuple[str, str]] = []
    exact_refs: set[str] = set()
    aliases: dict[str, str] = {}
    for index, line in enumerate(lines, start=1):
        match = _INVENTORY_LINE_RE.fullmatch(line)
        if match is None:
            raise EvidenceInventoryError(f"inventory line {index} is not canonical")
        digest, raw_ref = match.groups()
        ref = _validate_evidence_ref(raw_ref, label=f"inventory line {index}")
        if ref in {INVENTORY_REF, INVENTORY_SIDECAR_REF}:
            raise EvidenceInventoryError(f"inventory self-cycle entry is forbidden: {ref}")
        if ref in exact_refs:
            raise EvidenceInventoryError(f"duplicate inventory ref: {ref}")
        exact_refs.add(ref)
        alias = unicodedata.normalize("NFKC", ref).casefold()
        previous = aliases.get(alias)
        if previous is not None:
            raise EvidenceInventoryError(
                f"portable inventory alias collision: {ref!r} vs {previous!r}"
            )
        aliases[alias] = ref
        records.append((ref, digest))
    if not records:
        raise EvidenceInventoryError("inventory must declare at least one content file")
    ordered = sorted(records, key=lambda item: item[0].encode("ascii"))
    if records != ordered:
        raise EvidenceInventoryError("inventory refs must be sorted by ASCII bytes")
    return tuple(records)


def _expected_directories(file_refs: set[str]) -> set[str]:
    directories: set[str] = set()
    for ref in file_refs:
        parts = ref.split("/")
        for end in range(1, len(parts)):
            directories.add("/".join(parts[:end]))
    return directories


def _root_state_sha256(states: Mapping[str, _EntryState]) -> str:
    lines = [
        "\0".join(
            (
                ref,
                state.kind,
                str(state.device),
                str(state.inode),
                str(state.size),
                str(state.modified_ns),
                str(state.links),
            )
        )
        for ref, state in sorted(states.items(), key=lambda item: item[0].encode("ascii"))
    ]
    return _sha256(("\n".join(lines) + "\n").encode("ascii"))


def verify_evidence_root(
    root: Path,
    *,
    expected_inventory_sha256: str,
) -> EvidenceInventoryResult:
    """Verify a complete evidence root with an independently supplied digest."""
    if not _SHA256_RE.fullmatch(expected_inventory_sha256):
        raise EvidenceInventoryError("expected inventory SHA-256 must be lowercase 64-hex")
    exact_root = _absolute_unaliased_root(root)
    before = _scan_root(exact_root)
    for required_ref in (INVENTORY_REF, INVENTORY_SIDECAR_REF):
        state = before.get(required_ref)
        if state is None or state.kind != "file":
            raise EvidenceInventoryError(f"missing required evidence file: {required_ref}")

    inventory_raw = _read_regular_bounded(
        exact_root,
        INVENTORY_REF,
        before[INVENTORY_REF],
        max_bytes=MAX_INVENTORY_BYTES,
    )
    inventory_sha256 = _sha256(inventory_raw)
    if not hmac.compare_digest(inventory_sha256, expected_inventory_sha256):
        raise EvidenceInventoryError(
            "inventory SHA-256 differs from independent trust anchor: "
            f"expected {expected_inventory_sha256}, got {inventory_sha256}"
        )
    sidecar_raw = _read_regular_bounded(
        exact_root,
        INVENTORY_SIDECAR_REF,
        before[INVENTORY_SIDECAR_REF],
        max_bytes=MAX_SIDECAR_BYTES,
    )
    expected_sidecar = f"{inventory_sha256}  {INVENTORY_REF}\n".encode("ascii")
    if not hmac.compare_digest(sidecar_raw, expected_sidecar):
        raise EvidenceInventoryError("inventory digest sidecar is not canonical or does not match")

    records = _parse_inventory(inventory_raw)
    declared_file_refs = {ref for ref, _digest in records}
    expected_files = declared_file_refs | {INVENTORY_REF, INVENTORY_SIDECAR_REF}
    actual_files = {ref for ref, state in before.items() if state.kind == "file"}
    expected_directories = _expected_directories(expected_files)
    actual_directories = {ref for ref, state in before.items() if state.kind == "directory"}
    if actual_files != expected_files:
        raise EvidenceInventoryError(
            "evidence root file set differs from inventory contract: "
            + ", ".join(sorted(actual_files ^ expected_files))
        )
    if actual_directories != expected_directories:
        raise EvidenceInventoryError(
            "evidence root directory set differs from inventory contract: "
            + ", ".join(sorted(actual_directories ^ expected_directories))
        )

    total_content_bytes = 0
    for ref, expected_digest in records:
        state = before[ref]
        raw = _read_regular_bounded(
            exact_root,
            ref,
            state,
            max_bytes=MAX_CONTENT_FILE_BYTES,
        )
        total_content_bytes += len(raw)
        actual_digest = _sha256(raw)
        if not hmac.compare_digest(actual_digest, expected_digest):
            raise EvidenceInventoryError(
                f"evidence content SHA-256 mismatch for {ref}: "
                f"expected {expected_digest}, got {actual_digest}"
            )

    after = _scan_root(exact_root)
    if before != after:
        raise EvidenceInventoryError("evidence root changed during verification")
    return EvidenceInventoryResult(
        inventory_sha256=inventory_sha256,
        content_file_count=len(records),
        total_content_bytes=total_content_bytes,
        content_refs=tuple(ref for ref, _digest in records),
        root_state_sha256=_root_state_sha256(after),
    )


def _require_exact_keys(
    value: Any,
    expected: set[str],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceInventoryError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        raise EvidenceInventoryError(
            f"{label} fields differ from contract: " + ", ".join(sorted(actual ^ expected))
        )
    return cast(Mapping[str, Any], value)


def _json_exact_equal(actual: Any, expected: Any) -> bool:
    """Compare JSON values without Python's bool/int equality aliasing."""
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _json_exact_equal(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _json_exact_equal(actual_value, expected_value)
            for actual_value, expected_value in zip(actual, expected, strict=True)
        )
    return bool(actual == expected)


def _read_inventory_content(
    root: Path,
    inventory: EvidenceInventoryResult,
    ref: str,
) -> bytes:
    if ref not in inventory.content_refs:
        raise EvidenceInventoryError(f"evidence inventory does not bind {ref}")
    states = _scan_root(root)
    return _read_regular_bounded(
        root,
        ref,
        states[ref],
        max_bytes=MAX_CONTENT_FILE_BYTES,
    )


def _load_strict_json_content(
    root: Path,
    inventory: EvidenceInventoryResult,
    ref: str,
) -> Any:
    raw = _read_inventory_content(root, inventory, ref)
    try:
        return strict_loads(raw)
    except StrictJSONError as exc:
        raise EvidenceInventoryError(f"strict evidence JSON rejected for {ref}: {exc}") from exc


def _canonical_json_bytes(payload: Any) -> bytes:
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise EvidenceInventoryError(f"evidence JSON is not canonicalizable: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _load_canonical_json_content(
    root: Path,
    inventory: EvidenceInventoryResult,
    ref: str,
) -> Any:
    raw = _read_inventory_content(root, inventory, ref)
    try:
        payload = strict_loads(raw)
    except StrictJSONError as exc:
        raise EvidenceInventoryError(f"strict evidence JSON rejected for {ref}: {exc}") from exc
    if raw != _canonical_json_bytes(payload):
        raise EvidenceInventoryError(f"evidence JSON is not canonical compact JSON: {ref}")
    return payload


def _validate_curator_inventory(
    root: Path,
    inventory: EvidenceInventoryResult,
    manifest: SourceManifest,
) -> Mapping[str, Any]:
    payload = _load_strict_json_content(root, inventory, CURATOR_INVENTORY_REF)
    if not isinstance(payload, dict):
        raise EvidenceInventoryError("curator source inventory must be an object")
    if payload.get("schema_version") != "normshift-independent-source-curation/v1":
        raise EvidenceInventoryError("unsupported curator source inventory schema")
    if payload.get("curation_status") != (
        "DEVELOPMENT_SOURCE_CORPUS_READY__ACCEPTANCE_NOT_ADJUDICATED"
    ):
        raise EvidenceInventoryError("curator source inventory has an invalid status ceiling")
    policy = payload.get("policy")
    if not isinstance(policy, dict) or (
        policy.get("id"),
        policy.get("sha256"),
    ) != (
        manifest.acceptance_policy_id,
        manifest.acceptance_policy_sha256,
    ):
        raise EvidenceInventoryError("curator policy identity differs from manifest")
    scope = payload.get("scope_boundaries")
    scope_invalid = (
        not isinstance(scope, dict)
        or not scope
        or any(value is not False for value in scope.values())
    )
    if scope_invalid:
        raise EvidenceInventoryError("curator scope must exclude all evaluation activity")
    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list):
        raise EvidenceInventoryError("curator sources must be an array")
    curator_sources: dict[str, Mapping[str, Any]] = {}
    for index, raw_source in enumerate(raw_sources):
        if not isinstance(raw_source, dict):
            raise EvidenceInventoryError(f"curator sources[{index}] must be an object")
        source_id = raw_source.get("source_id")
        if not isinstance(source_id, str) or source_id in curator_sources:
            raise EvidenceInventoryError("curator source IDs must be unique strings")
        curator_sources[source_id] = cast(Mapping[str, Any], raw_source)
    manifest_ids = {record.source_id for record in manifest.sources}
    if set(curator_sources) != manifest_ids:
        raise EvidenceInventoryError("curator source set differs from manifest")

    family_mapping = {"RFC": "rfc", "W3C_TR": "w3c", "WHATWG": "whatwg"}
    adapter_ids = {
        "rfc": "normshift.adapters.rfc",
        "w3c": "normshift.adapters.w3c",
        "whatwg": "normshift.adapters.whatwg",
    }
    timestamp_re = re.compile(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})\.[0-9]+Z$")
    for record in manifest.sources:
        curator = curator_sources[record.source_id]
        curator_family = curator.get("family")
        if not isinstance(curator_family, str) or family_mapping.get(curator_family) != (
            record.family.value
        ):
            raise EvidenceInventoryError(
                f"curator family differs from manifest for {record.source_id}"
            )
        retrieved = curator.get("retrieved_at_utc")
        match = timestamp_re.fullmatch(retrieved) if isinstance(retrieved, str) else None
        if match is None or f"{match.group(1)}Z" != record.curator_retrieved_at_utc:
            raise EvidenceInventoryError(
                f"curator timestamp was not truncated exactly for {record.source_id}"
            )
        curator_license = curator.get("license")
        if not isinstance(curator_license, dict):
            raise EvidenceInventoryError(f"missing curator license for {record.source_id}")
        expected_pairs = {
            "standard_id": record.standard_id,
            "version_or_date": record.version_or_date,
            "requested_url": record.acquisition_url,
            "final_url": record.canonical_url,
            "canonical_url": record.canonical_url,
            "redirect_chain": list(record.redirect_chain),
            "etag_or_null": record.etag,
            "last_modified_or_null": record.last_modified,
            "media_type": record.media_type,
            "charset_or_null": record.charset,
            "raw_sha256": record.content_sha256,
            "byte_length": record.byte_length,
            "adapter_id": adapter_ids[record.family.value],
            "adapter_version": record.adapter_version,
            "normalization_version": record.normalization_version,
            "profile": record.profile.value,
        }
        for field, expected_value in expected_pairs.items():
            if not _json_exact_equal(curator.get(field), expected_value):
                raise EvidenceInventoryError(
                    f"curator field {field} differs from manifest for {record.source_id}"
                )
        expected_license = {
            "license_name": record.license_name,
            "license_url": record.license_url,
        }
        for field, expected_value in expected_license.items():
            if not _json_exact_equal(curator_license.get(field), expected_value):
                raise EvidenceInventoryError(
                    f"curator license {field} differs from manifest for {record.source_id}"
                )
        curator_basis = curator_license.get("redistribution_basis")
        if record.family.value == "whatwg":
            if curator_basis != _CURATOR_WHATWG_REDISTRIBUTION_BASIS or (
                record.redistribution_basis != _RECIPE_WHATWG_REDISTRIBUTION_BASIS
            ):
                raise EvidenceInventoryError(
                    "curator WHATWG redistribution basis was not mapped to the "
                    f"conditional recipe-only wording for {record.source_id}"
                )
        elif curator_basis != record.redistribution_basis:
            raise EvidenceInventoryError(
                f"curator license redistribution_basis differs from manifest for {record.source_id}"
            )
        if curator.get("replay_sha256") != record.content_sha256 or (
            curator.get("replay_byte_identical") is not True
        ):
            raise EvidenceInventoryError(f"curator replay identity differs for {record.source_id}")
        expected_document_version = f"sha256:{record.content_sha256[:12]}"
        if record.document_version != expected_document_version:
            raise EvidenceInventoryError(
                f"manifest document version is not hash-derived for {record.source_id}"
            )
    return cast(Mapping[str, Any], payload)


def _validate_curation_provenance(
    root: Path,
    inventory: EvidenceInventoryResult,
    manifest: SourceManifest,
    curator_inventory: Mapping[str, Any],
) -> None:
    payload = _load_canonical_json_content(root, inventory, CURATION_PROVENANCE_REF)
    obj = _require_exact_keys(
        payload,
        {
            "schema_version",
            "status",
            "materialized_at_utc",
            "source_curation",
            "materialization_rules",
            "acquisition_recipe_mappings",
            "timestamp_mappings",
            "repository_boundary",
        },
        label="curation provenance",
    )
    if obj["schema_version"] != "normshift-m1-development-curation-provenance/v1":
        raise EvidenceInventoryError("unsupported curation provenance schema")
    if obj["status"] != ("DEVELOPMENT_SOURCE_RECIPES_ONLY__ACCEPTANCE_NOT_ADJUDICATED"):
        raise EvidenceInventoryError("curation provenance has an invalid status ceiling")
    if obj["materialized_at_utc"] != "2026-08-11T02:11:54Z":
        raise EvidenceInventoryError("curation provenance materialization time differs")

    source_curation = _require_exact_keys(
        obj["source_curation"],
        {
            "schema_version",
            "inventory_ref",
            "inventory_sha256",
            "report_ref",
            "report_sha256",
            "license_inventory_ref",
            "license_inventory_sha256",
            "partial_checksum_file_sha256",
            "partial_checksum_file_in_repository",
            "policy_ref",
            "policy_sha256",
        },
        label="curation provenance source_curation",
    )
    expected_source_curation: dict[str, Any] = {
        "schema_version": "normshift-independent-source-curation/v1",
        "inventory_ref": CURATOR_INVENTORY_REF,
        "inventory_sha256": _CURATOR_INVENTORY_SHA256,
        "report_ref": CURATOR_REPORT_REF,
        "report_sha256": _CURATOR_REPORT_SHA256,
        "license_inventory_ref": CURATOR_LICENSE_INVENTORY_REF,
        "license_inventory_sha256": _CURATOR_LICENSE_INVENTORY_SHA256,
        "partial_checksum_file_sha256": _CURATOR_PARTIAL_CHECKSUM_SHA256,
        "partial_checksum_file_in_repository": False,
        "policy_ref": manifest.acceptance_policy_ref,
        "policy_sha256": manifest.acceptance_policy_sha256,
    }
    if not _json_exact_equal(dict(source_curation), expected_source_curation):
        raise EvidenceInventoryError("curation provenance source identities differ")
    if curator_inventory.get("schema_version") != source_curation["schema_version"]:
        raise EvidenceInventoryError("curation provenance source schema differs")
    for ref, expected_digest in (
        (CURATOR_INVENTORY_REF, _CURATOR_INVENTORY_SHA256),
        (CURATOR_REPORT_REF, _CURATOR_REPORT_SHA256),
        (CURATOR_LICENSE_INVENTORY_REF, _CURATOR_LICENSE_INVENTORY_SHA256),
    ):
        actual_digest = _sha256(_read_inventory_content(root, inventory, ref))
        if not hmac.compare_digest(actual_digest, expected_digest):
            raise EvidenceInventoryError(
                f"curation provenance copied artifact SHA-256 differs for {ref}"
            )

    rules = _require_exact_keys(
        obj["materialization_rules"],
        {
            "target_manifest",
            "family_mapping",
            "adapter_mapping",
            "adapter_version",
            "normalization_version",
            "identity_preflight_version",
            "document_version_rule",
            "header_value_source",
            "acquisition_recipe_mapping",
            "license_inventory_ref",
            "license_inventory_rule",
            "whatwg_basis_mapping",
            "header_sanitization",
            "timestamp_rule",
            "snapshot_distribution",
        },
        label="curation provenance materialization_rules",
    )
    expected_adapter_mapping = {
        "rfc": {"adapter": "rfc", "profile": "rfc2119"},
        "w3c": {"adapter": "w3c", "profile": "rfc2119"},
        "whatwg": {"adapter": "whatwg", "profile": "whatwg"},
    }
    expected_fixed_rules: dict[str, Any] = {
        "target_manifest": SOURCE_MANIFEST_REF,
        "family_mapping": {"RFC": "rfc", "W3C_TR": "w3c", "WHATWG": "whatwg"},
        "adapter_mapping": expected_adapter_mapping,
        "adapter_version": "1.0.0",
        "normalization_version": "1.0.0",
        "identity_preflight_version": "1.0.0",
        "document_version_rule": (
            "sha256: followed by the first 12 lowercase hexadecimal characters of content_sha256"
        ),
        "header_value_source": (
            "Exact redirect, ETag, Last-Modified, media-type, and charset assertions "
            "were transcribed from the hash-bound independent SOURCE-INVENTORY.json; "
            "no new HTTP observation is claimed."
        ),
        "acquisition_recipe_mapping": (
            "The curator acquisition_recipe_or_snapshot_ref is represented by each "
            "manifest acquisition_url plus the fetch_recipe_only distribution boundary; "
            "the stale helper script is not authority."
        ),
        "license_inventory_ref": LICENSE_INVENTORY_REF,
        "license_inventory_rule": (
            "Every per-source manifest license block must exactly match the canonical "
            "repository license inventory entry with the same source_id."
        ),
        "whatwg_basis_mapping": (
            "The original curator present-tense redistribution statement remains in "
            "curator/SOURCE-INVENTORY.json and curator/LICENSE-INVENTORY.md. The "
            "canonical recipe-only manifest renders it conditionally because this "
            "repository distributes no source response body."
        ),
        "snapshot_distribution": "fetch_recipe_only",
    }
    for field, expected_value in expected_fixed_rules.items():
        if not _json_exact_equal(rules[field], expected_value):
            raise EvidenceInventoryError(
                f"curation provenance materialization rule differs: {field}"
            )
    for record in manifest.sources:
        expected_adapter = expected_adapter_mapping[record.family.value]
        if (
            record.adapter.value != expected_adapter["adapter"]
            or record.profile.value != expected_adapter["profile"]
            or record.adapter_version != rules["adapter_version"]
            or record.normalization_version != rules["normalization_version"]
            or record.identity_preflight_version != rules["identity_preflight_version"]
        ):
            raise EvidenceInventoryError(
                f"curation provenance adapter rules differ for {record.source_id}"
            )
    header_rule = _require_exact_keys(
        rules["header_sanitization"],
        {
            "report_ref",
            "report_sha256",
            "sanitizer_version",
            "policy",
            "value_policy",
            "original_header_identity_rule",
        },
        label="curation provenance header_sanitization",
    )
    if not _json_exact_equal(
        dict(header_rule),
        {
            "report_ref": HEADER_SANITIZATION_REF,
            "report_sha256": REPORT_SHA256,
            "sanitizer_version": SANITIZER_VERSION,
            "policy": ("ALLOWLIST_FIELDS__DROP_UNKNOWN_FIELDS__DROP_ALL_CONTINUATION_LINES"),
            "value_policy": (
                "BOUNDED_PRINTABLE_FIELD_SPECIFIC__FROZEN_LOCATION__CREDENTIAL_MARKER_REJECT"
            ),
            "original_header_identity_rule": (
                "Retain each original staging SHA-256 and byte length in the report; "
                "exclude all original response-header bytes and all sensitive values."
            ),
        },
    ):
        raise EvidenceInventoryError("curation provenance header sanitizer rule differs")
    timestamp_rule = _require_exact_keys(
        rules["timestamp_rule"],
        {
            "source_field",
            "target_field",
            "operation",
            "rounding",
            "precision_loss_documented",
        },
        label="curation provenance timestamp_rule",
    )
    if not _json_exact_equal(
        dict(timestamp_rule),
        {
            "source_field": "retrieved_at_utc",
            "target_field": "curator_retrieved_at_utc",
            "operation": "truncate fractional seconds to the preceding whole second",
            "rounding": False,
            "precision_loss_documented": True,
        },
    ):
        raise EvidenceInventoryError("curation provenance timestamp rule differs")

    raw_curator_sources = curator_inventory.get("sources")
    if not isinstance(raw_curator_sources, list):
        raise EvidenceInventoryError("curator sources are unavailable for provenance")
    curator_sources_by_id = {
        source.get("source_id"): source
        for source in raw_curator_sources
        if isinstance(source, dict)
    }
    expected_acquisition_mappings = [
        {
            "source_id": record.source_id,
            "curator_acquisition_recipe_or_snapshot_ref": curator_sources_by_id[
                record.source_id
            ].get("acquisition_recipe_or_snapshot_ref"),
            "materialized_acquisition_url": record.acquisition_url,
            "snapshot_distribution": record.snapshot_distribution,
            "response_body_in_repository": False,
        }
        for record in manifest.sources
    ]
    if not _json_exact_equal(obj["acquisition_recipe_mappings"], expected_acquisition_mappings):
        raise EvidenceInventoryError("curation provenance acquisition recipe mappings differ")
    originals = {
        source.get("source_id"): source.get("retrieved_at_utc")
        for source in raw_curator_sources
        if isinstance(source, dict)
    }
    raw_mappings = obj["timestamp_mappings"]
    if not isinstance(raw_mappings, list) or len(raw_mappings) != len(manifest.sources):
        raise EvidenceInventoryError("curation provenance timestamp mapping set differs")
    expected_mappings = [
        {
            "source_id": record.source_id,
            "original": originals.get(record.source_id),
            "materialized": record.curator_retrieved_at_utc,
        }
        for record in manifest.sources
    ]
    if not _json_exact_equal(raw_mappings, expected_mappings):
        raise EvidenceInventoryError("curation provenance timestamp mappings differ")

    boundary = _require_exact_keys(
        obj["repository_boundary"],
        {
            "included",
            "excluded",
            "rejected_helper",
            "repository_readme_sha256",
            "candidate_executed",
            "labels_or_gold_included",
            "split_or_holdout_membership_included",
            "predictions_or_scores_included",
            "m1_acceptance_implication",
        },
        label="curation provenance repository_boundary",
    )
    expected_included = [
        (
            "Canonical acquisition recipes with exact official URLs, prior response "
            "headers, content SHA-256 values, byte lengths, adapter identities, and "
            "license bases"
        ),
        (
            "Exact independent curation inventory, report, and license inventory bytes "
            "plus the hash identity of their partial historical checksum file"
        ),
        (
            "Twenty-seven hash-linked sanitized source, replay, license, policy, and "
            "chain-evidence HTTP header records plus their original-to-sanitized "
            "identity map"
        ),
    ]
    expected_excluded = [
        "All raw and replay standards bytes",
        "All frozen license-page bytes",
        "All original unsanitized HTTP response-header bytes and sensitive header values",
        ("All labels, gold records, split membership, predictions, scores, and acceptance outputs"),
    ]
    if not _json_exact_equal(boundary["included"], expected_included) or not (
        _json_exact_equal(boundary["excluded"], expected_excluded)
    ):
        raise EvidenceInventoryError("curation provenance repository lists differ")
    rejected_helper = _require_exact_keys(
        boundary["rejected_helper"],
        {"name", "sha256", "status", "reason"},
        label="curation provenance rejected_helper",
    )
    if not _json_exact_equal(
        dict(rejected_helper),
        {
            "name": "acquire.ps1",
            "sha256": _REJECTED_HELPER_SHA256,
            "status": "REJECTED_NOT_IMPORTED",
            "reason": (
                "The historical helper is not the canonical ten-source fail-closed "
                "acquisition path. Use normshift corpus acquire with the frozen manifest "
                "digest instead."
            ),
        },
    ):
        raise EvidenceInventoryError("curation provenance rejected helper differs")
    if not _json_exact_equal(boundary["repository_readme_sha256"], _README_SHA256):
        raise EvidenceInventoryError("curation provenance README identity differs")
    actual_readme_sha256 = _sha256(_read_inventory_content(root, inventory, README_REF))
    if not hmac.compare_digest(actual_readme_sha256, _README_SHA256):
        raise EvidenceInventoryError("repository evidence README SHA-256 differs")
    expected_flags = {
        "candidate_executed": False,
        "labels_or_gold_included": False,
        "split_or_holdout_membership_included": False,
        "predictions_or_scores_included": False,
        "m1_acceptance_implication": "NONE",
    }
    for field, expected_value in expected_flags.items():
        if not _json_exact_equal(boundary[field], expected_value):
            raise EvidenceInventoryError(
                f"curation provenance repository boundary differs: {field}"
            )

    actual_content_refs = set(inventory.content_refs)
    header_refs = {ref for ref in actual_content_refs if ref.startswith("curation-headers/")}
    if len(header_refs) != 27 or actual_content_refs != (
        set(_FIXED_NON_HEADER_CONTENT_REFS) | header_refs
    ):
        raise EvidenceInventoryError("curation provenance evidence content set differs")


def _validate_header_sanitization(
    root: Path,
    inventory: EvidenceInventoryResult,
) -> None:
    payload = _load_canonical_json_content(root, inventory, HEADER_SANITIZATION_REF)
    if not hmac.compare_digest(
        _sha256(_read_inventory_content(root, inventory, HEADER_SANITIZATION_REF)),
        REPORT_SHA256,
    ):
        raise EvidenceInventoryError("header sanitization report SHA-256 differs")
    obj = _require_exact_keys(
        payload,
        {
            "schema_version",
            "sanitizer_version",
            "status",
            "allowed_field_names",
            "explicitly_forbidden_field_names",
            "unknown_field_policy",
            "continuation_policy",
            "value_policy",
            "raw_response_bodies_included",
            "sensitive_header_values_included",
            "files",
        },
        label="header sanitization report",
    )
    expected_identity = (
        "normshift-m1-header-sanitization/v1",
        SANITIZER_VERSION,
        "SANITIZED_ALLOWLIST_HEADER_PROVENANCE_ONLY",
    )
    if (
        obj["schema_version"],
        obj["sanitizer_version"],
        obj["status"],
    ) != expected_identity:
        raise EvidenceInventoryError("header sanitizer identity or status differs")
    if obj["allowed_field_names"] != sorted(ALLOWED_FIELDS):
        raise EvidenceInventoryError("header sanitizer allowlist differs")
    if obj["explicitly_forbidden_field_names"] != sorted(EXPLICITLY_FORBIDDEN_FIELDS):
        raise EvidenceInventoryError("header sanitizer forbidden-field list differs")
    if obj["unknown_field_policy"] != "DROP_ENTIRE_FIELD_AND_CONTINUATIONS":
        raise EvidenceInventoryError("header sanitizer must drop every unknown field")
    if obj["continuation_policy"] != "DROP_ALL_CONTINUATION_LINES":
        raise EvidenceInventoryError("header sanitizer must drop every continuation line")
    if obj["value_policy"] != (
        "BOUNDED_PRINTABLE_FIELD_SPECIFIC__FROZEN_LOCATION__CREDENTIAL_MARKER_REJECT"
    ):
        raise EvidenceInventoryError("header sanitizer value policy differs")
    if obj["raw_response_bodies_included"] is not False or (
        obj["sensitive_header_values_included"] is not False
    ):
        raise EvidenceInventoryError("header sanitizer report crosses repository boundary")

    raw_files = obj["files"]
    if not isinstance(raw_files, list) or len(raw_files) != 27:
        raise EvidenceInventoryError("header sanitizer must bind exactly 27 files")
    source_refs: set[str] = set()
    output_refs: set[str] = set()
    ordered_output_refs: list[str] = []
    for index, raw_record in enumerate(raw_files):
        record = _require_exact_keys(
            raw_record,
            {
                "source_ref",
                "output_ref",
                "original_sha256",
                "original_byte_length",
                "sanitized_sha256",
                "sanitized_byte_length",
                "removed_field_names",
                "retained_field_names",
            },
            label=f"header sanitization files[{index}]",
        )
        source_ref = record["source_ref"]
        output_ref = record["output_ref"]
        if not isinstance(source_ref, str) or not isinstance(output_ref, str):
            raise EvidenceInventoryError("header sanitizer refs must be strings")
        _validate_evidence_ref(source_ref, label="header sanitizer source_ref")
        _validate_evidence_ref(output_ref, label="header sanitizer output_ref")
        if (
            source_ref in source_refs
            or output_ref in output_refs
            or not output_ref.startswith("curation-headers/")
            or not output_ref.endswith(".headers.txt")
        ):
            raise EvidenceInventoryError("header sanitizer refs are not unique header refs")
        source_refs.add(source_ref)
        output_refs.add(output_ref)
        ordered_output_refs.append(output_ref)
        if HEADER_SOURCE_REF_BY_OUTPUT.get(output_ref) != source_ref:
            raise EvidenceInventoryError(
                f"header sanitizer frozen source ref differs for {output_ref}"
            )

        original_sha256 = record["original_sha256"]
        sanitized_sha256 = record["sanitized_sha256"]
        original_length = record["original_byte_length"]
        sanitized_length = record["sanitized_byte_length"]
        if (
            not isinstance(original_sha256, str)
            or not _SHA256_RE.fullmatch(original_sha256)
            or not isinstance(sanitized_sha256, str)
            or not _SHA256_RE.fullmatch(sanitized_sha256)
        ):
            raise EvidenceInventoryError("header sanitizer SHA-256 identity is invalid")
        for label, value in (
            ("original", original_length),
            ("sanitized", sanitized_length),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise EvidenceInventoryError(
                    f"header sanitizer {label} byte length must be positive"
                )
        expected_header_identity = HEADER_IDENTITY_BY_OUTPUT.get(output_ref)
        if (
            expected_header_identity is None
            or (
                original_sha256,
                original_length,
                sanitized_sha256,
                sanitized_length,
            )
            != expected_header_identity
        ):
            raise EvidenceInventoryError(
                f"header sanitizer frozen identity differs for {output_ref}"
            )

        removed = record["removed_field_names"]
        retained = record["retained_field_names"]
        if (
            not isinstance(removed, list)
            or not isinstance(retained, list)
            or not all(isinstance(field, str) for field in removed + retained)
            or removed != sorted(set(removed))
            or retained != sorted(set(retained))
            or set(removed) & set(retained)
            or not set(retained).issubset(ALLOWED_FIELDS)
        ):
            raise EvidenceInventoryError("header sanitizer field-name sets are invalid")

        raw = _read_inventory_content(root, inventory, output_ref)
        if len(raw) != sanitized_length or not hmac.compare_digest(_sha256(raw), sanitized_sha256):
            raise EvidenceInventoryError(f"sanitized header identity differs for {output_ref}")
        try:
            actual_fields = validate_sanitized_header_bytes(
                raw,
                source_ref=output_ref,
            )
        except HeaderSanitizationError as exc:
            raise EvidenceInventoryError(
                f"sanitized header contract rejected for {output_ref}: {exc}"
            ) from exc
        if actual_fields != frozenset(retained):
            raise EvidenceInventoryError(f"sanitized header field report differs for {output_ref}")

    bound_headers = {ref for ref in inventory.content_refs if ref.startswith("curation-headers/")}
    if output_refs != bound_headers:
        raise EvidenceInventoryError("header sanitizer output set differs from evidence root")
    if output_refs != set(HEADER_IDENTITY_BY_OUTPUT):
        raise EvidenceInventoryError("header sanitizer output set differs from frozen identities")
    if ordered_output_refs != sorted(HEADER_IDENTITY_BY_OUTPUT, key=str.encode):
        raise EvidenceInventoryError("header sanitizer file order differs")


def _validate_license_inventory(
    root: Path,
    inventory: EvidenceInventoryResult,
    manifest: SourceManifest,
    curator_inventory: Mapping[str, Any],
) -> None:
    payload = _load_strict_json_content(root, inventory, LICENSE_INVENTORY_REF)
    obj = _require_exact_keys(
        payload,
        {
            "schema_version",
            "status",
            "source_curation_license_inventory_sha256",
            "repository_distribution",
            "entries",
            "license_evidence",
            "future_sources_authorized",
            "legal_advice",
        },
        label="license inventory",
    )
    if obj["schema_version"] != "normshift-m1-development-license-inventory/v1":
        raise EvidenceInventoryError("unsupported development license inventory schema")
    if obj["status"] != "CURATOR_ASSERTIONS_FOR_FROZEN_DEVELOPMENT_RECIPES_ONLY":
        raise EvidenceInventoryError("license inventory has an invalid status ceiling")
    curation_sha = obj["source_curation_license_inventory_sha256"]
    if not isinstance(curation_sha, str) or not _SHA256_RE.fullmatch(curation_sha):
        raise EvidenceInventoryError("license inventory curation SHA-256 is invalid")
    actual_curation_sha = _sha256(
        _read_inventory_content(root, inventory, CURATOR_LICENSE_INVENTORY_REF)
    )
    if not hmac.compare_digest(curation_sha, actual_curation_sha) or not hmac.compare_digest(
        curation_sha, _CURATOR_LICENSE_INVENTORY_SHA256
    ):
        raise EvidenceInventoryError(
            "license inventory curator Markdown SHA-256 differs from copied bytes"
        )
    if obj["repository_distribution"] != "FETCH_RECIPE_ONLY_NO_RESPONSE_BODIES":
        raise EvidenceInventoryError("license inventory repository boundary is invalid")
    if obj["future_sources_authorized"] is not False or obj["legal_advice"] is not False:
        raise EvidenceInventoryError(
            "license inventory must not authorize future sources or advice"
        )

    raw_entries = obj["entries"]
    if not isinstance(raw_entries, list):
        raise EvidenceInventoryError("license inventory entries must be an array")
    entries: dict[str, Mapping[str, Any]] = {}
    for index, raw_entry in enumerate(raw_entries):
        entry = _require_exact_keys(
            raw_entry,
            {
                "source_id",
                "document_or_license",
                "url",
                "redistribution_basis",
                "snapshot_distribution",
            },
            label=f"license inventory entries[{index}]",
        )
        source_id = entry["source_id"]
        if not isinstance(source_id, str) or source_id in entries:
            raise EvidenceInventoryError("license inventory source IDs must be unique strings")
        entries[source_id] = entry
    manifest_ids = {source_record.source_id for source_record in manifest.sources}
    if set(entries) != manifest_ids:
        raise EvidenceInventoryError("license inventory source set differs from manifest")
    for source_record in manifest.sources:
        entry = entries[source_record.source_id]
        expected = {
            "source_id": source_record.source_id,
            "document_or_license": source_record.license_name,
            "url": source_record.license_url,
            "redistribution_basis": source_record.redistribution_basis,
            "snapshot_distribution": source_record.snapshot_distribution,
        }
        if not _json_exact_equal(dict(entry), expected):
            raise EvidenceInventoryError(
                f"license inventory differs from manifest for {source_record.source_id}"
            )

    raw_evidence = obj["license_evidence"]
    if not isinstance(raw_evidence, list) or len(raw_evidence) != 5:
        raise EvidenceInventoryError("license inventory must bind exactly five evidence identities")
    raw_curator_evidence = curator_inventory.get("license_evidence")
    if not isinstance(raw_curator_evidence, list) or len(raw_curator_evidence) != 5:
        raise EvidenceInventoryError("curator license evidence set differs")
    curator_evidence: dict[str, Mapping[str, Any]] = {}
    for raw_curator_record in raw_curator_evidence:
        if not isinstance(raw_curator_record, dict):
            raise EvidenceInventoryError("curator license evidence must contain objects")
        curator_id = raw_curator_record.get("id")
        if not isinstance(curator_id, str) or curator_id.lower() in curator_evidence:
            raise EvidenceInventoryError("curator license evidence IDs must be unique")
        curator_evidence[curator_id.lower()] = cast(Mapping[str, Any], raw_curator_record)
    evidence_ids: set[str] = set()
    evidence_hashes: set[str] = set()
    for index, raw_record in enumerate(raw_evidence):
        evidence_record = _require_exact_keys(
            raw_record,
            {"evidence_id", "url", "sha256", "byte_length", "body_in_repository"},
            label=f"license evidence[{index}]",
        )
        evidence_id = evidence_record["evidence_id"]
        digest = evidence_record["sha256"]
        byte_length = evidence_record["byte_length"]
        url = evidence_record["url"]
        if not isinstance(evidence_id, str) or not evidence_id or evidence_id in evidence_ids:
            raise EvidenceInventoryError("license evidence IDs must be unique strings")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise EvidenceInventoryError("license evidence SHA-256 is invalid")
        if digest in evidence_hashes:
            raise EvidenceInventoryError("license evidence SHA-256 values must be unique")
        if not isinstance(byte_length, int) or isinstance(byte_length, bool) or byte_length <= 0:
            raise EvidenceInventoryError("license evidence byte length must be positive")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise EvidenceInventoryError("license evidence URL must use HTTPS")
        if evidence_record["body_in_repository"] is not False:
            raise EvidenceInventoryError("license evidence response bodies must remain excluded")
        curator_record = curator_evidence.get(evidence_id)
        if curator_record is None or (
            curator_record.get("url") != url
            or curator_record.get("sha256") != digest
            or curator_record.get("byte_length") != byte_length
        ):
            raise EvidenceInventoryError(
                f"license evidence differs from curator inventory for {evidence_id}"
            )
        evidence_ids.add(evidence_id)
        evidence_hashes.add(digest)
    if evidence_ids != set(curator_evidence):
        raise EvidenceInventoryError("license evidence IDs differ from curator inventory")


def verify_source_recipe_evidence(
    evidence_root: Path,
    *,
    expected_inventory_sha256: str,
    expected_manifest_sha256: str,
    acceptance_policy_path: Path,
) -> SourceRecipeEvidenceResult:
    """Verify repository evidence and strictly load its development-only recipes."""
    exact_root = _absolute_unaliased_root(evidence_root)
    inventory = verify_evidence_root(
        exact_root,
        expected_inventory_sha256=expected_inventory_sha256,
    )
    if SOURCE_MANIFEST_REF not in inventory.content_refs:
        raise EvidenceInventoryError(f"evidence inventory does not bind {SOURCE_MANIFEST_REF}")
    _load_canonical_json_content(exact_root, inventory, SOURCE_MANIFEST_REF)
    manifest: SourceManifest = load_source_manifest(
        exact_root / SOURCE_MANIFEST_REF,
        expected_sha256=expected_manifest_sha256,
        acceptance_policy_path=acceptance_policy_path,
    )
    if manifest.corpus_kind != "ACTUAL_STANDARDS_SOURCE_CONTRACT":
        raise EvidenceInventoryError("recipe evidence must use an actual-source contract")
    non_recipe_sources = [
        record.source_id
        for record in manifest.sources
        if record.snapshot_distribution != "fetch_recipe_only"
    ]
    if non_recipe_sources:
        raise EvidenceInventoryError(
            "repository recipe evidence must not claim embedded source snapshots: "
            + ", ".join(non_recipe_sources)
        )
    curator_inventory = _validate_curator_inventory(exact_root, inventory, manifest)
    _validate_header_sanitization(exact_root, inventory)
    _validate_curation_provenance(
        exact_root,
        inventory,
        manifest,
        curator_inventory,
    )
    _validate_license_inventory(
        exact_root,
        inventory,
        manifest,
        curator_inventory,
    )
    final_inventory = verify_evidence_root(
        exact_root,
        expected_inventory_sha256=expected_inventory_sha256,
    )
    if final_inventory != inventory:
        raise EvidenceInventoryError(
            "evidence root changed while the manifest and license inventory were loaded"
        )
    return SourceRecipeEvidenceResult(
        inventory_sha256=inventory.inventory_sha256,
        manifest_sha256=manifest.manifest_sha256,
        corpus_id=manifest.corpus_id,
        source_count=len(manifest.sources),
        families=tuple(sorted({record.family.value for record in manifest.sources})),
    )
