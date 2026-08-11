"""Hash-frozen M1 source acquisition and network-free replay.

This module deliberately does not contain labels, thresholds, or measurement.
It establishes only the source/provenance boundary that must exist before an
independent reviewer may freeze an acceptance policy and labeled corpus.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
import unicodedata
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from http.client import HTTPMessage
from importlib import resources
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Final, cast
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator

from normshift.adapters.base import (
    ADAPTER_VERSION,
    NORMALIZATION_VERSION,
    AdaptedDocument,
    SourceAdapter,
)
from normshift.adapters.errors import AdapterError
from normshift.adapters.rfc_adapter import RfcAdapter
from normshift.adapters.w3c_adapter import W3cAdapter
from normshift.adapters.whatwg_adapter import WhatwgAdapter
from normshift.io_safety import assert_outputs_safe, write_transaction
from normshift.model.types import AdapterName, DocumentFamily, ProfileName
from normshift.portable_ref import (
    PortableRefError,
    resolve_declared_under_root,
    validate_portable_ref,
)
from normshift.strict_json import StrictJSONError, strict_loads

MANIFEST_SCHEMA_VERSION: Final = "normshift-m1-source-manifest/v1"
RECEIPT_SCHEMA_VERSION: Final = "normshift-m1-source-receipt/v1"
MANIFEST_SCHEMA_NAME: Final = "m1_source_manifest_v1.schema.json"
FROZEN_POLICY_ID: Final = "normshift-m1-m2-prereg-v1"
FROZEN_POLICY_SHA256: Final = (
    "0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773"
)
FROZEN_POLICY_REF: Final = "acceptance/m1_m2_prereg_v1.json"
SOURCE_IDENTITY_PREFLIGHT_VERSION: Final = "1.0.0"
MAX_MANIFEST_BYTES: Final = 4 * 1024 * 1024
MAX_POLICY_BYTES: Final = 2 * 1024 * 1024
MAX_SOURCE_COUNT: Final = 24
MAX_SOURCE_BYTES: Final = 64 * 1024 * 1024
MAX_TOTAL_SOURCE_BYTES: Final = 256 * 1024 * 1024
MAX_REDIRECTS: Final = 5
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_ID_RE: Final = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_MEDIA_TYPE_RE: Final = re.compile(r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+$")


class AcquisitionError(ValueError):
    """The acquisition contract could not be proven; no success is allowed."""


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    family: DocumentFamily
    adapter: AdapterName
    profile: ProfileName
    adapter_version: str
    normalization_version: str
    identity_preflight_version: str
    standard_id: str
    version_or_date: str
    document_version: str
    canonical_url: str
    acquisition_url: str
    curator_retrieved_at_utc: str
    redirect_chain: tuple[str, ...]
    etag: str | None
    last_modified: str | None
    media_type: str
    charset: str | None
    content_sha256: str
    byte_length: int
    local_ref: str
    license_name: str
    license_url: str | None
    redistribution_basis: str
    snapshot_distribution: str

    @property
    def metadata_ref(self) -> str:
        return f"{self.local_ref}.meta.json"

    @property
    def receipt_ref(self) -> str:
        return f"{self.local_ref}.receipt.json"


@dataclass(frozen=True)
class SourceManifest:
    corpus_id: str
    corpus_kind: str
    manifest_sha256: str
    acceptance_policy_id: str
    acceptance_policy_sha256: str
    acceptance_policy_ref: str
    sources: tuple[SourceRecord, ...]


@dataclass(frozen=True)
class FetchResult:
    """Exact response facts returned by a fetch implementation."""

    data: bytes
    redirect_chain: tuple[str, ...]
    etag: str | None
    last_modified: str | None
    content_type: str | None
    content_encoding: str | None
    content_length: str | None


@dataclass(frozen=True)
class CorpusReplayResult:
    manifest_sha256: str
    corpus_id: str
    source_count: int
    families: tuple[str, ...]
    mode: str


FetchFn = Callable[[SourceRecord], FetchResult]

_M1_ADAPTERS: Final[dict[DocumentFamily, SourceAdapter]] = {
    DocumentFamily.RFC: RfcAdapter(),
    DocumentFamily.W3C: W3cAdapter(),
    DocumentFamily.WHATWG: WhatwgAdapter(),
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_junction(path: Path) -> bool:
    checker = getattr(path, "is_junction", None)
    return bool(checker and checker())


def _read_regular_bounded(
    path: Path,
    *,
    label: str,
    max_bytes: int,
    expected_size: int | None = None,
) -> bytes:
    """Open one regular file and bound the read before allocating its contents."""
    candidate = Path(path)
    if candidate.is_symlink() or _is_junction(candidate):
        raise AcquisitionError(f"{label} must not be a symlink or junction: {candidate}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(candidate, flags)
    except OSError as exc:
        raise AcquisitionError(f"cannot open {label}: {exc}") from exc
    try:
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise AcquisitionError(f"{label} must be a regular file")
            if expected_size is not None and before.st_size != expected_size:
                raise AcquisitionError(
                    f"{label} size mismatch: expected {expected_size}, got {before.st_size}"
                )
            if before.st_size > max_bytes:
                raise AcquisitionError(f"{label} exceeds {max_bytes} bytes")
            limit = expected_size if expected_size is not None else max_bytes
            data = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
    except AcquisitionError:
        raise
    except OSError as exc:
        raise AcquisitionError(f"cannot read {label}: {exc}") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(data) != before.st_size:
        raise AcquisitionError(f"{label} changed during bounded read")
    return data


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
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


def _load_schema() -> Mapping[str, Any]:
    raw = resources.files("normshift.schemas").joinpath(MANIFEST_SCHEMA_NAME).read_bytes()
    try:
        payload = strict_loads(raw)
    except StrictJSONError as exc:  # pragma: no cover - trusted package corruption
        raise AcquisitionError(f"bundled manifest schema is invalid: {exc}") from exc
    if not isinstance(payload, dict):  # pragma: no cover - trusted package corruption
        raise AcquisitionError("bundled manifest schema root must be an object")
    return cast(dict[str, Any], payload)


def _schema_validate(payload: Any) -> None:
    validator = Draft202012Validator(_load_schema())
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.absolute_path))
    if not errors:
        return
    rendered: list[str] = []
    for error in errors[:20]:
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path
        )
        rendered.append(f"{path}: {error.message}")
    if len(errors) > len(rendered):
        rendered.append(f"... {len(errors) - len(rendered)} more schema errors")
    raise AcquisitionError("manifest schema validation failed: " + "; ".join(rendered))


def _validate_https_url(value: str, *, label: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise AcquisitionError(f"{label}: invalid URL: {exc}") from exc
    if parsed.scheme != "https":
        raise AcquisitionError(f"{label}: only canonical https URLs are allowed")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise AcquisitionError(f"{label}: URL must have a host and no credentials")
    host_labels = parsed.hostname.split(".")
    if any(
        not part
        or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
        for part in host_labels
    ):
        raise AcquisitionError(f"{label}: host has non-canonical DNS labels")
    if parsed.hostname != parsed.hostname.lower() or port is not None:
        raise AcquisitionError(f"{label}: host must be lowercase and explicit ports are forbidden")
    if parsed.query or parsed.fragment:
        raise AcquisitionError(f"{label}: query strings and fragments are forbidden")
    if parsed.netloc != parsed.hostname:
        raise AcquisitionError(f"{label}: non-canonical authority spelling")
    if not parsed.path.startswith("/") or "\\" in parsed.path or "//" in parsed.path:
        raise AcquisitionError(f"{label}: path must be canonical absolute URL-path spelling")
    decoded_path = unquote(parsed.path)
    if any(part in {".", ".."} for part in decoded_path.split("/")):
        raise AcquisitionError(f"{label}: dot segments are forbidden")
    if any(ord(char) < 0x20 or char in {"\\", "\x7f"} for char in decoded_path):
        raise AcquisitionError(f"{label}: encoded controls or backslashes are forbidden")
    if "%2f" in parsed.path.lower() or "%5c" in parsed.path.lower():
        raise AcquisitionError(f"{label}: encoded path separators are forbidden")
    return value


def _validate_portable_output_ref(value: str, *, label: str) -> str:
    try:
        ref = validate_portable_ref(value)
    except PortableRefError as exc:
        raise AcquisitionError(f"{label}: {exc}") from exc
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{number}"
        for prefix in ("COM", "LPT")
        for number in range(1, 10)
    }
    for segment in ref.split("/"):
        if unicodedata.normalize("NFC", segment) != segment:
            raise AcquisitionError(f"{label}: path segments must use Unicode NFC")
        if segment.endswith((".", " ")) or ":" in segment:
            raise AcquisitionError(f"{label}: Windows-unsafe path segment {segment!r}")
        if any(ord(char) < 0x20 or ord(char) == 0x7F for char in segment):
            raise AcquisitionError(f"{label}: control character in path segment")
        if segment.split(".", 1)[0].upper() in reserved:
            raise AcquisitionError(f"{label}: reserved Windows device segment {segment!r}")
    return ref


def _validate_actual_source_identity(record: SourceRecord) -> None:
    """Constrain actual sources to immutable, family-authoritative URL forms."""
    parsed = urlsplit(record.canonical_url)
    host = parsed.hostname or ""
    path = parsed.path
    if record.family == DocumentFamily.RFC:
        match = re.fullmatch(r"/rfc/rfc([1-9][0-9]*)\.(?:html|xml|txt)", path)
        if host not in {"rfc-editor.org", "www.rfc-editor.org"} or match is None:
            raise AcquisitionError(
                f"{record.source_id}: RFC source must be an exact RFC Editor resource"
            )
        expected_standard_id = f"RFC {match.group(1)}"
        if record.standard_id != expected_standard_id:
            raise AcquisitionError(
                f"{record.source_id}: standard_id must equal {expected_standard_id!r}"
            )
        return
    if record.family == DocumentFamily.W3C:
        match = re.fullmatch(
            r"/TR/([0-9]{4})/(?:REC|PR|CR|WD)-[A-Za-z0-9._-]+-([0-9]{8})/",
            path,
        )
        if host not in {"w3.org", "www.w3.org"} or match is None:
            raise AcquisitionError(
                f"{record.source_id}: W3C source must be a dated W3C /TR/ version"
            )
        compact_date = record.version_or_date.replace("-", "")
        if compact_date != match.group(2):
            raise AcquisitionError(
                f"{record.source_id}: version_or_date must match the dated W3C URL"
            )
        return
    if record.family == DocumentFamily.WHATWG:
        commit = re.fullmatch(r"/commit-snapshots/([0-9a-f]{40})/", path)
        review = re.fullmatch(r"/review-drafts/([0-9]{4}-[0-9]{2})/", path)
        if not (host.endswith(".spec.whatwg.org") and (commit or review)):
            raise AcquisitionError(
                f"{record.source_id}: WHATWG source must be a frozen commit or review draft"
            )
        url_version = commit.group(1) if commit else cast(re.Match[str], review).group(1)
        if record.version_or_date != url_version:
            raise AcquisitionError(
                f"{record.source_id}: version_or_date must match the frozen WHATWG URL"
            )
        return
    raise AcquisitionError(f"{record.source_id}: unsupported actual source family")


def _require_utc(value: str, *, label: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise AcquisitionError(f"{label}: invalid UTC timestamp") from exc
    offset = parsed.utcoffset()
    if not value.endswith("Z") or offset is None or offset.total_seconds() != 0:
        raise AcquisitionError(f"{label}: timestamp must use UTC Z spelling")


def _require_http_date(value: str | None, *, label: str) -> None:
    if value is None:
        return
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError) as exc:
        raise AcquisitionError(f"{label}: invalid HTTP date") from exc
    if parsed.utcoffset() is None:
        raise AcquisitionError(f"{label}: HTTP date must include a timezone")


def _record_from_json(raw: Mapping[str, Any], index: int) -> SourceRecord:
    label = f"sources[{index}]"
    license_info = cast(Mapping[str, Any], raw["license"])
    record = SourceRecord(
        source_id=cast(str, raw["source_id"]),
        family=DocumentFamily(cast(str, raw["family"])),
        adapter=AdapterName(cast(str, raw["adapter"])),
        profile=ProfileName(cast(str, raw["profile"])),
        adapter_version=cast(str, raw["adapter_version"]),
        normalization_version=cast(str, raw["normalization_version"]),
        identity_preflight_version=cast(str, raw["identity_preflight_version"]),
        standard_id=cast(str, raw["standard_id"]),
        version_or_date=cast(str, raw["version_or_date"]),
        document_version=cast(str, raw["document_version"]),
        canonical_url=cast(str, raw["canonical_url"]),
        acquisition_url=cast(str, raw["acquisition_url"]),
        curator_retrieved_at_utc=cast(str, raw["curator_retrieved_at_utc"]),
        redirect_chain=tuple(cast(list[str], raw["redirect_chain"])),
        etag=cast(str | None, raw["etag"]),
        last_modified=cast(str | None, raw["last_modified"]),
        media_type=cast(str, raw["media_type"]),
        charset=cast(str | None, raw["charset"]),
        content_sha256=cast(str, raw["content_sha256"]),
        byte_length=cast(int, raw["byte_length"]),
        local_ref=cast(str, raw["local_ref"]),
        license_name=cast(str, license_info["document_or_license"]),
        license_url=cast(str | None, license_info["url"]),
        redistribution_basis=cast(str, license_info["redistribution_basis"]),
        snapshot_distribution=cast(str, license_info["snapshot_distribution"]),
    )

    if not _ID_RE.fullmatch(record.source_id):
        raise AcquisitionError(f"{label}.source_id: non-canonical identifier")
    if not _SHA256_RE.fullmatch(record.content_sha256):
        raise AcquisitionError(f"{label}.content_sha256: expected lowercase SHA-256")
    if not _MEDIA_TYPE_RE.fullmatch(record.media_type):
        raise AcquisitionError(f"{label}.media_type: expected lowercase media type")
    if record.charset is not None and (
        record.charset != record.charset.lower()
        or not re.fullmatch(r"[a-z0-9._-]+", record.charset)
    ):
        raise AcquisitionError(f"{label}.charset: expected canonical lowercase charset")
    if record.adapter_version != ADAPTER_VERSION:
        raise AcquisitionError(
            f"{label}.adapter_version: {record.adapter_version!r} != runtime {ADAPTER_VERSION!r}"
        )
    if record.normalization_version != NORMALIZATION_VERSION:
        raise AcquisitionError(
            f"{label}.normalization_version: {record.normalization_version!r} "
            f"!= runtime {NORMALIZATION_VERSION!r}"
        )
    if record.identity_preflight_version != SOURCE_IDENTITY_PREFLIGHT_VERSION:
        raise AcquisitionError(
            f"{label}.identity_preflight_version: "
            f"{record.identity_preflight_version!r} != runtime "
            f"{SOURCE_IDENTITY_PREFLIGHT_VERSION!r}"
        )
    family_contract = {
        DocumentFamily.RFC: (AdapterName.RFC, ProfileName.RFC2119),
        DocumentFamily.W3C: (AdapterName.W3C, ProfileName.RFC2119),
        DocumentFamily.WHATWG: (AdapterName.WHATWG, ProfileName.WHATWG),
    }
    if (record.adapter, record.profile) != family_contract[record.family]:
        raise AcquisitionError(
            f"{label}: family/adapter/profile contract mismatch for {record.family.value}"
        )
    _validate_portable_output_ref(record.local_ref, label=f"{label}.local_ref")
    _validate_https_url(record.canonical_url, label=f"{label}.canonical_url")
    _validate_https_url(record.acquisition_url, label=f"{label}.acquisition_url")
    if not record.redirect_chain or record.redirect_chain[0] != record.acquisition_url:
        raise AcquisitionError(f"{label}.redirect_chain: first URL must equal acquisition_url")
    if len(record.redirect_chain) > MAX_REDIRECTS + 1:
        raise AcquisitionError(f"{label}.redirect_chain: too many redirects")
    for redirect_index, url in enumerate(record.redirect_chain):
        _validate_https_url(url, label=f"{label}.redirect_chain[{redirect_index}]")
    if len(set(record.redirect_chain)) != len(record.redirect_chain):
        raise AcquisitionError(f"{label}.redirect_chain: redirect loops are forbidden")
    if record.canonical_url != record.redirect_chain[-1]:
        raise AcquisitionError(
            f"{label}.canonical_url: must equal the frozen final response URL"
        )
    _require_utc(
        record.curator_retrieved_at_utc,
        label=f"{label}.curator_retrieved_at_utc",
    )
    _require_http_date(record.last_modified, label=f"{label}.last_modified")
    if record.license_url is not None:
        _validate_https_url(record.license_url, label=f"{label}.license.url")
    return record


def _verify_acceptance_policy(
    path: Path,
    *,
    expected_id: str,
    expected_sha256: str,
) -> None:
    policy_path = Path(path)
    raw = _read_regular_bounded(
        policy_path,
        label="acceptance policy",
        max_bytes=MAX_POLICY_BYTES,
    )
    actual = _sha256(raw)
    if not hmac.compare_digest(actual, expected_sha256):
        raise AcquisitionError(
            f"acceptance policy SHA-256 mismatch: expected {expected_sha256}, got {actual}"
        )
    try:
        payload = strict_loads(raw)
    except StrictJSONError as exc:
        raise AcquisitionError(f"strict acceptance policy JSON rejected: {exc}") from exc
    if not isinstance(payload, dict):
        raise AcquisitionError("acceptance policy root must be an object")
    policy_id = payload.get("policy_id", payload.get("id"))
    if policy_id != expected_id:
        raise AcquisitionError(
            f"acceptance policy id mismatch: expected {expected_id!r}, got {policy_id!r}"
        )


def load_source_manifest(
    path: Path,
    *,
    expected_sha256: str,
    acceptance_policy_path: Path,
    allow_test_contract: bool = False,
) -> SourceManifest:
    """Strictly load a reviewer-frozen source manifest."""
    if not _SHA256_RE.fullmatch(expected_sha256):
        raise AcquisitionError("--manifest-sha256 must be a lowercase 64-hex digest")
    manifest_path = Path(path)
    raw = _read_regular_bounded(
        manifest_path,
        label="manifest",
        max_bytes=MAX_MANIFEST_BYTES,
    )
    actual_sha256 = _sha256(raw)
    if not hmac.compare_digest(actual_sha256, expected_sha256):
        raise AcquisitionError(
            f"manifest SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}"
        )
    try:
        payload = strict_loads(raw)
    except StrictJSONError as exc:
        raise AcquisitionError(f"strict manifest JSON rejected: {exc}") from exc
    _schema_validate(payload)
    if not isinstance(payload, dict):  # schema already enforces this
        raise AcquisitionError("manifest root must be an object")
    obj = cast(dict[str, Any], payload)
    if obj["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise AcquisitionError("unsupported M1 source manifest schema")
    corpus_kind = cast(str, obj["corpus_kind"])
    if corpus_kind == "SOURCE_CONTRACT_TEST" and not allow_test_contract:
        raise AcquisitionError("test-only source contracts are forbidden in production acquisition")
    policy = cast(Mapping[str, Any], obj["acceptance_policy"])
    policy_id = cast(str, policy["id"])
    policy_sha256 = cast(str, policy["sha256"])
    policy_ref = cast(str, policy["local_ref"])
    try:
        validate_portable_ref(policy_ref)
    except PortableRefError as exc:
        raise AcquisitionError(f"acceptance_policy.local_ref: {exc}") from exc
    policy_parts = tuple(Path(policy_ref).parts)
    supplied_parts = tuple(Path(acceptance_policy_path).parts)
    has_policy_suffix = len(supplied_parts) >= len(policy_parts) and (
        supplied_parts[-len(policy_parts) :] == policy_parts
    )
    if not has_policy_suffix:
        raise AcquisitionError(
            f"acceptance policy path must end with manifest local_ref {policy_ref!r}"
        )
    if corpus_kind == "ACTUAL_STANDARDS_SOURCE_CONTRACT" and (
        policy_id != FROZEN_POLICY_ID
        or policy_sha256 != FROZEN_POLICY_SHA256
        or policy_ref != FROZEN_POLICY_REF
    ):
        raise AcquisitionError("actual-source manifest does not bind the approved frozen policy")
    _verify_acceptance_policy(
        acceptance_policy_path,
        expected_id=policy_id,
        expected_sha256=policy_sha256,
    )

    records = tuple(
        _record_from_json(cast(Mapping[str, Any], item), index)
        for index, item in enumerate(cast(list[Any], obj["sources"]))
    )

    if len(records) > MAX_SOURCE_COUNT:
        raise AcquisitionError(f"source count exceeds {MAX_SOURCE_COUNT}")
    total_bytes = sum(record.byte_length for record in records)
    if any(record.byte_length > MAX_SOURCE_BYTES for record in records):
        raise AcquisitionError(f"source byte length exceeds {MAX_SOURCE_BYTES}")
    if total_bytes > MAX_TOTAL_SOURCE_BYTES:
        raise AcquisitionError(f"total source bytes exceed {MAX_TOTAL_SOURCE_BYTES}")

    source_ids: set[str] = set()
    versions: set[tuple[DocumentFamily, str, str]] = set()
    rfc_standard_ids: set[str] = set()
    actual_identity_values: dict[str, dict[str, str]] = {
        "content_sha256": {},
        "document_version": {},
        "canonical_url": {},
        "acquisition_url": {},
    }
    exact_output_refs: dict[str, str] = {}
    output_spellings: dict[str, str] = {}
    for record in records:
        if record.source_id in source_ids:
            raise AcquisitionError(f"duplicate source_id: {record.source_id}")
        source_ids.add(record.source_id)
        version_key = (record.family, record.standard_id, record.version_or_date)
        if version_key in versions:
            raise AcquisitionError(
                f"duplicate family/standard/version: {record.family.value}/"
                f"{record.standard_id}/{record.version_or_date}"
            )
        versions.add(version_key)
        if corpus_kind == "ACTUAL_STANDARDS_SOURCE_CONTRACT":
            _validate_actual_source_identity(record)
            if record.family == DocumentFamily.RFC:
                if record.standard_id in rfc_standard_ids:
                    raise AcquisitionError(
                        f"duplicate actual RFC standard_id: {record.standard_id!r}"
                    )
                rfc_standard_ids.add(record.standard_id)
            for field, value in (
                ("content_sha256", record.content_sha256),
                ("document_version", record.document_version),
                ("canonical_url", record.canonical_url),
                ("acquisition_url", record.acquisition_url),
            ):
                previous_source = actual_identity_values[field].get(value)
                if previous_source is not None:
                    raise AcquisitionError(
                        f"duplicate actual-source {field}: {value!r} "
                        f"for {record.source_id!r} and {previous_source!r}"
                    )
                actual_identity_values[field][value] = record.source_id
        for output_ref in (record.local_ref, record.metadata_ref, record.receipt_ref):
            _validate_portable_output_ref(
                output_ref,
                label=f"{record.source_id} output",
            )
            previous_exact = exact_output_refs.get(output_ref)
            if previous_exact is not None:
                raise AcquisitionError(
                    f"duplicate portable output ref: {output_ref!r} "
                    f"for {record.source_id!r} and {previous_exact!r}"
                )
            exact_output_refs[output_ref] = record.source_id

            parts = output_ref.split("/")
            for end in range(1, len(parts) + 1):
                spelling = "/".join(parts[:end])
                alias_key = unicodedata.normalize("NFKC", spelling).casefold()
                previous = output_spellings.get(alias_key)
                if previous is not None and previous != spelling:
                    raise AcquisitionError(
                        f"portable output spelling collision: {spelling!r} vs {previous!r}"
                    )
                output_spellings[alias_key] = spelling

    for output_ref in exact_output_refs:
        parts = output_ref.split("/")
        for end in range(1, len(parts)):
            parent_ref = "/".join(parts[:end])
            if parent_ref in exact_output_refs:
                raise AcquisitionError(
                    f"portable output file/directory collision: {parent_ref!r} "
                    f"is an ancestor of {output_ref!r}"
                )

    if corpus_kind == "ACTUAL_STANDARDS_SOURCE_CONTRACT":
        for family in (DocumentFamily.RFC, DocumentFamily.W3C, DocumentFamily.WHATWG):
            family_records = [record for record in records if record.family == family]
            distinct_fields: dict[str, set[Any]] = {
                "standard/version": {
                    (record.standard_id, record.version_or_date) for record in family_records
                },
                "document_version": {record.document_version for record in family_records},
                "content_sha256": {record.content_sha256 for record in family_records},
                "canonical_url": {record.canonical_url for record in family_records},
            }
            insufficient = [name for name, values in distinct_fields.items() if len(values) < 2]
            if insufficient:
                raise AcquisitionError(
                    f"actual corpus requires two distinct {family.value} values for: "
                    + ", ".join(insufficient)
                )

    return SourceManifest(
        corpus_id=cast(str, obj["corpus_id"]),
        corpus_kind=corpus_kind,
        manifest_sha256=actual_sha256,
        acceptance_policy_id=policy_id,
        acceptance_policy_sha256=policy_sha256,
        acceptance_policy_ref=policy_ref,
        sources=records,
    )


class _PinnedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, expected: tuple[str, ...]) -> None:
        super().__init__()
        self.expected = expected
        self.observed: list[str] = [expected[0]]

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        next_index = len(self.observed)
        if next_index >= len(self.expected) or newurl != self.expected[next_index]:
            raise AcquisitionError(
                f"unexpected redirect from {req.full_url!r} to {newurl!r}"
            )
        _validate_https_url(newurl, label="HTTP redirect target")
        self.observed.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_https(record: SourceRecord, *, timeout_seconds: float) -> FetchResult:
    handler = _PinnedRedirectHandler(record.redirect_chain)
    opener = urllib.request.build_opener(handler)
    request = urllib.request.Request(
        record.acquisition_url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
            "User-Agent": "NormShift-M1-Acquisition/1.0",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            status = getattr(response, "status", None)
            if status != 200:
                raise AcquisitionError(f"{record.source_id}: HTTP status {status!r}, expected 200")
            final_url = response.geturl()
            if final_url != record.redirect_chain[-1]:
                raise AcquisitionError(
                    f"{record.source_id}: final URL {final_url!r} "
                    "differs from frozen redirect chain"
                )
            data = response.read(record.byte_length + 1)
            return FetchResult(
                data=data,
                redirect_chain=tuple(handler.observed),
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                content_type=response.headers.get("Content-Type"),
                content_encoding=response.headers.get("Content-Encoding"),
                content_length=response.headers.get("Content-Length"),
            )
    except AcquisitionError:
        raise
    except (OSError, urllib.error.URLError) as exc:
        raise AcquisitionError(f"{record.source_id}: HTTPS acquisition failed: {exc}") from exc


def _validate_fetch(record: SourceRecord, result: FetchResult) -> None:
    label = record.source_id
    if result.redirect_chain != record.redirect_chain:
        raise AcquisitionError(f"{label}: observed redirect chain differs from manifest")
    if result.etag != record.etag:
        raise AcquisitionError(f"{label}: ETag differs from manifest")
    if result.last_modified != record.last_modified:
        raise AcquisitionError(f"{label}: Last-Modified differs from manifest")
    encoding = result.content_encoding.strip().lower() if result.content_encoding else "identity"
    if encoding != "identity":
        raise AcquisitionError(f"{label}: unsupported Content-Encoding {encoding!r}")
    if result.content_type is None:
        raise AcquisitionError(f"{label}: missing Content-Type")
    parts = [part.strip() for part in result.content_type.split(";")]
    media_type = parts[0].lower()
    charset_values: list[str] = []
    for parameter in parts[1:]:
        if "=" not in parameter:
            raise AcquisitionError(f"{label}: malformed Content-Type parameter")
        key, value = parameter.split("=", 1)
        if key.strip().lower() == "charset":
            normalized = value.strip().strip('"').lower()
            if not normalized:
                raise AcquisitionError(f"{label}: empty Content-Type charset")
            charset_values.append(normalized)
    if len(charset_values) > 1:
        raise AcquisitionError(f"{label}: duplicate Content-Type charset")
    charset = charset_values[0] if charset_values else None
    if media_type != record.media_type:
        raise AcquisitionError(
            f"{label}: media type {media_type!r} differs from manifest {record.media_type!r}"
        )
    if charset != record.charset:
        raise AcquisitionError(
            f"{label}: charset {charset!r} differs from manifest {record.charset!r}"
        )
    if result.content_length is not None:
        try:
            declared_length = int(result.content_length, 10)
        except ValueError as exc:
            raise AcquisitionError(f"{label}: invalid Content-Length") from exc
        if declared_length != record.byte_length:
            raise AcquisitionError(f"{label}: Content-Length differs from manifest")
    if len(result.data) != record.byte_length:
        raise AcquisitionError(
            f"{label}: byte length mismatch: expected {record.byte_length}, got {len(result.data)}"
        )
    actual_sha256 = _sha256(result.data)
    if not hmac.compare_digest(actual_sha256, record.content_sha256):
        raise AcquisitionError(
            f"{label}: content SHA-256 mismatch: expected {record.content_sha256}, "
            f"got {actual_sha256}"
        )
    try:
        adapted = _adapt_source_bytes(record, result.data)
    except AdapterError as exc:
        raise AcquisitionError(f"{label}: adapter preflight failed: {exc}") from exc
    if adapted.family != record.family:
        raise AcquisitionError(f"{label}: adapter returned the wrong document family")
    if adapted.document_version != record.document_version:
        raise AcquisitionError(
            f"{label}: adapter document version {adapted.document_version!r} "
            f"differs from manifest {record.document_version!r}"
        )


def _adapt_source_bytes(record: SourceRecord, data: bytes) -> AdaptedDocument:
    """Run the M1-only identity gate without ambient sidecars or M0 semantic changes."""
    adapter = _M1_ADAPTERS[record.family]
    with TemporaryDirectory(prefix="normshift-m1-preflight-") as directory:
        synthetic_path = Path(directory) / Path(record.local_ref).name
        if not adapter.can_handle(synthetic_path, data):
            raise AcquisitionError(
                f"{record.source_id}: source identity preflight rejected forced "
                f"{record.family.value} family"
            )
        return adapter.load(synthetic_path, data)


def _metadata_payload(record: SourceRecord, manifest_sha256: str) -> dict[str, str]:
    metadata = {
        "acquisition_url": record.acquisition_url,
        "canonical_source": record.canonical_url,
        "content_type": record.media_type,
        "charset": record.charset if record.charset is not None else "null",
        "document_family": record.family.value,
        "license_basis": record.redistribution_basis,
        "license_name": record.license_name,
        "local_source_ref": record.local_ref,
        "manifest_sha256": manifest_sha256,
        "curator_retrieved_at_utc": record.curator_retrieved_at_utc,
        "source_id": record.source_id,
        "standard_id": record.standard_id,
        "version_or_date": record.version_or_date,
    }
    if record.etag is not None:
        metadata["etag"] = record.etag
    if record.last_modified is not None:
        metadata["last_modified"] = record.last_modified
    if record.license_url is not None:
        metadata["license_url"] = record.license_url
    return metadata


def _receipt_payload(record: SourceRecord, manifest_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "source_id": record.source_id,
        "receipt_scope": "PINNED_REACQUISITION_NOT_ORIGINAL_HTTP_ATTESTATION",
        "assertion_authority": "FROZEN_SOURCE_MANIFEST_CURATOR",
        "source": {
            "canonical_url": record.canonical_url,
            "acquisition_url": record.acquisition_url,
            "curator_retrieved_at_utc": record.curator_retrieved_at_utc,
            "redirect_chain": list(record.redirect_chain),
            "etag": record.etag,
            "last_modified": record.last_modified,
            "media_type": record.media_type,
            "charset": record.charset,
        },
        "snapshot": {
            "local_ref": record.local_ref,
            "content_sha256": record.content_sha256,
            "byte_length": record.byte_length,
            "snapshot_distribution": record.snapshot_distribution,
        },
        "adapter": {
            "family": record.family.value,
            "adapter": record.adapter.value,
            "adapter_version": record.adapter_version,
            "normalization_version": record.normalization_version,
            "identity_preflight_version": record.identity_preflight_version,
            "profile": record.profile.value,
            "standard_id": record.standard_id,
            "version_or_date": record.version_or_date,
            "document_version": record.document_version,
        },
        "license": {
            "document_or_license": record.license_name,
            "url": record.license_url,
            "redistribution_basis": record.redistribution_basis,
        },
        "adjudication_status": "EXPERIMENTAL_NOT_ADJUDICATED",
    }


def _artifact_bytes(
    manifest: SourceManifest,
    fetched: Mapping[str, FetchResult],
) -> dict[str, bytes]:
    artifacts: dict[str, bytes] = {}
    for record in manifest.sources:
        record_artifacts = {
            record.local_ref: fetched[record.source_id].data,
            record.metadata_ref: _canonical_json(
                _metadata_payload(record, manifest.manifest_sha256)
            ),
            record.receipt_ref: _canonical_json(
                _receipt_payload(record, manifest.manifest_sha256)
            ),
        }
        for ref, data in record_artifacts.items():
            if ref in artifacts:
                raise AcquisitionError(f"duplicate generated artifact ref: {ref!r}")
            artifacts[ref] = data
    expected_count = 3 * len(manifest.sources)
    if len(artifacts) != expected_count:
        raise AcquisitionError(
            f"generated artifact count mismatch: expected {expected_count}, "
            f"got {len(artifacts)}"
        )
    return artifacts


def _root_path(root: Path) -> Path:
    candidate = Path(root)
    if candidate.is_symlink() or _is_junction(candidate) or not candidate.is_dir():
        raise AcquisitionError(
            f"snapshot root must be a regular non-link directory: {candidate}"
        )
    return candidate.resolve()


def _inventory(root: Path) -> set[str]:
    inventory: set[str] = set()

    def walk(directory: Path, prefix: str) -> None:
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as exc:
            raise AcquisitionError(f"cannot enumerate snapshot root: {exc}") from exc
        for entry in entries:
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            path = Path(entry.path)
            if entry.is_symlink() or _is_junction(path):
                raise AcquisitionError(f"snapshot root contains link: {relative}")
            if entry.is_file(follow_symlinks=False):
                inventory.add(f"file:{relative}")
            elif entry.is_dir(follow_symlinks=False):
                inventory.add(f"dir:{relative}")
                walk(path, relative)
            else:
                raise AcquisitionError(f"snapshot root contains non-file entry: {relative}")

    walk(root, "")
    return inventory


def _expected_inventory(refs: list[str]) -> set[str]:
    inventory: set[str] = {f"file:{ref}" for ref in refs}
    for ref in refs:
        parent = Path(ref).parent
        while parent.as_posix() not in {"", "."}:
            inventory.add(f"dir:{parent.as_posix()}")
            parent = parent.parent
    return inventory


def _result(manifest: SourceManifest, *, mode: str) -> CorpusReplayResult:
    return CorpusReplayResult(
        manifest_sha256=manifest.manifest_sha256,
        corpus_id=manifest.corpus_id,
        source_count=len(manifest.sources),
        families=tuple(sorted({record.family.value for record in manifest.sources})),
        mode=mode,
    )


def acquire_corpus(
    manifest_path: Path,
    snapshot_root: Path,
    *,
    manifest_sha256: str,
    acceptance_policy_path: Path,
    timeout_seconds: float = 30.0,
    fetcher: FetchFn | None = None,
    allow_test_contract: bool = False,
) -> CorpusReplayResult:
    """Acquire all pinned sources, then commit bytes + provenance atomically.

    Existing complete corpora are verified offline and never overwritten. Any
    partial pre-existing output fails closed. Network data is held until every
    source hash, header, redirect, encoding, adapter, and version check passes.
    """
    if timeout_seconds <= 0 or timeout_seconds > 300:
        raise AcquisitionError("timeout_seconds must be in (0, 300]")
    manifest = load_source_manifest(
        manifest_path,
        expected_sha256=manifest_sha256,
        acceptance_policy_path=acceptance_policy_path,
        allow_test_contract=allow_test_contract,
    )
    root = _root_path(snapshot_root)

    if fetcher is not None and (
        manifest.corpus_kind != "SOURCE_CONTRACT_TEST" or not allow_test_contract
    ):
        raise AcquisitionError(
            "custom fetchers are restricted to explicitly enabled source-contract tests"
        )

    refs = [
        ref
        for record in manifest.sources
        for ref in (record.local_ref, record.metadata_ref, record.receipt_ref)
    ]
    existing = _inventory(root)
    expected_inventory = _expected_inventory(refs)
    if existing:
        if existing != expected_inventory:
            raise AcquisitionError(
                "snapshot root contains a partial acquisition; refusing to mix states: "
                + ", ".join(sorted(existing ^ expected_inventory))
            )
        return verify_corpus_offline(
            manifest_path,
            root,
            manifest_sha256=manifest.manifest_sha256,
            acceptance_policy_path=acceptance_policy_path,
            allow_test_contract=allow_test_contract,
        )

    actual_fetcher = fetcher or (
        lambda record: _fetch_https(record, timeout_seconds=timeout_seconds)
    )
    fetched: dict[str, FetchResult] = {}
    for record in manifest.sources:
        try:
            result = actual_fetcher(record)
        except AcquisitionError:
            raise
        except Exception as exc:  # noqa: BLE001 - bounded fail-closed callback boundary
            raise AcquisitionError(f"{record.source_id}: fetcher failed: {exc}") from exc
        _validate_fetch(record, result)
        fetched[record.source_id] = result

    artifacts = _artifact_bytes(manifest, fetched)
    destinations = [root / Path(ref) for ref in artifacts]
    assert_outputs_safe(
        inputs=[Path(manifest_path), Path(acceptance_policy_path)],
        outputs=destinations,
        labels=list(artifacts),
    )
    write_transaction(
        {
            destination: artifacts[ref]
            for destination, ref in zip(destinations, artifacts, strict=True)
        }
    )
    verify_corpus_offline(
        manifest_path,
        root,
        manifest_sha256=manifest.manifest_sha256,
        acceptance_policy_path=acceptance_policy_path,
        allow_test_contract=allow_test_contract,
    )
    return _result(manifest, mode="ACQUIRED")


def verify_corpus_offline(
    manifest_path: Path,
    snapshot_root: Path,
    *,
    manifest_sha256: str,
    acceptance_policy_path: Path,
    allow_test_contract: bool = False,
) -> CorpusReplayResult:
    """Replay provenance and adapters from pinned local bytes without network."""
    manifest = load_source_manifest(
        manifest_path,
        expected_sha256=manifest_sha256,
        acceptance_policy_path=acceptance_policy_path,
        allow_test_contract=allow_test_contract,
    )
    root = _root_path(snapshot_root)
    expected_refs = [
        ref
        for record in manifest.sources
        for ref in (record.local_ref, record.metadata_ref, record.receipt_ref)
    ]
    expected_inventory = _expected_inventory(expected_refs)
    observed_inventory = _inventory(root)
    if observed_inventory != expected_inventory:
        raise AcquisitionError(
            "snapshot inventory differs from manifest: "
            + ", ".join(sorted(observed_inventory ^ expected_inventory))
        )
    for record in manifest.sources:
        try:
            source_path, _ = resolve_declared_under_root(root, record.local_ref)
            metadata_path, _ = resolve_declared_under_root(root, record.metadata_ref)
            receipt_path, _ = resolve_declared_under_root(root, record.receipt_ref)
        except PortableRefError as exc:
            raise AcquisitionError(
                f"{record.source_id}: unsafe or missing snapshot artifact: {exc}"
            ) from exc

        source_bytes = _read_regular_bounded(
            source_path,
            label=f"{record.source_id} source",
            max_bytes=MAX_SOURCE_BYTES,
            expected_size=record.byte_length,
        )
        if len(source_bytes) != record.byte_length or not hmac.compare_digest(
            _sha256(source_bytes), record.content_sha256
        ):
            raise AcquisitionError(f"{record.source_id}: offline source bytes differ from manifest")
        expected_metadata = _canonical_json(
            _metadata_payload(record, manifest.manifest_sha256)
        )
        actual_metadata = _read_regular_bounded(
            metadata_path,
            label=f"{record.source_id} metadata",
            max_bytes=len(expected_metadata),
            expected_size=len(expected_metadata),
        )
        if actual_metadata != expected_metadata:
            raise AcquisitionError(f"{record.source_id}: provenance metadata differs from manifest")
        expected_receipt = _canonical_json(
            _receipt_payload(record, manifest.manifest_sha256)
        )
        actual_receipt = _read_regular_bounded(
            receipt_path,
            label=f"{record.source_id} receipt",
            max_bytes=len(expected_receipt),
            expected_size=len(expected_receipt),
        )
        if actual_receipt != expected_receipt:
            raise AcquisitionError(f"{record.source_id}: acquisition receipt differs from manifest")

        try:
            adapted = _adapt_source_bytes(record, source_bytes)
        except AdapterError as exc:
            raise AcquisitionError(
                f"{record.source_id}: offline adapter replay failed: {exc}"
            ) from exc
        provenance = adapted.provenance
        expected = (
            adapted.family == record.family,
            adapted.document_version == record.document_version,
            provenance.content_sha256 == record.content_sha256,
            provenance.byte_length == record.byte_length,
            provenance.content_type == record.media_type,
            provenance.adapter_id == f"normshift.adapters.{record.adapter.value}",
            provenance.adapter_version == record.adapter_version,
            provenance.normalization_version == record.normalization_version,
        )
        if not all(expected):
            raise AcquisitionError(f"{record.source_id}: offline provenance replay mismatch")
    return _result(manifest, mode="OFFLINE_VERIFIED")
