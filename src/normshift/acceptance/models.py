"""Strict models for blind M1/M2 gold, predictions, and metric results."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from normshift.acceptance.item_key import (
    acceptance_item_key,
    locator_source_ref,
    validate_portable_locator,
    validate_portable_source_ref,
)

SHA256_PATTERN = r"^[0-9a-f]{64}$"
GIT_OID_PATTERN = r"^[0-9a-f]{40}$"
UTC_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
CLASS_PATTERN = r"^[A-Z][A-Z0-9_]*$"
ReviewerId = Annotated[str, Field(pattern=ID_PATTERN)]


def _semantic_utc(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("timestamp must be a real UTC second in YYYY-MM-DDTHH:MM:SSZ") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError("timestamp is not canonical UTC")
    return value


UtcSecond = Annotated[str, Field(pattern=UTC_PATTERN), AfterValidator(_semantic_utc)]
PortableLocator = Annotated[
    str, Field(min_length=1, max_length=1024), AfterValidator(validate_portable_locator)
]
PortableSourceRef = Annotated[
    str, Field(min_length=1, max_length=768), AfterValidator(validate_portable_source_ref)
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvaluationTask(StrEnum):
    M1_REQUIREMENT_EXTRACTION = "M1_REQUIREMENT_EXTRACTION"
    M1_MODALITY = "M1_MODALITY"
    M1_REGION = "M1_REGION"
    M1_FAMILY_DETECTION = "M1_FAMILY_DETECTION"
    M2_IDENTITY = "M2_IDENTITY"
    M2_RELATION = "M2_RELATION"
    M2_CHANGE = "M2_CHANGE"
    M2_DEFINITION_XREF = "M2_DEFINITION_XREF"
    M2_AMBIGUITY_ROUTING = "M2_AMBIGUITY_ROUTING"


class EvaluationFamily(StrEnum):
    RFC = "RFC"
    W3C_TR = "W3C_TR"
    WHATWG = "WHATWG"


class SourceOrigin(StrEnum):
    ACTUAL = "ACTUAL"
    SYNTHETIC = "SYNTHETIC"


class DatasetSplit(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    BLIND_HOLDOUT = "BLIND_HOLDOUT"


class DecisionOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    ABSTAINED = "ABSTAINED"
    CONFLICT = "CONFLICT"


class ExternalGate(StrEnum):
    SOURCE_MANIFEST_PROVENANCE = "SOURCE_MANIFEST_PROVENANCE"
    BLIND_SPLIT_CUSTODY = "BLIND_SPLIT_CUSTODY"
    DECISION_LEDGER_AND_REVIEWER_AUTHORITY = "DECISION_LEDGER_AND_REVIEWER_AUTHORITY"
    ACTUAL_SOURCE_DOCUMENT_COVERAGE = "ACTUAL_SOURCE_DOCUMENT_COVERAGE"
    CONSECUTIVE_LINEAGE_COVERAGE = "CONSECUTIVE_LINEAGE_COVERAGE"
    EXACT_PASS_MATRICES = "EXACT_PASS_MATRICES"
    CLEAN_ROOM_REPLAY = "CLEAN_ROOM_REPLAY"
    EXTERNAL_AUDIT = "EXTERNAL_AUDIT"


class EvaluationSource(StrictModel):
    source_id: str = Field(pattern=ID_PATTERN)
    family: EvaluationFamily
    origin: SourceOrigin
    raw_sha256: str = Field(pattern=SHA256_PATTERN)
    standard_id: str = Field(min_length=1, max_length=256)
    version: str = Field(min_length=1, max_length=256)
    chain_id: str = Field(pattern=ID_PATTERN)
    lineage_sequence: int = Field(ge=1)
    portable_source_ref: PortableSourceRef


class ReviewEnvelope(StrictModel):
    labeler_ids: list[ReviewerId] = Field(min_length=2, max_length=16)
    adjudicator_id: str = Field(pattern=ID_PATTERN)
    predictions_viewed_before_freeze: Literal[False]
    labels_hash_frozen: Literal[True]
    decided_at_utc: UtcSecond

    @model_validator(mode="after")
    def validate_independence(self) -> ReviewEnvelope:
        if len(set(self.labeler_ids)) != len(self.labeler_ids):
            raise ValueError("labeler_ids must be unique")
        if self.adjudicator_id in self.labeler_ids:
            raise ValueError("adjudicator_id must be separate from labelers")
        return self


class GoldItem(StrictModel):
    item_key: str = Field(pattern=SHA256_PATTERN)
    label_id: str = Field(pattern=ID_PATTERN)
    decision_id: str = Field(pattern=ID_PATTERN)
    task: EvaluationTask
    evaluation_slot: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    expected_class: str = Field(pattern=CLASS_PATTERN)
    source_ids: list[str] = Field(min_length=1, max_length=4)
    portable_locators: list[PortableLocator] = Field(min_length=1, max_length=4)
    evidence_sha256: str = Field(pattern=SHA256_PATTERN)
    modal_distractor: bool = False

    @model_validator(mode="after")
    def validate_parallel_evidence(self) -> GoldItem:
        if len(self.source_ids) != len(self.portable_locators):
            raise ValueError("source_ids and portable_locators must have equal length")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("source_ids must be unique within an item")
        if self.modal_distractor and (
            self.task != EvaluationTask.M1_REQUIREMENT_EXTRACTION or self.expected_class != "NONE"
        ):
            raise ValueError("modal_distractor is valid only for M1 extraction NONE items")
        return self


class LabelDecision(StrictModel):
    decision_id: str = Field(pattern=ID_PATTERN)
    label_id: str = Field(pattern=ID_PATTERN)
    item_key: str = Field(pattern=SHA256_PATTERN)
    task: EvaluationTask
    evaluation_slot: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    source_ids: list[str] = Field(min_length=1, max_length=4)
    portable_locators: list[PortableLocator] = Field(min_length=1, max_length=4)
    evidence_sha256: str = Field(pattern=SHA256_PATTERN)
    decided_class: str | None = Field(default=None, pattern=CLASS_PATTERN)
    reviewer_ids: list[ReviewerId] = Field(min_length=2, max_length=16)
    adjudicator_id: str = Field(pattern=ID_PATTERN)
    decision: DecisionOutcome
    reason: str = Field(min_length=1, max_length=4096)
    decided_at_utc: UtcSecond

    @model_validator(mode="after")
    def validate_decision(self) -> LabelDecision:
        if len(self.source_ids) != len(self.portable_locators):
            raise ValueError("decision evidence lists must have equal length")
        if len(set(self.reviewer_ids)) != len(self.reviewer_ids):
            raise ValueError("decision reviewer_ids must be unique")
        if self.adjudicator_id in self.reviewer_ids:
            raise ValueError("decision adjudicator must be separate from reviewers")
        if self.decision == DecisionOutcome.ACCEPTED and self.decided_class is None:
            raise ValueError("accepted decision requires decided_class")
        if self.decision != DecisionOutcome.ACCEPTED and self.decided_class is not None:
            raise ValueError("abstained/conflict decision must not assert a class")
        return self


class GoldDocument(StrictModel):
    kind: Literal["normshift-acceptance-gold"]
    schema_version: Literal["1.0.0"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: str = Field(pattern=SHA256_PATTERN)
    scorer_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    dataset_id: str = Field(pattern=ID_PATTERN)
    dataset_version: str = Field(pattern=ID_PATTERN)
    split: DatasetSplit
    source_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    split_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    decision_ledger_sha256: str = Field(pattern=SHA256_PATTERN)
    frozen_at_utc: UtcSecond
    review: ReviewEnvelope
    sources: list[EvaluationSource] = Field(min_length=1, max_length=1000)
    items: list[GoldItem] = Field(min_length=1, max_length=250_000)
    decisions: list[LabelDecision] = Field(min_length=1, max_length=300_000)

    @model_validator(mode="after")
    def validate_graph(self) -> GoldDocument:
        if self.review.decided_at_utc > self.frozen_at_utc:
            raise ValueError("review decision timestamp is after gold freeze")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source_id values must be unique")
        known_sources = set(source_ids)
        source_by_id = {source.source_id: source for source in self.sources}
        portable_refs = [source.portable_source_ref for source in self.sources]
        if len(portable_refs) != len(set(portable_refs)):
            raise ValueError("source portable refs must be unique")
        folded_refs = [ref.casefold() for ref in portable_refs]
        if len(folded_refs) != len(set(folded_refs)):
            raise ValueError("source portable refs have a cross-platform case alias")
        raw_hashes = [source.raw_sha256 for source in self.sources]
        if len(raw_hashes) != len(set(raw_hashes)):
            raise ValueError("source raw_sha256 values must be unique")
        version_ids = [
            (source.family, source.standard_id, source.version) for source in self.sources
        ]
        if len(version_ids) != len(set(version_ids)):
            raise ValueError("source family/standard/version identities must be unique")
        sequence_ids = [
            (source.family, source.chain_id, source.lineage_sequence) for source in self.sources
        ]
        if len(sequence_ids) != len(set(sequence_ids)):
            raise ValueError("source lineage sequence identities must be unique")

        item_keys = [(item.task, item.item_key) for item in self.items]
        if len(item_keys) != len(set(item_keys)):
            raise ValueError("(task, item_key) values must be unique")
        label_ids = [item.label_id for item in self.items]
        if len(label_ids) != len(set(label_ids)):
            raise ValueError("gold label_id values must be unique")

        decision_ids = [decision.decision_id for decision in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("decision_id values must be unique")
        decision_by_id = {decision.decision_id: decision for decision in self.decisions}
        decision_label_ids = [decision.label_id for decision in self.decisions]
        if len(decision_label_ids) != len(set(decision_label_ids)):
            raise ValueError("decision label_id values must be unique")
        accepted_decisions = {
            decision.decision_id
            for decision in self.decisions
            if decision.decision == DecisionOutcome.ACCEPTED
        }
        if accepted_decisions != {item.decision_id for item in self.items}:
            raise ValueError("accepted decisions and scorable gold items must match exactly")

        for item in self.items:
            if not set(item.source_ids) <= known_sources:
                raise ValueError(f"item {item.label_id} references an unknown source")
            expected_key = acceptance_item_key(
                task=item.task.value,
                evaluation_slot=item.evaluation_slot,
                source_sha256s=[source_by_id[item_id].raw_sha256 for item_id in item.source_ids],
                portable_locators=item.portable_locators,
            )
            if item.item_key != expected_key:
                raise ValueError(f"item {item.label_id} has a non-canonical item_key")
            for source_id, locator in zip(item.source_ids, item.portable_locators, strict=True):
                if locator_source_ref(locator) != source_by_id[source_id].portable_source_ref:
                    raise ValueError(f"item {item.label_id} locator differs from source ref")
            decision = decision_by_id.get(item.decision_id)
            if decision is None or decision.decision != DecisionOutcome.ACCEPTED:
                raise ValueError(f"item {item.label_id} lacks an accepted decision")
            expected = (
                decision.label_id,
                decision.item_key,
                decision.task,
                decision.evaluation_slot,
                decision.source_ids,
                decision.portable_locators,
                decision.evidence_sha256,
                decision.decided_class,
            )
            observed = (
                item.label_id,
                item.item_key,
                item.task,
                item.evaluation_slot,
                item.source_ids,
                item.portable_locators,
                item.evidence_sha256,
                item.expected_class,
            )
            if observed != expected:
                raise ValueError(f"item {item.label_id} differs from its accepted decision")
            if set(decision.reviewer_ids) != set(self.review.labeler_ids):
                raise ValueError(f"item {item.label_id} decision reviewer set differs")
            if decision.adjudicator_id != self.review.adjudicator_id:
                raise ValueError(f"item {item.label_id} decision adjudicator differs")
        for decision in self.decisions:
            if not set(decision.source_ids) <= known_sources:
                raise ValueError(f"decision {decision.decision_id} references an unknown source")
            if set(decision.reviewer_ids) != set(self.review.labeler_ids):
                raise ValueError(f"decision {decision.decision_id} reviewer set differs")
            if decision.adjudicator_id != self.review.adjudicator_id:
                raise ValueError(f"decision {decision.decision_id} adjudicator differs")
            if decision.decided_at_utc > self.frozen_at_utc:
                raise ValueError(f"decision {decision.decision_id} is after gold freeze")
            for source_id, locator in zip(
                decision.source_ids, decision.portable_locators, strict=True
            ):
                if locator_source_ref(locator) != source_by_id[source_id].portable_source_ref:
                    raise ValueError(
                        f"decision {decision.decision_id} locator differs from source ref"
                    )
        return self


class CandidateBinding(StrictModel):
    commit: str = Field(pattern=GIT_OID_PATTERN)
    tree: str = Field(pattern=GIT_OID_PATTERN)
    wheel_sha256: str = Field(pattern=SHA256_PATTERN)
    sdist_sha256: str = Field(pattern=SHA256_PATTERN)
    source_zip_sha256: str = Field(pattern=SHA256_PATTERN)
    bundle_sha256: str = Field(pattern=SHA256_PATTERN)


class PredictionItem(StrictModel):
    item_key: str = Field(pattern=SHA256_PATTERN)
    task: EvaluationTask
    evaluation_slot: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    source_sha256s: list[str] = Field(min_length=1, max_length=4)
    portable_locators: list[PortableLocator] = Field(min_length=1, max_length=4)
    predicted_class: str = Field(pattern=CLASS_PATTERN)

    @model_validator(mode="after")
    def validate_key(self) -> PredictionItem:
        if len(self.source_sha256s) != len(self.portable_locators):
            raise ValueError("prediction evidence lists must have equal length")
        for source_sha256 in self.source_sha256s:
            if not re.fullmatch(SHA256_PATTERN, source_sha256):
                raise ValueError("prediction source_sha256 is invalid")
        expected = acceptance_item_key(
            task=self.task.value,
            evaluation_slot=self.evaluation_slot,
            source_sha256s=self.source_sha256s,
            portable_locators=self.portable_locators,
        )
        if self.item_key != expected:
            raise ValueError("prediction item_key is not canonical for its evidence")
        return self


class PredictionDocument(StrictModel):
    kind: Literal["normshift-acceptance-predictions"]
    schema_version: Literal["1.0.0"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: str = Field(pattern=SHA256_PATTERN)
    scorer_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    dataset_id: str = Field(pattern=ID_PATTERN)
    dataset_version: str = Field(pattern=ID_PATTERN)
    gold_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate: CandidateBinding
    generated_at_utc: UtcSecond
    predictions: list[PredictionItem] = Field(max_length=300_000)

    @model_validator(mode="after")
    def validate_unique_predictions(self) -> PredictionDocument:
        keys = [(item.task, item.item_key) for item in self.predictions]
        if len(keys) != len(set(keys)):
            raise ValueError("(task, item_key) prediction values must be unique")
        return self


class ExactRatio(StrictModel):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    threshold: str = Field(pattern=r"^(0|1)\.[0-9]{2}$")
    passed: bool

    @model_validator(mode="after")
    def validate_exact_comparison(self) -> ExactRatio:
        required = int(self.threshold[0]) * 100 + int(self.threshold[2:])
        expected = (
            required == 0
            if self.denominator == 0
            else self.numerator * 100 >= required * self.denominator
        )
        if self.passed != expected:
            raise ValueError("ratio passed flag differs from exact cross-multiplication")
        return self


class MetricGateResult(StrictModel):
    gate_id: str = Field(pattern=ID_PATTERN)
    phase: Literal["M1", "M2"]
    task: EvaluationTask
    family: EvaluationFamily | None
    class_name: str = Field(pattern=CLASS_PATTERN)
    true_positives: int = Field(ge=0)
    false_positives: int = Field(ge=0)
    false_negatives: int = Field(ge=0)
    support_observed: int = Field(ge=0)
    support_minimum: int = Field(ge=0)
    declared_actual_support_observed: int = Field(ge=0)
    declared_actual_support_minimum: int = Field(ge=0)
    modal_distractors_observed: int = Field(ge=0)
    modal_distractors_minimum: int = Field(ge=0)
    support_evidence_scope: Literal["DECLARED_GOLD_METADATA_UNVERIFIED"]
    precision: ExactRatio
    recall: ExactRatio
    f1: ExactRatio
    metric_thresholds_passed: bool
    reasons: list[str]

    @model_validator(mode="after")
    def validate_confusion_and_gate(self) -> MetricGateResult:
        if self.support_observed != self.true_positives + self.false_negatives:
            raise ValueError("support must equal TP+FN")
        if self.declared_actual_support_observed > self.support_observed:
            raise ValueError("declared actual support cannot exceed total support")
        expected_ratios = (
            (self.precision, self.true_positives, self.true_positives + self.false_positives),
            (self.recall, self.true_positives, self.true_positives + self.false_negatives),
            (
                self.f1,
                2 * self.true_positives,
                2 * self.true_positives + self.false_positives + self.false_negatives,
            ),
        )
        if any(
            ratio.numerator != numerator or ratio.denominator != denominator
            for ratio, numerator, denominator in expected_ratios
        ):
            raise ValueError("ratio numerators/denominators differ from confusion counts")
        expected_reasons: list[str] = []
        if self.support_observed < self.support_minimum:
            expected_reasons.append("minimum support not met")
        if self.declared_actual_support_observed < self.declared_actual_support_minimum:
            expected_reasons.append("minimum declared actual-source support not met")
        if self.modal_distractors_observed < self.modal_distractors_minimum:
            expected_reasons.append("minimum declared actual modal-distractor support not met")
        if not self.precision.passed:
            expected_reasons.append("precision threshold not met")
        if not self.recall.passed:
            expected_reasons.append("recall threshold not met")
        if not self.f1.passed:
            expected_reasons.append("f1 threshold not met")
        if self.reasons != expected_reasons:
            raise ValueError("metric gate reasons differ from recomputed failures")
        if self.metric_thresholds_passed != (not expected_reasons):
            raise ValueError("metric gate aggregate differs from recomputed failures")
        return self


class AcceptanceResult(StrictModel):
    kind: Literal["normshift-acceptance-metric-result"]
    schema_version: Literal["1.0.0"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: str = Field(pattern=SHA256_PATTERN)
    scorer_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    gold_sha256: str = Field(pattern=SHA256_PATTERN)
    predictions_sha256: str = Field(pattern=SHA256_PATTERN)
    dataset_id: str = Field(pattern=ID_PATTERN)
    dataset_version: str = Field(pattern=ID_PATTERN)
    split: DatasetSplit
    source_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    split_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    decision_ledger_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate: CandidateBinding
    metric_gates: list[MetricGateResult] = Field(min_length=1)
    m1_metric_thresholds_passed: bool
    m2_metric_thresholds_passed: bool
    all_metric_thresholds_passed: bool
    external_gates_evaluated: Literal[False]
    unverified_external_gates: list[ExternalGate] = Field(min_length=1)
    external_acceptance_granted: Literal[False]
    evaluation_scope: Literal["DECLARED_SUPPORT_METRICS_ONLY"]

    @model_validator(mode="after")
    def validate_aggregates(self) -> AcceptanceResult:
        gate_ids = [gate.gate_id for gate in self.metric_gates]
        if len(gate_ids) != len(set(gate_ids)):
            raise ValueError("metric gate IDs must be unique")
        m1 = all(gate.metric_thresholds_passed for gate in self.metric_gates if gate.phase == "M1")
        m2 = all(gate.metric_thresholds_passed for gate in self.metric_gates if gate.phase == "M2")
        if self.m1_metric_thresholds_passed != m1:
            raise ValueError("M1 metric aggregate differs from gates")
        if self.m2_metric_thresholds_passed != m2:
            raise ValueError("M2 metric aggregate differs from gates")
        if self.all_metric_thresholds_passed != (m1 and m2):
            raise ValueError("combined metric aggregate differs from gates")
        if len(self.unverified_external_gates) != len(set(self.unverified_external_gates)):
            raise ValueError("unverified external gates must be unique")
        if set(self.unverified_external_gates) != set(ExternalGate):
            raise ValueError("result must retain every external gate as unverified")
        return self


class ScorerFileRecord(StrictModel):
    path: str = Field(min_length=1, max_length=1024)
    sha256: str = Field(pattern=SHA256_PATTERN)
    bytes: int = Field(ge=1, le=8 * 1024 * 1024)

    @model_validator(mode="after")
    def validate_path(self) -> ScorerFileRecord:
        ref = self.path
        if "\\" in ref or "\x00" in ref or ref.startswith(("/", "file:")):
            raise ValueError("scorer file path must be a relative POSIX path")
        path = PurePosixPath(ref)
        if any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("scorer file path contains an unsafe segment")
        if path.parts and ":" in path.parts[0]:
            raise ValueError("scorer file path must not be drive-qualified")
        if path.as_posix() != ref:
            raise ValueError("scorer file path is not canonical POSIX")
        return self


class ScorerRuntime(StrictModel):
    python_implementation: Literal["CPython"]
    python_version: Literal["3.12"]
    pydantic_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")


class ScorerManifest(StrictModel):
    kind: Literal["normshift-acceptance-scorer-manifest"]
    schema_version: Literal["1.0.0"]
    scorer_id: Literal["normshift-m1-m2-exact-scorer-v1"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: str = Field(pattern=SHA256_PATTERN)
    frozen_before_blind_evaluation: Literal[True]
    runtime: ScorerRuntime
    files: list[ScorerFileRecord] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_unique_files(self) -> ScorerManifest:
        paths = [record.path for record in self.files]
        if paths != sorted(paths):
            raise ValueError("scorer manifest file paths must be sorted")
        if len(paths) != len(set(paths)):
            raise ValueError("scorer manifest file paths must be unique")
        if sum(record.bytes for record in self.files) > 32 * 1024 * 1024:
            raise ValueError("scorer manifest declared file bytes exceed 32 MiB")
        return self
