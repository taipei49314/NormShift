"""Synthetic-only tests for labeling and blind-split governance contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from typer.testing import CliRunner

from normshift.acceptance.item_key import acceptance_item_key
from normshift.cli import app
from normshift.evidence.hashing import canonical_json_bytes
from normshift.governance.models import (
    BlindSplitManifest,
    DecisionLedger,
    LabelingPacket,
)
from normshift.governance.verify import (
    POLICY_SHA256,
    GovernanceContractError,
    GovernanceVerificationResult,
    _bounded_read_regular_file,
    _crosscheck_packet_sources,
    verify_blind_split,
    verify_labeling_governance,
)
from normshift.strict_json import strict_loads

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "acceptance" / "m1_m2_prereg_v1.json"
SCHEMA_NAMES = (
    "blind_split_manifest_v1.schema.json",
    "decision_ledger_v1.schema.json",
    "label_submission_v1.schema.json",
    "labeling_packet_v1.schema.json",
)


def _sha(label: str) -> str:
    return hashlib.sha256(f"synthetic-only:{label}".encode()).hexdigest()


def _canonical_write(path: Path, payload: dict[str, Any]) -> tuple[bytes, str]:
    raw = canonical_json_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw, hashlib.sha256(raw).hexdigest()


def _validate_json(
    model: type[BlindSplitManifest] | type[DecisionLedger], payload: dict[str, Any]
) -> BlindSplitManifest | DecisionLedger:
    return model.model_validate_json(canonical_json_bytes(payload), strict=True)


def _packet_item(
    *,
    task: str,
    slot: str,
    source_labels: list[str],
    locators: list[str],
    allowed: list[str],
    evidence_label: str,
) -> dict[str, Any]:
    source_sha256s = [_sha(label) for label in source_labels]
    return {
        "item_key": acceptance_item_key(
            task=task,
            evaluation_slot=slot,
            source_sha256s=source_sha256s,
            portable_locators=locators,
        ),
        "task": task,
        "evaluation_slot": slot,
        "source_sha256s": source_sha256s,
        "portable_locators": locators,
        "evidence_sha256": _sha(evidence_label),
        "allowed_classes": allowed,
    }


def _response(
    item: dict[str, Any],
    *,
    outcome: str,
    selected_class: str | None,
    reason: str,
) -> dict[str, Any]:
    return {
        "item_key": item["item_key"],
        "task": item["task"],
        "evaluation_slot": item["evaluation_slot"],
        "source_sha256s": item["source_sha256s"],
        "portable_locators": item["portable_locators"],
        "evidence_sha256": item["evidence_sha256"],
        "outcome": outcome,
        "selected_class": selected_class,
        "reason": reason,
        "decided_at_utc": "2026-01-01T00:01:00Z",
    }


def _labeling_bundle(tmp_path: Path) -> dict[str, Any]:
    governance = _governance_manifests(tmp_path)
    source_manifest_sha256 = governance["source_manifest_sha256"]
    split_manifest_sha256 = governance["blind_split_sha256"]
    items = sorted(
        [
            _packet_item(
                task="M1_REGION",
                slot="region",
                source_labels=["raw-synthetic-02-rfc-d1"],
                locators=["synthetic/synthetic-02-rfc-d1.html#section-a"],
                allowed=["EXCLUDED", "INFORMATIVE", "NONE", "NORMATIVE"],
                evidence_label="evidence-region",
            ),
            _packet_item(
                task="M2_IDENTITY",
                slot="identity",
                source_labels=[
                    "raw-synthetic-07-whatwg-d1",
                    "raw-synthetic-08-whatwg-d2",
                ],
                locators=[
                    "synthetic/synthetic-07-whatwg-d1.html#requirement-a",
                    "synthetic/synthetic-08-whatwg-d2.html#requirement-b",
                ],
                allowed=["DIFFERENT_LINEAGE", "NONE", "SAME_LINEAGE"],
                evidence_label="evidence-identity",
            ),
        ],
        key=lambda item: item["item_key"],
    )
    packet = {
        "kind": "normshift-neutral-labeling-packet",
        "schema_version": "1.0.0",
        "policy_id": "normshift-m1-m2-prereg-v1",
        "policy_sha256": POLICY_SHA256,
        "packet_id": "synthetic-packet",
        "packet_version": "v1",
        "dataset_split": "DEVELOPMENT",
        "source_manifest_sha256": source_manifest_sha256,
        "split_manifest_sha256": split_manifest_sha256,
        "prepared_by_reviewer_id": "synthetic-packet-custodian",
        "prepared_at_utc": "2026-01-01T00:00:00Z",
        "neutrality": {
            "contains_model_proposal": False,
            "contains_model_confidence": False,
            "contains_candidate_prediction": False,
            "created_before_prediction_access": True,
        },
        "items": items,
    }
    packet_path = tmp_path / "packet.json"
    packet_raw, packet_sha256 = _canonical_write(packet_path, packet)

    labeler_ids = ["synthetic-labeler-a", "synthetic-labeler-b"]
    submissions_root = tmp_path / "submissions"
    submission_payloads: dict[str, dict[str, Any]] = {}
    submission_records: list[dict[str, Any]] = []
    response_hashes: dict[tuple[str, str], str] = {}
    for labeler_index, labeler_id in enumerate(labeler_ids):
        responses: list[dict[str, Any]] = []
        for item_index, item in enumerate(items):
            if item_index == 0:
                non_none = [value for value in item["allowed_classes"] if value != "NONE"]
                response = _response(
                    item,
                    outcome="LABELED",
                    selected_class=non_none[min(labeler_index, len(non_none) - 1)],
                    reason=f"synthetic independent evidence review {labeler_index}",
                )
            else:
                response = _response(
                    item,
                    outcome="ABSTAINED" if labeler_index == 0 else "AMBIGUOUS",
                    selected_class=None,
                    reason=f"synthetic uncertainty retained {labeler_index}",
                )
            responses.append(response)
            response_hashes[(labeler_id, item["item_key"])] = hashlib.sha256(
                canonical_json_bytes(response)
            ).hexdigest()
        submission = {
            "kind": "normshift-independent-label-submission",
            "schema_version": "1.0.0",
            "policy_id": "normshift-m1-m2-prereg-v1",
            "policy_sha256": POLICY_SHA256,
            "submission_id": f"synthetic-submission-{labeler_index + 1}",
            "packet_sha256": packet_sha256,
            "review_round_id": "synthetic-review-round-1",
            "labeler_id": labeler_id,
            "independence": {
                "worked_independently": True,
                "viewed_other_labeler_answers": False,
                "viewed_model_proposals": False,
                "viewed_model_confidence": False,
                "viewed_candidate_predictions": False,
                "implemented_evaluated_system": False,
            },
            "submitted_at_utc": "2026-01-01T00:02:00Z",
            "responses": responses,
        }
        portable_ref = f"{labeler_id}.json"
        raw, digest = _canonical_write(submissions_root / portable_ref, submission)
        submission_payloads[labeler_id] = submission
        submission_records.append(
            {
                "submission_id": submission["submission_id"],
                "review_round_id": "synthetic-review-round-1",
                "labeler_id": labeler_id,
                "portable_ref": portable_ref,
                "sha256": digest,
                "bytes": len(raw),
            }
        )

    def votes(item_key: str) -> list[dict[str, Any]]:
        return [
            {
                "labeler_id": record["labeler_id"],
                "submission_sha256": record["sha256"],
                "response_sha256": response_hashes[(record["labeler_id"], item_key)],
            }
            for record in submission_records
        ]

    events: list[dict[str, Any]] = []
    active_ids: list[str] = []
    for item_index, item in enumerate(items):
        base = {
            "review_round_id": "synthetic-review-round-1",
            "item_key": item["item_key"],
            "task": item["task"],
            "evaluation_slot": item["evaluation_slot"],
            "source_sha256s": item["source_sha256s"],
            "portable_locators": item["portable_locators"],
            "evidence_sha256": item["evidence_sha256"],
            "reviewer_ids": labeler_ids,
            "adjudicator_id": "synthetic-adjudicator",
            "votes": votes(item["item_key"]),
        }
        initial_id = f"synthetic-decision-{item_index + 1}-r1"
        initial = {
            **base,
            "decision_id": initial_id,
            "revision": 1,
            "event_type": "INITIAL",
            "supersedes_decision_id": None,
            "decision": "CONFLICT" if item_index == 0 else "AMBIGUOUS",
            "decided_class": None,
            "reason": (
                "synthetic conflict retained"
                if item_index == 0
                else "synthetic ambiguity retained"
            ),
            "decided_at_utc": "2026-01-01T00:03:00Z",
        }
        events.append(initial)
        if item_index == 0:
            active_id = f"synthetic-decision-{item_index + 1}-r2"
            non_none = [value for value in item["allowed_classes"] if value != "NONE"]
            events.append(
                {
                    **base,
                    "decision_id": active_id,
                    "revision": 2,
                    "event_type": "CORRECTION",
                    "supersedes_decision_id": initial_id,
                    "decision": "ACCEPTED",
                    "decided_class": non_none[0],
                    "reason": "synthetic evidence-backed adjudication correction",
                    "decided_at_utc": "2026-01-01T00:04:00Z",
                }
            )
        else:
            active_id = initial_id
        active_ids.append(active_id)

    ledger = {
        "kind": "normshift-label-decision-ledger",
        "schema_version": "1.0.0",
        "policy_id": "normshift-m1-m2-prereg-v1",
        "policy_sha256": POLICY_SHA256,
        "ledger_id": "synthetic-ledger",
        "ledger_version": "v1",
        "packet_sha256": packet_sha256,
        "candidate_predictions_viewed_before_freeze": False,
        "labels_and_decisions_hash_frozen_before_predictions": True,
        "review_rounds": [
            {
                "review_round_id": "synthetic-review-round-1",
                "sequence": 1,
                "kind": "INITIAL",
                "supersedes_review_round_id": None,
                "labeler_ids": labeler_ids,
                "adjudicator_id": "synthetic-adjudicator",
                "labelers_implemented_evaluated_system": False,
                "adjudicator_implemented_evaluated_system": False,
                "viewed_prior_label_decisions": False,
                "viewed_candidate_predictions": False,
                "opened_at_utc": "2026-01-01T00:00:30Z",
                "completed_at_utc": "2026-01-01T00:04:30Z",
            }
        ],
        "active_review_round_id": "synthetic-review-round-1",
        "submissions": submission_records,
        "revision_context": {
            "kind": "INITIAL_FREEZE",
            "supersedes_ledger_sha256": None,
            "invalidated_measurement_sha256s": [],
            "correction_reason": None,
        },
        "decisions": events,
        "active_decision_ids": sorted(active_ids),
        "frozen_at_utc": "2026-01-01T00:05:00Z",
    }
    ledger_path = tmp_path / "ledger.json"
    ledger_raw, ledger_sha256 = _canonical_write(ledger_path, ledger)
    return {
        "packet": packet,
        "packet_path": packet_path,
        "packet_raw": packet_raw,
        "packet_sha256": packet_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "split_manifest_sha256": split_manifest_sha256,
        "submissions_root": submissions_root,
        "submission_payloads": submission_payloads,
        "ledger": ledger,
        "ledger_path": ledger_path,
        "ledger_raw": ledger_raw,
        "ledger_sha256": ledger_sha256,
        **governance,
    }


def _verify_labeling(bundle: dict[str, Any]) -> GovernanceVerificationResult:
    return verify_labeling_governance(
        packet_path=bundle["packet_path"],
        expected_packet_sha256=bundle["packet_sha256"],
        source_manifest_path=bundle["source_manifest_path"],
        submissions_root=bundle["submissions_root"],
        ledger_path=bundle["ledger_path"],
        expected_ledger_sha256=bundle["ledger_sha256"],
        expected_source_manifest_sha256=bundle["source_manifest_sha256"],
        blind_split_manifest_path=bundle["blind_split_path"],
        expected_split_manifest_sha256=bundle["split_manifest_sha256"],
        acceptance_policy_path=POLICY,
        prior_ledger_path=bundle.get("prior_ledger_path"),
        expected_prior_ledger_sha256=bundle.get("prior_ledger_sha256"),
        _allow_test_source_contract=True,
    )


def _rewrite_packet_and_ledger_binding(
    bundle: dict[str, Any], packet: dict[str, Any]
) -> None:
    """Rebind the synthetic hash graph after changing only packet-level metadata."""

    packet_raw, packet_sha256 = _canonical_write(bundle["packet_path"], packet)
    ledger = copy.deepcopy(bundle["ledger"])
    ledger["packet_sha256"] = packet_sha256
    submission_hashes: dict[str, str] = {}
    response_hashes: dict[tuple[str, str], str] = {}
    for labeler_id, original in bundle["submission_payloads"].items():
        submission = copy.deepcopy(original)
        submission["packet_sha256"] = packet_sha256
        record = next(
            value for value in ledger["submissions"] if value["labeler_id"] == labeler_id
        )
        raw, digest = _canonical_write(
            bundle["submissions_root"] / record["portable_ref"], submission
        )
        record["sha256"] = digest
        record["bytes"] = len(raw)
        submission_hashes[labeler_id] = digest
        for response in submission["responses"]:
            response_hashes[(labeler_id, response["item_key"])] = hashlib.sha256(
                canonical_json_bytes(response)
            ).hexdigest()
    for event in ledger["decisions"]:
        for vote in event["votes"]:
            labeler_id = vote["labeler_id"]
            vote["submission_sha256"] = submission_hashes[labeler_id]
            vote["response_sha256"] = response_hashes[
                (labeler_id, event["item_key"])
            ]
    ledger_raw, ledger_sha256 = _canonical_write(bundle["ledger_path"], ledger)
    bundle.update(
        {
            "packet": packet,
            "packet_raw": packet_raw,
            "packet_sha256": packet_sha256,
            "ledger": ledger,
            "ledger_raw": ledger_raw,
            "ledger_sha256": ledger_sha256,
        }
    )


def _rewrite_split_and_labeling_graph(
    bundle: dict[str, Any], split: dict[str, Any]
) -> None:
    split_path, split_sha256 = _write_blind(bundle["blind_split_path"].parent, split)
    assert split_path == bundle["blind_split_path"]
    packet = copy.deepcopy(bundle["packet"])
    packet["split_manifest_sha256"] = split_sha256
    bundle["blind_split"] = split
    bundle["blind_split_sha256"] = split_sha256
    bundle["split_manifest_sha256"] = split_sha256
    _rewrite_packet_and_ledger_binding(bundle, packet)


def _rewrite_one_response_time(
    bundle: dict[str, Any], *, labeler_id: str, decided_at_utc: str
) -> None:
    submission = copy.deepcopy(bundle["submission_payloads"][labeler_id])
    target = submission["responses"][0]
    target["decided_at_utc"] = decided_at_utc
    record = next(
        item for item in bundle["ledger"]["submissions"] if item["labeler_id"] == labeler_id
    )
    raw, digest = _canonical_write(
        bundle["submissions_root"] / record["portable_ref"], submission
    )
    ledger = copy.deepcopy(bundle["ledger"])
    ledger_record = next(
        item for item in ledger["submissions"] if item["labeler_id"] == labeler_id
    )
    ledger_record["sha256"] = digest
    ledger_record["bytes"] = len(raw)
    response_sha256 = hashlib.sha256(canonical_json_bytes(target)).hexdigest()
    for event in ledger["decisions"]:
        for vote in event["votes"]:
            if vote["labeler_id"] == labeler_id:
                vote["submission_sha256"] = digest
                if event["item_key"] == target["item_key"]:
                    vote["response_sha256"] = response_sha256
    ledger_raw, ledger_sha256 = _canonical_write(bundle["ledger_path"], ledger)
    bundle.update(
        {
            "ledger": ledger,
            "ledger_raw": ledger_raw,
            "ledger_sha256": ledger_sha256,
        }
    )


def _extend_with_post_freeze_correction(bundle: dict[str, Any], tmp_path: Path) -> None:
    # V1 preserves correction history but cannot reuse a split that already
    # records prediction access.  A future evaluation attempt must bind the
    # corrected ledger independently before predictions begin.
    split = copy.deepcopy(bundle["blind_split"])
    split["candidate_freeze"]["predictions_started_at_utc"] = None
    _rewrite_split_and_labeling_graph(bundle, split)
    prior_path = tmp_path / "prior-ledger.json"
    prior_path.write_bytes(bundle["ledger_raw"])
    prior_sha256 = bundle["ledger_sha256"]
    ledger = copy.deepcopy(bundle["ledger"])
    ledger["ledger_version"] = "v2"
    correction_labelers = ["synthetic-labeler-c", "synthetic-labeler-d"]
    correction_round_id = "synthetic-review-round-2"
    ledger["review_rounds"].append(
        {
            "review_round_id": correction_round_id,
            "sequence": 2,
            "kind": "POST_FREEZE_CORRECTION",
            "supersedes_review_round_id": "synthetic-review-round-1",
            "labeler_ids": correction_labelers,
            "adjudicator_id": "synthetic-adjudicator-2",
            "labelers_implemented_evaluated_system": False,
            "adjudicator_implemented_evaluated_system": False,
            "viewed_prior_label_decisions": False,
            "viewed_candidate_predictions": False,
            "opened_at_utc": "2026-01-01T00:06:00Z",
            "completed_at_utc": "2026-01-01T00:09:00Z",
        }
    )
    ledger["active_review_round_id"] = correction_round_id

    response_hashes: dict[tuple[str, str], str] = {}
    correction_records: list[dict[str, Any]] = []
    for index, labeler_id in enumerate(correction_labelers, start=3):
        responses: list[dict[str, Any]] = []
        for item in bundle["packet"]["items"]:
            non_none = [value for value in item["allowed_classes"] if value != "NONE"]
            response = _response(
                item,
                outcome="LABELED",
                selected_class=non_none[0],
                reason=f"synthetic correction review {index}",
            )
            response["decided_at_utc"] = "2026-01-01T00:07:00Z"
            responses.append(response)
            response_hashes[(labeler_id, item["item_key"])] = hashlib.sha256(
                canonical_json_bytes(response)
            ).hexdigest()
        submission = {
            "kind": "normshift-independent-label-submission",
            "schema_version": "1.0.0",
            "policy_id": "normshift-m1-m2-prereg-v1",
            "policy_sha256": POLICY_SHA256,
            "submission_id": f"synthetic-submission-{index}",
            "packet_sha256": bundle["packet_sha256"],
            "review_round_id": correction_round_id,
            "labeler_id": labeler_id,
            "independence": {
                "worked_independently": True,
                "viewed_other_labeler_answers": False,
                "viewed_model_proposals": False,
                "viewed_model_confidence": False,
                "viewed_candidate_predictions": False,
                "implemented_evaluated_system": False,
            },
            "submitted_at_utc": "2026-01-01T00:08:00Z",
            "responses": responses,
        }
        portable_ref = f"{labeler_id}.json"
        raw, digest = _canonical_write(bundle["submissions_root"] / portable_ref, submission)
        bundle["submission_payloads"][labeler_id] = submission
        correction_records.append(
            {
                "submission_id": submission["submission_id"],
                "review_round_id": correction_round_id,
                "labeler_id": labeler_id,
                "portable_ref": portable_ref,
                "sha256": digest,
                "bytes": len(raw),
            }
        )
    ledger["submissions"].extend(correction_records)

    target = bundle["packet"]["items"][0]
    prior_event = [
        event for event in ledger["decisions"] if event["item_key"] == target["item_key"]
    ][-1]
    votes = [
        {
            "labeler_id": record["labeler_id"],
            "submission_sha256": record["sha256"],
            "response_sha256": response_hashes[(record["labeler_id"], target["item_key"])],
        }
        for record in correction_records
    ]
    correction_id = "synthetic-post-freeze-correction-r3"
    non_none = [value for value in target["allowed_classes"] if value != "NONE"]
    ledger["decisions"].append(
        {
            "decision_id": correction_id,
            "review_round_id": correction_round_id,
            "revision": prior_event["revision"] + 1,
            "event_type": "CORRECTION",
            "supersedes_decision_id": prior_event["decision_id"],
            "item_key": target["item_key"],
            "task": target["task"],
            "evaluation_slot": target["evaluation_slot"],
            "source_sha256s": target["source_sha256s"],
            "portable_locators": target["portable_locators"],
            "evidence_sha256": target["evidence_sha256"],
            "reviewer_ids": correction_labelers,
            "adjudicator_id": "synthetic-adjudicator-2",
            "votes": votes,
            "decision": "ACCEPTED",
            "decided_class": non_none[0],
            "reason": "synthetic independently reviewed post-freeze correction",
            "decided_at_utc": "2026-01-01T00:08:30Z",
        }
    )
    ledger["active_decision_ids"] = sorted(
        correction_id if decision_id == prior_event["decision_id"] else decision_id
        for decision_id in ledger["active_decision_ids"]
    )
    ledger["revision_context"] = {
        "kind": "POST_FREEZE_CORRECTION",
        "supersedes_ledger_sha256": prior_sha256,
        "invalidated_measurement_sha256s": [_sha("synthetic-affected-measurement")],
        "correction_reason": "synthetic independently reviewed correction",
    }
    ledger["frozen_at_utc"] = "2026-01-01T00:10:00Z"
    ledger_raw, ledger_sha256 = _canonical_write(bundle["ledger_path"], ledger)
    bundle.update(
        {
            "ledger": ledger,
            "ledger_raw": ledger_raw,
            "ledger_sha256": ledger_sha256,
            "prior_ledger_path": prior_path,
            "prior_ledger_sha256": prior_sha256,
        }
    )


def _blind_manifest() -> dict[str, Any]:
    documents: list[dict[str, Any]] = []

    def add(
        source_id: str,
        family: str,
        split: str,
        *,
        m1: bool,
        chain: str | None,
    ) -> None:
        documents.append(
            {
                "source_id": source_id,
                "family": family,
                "standard_id": f"synthetic-standard-{family.lower()}",
                "version": source_id,
                "raw_sha256": _sha(f"raw-{source_id}"),
                "derived_sha256s": [_sha(f"derived-{source_id}")],
                "portable_source_ref": f"synthetic/{source_id}.html",
                "m1_in_scope": m1,
                "m2_in_scope": chain is not None,
                "m2_lineage_chain_id": chain,
                "split": split,
            }
        )

    add("synthetic-01-rfc-h", "RFC", "BLIND_HOLDOUT", m1=True, chain=None)
    add("synthetic-02-rfc-d1", "RFC", "DEVELOPMENT", m1=True, chain="synthetic-rfc-dev")
    add("synthetic-03-rfc-d2", "RFC", "DEVELOPMENT", m1=True, chain="synthetic-rfc-dev")
    add("synthetic-03z-rfc-d3", "RFC", "DEVELOPMENT", m1=True, chain="synthetic-rfc-dev")
    add("synthetic-04-w3c-h1", "W3C_TR", "BLIND_HOLDOUT", m1=True, chain="synthetic-w3c-h")
    add("synthetic-05-w3c-h2", "W3C_TR", "BLIND_HOLDOUT", m1=False, chain="synthetic-w3c-h")
    add("synthetic-05z-w3c-h3", "W3C_TR", "BLIND_HOLDOUT", m1=False, chain="synthetic-w3c-h")
    add("synthetic-06-whatwg-h", "WHATWG", "BLIND_HOLDOUT", m1=True, chain=None)
    add(
        "synthetic-07-whatwg-d1",
        "WHATWG",
        "DEVELOPMENT",
        m1=True,
        chain="synthetic-whatwg-dev",
    )
    add(
        "synthetic-08-whatwg-d2",
        "WHATWG",
        "DEVELOPMENT",
        m1=True,
        chain="synthetic-whatwg-dev",
    )
    add(
        "synthetic-08z-whatwg-d3",
        "WHATWG",
        "DEVELOPMENT",
        m1=True,
        chain="synthetic-whatwg-dev",
    )
    add("synthetic-09-rfc-m1-dev", "RFC", "DEVELOPMENT", m1=True, chain=None)
    return {
        "kind": "normshift-blind-split-manifest",
        "schema_version": "1.0.0",
        "policy_id": "normshift-m1-m2-prereg-v1",
        "policy_sha256": POLICY_SHA256,
        "split_id": "synthetic-blind-split",
        "split_version": "v1",
        "source_manifest_sha256": _sha("source-manifest"),
        "custodian_ids": ["synthetic-split-custodian"],
        "implementation_author_ids": ["synthetic-implementation-author"],
        "created_at_utc": "2026-01-01T00:00:00Z",
        "split_frozen_at_utc": "2026-01-01T00:01:00Z",
        "blindness": {
            "holdout_membership_visible_to_implementation_before_candidate_freeze": False,
            "holdout_gold_visible_to_implementation_before_candidate_freeze": False,
            "holdout_predictions_visible_to_implementation_before_candidate_freeze": False,
            "fixture_name_path_url_or_hash_special_cases_added": False,
        },
        "candidate_freeze": {
            "status": "FROZEN",
            "candidate": {
                "commit": "1" * 40,
                "tree": "2" * 40,
                "wheel_sha256": _sha("wheel"),
                "sdist_sha256": _sha("sdist"),
                "source_zip_sha256": _sha("source-zip"),
                "bundle_sha256": _sha("bundle"),
            },
            "frozen_at_utc": "2026-01-01T00:02:00Z",
            "holdout_opened_at_utc": "2026-01-01T00:03:00Z",
            "predictions_started_at_utc": "2026-01-01T00:12:00Z",
        },
        "documents": documents,
    }


def _write_blind(tmp_path: Path, payload: dict[str, Any]) -> tuple[Path, str]:
    path = tmp_path / "blind-split.json"
    _, digest = _canonical_write(path, payload)
    return path, digest


def _source_manifest_payload(blind_split: dict[str, Any]) -> dict[str, Any]:
    family_contract = {
        "RFC": ("rfc", "rfc2119"),
        "W3C_TR": ("w3c", "rfc2119"),
        "WHATWG": ("whatwg", "whatwg"),
    }
    sources: list[dict[str, Any]] = []
    for document in blind_split["documents"]:
        family, profile = family_contract[document["family"]]
        url = f"https://standards.example.test/{family}/{document['source_id']}.html"
        sources.append(
            {
                "source_id": document["source_id"],
                "family": family,
                "adapter": family,
                "profile": profile,
                "adapter_version": "1.0.0",
                "normalization_version": "1.0.0",
                "identity_preflight_version": "1.0.0",
                "standard_id": document["standard_id"],
                "version_or_date": document["version"],
                "document_version": f"sha256:{document['raw_sha256'][:12]}",
                "canonical_url": url,
                "acquisition_url": url,
                "curator_retrieved_at_utc": "2026-01-01T00:00:00Z",
                "redirect_chain": [url],
                "etag": f'"{document["source_id"]}-synthetic"',
                "last_modified": "Thu, 01 Jan 2026 00:00:00 GMT",
                "media_type": "text/html",
                "charset": "utf-8",
                "content_sha256": document["raw_sha256"],
                "byte_length": 1,
                "local_ref": document["portable_source_ref"],
                "license": {
                    "document_or_license": "Synthetic-only test fixture contract",
                    "url": "https://standards.example.test/license/",
                    "redistribution_basis": "Generated synthetic metadata only.",
                    "snapshot_distribution": "embedded",
                },
            }
        )
    return {
        "schema_version": "normshift-m1-source-manifest/v1",
        "corpus_id": "synthetic-governance-contract-test",
        "corpus_kind": "SOURCE_CONTRACT_TEST",
        "adjudication_status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "acceptance_policy": {
            "id": "normshift-m1-m2-prereg-v1",
            "sha256": POLICY_SHA256,
            "local_ref": "acceptance/m1_m2_prereg_v1.json",
            "status": "FROZEN_BEFORE_BLIND_EVALUATION",
        },
        "ground_truth_status": "NOT_INCLUDED",
        "sources": sources,
    }


def _governance_manifests(tmp_path: Path) -> dict[str, Any]:
    blind_split = _blind_manifest()
    source_payload = _source_manifest_payload(blind_split)
    source_raw = (
        json.dumps(
            source_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    source_path = tmp_path / "source-manifest.json"
    source_path.write_bytes(source_raw)
    source_sha256 = hashlib.sha256(source_raw).hexdigest()
    blind_split["source_manifest_sha256"] = source_sha256
    blind_path, blind_sha256 = _write_blind(tmp_path, blind_split)
    return {
        "blind_split": blind_split,
        "blind_split_path": blind_path,
        "blind_split_sha256": blind_sha256,
        "source_manifest": source_payload,
        "source_manifest_path": source_path,
        "source_manifest_sha256": source_sha256,
    }


def test_labeling_governance_hash_graph_passes_without_acceptance_claim(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    result = _verify_labeling(bundle)
    assert result.contract_kind == "LABELING_GOVERNANCE"
    assert result.item_or_document_count == 2
    assert result.independent_labeler_count == 2
    assert result.holdout_document_count == 5
    assert result.candidate_frozen is True
    assert result.metrics_evaluated is False
    assert result.external_acceptance_granted is False
    assert result.scope == "GOVERNANCE_CONTRACT_ONLY"

    decisions = bundle["ledger"]["decisions"]
    assert {event["decision"] for event in decisions} == {"ACCEPTED", "AMBIGUOUS", "CONFLICT"}
    assert any(event["event_type"] == "CORRECTION" for event in decisions)


@pytest.mark.parametrize("prediction_start", ["2026-01-01T00:04:00Z", "2026-01-01T00:05:00Z"])
def test_initial_ledger_must_freeze_strictly_before_predictions(
    tmp_path: Path, prediction_start: str
) -> None:
    bundle = _labeling_bundle(tmp_path)
    split = copy.deepcopy(bundle["blind_split"])
    split["candidate_freeze"]["predictions_started_at_utc"] = prediction_start
    _rewrite_split_and_labeling_graph(bundle, split)
    with pytest.raises(GovernanceContractError, match="strictly before predictions"):
        _verify_labeling(bundle)


def test_v1_correction_rejects_a_split_that_already_records_prediction_access(
    tmp_path: Path,
) -> None:
    bundle = _labeling_bundle(tmp_path)
    _extend_with_post_freeze_correction(bundle, tmp_path)
    split = copy.deepcopy(bundle["blind_split"])
    split["candidate_freeze"]["predictions_started_at_utc"] = "2026-01-01T00:12:00Z"
    _rewrite_split_and_labeling_graph(bundle, split)
    with pytest.raises(GovernanceContractError, match="evaluation-attempt contract"):
        _verify_labeling(bundle)


def test_neutral_packet_rejects_proposal_or_confidence_fields(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    for forbidden in ("model_proposal", "model_confidence", "candidate_prediction"):
        packet = copy.deepcopy(bundle["packet"])
        packet["items"][0][forbidden] = "forbidden"
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            LabelingPacket.model_validate_json(canonical_json_bytes(packet), strict=True)


def test_m1_packet_item_must_bind_exactly_one_whole_document(tmp_path: Path) -> None:
    packet = copy.deepcopy(_labeling_bundle(tmp_path)["packet"])
    item = next(value for value in packet["items"] if value["task"].startswith("M1_"))
    item["source_sha256s"].append(_sha("second-m1-source"))
    item["portable_locators"].append("synthetic/second-m1-source.html#section-b")
    item["item_key"] = acceptance_item_key(
        task=item["task"],
        evaluation_slot=item["evaluation_slot"],
        source_sha256s=item["source_sha256s"],
        portable_locators=item["portable_locators"],
    )
    packet["items"] = sorted(packet["items"], key=lambda value: value["item_key"])
    with pytest.raises(ValidationError, match="exactly one whole source"):
        LabelingPacket.model_validate_json(canonical_json_bytes(packet), strict=True)


def test_labeling_wrong_independent_trust_anchor_fails(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    bundle["packet_sha256"] = "0" * 64
    with pytest.raises(GovernanceContractError, match="packet SHA-256 mismatch"):
        _verify_labeling(bundle)


def test_packet_cannot_rehash_an_arbitrary_source_outside_verified_manifests(
    tmp_path: Path,
) -> None:
    bundle = _labeling_bundle(tmp_path)
    packet = copy.deepcopy(bundle["packet"])
    target = packet["items"][0]
    old_key = target["item_key"]
    target["source_sha256s"][0] = _sha("attacker-unmanifested-source")
    target["item_key"] = acceptance_item_key(
        task=target["task"],
        evaluation_slot=target["evaluation_slot"],
        source_sha256s=target["source_sha256s"],
        portable_locators=target["portable_locators"],
    )
    new_key = target["item_key"]
    packet["items"] = sorted(packet["items"], key=lambda item: item["item_key"])
    _, packet_sha256 = _canonical_write(bundle["packet_path"], packet)

    ledger = copy.deepcopy(bundle["ledger"])
    ledger["packet_sha256"] = packet_sha256
    response_hashes: dict[str, str] = {}
    submission_hashes: dict[str, str] = {}
    for labeler_id, original in bundle["submission_payloads"].items():
        submission = copy.deepcopy(original)
        submission["packet_sha256"] = packet_sha256
        response = next(value for value in submission["responses"] if value["item_key"] == old_key)
        response["item_key"] = new_key
        response["source_sha256s"] = target["source_sha256s"]
        submission["responses"] = sorted(
            submission["responses"], key=lambda value: value["item_key"]
        )
        response_hashes[labeler_id] = hashlib.sha256(canonical_json_bytes(response)).hexdigest()
        record = next(
            value for value in ledger["submissions"] if value["labeler_id"] == labeler_id
        )
        submission_path = bundle["submissions_root"] / record["portable_ref"]
        raw, digest = _canonical_write(submission_path, submission)
        record["sha256"] = digest
        record["bytes"] = len(raw)
        submission_hashes[labeler_id] = digest
    for event in ledger["decisions"]:
        if event["item_key"] != old_key:
            continue
        event["item_key"] = new_key
        event["source_sha256s"] = target["source_sha256s"]
        for vote in event["votes"]:
            labeler_id = vote["labeler_id"]
            vote["submission_sha256"] = submission_hashes[labeler_id]
            vote["response_sha256"] = response_hashes[labeler_id]
    _, bundle["ledger_sha256"] = _canonical_write(bundle["ledger_path"], ledger)
    bundle["packet_sha256"] = packet_sha256
    with pytest.raises(GovernanceContractError, match="outside the verified manifest"):
        _verify_labeling(bundle)


def test_packet_tasks_must_bind_sources_in_their_declared_scope(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    split = BlindSplitManifest.model_validate_json(
        canonical_json_bytes(bundle["blind_split"]), strict=True
    )
    split_by_sha = {document.raw_sha256: document for document in split.documents}
    packet = LabelingPacket.model_validate_json(
        canonical_json_bytes(bundle["packet"]), strict=True
    )

    m1_item = next(item for item in packet.items if item.task.value.startswith("M1_"))
    m1_document = split_by_sha[m1_item.source_sha256s[0]]
    split_by_sha[m1_document.raw_sha256] = m1_document.model_copy(
        update={"m1_in_scope": False}
    )
    with pytest.raises(GovernanceContractError, match="outside M1 scope"):
        _crosscheck_packet_sources(packet, split_by_sha)

    split_by_sha = {document.raw_sha256: document for document in split.documents}
    m2_item = next(item for item in packet.items if item.task.value.startswith("M2_"))
    m2_document = split_by_sha[m2_item.source_sha256s[0]]
    split_by_sha[m2_document.raw_sha256] = m2_document.model_copy(
        update={"m2_in_scope": False, "m2_lineage_chain_id": None}
    )
    with pytest.raises(GovernanceContractError, match="outside M2 scope"):
        _crosscheck_packet_sources(packet, split_by_sha)


def test_m2_identity_allows_cross_lineage_hard_negative_but_relation_does_not(
    tmp_path: Path,
) -> None:
    bundle = _labeling_bundle(tmp_path)
    split = BlindSplitManifest.model_validate_json(
        canonical_json_bytes(bundle["blind_split"]), strict=True
    )
    split_by_sha = {document.raw_sha256: document for document in split.documents}
    common = copy.deepcopy(bundle["packet"])
    source_labels = ["raw-synthetic-02-rfc-d1", "raw-synthetic-07-whatwg-d1"]
    locators = [
        "synthetic/synthetic-02-rfc-d1.html#requirement-a",
        "synthetic/synthetic-07-whatwg-d1.html#requirement-b",
    ]
    identity_item = _packet_item(
        task="M2_IDENTITY",
        slot="identity",
        source_labels=source_labels,
        locators=locators,
        allowed=["DIFFERENT_LINEAGE", "NONE", "SAME_LINEAGE"],
        evidence_label="cross-lineage-identity",
    )
    common["items"] = [identity_item]
    identity_packet = LabelingPacket.model_validate_json(
        canonical_json_bytes(common), strict=True
    )
    _crosscheck_packet_sources(identity_packet, split_by_sha)

    relation_item = _packet_item(
        task="M2_RELATION",
        slot="relation",
        source_labels=source_labels,
        locators=locators,
        allowed=[
            "ADDED",
            "AMBIGUOUS",
            "CONTINUES",
            "MERGED_FROM",
            "NONE",
            "REMOVED",
            "SPLIT_INTO",
        ],
        evidence_label="cross-lineage-relation",
    )
    common["items"] = [relation_item]
    relation_packet = LabelingPacket.model_validate_json(
        canonical_json_bytes(common), strict=True
    )
    with pytest.raises(GovernanceContractError, match="family/lineage boundary"):
        _crosscheck_packet_sources(relation_packet, split_by_sha)


def test_labeling_exact_root_rejects_extra_file_and_directory(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    (bundle["submissions_root"] / "extra.json").write_text("{}", encoding="utf-8")
    with pytest.raises(GovernanceContractError, match="inventory differs"):
        _verify_labeling(bundle)

    (bundle["submissions_root"] / "extra.json").unlink()
    (bundle["submissions_root"] / "empty-extra").mkdir()
    with pytest.raises(GovernanceContractError, match="inventory differs"):
        _verify_labeling(bundle)


def test_labeling_exact_root_rejects_external_hardlink_alias(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    submission = bundle["submissions_root"] / "synthetic-labeler-a.json"
    outside = tmp_path / "outside-submission-alias.json"
    outside.write_bytes(submission.read_bytes())
    submission.unlink()
    os.link(outside, submission)
    assert submission.stat().st_nlink == 2
    with pytest.raises(GovernanceContractError, match="hard-linked"):
        _verify_labeling(bundle)


def test_bounded_governance_read_detects_in_place_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_bytes(b'{"value":"before"}')
    original_read = os.read
    changed = False

    def changing_read(descriptor: int, count: int) -> bytes:
        nonlocal changed
        chunk = original_read(descriptor, count)
        if chunk and not changed:
            changed = True
            evidence.write_bytes(b'{"value":"after-and-longer"}')
        return chunk

    monkeypatch.setattr(os, "read", changing_read)
    with pytest.raises(GovernanceContractError, match="changed while being read"):
        _bounded_read_regular_file(evidence, "synthetic evidence", max_bytes=1024)


@pytest.mark.parametrize(
    "portable_ref",
    [
        "\uff41.json",
        "con.json",
        "trailing-dot.",
        "forbidden?.json",
        "a" * 241 + ".json",
    ],
)
def test_submission_refs_use_bounded_conservative_portable_paths(
    tmp_path: Path, portable_ref: str
) -> None:
    ledger = copy.deepcopy(_labeling_bundle(tmp_path)["ledger"])
    ledger["submissions"][0]["portable_ref"] = portable_ref
    with pytest.raises(ValidationError):
        _validate_json(DecisionLedger, ledger)


@pytest.mark.parametrize(
    "authority",
    [
        "synthetic-packet-custodian",
        "synthetic-labeler-a",
        "synthetic-adjudicator",
    ],
)
def test_labeling_authority_must_be_separate_from_implementation(
    tmp_path: Path, authority: str
) -> None:
    bundle = _labeling_bundle(tmp_path)
    split = copy.deepcopy(bundle["blind_split"])
    split["implementation_author_ids"] = [authority]
    _rewrite_split_and_labeling_graph(bundle, split)
    with pytest.raises(GovernanceContractError, match="implementation authors"):
        _verify_labeling(bundle)


@pytest.mark.parametrize(
    ("decided_at_utc", "message"),
    [
        ("2025-12-31T23:59:59Z", "before the packet was prepared"),
        ("2026-01-01T00:00:00Z", "before its review round opened"),
    ],
)
def test_response_cannot_predate_packet_or_review_round(
    tmp_path: Path, decided_at_utc: str, message: str
) -> None:
    bundle = _labeling_bundle(tmp_path)
    _rewrite_one_response_time(
        bundle, labeler_id="synthetic-labeler-a", decided_at_utc=decided_at_utc
    )
    with pytest.raises(GovernanceContractError, match=message):
        _verify_labeling(bundle)


def test_response_may_equal_its_review_round_opening(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    _rewrite_one_response_time(
        bundle,
        labeler_id="synthetic-labeler-a",
        decided_at_utc="2026-01-01T00:00:30Z",
    )
    assert _verify_labeling(bundle).contract_kind == "LABELING_GOVERNANCE"


def test_submission_evidence_tamper_fails_even_after_attacker_rehashes_graph(
    tmp_path: Path,
) -> None:
    bundle = _labeling_bundle(tmp_path)
    labeler_id = "synthetic-labeler-a"
    submission = copy.deepcopy(bundle["submission_payloads"][labeler_id])
    submission["responses"][0]["evidence_sha256"] = _sha("attacker-evidence")
    submission_path = bundle["submissions_root"] / f"{labeler_id}.json"
    submission_raw, submission_sha = _canonical_write(submission_path, submission)

    ledger = copy.deepcopy(bundle["ledger"])
    record = next(item for item in ledger["submissions"] if item["labeler_id"] == labeler_id)
    record["sha256"] = submission_sha
    record["bytes"] = len(submission_raw)
    tampered_response_sha = hashlib.sha256(
        canonical_json_bytes(submission["responses"][0])
    ).hexdigest()
    tampered_key = submission["responses"][0]["item_key"]
    for event in ledger["decisions"]:
        for vote in event["votes"]:
            if vote["labeler_id"] == labeler_id:
                vote["submission_sha256"] = submission_sha
                if event["item_key"] == tampered_key:
                    vote["response_sha256"] = tampered_response_sha
    _, bundle["ledger_sha256"] = _canonical_write(bundle["ledger_path"], ledger)
    with pytest.raises(GovernanceContractError, match="changed evidence"):
        _verify_labeling(bundle)


def test_labeling_rejects_broken_correction_chain(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    ledger = copy.deepcopy(bundle["ledger"])
    correction = next(event for event in ledger["decisions"] if event["revision"] == 2)
    correction["supersedes_decision_id"] = "synthetic-wrong-prior"
    _, bundle["ledger_sha256"] = _canonical_write(bundle["ledger_path"], ledger)
    with pytest.raises(GovernanceContractError, match="immediate prior decision"):
        _verify_labeling(bundle)


def test_post_freeze_correction_requires_new_prediction_blind_reviewers(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    ledger = copy.deepcopy(bundle["ledger"])
    ledger["ledger_version"] = "v2"
    correction_round = copy.deepcopy(ledger["review_rounds"][0])
    correction_round.update(
        {
            "review_round_id": "synthetic-review-round-2",
            "sequence": 2,
            "kind": "POST_FREEZE_CORRECTION",
            "supersedes_review_round_id": "synthetic-review-round-1",
            "opened_at_utc": "2026-01-01T00:06:00Z",
            "completed_at_utc": "2026-01-01T00:09:00Z",
        }
    )
    ledger["review_rounds"].append(correction_round)
    ledger["active_review_round_id"] = "synthetic-review-round-2"
    ledger["revision_context"] = {
        "kind": "POST_FREEZE_CORRECTION",
        "supersedes_ledger_sha256": _sha("prior-ledger"),
        "invalidated_measurement_sha256s": [_sha("synthetic-affected-measurement")],
        "correction_reason": "synthetic evidence-backed correction",
    }
    _, bundle["ledger_sha256"] = _canonical_write(bundle["ledger_path"], ledger)
    with pytest.raises(GovernanceContractError, match="new reviewer authority separate"):
        _verify_labeling(bundle)


def test_post_freeze_correction_retains_exact_prior_prefix(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    _extend_with_post_freeze_correction(bundle, tmp_path)
    result = _verify_labeling(bundle)
    assert result.contract_kind == "LABELING_GOVERNANCE"
    assert result.independent_labeler_count == 2
    assert len(bundle["ledger"]["review_rounds"]) == 2
    assert len(bundle["ledger"]["submissions"]) == 4


def test_correction_round_must_open_strictly_after_prior_ledger_freeze(
    tmp_path: Path,
) -> None:
    bundle = _labeling_bundle(tmp_path)
    _extend_with_post_freeze_correction(bundle, tmp_path)
    ledger = copy.deepcopy(bundle["ledger"])
    ledger["review_rounds"][-1]["opened_at_utc"] = "2026-01-01T00:05:00Z"
    _, bundle["ledger_sha256"] = _canonical_write(bundle["ledger_path"], ledger)
    with pytest.raises(GovernanceContractError, match="strictly after the prior ledger"):
        _verify_labeling(bundle)


def test_review_rounds_cannot_overlap_or_move_backwards(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    _extend_with_post_freeze_correction(bundle, tmp_path)
    ledger = copy.deepcopy(bundle["ledger"])
    ledger["review_rounds"][-1]["opened_at_utc"] = ledger["review_rounds"][0][
        "completed_at_utc"
    ]
    with pytest.raises(ValidationError, match="strictly after the prior round"):
        _validate_json(DecisionLedger, ledger)


def test_correction_suffix_cannot_reuse_retained_prior_authority(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    _extend_with_post_freeze_correction(bundle, tmp_path)
    ledger = copy.deepcopy(bundle["ledger"])
    appended = ledger["decisions"][-1]
    prior = next(
        event
        for event in reversed(ledger["decisions"][:-1])
        if event["item_key"] == appended["item_key"]
    )
    appended["review_round_id"] = prior["review_round_id"]
    appended["reviewer_ids"] = prior["reviewer_ids"]
    appended["adjudicator_id"] = prior["adjudicator_id"]
    appended["votes"] = prior["votes"]
    appended["decided_at_utc"] = prior["decided_at_utc"]
    _, bundle["ledger_sha256"] = _canonical_write(bundle["ledger_path"], ledger)
    with pytest.raises(GovernanceContractError, match="retained prior reviewer authority"):
        _verify_labeling(bundle)


def test_decision_cannot_postdate_its_review_round(tmp_path: Path) -> None:
    ledger = copy.deepcopy(_labeling_bundle(tmp_path)["ledger"])
    ledger["decisions"][-1]["decided_at_utc"] = "2026-01-01T00:04:31Z"
    with pytest.raises(ValidationError, match="after its review round"):
        _validate_json(DecisionLedger, ledger)


def test_post_freeze_correction_rejects_rewritten_prior_history(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    _extend_with_post_freeze_correction(bundle, tmp_path)
    ledger = copy.deepcopy(bundle["ledger"])
    ledger["decisions"][0]["reason"] = "synthetic attacker rewrote retained history"
    _, bundle["ledger_sha256"] = _canonical_write(bundle["ledger_path"], ledger)
    with pytest.raises(GovernanceContractError, match="rewrites retained prior decision events"):
        _verify_labeling(bundle)


def test_post_freeze_correction_requires_prior_bytes_not_only_a_claimed_hash(
    tmp_path: Path,
) -> None:
    bundle = _labeling_bundle(tmp_path)
    _extend_with_post_freeze_correction(bundle, tmp_path)
    bundle["prior_ledger_path"] = None
    with pytest.raises(GovernanceContractError, match="requires prior ledger bytes"):
        _verify_labeling(bundle)


def test_models_reject_single_labeler_or_adjudicator_overlap(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    ledger = copy.deepcopy(bundle["ledger"])
    ledger["review_rounds"][0]["labeler_ids"] = ["synthetic-labeler-a"]
    ledger["submissions"] = ledger["submissions"][:1]
    with pytest.raises(ValidationError):
        _validate_json(DecisionLedger, ledger)

    ledger = copy.deepcopy(bundle["ledger"])
    ledger["review_rounds"][0]["adjudicator_id"] = ledger["review_rounds"][0][
        "labeler_ids"
    ][0]
    with pytest.raises(ValidationError, match="separate from labelers"):
        _validate_json(DecisionLedger, ledger)


def test_blind_split_exact_boundary_and_candidate_order_pass(tmp_path: Path) -> None:
    governance = _governance_manifests(tmp_path)
    result = verify_blind_split(
        manifest_path=governance["blind_split_path"],
        expected_manifest_sha256=governance["blind_split_sha256"],
        source_manifest_path=governance["source_manifest_path"],
        expected_source_manifest_sha256=governance["source_manifest_sha256"],
        acceptance_policy_path=POLICY,
        _allow_test_source_contract=True,
    )
    assert result.contract_kind == "BLIND_SPLIT_GOVERNANCE"
    assert result.holdout_document_count == 5
    assert result.item_or_document_count == 12
    assert result.candidate_frozen is True
    assert result.metrics_evaluated is False
    assert result.external_acceptance_granted is False
    assert result.source_contract_kind == "SOURCE_CONTRACT_TEST"


def test_blind_split_rejects_source_identity_not_in_frozen_manifest(tmp_path: Path) -> None:
    governance = _governance_manifests(tmp_path)
    split = copy.deepcopy(governance["blind_split"])
    split["documents"][0]["raw_sha256"] = _sha("attacker-source-bytes")
    path, digest = _write_blind(tmp_path, split)
    with pytest.raises(GovernanceContractError, match="source binding differs"):
        verify_blind_split(
            manifest_path=path,
            expected_manifest_sha256=digest,
            source_manifest_path=governance["source_manifest_path"],
            expected_source_manifest_sha256=governance["source_manifest_sha256"],
            acceptance_policy_path=POLICY,
            _allow_test_source_contract=True,
        )


def test_source_manifest_requires_frozen_acquisition_canonical_form(tmp_path: Path) -> None:
    governance = _governance_manifests(tmp_path)
    noncanonical = canonical_json_bytes(governance["source_manifest"])
    governance["source_manifest_path"].write_bytes(noncanonical)
    digest = hashlib.sha256(noncanonical).hexdigest()
    split = copy.deepcopy(governance["blind_split"])
    split["source_manifest_sha256"] = digest
    split_path, split_digest = _write_blind(tmp_path, split)
    with pytest.raises(GovernanceContractError, match="not canonical compact"):
        verify_blind_split(
            manifest_path=split_path,
            expected_manifest_sha256=split_digest,
            source_manifest_path=governance["source_manifest_path"],
            expected_source_manifest_sha256=digest,
            acceptance_policy_path=POLICY,
            _allow_test_source_contract=True,
        )


def test_blind_split_rejects_below_exact_40_percent(tmp_path: Path) -> None:
    payload = _blind_manifest()
    for document in payload["documents"]:
        if document["source_id"] in {"synthetic-01-rfc-h", "synthetic-05-w3c-h2"}:
            document["split"] = "DEVELOPMENT"
    with pytest.raises(ValidationError, match="below the exact 40%"):
        _validate_json(BlindSplitManifest, payload)


def test_blind_split_rejects_missing_holdout_m1_family() -> None:
    payload = _blind_manifest()
    for document in payload["documents"]:
        if document["family"] == "WHATWG" and document["split"] == "BLIND_HOLDOUT":
            document["m1_in_scope"] = False
            document["m2_in_scope"] = True
            document["m2_lineage_chain_id"] = "synthetic-whatwg-holdout"
    with pytest.raises(ValidationError, match="WHATWG"):
        _validate_json(BlindSplitManifest, payload)


def test_blind_split_rejects_raw_or_derived_cross_split_overlap() -> None:
    payload = _blind_manifest()
    development = next(
        item for item in payload["documents"] if item["split"] == "DEVELOPMENT"
    )
    holdout = next(
        item for item in payload["documents"] if item["split"] == "BLIND_HOLDOUT"
    )
    development["derived_sha256s"] = [holdout["raw_sha256"]]
    with pytest.raises(ValidationError, match="raw/derived hashes overlap"):
        _validate_json(BlindSplitManifest, payload)


def test_blind_split_rejects_m2_lineage_split() -> None:
    payload = _blind_manifest()
    member = next(
        item for item in payload["documents"] if item["source_id"] == "synthetic-05-w3c-h2"
    )
    member["split"] = "DEVELOPMENT"
    replacement = next(
        item for item in payload["documents"] if item["source_id"] == "synthetic-09-rfc-m1-dev"
    )
    replacement["split"] = "BLIND_HOLDOUT"
    with pytest.raises(ValidationError, match="lineage chains cross"):
        _validate_json(BlindSplitManifest, payload)


def test_blind_split_rejects_undersized_per_version_lineage_aliases() -> None:
    payload = _blind_manifest()
    member = next(
        item for item in payload["documents"] if item["source_id"] == "synthetic-03-rfc-d2"
    )
    member["m2_lineage_chain_id"] = "synthetic-rfc-alias"
    with pytest.raises(ValidationError, match="at least three whole document versions"):
        _validate_json(BlindSplitManifest, payload)


def test_blind_split_requires_an_m2_lineage_chain_for_every_family() -> None:
    payload = _blind_manifest()
    for document in payload["documents"]:
        if document["family"] == "RFC" and document["m2_in_scope"]:
            document["m2_in_scope"] = False
            document["m2_lineage_chain_id"] = None
    with pytest.raises(ValidationError, match="cover every required family.*RFC"):
        _validate_json(BlindSplitManifest, payload)


@pytest.mark.parametrize(
    ("field", "bad_value", "message"),
    [
        ("holdout_opened_at_utc", "2026-01-01T00:02:00Z", "strictly after exact"),
        ("predictions_started_at_utc", "2026-01-01T00:02:00Z", "strictly after exact"),
        ("predictions_started_at_utc", "2026-01-01T00:03:00Z", "after holdout opens"),
    ],
)
def test_blind_split_rejects_access_or_prediction_before_candidate_freeze(
    field: str,
    bad_value: str,
    message: str,
) -> None:
    payload = _blind_manifest()
    payload["candidate_freeze"][field] = bad_value
    with pytest.raises(ValidationError, match=message):
        _validate_json(BlindSplitManifest, payload)


def test_not_frozen_candidate_cannot_have_prediction_or_artifact_fields() -> None:
    payload = _blind_manifest()
    payload["candidate_freeze"]["status"] = "NOT_FROZEN"
    with pytest.raises(ValidationError, match="must not contain"):
        _validate_json(BlindSplitManifest, payload)


def test_canonical_json_and_duplicate_key_fail_closed(tmp_path: Path) -> None:
    governance = _governance_manifests(tmp_path)
    payload = governance["blind_split"]
    path = governance["blind_split_path"]
    raw = canonical_json_bytes(payload) + b"\n"
    path.write_bytes(raw)
    with pytest.raises(GovernanceContractError, match="not canonical"):
        verify_blind_split(
            manifest_path=path,
            expected_manifest_sha256=hashlib.sha256(raw).hexdigest(),
            source_manifest_path=governance["source_manifest_path"],
            expected_source_manifest_sha256=payload["source_manifest_sha256"],
            acceptance_policy_path=POLICY,
            _allow_test_source_contract=True,
        )

    duplicate_raw = b'{"kind":"x","kind":"x"}'
    path.write_bytes(duplicate_raw)
    with pytest.raises(GovernanceContractError, match="Duplicate JSON object key"):
        verify_blind_split(
            manifest_path=path,
            expected_manifest_sha256=hashlib.sha256(duplicate_raw).hexdigest(),
            source_manifest_path=governance["source_manifest_path"],
            expected_source_manifest_sha256=payload["source_manifest_sha256"],
            acceptance_policy_path=POLICY,
            _allow_test_source_contract=True,
        )


def test_repository_and_packaged_schemas_are_exact_strict_validators(tmp_path: Path) -> None:
    bundle = _labeling_bundle(tmp_path)
    payload_by_name = {
        "blind_split_manifest_v1.schema.json": _blind_manifest(),
        "decision_ledger_v1.schema.json": bundle["ledger"],
        "label_submission_v1.schema.json": next(iter(bundle["submission_payloads"].values())),
        "labeling_packet_v1.schema.json": bundle["packet"],
    }
    for name in SCHEMA_NAMES:
        repository_raw = (ROOT / "schemas" / name).read_bytes()
        packaged_raw = (ROOT / "src" / "normshift" / "schemas" / name).read_bytes()
        assert repository_raw == packaged_raw
        schema = strict_loads(repository_raw)
        assert canonical_json_bytes(schema) == repository_raw
        assert "does not" in schema["$comment"]
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload_by_name[name])


def test_cli_production_mode_rejects_synthetic_source_contract(tmp_path: Path) -> None:
    governance = _governance_manifests(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "governance",
            "verify-blind-split",
            str(governance["blind_split_path"]),
            "--manifest-sha256",
            governance["blind_split_sha256"],
            "--source-manifest",
            str(governance["source_manifest_path"]),
            "--source-manifest-sha256",
            governance["source_manifest_sha256"],
            "--acceptance-policy",
            str(POLICY),
        ],
    )
    assert result.exit_code == 2, result.output
    assert "test-only source contracts are forbidden" in result.output


def test_labeling_cli_production_mode_rejects_synthetic_source_contract(
    tmp_path: Path,
) -> None:
    bundle = _labeling_bundle(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "governance",
            "verify-labeling",
            str(bundle["packet_path"]),
            "--packet-sha256",
            bundle["packet_sha256"],
            "--source-manifest",
            str(bundle["source_manifest_path"]),
            "--source-manifest-sha256",
            bundle["source_manifest_sha256"],
            "--blind-split-manifest",
            str(bundle["blind_split_path"]),
            "--split-manifest-sha256",
            bundle["blind_split_sha256"],
            "--submissions-root",
            str(bundle["submissions_root"]),
            "--ledger",
            str(bundle["ledger_path"]),
            "--ledger-sha256",
            bundle["ledger_sha256"],
            "--acceptance-policy",
            str(POLICY),
        ],
    )
    assert result.exit_code == 2, result.output
    assert "test-only source contracts are forbidden" in result.output
