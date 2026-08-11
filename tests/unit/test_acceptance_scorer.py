from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from normshift.acceptance.item_key import acceptance_item_key
from normshift.acceptance.models import AcceptanceResult
from normshift.acceptance.scorer import (
    POLICY_SHA256,
    REQUIRED_SCORER_FILES,
    AcceptanceScoringError,
    score_acceptance,
)
from normshift.evidence.hashing import canonical_json_bytes
from normshift.strict_json import strict_loads

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "acceptance" / "m1_m2_prereg_v1.json"
MANIFEST = ROOT / "acceptance" / "scorer_v1_manifest.json"
SIDECAR = ROOT / "acceptance" / "scorer_v1_manifest.json.sha256"
SCRIPT = ROOT / "scripts" / "score_acceptance.py"


def _sha(value: str | bytes) -> str:
    raw = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def _frozen_manifest_sha() -> str:
    digest, name = SIDECAR.read_text(encoding="ascii").strip().split("  ")
    assert name == MANIFEST.name
    assert digest == _sha(MANIFEST.read_bytes())
    return digest


def _source(family: str, version: int) -> dict[str, Any]:
    source_id = f"{family.lower()}-{version}"
    return {
        "source_id": source_id,
        "family": family,
        "origin": "ACTUAL",
        "raw_sha256": _sha(f"{source_id}-raw"),
        "standard_id": f"{family}-standard",
        "version": f"v{version}",
        "chain_id": f"{family.lower()}-chain",
        "lineage_sequence": version,
        "portable_source_ref": f"sources/{source_id}.html",
    }


