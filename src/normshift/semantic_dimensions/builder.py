"""Deterministic construction and source replay for M2 semantic dimensions."""

from __future__ import annotations

from collections.abc import Iterable

from normshift.evidence.hashing import canonical_json_bytes
from normshift.model.types import Requirement
from normshift.normalize.html_normalize import editorial_normalize, strip_heading_number
from normshift.semantic_dimensions.authority import (
    VerifiedReportAuthority,
    canonical_change_sha256,
    canonical_requirement_sha256,
)
from normshift.semantic_dimensions.errors import SemanticDimensionsError
from normshift.semantic_dimensions.models import (
    SEMANTIC_DIMENSIONS_KIND,
    SEMANTIC_DIMENSIONS_SCHEMA_VERSION,
    DimensionDisposition,
    NormalizedTextSpan,
    ObservationOrigin,
    ObservationVerification,
    RequirementEvidenceRef,
    SemanticChangeClass,
    SemanticChangeDimensions,
    SemanticChangeEvidence,
    SemanticDimension,
    SemanticDimensionsDocument,
    SemanticDimensionSlots,
    SemanticSlotChange,
    SemanticValueEvidence,
    StructuralForm,
    canonical_sha256,
    sha256_text,
)


def _section_core(path: str) -> str:
    parts = [strip_heading_number(part.strip()) for part in path.split(">")]
    return " > ".join(part.lower() for part in parts if part)


def _requirement_evidence(requirement: Requirement) -> RequirementEvidenceRef:
    return RequirementEvidenceRef(
        requirement_id=requirement.requirement_id,
        document_sha256=requirement.document_sha256,
        document_version=requirement.document_version,
        source_locator=requirement.source_locator,
        section_path=requirement.section_path,
        original_text_sha256=sha256_text(requirement.original_text),
        normalized_text_sha256=sha256_text(requirement.normalized_text),
        semantic_fingerprint=requirement.fingerprint,
        requirement_payload_sha256=canonical_requirement_sha256(requirement),
    )


def _canonical_value(dimension: SemanticDimension, raw: str) -> str:
    if dimension in {SemanticDimension.MODALITY, SemanticDimension.POLARITY}:
        return raw
    return editorial_normalize(raw)


def _observation(
    *,
    requirement: Requirement,
    dimension: SemanticDimension,
    raw_value: str | None,
) -> SemanticValueEvidence | None:
    if raw_value is None:
        return None
    value = _canonical_value(dimension, raw_value)
    if not value:
        return None
    payload = {
        "dimension": dimension.value,
        "value": value,
        "value_sha256": sha256_text(value),
        "origin": ObservationOrigin.REQUIREMENT_FIELD.value,
        "verification_status": ObservationVerification.VERIFIED_REQUIREMENT_FIELD.value,
        "source_text_sha256": sha256_text(requirement.normalized_text),
        "span_start": None,
        "span_end": None,
    }
    return SemanticValueEvidence(
        dimension=dimension,
        value=value,
        value_sha256=sha256_text(value),
        origin=ObservationOrigin.REQUIREMENT_FIELD,
        verification_status=ObservationVerification.VERIFIED_REQUIREMENT_FIELD,
        source_text_sha256=sha256_text(requirement.normalized_text),
        span_start=None,
        span_end=None,
        evidence_sha256=canonical_sha256(payload),
    )


def _span_observation(
    *,
    requirement: Requirement,
    dimension: SemanticDimension,
    span: NormalizedTextSpan | None,
) -> SemanticValueEvidence | None:
    if span is None:
        return None
    if span.end > len(requirement.normalized_text):
        raise SemanticDimensionsError(f"{dimension.value} span exceeds normalized requirement text")
    exact_excerpt = requirement.normalized_text[span.start : span.end]
    if not exact_excerpt or exact_excerpt != exact_excerpt.strip():
        raise SemanticDimensionsError(
            f"{dimension.value} span must select non-empty text without edge whitespace"
        )
    text = requirement.normalized_text
    if (
        span.start > 0
        and _is_token_character(text[span.start - 1])
        and _is_token_character(text[span.start])
    ) or (
        span.end < len(text)
        and _is_token_character(text[span.end - 1])
        and _is_token_character(text[span.end])
    ):
        raise SemanticDimensionsError(
            f"{dimension.value} span must not begin or end inside a token"
        )
    value = _canonical_value(dimension, exact_excerpt)
    if not value:
        raise SemanticDimensionsError(f"{dimension.value} span has no semantic content")
    payload = {
        "dimension": dimension.value,
        "value": value,
        "value_sha256": sha256_text(value),
        "origin": ObservationOrigin.NORMALIZED_TEXT_SPAN.value,
        "verification_status": ObservationVerification.ASSERTED_UNVERIFIED.value,
        "source_text_sha256": sha256_text(requirement.normalized_text),
        "span_start": span.start,
        "span_end": span.end,
    }
    return SemanticValueEvidence(
        dimension=dimension,
        value=value,
        value_sha256=sha256_text(value),
        origin=ObservationOrigin.NORMALIZED_TEXT_SPAN,
        verification_status=ObservationVerification.ASSERTED_UNVERIFIED,
        source_text_sha256=sha256_text(requirement.normalized_text),
        span_start=span.start,
        span_end=span.end,
        evidence_sha256=canonical_sha256(payload),
    )


