"""Network-free verification of the adopted M1 development source recipes."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

import normshift.corpus.evidence_inventory as evidence_inventory_module
from normshift.corpus.acquisition import FROZEN_POLICY_SHA256
from normshift.corpus.evidence_inventory import (
    EvidenceInventoryError,
    verify_evidence_root,
    verify_source_recipe_evidence,
)
from normshift.corpus.header_sanitization import (
    FORBIDDEN_VALUE_MARKERS,
    REPORT_SHA256,
)
from normshift.strict_json import strict_loads

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "corpus" / "m1-development"
POLICY = ROOT / "acceptance" / "m1_m2_prereg_v1.json"
INVENTORY_SHA256 = "0eb3e50d0c35eb091b181f8cfe2007cc88b6496d38147870570e0219d92b5938"
MANIFEST_SHA256 = "a2cfd4efa43fc2e90a76ded6e6c461bbf42ccd445cd674009cc083faa7102aaf"
EXPECTED_SOURCE_HASHES = {
    "rfc-tls-1.0-rfc2246": "82ef7a3d371e5801b445aea0c639b1fa0851ae542d740a5b238d00e07d6c3cf3",
    "rfc-tls-1.1-rfc4346": "b58c88a5bb51205bf656cf80b5053d9eb32db38847daea95b4402b91da7bba1e",
    "rfc-tls-1.2-rfc5246": "a6102891f08ad01933fdce6891c0045432b699c917db12903cfa694372b5e86a",
    "w3c-micropub-cr-20161018": (
        "8341ae06105a972b8c5e2e60d9924722a174705b7396619caf734c3b7db890f3"
    ),
    "w3c-micropub-pr-20170413": (
        "3edf8e00e5b1068ad83f8a714531d9980acbcee655848f0cc405ba3f8b640597"
    ),
    "w3c-micropub-rec-20170523": (
        "9eebd4b244e9b0fce61ab6830a79527ff780ebcd225316009451a9c6d902551d"
    ),
    "whatwg-mimesniff-review-2023-07": (
        "01528914273a059ea6d61035f0b778013b128a3635421da91c3a4199c09cf109"
    ),
    "whatwg-mimesniff-review-2024-07": (
        "596ec6c40da0dc935e4664d03d6ac9ea55d3d7787d9eee24bb303cc84717218f"
    ),
    "whatwg-mimesniff-review-2025-01": (
        "b5388f593d4941b61015659e57daca1e7e9eb44508ee04b3854a9b2f2b4e7421"
    ),
    "whatwg-mimesniff-review-2025-07": (
        "db83d3e4a68e6a89361ef10c8113ea569feb05c7782818d9b6223a0b213117b7"
    ),
}
EXPECTED_ORIGINAL_HEADER_HASHES = {
    "curation-headers/chain/whatwg-mimesniff-review-drafts.headers.txt": (
        "df9321f5817987bd764970af6f5bd21819cca8c8c019e578ba320ff2cae426cc"
    ),
    "curation-headers/first/rfc-tls-1.0.headers.txt": (
        "4044df4a16d6452a195807bf0174ce8ecd138eb0ae2365180fa97fa089dc953a"
    ),
    "curation-headers/first/rfc-tls-1.1.headers.txt": (
        "0600930f99e5b8667623c1034012a4a1423d81537f07cfa41350febc26044639"
    ),
    "curation-headers/first/rfc-tls-1.2.headers.txt": (
        "1ad6e4e4e02b15cc6f04ef05930c064f1b0c714d451e3eb1d7a99643902c4e0e"
    ),
    "curation-headers/first/w3c-micropub-cr-20161018.headers.txt": (
        "986017dda1ce768dcf65b3ce4b4311e63007fa5b377b2283c516323cbf55a4ee"
    ),
    "curation-headers/first/w3c-micropub-pr-20170413.headers.txt": (
        "9fa4d189cd7181f77029e12078bfd4440f88ea7993c4ea0bd2432de7ece43c42"
    ),
    "curation-headers/first/w3c-micropub-rec-20170523.headers.txt": (
        "cbc895b9700bd5ad3bb1a9aff2b75e5387816cc28a1e25c93e6d8214d642f70f"
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2023-07.headers.txt": (
        "b86fa828cee6c824d2ec4f7413484914d5886bd4041a2c019d1758ef976c8111"
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2024-07.headers.txt": (
        "8ad8e1537c74abd231c4cbe8a6384a4e0209b2c6e2ff15c2baa168c8f9c7b132"
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2025-01.headers.txt": (
        "5faa963eedc6857d20371bf7da5302e2584b30ea340a05b51c29bc2373c86bcc"
    ),
    "curation-headers/first/whatwg-mimesniff-rd-2025-07.headers.txt": (
        "93a3cdb15fadfa75df17e89712112181200fb8ae988112ae4f933f3b5739738b"
    ),
    "curation-headers/license/CC-BY-4.0-legalcode.headers.txt": (
        "00a88da3b3dfbede35febbe96225d187933ade3560109dbb19461580a5e0de0b"
    ),
    "curation-headers/license/IETF-TLP-5.headers.txt": (
        "3c6f334aac7a4bd8dacf337d5eab962a3fda291fc479fefd1c56174975c78fef"
    ),
    "curation-headers/license/IETF-TLP-FAQ.headers.txt": (
        "9971d573345574b6c6d5b3934d1f073030f3d2256b455c80d3d1a0ac6c7a4377"
    ),
    "curation-headers/license/W3C-Software-Document-License-2015.headers.txt": (
        "4238c064f29759eb562509dc82508e83b2283a8881547c91032ffef2ec740699"
    ),
    "curation-headers/license/WHATWG-IPR-Policy.headers.txt": (
        "04258566b8d74f327f98a71954943e97a1c4182f0dd82ac90aa52cd6f4ea0e6d"
    ),
    "curation-headers/policy/m1_m2_prereg_v1.headers.txt": (
        "7996089641c62273855039e3f2f9595118f879368e4454201bc7230360aca99f"
    ),
    "curation-headers/replay/micropub-cr.headers.txt": (
        "21aa4b6addae52e257bff349acc9f3b486c13a9b73a1e9483fd4619f97a8ecf2"
    ),
    "curation-headers/replay/micropub-pr.headers.txt": (
        "cb8b023f804097c7d2ff6cd5c0c210ae652a621e745eb4505c2413026ef5546f"
    ),
    "curation-headers/replay/micropub-rec.headers.txt": (
        "222ed982234a50ce8d1f0ca429079cd97ca25a8b8004d97cfa0cb3a224c43fc0"
    ),
    "curation-headers/replay/mimesniff-2023.headers.txt": (
        "e644676922ffda6bbd47e22201a06f409d9e01540d88c27c819e86df8239e13f"
    ),
    "curation-headers/replay/mimesniff-2024.headers.txt": (
        "26fcf219a91efd530bc9a0f0c799da0af169e7de0c52b93c0adceac316708ab5"
    ),
    "curation-headers/replay/mimesniff-2025-01.headers.txt": (
        "02c6ceecbe81ef76bbf7546ee89fc5be34a5dca68f4c8937c2b556dce2a95140"
    ),
    "curation-headers/replay/mimesniff-2025.headers.txt": (
        "1795bc492f4882489c86534057521a456ce6d661e13322dde77ed9783fae6f4c"
    ),
    "curation-headers/replay/rfc2246.headers.txt": (
        "2a8f8959384b601baafc8a845be5378fdca92f2162d094c3df6954d6d531c553"
    ),
    "curation-headers/replay/rfc4346.headers.txt": (
        "6b3844bfc1a0ef1f4bd9dd0b7b5f5c5e5e89b39020a66870455844a1646ecec7"
    ),
    "curation-headers/replay/rfc5246.headers.txt": (
        "3910495f9082b82210b777e1a8723d61ede7a6c95a765b3a7e75739078546147"
    ),
}


def _strict_object(path: Path) -> dict[str, Any]:
    payload = strict_loads(path.read_bytes())
    assert isinstance(payload, dict)
    return payload


def _reseal(root: Path) -> str:
    content: list[tuple[str, bytes]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name in {"EVIDENCE.sha256", "EVIDENCE.sha256.sha256"}:
            continue
        content.append((path.relative_to(root).as_posix(), path.read_bytes()))
    content.sort(key=lambda item: item[0].encode("ascii"))
    inventory = "".join(
        f"{hashlib.sha256(raw).hexdigest()}  {ref}\n" for ref, raw in content
    ).encode("ascii")
    digest = hashlib.sha256(inventory).hexdigest()
    (root / "EVIDENCE.sha256").write_bytes(inventory)
    (root / "EVIDENCE.sha256.sha256").write_bytes(f"{digest}  EVIDENCE.sha256\n".encode("ascii"))
    return digest


def _write_canonical_json(path: Path, payload: Any) -> None:
    path.write_bytes(
        (
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    )


def test_development_recipe_evidence_is_exact_and_network_free() -> None:
    result = verify_source_recipe_evidence(
        EVIDENCE_ROOT,
        expected_inventory_sha256=INVENTORY_SHA256,
        expected_manifest_sha256=MANIFEST_SHA256,
        acceptance_policy_path=POLICY,
    )
    inventory = verify_evidence_root(
        EVIDENCE_ROOT,
        expected_inventory_sha256=INVENTORY_SHA256,
    )

    assert result.mode == "DEVELOPMENT_RECIPE_EVIDENCE_VERIFIED"
    assert result.source_count == 10
    assert result.families == ("rfc", "w3c", "whatwg")
    assert result.manifest_sha256 == MANIFEST_SHA256
    assert inventory.content_file_count == 35
    header_refs = [ref for ref in inventory.content_refs if ref.startswith("curation-headers/")]
    assert len(header_refs) == 27
    assert all(ref.endswith(".headers.txt") for ref in header_refs)
    assert not list(EVIDENCE_ROOT.rglob("*.html"))


def test_header_evidence_is_sanitized_and_hash_linked_to_all_originals() -> None:
    report_path = EVIDENCE_ROOT / "header-sanitization.json"
    assert hashlib.sha256(report_path.read_bytes()).hexdigest() == REPORT_SHA256
    report = _strict_object(report_path)
    files = report["files"]
    assert report["sanitizer_version"] == "1.0.0"
    assert report["unknown_field_policy"] == "DROP_ENTIRE_FIELD_AND_CONTINUATIONS"
    assert report["continuation_policy"] == "DROP_ALL_CONTINUATION_LINES"
    assert report["value_policy"].startswith("BOUNDED_PRINTABLE_FIELD_SPECIFIC")
    assert "link" not in report["allowed_field_names"]
    assert report["sensitive_header_values_included"] is False
    assert isinstance(files, list)
    original_by_output = {record["output_ref"]: record["original_sha256"] for record in files}
    assert original_by_output == EXPECTED_ORIGINAL_HEADER_HASHES
    removed_cookie_name = "set-" + "cookie"
    assert sum(removed_cookie_name in record["removed_field_names"] for record in files) == 15
    for record in files:
        raw = (EVIDENCE_ROOT / record["output_ref"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record["sanitized_sha256"]
        assert len(raw) == record["sanitized_byte_length"]

    forbidden_names = (
        "set-" + "cookie",
        "cookie",
        "author" + "ization",
        "proxy-" + "authorization",
        "proxy-" + "authenticate",
        "www-" + "authenticate",
        "x-api-" + "key",
        "x-auth-" + "token",
    )
    forbidden_markers = (
        tuple(name.encode("ascii") + b":" for name in forbidden_names) + FORBIDDEN_VALUE_MARKERS
    )
    for path in EVIDENCE_ROOT.rglob("*"):
        if path.is_file():
            lower = path.read_bytes().lower()
            assert not any(marker in lower for marker in forbidden_markers), path


def test_source_manifest_uses_frozen_compact_json_bytes() -> None:
    raw = (EVIDENCE_ROOT / "source-manifest.json").read_bytes()
    payload = strict_loads(raw)
    expected = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    assert raw == expected


def test_manifest_is_recipe_only_and_contains_all_ten_curated_sources() -> None:
    payload = _strict_object(EVIDENCE_ROOT / "source-manifest.json")

    assert set(payload) == {
        "schema_version",
        "corpus_id",
        "corpus_kind",
        "adjudication_status",
        "acceptance_policy",
        "ground_truth_status",
        "sources",
    }
    assert payload["adjudication_status"] == "EXPERIMENTAL_NOT_ADJUDICATED"
    assert payload["ground_truth_status"] == "NOT_INCLUDED"
    assert payload["acceptance_policy"]["sha256"] == FROZEN_POLICY_SHA256
    sources = payload["sources"]
    assert isinstance(sources, list)
    assert Counter(source["family"] for source in sources) == {
        "rfc": 3,
        "w3c": 3,
        "whatwg": 4,
    }
    assert {source["source_id"]: source["content_sha256"] for source in sources} == (
        EXPECTED_SOURCE_HASHES
    )
    assert all(
        source["license"]["snapshot_distribution"] == "fetch_recipe_only" for source in sources
    )
    assert "whatwg-mimesniff-review-2025-01" in EXPECTED_SOURCE_HASHES
    assert len({source["canonical_url"] for source in sources}) == 10
    assert len({source["acquisition_url"] for source in sources}) == 10
    assert len({source["content_sha256"] for source in sources}) == 10
    assert not (EVIDENCE_ROOT / "snapshots").exists()


def test_curator_precision_and_nonclaim_boundaries_are_explicit() -> None:
    provenance = _strict_object(EVIDENCE_ROOT / "curation-provenance.json")
    mappings = provenance["timestamp_mappings"]
    assert isinstance(mappings, list)
    assert len(mappings) == 10
    for mapping in mappings:
        original = mapping["original"]
        materialized = mapping["materialized"]
        assert isinstance(original, str)
        assert isinstance(materialized, str)
        assert original.rsplit(".", 1)[0] + "Z" == materialized
    rules = provenance["materialization_rules"]
    assert rules["timestamp_rule"]["operation"] == (
        "truncate fractional seconds to the preceding whole second"
    )
    assert rules["acquisition_recipe_mapping"].startswith(
        "The curator acquisition_recipe_or_snapshot_ref"
    )
    assert rules["license_inventory_ref"] == "license-inventory.json"
    recipe_mappings = provenance["acquisition_recipe_mappings"]
    manifest = _strict_object(EVIDENCE_ROOT / "source-manifest.json")
    assert [mapping["source_id"] for mapping in recipe_mappings] == [
        source["source_id"] for source in manifest["sources"]
    ]
    assert all(
        mapping["materialized_acquisition_url"] == source["acquisition_url"]
        and mapping["snapshot_distribution"] == "fetch_recipe_only"
        and mapping["response_body_in_repository"] is False
        and mapping["curator_acquisition_recipe_or_snapshot_ref"].startswith(
            f"HTTPS GET {source['acquisition_url']} "
        )
        for mapping, source in zip(recipe_mappings, manifest["sources"], strict=True)
    )
    boundary = provenance["repository_boundary"]
    assert boundary["candidate_executed"] is False
    assert boundary["labels_or_gold_included"] is False
    assert boundary["split_or_holdout_membership_included"] is False
    assert boundary["predictions_or_scores_included"] is False
    assert boundary["m1_acceptance_implication"] == "NONE"
    assert boundary["rejected_helper"]["status"] == "REJECTED_NOT_IMPORTED"


def test_wrapper_rechecks_entire_root_after_manifest_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    original_validator = evidence_inventory_module._validate_license_inventory

    def mutating_validator(*args: Any, **kwargs: Any) -> None:
        original_validator(*args, **kwargs)
        target = copied_root / "README.md"
        target.write_bytes(target.read_bytes() + b"tampered\n")

    monkeypatch.setattr(
        evidence_inventory_module,
        "_validate_license_inventory",
        mutating_validator,
    )

    with pytest.raises(EvidenceInventoryError, match="content SHA-256 mismatch"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=INVENTORY_SHA256,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_canonical_license_inventory_must_exactly_match_manifest(tmp_path: Path) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    license_path = copied_root / "license-inventory.json"
    payload = json.loads(license_path.read_text(encoding="utf-8"))
    payload["entries"][0]["redistribution_basis"] = "tampered basis"
    license_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError, match="differs from manifest"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_verifier_rejects_every_sanitized_header_continuation(tmp_path: Path) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    output_ref = "curation-headers/first/rfc-tls-1.0.headers.txt"
    header_path = copied_root / output_ref
    original = header_path.read_bytes()
    assert original.endswith(b"\r\n\r\n")
    tampered = original[:-2] + b" folded-metadata\r\n\r\n"
    header_path.write_bytes(tampered)

    report_path = copied_root / "header-sanitization.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    record = next(item for item in report["files"] if item["output_ref"] == output_ref)
    record["sanitized_sha256"] = hashlib.sha256(tampered).hexdigest()
    record["sanitized_byte_length"] = len(tampered)
    _write_canonical_json(report_path, report)
    inventory_digest = _reseal(copied_root)

    with pytest.raises(
        EvidenceInventoryError,
        match="report SHA-256|frozen identity|continuation",
    ):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_resealed_curation_timestamp_tamper_is_rejected(tmp_path: Path) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    provenance_path = copied_root / "curation-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["timestamp_mappings"][0]["original"] = "2026-08-11T00:41:47.999Z"
    _write_canonical_json(provenance_path, provenance)
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError, match="timestamp mappings differ"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_resealed_curation_acquisition_mapping_tamper_is_rejected(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    provenance_path = copied_root / "curation-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["acquisition_recipe_mappings"][0]["materialized_acquisition_url"] = (
        "https://example.invalid/rebound"
    )
    _write_canonical_json(provenance_path, provenance)
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError, match="acquisition recipe mappings differ"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_resealed_header_report_source_ref_tamper_is_rejected(tmp_path: Path) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    report_path = copied_root / "header-sanitization.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["files"][0]["source_ref"] = "http/rebound.headers.txt"
    _write_canonical_json(report_path, report)
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError, match="report SHA-256"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


@pytest.mark.parametrize(
    ("path", "numeric_alias"),
    [
        (("source_curation", "partial_checksum_file_in_repository"), 0),
        (("materialization_rules", "timestamp_rule", "rounding"), 0),
        (
            (
                "materialization_rules",
                "timestamp_rule",
                "precision_loss_documented",
            ),
            1,
        ),
        (("acquisition_recipe_mappings", 0, "response_body_in_repository"), 0),
        (("repository_boundary", "candidate_executed"), 0),
        (("repository_boundary", "labels_or_gold_included"), 0.0),
    ],
)
def test_resealed_provenance_rejects_boolean_numeric_aliases(
    tmp_path: Path,
    path: tuple[str | int, ...],
    numeric_alias: int | float,
) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    provenance_path = copied_root / "curation-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    target: Any = provenance
    for segment in path[:-1]:
        target = target[segment]
    target[path[-1]] = numeric_alias
    _write_canonical_json(provenance_path, provenance)
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_resealed_repository_readme_tamper_is_rejected(tmp_path: Path) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    readme_path = copied_root / "README.md"
    readme_path.write_bytes(
        readme_path.read_bytes() + b"RFC SAMPLE BODY THAT MUST NOT BE DISTRIBUTED\n"
    )
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError, match="README SHA-256 differs"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_resealed_curator_license_markdown_cannot_be_rebound(tmp_path: Path) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    curator_license = copied_root / "curator" / "LICENSE-INVENTORY.md"
    curator_license.write_bytes(curator_license.read_bytes() + b"tampered\n")
    tampered_digest = hashlib.sha256(curator_license.read_bytes()).hexdigest()

    provenance_path = copied_root / "curation-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["source_curation"]["license_inventory_sha256"] = tampered_digest
    _write_canonical_json(provenance_path, provenance)
    license_path = copied_root / "license-inventory.json"
    license_inventory = json.loads(license_path.read_text(encoding="utf-8"))
    license_inventory["source_curation_license_inventory_sha256"] = tampered_digest
    license_path.write_text(
        json.dumps(license_inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError, match="source identities differ"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )


def test_resealed_extra_content_file_is_rejected_by_semantic_set(tmp_path: Path) -> None:
    copied_root = tmp_path / "evidence"
    shutil.copytree(EVIDENCE_ROOT, copied_root)
    (copied_root / "extra.txt").write_bytes(b"not part of the frozen evidence set\n")
    inventory_digest = _reseal(copied_root)

    with pytest.raises(EvidenceInventoryError, match="content set differs"):
        verify_source_recipe_evidence(
            copied_root,
            expected_inventory_sha256=inventory_digest,
            expected_manifest_sha256=MANIFEST_SHA256,
            acceptance_policy_path=POLICY,
        )