def _documents() -> tuple[dict[str, Any], dict[str, Any]]:
    sources = [
        _source(family, version)
        for family in ("RFC", "W3C_TR", "WHATWG")
        for version in range(1, 4)
    ]
    source_ids = {
        family: [source["source_id"] for source in sources if source["family"] == family]
        for family in ("RFC", "W3C_TR", "WHATWG")
    }
    items: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    source_by_id = {source["source_id"]: source for source in sources}

    def slot_for(task: str, expected_class: str) -> str:
        if task == "M1_REQUIREMENT_EXTRACTION":
            return "requirement"
        if task == "M1_MODALITY":
            return "modality"
        if task == "M1_REGION":
            return "region"
        if task == "M1_FAMILY_DETECTION":
            return "family"
        if task == "M2_IDENTITY":
            return "identity"
        if task == "M2_RELATION":
            return "relation"
        if task == "M2_AMBIGUITY_ROUTING":
            return "routing"
        if task == "M2_CHANGE":
            return {
                "MOVE_ONLY": "structural_form",
                "REWRITE_ONLY": "structural_form",
                "MOVED_AND_REWRITTEN": "structural_form",
                "ACTOR_CHANGED": "actor",
                "ACTION_CHANGED": "action",
                "OBJECT_CHANGED": "object",
                "SCOPE_CHANGED": "scope",
                "MODALITY_CHANGED": "modality",
                "POLARITY_CHANGED": "polarity",
                "CONDITION_ADDED": "condition",
                "CONDITION_REMOVED": "condition",
                "EXCEPTION_ADDED": "exception",
                "EXCEPTION_REMOVED": "exception",
            }[expected_class]
        return {
            "DEFINITION_ADDED": "definition",
            "DEFINITION_CHANGED": "definition",
            "DEFINITION_REMOVED": "definition",
            "REFERENCES_DEFINITION": "definition_reference",
            "CROSS_REFERENCE": "cross_reference",
            "INDIRECT_IMPACT": "indirect_impact",
        }[expected_class]

    def add_item(
        task: str,
        expected_class: str,
        source_id_list: list[str],
        *,
        modal_distractor: bool = False,
    ) -> None:
        index = len(items)
        label_id = f"label-{index:04d}"
        decision_id = f"decision-{index:04d}"
        locators = [
            f"{source_by_id[source_id]['portable_source_ref']}#case-{index}"
            for source_id in source_id_list
        ]
        evaluation_slot = slot_for(task, expected_class)
        source_sha256s = [source_by_id[source_id]["raw_sha256"] for source_id in source_id_list]
        item_key = acceptance_item_key(
            task=task,
            evaluation_slot=evaluation_slot,
            source_sha256s=source_sha256s,
            portable_locators=locators,
        )
        evidence_sha256 = _sha("\x1f".join(locators))
        item = {
            "item_key": item_key,
            "label_id": label_id,
            "decision_id": decision_id,
            "task": task,
            "evaluation_slot": evaluation_slot,
            "expected_class": expected_class,
            "source_ids": source_id_list,
            "portable_locators": locators,
            "evidence_sha256": evidence_sha256,
            "modal_distractor": modal_distractor,
        }
        decision = {
            "decision_id": decision_id,
            "label_id": label_id,
            "item_key": item_key,
            "task": task,
            "evaluation_slot": evaluation_slot,
            "source_ids": source_id_list,
            "portable_locators": locators,
            "evidence_sha256": evidence_sha256,
            "decided_class": expected_class,
            "reviewer_ids": ["reviewer-alpha", "reviewer-beta"],
            "adjudicator_id": "reviewer-gamma",
            "decision": "ACCEPTED",
            "reason": "Synthetic scorer-contract fixture; not product ground truth.",
            "decided_at_utc": "2026-08-11T00:00:00Z",
        }
        items.append(item)
        decisions.append(decision)

    for family in ("RFC", "W3C_TR", "WHATWG"):
        for index in range(30):
            add_item(
                "M1_REQUIREMENT_EXTRACTION",
                "REQUIREMENT",
                [source_ids[family][index % 3]],
            )
        for index in range(30):
            add_item(
                "M1_REQUIREMENT_EXTRACTION",
                "NONE",
                [source_ids[family][index % 3]],
                modal_distractor=True,
            )
        for class_name in ("NORMATIVE", "INFORMATIVE", "EXCLUDED"):
            for index in range(20):
                add_item("M1_REGION", class_name, [source_ids[family][index % 3]])

    for class_name, support in {
        "MUST": 25,
        "MUST_NOT": 8,
        "SHOULD": 10,
        "SHOULD_NOT": 8,
        "MAY": 10,
    }.items():
        for index in range(support):
            family = ("RFC", "W3C_TR", "WHATWG")[index % 3]
            add_item("M1_MODALITY", class_name, [source_ids[family][index % 3]])

    for family in ("RFC", "W3C_TR", "WHATWG"):
        for source_id in source_ids[family][:2]:
            add_item("M1_FAMILY_DETECTION", family, [source_id])

    m2_specs = {
        "M2_IDENTITY": {"SAME_LINEAGE": 40, "DIFFERENT_LINEAGE": 40},
        "M2_RELATION": {
            "CONTINUES": 30,
            "SPLIT_INTO": 6,
            "MERGED_FROM": 6,
            "ADDED": 10,
            "REMOVED": 10,
            "AMBIGUOUS": 8,
        },
        "M2_CHANGE": {
            "MOVE_ONLY": 8,
            "REWRITE_ONLY": 8,
            "MOVED_AND_REWRITTEN": 8,
            "ACTOR_CHANGED": 6,
            "ACTION_CHANGED": 6,
            "OBJECT_CHANGED": 6,
            "SCOPE_CHANGED": 6,
            "MODALITY_CHANGED": 6,
            "POLARITY_CHANGED": 6,
            "CONDITION_ADDED": 6,
            "CONDITION_REMOVED": 6,
            "EXCEPTION_ADDED": 6,
            "EXCEPTION_REMOVED": 6,
        },
        "M2_DEFINITION_XREF": {
            "DEFINITION_ADDED": 6,
            "DEFINITION_CHANGED": 6,
            "DEFINITION_REMOVED": 6,
            "REFERENCES_DEFINITION": 10,
            "CROSS_REFERENCE": 10,
            "INDIRECT_IMPACT": 6,
        },
        "M2_AMBIGUITY_ROUTING": {"ROUTE_AMBIGUOUS": 10, "ROUTE_CONFIDENT": 30},
    }
    all_source_ids = [source["source_id"] for source in sources]
    for task, classes in m2_specs.items():
        for class_name, support in classes.items():
            for index in range(support):
                first = all_source_ids[index % len(all_source_ids)]
                family = next(
                    source["family"] for source in sources if source["source_id"] == first
                )
                family_sources = source_ids[family]
                second = family_sources[(family_sources.index(first) + 1) % 3]
                add_item(task, class_name, [first, second])

    manifest_sha = _frozen_manifest_sha()
    gold = {
        "kind": "normshift-acceptance-gold",
        "schema_version": "1.0.0",
        "policy_id": "normshift-m1-m2-prereg-v1",
        "policy_sha256": POLICY_SHA256,
        "scorer_manifest_sha256": manifest_sha,
        "dataset_id": "synthetic-scorer-contract",
        "dataset_version": "v1",
        "split": "BLIND_HOLDOUT",
        "source_manifest_sha256": _sha("source-manifest"),
        "split_manifest_sha256": _sha("split-manifest"),
        "decision_ledger_sha256": _sha("decision-ledger"),
        "frozen_at_utc": "2026-08-11T00:00:00Z",
        "review": {
            "labeler_ids": ["reviewer-alpha", "reviewer-beta"],
            "adjudicator_id": "reviewer-gamma",
            "predictions_viewed_before_freeze": False,
            "labels_hash_frozen": True,
            "decided_at_utc": "2026-08-11T00:00:00Z",
        },
        "sources": sources,
        "items": items,
        "decisions": decisions,
    }
    gold_raw = canonical_json_bytes(gold)
    predictions = {
        "kind": "normshift-acceptance-predictions",
        "schema_version": "1.0.0",
        "policy_id": "normshift-m1-m2-prereg-v1",
        "policy_sha256": POLICY_SHA256,
        "scorer_manifest_sha256": manifest_sha,
        "dataset_id": gold["dataset_id"],
        "dataset_version": gold["dataset_version"],
        "gold_sha256": _sha(gold_raw),
        "candidate": {
            "commit": "a" * 40,
            "tree": "b" * 40,
            "wheel_sha256": "c" * 64,
            "sdist_sha256": "d" * 64,
            "source_zip_sha256": "e" * 64,
            "bundle_sha256": "f" * 64,
        },
        "generated_at_utc": "2026-08-11T00:01:00Z",
        "predictions": [
            {
                "item_key": item["item_key"],
                "task": item["task"],
                "evaluation_slot": item["evaluation_slot"],
                "source_sha256s": [
                    source_by_id[source_id]["raw_sha256"] for source_id in item["source_ids"]
                ],
                "portable_locators": item["portable_locators"],
                "predicted_class": item["expected_class"],
            }
            for item in items
        ],
    }
    return gold, predictions


