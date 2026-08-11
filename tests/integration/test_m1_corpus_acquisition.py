"""M1 source acquisition contract; intentionally contains no labels or measurement."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from normshift.adapters.base import ADAPTER_VERSION, NORMALIZATION_VERSION
from normshift.adapters.registry import load_document
from normshift.corpus.acquisition import (
    FROZEN_POLICY_ID,
    FROZEN_POLICY_REF,
    FROZEN_POLICY_SHA256,
    MAX_MANIFEST_BYTES,
    MAX_POLICY_BYTES,
    AcquisitionError,
    FetchResult,
    SourceRecord,
    acquire_corpus,
    load_source_manifest,
    verify_corpus_offline,
)
from normshift.model.types import AdapterName

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "fixtures" / "corpus"
TEST_POLICY_BYTES = b'{"policy_id":"test-prereg-v1","status":"FROZEN_PRE_RESULT"}\n'


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture_sources() -> dict[str, tuple[str, str, bytes]]:
    return {
        "rfc-source": (
            "rfc",
            "rfc2119",
            (CORPUS / "rfc" / "sample-v1.html").read_bytes(),
        ),
        "w3c-source": (
            "w3c",
            "rfc2119",
            (CORPUS / "w3c" / "sample-v1.html").read_bytes(),
        ),
        "whatwg-source": (
            "whatwg",
            "whatwg",
            (CORPUS / "whatwg" / "sample-v1.html").read_bytes(),
        ),
    }


def _manifest_payload() -> tuple[dict[str, Any], dict[str, bytes]]:
    fixture_sources = _fixture_sources()
    sources: list[dict[str, Any]] = []
    raw_by_id: dict[str, bytes] = {}
    for source_id, (family, profile, raw) in fixture_sources.items():
        adapter = AdapterName(family)
        filename = f"{source_id}.html"
        fixture_path = CORPUS / family / "sample-v1.html"
        document_version = load_document(fixture_path, adapter).document_version
        url = f"https://standards.example.test/{family}/{filename}"
        sources.append(
            {
                "source_id": source_id,
                "family": family,
                "adapter": family,
                "profile": profile,
                "adapter_version": ADAPTER_VERSION,
                "normalization_version": NORMALIZATION_VERSION,
                "identity_preflight_version": "1.0.0",
                "standard_id": f"{family}-fixture-standard",
                "version_or_date": "fixture-v1",
                "document_version": document_version,
                "canonical_url": url,
                "acquisition_url": url,
                "curator_retrieved_at_utc": "2026-08-11T00:00:00Z",
                "redirect_chain": [url],
                "etag": f'"{source_id}-etag"',
                "last_modified": "Mon, 10 Aug 2026 00:00:00 GMT",
                "media_type": "text/html",
                "charset": "utf-8",
                "content_sha256": _sha256(raw),
                "byte_length": len(raw),
                "local_ref": f"snapshots/{family}/{filename}",
                "license": {
                    "document_or_license": "Test-only fixture license record",
                    "url": "https://standards.example.test/license/",
                    "redistribution_basis": "Repository test fixture; not real-source evidence.",
                    "snapshot_distribution": "embedded",
                },
            }
        )
        raw_by_id[source_id] = raw
    return (
        {
            "schema_version": "normshift-m1-source-manifest/v1",
            "corpus_id": "acquisition-contract-test",
            "corpus_kind": "SOURCE_CONTRACT_TEST",
            "adjudication_status": "EXPERIMENTAL_NOT_ADJUDICATED",
            "acceptance_policy": {
                "id": "test-prereg-v1",
                "sha256": _sha256(TEST_POLICY_BYTES),
                "local_ref": "test-prereg-policy.json",
                "status": "FROZEN_PRE_RESULT",
            },
            "ground_truth_status": "NOT_INCLUDED",
            "sources": sources,
        },
        raw_by_id,
    )


def _actual_contract_payload() -> dict[str, Any]:
    definitions = [
        (
            "rfc-2246",
            "rfc",
            "rfc2119",
            CORPUS / "rfc" / "sample-v1.html",
            "RFC 2246",
            "1999-01",
            "https://www.rfc-editor.org/rfc/rfc2246.html",
        ),
        (
            "rfc-4346",
            "rfc",
            "rfc2119",
            CORPUS / "rfc" / "sample-v2.html",
            "RFC 4346",
            "2006-04",
            "https://www.rfc-editor.org/rfc/rfc4346.html",
        ),
        (
            "w3c-micropub-cr",
            "w3c",
            "rfc2119",
            CORPUS / "w3c" / "sample-v1.html",
            "Micropub",
            "2016-08-16",
            "https://www.w3.org/TR/2016/CR-micropub-20160816/",
        ),
        (
            "w3c-micropub-pr",
            "w3c",
            "rfc2119",
            CORPUS / "w3c" / "sample-v2.html",
            "Micropub",
            "2017-01-19",
            "https://www.w3.org/TR/2017/PR-micropub-20170119/",
        ),
        (
            "whatwg-mimesniff-2023-07",
            "whatwg",
            "whatwg",
            CORPUS / "whatwg" / "sample-v1.html",
            "MIME Sniffing",
            "2023-07",
            "https://mimesniff.spec.whatwg.org/review-drafts/2023-07/",
        ),
        (
            "whatwg-mimesniff-2024-07",
            "whatwg",
            "whatwg",
            CORPUS / "whatwg" / "sample-v2.html",
            "MIME Sniffing",
            "2024-07",
            "https://mimesniff.spec.whatwg.org/review-drafts/2024-07/",
        ),
    ]
    sources: list[dict[str, Any]] = []
    for source_id, family, profile, fixture, standard_id, version_or_date, url in definitions:
        raw = fixture.read_bytes()
        document_version = load_document(fixture, AdapterName(family)).document_version
        sources.append(
            {
                "source_id": source_id,
                "family": family,
                "adapter": family,
                "profile": profile,
                "adapter_version": ADAPTER_VERSION,
                "normalization_version": NORMALIZATION_VERSION,
                "identity_preflight_version": "1.0.0",
                "standard_id": standard_id,
                "version_or_date": version_or_date,
                "document_version": document_version,
                "canonical_url": url,
                "acquisition_url": url,
                "curator_retrieved_at_utc": "2026-08-11T00:00:00Z",
                "redirect_chain": [url],
                "etag": f'"{source_id}-etag"',
                "last_modified": "Mon, 10 Aug 2026 00:00:00 GMT",
                "media_type": "text/html",
                "charset": "utf-8",
                "content_sha256": _sha256(raw),
                "byte_length": len(raw),
                "local_ref": f"snapshots/{family}/{source_id}.html",
                "license": {
                    "document_or_license": "Ephemeral test fixture license record",
                    "url": "https://standards.example.test/license/",
                    "redistribution_basis": "Test-only bytes; never actual M1 evidence.",
                    "snapshot_distribution": "embedded",
                },
            }
        )
    return {
        "schema_version": "normshift-m1-source-manifest/v1",
        "corpus_id": "ephemeral-actual-contract-branch-coverage",
        "corpus_kind": "ACTUAL_STANDARDS_SOURCE_CONTRACT",
        "adjudication_status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "acceptance_policy": {
            "id": FROZEN_POLICY_ID,
            "sha256": FROZEN_POLICY_SHA256,
            "local_ref": FROZEN_POLICY_REF,
            "status": "FROZEN_BEFORE_BLIND_EVALUATION",
        },
        "ground_truth_status": "NOT_INCLUDED",
        "sources": sources,
    }


def _write_manifest(path: Path, payload: dict[str, Any]) -> str:
    raw = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    path.write_bytes(raw)
    return _sha256(raw)


def _write_policy(tmp_path: Path) -> Path:
    policy = tmp_path / "test-prereg-policy.json"
    policy.write_bytes(TEST_POLICY_BYTES)
    return policy


def _load_actual_contract(tmp_path: Path, payload: dict[str, Any]):
    manifest_path = tmp_path / "actual-sources.json"
    digest = _write_manifest(manifest_path, payload)
    return load_source_manifest(
        manifest_path,
        expected_sha256=digest,
        acceptance_policy_path=ROOT / FROZEN_POLICY_REF,
    )


def _fetcher(raw_by_id: dict[str, bytes]):
    def fetch(record: SourceRecord) -> FetchResult:
        raw = raw_by_id[record.source_id]
        content_type = record.media_type
        if record.charset is not None:
            content_type += f"; charset={record.charset}"
        return FetchResult(
            data=raw,
            redirect_chain=record.redirect_chain,
            etag=record.etag,
            last_modified=record.last_modified,
            content_type=content_type,
            content_encoding=None,
            content_length=str(len(raw)),
        )

    return fetch


def _acquire_valid(tmp_path: Path) -> tuple[Path, Path, Path, str, dict[str, bytes]]:
    payload, raw_by_id = _manifest_payload()
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    snapshot_root = tmp_path / "corpus"
    snapshot_root.mkdir()
    policy_path = _write_policy(tmp_path)
    result = acquire_corpus(
        manifest_path,
        snapshot_root,
        manifest_sha256=digest,
        acceptance_policy_path=policy_path,
        fetcher=_fetcher(raw_by_id),
        allow_test_contract=True,
    )
    assert result.mode == "ACQUIRED"
    return manifest_path, policy_path, snapshot_root, digest, raw_by_id


def test_acquire_then_replay_three_families_without_network(tmp_path: Path) -> None:
    manifest_path, policy_path, snapshot_root, digest, _ = _acquire_valid(tmp_path)

    result = verify_corpus_offline(
        manifest_path,
        snapshot_root,
        manifest_sha256=digest,
        acceptance_policy_path=policy_path,
        allow_test_contract=True,
    )

    assert result.mode == "OFFLINE_VERIFIED"
    assert result.source_count == 3
    assert result.families == ("rfc", "w3c", "whatwg")
    receipts = sorted(snapshot_root.rglob("*.receipt.json"))
    assert len(receipts) == 3
    for receipt in receipts:
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        assert payload["manifest_sha256"] == digest
        assert payload["adjudication_status"] == "EXPERIMENTAL_NOT_ADJUDICATED"


def test_complete_acquisition_is_idempotently_verified_not_refetched(tmp_path: Path) -> None:
    manifest_path, policy_path, snapshot_root, digest, _ = _acquire_valid(tmp_path)

    def forbidden_fetch(_record: SourceRecord) -> FetchResult:
        raise AssertionError("network fetch must not run for a complete local corpus")

    result = acquire_corpus(
        manifest_path,
        snapshot_root,
        manifest_sha256=digest,
        acceptance_policy_path=policy_path,
        fetcher=forbidden_fetch,
        allow_test_contract=True,
    )
    assert result.mode == "OFFLINE_VERIFIED"


def test_wrong_manifest_hash_fails_before_fetch_or_output(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    manifest_path = tmp_path / "sources.json"
    _write_manifest(manifest_path, payload)
    snapshot_root = tmp_path / "corpus"
    snapshot_root.mkdir()
    policy_path = _write_policy(tmp_path)

    def forbidden_fetch(_record: SourceRecord) -> FetchResult:
        raise AssertionError("fetch must not run before manifest hash verification")

    with pytest.raises(AcquisitionError, match="manifest SHA-256 mismatch"):
        acquire_corpus(
            manifest_path,
            snapshot_root,
            manifest_sha256="0" * 64,
            acceptance_policy_path=policy_path,
            fetcher=forbidden_fetch,
            allow_test_contract=True,
        )
    assert list(snapshot_root.rglob("*")) == []


def test_strict_manifest_rejects_duplicate_keys(tmp_path: Path) -> None:
    manifest_path = tmp_path / "sources.json"
    raw = b'{"schema_version":"x","schema_version":"x"}\n'
    manifest_path.write_bytes(raw)
    with pytest.raises(AcquisitionError, match="Duplicate JSON object key"):
        load_source_manifest(
            manifest_path,
            expected_sha256=_sha256(raw),
            acceptance_policy_path=tmp_path / "unused-policy.json",
            allow_test_contract=True,
        )


def test_manifest_rejects_unknown_fields(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    payload["unexpected"] = True
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError, match="schema validation failed"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("canonical_url", "http://standards.example.test/source.html"),
        ("acquisition_url", "https://Standards.example.test/source.html"),
        ("canonical_url", "https://user@standards.example.test/source.html"),
        ("canonical_url", "https://standards.example.test/a/%2e%2e/source.html"),
        ("canonical_url", "https://standards.example.test/source.html#fragment"),
    ],
)
def test_manifest_rejects_noncanonical_source_urls(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    payload, _ = _manifest_payload()
    payload["sources"][0][field] = value
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_manifest_rejects_casefold_output_collision(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    payload["sources"][0]["local_ref"] = "snapshots/shared/SOURCE.html"
    payload["sources"][1]["local_ref"] = "snapshots/shared/source.html"
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError, match="portable output spelling collision"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_manifest_rejects_casefold_parent_directory_collision(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    payload["sources"][0]["local_ref"] = "snapshots/RFC/first.html"
    payload["sources"][1]["local_ref"] = "snapshots/rfc/second.html"
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError, match="portable output spelling collision"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


@pytest.mark.parametrize("segment", ["CON", "aux.txt", "trailing.", "trailing "])
def test_manifest_rejects_windows_unsafe_output_segments(
    tmp_path: Path,
    segment: str,
) -> None:
    payload, _ = _manifest_payload()
    payload["sources"][0]["local_ref"] = f"snapshots/rfc/{segment}"
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError, match="Windows"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_manifest_rejects_canonical_final_url_disagreement(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    payload["sources"][0]["canonical_url"] = (
        "https://standards.example.test/rfc/different.html"
    )
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError, match="must equal the frozen final response URL"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_test_contract_is_forbidden_without_explicit_test_mode(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError, match="test-only source contracts are forbidden"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
        )


def test_acceptance_policy_bytes_and_id_are_bound(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    policy_path.write_bytes(TEST_POLICY_BYTES.replace(b"test-prereg-v1", b"other-policy-x"))
    with pytest.raises(AcquisitionError, match="acceptance policy SHA-256 mismatch"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_actual_contract_requires_two_versions_per_family(tmp_path: Path) -> None:
    payload, _ = _manifest_payload()
    payload["corpus_kind"] = "ACTUAL_STANDARDS_SOURCE_CONTRACT"
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    policy_path = _write_policy(tmp_path)
    with pytest.raises(AcquisitionError, match="schema validation failed"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
        )


def test_valid_actual_contract_binds_policy_and_all_authoritative_url_forms(
    tmp_path: Path,
) -> None:
    manifest = _load_actual_contract(tmp_path, _actual_contract_payload())
    assert manifest.corpus_kind == "ACTUAL_STANDARDS_SOURCE_CONTRACT"
    assert manifest.acceptance_policy_id == FROZEN_POLICY_ID
    assert manifest.acceptance_policy_sha256 == FROZEN_POLICY_SHA256
    assert len(manifest.sources) == 6


def test_actual_contract_rejects_renamed_duplicate_bytes_as_two_versions(
    tmp_path: Path,
) -> None:
    payload = _actual_contract_payload()
    first = payload["sources"][0]
    second = payload["sources"][1]
    second.update(
        {
            "standard_id": first["standard_id"],
            "version_or_date": "2000-01",
            "document_version": first["document_version"],
            "canonical_url": first["canonical_url"],
            "acquisition_url": first["acquisition_url"],
            "redirect_chain": first["redirect_chain"],
            "content_sha256": first["content_sha256"],
            "byte_length": first["byte_length"],
        }
    )
    with pytest.raises(AcquisitionError, match="document_version.*content_sha256.*canonical_url"):
        _load_actual_contract(tmp_path, payload)


@pytest.mark.parametrize(
    ("source_index", "url", "version_or_date", "standard_id", "error"),
    [
        (
            0,
            "https://www.rfc-editor.org/about/",
            "1999-01",
            "RFC 2246",
            "exact RFC Editor resource",
        ),
        (
            0,
            "https://www.rfc-editor.org/rfc/rfc2246.html",
            "1999-01",
            "RFC 9999",
            "standard_id must equal",
        ),
        (
            2,
            "https://www.w3.org/TR/micropub/",
            "2016-08-16",
            "Micropub",
            "dated W3C /TR/ version",
        ),
        (
            2,
            "https://www.w3.org/TR/2016/CR-micropub-20160816/",
            "2016-08-17",
            "Micropub",
            "version_or_date must match",
        ),
        (
            4,
            "https://mimesniff.spec.whatwg.org/",
            "2023-07",
            "MIME Sniffing",
            "frozen commit or review draft",
        ),
        (
            4,
            "https://mimesniff.spec.whatwg.org/review-drafts/2023-07/",
            "2023-08",
            "MIME Sniffing",
            "version_or_date must match",
        ),
    ],
)
def test_actual_contract_rejects_non_authoritative_or_mismatched_identity(
    tmp_path: Path,
    source_index: int,
    url: str,
    version_or_date: str,
    standard_id: str,
    error: str,
) -> None:
    payload = _actual_contract_payload()
    source = payload["sources"][source_index]
    source["canonical_url"] = url
    source["acquisition_url"] = url
    source["redirect_chain"] = [url]
    source["version_or_date"] = version_or_date
    source["standard_id"] = standard_id
    with pytest.raises(AcquisitionError, match=error):
        _load_actual_contract(tmp_path, payload)


def test_acquisition_preflight_ignores_ambient_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("rfc-source.html.meta.json").write_text(
        '{"canonical_source":"https://attacker.example.test/forged"}\n',
        encoding="utf-8",
    )
    work = tmp_path / "work"
    work.mkdir()
    _acquire_valid(work)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        (lambda result: replace(result, etag='"stale"'), "ETag differs"),
        (
            lambda result: replace(result, last_modified="Sun, 09 Aug 2026 00:00:00 GMT"),
            "Last-Modified differs",
        ),
        (
            lambda result: replace(
                result,
                redirect_chain=("https://standards.example.test/unexpected.html",),
            ),
            "redirect chain differs",
        ),
        (lambda result: replace(result, content_encoding="gzip"), "Content-Encoding"),
        (lambda result: replace(result, content_type="text/plain"), "media type"),
        (
            lambda result: replace(result, content_type="text/html; charset=us-ascii"),
            "charset",
        ),
        (lambda result: replace(result, content_length="1"), "Content-Length"),
        (
            lambda result: replace(
                result,
                data=bytes([result.data[0] ^ 1]) + result.data[1:],
            ),
            "content SHA-256 mismatch",
        ),
    ],
)
def test_fetch_contract_failures_leave_no_outputs(
    tmp_path: Path,
    mutation: Any,
    error: str,
) -> None:
    payload, raw_by_id = _manifest_payload()
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    snapshot_root = tmp_path / "corpus"
    snapshot_root.mkdir()
    policy_path = _write_policy(tmp_path)
    base_fetch = _fetcher(raw_by_id)

    def fetch(record: SourceRecord) -> FetchResult:
        result = base_fetch(record)
        return mutation(result) if record.source_id == "rfc-source" else result

    with pytest.raises(AcquisitionError, match=error):
        acquire_corpus(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            fetcher=fetch,
            allow_test_contract=True,
        )
    assert list(snapshot_root.rglob("*")) == []


def test_later_fetch_failure_leaves_no_partial_outputs(tmp_path: Path) -> None:
    payload, raw_by_id = _manifest_payload()
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    snapshot_root = tmp_path / "corpus"
    snapshot_root.mkdir()
    policy_path = _write_policy(tmp_path)
    base_fetch = _fetcher(raw_by_id)

    def fetch(record: SourceRecord) -> FetchResult:
        if record.source_id == "w3c-source":
            raise AcquisitionError("injected second-source failure")
        return base_fetch(record)

    with pytest.raises(AcquisitionError, match="injected second-source failure"):
        acquire_corpus(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            fetcher=fetch,
            allow_test_contract=True,
        )
    assert list(snapshot_root.rglob("*")) == []


def test_adapter_wrong_family_fails_before_any_output(tmp_path: Path) -> None:
    payload, raw_by_id = _manifest_payload()
    rfc = payload["sources"][0]
    w3c_bytes = raw_by_id["w3c-source"]
    rfc["content_sha256"] = _sha256(w3c_bytes)
    rfc["byte_length"] = len(w3c_bytes)
    raw_by_id["rfc-source"] = w3c_bytes
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    snapshot_root = tmp_path / "corpus"
    snapshot_root.mkdir()
    policy_path = _write_policy(tmp_path)

    with pytest.raises(AcquisitionError, match="source identity preflight rejected"):
        acquire_corpus(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            fetcher=_fetcher(raw_by_id),
            allow_test_contract=True,
        )
    assert list(snapshot_root.rglob("*")) == []


@pytest.mark.parametrize("suffix", ["", ".meta.json", ".receipt.json"])
def test_offline_replay_rejects_mutated_source_or_provenance(
    tmp_path: Path,
    suffix: str,
) -> None:
    manifest_path, policy_path, snapshot_root, digest, _ = _acquire_valid(tmp_path)
    target = snapshot_root / f"snapshots/rfc/rfc-source.html{suffix}"
    original = target.read_bytes()
    target.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    with pytest.raises(AcquisitionError):
        verify_corpus_offline(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_offline_replay_rejects_unmanifested_extra_file(tmp_path: Path) -> None:
    manifest_path, policy_path, snapshot_root, digest, _ = _acquire_valid(tmp_path)
    (snapshot_root / "unmanifested.txt").write_text("extra", encoding="utf-8")
    with pytest.raises(AcquisitionError, match="snapshot inventory differs"):
        verify_corpus_offline(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_offline_replay_rejects_extra_empty_directory(tmp_path: Path) -> None:
    manifest_path, policy_path, snapshot_root, digest, _ = _acquire_valid(tmp_path)
    (snapshot_root / "unmanifested-empty").mkdir()
    with pytest.raises(AcquisitionError, match="snapshot inventory differs"):
        verify_corpus_offline(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_oversized_manifest_is_rejected_before_json_parse(tmp_path: Path) -> None:
    manifest_path = tmp_path / "oversized.json"
    raw = b"{" + (b" " * MAX_MANIFEST_BYTES)
    manifest_path.write_bytes(raw)
    with pytest.raises(AcquisitionError, match="manifest exceeds"):
        load_source_manifest(
            manifest_path,
            expected_sha256=_sha256(raw),
            acceptance_policy_path=tmp_path / "unused-policy.json",
            allow_test_contract=True,
        )


def test_oversized_policy_is_rejected_before_json_parse(tmp_path: Path) -> None:
    policy_path = tmp_path / "test-prereg-policy.json"
    oversized_policy = b"{" + (b" " * MAX_POLICY_BYTES)
    policy_path.write_bytes(oversized_policy)
    payload, _ = _manifest_payload()
    payload["acceptance_policy"]["sha256"] = _sha256(oversized_policy)
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    with pytest.raises(AcquisitionError, match="acceptance policy exceeds"):
        load_source_manifest(
            manifest_path,
            expected_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_offline_replay_rejects_source_size_before_read(tmp_path: Path) -> None:
    manifest_path, policy_path, snapshot_root, digest, _ = _acquire_valid(tmp_path)
    source = snapshot_root / "snapshots/rfc/rfc-source.html"
    source.write_bytes(source.read_bytes() + b"x")
    with pytest.raises(AcquisitionError, match="source size mismatch"):
        verify_corpus_offline(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


@pytest.mark.parametrize("suffix", [".meta.json", ".receipt.json"])
def test_offline_replay_rejects_sidecar_size_before_read(
    tmp_path: Path,
    suffix: str,
) -> None:
    manifest_path, policy_path, snapshot_root, digest, _ = _acquire_valid(tmp_path)
    sidecar = snapshot_root / f"snapshots/rfc/rfc-source.html{suffix}"
    sidecar.write_bytes(sidecar.read_bytes() + b"x")
    with pytest.raises(AcquisitionError, match="size mismatch"):
        verify_corpus_offline(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            allow_test_contract=True,
        )


def test_partial_existing_acquisition_is_preserved_and_rejected(tmp_path: Path) -> None:
    payload, raw_by_id = _manifest_payload()
    manifest_path = tmp_path / "sources.json"
    digest = _write_manifest(manifest_path, payload)
    snapshot_root = tmp_path / "corpus"
    partial = snapshot_root / "snapshots/rfc/rfc-source.html"
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b"preserve-me")
    policy_path = _write_policy(tmp_path)

    with pytest.raises(AcquisitionError, match="partial acquisition"):
        acquire_corpus(
            manifest_path,
            snapshot_root,
            manifest_sha256=digest,
            acceptance_policy_path=policy_path,
            fetcher=_fetcher(raw_by_id),
            allow_test_contract=True,
        )
    assert partial.read_bytes() == b"preserve-me"
    assert [path for path in snapshot_root.rglob("*") if path.is_file()] == [partial]


def test_repository_and_packaged_manifest_schemas_are_identical() -> None:
    assert (ROOT / "schemas" / "m1_source_manifest_v1.schema.json").read_bytes() == (
        ROOT / "src" / "normshift" / "schemas" / "m1_source_manifest_v1.schema.json"
    ).read_bytes()


def test_manifest_fixture_builder_does_not_embed_labels_or_holdout() -> None:
    payload, _ = _manifest_payload()
    serialized = json.dumps(deepcopy(payload), sort_keys=True).lower()
    assert payload["ground_truth_status"] == "NOT_INCLUDED"
    assert "threshold" not in serialized
    assert "holdout" not in serialized
    assert "label" not in serialized