def _is_token_character(value: str) -> bool:
    return value.isalnum() or value == "_"


def _validate_candidate_spans(
    *,
    side: str,
    object_span: NormalizedTextSpan | None,
    scope_span: NormalizedTextSpan | None,
) -> None:
    if object_span is None or scope_span is None:
        return
    if max(object_span.start, scope_span.start) < min(object_span.end, scope_span.end):
        raise SemanticDimensionsError(
            f"{side} object/scope candidate spans must not overlap or be reused"
        )


def _scalar_slot(
    dimension: SemanticDimension,
    old: SemanticValueEvidence | None,
    new: SemanticValueEvidence | None,
) -> SemanticSlotChange:
    if old is None or new is None:
        return SemanticSlotChange(
            dimension=dimension,
            disposition=DimensionDisposition.UNKNOWN,
            change_class=None,
            old=old,
            new=new,
            reason="At least one exact observation is unavailable; no change class is forced.",
        )
    if old.value == new.value:
        return SemanticSlotChange(
            dimension=dimension,
            disposition=DimensionDisposition.UNCHANGED,
            change_class=None,
            old=old,
            new=new,
            reason="Canonical old and new observations are equal.",
        )
    change_class = SemanticChangeClass(f"{dimension.value.upper()}_CHANGED")
    return SemanticSlotChange(
        dimension=dimension,
        disposition=DimensionDisposition.CHANGED,
        change_class=change_class,
        old=old,
        new=new,
        reason="Canonical old and new observations differ with exact evidence on both sides.",
    )


def _unverified_candidate_slot(
    dimension: SemanticDimension,
    old: SemanticValueEvidence | None,
    new: SemanticValueEvidence | None,
) -> SemanticSlotChange:
    return SemanticSlotChange(
        dimension=dimension,
        disposition=DimensionDisposition.UNKNOWN,
        change_class=None,
        old=old,
        new=new,
        reason=(
            "Caller-selected spans are retained only as unverified candidates; "
            "no semantic role or change class is inferred."
        ),
    )


def _transition_slot(
    dimension: SemanticDimension,
    old: SemanticValueEvidence | None,
    new: SemanticValueEvidence | None,
) -> SemanticSlotChange:
    prefix = dimension.value.upper()
    if old is None and new is None:
        return SemanticSlotChange(
            dimension=dimension,
            disposition=DimensionDisposition.UNCHANGED,
            change_class=None,
            old=None,
            new=None,
            reason="The deterministic extractor reports no value on either side.",
        )
    if old is None:
        return SemanticSlotChange(
            dimension=dimension,
            disposition=DimensionDisposition.ADDED,
            change_class=SemanticChangeClass(f"{prefix}_ADDED"),
            old=None,
            new=new,
            reason="A canonical value is present only on the new requirement.",
        )
    if new is None:
        return SemanticSlotChange(
            dimension=dimension,
            disposition=DimensionDisposition.REMOVED,
            change_class=SemanticChangeClass(f"{prefix}_REMOVED"),
            old=old,
            new=None,
            reason="A canonical value is present only on the old requirement.",
        )
    if old.value == new.value:
        return SemanticSlotChange(
            dimension=dimension,
            disposition=DimensionDisposition.UNCHANGED,
            change_class=None,
            old=old,
            new=new,
            reason="Canonical old and new observations are equal.",
        )
    return SemanticSlotChange(
        dimension=dimension,
        disposition=DimensionDisposition.AMBIGUOUS,
        change_class=None,
        old=old,
        new=new,
        reason=(
            "Both canonical values changed, but the frozen policy has no forced "
            f"{prefix}_CHANGED class."
        ),
    )