def _write_documents(
    tmp_path: Path, gold: dict[str, Any], predictions: dict[str, Any]
) -> tuple[Path, Path]:
    gold_path = tmp_path / "gold.json"
    prediction_path = tmp_path / "predictions.json"
    gold_raw = canonical_json_bytes(gold)
    predictions["gold_sha256"] = _sha(gold_raw)
    gold_path.write_bytes(gold_raw)
    prediction_path.write_bytes(canonical_json_bytes(predictions))
    return gold_path, prediction_path


def _score(tmp_path: Path, gold: dict[str, Any], predictions: dict[str, Any]):
    gold_path, prediction_path = _write_documents(tmp_path, gold, predictions)
    return score_acceptance(
        policy_path=POLICY,
        gold_path=gold_path,
        predictions_path=prediction_path,
        scorer_manifest_path=MANIFEST,
        expected_scorer_manifest_sha256=_frozen_manifest_sha(),
        source_root=ROOT,
    )


def test_exact_per_class_scoring_is_deterministic_and_never_grants_audit(tmp_path: Path) -> None:
    gold, predictions = _documents()
    first = _score(tmp_path, gold, predictions)
    second = _score(tmp_path, gold, predictions)

    assert len(first.metric_gates) == 49
    assert first.m1_metric_thresholds_passed
    assert first.m2_metric_thresholds_passed
    assert first.all_metric_thresholds_passed
    assert not first.external_gates_evaluated
    assert len(first.unverified_external_gates) == 8
    assert not first.external_acceptance_granted
    assert first.evaluation_scope == "DECLARED_SUPPORT_METRICS_ONLY"
    assert canonical_json_bytes(first.model_dump(mode="json")) == canonical_json_bytes(
        second.model_dump(mode="json")
    )


def test_missing_predictions_are_false_negatives_without_rounding(tmp_path: Path) -> None:
    gold, predictions = _documents()
    rfc_positive = {
        item["item_key"]
        for item in gold["items"]
        if item["task"] == "M1_REQUIREMENT_EXTRACTION"
        and item["expected_class"] == "REQUIREMENT"
        and item["source_ids"][0].startswith("rfc-")
    }
    removed = 0
    retained = []
    for prediction in predictions["predictions"]:
        if prediction["item_key"] in rfc_positive and removed < 2:
            removed += 1
        else:
            retained.append(prediction)
    predictions["predictions"] = retained
    result = _score(tmp_path, gold, predictions)
    gate = next(
        item for item in result.metric_gates if item.gate_id == "m1.extraction.rfc.requirement"
    )
    assert (gate.true_positives, gate.false_negatives) == (28, 2)
    assert not gate.recall.passed
    assert gate.f1.passed
    assert not gate.metric_thresholds_passed


