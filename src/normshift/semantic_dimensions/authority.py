"""Source-replayed authority for semantic-dimension construction."""

from __future__ import annotations

import hashlib
import math
import os
import re
import stat
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from normshift import __version__
from normshift.evidence.hashing import canonical_json_bytes, evidence_hash, integrity_payload_hash
from normshift.extract.extractor import fingerprint_requirement
from normshift.model.types import (
    Change,
    ChangeClassification,
    DocumentSnapshot,
    Polarity,
    Report,
    Requirement,
)
from normshift.portable_ref import (
    PortableRefError,
    resolve_declared_under_root,
    validate_portable_ref,
)
from normshift.semantic_dimensions.errors import SemanticDimensionsError
from normshift.semantic_dimensions.models import canonical_sha256
from normshift.strict_json import StrictJSONError, deep_require_keys, strict_loads
from normshift.verify.verifier import VerifyResult, verify_report_file

FULL_REPLAY_AUTHORITY_KIND: Literal["FULL_REPORT_REPLAY"] = "FULL_REPORT_REPLAY"
FULL_VERIFICATION_RECEIPT_SCHEMA_VERSION: Literal[
    "normshift-full-report-verification-receipt/v1"
] = "normshift-full-report-verification-receipt/v1"
MAX_AUTHORITY_REPORT_BYTES = 50_000_000
MAX_AUTHORITY_SOURCE_BYTES = 100_000_000
MAX_VERIFICATION_RECEIPT_BYTES = 100_000
FULL_VERIFICATION_RECEIPT_SCHEMA_ID = (
    "https://normshift.local/schemas/full_verification_receipt_v1.schema.json"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA256_SCHEMA_PATTERN = r"^[0-9a-f]{64}$"
_PORTABLE_REF_SCHEMA_PATTERN = (
    r"^(?!/)(?![A-Za-z]:)(?![A-Za-z][A-Za-z0-9+.-]*:)"
    r"(?!.*://)(?!.*\\)(?!.*//)(?!\.{1,2}(?:/|$))"
    r"(?!.*(?:/\.{1,2})(?:/|$)).+$"
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def _require_sha256(value: str, *, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _portable_alias_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


class VerifiedSourceBinding(_StrictModel):
    """One portable source identity established by a FULL replay."""

    source_ref: str = Field(
        min_length=1,
        json_schema_extra={"pattern": _PORTABLE_REF_SCHEMA_PATTERN},
    )
    content_sha256: str = Field(pattern=_SHA256_SCHEMA_PATTERN)
    byte_length: int = Field(ge=0, le=MAX_AUTHORITY_SOURCE_BYTES)
    document_version: str = Field(min_length=1)
    source_ref_mode: Literal["source_root_relative"]

    @field_validator("source_ref")
    @classmethod
    def _validate_source_ref(cls, value: str) -> str:
        try:
            return validate_portable_ref(value)
        except PortableRefError as exc:
            raise ValueError(f"source_ref is not a canonical portable ref: {exc}") from exc

    @model_validator(mode="after")
    def _validate_binding(self) -> Self:
        _require_sha256(self.content_sha256, field_name="content_sha256")
        return self


class FullVerificationReceipt(_StrictModel):
    """Canonical deterministic receipt for an exact FULL report replay."""

    schema_version: Literal["normshift-full-report-verification-receipt/v1"]
    authority_kind: Literal["FULL_REPORT_REPLAY"]
    verification_scope: Literal["FULL"]
    result: Literal["OK"]
    verifier_id: Literal["normshift.verify.verifier.verify_report_file"]
    verifier_version: str = Field(min_length=1)
    report_file_sha256: str = Field(pattern=_SHA256_SCHEMA_PATTERN)
    report_content_sha256: str = Field(pattern=_SHA256_SCHEMA_PATTERN)
    report_schema_version: str = Field(min_length=1)
    report_tool_version: str = Field(min_length=1)
    old_source: VerifiedSourceBinding
    new_source: VerifiedSourceBinding
    receipt_payload_sha256: str = Field(pattern=_SHA256_SCHEMA_PATTERN)

    @model_validator(mode="after")
    def _validate_receipt(self) -> Self:
        for field_name in (
            "report_file_sha256",
            "report_content_sha256",
            "receipt_payload_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name=field_name)
        payload = self.model_dump(mode="json", exclude={"receipt_payload_sha256"})
        if self.receipt_payload_sha256 != canonical_sha256(payload):
            raise ValueError("receipt_payload_sha256 does not bind the FULL receipt")
        old_ref = self.old_source.source_ref
        new_ref = self.new_source.source_ref
        if old_ref != new_ref and _portable_alias_key(old_ref) == _portable_alias_key(new_ref):
            raise ValueError("old/new source_ref values are cross-platform aliases")
        return self


def full_verification_receipt_json_schema() -> dict[str, Any]:
    """Return the deterministic strict Draft 2020-12 receipt schema."""
    schema = FullVerificationReceipt.model_json_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FULL_VERIFICATION_RECEIPT_SCHEMA_ID,
        **schema,
    }


def canonical_report_sha256(report: Report) -> str:
    """Hash the complete canonical report, including its integrity envelope."""
    return hashlib.sha256(canonical_json_bytes(report.model_dump(mode="json"))).hexdigest()


def canonical_change_sha256(change: Change) -> str:
    """Hash every typed primary ``Change`` field."""
    return canonical_sha256(change.model_dump(mode="json"))


def canonical_requirement_sha256(requirement: Requirement) -> str:
    """Hash every typed ``Requirement`` field."""
    return canonical_sha256(requirement.model_dump(mode="json"))


def full_verification_receipt_json_bytes(receipt: FullVerificationReceipt) -> bytes:
    """Serialize a FULL verification receipt as canonical JSON."""
    return canonical_json_bytes(receipt.model_dump(mode="json"))


def parse_full_verification_receipt_bytes(raw: bytes) -> FullVerificationReceipt:
    """Parse a bounded, canonical, duplicate-free FULL verification receipt."""
    if len(raw) > MAX_VERIFICATION_RECEIPT_BYTES:
        raise SemanticDimensionsError("FULL verification receipt exceeds size limit")
    try:
        parsed = strict_loads(raw)
    except StrictJSONError as exc:
        raise SemanticDimensionsError(f"invalid FULL verification receipt: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SemanticDimensionsError("FULL verification receipt must be a JSON object")
    if canonical_json_bytes(parsed) != raw:
        raise SemanticDimensionsError("FULL verification receipt JSON is not canonical")
    try:
        receipt = FullVerificationReceipt.model_validate_json(raw)
    except ValidationError as exc:
        raise SemanticDimensionsError(f"invalid FULL verification receipt: {exc}") from exc
    if full_verification_receipt_json_bytes(receipt) != raw:
        raise SemanticDimensionsError("FULL receipt omits or changes typed fields")
    return receipt


def _primary_change_id(
    classification: ChangeClassification,
    old: Requirement | None,
    new: Requirement | None,
) -> str:
    parts = [
        classification.value,
        old.requirement_id if old is not None else "",
        new.requirement_id if new is not None else "",
        old.normalized_text if old is not None else "",
        new.normalized_text if new is not None else "",
    ]
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _expected_primary_evidence_hashes(
    classification: ChangeClassification,
    old: Requirement | None,
    new: Requirement | None,
) -> list[str]:
    hashes: list[str] = []
    if old is not None:
        hashes.append(evidence_hash("old_text", old.original_text))
        hashes.append(evidence_hash("old_locator", old.source_locator))
    if new is not None:
        hashes.append(evidence_hash("new_text", new.original_text))
        hashes.append(evidence_hash("new_locator", new.source_locator))
    hashes.append(evidence_hash("classification", classification.value))
    return sorted(set(hashes))


def _expected_modality_transition(old: Requirement | None, new: Requirement | None) -> str | None:
    if old is not None and new is not None:
        return f"{old.modality.value}->{new.modality.value}"
    if old is not None:
        return f"{old.modality.value}->∅"
    if new is not None:
        return f"∅->{new.modality.value}"
    return None


def _validate_side_binding(*, side: str, change: Change, requirement: Requirement | None) -> None:
    observed = (
        getattr(change, f"{side}_requirement_id"),
        getattr(change, f"{side}_source_locator"),
        getattr(change, f"{side}_text"),
        getattr(change, f"{side}_section_path"),
    )
    if requirement is None:
        if any(value is not None for value in observed):
            raise SemanticDimensionsError(f"primary change carries unexpected {side} evidence")
        return
    expected = (
        requirement.requirement_id,
        requirement.source_locator,
        requirement.original_text,
        requirement.section_path,
    )
    if observed != expected:
        raise SemanticDimensionsError(f"primary change {side} evidence does not match requirement")


def validate_primary_change_binding(
    *, change: Change, old: Requirement | None, new: Requirement | None
) -> None:
    """Validate primary identity and source fields before semantic expansion."""
    if old is None and new is None:
        raise SemanticDimensionsError("primary change has no requirement side")
    if old is None:
        if change.classification is not ChangeClassification.ADDED:
            raise SemanticDimensionsError("an unpaired new requirement must retain primary ADDED")
    elif new is None:
        if change.classification is not ChangeClassification.REMOVED:
            raise SemanticDimensionsError("an unpaired old requirement must retain primary REMOVED")
    elif change.classification in {ChangeClassification.ADDED, ChangeClassification.REMOVED}:
        raise SemanticDimensionsError("paired requirements cannot retain primary ADDED/REMOVED")

    _validate_side_binding(side="old", change=change, requirement=old)
    _validate_side_binding(side="new", change=change, requirement=new)
    if change.change_id != _primary_change_id(change.classification, old, new):
        raise SemanticDimensionsError("primary change_id does not bind exact requirements")
    if change.evidence_hashes != _expected_primary_evidence_hashes(change.classification, old, new):
        raise SemanticDimensionsError("primary evidence hashes do not bind exact requirements")
    if change.modality_transition != _expected_modality_transition(old, new):
        raise SemanticDimensionsError("primary modality_transition does not match requirements")
    if not math.isfinite(change.confidence) or not 0.0 <= change.confidence <= 1.0:
        raise SemanticDimensionsError("primary confidence is invalid")
    if not change.classification_reasons or any(
        not reason for reason in change.classification_reasons
    ):
        raise SemanticDimensionsError("primary classification reasons are missing")


def _validate_requirement(
    requirement: Requirement,
    *,
    snapshot: DocumentSnapshot,
) -> None:
    if requirement.document_sha256 != snapshot.sha256:
        raise SemanticDimensionsError("requirement document SHA differs from report snapshot")
    if requirement.document_version != snapshot.version:
        raise SemanticDimensionsError("requirement version differs from report snapshot")
    if not _SHA256_RE.fullmatch(requirement.document_sha256):
        raise SemanticDimensionsError("requirement document SHA is not canonical")
    expected_fingerprint = fingerprint_requirement(
        requirement.normalized_text,
        requirement.modality.value,
        requirement.actor,
        requirement.action,
        requirement.condition,
        requirement.exception,
    )
    if requirement.fingerprint != expected_fingerprint:
        raise SemanticDimensionsError("requirement fingerprint does not match semantic fields")
    expected_polarity = (
        Polarity.NEGATIVE if requirement.modality.value.endswith("_NOT") else Polarity.AFFIRMATIVE
    )
    if requirement.polarity is not expected_polarity:
        raise SemanticDimensionsError("requirement polarity does not match modality")
    if not math.isfinite(requirement.confidence) or not 0.0 <= requirement.confidence <= 1.0:
        raise SemanticDimensionsError("requirement confidence is invalid")
    if type(requirement.structural_index) is not int or requirement.structural_index < 0:
        raise SemanticDimensionsError("requirement structural_index is invalid")
    if not requirement.extractor_version:
        raise SemanticDimensionsError("requirement extractor_version is missing")


def _validate_report(report: Report) -> None:
    data = report.model_dump(mode="json")
    if report.integrity.alg != "sha256":
        raise SemanticDimensionsError("report integrity algorithm is not sha256")
    if report.integrity.content_sha256 != integrity_payload_hash(data):
        raise SemanticDimensionsError("report integrity payload hash is invalid")

    sides = (
        ("old", report.old_document, report.old_requirements),
        ("new", report.new_document, report.new_requirements),
    )
    requirement_maps: dict[str, dict[str, Requirement]] = {}
    for side, snapshot, requirements in sides:
        if not _SHA256_RE.fullmatch(snapshot.sha256):
            raise SemanticDimensionsError(f"{side} document SHA is not canonical")
        ids = [requirement.requirement_id for requirement in requirements]
        if len(ids) != len(set(ids)):
            raise SemanticDimensionsError(f"duplicate {side} requirement IDs")
        for requirement in requirements:
            _validate_requirement(requirement, snapshot=snapshot)
        requirement_maps[side] = dict(zip(ids, requirements, strict=True))

    change_ids = [change.change_id for change in report.changes]
    if len(change_ids) != len(set(change_ids)):
        raise SemanticDimensionsError("duplicate primary change IDs")
    for change in report.changes:
        old = (
            requirement_maps["old"].get(change.old_requirement_id)
            if change.old_requirement_id is not None
            else None
        )
        new = (
            requirement_maps["new"].get(change.new_requirement_id)
            if change.new_requirement_id is not None
            else None
        )
        validate_primary_change_binding(change=change, old=old, new=new)

    expected_counts = dict(
        sorted(Counter(item.classification.value for item in report.changes).items())
    )
    if report.summary.old_requirement_count != len(report.old_requirements):
        raise SemanticDimensionsError("report old requirement count is invalid")
    if report.summary.new_requirement_count != len(report.new_requirements):
        raise SemanticDimensionsError("report new requirement count is invalid")
    if report.summary.change_count != len(report.changes):
        raise SemanticDimensionsError("report change count is invalid")
    if report.summary.classification_counts != expected_counts:
        raise SemanticDimensionsError("report classification counts are invalid")


_FileIdentity = tuple[int, int, int, int, int, int, int]


@dataclass(frozen=True)
class _BoundedFileRead:
    path: Path
    label: str
    raw: bytes
    content_sha256: str
    before: _FileIdentity
    after: _FileIdentity
    final: _FileIdentity

    @property
    def size(self) -> int:
        return len(self.raw)


@dataclass(frozen=True)
class _AuthorityInputs:
    report_file: _BoundedFileRead
    report: Report
    old_source_file: _BoundedFileRead
    old_source: VerifiedSourceBinding
    new_source_file: _BoundedFileRead
    new_source: VerifiedSourceBinding


def _is_reparse(stat_result: os.stat_result) -> bool:
    attributes = int(getattr(stat_result, "st_file_attributes", 0))
    reparse = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return bool(attributes & reparse)


def _is_junction(path: Path) -> bool:
    checker = getattr(path, "is_junction", None)
    return bool(checker and checker())


def _file_identity(stat_result: os.stat_result) -> _FileIdentity:
    return (
        int(stat_result.st_dev),
        int(stat_result.st_ino),
        int(stat_result.st_mode),
        int(stat_result.st_size),
        int(stat_result.st_mtime_ns),
        int(getattr(stat_result, "st_nlink", 1)),
        int(getattr(stat_result, "st_file_attributes", 0)),
    )


def _validate_regular_identity(
    stat_result: os.stat_result,
    *,
    label: str,
    max_bytes: int,
    expected_size: int | None,
) -> None:
    if not stat.S_ISREG(stat_result.st_mode) or _is_reparse(stat_result):
        raise SemanticDimensionsError(f"{label} must be a regular non-reparse file")
    if int(getattr(stat_result, "st_nlink", 1)) != 1:
        raise SemanticDimensionsError(f"{label} must not have hard-link aliases")
    if stat_result.st_size < 0 or stat_result.st_size > max_bytes:
        raise SemanticDimensionsError(f"{label} exceeds size limit")
    if expected_size is not None and stat_result.st_size != expected_size:
        raise SemanticDimensionsError(f"{label} byte length differs from report")


def _bounded_read_regular_file(
    path: Path,
    *,
    label: str,
    max_bytes: int,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
) -> _BoundedFileRead:
    """Read one unaliased regular file through a bounded descriptor snapshot."""
    candidate = Path(path)
    if candidate.is_symlink() or _is_junction(candidate):
        raise SemanticDimensionsError(f"{label} must not be a symlink or junction")
    try:
        initial = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise SemanticDimensionsError(f"cannot stat {label}: {exc}") from exc
    _validate_regular_identity(
        initial,
        label=label,
        max_bytes=max_bytes,
        expected_size=expected_size,
    )
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise SemanticDimensionsError(f"cannot open {label}: {exc}") from exc
    try:
        before_stat = os.fstat(descriptor)
        _validate_regular_identity(
            before_stat,
            label=label,
            max_bytes=max_bytes,
            expected_size=expected_size,
        )
        before = _file_identity(before_stat)
        if _file_identity(initial) != before:
            raise SemanticDimensionsError(f"{label} path identity changed before read")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after_stat = os.fstat(descriptor)
        _validate_regular_identity(
            after_stat,
            label=label,
            max_bytes=max_bytes,
            expected_size=expected_size,
        )
        after = _file_identity(after_stat)
    except OSError as exc:
        raise SemanticDimensionsError(f"cannot read {label}: {exc}") from exc
    finally:
        os.close(descriptor)
    if len(raw) > max_bytes:
        raise SemanticDimensionsError(f"{label} exceeds size limit")
    if before != after or len(raw) != after_stat.st_size:
        raise SemanticDimensionsError(f"{label} changed while its descriptor was read")
    try:
        final_stat = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise SemanticDimensionsError(f"cannot restat {label}: {exc}") from exc
    _validate_regular_identity(
        final_stat,
        label=label,
        max_bytes=max_bytes,
        expected_size=expected_size,
    )
    final = _file_identity(final_stat)
    if candidate.is_symlink() or _is_junction(candidate) or final != after:
        raise SemanticDimensionsError(f"{label} final path identity changed while being read")
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise SemanticDimensionsError(f"{label} SHA differs from report")
    return _BoundedFileRead(
        path=candidate,
        label=label,
        raw=raw,
        content_sha256=digest,
        before=before,
        after=after,
        final=final,
    )


def _read_report_file(path: Path) -> tuple[_BoundedFileRead, Report]:
    file_read = _bounded_read_regular_file(
        path,
        label="authority report",
        max_bytes=MAX_AUTHORITY_REPORT_BYTES,
    )
    raw = file_read.raw
    try:
        parsed = strict_loads(raw)
    except StrictJSONError as exc:
        raise SemanticDimensionsError(f"authority report strict JSON failed: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SemanticDimensionsError("authority report must be a JSON object")
    try:
        report = Report.model_validate(parsed)
        dumped = report.model_dump(mode="json")
        deep_require_keys(parsed, dumped)
    except (ValidationError, StrictJSONError) as exc:
        raise SemanticDimensionsError(f"authority report typed validation failed: {exc}") from exc
    if raw != canonical_json_bytes(dumped):
        raise SemanticDimensionsError("authority report bytes are not the complete canonical dump")
    return file_read, report


def _verified_source_binding(
    *, source_root: Path, snapshot: DocumentSnapshot, side: str
) -> tuple[_BoundedFileRead, VerifiedSourceBinding]:
    if snapshot.source_ref_mode != "source_root_relative":
        raise SemanticDimensionsError(f"{side} source is not source-root-relative")
    try:
        path, source_ref = resolve_declared_under_root(source_root, snapshot.path)
    except PortableRefError as exc:
        raise SemanticDimensionsError(f"{side} source resolution failed: {exc}") from exc
    file_read = _bounded_read_regular_file(
        path,
        label=f"{side} source",
        max_bytes=MAX_AUTHORITY_SOURCE_BYTES,
        expected_size=snapshot.byte_length,
        expected_sha256=snapshot.sha256,
    )
    binding = VerifiedSourceBinding(
        source_ref=source_ref,
        content_sha256=file_read.content_sha256,
        byte_length=file_read.size,
        document_version=snapshot.version,
        source_ref_mode="source_root_relative",
    )
    return file_read, binding


def _preflight_authority_inputs(report_path: Path, source_root: Path) -> _AuthorityInputs:
    report_file, report = _read_report_file(report_path)
    _validate_report(report)
    old_source_file, old_source = _verified_source_binding(
        source_root=source_root,
        snapshot=report.old_document,
        side="old",
    )
    new_source_file, new_source = _verified_source_binding(
        source_root=source_root,
        snapshot=report.new_document,
        side="new",
    )
    if (
        old_source.source_ref != new_source.source_ref
        and _portable_alias_key(old_source.source_ref)
        == _portable_alias_key(new_source.source_ref)
    ):
        raise SemanticDimensionsError("old/new source refs are cross-platform aliases")
    return _AuthorityInputs(
        report_file=report_file,
        report=report,
        old_source_file=old_source_file,
        old_source=old_source,
        new_source_file=new_source_file,
        new_source=new_source,
    )


def _authority_files(inputs: _AuthorityInputs) -> tuple[_BoundedFileRead, ...]:
    return (inputs.report_file, inputs.old_source_file, inputs.new_source_file)


def _assert_stable_authority_inputs(
    before: _AuthorityInputs,
    after: _AuthorityInputs,
    *,
    phase: str,
) -> None:
    for initial, final in zip(
        _authority_files(before),
        _authority_files(after),
        strict=True,
    ):
        if (
            initial.path != final.path
            or initial.size != final.size
            or initial.content_sha256 != final.content_sha256
            or initial.raw != final.raw
            or initial.final != final.before
        ):
            raise SemanticDimensionsError(f"{initial.label} changed across {phase}")
    if (
        before.report != after.report
        or before.old_source != after.old_source
        or before.new_source != after.new_source
    ):
        raise SemanticDimensionsError(f"authority bindings changed across {phase}")


def _assert_equivalent_authority_payload(
    expected: _AuthorityInputs,
    observed: _AuthorityInputs,
) -> None:
    expected_files = _authority_files(expected)
    observed_files = _authority_files(observed)
    if any(
        left.size != right.size
        or left.content_sha256 != right.content_sha256
        or left.raw != right.raw
        for left, right in zip(expected_files, observed_files, strict=True)
    ) or (
        expected.report != observed.report
        or expected.old_source != observed.old_source
        or expected.new_source != observed.new_source
    ):
        raise SemanticDimensionsError("isolated FULL replay inputs differ from bounded preflight")


def _write_isolated_file(path: Path, raw: bytes, *, label: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise SemanticDimensionsError(f"cannot materialize isolated {label}: {exc}") from exc


def _run_full_verifier_on_snapshot(inputs: _AuthorityInputs) -> VerifyResult:
    with TemporaryDirectory(prefix="normshift-full-replay-") as directory:
        replay_root = Path(directory) / "source-root"
        replay_root.mkdir()
        source_payloads: dict[str, bytes] = {}
        for binding, file_read in (
            (inputs.old_source, inputs.old_source_file),
            (inputs.new_source, inputs.new_source_file),
        ):
            previous = source_payloads.get(binding.source_ref)
            if previous is not None and previous != file_read.raw:
                raise SemanticDimensionsError("one source_ref maps to different bounded bytes")
            source_payloads[binding.source_ref] = file_read.raw
        for source_ref, raw in sorted(source_payloads.items()):
            _write_isolated_file(replay_root / source_ref, raw, label=f"source {source_ref}")
        replay_report = Path(directory) / "report.json"
        _write_isolated_file(replay_report, inputs.report_file.raw, label="report")

        replay_before = _preflight_authority_inputs(replay_report, replay_root)
        _assert_equivalent_authority_payload(inputs, replay_before)
        result = verify_report_file(
            replay_report,
            source_root=replay_root,
            require_sources=True,
        )
        replay_after = _preflight_authority_inputs(replay_report, replay_root)
        _assert_stable_authority_inputs(
            replay_before,
            replay_after,
            phase="isolated FULL verifier replay",
        )
        _assert_equivalent_authority_payload(inputs, replay_after)
        return result


def _require_full_result(result: VerifyResult) -> None:
    if (
        not result.ok
        or result.errors
        or result.verification_scope != "FULL"
        or result.override_used
        or result.content_sha256 is None
    ):
        detail = "; ".join(result.errors[:3]) or "verifier did not return strict FULL success"
        raise SemanticDimensionsError(f"FULL report verification failed: {detail}")


def _derive_full_verification_receipt(
    report_path: Path, source_root: Path
) -> tuple[Report, FullVerificationReceipt]:
    try:
        exact_report, exact_root = _resolve_authority_paths(report_path, source_root)
        before = _preflight_authority_inputs(exact_report, exact_root)
    except SemanticDimensionsError as exc:
        raise SemanticDimensionsError(
            f"FULL report verification failed during bounded preflight: {exc}"
        ) from exc
    result = _run_full_verifier_on_snapshot(before)
    try:
        after = _preflight_authority_inputs(exact_report, exact_root)
    except SemanticDimensionsError as exc:
        raise SemanticDimensionsError(
            f"FULL report verification failed during post-verifier recheck: {exc}"
        ) from exc
    _assert_stable_authority_inputs(before, after, phase="FULL verifier replay")
    _require_full_result(result)
    assert result.content_sha256 is not None
    report = after.report
    if result.content_sha256 != report.integrity.content_sha256:
        raise SemanticDimensionsError("FULL verifier content SHA differs from report integrity")
    report_sha256 = after.report_file.content_sha256
    old_source = after.old_source
    new_source = after.new_source
    payload: dict[str, object] = {
        "schema_version": FULL_VERIFICATION_RECEIPT_SCHEMA_VERSION,
        "authority_kind": FULL_REPLAY_AUTHORITY_KIND,
        "verification_scope": "FULL",
        "result": "OK",
        "verifier_id": "normshift.verify.verifier.verify_report_file",
        "verifier_version": __version__,
        "report_file_sha256": report_sha256,
        "report_content_sha256": result.content_sha256,
        "report_schema_version": report.schema_version,
        "report_tool_version": report.tool_version,
        "old_source": old_source.model_dump(mode="json"),
        "new_source": new_source.model_dump(mode="json"),
    }
    receipt = FullVerificationReceipt(
        schema_version=FULL_VERIFICATION_RECEIPT_SCHEMA_VERSION,
        authority_kind=FULL_REPLAY_AUTHORITY_KIND,
        verification_scope="FULL",
        result="OK",
        verifier_id="normshift.verify.verifier.verify_report_file",
        verifier_version=__version__,
        report_file_sha256=report_sha256,
        report_content_sha256=result.content_sha256,
        report_schema_version=report.schema_version,
        report_tool_version=report.tool_version,
        old_source=old_source,
        new_source=new_source,
        receipt_payload_sha256=canonical_sha256(payload),
    )
    return report, receipt


def _resolve_authority_paths(report_path: Path, source_root: Path) -> tuple[Path, Path]:
    report_candidate = Path(report_path)
    root_candidate = Path(source_root)
    if report_candidate.is_symlink() or _is_junction(report_candidate):
        raise SemanticDimensionsError("authority report path must not be a symlink or junction")
    if root_candidate.is_symlink() or _is_junction(root_candidate):
        raise SemanticDimensionsError("source_root must not be a symlink or junction")
    try:
        report_stat = report_candidate.stat(follow_symlinks=False)
        root_stat = root_candidate.stat(follow_symlinks=False)
        exact_report = report_candidate.resolve(strict=True)
        exact_root = root_candidate.resolve(strict=True)
    except OSError as exc:
        raise SemanticDimensionsError(f"authority path resolution failed: {exc}") from exc
    if not stat.S_ISREG(report_stat.st_mode) or _is_reparse(report_stat):
        raise SemanticDimensionsError("authority report path is not a regular file")
    if not stat.S_ISDIR(root_stat.st_mode) or _is_reparse(root_stat):
        raise SemanticDimensionsError("source_root is not a regular non-reparse directory")
    return exact_report, exact_root


def create_full_verification_receipt(
    report_path: Path, *, source_root: Path
) -> FullVerificationReceipt:
    """Run the existing non-writing FULL verifier and return its typed receipt."""
    exact_report, exact_root = _resolve_authority_paths(report_path, source_root)
    _report, receipt = _derive_full_verification_receipt(exact_report, exact_root)
    return receipt


@dataclass(frozen=True)
class VerifiedReportAuthority:
    """Exact report plus a canonical receipt backed by repeatable FULL replay."""

    report: Report
    report_path: Path
    source_root: Path
    receipt: FullVerificationReceipt
    receipt_bytes: bytes
    expected_report_file_sha256: str
    expected_receipt_sha256: str

    @property
    def authority_kind(self) -> str:
        return FULL_REPLAY_AUTHORITY_KIND

    @property
    def authority_id(self) -> str:
        return f"full-report-replay:{self.expected_receipt_sha256}"

    def verify(self) -> None:
        """Re-run FULL source replay and recheck every immutable receipt binding."""
        for field_name, digest in (
            ("expected_report_file_sha256", self.expected_report_file_sha256),
            ("expected_receipt_sha256", self.expected_receipt_sha256),
        ):
            if not _SHA256_RE.fullmatch(digest):
                raise SemanticDimensionsError(f"{field_name} is not canonical")
        if hashlib.sha256(self.receipt_bytes).hexdigest() != self.expected_receipt_sha256:
            raise SemanticDimensionsError("receipt bytes differ from the independently held SHA")
        parsed_receipt = parse_full_verification_receipt_bytes(self.receipt_bytes)
        if parsed_receipt != self.receipt:
            raise SemanticDimensionsError("typed FULL receipt differs from exact receipt bytes")
        if canonical_report_sha256(self.report) != self.expected_report_file_sha256:
            raise SemanticDimensionsError("in-memory report differs from the verified report file")
        live_report, live_receipt = _derive_full_verification_receipt(
            self.report_path, self.source_root
        )
        if canonical_report_sha256(live_report) != self.expected_report_file_sha256:
            raise SemanticDimensionsError("report file differs from the independently held SHA")
        if live_receipt != self.receipt:
            raise SemanticDimensionsError("FULL replay receipt differs from the anchored receipt")

    def resolve(
        self, primary_change_id: str
    ) -> tuple[Change, Requirement | None, Requirement | None]:
        """Resolve one exact primary event and its source-replayed requirements."""
        self.verify()
        matches = [item for item in self.report.changes if item.change_id == primary_change_id]
        if len(matches) != 1:
            raise SemanticDimensionsError("authority must contain exactly one requested change")
        change = matches[0]
        old_by_id = {item.requirement_id: item for item in self.report.old_requirements}
        new_by_id = {item.requirement_id: item for item in self.report.new_requirements}
        old = (
            old_by_id.get(change.old_requirement_id)
            if change.old_requirement_id is not None
            else None
        )
        new = (
            new_by_id.get(change.new_requirement_id)
            if change.new_requirement_id is not None
            else None
        )
        validate_primary_change_binding(change=change, old=old, new=new)
        return change, old, new


def bind_verified_report_file(
    report_path: Path,
    *,
    source_root: Path,
    receipt_bytes: bytes,
    expected_report_file_sha256: str,
    expected_receipt_sha256: str,
) -> VerifiedReportAuthority:
    """Bind only exact receipt bytes that a fresh FULL source replay reproduces."""
    if not _SHA256_RE.fullmatch(expected_report_file_sha256):
        raise SemanticDimensionsError("expected report file SHA is not canonical")
    if not _SHA256_RE.fullmatch(expected_receipt_sha256):
        raise SemanticDimensionsError("expected receipt SHA is not canonical")
    if hashlib.sha256(receipt_bytes).hexdigest() != expected_receipt_sha256:
        raise SemanticDimensionsError("receipt bytes differ from the independently held SHA")
    anchored_receipt = parse_full_verification_receipt_bytes(receipt_bytes)
    if anchored_receipt.report_file_sha256 != expected_report_file_sha256:
        raise SemanticDimensionsError("FULL receipt does not bind the expected report file")
    exact_report, exact_root = _resolve_authority_paths(report_path, source_root)
    report, replayed_receipt = _derive_full_verification_receipt(exact_report, exact_root)
    if canonical_report_sha256(report) != expected_report_file_sha256:
        raise SemanticDimensionsError("report file differs from the independently held SHA")
    if replayed_receipt != anchored_receipt:
        raise SemanticDimensionsError("supplied FULL receipt differs from fresh source replay")
    report_copy = Report.model_validate(report.model_dump(mode="json"))
    authority = VerifiedReportAuthority(
        report=report_copy,
        report_path=exact_report,
        source_root=exact_root,
        receipt=anchored_receipt,
        receipt_bytes=bytes(receipt_bytes),
        expected_report_file_sha256=expected_report_file_sha256,
        expected_receipt_sha256=expected_receipt_sha256,
    )
    authority.verify()
    return authority