def _not_applicable_slots() -> SemanticDimensionSlots:
    def slot(dimension: SemanticDimension) -> SemanticSlotChange:
        return SemanticSlotChange(
            dimension=dimension,
            disposition=DimensionDisposition.NOT_APPLICABLE,
            change_class=None,
            old=None,
            new=None,
            reason="The primary change has no old/new pair for dimension comparison.",
        )

    return SemanticDimensionSlots(
        actor=slot(SemanticDimension.ACTOR),
        action=slot(SemanticDimension.ACTION),
        object=slot(SemanticDimension.OBJECT),
        scope=slot(SemanticDimension.SCOPE),
        modality=slot(SemanticDimension.MODALITY),
        polarity=slot(SemanticDimension.POLARITY),
        condition=slot(SemanticDimension.CONDITION),
        exception=slot(SemanticDimension.EXCEPTION),
    )


def _paired_slots(
    *,
    old: Requirement,
    new: Requirement,
    old_object_span: NormalizedTextSpan | None,
    new_object_span: NormalizedTextSpan | None,
    old_scope_span: NormalizedTextSpan | None,
    new_scope_span: NormalizedTextSpan | None,
) -> SemanticDimensionSlots:
    _validate_candidate_spans(
        side="old",
        object_span=old_object_span,
        scope_span=old_scope_span,
    )
    _validate_candidate_spans(
        side="new",
        object_span=new_object_span,
        scope_span=new_scope_span,
    )
    actor = _scalar_slot(
        SemanticDimension.ACTOR,
        _observation(requirement=old, dimension=SemanticDimension.ACTOR, raw_value=old.actor),
        _observation(requirement=new, dimension=SemanticDimension.ACTOR, raw_value=new.actor),
    )
    action = _scalar_slot(
        SemanticDimension.ACTION,
        _observation(requirement=old, dimension=SemanticDimension.ACTION, raw_value=old.action),
        _observation(requirement=new, dimension=SemanticDimension.ACTION, raw_value=new.action),
    )
    object_change = _unverified_candidate_slot(
        SemanticDimension.OBJECT,
        _span_observation(
            requirement=old,
            dimension=SemanticDimension.OBJECT,
            span=old_object_span,
        ),
        _span_observation(
            requirement=new,
            dimension=SemanticDimension.OBJECT,
            span=new_object_span,
        ),
    )
    scope = _unverified_candidate_slot(
        SemanticDimension.SCOPE,
        _span_observation(
            requirement=old,
            dimension=SemanticDimension.SCOPE,
            span=old_scope_span,
        ),
        _span_observation(
            requirement=new,
            dimension=SemanticDimension.SCOPE,
            span=new_scope_span,
        ),
    )
    modality = _scalar_slot(
        SemanticDimension.MODALITY,
        _observation(
            requirement=old,
            dimension=SemanticDimension.MODALITY,
            raw_value=old.modality.value,
        ),
        _observation(
            requirement=new,
            dimension=SemanticDimension.MODALITY,
            raw_value=new.modality.value,
        ),
    )
    polarity = _scalar_slot(
        SemanticDimension.POLARITY,
        _observation(
            requirement=old,
            dimension=SemanticDimension.POLARITY,
            raw_value=old.polarity.value,
        ),
        _observation(
            requirement=new,
            dimension=SemanticDimension.POLARITY,
            raw_value=new.polarity.value,
        ),
    )
    condition = _transition_slot(
        SemanticDimension.CONDITION,
        _observation(
            requirement=old,
            dimension=SemanticDimension.CONDITION,
            raw_value=old.condition,
        ),
        _observation(
            requirement=new,
            dimension=SemanticDimension.CONDITION,
            raw_value=new.condition,
        ),
    )
    exception = _transition_slot(
        SemanticDimension.EXCEPTION,
        _observation(
            requirement=old,
            dimension=SemanticDimension.EXCEPTION,
            raw_value=old.exception,
        ),
        _observation(
            requirement=new,
            dimension=SemanticDimension.EXCEPTION,
            raw_value=new.exception,
        ),
    )
    return SemanticDimensionSlots(
        actor=actor,
        action=action,
        object=object_change,
        scope=scope,
        modality=modality,
        polarity=polarity,
        condition=condition,
        exception=exception,
    )


def _structural_form(old: Requirement | None, new: Requirement | None) -> StructuralForm:
    if old is None or new is None:
        return StructuralForm.NONE
    moved = _section_core(old.section_path) != _section_core(new.section_path)
    rewritten = editorial_normalize(old.normalized_text) != editorial_normalize(new.normalized_text)
    if moved and rewritten:
        return StructuralForm.MOVED_AND_REWRITTEN
    if moved:
        return StructuralForm.MOVE_ONLY
    if rewritten:
        return StructuralForm.REWRITE_ONLY
    return StructuralForm.NONE