def test_unexpected_predictions_are_false_positives(tmp_path: Path) -> None:
    gold, predictions = _documents()
    distractors = {
        item["item_key"]
        for item in gold["items"]
        if item["task"] == "M1_REQUIREMENT_EXTRACTION"
        and item["modal_distractor"]
        and item["source_ids"][0].startswith("rfc-")
    }
    changed = 0
    for prediction in predictions["predictions"]:
        if prediction["item_key"] in distractors and changed < 2:
            prediction["predicted_class"] = "REQUIREMENT"
            changed += 1
    result = _score(tmp_path, gold, predictions)
    gate = next(
        item for item in result.metric_gates if item.gate_id == "m1.extraction.rfc.requirement"
    )
    assert (gate.true_positives, gate.false_positives) == (30, 2)
    assert not gate.precision.passed
    assert gate.f1.passed
    assert not gate.metric_thresholds_passed


def test_valid_predictions_outside_gold_are_counted_as_false_positives(
    tmp_path: Path,
) -> None:
    gold, predictions = _documents()
    source = gold["sources"][0]
    for index in range(2):
        locators = [f"{source['portable_source_ref']}#unexpected-{index}"]
        prediction = {
            "task": "M1_MODALITY",
            "evaluation_slot": "modality",
            "source_sha256s": [source["raw_sha256"]],
            "portable_locators": locators,
            "predicted_class": "MUST",
        }
        prediction["item_key"] = acceptance_item_key(
            task=prediction["task"],
            evaluation_slot=prediction["evaluation_slot"],
            source_sha256s=prediction["source_sha256s"],
            portable_locators=prediction["portable_locators"],
        )
        predictions["predictions"].append(prediction)
    result = _score(tmp_path, gold, predictions)
    gate = next(item for item in result.metric_gates if item.gate_id == "m1.modality.must")
    assert (gate.true_positives, gate.false_positives) == (25, 2)
    assert not gate.precision.passed
    assert not gate.metric_thresholds_passed


def test_m2_cross_family_hard_negatives_and_extra_predictions_are_scored(
    tmp_path: Path,
) -> None:
    gold, predictions = _documents()
    source_by_id = {source["source_id"]: source for source in gold["sources"]}
    source_ids = ["rfc-1", "w3c_tr-1"]
    locators = [
        f"{source_by_id[source_id]['portable_source_ref']}#cross-family" for source_id in source_ids
    ]
    source_sha256s = [source_by_id[source_id]["raw_sha256"] for source_id in source_ids]
    item = next(
        value
        for value in gold["items"]
        if value["task"] == "M2_IDENTITY" and value["expected_class"] == "DIFFERENT_LINEAGE"
    )
    old_key = item["item_key"]
    new_key = acceptance_item_key(
        task="M2_IDENTITY",
        evaluation_slot="identity",
        source_sha256s=source_sha256s,
        portable_locators=locators,
    )
    item.update(
        item_key=new_key,
        source_ids=source_ids,
        portable_locators=locators,
        evidence_sha256=_sha("\x1f".join(locators)),
    )
    decision = next(
        value for value in gold["decisions"] if value["decision_id"] == item["decision_id"]
    )
    decision.update(
        item_key=new_key,
        source_ids=source_ids,
        portable_locators=locators,
        evidence_sha256=item["evidence_sha256"],
    )
    prediction = next(value for value in predictions["predictions"] if value["item_key"] == old_key)
    prediction.update(
        item_key=new_key,
        source_sha256s=source_sha256s,
        portable_locators=locators,
    )

    extra_locators = [
        f"{source_by_id[source_id]['portable_source_ref']}#cross-family-extra"
        for source_id in source_ids
    ]
    predictions["predictions"].append(
        {
            "item_key": acceptance_item_key(
                task="M2_IDENTITY",
                evaluation_slot="identity",
                source_sha256s=source_sha256s,
                portable_locators=extra_locators,
            ),
            "task": "M2_IDENTITY",
            "evaluation_slot": "identity",
            "source_sha256s": source_sha256s,
            "portable_locators": extra_locators,
            "predicted_class": "DIFFERENT_LINEAGE",
        }
    )
    result = _score(tmp_path, gold, predictions)
    gate = next(
        value for value in result.metric_gates if value.gate_id == "m2.identity.different_lineage"
    )
    assert gate.true_positives == 40
    assert gate.false_positives == 1
    assert gate.metric_thresholds_passed


