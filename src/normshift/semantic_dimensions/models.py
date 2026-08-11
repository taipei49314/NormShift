"""Versioned, evidence-bound models for independent M2 semantic dimensions."""

from __future__ import annotations

import hashlib
import re
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from normshift.evidence.hashing import canonical_json_bytes
from normshift.model.types import ChangeClassification

SEMANTIC_DIMENSIONS_SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"
SEMANTIC_DIMENSIONS_KIND: Literal["normshift-semantic-change-dimensions"] = (
    "normshift-semantic-change-dimensions"
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_text(value: str) -> str:
    """Return the SHA-256 of exact UTF-8 text bytes."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_sha256(value: object) -> str:
    """Hash a value after NormShift canonical JSON serialization."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(value: str, *, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class StructuralForm(StrEnum):
    """Orthogonal physical form of a paired requirement change."""

    NONE = "NONE"
    MOVE_ONLY = "MOVE_ONLY"
    REWRITE_ONLY = "REWRITE_ONLY"
    MOVED_AND_REWRITTEN = "MOVED_AND_REWRITTEN"


class SemanticDimension(StrEnum):
    ACTOR = "actor"
    ACTION = "action"
    OBJECT = "object"
    SCOPE = "scope"
    MODALITY = "modality"
    POLARITY = "polarity"
    CONDITION = "condition"
    EXCEPTION = "exception"


class DimensionDisposition(StrEnum):
    """Evidence-aware state for one semantic dimension."""

    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SemanticChangeClass(StrEnum):
    """Exact M2 change classes preregistered by the frozen acceptance policy."""

    MOVE_ONLY = "MOVE_ONLY"
    REWRITE_ONLY = "REWRITE_ONLY"
    MOVED_AND_REWRITTEN = "MOVED_AND_REWRITTEN"
    ACTOR_CHANGED = "ACTOR_CHANGED"
    ACTION_CHANGED = "ACTION_CHANGED"
    OBJECT_CHANGED = "OBJECT_CHANGED"
    SCOPE_CHANGED = "SCOPE_CHANGED"
    MODALITY_CHANGED = "MODALITY_CHANGED"
    POLARITY_CHANGED = "POLARITY_CHANGED"
    CONDITION_ADDED = "CONDITION_ADDED"
    CONDITION_REMOVED = "CONDITION_REMOVED"
    EXCEPTION_ADDED = "EXCEPTION_ADDED"
    EXCEPTION_REMOVED = "EXCEPTION_REMOVED"


class ObservationOrigin(StrEnum):
    REQUIREMENT_FIELD = "REQUIREMENT_FIELD"
    NORMALIZED_TEXT_SPAN = "NORMALIZED_TEXT_SPAN"


class ObservationVerification(StrEnum):
    VERIFIED_REQUIREMENT_FIELD = "VERIFIED_REQUIREMENT_FIELD"
    ASSERTED_UNVERIFIED = "ASSERTED_UNVERIFIED"


class NormalizedTextSpan(_StrictModel):
    """Caller-supplied exact span into ``Requirement.normalized_text``."""

    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def _validate_range(self) -> Self:
        if self.end <= self.start:
            raise ValueError("normalized-text span end must be greater than start")
        return self


class RequirementEvidenceRef(_StrictModel):
    """Exact source identity for one old/new requirement side."""

    requirement_id: str = Field(min_length=1)
    document_sha256: str
    document_version: str = Field(min_length=1)
    source_locator: str = Field(min_length=1)
    section_path: str = Field(min_length=1)
    original_text_sha256: str
    normalized_text_sha256: str
    semantic_fingerprint: str = Field(min_length=1)
    requirement_payload_sha256: str

    @model_validator(mode="after")
    def _validate_hashes(self) -> Self:
        for field_name in (
            "document_sha256",
            "original_text_sha256",
            "normalized_text_sha256",
            "requirement_payload_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name=field_name)
        return self


class SemanticValueEvidence(_StrictModel):
    """One normalized semantic value and its exact source binding."""

    dimension: SemanticDimension
    value: str = Field(min_length=1)
    value_sha256: str
    origin: ObservationOrigin
    verification_status: ObservationVerification
    source_text_sha256: str
    span_start: int | None = Field(default=None, ge=0)
    span_end: int | None = Field(default=None, gt=0)
    evidence_sha256: str

    @model_validator(mode="after")
    def _validate_evidence(self) -> Self:
        _require_sha256(self.value_sha256, field_name="value_sha256")
        _require_sha256(self.source_text_sha256, field_name="source_text_sha256")
        _require_sha256(self.evidence_sha256, field_name="evidence_sha256")
        if self.value_sha256 != sha256_text(self.value):
            raise ValueError("value_sha256 does not bind the exact semantic value")
        if self.origin is ObservationOrigin.NORMALIZED_TEXT_SPAN:
            if self.verification_status is not ObservationVerification.ASSERTED_UNVERIFIED:
                raise ValueError("caller-selected spans must remain explicitly unverified")
            if self.span_start is None or self.span_end is None:
                raise ValueError("normalized-text evidence requires both span bounds")
            if self.span_end <= self.span_start:
                raise ValueError("normalized-text evidence has an invalid span")
        else:
            if self.verification_status is not ObservationVerification.VERIFIED_REQUIREMENT_FIELD:
                raise ValueError("requirement fields must retain verified status")
            if self.span_start is not None or self.span_end is not None:
                raise ValueError("requirement-field evidence cannot carry text span bounds")
        payload = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if self.evidence_sha256 != canonical_sha256(payload):
            raise ValueError("evidence_sha256 does not bind the observation")
        return self


_SCALAR_CLASS_BY_DIMENSION: dict[SemanticDimension, SemanticChangeClass] = {
    SemanticDimension.ACTOR: SemanticChangeClass.ACTOR_CHANGED,
    SemanticDimension.ACTION: SemanticChangeClass.ACTION_CHANGED,
    SemanticDimension.OBJECT: SemanticChangeClass.OBJECT_CHANGED,
    SemanticDimension.SCOPE: SemanticChangeClass.SCOPE_CHANGED,
    SemanticDimension.MODALITY: SemanticChangeClass.MODALITY_CHANGED,
    SemanticDimension.POLARITY: SemanticChangeClass.POLARITY_CHANGED,
}

_TRANSITION_CLASS_BY_DIMENSION: dict[
    SemanticDimension, tuple[SemanticChangeClass, SemanticChangeClass]
] = {
    SemanticDimension.CONDITION: (
        SemanticChangeClass.CONDITION_ADDED,
        SemanticChangeClass.CONDITION_REMOVED,
    ),
    SemanticDimension.EXCEPTION: (
        SemanticChangeClass.EXCEPTION_ADDED,
        SemanticChangeClass.EXCEPTION_REMOVED,
    ),
}


class SemanticSlotChange(_StrictModel):
    """Typed comparison result for one fixed semantic dimension."""

    dimension: SemanticDimension
    disposition: DimensionDisposition
    change_class: SemanticChangeClass | None
    old: SemanticValueEvidence | None
    new: SemanticValueEvidence | None
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_transition(self) -> Self:
        for observation in (self.old, self.new):
            if observation is not None and observation.dimension is not self.dimension:
                raise ValueError("slot observation dimension does not match its slot")
            if (
                observation is not None
                and self.dimension in {SemanticDimension.OBJECT, SemanticDimension.SCOPE}
                and observation.verification_status
                is not ObservationVerification.ASSERTED_UNVERIFIED
            ):
                raise ValueError("object/scope observations require unverified candidate status")

        if self.dimension in {SemanticDimension.OBJECT, SemanticDimension.SCOPE} and (
            self.disposition
            not in {DimensionDisposition.UNKNOWN, DimensionDisposition.NOT_APPLICABLE}
        ):
            raise ValueError("object/scope slots cannot be adjudicated in schema version 1.0.0")

        expected_class: SemanticChangeClass | None = None
        if self.disposition is DimensionDisposition.CHANGED:
            expected_class = _SCALAR_CLASS_BY_DIMENSION.get(self.dimension)
            if expected_class is None:
                raise ValueError("CHANGED is not a preregistered condition/exception class")
        elif self.disposition is DimensionDisposition.ADDED:
            transition = _TRANSITION_CLASS_BY_DIMENSION.get(self.dimension)
            if transition is None:
                raise ValueError("ADDED is limited to condition and exception slots")
            expected_class = transition[0]
        elif self.disposition is DimensionDisposition.REMOVED:
            transition = _TRANSITION_CLASS_BY_DIMENSION.get(self.dimension)
            if transition is None:
                raise ValueError("REMOVED is limited to condition and exception slots")
            expected_class = transition[1]
        if self.change_class is not expected_class:
            raise ValueError("slot change_class does not match dimension/disposition")

        old_value = self.old.value if self.old is not None else None
        new_value = self.new.value if self.new is not None else None
        if self.disposition is DimensionDisposition.NOT_APPLICABLE:
            if self.old is not None or self.new is not None:
                raise ValueError("NOT_APPLICABLE slots cannot carry observations")
        elif (
            self.disposition is DimensionDisposition.UNKNOWN
            and self.old is not None
            and self.new is not None
            and all(
                observation.verification_status
                is ObservationVerification.VERIFIED_REQUIREMENT_FIELD
                for observation in (self.old, self.new)
            )
        ):
            raise ValueError("UNKNOWN with two observations requires explicit unverified evidence")
        elif self.disposition is DimensionDisposition.AMBIGUOUS:
            if self.old is None or self.new is None or old_value == new_value:
                raise ValueError("AMBIGUOUS requires two conflicting observations")
        elif self.disposition is DimensionDisposition.UNCHANGED:
            both_absent = self.old is None and self.new is None
            if both_absent:
                if self.dimension not in {
                    SemanticDimension.CONDITION,
                    SemanticDimension.EXCEPTION,
                }:
                    raise ValueError(
                        "only condition/exception can be explicitly absent on both sides"
                    )
            elif self.old is None or self.new is None or old_value != new_value:
                raise ValueError("UNCHANGED requires equal observations")
        elif self.disposition is DimensionDisposition.CHANGED:
            if self.old is None or self.new is None or old_value == new_value:
                raise ValueError("CHANGED requires two different observations")
        elif self.disposition is DimensionDisposition.ADDED:
            if self.old is not None or self.new is None:
                raise ValueError("ADDED requires only a new observation")
        elif self.disposition is DimensionDisposition.REMOVED and (
            self.old is None or self.new is not None
        ):
            raise ValueError("REMOVED requires only an old observation")
        return self


class SemanticDimensionSlots(_StrictModel):
    actor: SemanticSlotChange
    action: SemanticSlotChange
    object: SemanticSlotChange
    scope: SemanticSlotChange
    modality: SemanticSlotChange
    polarity: SemanticSlotChange
    condition: SemanticSlotChange
    exception: SemanticSlotChange

    @model_validator(mode="after")
    def _validate_fixed_dimensions(self) -> Self:
        expected = {
            "actor": SemanticDimension.ACTOR,
            "action": SemanticDimension.ACTION,
            "object": SemanticDimension.OBJECT,
            "scope": SemanticDimension.SCOPE,
            "modality": SemanticDimension.MODALITY,
            "polarity": SemanticDimension.POLARITY,
            "condition": SemanticDimension.CONDITION,
            "exception": SemanticDimension.EXCEPTION,
        }
        for field_name, dimension in expected.items():
            if getattr(self, field_name).dimension is not dimension:
                raise ValueError(f"{field_name} slot has the wrong dimension")
        return self

    def ordered(self) -> tuple[SemanticSlotChange, ...]:
        """Return slots in the canonical schema order."""
        return (
            self.actor,
            self.action,
            self.object,
            self.scope,
            self.modality,
            self.polarity,
            self.condition,
            self.exception,
        )


class SemanticChangeEvidence(_StrictModel):
    """Binding to the unchanged primary M0 ``Change`` and exact requirements."""

    authority_kind: Literal["FULL_REPORT_REPLAY"]
    authority_id: str = Field(min_length=1)
    authority_report_sha256: str
    verification_receipt_sha256: str
    verification_receipt_payload_sha256: str
    primary_change_id: str = Field(min_length=1)
    primary_classification: ChangeClassification
    primary_change_sha256: str
    primary_evidence_hashes: list[str]
    old_requirement: RequirementEvidenceRef | None
    new_requirement: RequirementEvidenceRef | None

    @model_validator(mode="after")
    def _validate_evidence(self) -> Self:
        for field_name in (
            "authority_report_sha256",
            "verification_receipt_sha256",
            "verification_receipt_payload_sha256",
            "primary_change_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name=field_name)
        if self.old_requirement is None and self.new_requirement is None:
            raise ValueError("semantic change evidence requires at least one requirement side")
        if self.primary_evidence_hashes != sorted(set(self.primary_evidence_hashes)):
            raise ValueError("primary_evidence_hashes must be sorted and unique")
        for digest in self.primary_evidence_hashes:
            _require_sha256(digest, field_name="primary_evidence_hashes item")
        if self.primary_classification is ChangeClassification.ADDED:
            if self.old_requirement is not None or self.new_requirement is None:
                raise ValueError("ADDED evidence must contain only the new requirement")
        elif self.primary_classification is ChangeClassification.REMOVED:
            if self.old_requirement is None or self.new_requirement is not None:
                raise ValueError("REMOVED evidence must contain only the old requirement")
        elif self.old_requirement is None or self.new_requirement is None:
            raise ValueError("paired primary classifications require both requirement sides")
        return self


class SemanticChangeDimensions(_StrictModel):
    """Independent M2 dimensions for one unchanged primary M0 change event."""

    semantic_change_id: str
    structural_form: StructuralForm
    change_classes: list[SemanticChangeClass]
    slots: SemanticDimensionSlots
    evidence: SemanticChangeEvidence

    @model_validator(mode="after")
    def _validate_derived_fields(self) -> Self:
        _require_sha256(self.semantic_change_id, field_name="semantic_change_id")
        expected_classes: set[SemanticChangeClass] = set()
        if self.structural_form is not StructuralForm.NONE:
            expected_classes.add(SemanticChangeClass(self.structural_form.value))
        expected_classes.update(
            slot.change_class for slot in self.slots.ordered() if slot.change_class is not None
        )
        ordered_classes = sorted(expected_classes, key=lambda item: item.value)
        if self.change_classes != ordered_classes:
            raise ValueError("change_classes must exactly equal sorted derived classes")
        payload = self.model_dump(mode="json", exclude={"semantic_change_id"})
        if self.semantic_change_id != canonical_sha256(payload):
            raise ValueError("semantic_change_id does not bind the semantic payload")
        return self


class SemanticDimensionsDocument(_StrictModel):
    """Canonical versioned document with a self-consistency integrity digest."""

    schema_version: Literal["1.0.0"]
    kind: Literal["normshift-semantic-change-dimensions"]
    change: SemanticChangeDimensions
    integrity_sha256: str

    @model_validator(mode="after")
    def _validate_integrity(self) -> Self:
        _require_sha256(self.integrity_sha256, field_name="integrity_sha256")
        payload = self.model_dump(mode="json", exclude={"integrity_sha256"})
        if self.integrity_sha256 != canonical_sha256(payload):
            raise ValueError("integrity_sha256 does not bind the document payload")
        return self
