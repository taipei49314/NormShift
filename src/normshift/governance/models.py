"""Strict data contracts for neutral labeling and blind split custody.

These models are governance primitives only.  They do not contain acceptance
thresholds, system predictions, metric values, or an authority to grant M1/M2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from normshift.acceptance.item_key import (
    acceptance_item_key,
    validate_portable_locator,
    validate_portable_source_ref,
)
from normshift.acceptance.models import EvaluationFamily, EvaluationTask

SHA256_PATTERN = r"^[0-9a-f]{64}$"
GIT_OID_PATTERN = r"^[0-9a-f]{40}$"
UTC_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
CLASS_PATTERN = r"^[A-Z][A-Z0-9_]*$"
SLOT_PATTERN = r"^[a-z][a-z0-9_]*$"


def _semantic_utc(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("timestamp must be a real UTC second in YYYY-MM-DDTHH:MM:SSZ") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError("timestamp is not canonical UTC")
    return value


UtcSecond = Annotated[str, Field(pattern=UTC_PATTERN), AfterValidator(_semantic_utc)]
Sha256 = Annotated[str, Field(pattern=SHA256_PATTERN)]
GitOid = Annotated[str, Field(pattern=GIT_OID_PATTERN)]
ReviewerId = Annotated[str, Field(pattern=ID_PATTERN)]
PortableLocator = Annotated[
    str, Field(min_length=1, max_length=1024), AfterValidator(validate_portable_locator)
]


def _governance_portable_source_ref(value: str) -> str:
    """Apply the frozen portable grammar plus a conservative custody encoding.

    Governance paths are materialized on all three supported operating systems.
    Restricting their path portion to ASCII prevents compatibility-normalization
    aliases (for example ``a`` versus full-width ``\uff41``) from naming distinct
    evidence records on one host and the same record on another.
    """

    validate_portable_source_ref(value)
    if not value.isascii():
        raise ValueError("governance portable source ref must use ASCII path bytes")
    if len(value.encode("ascii")) > 768:
        raise ValueError("governance portable source ref exceeds 768 path bytes")
    if any(len(segment.encode("ascii")) > 240 for segment in value.split("/")):
        raise ValueError("governance portable source ref segment exceeds 240 path bytes")
    return value


PortableSourceRef = Annotated[
    str,
    Field(min_length=1, max_length=768),
    AfterValidator(_governance_portable_source_ref),
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


# This is a governance copy of the already-frozen scorer ontology.  It prevents
# packets from silently inventing slots/classes while keeping scorer authority
# untouched.  The verifier also binds every artifact to the exact frozen policy.
SLOT_CLASSES: dict[EvaluationTask, dict[str, frozenset[str]]] = {
    EvaluationTask.M1_REQUIREMENT_EXTRACTION: {
        "requirement": frozenset({"NONE", "REQUIREMENT"})
    },
    EvaluationTask.M1_MODALITY: {
        "modality": frozenset({"NONE", "MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT", "MAY"})
    },
    EvaluationTask.M1_REGION: {
        "region": frozenset({"NONE", "NORMATIVE", "INFORMATIVE", "EXCLUDED"})
    },
    EvaluationTask.M1_FAMILY_DETECTION: {
        "family": frozenset({"NONE", "RFC", "W3C_TR", "WHATWG"})
    },
    EvaluationTask.M2_IDENTITY: {
        "identity": frozenset({"NONE", "SAME_LINEAGE", "DIFFERENT_LINEAGE"})
    },
    EvaluationTask.M2_RELATION: {
        "relation": frozenset(
            {"NONE", "CONTINUES", "SPLIT_INTO", "MERGED_FROM", "ADDED", "REMOVED", "AMBIGUOUS"}
        )
    },
    EvaluationTask.M2_CHANGE: {
        "structural_form": frozenset(
            {"NONE", "MOVE_ONLY", "REWRITE_ONLY", "MOVED_AND_REWRITTEN"}
        ),
        "actor": frozenset({"NONE", "ACTOR_CHANGED"}),
        "action": frozenset({"NONE", "ACTION_CHANGED"}),
        "object": frozenset({"NONE", "OBJECT_CHANGED"}),
        "scope": frozenset({"NONE", "SCOPE_CHANGED"}),
        "modality": frozenset({"NONE", "MODALITY_CHANGED"}),
        "polarity": frozenset({"NONE", "POLARITY_CHANGED"}),
        "condition": frozenset({"NONE", "CONDITION_ADDED", "CONDITION_REMOVED"}),
        "exception": frozenset({"NONE", "EXCEPTION_ADDED", "EXCEPTION_REMOVED"}),
    },
    EvaluationTask.M2_DEFINITION_XREF: {
        "definition": frozenset(
            {"NONE", "DEFINITION_ADDED", "DEFINITION_CHANGED", "DEFINITION_REMOVED"}
        ),
        "definition_reference": frozenset({"NONE", "REFERENCES_DEFINITION"}),
        "cross_reference": frozenset({"NONE", "CROSS_REFERENCE"}),
        "indirect_impact": frozenset({"NONE", "INDIRECT_IMPACT"}),
    },
    EvaluationTask.M2_AMBIGUITY_ROUTING: {
        "routing": frozenset({"NONE", "ROUTE_AMBIGUOUS", "ROUTE_CONFIDENT"})
    },
}


def _validate_item_binding(
    *,
    item_key: str,
    task: EvaluationTask,
    evaluation_slot: str,
    source_sha256s: list[str],
    portable_locators: list[str],
) -> None:
    if len(source_sha256s) != len(portable_locators):
        raise ValueError("source_sha256s and portable_locators must have equal length")
    if task.value.startswith("M1_") and len(source_sha256s) != 1:
        raise ValueError("M1 evidence must bind exactly one whole source document")
    if len(set(source_sha256s)) != len(source_sha256s):
        raise ValueError("source_sha256s must be unique within one evidence binding")
    expected = acceptance_item_key(
        task=task.value,
        evaluation_slot=evaluation_slot,
        source_sha256s=source_sha256s,
        portable_locators=portable_locators,
    )
    if item_key != expected:
        raise ValueError("item_key is not canonical for task/slot/source/locator evidence")


def _validate_slot_classes(
    task: EvaluationTask, evaluation_slot: str, allowed_classes: list[str]
) -> None:
    task_slots = SLOT_CLASSES[task]
    expected = task_slots.get(evaluation_slot)
    if expected is None:
        raise ValueError(f"evaluation_slot is not frozen for {task.value}")
    if allowed_classes != sorted(expected):
        raise ValueError("allowed_classes must exactly equal the sorted frozen slot ontology")


class NeutralityAttestation(StrictModel):
    contains_model_proposal: Literal[False]
    contains_model_confidence: Literal[False]
    contains_candidate_prediction: Literal[False]
    created_before_prediction_access: Literal[True]


class PacketItem(StrictModel):
    item_key: Sha256
    task: EvaluationTask
    evaluation_slot: str = Field(pattern=SLOT_PATTERN)
    source_sha256s: list[Sha256] = Field(min_length=1, max_length=4)
    portable_locators: list[PortableLocator] = Field(min_length=1, max_length=4)
    evidence_sha256: Sha256
    allowed_classes: list[str] = Field(min_length=2, max_length=16)

    @model_validator(mode="after")
    def validate_binding_and_ontology(self) -> PacketItem:
        _validate_item_binding(
            item_key=self.item_key,
            task=self.task,
            evaluation_slot=self.evaluation_slot,
            source_sha256s=self.source_sha256s,
            portable_locators=self.portable_locators,
        )
        _validate_slot_classes(self.task, self.evaluation_slot, self.allowed_classes)
        return self


class LabelingPacket(StrictModel):
    kind: Literal["normshift-neutral-labeling-packet"]
    schema_version: Literal["1.0.0"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: Sha256
    packet_id: str = Field(pattern=ID_PATTERN)
    packet_version: str = Field(pattern=ID_PATTERN)
    dataset_split: Literal["DEVELOPMENT", "BLIND_HOLDOUT"]
    source_manifest_sha256: Sha256
    split_manifest_sha256: Sha256
    prepared_by_reviewer_id: ReviewerId
    prepared_at_utc: UtcSecond
    neutrality: NeutralityAttestation
    items: list[PacketItem] = Field(min_length=1, max_length=250_000)

    @model_validator(mode="after")
    def validate_unique_items(self) -> LabelingPacket:
        keys = [item.item_key for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("packet item_key values must be unique")
        if keys != sorted(keys):
            raise ValueError("packet items must be sorted by item_key")
        return self


class LabelResponseOutcome(StrEnum):
    LABELED = "LABELED"
    ABSTAINED = "ABSTAINED"
    AMBIGUOUS = "AMBIGUOUS"


class LabelResponse(StrictModel):
    item_key: Sha256
    task: EvaluationTask
    evaluation_slot: str = Field(pattern=SLOT_PATTERN)
    source_sha256s: list[Sha256] = Field(min_length=1, max_length=4)
    portable_locators: list[PortableLocator] = Field(min_length=1, max_length=4)
    evidence_sha256: Sha256
    outcome: LabelResponseOutcome
    selected_class: str | None = Field(default=None, pattern=CLASS_PATTERN)
    reason: str = Field(min_length=1, max_length=4096)
    decided_at_utc: UtcSecond

    @model_validator(mode="after")
    def validate_response(self) -> LabelResponse:
        _validate_item_binding(
            item_key=self.item_key,
            task=self.task,
            evaluation_slot=self.evaluation_slot,
            source_sha256s=self.source_sha256s,
            portable_locators=self.portable_locators,
        )
        if self.outcome == LabelResponseOutcome.LABELED:
            if self.selected_class is None:
                raise ValueError("LABELED response requires selected_class")
            allowed = SLOT_CLASSES[self.task].get(self.evaluation_slot)
            if allowed is None or self.selected_class not in allowed:
                raise ValueError("selected_class is outside the frozen slot ontology")
        elif self.selected_class is not None:
            raise ValueError("abstained/ambiguous response must not assert a class")
        return self


class IndependenceAttestation(StrictModel):
    worked_independently: Literal[True]
    viewed_other_labeler_answers: Literal[False]
    viewed_model_proposals: Literal[False]
    viewed_model_confidence: Literal[False]
    viewed_candidate_predictions: Literal[False]
    implemented_evaluated_system: Literal[False]


class LabelSubmission(StrictModel):
    kind: Literal["normshift-independent-label-submission"]
    schema_version: Literal["1.0.0"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: Sha256
    submission_id: str = Field(pattern=ID_PATTERN)
    packet_sha256: Sha256
    review_round_id: str = Field(pattern=ID_PATTERN)
    labeler_id: ReviewerId
    independence: IndependenceAttestation
    submitted_at_utc: UtcSecond
    responses: list[LabelResponse] = Field(min_length=1, max_length=250_000)

    @model_validator(mode="after")
    def validate_unique_responses(self) -> LabelSubmission:
        keys = [response.item_key for response in self.responses]
        if len(keys) != len(set(keys)):
            raise ValueError("submission response item_key values must be unique")
        if keys != sorted(keys):
            raise ValueError("submission responses must be sorted by item_key")
        if any(response.decided_at_utc > self.submitted_at_utc for response in self.responses):
            raise ValueError("response decision timestamp is after submission timestamp")
        return self


class SubmissionFile(StrictModel):
    submission_id: str = Field(pattern=ID_PATTERN)
    review_round_id: str = Field(pattern=ID_PATTERN)
    labeler_id: ReviewerId
    portable_ref: PortableSourceRef
    sha256: Sha256
    bytes: int = Field(ge=1, le=16 * 1024 * 1024)


class VoteBinding(StrictModel):
    labeler_id: ReviewerId
    submission_sha256: Sha256
    response_sha256: Sha256


class AdjudicationOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    ABSTAINED = "ABSTAINED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICT = "CONFLICT"


class DecisionEventType(StrEnum):
    INITIAL = "INITIAL"
    CORRECTION = "CORRECTION"


class DecisionEvent(StrictModel):
    decision_id: str = Field(pattern=ID_PATTERN)
    review_round_id: str = Field(pattern=ID_PATTERN)
    revision: int = Field(ge=1, le=1_000_000)
    event_type: DecisionEventType
    supersedes_decision_id: str | None = Field(default=None, pattern=ID_PATTERN)
    item_key: Sha256
    task: EvaluationTask
    evaluation_slot: str = Field(pattern=SLOT_PATTERN)
    source_sha256s: list[Sha256] = Field(min_length=1, max_length=4)
    portable_locators: list[PortableLocator] = Field(min_length=1, max_length=4)
    evidence_sha256: Sha256
    reviewer_ids: list[ReviewerId] = Field(min_length=2, max_length=16)
    adjudicator_id: ReviewerId
    votes: list[VoteBinding] = Field(min_length=2, max_length=16)
    decision: AdjudicationOutcome
    decided_class: str | None = Field(default=None, pattern=CLASS_PATTERN)
    reason: str = Field(min_length=1, max_length=4096)
    decided_at_utc: UtcSecond

    @model_validator(mode="after")
    def validate_event(self) -> DecisionEvent:
        _validate_item_binding(
            item_key=self.item_key,
            task=self.task,
            evaluation_slot=self.evaluation_slot,
            source_sha256s=self.source_sha256s,
            portable_locators=self.portable_locators,
        )
        if len(self.reviewer_ids) != len(set(self.reviewer_ids)):
            raise ValueError("reviewer_ids must be unique")
        if self.reviewer_ids != sorted(self.reviewer_ids):
            raise ValueError("reviewer_ids must be sorted")
        if self.adjudicator_id in self.reviewer_ids:
            raise ValueError("adjudicator must be separate from independent labelers")
        vote_ids = [vote.labeler_id for vote in self.votes]
        if vote_ids != self.reviewer_ids:
            raise ValueError("votes must be sorted and exactly cover reviewer_ids")
        if self.revision == 1:
            if (
                self.event_type != DecisionEventType.INITIAL
                or self.supersedes_decision_id is not None
            ):
                raise ValueError("revision 1 must be INITIAL and supersede nothing")
        elif self.event_type != DecisionEventType.CORRECTION or self.supersedes_decision_id is None:
            raise ValueError("revision >1 must be a CORRECTION with a superseded decision")
        if self.decision == AdjudicationOutcome.ACCEPTED:
            if self.decided_class is None:
                raise ValueError("accepted decision requires decided_class")
            allowed = SLOT_CLASSES[self.task].get(self.evaluation_slot)
            if allowed is None or self.decided_class not in allowed:
                raise ValueError("decided_class is outside the frozen slot ontology")
        elif self.decided_class is not None:
            raise ValueError("non-accepted decision must not assert a class")
        return self


class LedgerRevisionKind(StrEnum):
    INITIAL_FREEZE = "INITIAL_FREEZE"
    POST_FREEZE_CORRECTION = "POST_FREEZE_CORRECTION"


class LedgerRevisionContext(StrictModel):
    kind: LedgerRevisionKind
    supersedes_ledger_sha256: Sha256 | None
    invalidated_measurement_sha256s: list[Sha256] = Field(max_length=100_000)
    correction_reason: str | None = Field(default=None, min_length=1, max_length=4096)

    @model_validator(mode="after")
    def validate_revision_context(self) -> LedgerRevisionContext:
        if len(self.invalidated_measurement_sha256s) != len(
            set(self.invalidated_measurement_sha256s)
        ):
            raise ValueError("invalidated measurement hashes must be unique")
        if self.invalidated_measurement_sha256s != sorted(self.invalidated_measurement_sha256s):
            raise ValueError("invalidated measurement hashes must be sorted")
        if self.kind == LedgerRevisionKind.INITIAL_FREEZE:
            if (
                self.supersedes_ledger_sha256 is not None
                or self.invalidated_measurement_sha256s
                or self.correction_reason is not None
            ):
                raise ValueError("initial ledger freeze cannot contain correction fields")
        elif (
            self.supersedes_ledger_sha256 is None
            or not self.invalidated_measurement_sha256s
            or self.correction_reason is None
        ):
            raise ValueError(
                "post-freeze correction requires prior ledger, affected measurements, and reason"
            )
        return self


class ReviewRoundKind(StrEnum):
    INITIAL = "INITIAL"
    POST_FREEZE_CORRECTION = "POST_FREEZE_CORRECTION"


class ReviewRound(StrictModel):
    review_round_id: str = Field(pattern=ID_PATTERN)
    sequence: int = Field(ge=1, le=1_000_000)
    kind: ReviewRoundKind
    supersedes_review_round_id: str | None = Field(default=None, pattern=ID_PATTERN)
    labeler_ids: list[ReviewerId] = Field(min_length=2, max_length=16)
    adjudicator_id: ReviewerId
    labelers_implemented_evaluated_system: Literal[False]
    adjudicator_implemented_evaluated_system: Literal[False]
    viewed_prior_label_decisions: Literal[False]
    viewed_candidate_predictions: Literal[False]
    opened_at_utc: UtcSecond
    completed_at_utc: UtcSecond

    @model_validator(mode="after")
    def validate_round(self) -> ReviewRound:
        if len(self.labeler_ids) != len(set(self.labeler_ids)):
            raise ValueError("review-round labeler_ids must be unique")
        if self.labeler_ids != sorted(self.labeler_ids):
            raise ValueError("review-round labeler_ids must be sorted")
        if self.adjudicator_id in self.labeler_ids:
            raise ValueError("review-round adjudicator must be separate from labelers")
        if self.opened_at_utc > self.completed_at_utc:
            raise ValueError("review round opens after it completes")
        if self.sequence == 1:
            if self.kind != ReviewRoundKind.INITIAL or self.supersedes_review_round_id is not None:
                raise ValueError("review round 1 must be INITIAL and supersede nothing")
        elif (
            self.kind != ReviewRoundKind.POST_FREEZE_CORRECTION
            or self.supersedes_review_round_id is None
        ):
            raise ValueError("later review rounds must be post-freeze corrections")
        return self


class DecisionLedger(StrictModel):
    kind: Literal["normshift-label-decision-ledger"]
    schema_version: Literal["1.0.0"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: Sha256
    ledger_id: str = Field(pattern=ID_PATTERN)
    ledger_version: str = Field(pattern=ID_PATTERN)
    packet_sha256: Sha256
    candidate_predictions_viewed_before_freeze: Literal[False]
    labels_and_decisions_hash_frozen_before_predictions: Literal[True]
    review_rounds: list[ReviewRound] = Field(min_length=1, max_length=64)
    active_review_round_id: str = Field(pattern=ID_PATTERN)
    submissions: list[SubmissionFile] = Field(min_length=2, max_length=1024)
    revision_context: LedgerRevisionContext
    decisions: list[DecisionEvent] = Field(min_length=1, max_length=1_000_000)
    active_decision_ids: list[str] = Field(min_length=1, max_length=250_000)
    frozen_at_utc: UtcSecond

    @model_validator(mode="after")
    def validate_ledger_structure(self) -> DecisionLedger:
        round_ids = [round_.review_round_id for round_ in self.review_rounds]
        if len(round_ids) != len(set(round_ids)):
            raise ValueError("review_round_id values must be unique")
        if [round_.sequence for round_ in self.review_rounds] != list(
            range(1, len(self.review_rounds) + 1)
        ):
            raise ValueError("review rounds must be contiguous and ordered from sequence 1")
        for previous, current in zip(self.review_rounds, self.review_rounds[1:], strict=False):
            if current.supersedes_review_round_id != previous.review_round_id:
                raise ValueError("review round must supersede the immediate prior round")
            if current.opened_at_utc <= previous.completed_at_utc:
                raise ValueError(
                    "later review round must open strictly after the prior round completes"
                )
        if self.active_review_round_id != self.review_rounds[-1].review_round_id:
            raise ValueError("active_review_round_id must name the latest retained round")
        prior_authority: set[str] = set()
        for round_ in self.review_rounds:
            current_authority = set(round_.labeler_ids) | {round_.adjudicator_id}
            if round_.sequence > 1 and current_authority & prior_authority:
                raise ValueError(
                    "post-freeze correction must use new reviewer authority "
                    "separate from prior rounds"
                )
            prior_authority.update(current_authority)
            if round_.completed_at_utc > self.frozen_at_utc:
                raise ValueError("review round completes after ledger freeze")
        if self.revision_context.kind == LedgerRevisionKind.INITIAL_FREEZE:
            if len(self.review_rounds) != 1:
                raise ValueError("initial ledger freeze must contain exactly one review round")
        elif len(self.review_rounds) < 2:
            raise ValueError("post-freeze correction ledger requires a retained correction round")
        submission_ids = [record.submission_id for record in self.submissions]
        if len(submission_ids) != len(set(submission_ids)):
            raise ValueError("submission_id values must be unique")
        round_by_id = {round_.review_round_id: round_ for round_ in self.review_rounds}
        observed_submission_order: list[tuple[int, str]] = []
        submissions_by_round: dict[str, list[str]] = {}
        for record in self.submissions:
            submission_round = round_by_id.get(record.review_round_id)
            if submission_round is None:
                raise ValueError("submission names an unknown review round")
            observed_submission_order.append((submission_round.sequence, record.labeler_id))
            submissions_by_round.setdefault(record.review_round_id, []).append(record.labeler_id)
        if observed_submission_order != sorted(observed_submission_order):
            raise ValueError("submissions must be sorted by review round then labeler")
        for round_ in self.review_rounds:
            if submissions_by_round.get(round_.review_round_id) != round_.labeler_ids:
                raise ValueError("submissions must exactly cover every review-round labeler")
        refs = [record.portable_ref for record in self.submissions]
        if len(refs) != len(set(refs)) or len({ref.casefold() for ref in refs}) != len(refs):
            raise ValueError("submission portable refs must be exact and casefold unique")
        decision_ids = [event.decision_id for event in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("decision_id values must be unique")
        for event in self.decisions:
            event_round = round_by_id.get(event.review_round_id)
            if event_round is None:
                raise ValueError("decision event names an unknown review round")
            if event.decided_at_utc > event_round.completed_at_utc:
                raise ValueError("decision timestamp is after its review round completes")
        if any(event.decided_at_utc > self.frozen_at_utc for event in self.decisions):
            raise ValueError("decision timestamp is after ledger freeze")
        if len(self.active_decision_ids) != len(set(self.active_decision_ids)):
            raise ValueError("active_decision_ids must be unique")
        if self.active_decision_ids != sorted(self.active_decision_ids):
            raise ValueError("active_decision_ids must be sorted")
        return self


class DatasetSplit(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    BLIND_HOLDOUT = "BLIND_HOLDOUT"


class BlindSplitDocument(StrictModel):
    source_id: str = Field(pattern=ID_PATTERN)
    family: EvaluationFamily
    standard_id: str = Field(min_length=1, max_length=256)
    version: str = Field(min_length=1, max_length=256)
    raw_sha256: Sha256
    derived_sha256s: list[Sha256] = Field(max_length=128)
    portable_source_ref: PortableSourceRef
    m1_in_scope: bool
    m2_in_scope: bool
    m2_lineage_chain_id: str | None = Field(default=None, pattern=ID_PATTERN)
    split: DatasetSplit

    @model_validator(mode="after")
    def validate_document(self) -> BlindSplitDocument:
        if len(self.derived_sha256s) != len(set(self.derived_sha256s)):
            raise ValueError("derived_sha256s must be unique")
        if self.derived_sha256s != sorted(self.derived_sha256s):
            raise ValueError("derived_sha256s must be sorted")
        if self.raw_sha256 in self.derived_sha256s:
            raise ValueError("raw_sha256 must not be repeated as a derived hash")
        if not self.m1_in_scope and not self.m2_in_scope:
            raise ValueError("every split document must be in M1 and/or M2 scope")
        if self.m2_in_scope != (self.m2_lineage_chain_id is not None):
            raise ValueError("m2 lineage chain is required exactly when m2_in_scope is true")
        return self


class CandidateArtifacts(StrictModel):
    commit: GitOid
    tree: GitOid
    wheel_sha256: Sha256
    sdist_sha256: Sha256
    source_zip_sha256: Sha256
    bundle_sha256: Sha256


class CandidateFreezeStatus(StrEnum):
    NOT_FROZEN = "NOT_FROZEN"
    FROZEN = "FROZEN"


class CandidateFreeze(StrictModel):
    status: CandidateFreezeStatus
    candidate: CandidateArtifacts | None
    frozen_at_utc: UtcSecond | None
    holdout_opened_at_utc: UtcSecond | None
    predictions_started_at_utc: UtcSecond | None

    @model_validator(mode="after")
    def validate_candidate_order(self) -> CandidateFreeze:
        if self.status == CandidateFreezeStatus.NOT_FROZEN:
            if any(
                value is not None
                for value in (
                    self.candidate,
                    self.frozen_at_utc,
                    self.holdout_opened_at_utc,
                    self.predictions_started_at_utc,
                )
            ):
                raise ValueError("NOT_FROZEN candidate must not contain candidate/access fields")
            return self
        if self.candidate is None or self.frozen_at_utc is None:
            raise ValueError("FROZEN status requires all exact candidate hashes and freeze time")
        if (
            self.holdout_opened_at_utc is not None
            and self.holdout_opened_at_utc <= self.frozen_at_utc
        ):
            raise ValueError("holdout must open strictly after exact candidate freeze")
        if (
            self.predictions_started_at_utc is not None
            and self.predictions_started_at_utc <= self.frozen_at_utc
        ):
            raise ValueError("predictions must start strictly after exact candidate freeze")
        if self.predictions_started_at_utc is not None and self.holdout_opened_at_utc is None:
            raise ValueError("predictions cannot start before holdout opening is recorded")
        if (
            self.holdout_opened_at_utc is not None
            and self.predictions_started_at_utc is not None
            and self.predictions_started_at_utc <= self.holdout_opened_at_utc
        ):
            raise ValueError("predictions must start strictly after holdout opens")
        return self


class BlindnessAttestation(StrictModel):
    holdout_membership_visible_to_implementation_before_candidate_freeze: Literal[False]
    holdout_gold_visible_to_implementation_before_candidate_freeze: Literal[False]
    holdout_predictions_visible_to_implementation_before_candidate_freeze: Literal[False]
    fixture_name_path_url_or_hash_special_cases_added: Literal[False]


class BlindSplitManifest(StrictModel):
    kind: Literal["normshift-blind-split-manifest"]
    schema_version: Literal["1.0.0"]
    policy_id: Literal["normshift-m1-m2-prereg-v1"]
    policy_sha256: Sha256
    split_id: str = Field(pattern=ID_PATTERN)
    split_version: str = Field(pattern=ID_PATTERN)
    source_manifest_sha256: Sha256
    custodian_ids: list[ReviewerId] = Field(min_length=1, max_length=16)
    implementation_author_ids: list[ReviewerId] = Field(min_length=1, max_length=128)
    created_at_utc: UtcSecond
    split_frozen_at_utc: UtcSecond
    blindness: BlindnessAttestation
    candidate_freeze: CandidateFreeze
    documents: list[BlindSplitDocument] = Field(min_length=3, max_length=10_000)

    @model_validator(mode="after")
    def validate_split(self) -> BlindSplitManifest:
        if self.created_at_utc > self.split_frozen_at_utc:
            raise ValueError("split creation timestamp is after split freeze")
        for label, values in (
            ("custodian_ids", self.custodian_ids),
            ("implementation_author_ids", self.implementation_author_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
            if values != sorted(values):
                raise ValueError(f"{label} must be sorted")
        if set(self.custodian_ids) & set(self.implementation_author_ids):
            raise ValueError("split custodians must be independent of implementation authors")
        source_ids = [document.source_id for document in self.documents]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source_id values must be unique (whole-document M1 split)")
        if source_ids != sorted(source_ids):
            raise ValueError("documents must be sorted by source_id")
        raw_hashes = [document.raw_sha256 for document in self.documents]
        if len(raw_hashes) != len(set(raw_hashes)):
            raise ValueError("raw_sha256 values must be unique")
        refs = [document.portable_source_ref for document in self.documents]
        if len(refs) != len(set(refs)) or len({ref.casefold() for ref in refs}) != len(refs):
            raise ValueError("portable source refs must be exact and casefold unique")

        holdout_count = sum(
            document.split == DatasetSplit.BLIND_HOLDOUT for document in self.documents
        )
        if holdout_count * 5 < len(self.documents) * 2:
            raise ValueError("blind holdout is below the exact 40% document-count minimum")

        required_families = set(EvaluationFamily)
        holdout_m1_families = {
            document.family
            for document in self.documents
            if document.m1_in_scope and document.split == DatasetSplit.BLIND_HOLDOUT
        }
        missing_families = sorted(
            family.value for family in required_families - holdout_m1_families
        )
        if missing_families:
            raise ValueError(f"M1 holdout lacks a whole version for families {missing_families}")

        hashes_by_split: dict[DatasetSplit, set[str]] = {
            DatasetSplit.DEVELOPMENT: set(),
            DatasetSplit.BLIND_HOLDOUT: set(),
        }
        for document in self.documents:
            hashes_by_split[document.split].add(document.raw_sha256)
            hashes_by_split[document.split].update(document.derived_sha256s)
        overlap = hashes_by_split[DatasetSplit.DEVELOPMENT] & hashes_by_split[
            DatasetSplit.BLIND_HOLDOUT
        ]
        if overlap:
            raise ValueError("development and holdout raw/derived hashes overlap")

        chain_splits: dict[tuple[EvaluationFamily, str], set[DatasetSplit]] = {}
        chain_members: dict[tuple[EvaluationFamily, str], set[str]] = {}
        for document in self.documents:
            if document.m2_lineage_chain_id is not None:
                key = (document.family, document.m2_lineage_chain_id)
                chain_splits.setdefault(key, set()).add(document.split)
                chain_members.setdefault(key, set()).add(document.source_id)
        missing_chain_families = sorted(
            family.value
            for family in required_families
            if not any(chain_family == family for chain_family, _ in chain_members)
        )
        if missing_chain_families:
            raise ValueError(
                "M2 lineage chains must cover every required family; "
                f"missing={missing_chain_families}"
            )
        undersized_chains = sorted(
            f"{family.value}:{chain_id}"
            for (family, chain_id), members in chain_members.items()
            if len(members) < 3
        )
        if undersized_chains:
            raise ValueError(
                "M2 lineage chains require at least three whole document versions; "
                f"undersized={undersized_chains}"
            )
        split_chains = sorted(
            f"{family.value}:{chain_id}"
            for (family, chain_id), splits in chain_splits.items()
            if len(splits) != 1
        )
        if split_chains:
            raise ValueError(f"M2 lineage chains cross development/holdout: {split_chains}")
        return self