def test_perfect_metrics_cannot_hide_below_minimum_support(tmp_path: Path) -> None:
    gold, predictions = _documents()
    victim = next(
        item
        for item in gold["items"]
        if item["task"] == "M1_REGION"
        and item["expected_class"] == "EXCLUDED"
        and item["source_ids"][0].startswith("whatwg-")
    )
    gold["items"] = [item for item in gold["items"] if item["label_id"] != victim["label_id"]]
    gold["decisions"] = [
        item for item in gold["decisions"] if item["decision_id"] != victim["decision_id"]
    ]
    predictions["predictions"] = [
        item for item in predictions["predictions"] if item["item_key"] != victim["item_key"]
    ]
    result = _score(tmp_path, gold, predictions)
    gate = next(item for item in result.metric_gates if item.gate_id == "m1.region.whatwg.excluded")
    assert gate.precision.passed and gate.recall.passed and gate.f1.passed
    assert gate.support_observed == 19
    assert not gate.metric_thresholds_passed
    assert "minimum support not met" in gate.reasons


@pytest.mark.parametrize("failure", ["duplicate", "malformed_key", "wrong_class"])
def test_invalid_prediction_sets_fail_closed(tmp_path: Path, failure: str) -> None:
    gold, predictions = _documents()
    if failure == "duplicate":
        predictions["predictions"].append(deepcopy(predictions["predictions"][0]))
    elif failure == "malformed_key":
        predictions["predictions"][0]["item_key"] = "9" * 64
    else:
        predictions["predictions"][0]["predicted_class"] = "MUST"
    with pytest.raises(AcceptanceScoringError):
        _score(tmp_path, gold, predictions)


def test_policy_gold_and_scorer_hash_bindings_fail_closed(tmp_path: Path) -> None:
    gold, predictions = _documents()
    gold["policy_sha256"] = "0" * 64
    with pytest.raises(AcceptanceScoringError, match="frozen policy"):
        _score(tmp_path, gold, predictions)

    gold, predictions = _documents()
    predictions["scorer_manifest_sha256"] = "0" * 64
    with pytest.raises(AcceptanceScoringError, match="scorer manifest"):
        _score(tmp_path, gold, predictions)

    gold, predictions = _documents()
    gold_path, prediction_path = _write_documents(tmp_path, gold, predictions)
    with pytest.raises(AcceptanceScoringError, match="independent expected"):
        score_acceptance(
            policy_path=POLICY,
            gold_path=gold_path,
            predictions_path=prediction_path,
            scorer_manifest_path=MANIFEST,
            expected_scorer_manifest_sha256="0" * 64,
            source_root=ROOT,
        )


def test_duplicate_keys_and_noncanonical_json_fail_before_scoring(tmp_path: Path) -> None:
    gold, predictions = _documents()
    gold_path, prediction_path = _write_documents(tmp_path, gold, predictions)
    raw = prediction_path.read_text(encoding="utf-8")
    prediction_path.write_text(
        raw.replace('{\n  "candidate"', '{\n  "kind": "duplicate",\n  "candidate"', 1),
        encoding="utf-8",
    )
    with pytest.raises(AcceptanceScoringError, match="strict JSON"):
        score_acceptance(
            policy_path=POLICY,
            gold_path=gold_path,
            predictions_path=prediction_path,
            scorer_manifest_path=MANIFEST,
            expected_scorer_manifest_sha256=_frozen_manifest_sha(),
            source_root=ROOT,
        )
    prediction_path.write_bytes(canonical_json_bytes(predictions) + b"\n")
    with pytest.raises(AcceptanceScoringError, match="not canonical"):
        score_acceptance(
            policy_path=POLICY,
            gold_path=gold_path,
            predictions_path=prediction_path,
            scorer_manifest_path=MANIFEST,
            expected_scorer_manifest_sha256=_frozen_manifest_sha(),
            source_root=ROOT,
        )


@pytest.mark.parametrize(
    "bad_locator",
    [
        "/absolute#x",
        "C:secret#x",
        "https://example.test/x#y",
        "sources/../x#y",
        "sources//x#y",
        "sources/x#bad space",
        "sources/CON.txt#x",
        "sources/trailing.#x",
    ],
)
def test_nonportable_locators_fail_closed(tmp_path: Path, bad_locator: str) -> None:
    gold, predictions = _documents()
    gold["items"][0]["portable_locators"][0] = bad_locator
    gold["decisions"][0]["portable_locators"][0] = bad_locator
    with pytest.raises(AcceptanceScoringError):
        _score(tmp_path, gold, predictions)