def _derived_classes(
    structural_form: StructuralForm, slots: Iterable[SemanticSlotChange]
) -> list[SemanticChangeClass]:
    classes: set[SemanticChangeClass] = set()
    if structural_form is not StructuralForm.NONE:
        classes.add(SemanticChangeClass(structural_form.value))
    classes.update(slot.change_class for slot in slots if slot.change_class is not None)
    return sorted(classes, key=lambda item: item.value)


def build_semantic_dimensions(
    *,
    authority: VerifiedReportAuthority,
    primary_change_id: str,
    old_object_span: NormalizedTextSpan | None = None,
    new_object_span: NormalizedTextSpan | None = None,
    old_scope_span: NormalizedTextSpan | None = None,
    new_scope_span: NormalizedTextSpan | None = None,
) -> SemanticDimensionsDocument:
    """Build dimensions from an independently anchored, verified primary report.

    Object and scope spans are retained as explicitly unverified candidates.
    They remain ``UNKNOWN`` and cannot emit a semantic class without a future,
    independently anchored semantic-role authority.
    """
    change, old, new = authority.resolve(primary_change_id)

    if old is None or new is None:
        if any(
            span is not None
            for span in (
                old_object_span,
                new_object_span,
                old_scope_span,
                new_scope_span,
            )
        ):
            raise SemanticDimensionsError("unpaired changes cannot carry comparison spans")
        slots = _not_applicable_slots()
    else:
        slots = _paired_slots(
            old=old,
            new=new,
            old_object_span=old_object_span,
            new_object_span=new_object_span,
            old_scope_span=old_scope_span,
            new_scope_span=new_scope_span,
        )

    structural_form = _structural_form(old, new)
    change_classes = _derived_classes(structural_form, slots.ordered())
    evidence = SemanticChangeEvidence(
        authority_kind="FULL_REPORT_REPLAY",
        authority_id=authority.authority_id,
        authority_report_sha256=authority.expected_report_file_sha256,
        verification_receipt_sha256=authority.expected_receipt_sha256,
        verification_receipt_payload_sha256=authority.receipt.receipt_payload_sha256,
        primary_change_id=change.change_id,
        primary_classification=change.classification,
        primary_change_sha256=canonical_change_sha256(change),
        primary_evidence_hashes=change.evidence_hashes,
        old_requirement=_requirement_evidence(old) if old is not None else None,
        new_requirement=_requirement_evidence(new) if new is not None else None,
    )
    semantic_payload = {
        "structural_form": structural_form.value,
        "change_classes": [item.value for item in change_classes],
        "slots": slots.model_dump(mode="json"),
        "evidence": evidence.model_dump(mode="json"),
    }
    semantic_change = SemanticChangeDimensions(
        semantic_change_id=canonical_sha256(semantic_payload),
        structural_form=structural_form,
        change_classes=change_classes,
        slots=slots,
        evidence=evidence,
    )
    document_payload = {
        "schema_version": "1.0.0",
        "kind": "normshift-semantic-change-dimensions",
        "change": semantic_change.model_dump(mode="json"),
    }
    return SemanticDimensionsDocument(
        schema_version=SEMANTIC_DIMENSIONS_SCHEMA_VERSION,
        kind=SEMANTIC_DIMENSIONS_KIND,
        change=semantic_change,
        integrity_sha256=canonical_sha256(document_payload),
    )


def verify_semantic_dimensions(
    document: SemanticDimensionsDocument,
    *,
    authority: VerifiedReportAuthority,
    primary_change_id: str,
    old_object_span: NormalizedTextSpan | None = None,
    new_object_span: NormalizedTextSpan | None = None,
    old_scope_span: NormalizedTextSpan | None = None,
    new_scope_span: NormalizedTextSpan | None = None,
) -> None:
    """Replay exact source bindings and reject any rehashed semantic forgery."""
    expected = build_semantic_dimensions(
        authority=authority,
        primary_change_id=primary_change_id,
        old_object_span=old_object_span,
        new_object_span=new_object_span,
        old_scope_span=old_scope_span,
        new_scope_span=new_scope_span,
    )
    submitted = canonical_json_bytes(document.model_dump(mode="json"))
    replayed = canonical_json_bytes(expected.model_dump(mode="json"))
    if submitted != replayed:
        raise SemanticDimensionsError("semantic dimension document differs from exact replay")
