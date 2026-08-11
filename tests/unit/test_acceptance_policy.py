"""Pre-result M1/M2 acceptance policy freeze."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from normshift.strict_json import strict_loads

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "acceptance" / "m1_m2_prereg_v1.json"
SIDECAR = POLICY.with_suffix(POLICY.suffix + ".sha256")
EXPECTED_SHA256 = "0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773"
EXPECTED_BYTES = 15_310


def _policy() -> dict[str, Any]:
    payload = strict_loads(POLICY.read_bytes())
    assert isinstance(payload, dict)
    return payload


def test_preregistered_policy_bytes_are_frozen() -> None:
    raw = POLICY.read_bytes()
    assert len(raw) == EXPECTED_BYTES
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    assert SIDECAR.read_text(encoding="utf-8") == (
        f"{EXPECTED_SHA256}  {POLICY.name}\n"
    )


def test_preregistered_policy_retains_fail_closed_authority() -> None:
    payload = _policy()
    assert payload["policy_id"] == "normshift-m1-m2-prereg-v1"
    assert payload["status"] == "FROZEN_BEFORE_BLIND_EVALUATION"
    assert payload["baseline"] == {
        "commit": "b3af3dc26e64a3399545d179731222f6e87213c9",
        "tree": "c629e2d51fc5219514d6068a90d3453725bd8010",
        "default_branch": "master",
        "repository": "https://github.com/taipei49314/NormShift",
    }
    assert payload["authority"]["implementation_authority_may_approve_policy"] is False
    assert payload["metric_contract"]["aggregate_scores_are_acceptance_authority"] is False
    assert payload["metric_contract"]["all_required_classes_must_pass_individually"] is True
    assert payload["ground_truth_contract"]["minimum_independent_labelers"] == 2
    assert payload["ground_truth_contract"]["independent_adjudicator_required"] is True
    assert payload["blind_holdout"]["minimum_holdout_fraction_by_document_count"] == "0.40"
    assert (
        payload["revision_and_failure_policy"]["threshold_lowering_or_support_reduction"]
        == "FORBIDDEN"
    )
    assert payload["revision_and_failure_policy"]["open_p0_or_p1_or_false_success"] == "FAIL"


def test_preregistered_policy_has_all_nonzero_per_class_gates() -> None:
    payload = _policy()
    m1 = payload["m1"]
    assert {item["family"] for item in m1["requirement_extraction"]} == {
        "RFC",
        "W3C_TR",
        "WHATWG",
    }
    assert all(
        item["minimum_gold_positive_support"] >= 30
        for item in m1["requirement_extraction"]
    )
    assert all(
        item["minimum_labeled_modal_distractors"] >= 30
        for item in m1["requirement_extraction"]
    )
    assert len(m1["region_classification"]) == 9
    assert all(item["minimum_support"] >= 20 for item in m1["region_classification"])
    assert {item["class"] for item in m1["modality_classification"]} == {
        "MUST",
        "MUST_NOT",
        "SHOULD",
        "SHOULD_NOT",
        "MAY",
    }

    m2 = payload["m2"]
    for group in (
        "identity",
        "relations",
        "change_classes",
        "definition_and_xref_classes",
        "ambiguity_routing",
    ):
        assert m2[group]
        assert all(item["minimum_support"] > 0 for item in m2[group])
        assert all(item["minimum_real_support"] > 0 for item in m2[group])
    assert m2["required_family_chain_coverage"] == ["RFC", "W3C_TR", "WHATWG"]