def test_oversized_predictions_are_rejected_before_read(tmp_path: Path) -> None:
    gold, predictions = _documents()
    gold_path, prediction_path = _write_documents(tmp_path, gold, predictions)
    with prediction_path.open("wb") as handle:
        handle.truncate(64 * 1024 * 1024 + 1)
    with pytest.raises(AcceptanceScoringError, match="exceeds"):
        score_acceptance(
            policy_path=POLICY,
            gold_path=gold_path,
            predictions_path=prediction_path,
            scorer_manifest_path=MANIFEST,
            expected_scorer_manifest_sha256=_frozen_manifest_sha(),
            source_root=ROOT,
        )


def test_duplicate_source_bytes_fail_closed(tmp_path: Path) -> None:
    gold, predictions = _documents()
    rfc_sources = [item for item in gold["sources"] if item["family"] == "RFC"]
    for source in rfc_sources[1:]:
        source["raw_sha256"] = rfc_sources[0]["raw_sha256"]
    with pytest.raises(AcceptanceScoringError, match="raw_sha256 values must be unique"):
        _score(tmp_path, gold, predictions)


def test_scorer_manifest_and_json_schemas_are_exact_and_valid() -> None:
    manifest_raw = MANIFEST.read_bytes()
    manifest = strict_loads(manifest_raw)
    assert canonical_json_bytes(manifest) == manifest_raw
    assert manifest["policy_sha256"] == POLICY_SHA256
    assert {item["path"] for item in manifest["files"]} == REQUIRED_SCORER_FILES
    for record in manifest["files"]:
        path = ROOT / Path(record["path"])
        raw = path.read_bytes()
        assert len(raw) == record["bytes"]
        assert _sha(raw) == record["sha256"]
    for name in (
        "acceptance_gold_v1.schema.json",
        "acceptance_predictions_v1.schema.json",
        "acceptance_result_v1.schema.json",
    ):
        root_raw = (ROOT / "schemas" / name).read_bytes()
        package_raw = (ROOT / "src" / "normshift" / "schemas" / name).read_bytes()
        assert root_raw == package_raw
        schema = json.loads(root_raw)
        assert "JSON Schema validation alone never grants acceptance" in schema["$comment"]
        Draft202012Validator.check_schema(schema)


def test_result_cross_field_forgery_is_rejected(tmp_path: Path) -> None:
    gold, predictions = _documents()
    result = _score(tmp_path, gold, predictions).model_dump(mode="json")
    result["metric_gates"][0]["true_positives"] += 1
    with pytest.raises(ValidationError, match=r"support must equal TP\+FN"):
        AcceptanceResult.model_validate_json(canonical_json_bytes(result), strict=True)


def test_script_failure_preserves_existing_output(tmp_path: Path) -> None:
    gold, predictions = _documents()
    predictions["predictions"][0]["item_key"] = "9" * 64
    gold_path, prediction_path = _write_documents(tmp_path, gold, predictions)
    output_root = tmp_path / "output"
    output_root.mkdir()
    output = output_root / "acceptance-result.json"
    output.write_bytes(b"sentinel")
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--policy",
            str(POLICY),
            "--gold",
            str(gold_path),
            "--predictions",
            str(prediction_path),
            "--scorer-manifest",
            str(MANIFEST),
            "--scorer-manifest-sha256",
            _frozen_manifest_sha(),
            "--source-root",
            str(ROOT),
            "--required-phase",
            "ALL",
            "--output-root",
            str(output_root),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 1
    assert output.read_bytes() == b"sentinel"
    assert len(completed.stderr) <= 2100


def test_script_cannot_overwrite_frozen_source_tree(tmp_path: Path) -> None:
    gold, predictions = _documents()
    gold_path, prediction_path = _write_documents(tmp_path, gold, predictions)
    scorer_path = ROOT / "src" / "normshift" / "acceptance" / "scorer.py"
    before = _sha(scorer_path.read_bytes())
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--policy",
            str(POLICY),
            "--gold",
            str(gold_path),
            "--predictions",
            str(prediction_path),
            "--scorer-manifest",
            str(MANIFEST),
            "--scorer-manifest-sha256",
            _frozen_manifest_sha(),
            "--source-root",
            str(ROOT),
            "--required-phase",
            "ALL",
            "--output-root",
            str(scorer_path.parent),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 1
    assert _sha(scorer_path.read_bytes()) == before
