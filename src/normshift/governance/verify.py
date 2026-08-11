"""Fail-closed verification for labeling custody and blind split manifests."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast

from pydantic import BaseModel, ValidationError

from normshift.acceptance.item_key import locator_source_ref
from normshift.corpus.acquisition import (
    MAX_MANIFEST_BYTES,
    AcquisitionError,
    SourceManifest,
    load_source_manifest,
)
from normshift.evidence.hashing import canonical_json_bytes
from normshift.governance.models import (
    BlindSplitDocument,
    BlindSplitManifest,
    CandidateFreezeStatus,
    DecisionEvent,
    DecisionLedger,
    LabelingPacket,
    LabelResponse,
    LabelSubmission,
    LedgerRevisionKind,
    PacketItem,
)
from normshift.strict_json import StrictJSONError, strict_loads

POLICY_ID: Literal["normshift-m1-m2-prereg-v1"] = "normshift-m1-m2-prereg-v1"
POLICY_SHA256 = "0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773"
MAX_POLICY_BYTES = 1024 * 1024
MAX_PACKET_BYTES = 64 * 1024 * 1024
MAX_LEDGER_BYTES = 64 * 1024 * 1024
MAX_SPLIT_BYTES = 16 * 1024 * 1024
MAX_SUBMISSION_BYTES = 16 * 1024 * 1024
MAX_TOTAL_SUBMISSION_BYTES = 64 * 1024 * 1024
MAX_CONCRETE_CUSTODY_PATH_BYTES = 240
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SourceContractKind = Literal[
    "ACTUAL_STANDARDS_SOURCE_CONTRACT", "SOURCE_CONTRACT_TEST"
]


class GovernanceContractError(ValueError):
    """Raised when a governance artifact fails closed."""


@dataclass(frozen=True)
class GovernanceVerificationResult:
    """Machine-readable contract result that deliberately grants no acceptance."""

    contract_kind: Literal["LABELING_GOVERNANCE", "BLIND_SPLIT_GOVERNANCE"]
    source_contract_kind: SourceContractKind
    artifact_sha256: str
    item_or_document_count: int
    independent_labeler_count: int
    holdout_document_count: int
    candidate_frozen: bool
    metrics_evaluated: Literal[False] = False
    external_acceptance_granted: Literal[False] = False
    scope: Literal["GOVERNANCE_CONTRACT_ONLY"] = "GOVERNANCE_CONTRACT_ONLY"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_sha256(value: str, label: str) -> None:
    if not SHA256_RE.fullmatch(value):
        raise GovernanceContractError(f"{label} must be a lowercase 64-hex SHA-256")


def _is_reparse(stat_result: os.stat_result) -> bool:
    attributes = getattr(stat_result, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse)


def _is_multiply_linked(stat_result: os.stat_result) -> bool:
    """Return whether a regular evidence file has an external hard-link alias."""

    return int(getattr(stat_result, "st_nlink", 1)) != 1


def _portable_alias_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _bounded_read_regular_file(
    path: Path,
    label: str,
    *,
    max_bytes: int,
    expected_bytes: int | None = None,
) -> bytes:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise GovernanceContractError(f"{label} must be a regular non-symlink file: {path}")
    try:
        initial_path_stat = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise GovernanceContractError(f"cannot stat {label}: {exc}") from exc
    if _is_reparse(initial_path_stat):
        raise GovernanceContractError(f"{label} must not be a reparse point")
    if _is_multiply_linked(initial_path_stat):
        raise GovernanceContractError(f"{label} must not be a hard-linked file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise GovernanceContractError(f"cannot open {label}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or _is_reparse(before)
            or _is_multiply_linked(before)
        ):
            raise GovernanceContractError(f"{label} is not a regular non-reparse file")
        if before.st_size > max_bytes:
            raise GovernanceContractError(f"{label} exceeds {max_bytes} bytes")
        if expected_bytes is not None and before.st_size != expected_bytes:
            raise GovernanceContractError(f"{label} byte length differs before read")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise GovernanceContractError(f"cannot read {label}: {exc}") from exc
    finally:
        os.close(descriptor)
    if len(raw) > max_bytes:
        raise GovernanceContractError(f"{label} exceeds {max_bytes} bytes")
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
    if identity_before != identity_after or len(raw) != after.st_size:
        raise GovernanceContractError(f"{label} changed while being read")
    try:
        final_path_stat = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise GovernanceContractError(f"cannot restat {label}: {exc}") from exc
    path_identity = (
        final_path_stat.st_dev,
        final_path_stat.st_ino,
        final_path_stat.st_size,
        final_path_stat.st_mtime_ns,
        final_path_stat.st_nlink,
    )
    if (
        not stat.S_ISREG(final_path_stat.st_mode)
        or _is_reparse(final_path_stat)
        or _is_multiply_linked(final_path_stat)
        or candidate.is_symlink()
        or path_identity != identity_after
    ):
        raise GovernanceContractError(f"{label} path identity changed while being read")
    return raw


def _strict_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = strict_loads(raw)
    except StrictJSONError as exc:
        raise GovernanceContractError(f"{label} is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceContractError(f"{label} must be a JSON object")
    return cast(dict[str, Any], value)


def _load_canonical_model[ModelT: BaseModel](
    path: Path,
    model: type[ModelT],
    label: str,
    *,
    max_bytes: int,
    expected_sha256: str,
    expected_bytes: int | None = None,
) -> tuple[ModelT, bytes]:
    _require_sha256(expected_sha256, f"expected {label}")
    raw = _bounded_read_regular_file(
        path,
        label,
        max_bytes=max_bytes,
        expected_bytes=expected_bytes,
    )
    observed_sha256 = _sha256(raw)
    if observed_sha256 != expected_sha256:
        raise GovernanceContractError(
            f"{label} SHA-256 mismatch: expected {expected_sha256}, got {observed_sha256}"
        )
    _strict_object(raw, label)
    try:
        parsed = model.model_validate_json(raw, strict=True)
    except ValidationError as exc:
        raise GovernanceContractError(f"{label} schema validation failed: {exc}") from exc
    if canonical_json_bytes(parsed.model_dump(mode="json")) != raw:
        raise GovernanceContractError(f"{label} is not canonical UTF-8 JSON")
    return parsed, raw


def _verify_policy(path: Path) -> None:
    raw = _bounded_read_regular_file(path, "acceptance policy", max_bytes=MAX_POLICY_BYTES)
    if _sha256(raw) != POLICY_SHA256:
        raise GovernanceContractError("acceptance policy SHA-256 differs from frozen policy")
    policy = _strict_object(raw, "acceptance policy")
    if (
        policy.get("policy_id") != POLICY_ID
        or policy.get("status") != "FROZEN_BEFORE_BLIND_EVALUATION"
    ):
        raise GovernanceContractError("acceptance policy identity/status differs")


def _source_manifest_canonical_bytes(payload: dict[str, Any]) -> bytes:
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise GovernanceContractError(f"source manifest cannot be canonicalized: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _load_verified_source_manifest(
    *,
    path: Path,
    expected_sha256: str,
    acceptance_policy_path: Path,
    allow_test_contract: bool,
) -> SourceManifest:
    """Load the acquisition manifest under its own frozen compact canonical form."""

    _require_sha256(expected_sha256, "expected source manifest")
    raw_before = _bounded_read_regular_file(
        path,
        "source manifest",
        max_bytes=MAX_MANIFEST_BYTES,
    )
    if _sha256(raw_before) != expected_sha256:
        raise GovernanceContractError("source manifest differs from independent expected SHA-256")
    payload = _strict_object(raw_before, "source manifest")
    if raw_before != _source_manifest_canonical_bytes(payload):
        raise GovernanceContractError("source manifest is not canonical compact UTF-8 JSON")
    try:
        manifest = load_source_manifest(
            path,
            expected_sha256=expected_sha256,
            acceptance_policy_path=acceptance_policy_path,
            allow_test_contract=allow_test_contract,
        )
    except AcquisitionError as exc:
        raise GovernanceContractError(f"source manifest contract rejected: {exc}") from exc
    raw_after = _bounded_read_regular_file(
        path,
        "source manifest",
        max_bytes=MAX_MANIFEST_BYTES,
    )
    if raw_after != raw_before:
        raise GovernanceContractError("source manifest changed across contract validation")
    return manifest


def _source_contract_kind(manifest: SourceManifest) -> SourceContractKind:
    if manifest.corpus_kind not in {
        "ACTUAL_STANDARDS_SOURCE_CONTRACT",
        "SOURCE_CONTRACT_TEST",
    }:
        raise GovernanceContractError("source manifest has an unsupported contract kind")
    return cast(SourceContractKind, manifest.corpus_kind)


def _entry_ref(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise GovernanceContractError(f"submission entry escapes root: {path}") from exc


def _verify_exact_submission_root(root: Path, expected_refs: set[str]) -> None:
    root = Path(root)
    try:
        root_stat = root.stat(follow_symlinks=False)
    except OSError as exc:
        raise GovernanceContractError(f"cannot stat submissions root: {exc}") from exc
    if root.is_symlink() or not stat.S_ISDIR(root_stat.st_mode) or _is_reparse(root_stat):
        raise GovernanceContractError("submissions root must be a regular non-reparse directory")
    for ref in expected_refs:
        concrete = root.joinpath(*PurePosixPath(ref).parts).absolute()
        if len(str(concrete).encode("utf-8")) > MAX_CONCRETE_CUSTODY_PATH_BYTES:
            raise GovernanceContractError(
                f"submission destination exceeds the portable concrete-path budget: {ref}"
            )

    expected_dirs: set[str] = set()
    for ref in expected_refs:
        parent = PurePosixPath(ref).parent
        while parent.as_posix() != ".":
            expected_dirs.add(parent.as_posix())
            parent = parent.parent

    observed_files: set[str] = set()
    observed_dirs: set[str] = set()
    observed_file_identities: set[tuple[int, int]] = set()
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except OSError as exc:
            raise GovernanceContractError(f"cannot scan submissions root: {exc}") from exc
        for entry in entries:
            path = Path(entry.path)
            try:
                # ``DirEntry.stat().st_nlink`` is reported as zero on some
                # Windows/Python combinations.  Path.stat obtains the real
                # link count needed by the custody invariant.
                entry_stat = path.stat(follow_symlinks=False)
            except OSError as exc:
                raise GovernanceContractError(
                    f"cannot stat submission entry {path}: {exc}"
                ) from exc
            ref = _entry_ref(root, path)
            if entry.is_symlink() or _is_reparse(entry_stat):
                raise GovernanceContractError(
                    f"submission entry must not be symlink/reparse: {ref}"
                )
            if stat.S_ISDIR(entry_stat.st_mode):
                observed_dirs.add(ref)
                stack.append(path)
            elif stat.S_ISREG(entry_stat.st_mode):
                if _is_multiply_linked(entry_stat):
                    raise GovernanceContractError(
                        f"submission entry must not be a hard-linked file: {ref}"
                    )
                identity = (entry_stat.st_dev, entry_stat.st_ino)
                if identity in observed_file_identities:
                    raise GovernanceContractError(
                        f"submission files share one filesystem identity: {ref}"
                    )
                observed_file_identities.add(identity)
                observed_files.add(ref)
            else:
                raise GovernanceContractError(
                    f"submission entry is not regular file/directory: {ref}"
                )
    if len({_portable_alias_key(ref) for ref in observed_files | observed_dirs}) != len(
        observed_files | observed_dirs
    ):
        raise GovernanceContractError(
            "submissions root contains a cross-platform Unicode/case alias"
        )
    if observed_files != expected_refs or observed_dirs != expected_dirs:
        missing_files = sorted(expected_refs - observed_files)
        extra_files = sorted(observed_files - expected_refs)
        missing_dirs = sorted(expected_dirs - observed_dirs)
        extra_dirs = sorted(observed_dirs - expected_dirs)
        raise GovernanceContractError(
            "submissions root inventory differs; "
            f"missing_files={missing_files}, extra_files={extra_files}, "
            f"missing_dirs={missing_dirs}, extra_dirs={extra_dirs}"
        )


def _binding(item: PacketItem | LabelResponse | DecisionEvent) -> tuple[object, ...]:
    return (
        item.item_key,
        item.task,
        item.evaluation_slot,
        item.source_sha256s,
        item.portable_locators,
        item.evidence_sha256,
    )


def _response_sha256(response: LabelResponse) -> str:
    return _sha256(canonical_json_bytes(response.model_dump(mode="json")))


def _crosscheck_split_sources(
    split: BlindSplitManifest,
    source_manifest: SourceManifest,
) -> dict[str, BlindSplitDocument]:
    family_names = {"rfc": "RFC", "w3c": "W3C_TR", "whatwg": "WHATWG"}
    source_by_id = {record.source_id: record for record in source_manifest.sources}
    split_by_id = {document.source_id: document for document in split.documents}
    if set(split_by_id) != set(source_by_id):
        missing = sorted(set(source_by_id) - set(split_by_id))
        extra = sorted(set(split_by_id) - set(source_by_id))
        raise GovernanceContractError(
            "blind split/source manifest document identities differ; "
            f"missing={missing}, extra={extra}"
        )
    for source_id, record in source_by_id.items():
        document = split_by_id[source_id]
        expected = (
            family_names[record.family.value],
            record.standard_id,
            record.version_or_date,
            record.content_sha256,
            record.local_ref,
        )
        observed = (
            document.family.value,
            document.standard_id,
            document.version,
            document.raw_sha256,
            document.portable_source_ref,
        )
        if observed != expected:
            raise GovernanceContractError(
                f"blind split source binding differs for {source_id}: "
                f"expected={expected}, observed={observed}"
            )
    return {document.raw_sha256: document for document in split.documents}


def _crosscheck_packet_sources(
    packet: LabelingPacket,
    split_by_sha256: dict[str, BlindSplitDocument],
) -> None:
    for item in packet.items:
        item_documents: list[BlindSplitDocument] = []
        for source_sha256, locator in zip(
            item.source_sha256s, item.portable_locators, strict=True
        ):
            document = split_by_sha256.get(source_sha256)
            if document is None:
                raise GovernanceContractError(
                    f"packet item {item.item_key} names a source outside the verified manifest"
                )
            if locator_source_ref(locator) != document.portable_source_ref:
                raise GovernanceContractError(
                    f"packet item {item.item_key} locator differs from verified source ref"
                )
            if document.split.value != packet.dataset_split:
                raise GovernanceContractError(
                    f"packet item {item.item_key} crosses its declared dataset split"
                )
            item_documents.append(document)
        if item.task.value.startswith("M1_"):
            if any(not document.m1_in_scope for document in item_documents):
                raise GovernanceContractError(
                    f"packet item {item.item_key} references a source outside M1 scope"
                )
            continue
        if any(not document.m2_in_scope for document in item_documents):
            raise GovernanceContractError(
                f"packet item {item.item_key} references a source outside M2 scope"
            )
        if item.task.value != "M2_IDENTITY" and len(item_documents) > 1:
            lineage_keys = {
                (document.family, document.m2_lineage_chain_id)
                for document in item_documents
            }
            if len(lineage_keys) != 1:
                raise GovernanceContractError(
                    f"packet item {item.item_key} crosses an M2 family/lineage boundary"
                )


def _verify_retained_prior_ledger(
    *,
    ledger: DecisionLedger,
    prior_ledger_path: Path | None,
    expected_prior_ledger_sha256: str | None,
) -> None:
    if ledger.revision_context.kind == LedgerRevisionKind.INITIAL_FREEZE:
        if prior_ledger_path is not None or expected_prior_ledger_sha256 is not None:
            raise GovernanceContractError("initial ledger must not supply a prior ledger")
        return
    if prior_ledger_path is None or expected_prior_ledger_sha256 is None:
        raise GovernanceContractError(
            "post-freeze correction requires prior ledger bytes and independent SHA-256"
        )
    prior, prior_raw = _load_canonical_model(
        prior_ledger_path,
        DecisionLedger,
        "prior decision ledger",
        max_bytes=MAX_LEDGER_BYTES,
        expected_sha256=expected_prior_ledger_sha256,
    )
    prior_sha256 = _sha256(prior_raw)
    if ledger.revision_context.supersedes_ledger_sha256 != prior_sha256:
        raise GovernanceContractError("correction ledger does not supersede exact prior bytes")
    if prior.policy_sha256 != POLICY_SHA256:
        raise GovernanceContractError("prior ledger does not bind the frozen policy")
    immutable_identity = (
        ledger.kind,
        ledger.schema_version,
        ledger.policy_id,
        ledger.policy_sha256,
        ledger.ledger_id,
        ledger.packet_sha256,
    )
    prior_identity = (
        prior.kind,
        prior.schema_version,
        prior.policy_id,
        prior.policy_sha256,
        prior.ledger_id,
        prior.packet_sha256,
    )
    if immutable_identity != prior_identity:
        raise GovernanceContractError("correction ledger rewrites prior immutable identity")
    if ledger.ledger_version == prior.ledger_version:
        raise GovernanceContractError("correction ledger must use a new ledger_version")
    if ledger.frozen_at_utc <= prior.frozen_at_utc:
        raise GovernanceContractError("correction ledger must freeze strictly after prior ledger")
    retained_prefixes = (
        (ledger.review_rounds[: len(prior.review_rounds)], prior.review_rounds, "review rounds"),
        (ledger.submissions[: len(prior.submissions)], prior.submissions, "submissions"),
        (ledger.decisions[: len(prior.decisions)], prior.decisions, "decision events"),
    )
    for observed, expected, label in retained_prefixes:
        if observed != expected:
            raise GovernanceContractError(f"correction ledger rewrites retained prior {label}")
    if len(ledger.review_rounds) <= len(prior.review_rounds):
        raise GovernanceContractError("correction ledger does not append a new review round")
    if len(ledger.submissions) <= len(prior.submissions):
        raise GovernanceContractError("correction ledger does not append new submissions")
    if len(ledger.decisions) <= len(prior.decisions):
        raise GovernanceContractError("correction ledger does not append a decision event")
    appended_rounds = ledger.review_rounds[len(prior.review_rounds) :]
    if appended_rounds[0].opened_at_utc <= prior.frozen_at_utc:
        raise GovernanceContractError(
            "correction review round must open strictly after the prior ledger freeze"
        )
    appended_round_ids = {round_.review_round_id for round_ in appended_rounds}
    if any(
        event.review_round_id not in appended_round_ids
        for event in ledger.decisions[len(prior.decisions) :]
    ):
        raise GovernanceContractError(
            "correction ledger appends a decision under retained prior reviewer authority"
        )


def verify_labeling_governance(
    *,
    packet_path: Path,
    expected_packet_sha256: str,
    source_manifest_path: Path,
    submissions_root: Path,
    ledger_path: Path,
    expected_ledger_sha256: str,
    expected_source_manifest_sha256: str,
    blind_split_manifest_path: Path,
    expected_split_manifest_sha256: str,
    acceptance_policy_path: Path,
    prior_ledger_path: Path | None = None,
    expected_prior_ledger_sha256: str | None = None,
    _allow_test_source_contract: bool = False,
) -> GovernanceVerificationResult:
    """Verify neutral packet, independent submissions, and append-only decisions.

    All examples and tests for this function are synthetic.  A successful result
    means only that the governance graph is internally consistent and hash-bound.
    """

    _verify_policy(acceptance_policy_path)
    source_manifest = _load_verified_source_manifest(
        path=source_manifest_path,
        expected_sha256=expected_source_manifest_sha256,
        acceptance_policy_path=acceptance_policy_path,
        allow_test_contract=_allow_test_source_contract,
    )
    blind_split, blind_split_raw = _load_canonical_model(
        blind_split_manifest_path,
        BlindSplitManifest,
        "blind split manifest",
        max_bytes=MAX_SPLIT_BYTES,
        expected_sha256=expected_split_manifest_sha256,
    )
    if blind_split.policy_sha256 != POLICY_SHA256:
        raise GovernanceContractError("blind split manifest does not bind the frozen policy")
    if blind_split.source_manifest_sha256 != expected_source_manifest_sha256:
        raise GovernanceContractError(
            "blind split differs from independently expected source manifest"
        )
    if _sha256(blind_split_raw) != expected_split_manifest_sha256:
        raise GovernanceContractError("blind split trust anchor changed during verification")
    split_by_sha256 = _crosscheck_split_sources(blind_split, source_manifest)
    packet, packet_raw = _load_canonical_model(
        packet_path,
        LabelingPacket,
        "neutral labeling packet",
        max_bytes=MAX_PACKET_BYTES,
        expected_sha256=expected_packet_sha256,
    )
    ledger, ledger_raw = _load_canonical_model(
        ledger_path,
        DecisionLedger,
        "decision ledger",
        max_bytes=MAX_LEDGER_BYTES,
        expected_sha256=expected_ledger_sha256,
    )
    if packet.policy_sha256 != POLICY_SHA256 or ledger.policy_sha256 != POLICY_SHA256:
        raise GovernanceContractError("packet/ledger does not bind the frozen policy")
    implementation_authors = set(blind_split.implementation_author_ids)
    labeling_authority = {packet.prepared_by_reviewer_id}
    for review_round in ledger.review_rounds:
        labeling_authority.update(review_round.labeler_ids)
        labeling_authority.add(review_round.adjudicator_id)
    authority_overlap = sorted(implementation_authors & labeling_authority)
    if authority_overlap:
        raise GovernanceContractError(
            "labeling authority overlaps evaluated-system implementation authors: "
            f"{authority_overlap}"
        )
    if packet.source_manifest_sha256 != expected_source_manifest_sha256:
        raise GovernanceContractError("packet differs from independently expected source manifest")
    if packet.split_manifest_sha256 != expected_split_manifest_sha256:
        raise GovernanceContractError("packet differs from independently expected split manifest")
    _crosscheck_packet_sources(packet, split_by_sha256)
    packet_sha256 = _sha256(packet_raw)
    if ledger.packet_sha256 != packet_sha256:
        raise GovernanceContractError("ledger does not bind the exact neutral packet bytes")
    predictions_started_at_utc = (
        blind_split.candidate_freeze.predictions_started_at_utc
    )
    if ledger.revision_context.kind == LedgerRevisionKind.POST_FREEZE_CORRECTION:
        if predictions_started_at_utc is not None:
            raise GovernanceContractError(
                "v1 correction custody cannot reuse a split that already records prediction "
                "access; a separately hash-bound evaluation-attempt contract is required"
            )
    elif (
        predictions_started_at_utc is not None
        and ledger.frozen_at_utc >= predictions_started_at_utc
    ):
        raise GovernanceContractError(
            "initial decision ledger must freeze strictly before predictions start"
        )
    _verify_retained_prior_ledger(
        ledger=ledger,
        prior_ledger_path=prior_ledger_path,
        expected_prior_ledger_sha256=expected_prior_ledger_sha256,
    )

    expected_refs = {record.portable_ref for record in ledger.submissions}
    _verify_exact_submission_root(submissions_root, expected_refs)
    if sum(record.bytes for record in ledger.submissions) > MAX_TOTAL_SUBMISSION_BYTES:
        raise GovernanceContractError("total declared submission bytes exceed bounded budget")

    packet_by_key = {item.item_key: item for item in packet.items}
    round_by_id = {round_.review_round_id: round_ for round_ in ledger.review_rounds}
    submissions_by_reviewer: dict[tuple[str, str], tuple[LabelSubmission, str]] = {}
    responses_by_reviewer: dict[tuple[str, str], dict[str, LabelResponse]] = {}
    for record in ledger.submissions:
        submission_path = Path(submissions_root).joinpath(*PurePosixPath(record.portable_ref).parts)
        submission, raw = _load_canonical_model(
            submission_path,
            LabelSubmission,
            f"submission {record.submission_id}",
            max_bytes=MAX_SUBMISSION_BYTES,
            expected_sha256=record.sha256,
            expected_bytes=record.bytes,
        )
        if submission.policy_sha256 != POLICY_SHA256:
            raise GovernanceContractError(f"submission {record.submission_id} policy differs")
        if submission.packet_sha256 != packet_sha256:
            raise GovernanceContractError(f"submission {record.submission_id} packet differs")
        if submission.submission_id != record.submission_id:
            raise GovernanceContractError(f"submission identity differs for {record.portable_ref}")
        if submission.review_round_id != record.review_round_id:
            raise GovernanceContractError(
                f"submission review round differs for {record.portable_ref}"
            )
        if submission.labeler_id != record.labeler_id:
            raise GovernanceContractError(f"submission labeler differs for {record.portable_ref}")
        round_ = round_by_id[record.review_round_id]
        if submission.submitted_at_utc < packet.prepared_at_utc:
            raise GovernanceContractError(f"submission {record.submission_id} predates packet")
        if submission.submitted_at_utc < round_.opened_at_utc:
            raise GovernanceContractError(
                f"submission {record.submission_id} predates its review round"
            )
        if submission.submitted_at_utc > round_.completed_at_utc:
            raise GovernanceContractError(
                f"submission {record.submission_id} is after its review round"
            )
        response_by_key = {response.item_key: response for response in submission.responses}
        if set(response_by_key) != set(packet_by_key):
            raise GovernanceContractError(
                f"submission {record.submission_id} does not exactly cover packet items"
            )
        for item_key, response in response_by_key.items():
            if response.decided_at_utc < packet.prepared_at_utc:
                raise GovernanceContractError(
                    f"submission {record.submission_id} contains a response decided "
                    "before the packet was prepared"
                )
            if response.decided_at_utc < round_.opened_at_utc:
                raise GovernanceContractError(
                    f"submission {record.submission_id} contains a response decided "
                    "before its review round opened"
                )
            if _binding(response) != _binding(packet_by_key[item_key]):
                raise GovernanceContractError(
                    f"submission {record.submission_id} changed evidence for {item_key}"
                )
        reviewer_key = (record.review_round_id, record.labeler_id)
        submissions_by_reviewer[reviewer_key] = (submission, _sha256(raw))
        responses_by_reviewer[reviewer_key] = response_by_key

    # Re-scan after every bounded read so an added/removed entry cannot turn a
    # transient root into an accepted custody inventory.
    _verify_exact_submission_root(submissions_root, expected_refs)

    expected_reviewers = {
        (round_.review_round_id, labeler_id)
        for round_ in ledger.review_rounds
        for labeler_id in round_.labeler_ids
    }
    if set(submissions_by_reviewer) != expected_reviewers:
        raise GovernanceContractError(
            "loaded submissions do not exactly cover every retained review round"
        )

    events_by_item: dict[str, list[DecisionEvent]] = {}
    for event in ledger.decisions:
        packet_item = packet_by_key.get(event.item_key)
        if packet_item is None:
            raise GovernanceContractError(f"decision {event.decision_id} has unknown item_key")
        if _binding(event) != _binding(packet_item):
            raise GovernanceContractError(f"decision {event.decision_id} changed packet evidence")
        event_round = round_by_id.get(event.review_round_id)
        if event_round is None:
            raise GovernanceContractError(f"decision {event.decision_id} has unknown review round")
        if event.reviewer_ids != event_round.labeler_ids:
            raise GovernanceContractError(f"decision {event.decision_id} reviewer set differs")
        if event.adjudicator_id != event_round.adjudicator_id:
            raise GovernanceContractError(f"decision {event.decision_id} adjudicator differs")
        latest_submission_time = max(
            submissions_by_reviewer[(event.review_round_id, labeler_id)][0].submitted_at_utc
            for labeler_id in event_round.labeler_ids
        )
        if event.decided_at_utc < latest_submission_time:
            raise GovernanceContractError(
                f"decision {event.decision_id} predates an independent submission"
            )
        for vote in event.votes:
            reviewer_key = (event.review_round_id, vote.labeler_id)
            submission, submission_sha256 = submissions_by_reviewer[reviewer_key]
            if vote.submission_sha256 != submission_sha256:
                raise GovernanceContractError(
                    f"decision {event.decision_id} vote has wrong submission hash"
                )
            response = responses_by_reviewer[reviewer_key][event.item_key]
            if vote.response_sha256 != _response_sha256(response):
                raise GovernanceContractError(
                    f"decision {event.decision_id} vote has wrong response hash"
                )
        events_by_item.setdefault(event.item_key, []).append(event)
    if set(events_by_item) != set(packet_by_key):
        raise GovernanceContractError("decision events do not exactly cover packet items")

    active_decisions: list[str] = []
    correction_events = 0
    for item_key, events in events_by_item.items():
        revisions = [event.revision for event in events]
        if revisions != list(range(1, len(events) + 1)):
            raise GovernanceContractError(f"item {item_key} revisions are not contiguous from 1")
        round_sequences = [round_by_id[event.review_round_id].sequence for event in events]
        if round_sequences != sorted(round_sequences):
            raise GovernanceContractError(f"item {item_key} review rounds move backwards")
        for previous, current in zip(events, events[1:], strict=False):
            if current.supersedes_decision_id != previous.decision_id:
                raise GovernanceContractError(
                    f"item {item_key} correction does not supersede immediate prior decision"
                )
            correction_events += 1
        active_decisions.append(events[-1].decision_id)
    if sorted(active_decisions) != ledger.active_decision_ids:
        raise GovernanceContractError("active_decision_ids differ from latest retained decisions")
    if (
        ledger.revision_context.kind == LedgerRevisionKind.POST_FREEZE_CORRECTION
        and (
            correction_events == 0
            or not any(
            event.review_round_id == ledger.active_review_round_id and event.revision > 1
            for event in ledger.decisions
            )
        )
    ):
        raise GovernanceContractError(
            "post-freeze correction ledger retains no active-round correction event"
        )

    active_round = round_by_id[ledger.active_review_round_id]
    return GovernanceVerificationResult(
        contract_kind="LABELING_GOVERNANCE",
        source_contract_kind=_source_contract_kind(source_manifest),
        artifact_sha256=_sha256(ledger_raw),
        item_or_document_count=len(packet.items),
        independent_labeler_count=len(active_round.labeler_ids),
        holdout_document_count=sum(
            document.split.value == "BLIND_HOLDOUT"
            for document in blind_split.documents
        ),
        candidate_frozen=(
            blind_split.candidate_freeze.status == CandidateFreezeStatus.FROZEN
        ),
    )


def verify_blind_split(
    *,
    manifest_path: Path,
    expected_manifest_sha256: str,
    source_manifest_path: Path,
    expected_source_manifest_sha256: str,
    acceptance_policy_path: Path,
    _allow_test_source_contract: bool = False,
) -> GovernanceVerificationResult:
    """Verify whole-document/whole-lineage blind split governance only."""

    _verify_policy(acceptance_policy_path)
    source_manifest = _load_verified_source_manifest(
        path=source_manifest_path,
        expected_sha256=expected_source_manifest_sha256,
        acceptance_policy_path=acceptance_policy_path,
        allow_test_contract=_allow_test_source_contract,
    )
    manifest, raw = _load_canonical_model(
        manifest_path,
        BlindSplitManifest,
        "blind split manifest",
        max_bytes=MAX_SPLIT_BYTES,
        expected_sha256=expected_manifest_sha256,
    )
    if manifest.policy_sha256 != POLICY_SHA256:
        raise GovernanceContractError("blind split manifest does not bind the frozen policy")
    if manifest.source_manifest_sha256 != expected_source_manifest_sha256:
        raise GovernanceContractError(
            "blind split differs from independently expected source manifest"
        )
    _crosscheck_split_sources(manifest, source_manifest)
    holdout_count = sum(document.split.value == "BLIND_HOLDOUT" for document in manifest.documents)
    return GovernanceVerificationResult(
        contract_kind="BLIND_SPLIT_GOVERNANCE",
        source_contract_kind=_source_contract_kind(source_manifest),
        artifact_sha256=_sha256(raw),
        item_or_document_count=len(manifest.documents),
        independent_labeler_count=0,
        holdout_document_count=holdout_count,
        candidate_frozen=manifest.candidate_freeze.status == CandidateFreezeStatus.FROZEN,
    )
