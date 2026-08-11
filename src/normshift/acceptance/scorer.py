"""Exact, deterministic M1/M2 acceptance metric scorer.

This module recomputes only the frozen per-class metric gates.  It deliberately
cannot grant external acceptance: source provenance, blind-split custody,
exact-pass matrices, clean-room replay, and reviewer independence remain
separate evidence gates.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import pydantic
from pydantic import BaseModel, ValidationError

from normshift.acceptance.item_key import locator_source_ref
from normshift.acceptance.models import (
    AcceptanceResult,
    EvaluationFamily,
    EvaluationSource,
    EvaluationTask,
    ExactRatio,
    ExternalGate,
    GoldDocument,
    GoldItem,
    MetricGateResult,
    PredictionDocument,
    PredictionItem,
    ScorerManifest,
    SourceOrigin,
)
from normshift.evidence.hashing import canonical_json_bytes
from normshift.portable_ref import PortableRefError, resolve_declared_under_root
from normshift.strict_json import StrictJSONError, strict_loads

POLICY_ID: Literal["normshift-m1-m2-prereg-v1"] = "normshift-m1-m2-prereg-v1"
POLICY_SHA256 = "0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773"
SCORER_ID: Literal["normshift-m1-m2-exact-scorer-v1"] = "normshift-m1-m2-exact-scorer-v1"
SCORER_MANIFEST_REF = "acceptance/scorer_v1_manifest.json"
POLICY_REF = "acceptance/m1_m2_prereg_v1.json"
MAX_CONTROL_JSON_BYTES = 1024 * 1024
MAX_EVALUATION_JSON_BYTES = 64 * 1024 * 1024
REQUIRED_SCORER_FILES = frozenset(
    {
        POLICY_REF,
        "acceptance/README.md",
        "pyproject.toml",
        "schemas/acceptance_gold_v1.schema.json",
        "schemas/acceptance_predictions_v1.schema.json",
        "schemas/acceptance_result_v1.schema.json",
        "scripts/export_acceptance_schemas.py",
        "scripts/freeze_acceptance_scorer.py",
        "scripts/score_acceptance.py",
        "src/normshift/__init__.py",
        "src/normshift/acceptance/__init__.py",
        "src/normshift/acceptance/item_key.py",
        "src/normshift/acceptance/models.py",
        "src/normshift/acceptance/scorer.py",
        "src/normshift/evidence/__init__.py",
        "src/normshift/evidence/hashing.py",
        "src/normshift/io_safety.py",
        "src/normshift/portable_ref.py",
        "src/normshift/schemas/acceptance_gold_v1.schema.json",
        "src/normshift/schemas/acceptance_predictions_v1.schema.json",
        "src/normshift/schemas/acceptance_result_v1.schema.json",
        "src/normshift/strict_json.py",
        "tests/unit/test_acceptance_scorer.py",
        "uv.lock",
    }
)


class AcceptanceScoringError(ValueError):
    """Raised when frozen scorer inputs are missing, ambiguous, or inconsistent."""


@dataclass(frozen=True)
class GateSpec:
    gate_id: str
    phase: Literal["M1", "M2"]
    task: EvaluationTask
    family: EvaluationFamily | None
    class_name: str
    support_minimum: int
    real_support_minimum: int
    modal_distractors_minimum: int
    precision: str
    recall: str
    f1: str


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def bounded_read_regular_file(
    path: Path,
    label: str,
    *,
    max_bytes: int,
    expected_bytes: int | None = None,
) -> bytes:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise AcceptanceScoringError(f"{label} must be a regular non-symlink file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise AcceptanceScoringError(f"cannot open {label}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise AcceptanceScoringError(f"{label} is not a regular file")
        if before.st_size > max_bytes:
            raise AcceptanceScoringError(f"{label} exceeds {max_bytes} bytes")
        if expected_bytes is not None and before.st_size != expected_bytes:
            raise AcceptanceScoringError(f"{label} byte length differs before read")
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
        raise AcceptanceScoringError(f"cannot read {label}: {exc}") from exc
    finally:
        os.close(descriptor)
    if len(raw) > max_bytes:
        raise AcceptanceScoringError(f"{label} exceeds {max_bytes} bytes")
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(raw) != after.st_size:
        raise AcceptanceScoringError(f"{label} changed while being read")
    try:
        path_after = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise AcceptanceScoringError(f"cannot restat {label}: {exc}") from exc
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        not stat.S_ISREG(path_after.st_mode)
        or candidate.is_symlink()
        or path_identity != identity_after
    ):
        raise AcceptanceScoringError(f"{label} path identity changed while being read")
    return raw


def _strict_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = strict_loads(raw)
    except StrictJSONError as exc:
        raise AcceptanceScoringError(f"{label} is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AcceptanceScoringError(f"{label} must be a JSON object")
    return cast(dict[str, Any], value)


def _load_canonical_model[ModelT: BaseModel](
    path: Path,
    model: type[ModelT],
    label: str,
    *,
    max_bytes: int,
    expected_sha256: str | None = None,
) -> tuple[ModelT, bytes]:
    raw = bounded_read_regular_file(path, label, max_bytes=max_bytes)
    if expected_sha256 is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise AcceptanceScoringError(f"expected {label} SHA-256 is not lowercase hex")
        if _sha256(raw) != expected_sha256:
            raise AcceptanceScoringError(f"{label} differs from independent expected SHA-256")
    _strict_object(raw, label)
    try:
        parsed = model.model_validate_json(raw, strict=True)
    except ValidationError as exc:
        raise AcceptanceScoringError(f"{label} schema validation failed: {exc}") from exc
    canonical = canonical_json_bytes(parsed.model_dump(mode="json"))
    if raw != canonical:
        raise AcceptanceScoringError(f"{label} is not canonical UTF-8 JSON")
    return parsed, raw


def _manifest_source_root(manifest_path: Path, source_root: Path | None) -> Path:
    root = (
        Path(source_root).resolve()
        if source_root is not None
        else manifest_path.parent.parent.resolve()
    )
    if not root.is_dir():
        raise AcceptanceScoringError(f"source root is not a directory: {root}")
    try:
        expected_manifest, _ = resolve_declared_under_root(root, SCORER_MANIFEST_REF)
    except PortableRefError as exc:
        raise AcceptanceScoringError(
            f"cannot resolve scorer manifest under source root: {exc}"
        ) from exc
    if manifest_path.resolve() != expected_manifest:
        raise AcceptanceScoringError(
            f"scorer manifest must be the frozen {SCORER_MANIFEST_REF} under source root"
        )
    return root


def _load_and_verify_manifest(
    manifest_path: Path,
    source_root: Path | None,
    expected_sha256: str,
) -> tuple[ScorerManifest, bytes, Path]:
    root = _manifest_source_root(Path(manifest_path), source_root)
    manifest, raw = _load_canonical_model(
        Path(manifest_path),
        ScorerManifest,
        "scorer manifest",
        max_bytes=MAX_CONTROL_JSON_BYTES,
        expected_sha256=expected_sha256,
    )
    if manifest.policy_sha256 != POLICY_SHA256:
        raise AcceptanceScoringError("scorer manifest policy SHA-256 differs from frozen policy")
    observed_runtime = (
        platform.python_implementation(),
        f"{sys.version_info.major}.{sys.version_info.minor}",
        pydantic.__version__,
    )
    expected_runtime = (
        manifest.runtime.python_implementation,
        manifest.runtime.python_version,
        manifest.runtime.pydantic_version,
    )
    if observed_runtime != expected_runtime:
        raise AcceptanceScoringError(
            f"scorer runtime differs: expected={expected_runtime}, observed={observed_runtime}"
        )
    observed_paths = {record.path for record in manifest.files}
    if observed_paths != REQUIRED_SCORER_FILES:
        missing = sorted(REQUIRED_SCORER_FILES - observed_paths)
        extra = sorted(observed_paths - REQUIRED_SCORER_FILES)
        raise AcceptanceScoringError(
            "scorer manifest file inventory differs from authority; "
            f"missing={missing}, extra={extra}"
        )
    for record in manifest.files:
        try:
            path, _ = resolve_declared_under_root(root, record.path)
        except PortableRefError as exc:
            raise AcceptanceScoringError(f"scorer file {record.path!r} is unsafe: {exc}") from exc
        file_raw = bounded_read_regular_file(
            path,
            f"scorer file {record.path}",
            max_bytes=record.bytes,
            expected_bytes=record.bytes,
        )
        if len(file_raw) != record.bytes:
            raise AcceptanceScoringError(f"scorer file {record.path!r} byte length differs")
        if _sha256(file_raw) != record.sha256:
            raise AcceptanceScoringError(f"scorer file {record.path!r} SHA-256 differs")
    return manifest, raw, root


def _load_policy(path: Path, root: Path) -> dict[str, Any]:
    try:
        expected, _ = resolve_declared_under_root(root, POLICY_REF)
    except PortableRefError as exc:
        raise AcceptanceScoringError(f"cannot resolve frozen policy: {exc}") from exc
    if path.resolve() != expected:
        raise AcceptanceScoringError(f"policy must be the frozen {POLICY_REF} under source root")
    raw = bounded_read_regular_file(path, "policy", max_bytes=MAX_CONTROL_JSON_BYTES)
    if _sha256(raw) != POLICY_SHA256:
        raise AcceptanceScoringError("policy SHA-256 differs from frozen pre-registration")
    policy = _strict_object(raw, "policy")
    if (
        policy.get("policy_id") != POLICY_ID
        or policy.get("status") != "FROZEN_BEFORE_BLIND_EVALUATION"
    ):
        raise AcceptanceScoringError("policy identity/status differs from frozen pre-registration")
    return policy


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AcceptanceScoringError(f"frozen policy {label} must be an object")
    return cast(dict[str, Any], value)


def _records(value: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise AcceptanceScoringError(f"frozen policy {label} must be a non-empty array")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        result.append(_mapping(item, f"{label}[{index}]"))
    return result


def _text(record: dict[str, Any], key: str, label: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise AcceptanceScoringError(f"frozen policy {label}.{key} must be a string")
    return value


def _integer(record: dict[str, Any], key: str, label: str) -> int:
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AcceptanceScoringError(f"frozen policy {label}.{key} must be a non-negative integer")
    return value


def _family(value: str, label: str) -> EvaluationFamily:
    try:
        return EvaluationFamily(value)
    except ValueError as exc:
        raise AcceptanceScoringError(f"frozen policy {label} has unknown family {value!r}") from exc


def _gate_specs(policy: dict[str, Any]) -> list[GateSpec]:
    m1 = _mapping(policy.get("m1"), "m1")
    m2 = _mapping(policy.get("m2"), "m2")
    specs: list[GateSpec] = []

    for index, record in enumerate(
        _records(m1.get("requirement_extraction"), "m1.requirement_extraction")
    ):
        label = f"m1.requirement_extraction[{index}]"
        family = _family(_text(record, "family", label), label)
        minimum = _integer(record, "minimum_gold_positive_support", label)
        specs.append(
            GateSpec(
                f"m1.extraction.{family.value.lower()}.requirement",
                "M1",
                EvaluationTask.M1_REQUIREMENT_EXTRACTION,
                family,
                "REQUIREMENT",
                minimum,
                minimum,
                _integer(record, "minimum_labeled_modal_distractors", label),
                _text(record, "precision", label),
                _text(record, "recall", label),
                _text(record, "f1", label),
            )
        )

    for index, record in enumerate(
        _records(m1.get("region_classification"), "m1.region_classification")
    ):
        label = f"m1.region_classification[{index}]"
        family = _family(_text(record, "family", label), label)
        minimum = _integer(record, "minimum_support", label)
        class_name = _text(record, "class", label)
        specs.append(
            GateSpec(
                f"m1.region.{family.value.lower()}.{class_name.lower()}",
                "M1",
                EvaluationTask.M1_REGION,
                family,
                class_name,
                minimum,
                minimum,
                0,
                _text(record, "precision", label),
                _text(record, "recall", label),
                _text(record, "f1", label),
            )
        )

    for index, record in enumerate(
        _records(m1.get("modality_classification"), "m1.modality_classification")
    ):
        label = f"m1.modality_classification[{index}]"
        minimum = _integer(record, "minimum_actual_support", label)
        class_name = _text(record, "class", label)
        specs.append(
            GateSpec(
                f"m1.modality.{class_name.lower()}",
                "M1",
                EvaluationTask.M1_MODALITY,
                None,
                class_name,
                minimum,
                minimum,
                0,
                _text(record, "precision", label),
                _text(record, "recall", label),
                _text(record, "f1", label),
            )
        )

    for index, record in enumerate(_records(m1.get("family_detection"), "m1.family_detection")):
        label = f"m1.family_detection[{index}]"
        class_name = _text(record, "class", label)
        minimum = _integer(record, "minimum_actual_documents", label)
        specs.append(
            GateSpec(
                f"m1.family_detection.{class_name.lower()}",
                "M1",
                EvaluationTask.M1_FAMILY_DETECTION,
                None,
                class_name,
                minimum,
                minimum,
                0,
                _text(record, "precision", label),
                _text(record, "recall", label),
                _text(record, "f1", label),
            )
        )

    def append_m2(
        records: list[dict[str, Any]],
        *,
        section: str,
        task: EvaluationTask,
        shared_thresholds: dict[str, Any] | None = None,
    ) -> None:
        for index, record in enumerate(records):
            label = f"m2.{section}[{index}]"
            class_name = _text(record, "class", label)
            thresholds = shared_thresholds if shared_thresholds is not None else record
            specs.append(
                GateSpec(
                    f"m2.{section}.{class_name.lower()}",
                    "M2",
                    task,
                    None,
                    class_name,
                    _integer(record, "minimum_support", label),
                    _integer(record, "minimum_real_support", label),
                    0,
                    _text(thresholds, "precision", label),
                    _text(thresholds, "recall", label),
                    _text(thresholds, "f1", label),
                )
            )

    append_m2(
        _records(m2.get("identity"), "m2.identity"),
        section="identity",
        task=EvaluationTask.M2_IDENTITY,
    )
    append_m2(
        _records(m2.get("relations"), "m2.relations"),
        section="relations",
        task=EvaluationTask.M2_RELATION,
    )
    append_m2(
        _records(m2.get("change_classes"), "m2.change_classes"),
        section="change",
        task=EvaluationTask.M2_CHANGE,
        shared_thresholds=_mapping(m2.get("change_class_thresholds"), "m2.change_class_thresholds"),
    )
    append_m2(
        _records(m2.get("definition_and_xref_classes"), "m2.definition_and_xref_classes"),
        section="definition_xref",
        task=EvaluationTask.M2_DEFINITION_XREF,
        shared_thresholds=_mapping(
            m2.get("definition_and_xref_thresholds"), "m2.definition_and_xref_thresholds"
        ),
    )
    append_m2(
        _records(m2.get("ambiguity_routing"), "m2.ambiguity_routing"),
        section="ambiguity_routing",
        task=EvaluationTask.M2_AMBIGUITY_ROUTING,
    )
    return specs


def _allowed_classes(specs: list[GateSpec]) -> dict[EvaluationTask, set[str]]:
    allowed = {task: {"NONE"} for task in EvaluationTask}
    for spec in specs:
        allowed[spec.task].add(spec.class_name)
    return allowed


def _slot_classes(specs: list[GateSpec]) -> dict[EvaluationTask, dict[str, set[str]]]:
    slots: dict[EvaluationTask, dict[str, set[str]]] = {
        EvaluationTask.M1_REQUIREMENT_EXTRACTION: {"requirement": {"NONE", "REQUIREMENT"}},
        EvaluationTask.M1_MODALITY: {
            "modality": {"NONE", "MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT", "MAY"}
        },
        EvaluationTask.M1_REGION: {"region": {"NONE", "NORMATIVE", "INFORMATIVE", "EXCLUDED"}},
        EvaluationTask.M1_FAMILY_DETECTION: {"family": {"NONE", "RFC", "W3C_TR", "WHATWG"}},
        EvaluationTask.M2_IDENTITY: {"identity": {"NONE", "SAME_LINEAGE", "DIFFERENT_LINEAGE"}},
        EvaluationTask.M2_RELATION: {
            "relation": {
                "NONE",
                "CONTINUES",
                "SPLIT_INTO",
                "MERGED_FROM",
                "ADDED",
                "REMOVED",
                "AMBIGUOUS",
            }
        },
        EvaluationTask.M2_CHANGE: {
            "structural_form": {
                "NONE",
                "MOVE_ONLY",
                "REWRITE_ONLY",
                "MOVED_AND_REWRITTEN",
            },
            "actor": {"NONE", "ACTOR_CHANGED"},
            "action": {"NONE", "ACTION_CHANGED"},
            "object": {"NONE", "OBJECT_CHANGED"},
            "scope": {"NONE", "SCOPE_CHANGED"},
            "modality": {"NONE", "MODALITY_CHANGED"},
            "polarity": {"NONE", "POLARITY_CHANGED"},
            "condition": {"NONE", "CONDITION_ADDED", "CONDITION_REMOVED"},
            "exception": {"NONE", "EXCEPTION_ADDED", "EXCEPTION_REMOVED"},
        },
        EvaluationTask.M2_DEFINITION_XREF: {
            "definition": {
                "NONE",
                "DEFINITION_ADDED",
                "DEFINITION_CHANGED",
                "DEFINITION_REMOVED",
            },
            "definition_reference": {"NONE", "REFERENCES_DEFINITION"},
            "cross_reference": {"NONE", "CROSS_REFERENCE"},
            "indirect_impact": {"NONE", "INDIRECT_IMPACT"},
        },
        EvaluationTask.M2_AMBIGUITY_ROUTING: {
            "routing": {"NONE", "ROUTE_AMBIGUOUS", "ROUTE_CONFIDENT"}
        },
    }
    allowed = _allowed_classes(specs)
    for task, task_slots in slots.items():
        if set().union(*task_slots.values()) != allowed[task]:
            raise AcceptanceScoringError(
                f"frozen slot ontology differs from policy classes for {task.value}"
            )
    return slots


def _source_index(gold: GoldDocument) -> dict[str, EvaluationSource]:
    return {source.source_id: source for source in gold.sources}


def _item_family(item: GoldItem, sources: dict[str, EvaluationSource]) -> EvaluationFamily:
    families = {sources[source_id].family for source_id in item.source_ids}
    if len(families) != 1:
        raise AcceptanceScoringError(
            f"gold item {item.label_id!r} crosses source families; "
            "family-scoped metrics are ambiguous"
        )
    return next(iter(families))


def _item_is_actual(item: GoldItem, sources: dict[str, EvaluationSource]) -> bool:
    return all(sources[source_id].origin == SourceOrigin.ACTUAL for source_id in item.source_ids)


def _threshold_hundredths(value: str) -> int:
    if len(value) != 4 or value[1] != "." or not (value[0] + value[2:]).isdigit():
        raise AcceptanceScoringError(f"invalid frozen threshold {value!r}")
    hundredths = int(value[0]) * 100 + int(value[2:])
    if hundredths > 100:
        raise AcceptanceScoringError(f"frozen threshold exceeds 1.00: {value!r}")
    return hundredths


def _ratio(numerator: int, denominator: int, threshold: str) -> ExactRatio:
    required = _threshold_hundredths(threshold)
    passed = required == 0 if denominator == 0 else numerator * 100 >= required * denominator
    return ExactRatio(
        numerator=numerator,
        denominator=denominator,
        threshold=threshold,
        passed=passed,
    )


def _validate_items(
    gold: GoldDocument,
    predictions: PredictionDocument,
    specs: list[GateSpec],
    sources: dict[str, EvaluationSource],
) -> tuple[dict[tuple[EvaluationTask, str], str], list[PredictionItem]]:
    allowed = _allowed_classes(specs)
    slots = _slot_classes(specs)
    gold_keys = {(item.task, item.item_key) for item in gold.items}
    prediction_map = {
        (prediction.task, prediction.item_key): prediction.predicted_class
        for prediction in predictions.predictions
    }
    source_by_sha = {source.raw_sha256: source for source in sources.values()}
    extras: list[PredictionItem] = []
    for prediction in predictions.predictions:
        slot_classes = slots[prediction.task].get(prediction.evaluation_slot)
        if slot_classes is None or prediction.predicted_class not in slot_classes:
            raise AcceptanceScoringError(
                "prediction class/evaluation_slot combination is outside the frozen ontology"
            )
        prediction_sources = [source_by_sha.get(value) for value in prediction.source_sha256s]
        if any(source is None for source in prediction_sources):
            raise AcceptanceScoringError("prediction references a source outside frozen gold")
        if prediction.task.value.startswith("M1_") and len(prediction_sources) != 1:
            raise AcceptanceScoringError(
                "M1 prediction evidence must bind exactly one source document"
            )
        for source, locator in zip(prediction_sources, prediction.portable_locators, strict=True):
            if source is None or locator_source_ref(locator) != source.portable_source_ref:
                raise AcceptanceScoringError(
                    "prediction locator differs from its frozen source ref"
                )
        if (prediction.task, prediction.item_key) not in gold_keys:
            if prediction.predicted_class == "NONE":
                raise AcceptanceScoringError("unexpected NONE prediction is not a valid output")
            extras.append(prediction)
    family_detection_sources: set[str] = set()
    for item in gold.items:
        if item.task.value.startswith("M1_") and len(item.source_ids) != 1:
            raise AcceptanceScoringError("M1 gold evidence must bind exactly one source document")
        slot_classes = slots[item.task].get(item.evaluation_slot)
        if slot_classes is None or item.expected_class not in slot_classes:
            raise AcceptanceScoringError(
                f"gold item {item.label_id!r} has an invalid class/evaluation_slot"
            )
        predicted = prediction_map.get((item.task, item.item_key), "NONE")
        if predicted not in allowed[item.task] or predicted not in slot_classes:
            raise AcceptanceScoringError(
                f"prediction for {item.label_id!r} has class {predicted!r} "
                f"invalid for {item.task.value}"
            )
        if item.task == EvaluationTask.M1_FAMILY_DETECTION:
            if len(item.source_ids) != 1:
                raise AcceptanceScoringError(
                    "family-detection gold items must bind exactly one source"
                )
            source_id = item.source_ids[0]
            if source_id in family_detection_sources:
                raise AcceptanceScoringError(
                    "family-detection gold must contain exactly one item per source document"
                )
            family_detection_sources.add(source_id)
            expected_family = sources[source_id].family.value
            if item.expected_class != expected_family:
                raise AcceptanceScoringError(
                    "family-detection gold class differs from its source family identity"
                )
    return prediction_map, extras


def _metric_gate(
    spec: GateSpec,
    items: list[GoldItem],
    prediction_map: dict[tuple[EvaluationTask, str], str],
    extra_predictions: list[PredictionItem],
    sources: dict[str, EvaluationSource],
) -> MetricGateResult:
    candidates = [item for item in items if item.task == spec.task]
    if spec.family is not None:
        candidates = [item for item in candidates if _item_family(item, sources) == spec.family]
    tp = sum(
        item.expected_class == spec.class_name
        and prediction_map.get((item.task, item.item_key), "NONE") == spec.class_name
        for item in candidates
    )
    fp = sum(
        item.expected_class != spec.class_name
        and prediction_map.get((item.task, item.item_key), "NONE") == spec.class_name
        for item in candidates
    )
    source_by_sha = {source.raw_sha256: source for source in sources.values()}
    for prediction in extra_predictions:
        if prediction.task != spec.task or prediction.predicted_class != spec.class_name:
            continue
        if (
            spec.family is None
            or source_by_sha[prediction.source_sha256s[0]].family == spec.family
        ):
            fp += 1
    fn = sum(
        item.expected_class == spec.class_name
        and prediction_map.get((item.task, item.item_key), "NONE") != spec.class_name
        for item in candidates
    )
    support = tp + fn
    declared_actual_support = sum(
        item.expected_class == spec.class_name and _item_is_actual(item, sources)
        for item in candidates
    )
    modal_distractors = sum(
        item.modal_distractor and _item_is_actual(item, sources) for item in candidates
    )
    precision = _ratio(tp, tp + fp, spec.precision)
    recall = _ratio(tp, tp + fn, spec.recall)
    f1 = _ratio(2 * tp, 2 * tp + fp + fn, spec.f1)
    reasons: list[str] = []
    if support < spec.support_minimum:
        reasons.append("minimum support not met")
    if declared_actual_support < spec.real_support_minimum:
        reasons.append("minimum declared actual-source support not met")
    if modal_distractors < spec.modal_distractors_minimum:
        reasons.append("minimum declared actual modal-distractor support not met")
    if not precision.passed:
        reasons.append("precision threshold not met")
    if not recall.passed:
        reasons.append("recall threshold not met")
    if not f1.passed:
        reasons.append("f1 threshold not met")
    return MetricGateResult(
        gate_id=spec.gate_id,
        phase=spec.phase,
        task=spec.task,
        family=spec.family,
        class_name=spec.class_name,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        support_observed=support,
        support_minimum=spec.support_minimum,
        declared_actual_support_observed=declared_actual_support,
        declared_actual_support_minimum=spec.real_support_minimum,
        modal_distractors_observed=modal_distractors,
        modal_distractors_minimum=spec.modal_distractors_minimum,
        support_evidence_scope="DECLARED_GOLD_METADATA_UNVERIFIED",
        precision=precision,
        recall=recall,
        f1=f1,
        metric_thresholds_passed=not reasons,
        reasons=reasons,
    )


def score_acceptance(
    *,
    policy_path: Path,
    gold_path: Path,
    predictions_path: Path,
    scorer_manifest_path: Path,
    expected_scorer_manifest_sha256: str,
    source_root: Path | None = None,
) -> AcceptanceResult:
    """Recompute frozen per-class metrics without revealing or granting audit authority."""
    manifest, manifest_raw, root = _load_and_verify_manifest(
        scorer_manifest_path,
        source_root,
        expected_scorer_manifest_sha256,
    )
    policy = _load_policy(policy_path, root)
    gold, gold_raw = _load_canonical_model(
        gold_path, GoldDocument, "gold", max_bytes=MAX_EVALUATION_JSON_BYTES
    )
    predictions, prediction_raw = _load_canonical_model(
        predictions_path,
        PredictionDocument,
        "predictions",
        max_bytes=MAX_EVALUATION_JSON_BYTES,
    )
    manifest_sha256 = _sha256(manifest_raw)
    gold_sha256 = _sha256(gold_raw)
    if manifest.scorer_id != SCORER_ID:
        raise AcceptanceScoringError("scorer manifest identity differs from frozen scorer")
    if gold.policy_sha256 != POLICY_SHA256 or predictions.policy_sha256 != POLICY_SHA256:
        raise AcceptanceScoringError("gold/predictions do not bind the frozen policy")
    if gold.scorer_manifest_sha256 != manifest_sha256:
        raise AcceptanceScoringError("gold does not bind the supplied scorer manifest")
    if predictions.scorer_manifest_sha256 != manifest_sha256:
        raise AcceptanceScoringError("predictions do not bind the supplied scorer manifest")
    if predictions.gold_sha256 != gold_sha256:
        raise AcceptanceScoringError("predictions do not bind the exact gold bytes")
    if predictions.generated_at_utc < gold.frozen_at_utc:
        raise AcceptanceScoringError("predictions timestamp precedes gold freeze")
    if (predictions.dataset_id, predictions.dataset_version) != (
        gold.dataset_id,
        gold.dataset_version,
    ):
        raise AcceptanceScoringError("gold and predictions dataset identity differs")

    specs = _gate_specs(policy)
    sources = _source_index(gold)
    prediction_map, extra_predictions = _validate_items(gold, predictions, specs, sources)
    metric_gates = [
        _metric_gate(spec, gold.items, prediction_map, extra_predictions, sources) for spec in specs
    ]
    m1_metrics = all(item.metric_thresholds_passed for item in metric_gates if item.phase == "M1")
    m2_metrics = all(item.metric_thresholds_passed for item in metric_gates if item.phase == "M2")
    return AcceptanceResult(
        kind="normshift-acceptance-metric-result",
        schema_version="1.0.0",
        policy_id=POLICY_ID,
        policy_sha256=POLICY_SHA256,
        scorer_manifest_sha256=manifest_sha256,
        gold_sha256=gold_sha256,
        predictions_sha256=_sha256(prediction_raw),
        dataset_id=gold.dataset_id,
        dataset_version=gold.dataset_version,
        split=gold.split,
        source_manifest_sha256=gold.source_manifest_sha256,
        split_manifest_sha256=gold.split_manifest_sha256,
        decision_ledger_sha256=gold.decision_ledger_sha256,
        candidate=predictions.candidate,
        metric_gates=metric_gates,
        m1_metric_thresholds_passed=m1_metrics,
        m2_metric_thresholds_passed=m2_metrics,
        all_metric_thresholds_passed=m1_metrics and m2_metrics,
        external_gates_evaluated=False,
        unverified_external_gates=list(ExternalGate),
        external_acceptance_granted=False,
        evaluation_scope="DECLARED_SUPPORT_METRICS_ONLY",
    )
