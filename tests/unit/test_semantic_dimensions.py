"""Synthetic coverage for the independent M2 semantic-dimension foundation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import replace
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

import normshift.semantic_dimensions.authority as authority_module
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.extract.extractor import fingerprint_requirement
from normshift.model.types import (
    Change,
    ChangeClassification,
    IntegrityEnvelope,
    Modality,
    Polarity,
    ProfileName,
    Report,
    Requirement,
)
from normshift.pipeline import run_diff
from normshift.semantic_dimensions import (
    DimensionDisposition,
    FullVerificationReceipt,
    NormalizedTextSpan,
    ObservationVerification,
    SemanticChangeClass,
    SemanticDimensionsDocument,
    SemanticDimensionsError,
    StructuralForm,
    VerifiedReportAuthority,
    VerifiedSourceBinding,
    bind_verified_report_file,
    build_semantic_dimensions,
    canonical_change_sha256,
    canonical_requirement_sha256,
    create_full_verification_receipt,
    full_verification_receipt_json_bytes,
    full_verification_receipt_json_schema,
    parse_full_verification_receipt_bytes,
    parse_semantic_dimensions_bytes,
    semantic_dimensions_json_bytes,
    semantic_dimensions_json_schema,
    verify_semantic_dimensions,
)
from normshift.semantic_dimensions.models import canonical_sha256
from normshift.semantic_dimensions.serialization import MAX_SEMANTIC_DIMENSIONS_BYTES

ROOT = Path(__file__).resolve().parents[2]
_TEMPORARY_AUTHORITIES: list[TemporaryDirectory[str]] = []


def _req(
    rid: str,
    text: str,
    *,
    section: str = "1. Processing",
    modality: Modality = Modality.MUST,
    actor: str | None = "Clients",
    action: str | None = "send frames",
    condition: str | None = None,
    exception: str | None = None,
    document_sha256: str | None = None,
) -> Requirement:
    polarity = (
        Polarity.NEGATIVE
        if modality in {Modality.MUST_NOT, Modality.SHOULD_NOT}
        else Polarity.AFFIRMATIVE
    )
    fingerprint = fingerprint_requirement(
        text,
        modality.value,
        actor,
        action,
        condition,
        exception,
    )
    return Requirement(
        requirement_id=rid,
        document_sha256=document_sha256 or ("a" if rid.startswith("old") else "b") * 64,
        document_version="1" if rid.startswith("old") else "2",
        section_path=section,
        source_locator=f"id:{rid}",
        original_text=text,
        normalized_text=text,
        modality=modality,
        polarity=polarity,
        actor=actor,
        action=action,
        condition=condition,
        exception=exception,
        confidence=0.9,
        extractor_version="test-v1",
        fingerprint=fingerprint,
        structural_index=0,
    )


def _report(
    old: Requirement | None,
    new: Requirement | None,
) -> tuple[Report, Path, Path]:
    holder = TemporaryDirectory(prefix="normshift-semantic-authority-")
    _TEMPORARY_AUTHORITIES.append(holder)
    source_root = Path(holder.name)
    old_path = source_root / "old.html"
    new_path = source_root / "new.html"
    report_path = source_root / "report.json"

    def source_html(requirement: Requirement | None) -> str:
        if requirement is None:
            return "<html><body><p>Informative text only.</p></body></html>"
        return (
            "<html><body>"
            f"<h1>{escape(requirement.section_path)}</h1>"
            f"<p>{escape(requirement.original_text)}</p>"
            "</body></html>"
        )

    old_path.write_text(source_html(old), encoding="utf-8")
    new_path.write_text(source_html(new), encoding="utf-8")
    report = run_diff(
        old_path,
        new_path,
        profile=ProfileName.RFC2119,
        source_root=source_root,
        json_out=report_path,
    )
    return report, report_path, source_root


def _bind_report(report_path: Path, source_root: Path) -> VerifiedReportAuthority:
    receipt = create_full_verification_receipt(report_path, source_root=source_root)
    receipt_bytes = full_verification_receipt_json_bytes(receipt)
    return bind_verified_report_file(
        report_path,
        source_root=source_root,
        receipt_bytes=receipt_bytes,
        expected_report_file_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        expected_receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
    )


def _reseal_receipt_source_refs(
    receipt: FullVerificationReceipt,
    *,
    old_ref: str,
    new_ref: str,
) -> bytes:
    data = receipt.model_dump(mode="json")
    data["old_source"]["source_ref"] = old_ref
    data["new_source"]["source_ref"] = new_ref
    payload = {key: value for key, value in data.items() if key != "receipt_payload_sha256"}
    data["receipt_payload_sha256"] = canonical_sha256(payload)
    return canonical_json_bytes(data)


def _make_directory_alias(*, target: Path, alias: Path) -> None:
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        checker = getattr(alias, "is_junction", None)
        assert checker is not None and checker()
    else:
        alias.symlink_to(target, target_is_directory=True)
        assert alias.is_symlink()


def _remove_directory_alias(alias: Path) -> None:
    if os.name == "nt":
        alias.rmdir()
    else:
        alias.unlink()


def _authority(
    old: Requirement | None,
    new: Requirement | None,
) -> tuple[VerifiedReportAuthority, Change]:
    report, report_path, source_root = _report(old, new)
    authority = _bind_report(report_path, source_root)
    candidates = [
        change
        for change in report.changes
        if (old is None or change.old_requirement_id is not None)
        and (new is None or change.new_requirement_id is not None)
    ]
    if len(candidates) != 1:
        raise AssertionError(
            "synthetic source must produce exactly one requested primary change; "
            f"got {[item.classification.value for item in report.changes]}"
        )
    return authority, candidates[0]


def _refresh_report_integrity(report: Report) -> Report:
    data = report.model_dump(mode="json")
    return report.model_copy(
        update={
            "integrity": IntegrityEnvelope(
                alg="sha256",
                content_sha256=integrity_payload_hash(data),
            )
        }
    )


def _span(requirement: Requirement, exact: str) -> NormalizedTextSpan:
    start = requirement.normalized_text.index(exact)
    return NormalizedTextSpan(start=start, end=start + len(exact))


@pytest.mark.parametrize(
    ("new_text", "new_section", "expected"),
    [
        ("Clients MUST send frames.", "1. Processing", StructuralForm.NONE),
        ("Clients MUST send frames.", "2. Transport", StructuralForm.MOVE_ONLY),
        (
            "Clients MUST send frames promptly.",
            "1. Processing",
            StructuralForm.REWRITE_ONLY,
        ),
        (
            "Clients MUST send frames promptly.",
            "2. Transport",
            StructuralForm.MOVED_AND_REWRITTEN,
        ),
    ],
)
def test_structural_form_is_orthogonal_and_exact(
    new_text: str, new_section: str, expected: StructuralForm
) -> None:
    old = _req("old-1", "Clients MUST send frames.")
    new = _req("new-1", new_text, section=new_section)
    authority, change = _authority(old, new)
    primary_before = change.model_dump(mode="json")

    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )

    assert document.change.structural_form is expected
    assert change.model_dump(mode="json") == primary_before
    assert document.change.evidence.primary_classification is change.classification
    structural_classes = {
        item
        for item in document.change.change_classes
        if item
        in {
            SemanticChangeClass.MOVE_ONLY,
            SemanticChangeClass.REWRITE_ONLY,
            SemanticChangeClass.MOVED_AND_REWRITTEN,
        }
    }
    if expected is StructuralForm.NONE:
        assert structural_classes == set()
    else:
        assert structural_classes == {SemanticChangeClass(expected.value)}


def test_verified_slots_and_unverified_candidates_are_independent() -> None:
    old = _req(
        "old-many",
        "Clients MUST send frames for origin A when connected unless offline.",
        actor="Clients",
        action="send frames",
        condition="when connected unless offline",
        exception="unless offline",
    )
    new = _req(
        "new-many",
        "Servers MUST NOT send packets for origin B when connected unless offline.",
        actor="Servers",
        action="send packets",
        modality=Modality.MUST_NOT,
        condition="when connected unless offline",
        exception="unless offline",
    )
    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
        old_object_span=_span(old, "frames"),
        new_object_span=_span(new, "packets"),
        old_scope_span=_span(old, "origin A"),
        new_scope_span=_span(new, "origin B"),
    )
    slots = document.change.slots
    expected = {
        "actor": SemanticChangeClass.ACTOR_CHANGED,
        "action": SemanticChangeClass.ACTION_CHANGED,
        "modality": SemanticChangeClass.MODALITY_CHANGED,
        "polarity": SemanticChangeClass.POLARITY_CHANGED,
    }
    for field_name, change_class in expected.items():
        slot = getattr(slots, field_name)
        assert slot.disposition is DimensionDisposition.CHANGED
        assert slot.change_class is change_class
        assert change_class in document.change.change_classes

    for field_name in ("object", "scope"):
        slot = getattr(slots, field_name)
        assert slot.disposition is DimensionDisposition.UNKNOWN
        assert slot.change_class is None
        assert slot.old is not None
        assert slot.new is not None
        assert slot.old.verification_status is ObservationVerification.ASSERTED_UNVERIFIED
        assert slot.new.verification_status is ObservationVerification.ASSERTED_UNVERIFIED
    assert SemanticChangeClass.OBJECT_CHANGED not in document.change.change_classes
    assert SemanticChangeClass.SCOPE_CHANGED not in document.change.change_classes

    assert slots.condition.disposition is DimensionDisposition.UNCHANGED
    assert slots.condition.change_class is None
    assert slots.exception.disposition is DimensionDisposition.UNCHANGED
    assert slots.exception.change_class is None
    assert document.change.structural_form is StructuralForm.REWRITE_ONLY


@pytest.mark.parametrize(
    ("field_name", "old_value", "new_value", "disposition", "change_class"),
    [
        (
            "condition",
            None,
            "when connected",
            DimensionDisposition.ADDED,
            SemanticChangeClass.CONDITION_ADDED,
        ),
        (
            "condition",
            "when connected",
            None,
            DimensionDisposition.REMOVED,
            SemanticChangeClass.CONDITION_REMOVED,
        ),
        (
            "exception",
            None,
            "unless offline",
            DimensionDisposition.ADDED,
            SemanticChangeClass.EXCEPTION_ADDED,
        ),
        (
            "exception",
            "unless offline",
            None,
            DimensionDisposition.REMOVED,
            SemanticChangeClass.EXCEPTION_REMOVED,
        ),
    ],
)
def test_condition_and_exception_use_only_frozen_transition_classes(
    field_name: str,
    old_value: str | None,
    new_value: str | None,
    disposition: DimensionDisposition,
    change_class: SemanticChangeClass,
) -> None:
    values: dict[str, tuple[str | None, str | None]] = {
        "condition": (None, None),
        "exception": (None, None),
    }
    values[field_name] = (old_value, new_value)

    def requirement_text(condition: str | None, exception: str | None) -> str:
        suffix = " ".join(item for item in (condition, exception) if item)
        return f"Clients MUST send frames{' ' + suffix if suffix else ''}."

    old = _req(
        "old-transition",
        requirement_text(values["condition"][0], values["exception"][0]),
        condition=values["condition"][0],
        exception=values["exception"][0],
    )
    new = _req(
        "new-transition",
        requirement_text(values["condition"][1], values["exception"][1]),
        condition=values["condition"][1],
        exception=values["exception"][1],
    )

    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )
    slot = getattr(document.change.slots, field_name)
    assert slot.disposition is disposition
    assert slot.change_class is change_class
    assert change_class in document.change.change_classes


def test_missing_object_scope_evidence_stays_unknown() -> None:
    old = _req("old-unknown", "Clients MUST send frames for origin A.")
    new = _req("new-unknown", "Clients MUST send packets for origin B.")

    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )

    assert document.change.slots.object.disposition is DimensionDisposition.UNKNOWN
    assert document.change.slots.scope.disposition is DimensionDisposition.UNKNOWN
    assert SemanticChangeClass.OBJECT_CHANGED not in document.change.change_classes
    assert SemanticChangeClass.SCOPE_CHANGED not in document.change.change_classes


@pytest.mark.parametrize("keep_side", ["old", "new"])
def test_add_remove_no_pair_has_no_forced_dimension_classes(keep_side: str) -> None:
    requirement = _req(
        "old-unpaired" if keep_side == "old" else "new-unpaired",
        "Clients MUST send frames.",
    )
    old = requirement if keep_side == "old" else None
    new = requirement if keep_side == "new" else None
    authority, change = _authority(old, new)

    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )

    assert document.change.structural_form is StructuralForm.NONE
    assert document.change.change_classes == []
    assert all(
        slot.disposition is DimensionDisposition.NOT_APPLICABLE
        for slot in document.change.slots.ordered()
    )


def test_canonical_serialization_schema_and_replay_are_deterministic() -> None:
    old = _req("old-deterministic", "Clients MUST send frames for origin A.")
    new = _req(
        "new-deterministic",
        "Clients MUST send packets for origin B.",
        section="2. Transport",
        action="send packets",
    )
    authority, change = _authority(old, new)
    kwargs = {
        "authority": authority,
        "primary_change_id": change.change_id,
        "old_object_span": _span(old, "frames"),
        "new_object_span": _span(new, "packets"),
        "old_scope_span": _span(old, "origin A"),
        "new_scope_span": _span(new, "origin B"),
    }
    first = build_semantic_dimensions(**kwargs)
    second = build_semantic_dimensions(**kwargs)
    raw = semantic_dimensions_json_bytes(first)

    assert raw == semantic_dimensions_json_bytes(second)
    assert parse_semantic_dimensions_bytes(raw) == first
    verify_semantic_dimensions(first, **kwargs)
    assert first.change.evidence.primary_change_sha256 == canonical_change_sha256(change)
    assert first.change.evidence.authority_kind == "FULL_REPORT_REPLAY"
    assert first.change.evidence.authority_report_sha256 == authority.expected_report_file_sha256
    assert first.change.evidence.verification_receipt_sha256 == authority.expected_receipt_sha256
    assert parse_full_verification_receipt_bytes(authority.receipt_bytes) == authority.receipt
    assert first.change.evidence.old_requirement is not None
    assert first.change.evidence.new_requirement is not None
    authoritative_old = authority.report.old_requirements[0]
    authoritative_new = authority.report.new_requirements[0]
    assert (
        first.change.evidence.old_requirement.requirement_payload_sha256
        == canonical_requirement_sha256(authoritative_old)
    )
    assert (
        first.change.evidence.new_requirement.requirement_payload_sha256
        == canonical_requirement_sha256(authoritative_new)
    )

    schema = semantic_dimensions_json_schema()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(json.loads(raw))
    generated = canonical_json_bytes(schema)
    repository_schema = ROOT / "schemas" / "semantic_change_dimensions_v1.schema.json"
    assert generated == repository_schema.read_bytes()
    assert (
        generated
        == (
            ROOT / "src" / "normshift" / "schemas" / "semantic_change_dimensions_v1.schema.json"
        ).read_bytes()
    )

    receipt_schema = full_verification_receipt_json_schema()
    Draft202012Validator.check_schema(receipt_schema)
    Draft202012Validator(receipt_schema).validate(json.loads(authority.receipt_bytes))
    assert receipt_schema["additionalProperties"] is False
    definitions = receipt_schema["$defs"]
    assert isinstance(definitions, dict)
    assert all(
        definition.get("additionalProperties") is False
        for definition in definitions.values()
    )
    generated_receipt_schema = canonical_json_bytes(receipt_schema)
    receipt_schema_name = "full_verification_receipt_v1.schema.json"
    assert generated_receipt_schema == (ROOT / "schemas" / receipt_schema_name).read_bytes()
    assert generated_receipt_schema == (
        ROOT / "src" / "normshift" / "schemas" / receipt_schema_name
    ).read_bytes()
    invalid_ref_receipt = json.loads(authority.receipt_bytes)
    invalid_ref_receipt["old_source"]["source_ref"] = "../old.html"
    assert list(Draft202012Validator(receipt_schema).iter_errors(invalid_ref_receipt))
    invalid_digest_receipt = json.loads(authority.receipt_bytes)
    invalid_digest_receipt["report_file_sha256"] = "not-a-sha256"
    assert list(Draft202012Validator(receipt_schema).iter_errors(invalid_digest_receipt))


def test_semantic_serialization_enforces_the_same_boundary_as_parsing() -> None:
    old = _req("old-serialization-boundary", "Clients MUST send frames.")
    new = _req("new-serialization-boundary", "Clients MUST send frames promptly.")
    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )

    def with_actor_reason(reason: str) -> SemanticDimensionsDocument:
        data = document.model_dump()
        data["change"]["slots"]["actor"]["reason"] = reason
        change_payload = {
            key: value for key, value in data["change"].items() if key != "semantic_change_id"
        }
        data["change"]["semantic_change_id"] = canonical_sha256(change_payload)
        document_payload = {
            key: value for key, value in data.items() if key != "integrity_sha256"
        }
        data["integrity_sha256"] = canonical_sha256(document_payload)
        return SemanticDimensionsDocument.model_validate(data)

    baseline = len(semantic_dimensions_json_bytes(with_actor_reason("x")))
    at_limit = with_actor_reason("x" * (MAX_SEMANTIC_DIMENSIONS_BYTES - baseline + 1))
    assert len(semantic_dimensions_json_bytes(at_limit)) == MAX_SEMANTIC_DIMENSIONS_BYTES
    over_limit = with_actor_reason(
        "x" * (MAX_SEMANTIC_DIMENSIONS_BYTES - baseline + 2)
    )
    with pytest.raises(SemanticDimensionsError, match="exceeds size limit"):
        semantic_dimensions_json_bytes(over_limit)


@pytest.mark.parametrize(
    "source_ref",
    [
        "../old.html",
        "/old.html",
        "C:/old.html",
        "old\\alias.html",
        "old//alias.html",
        "old/./alias.html",
        "old/../alias.html",
        "https://example.invalid/old.html",
    ],
)
def test_verified_source_binding_rejects_nonportable_aliases(source_ref: str) -> None:
    with pytest.raises(ValidationError, match="canonical portable ref"):
        VerifiedSourceBinding(
            source_ref=source_ref,
            content_sha256="a" * 64,
            byte_length=1,
            document_version="1",
            source_ref_mode="source_root_relative",
        )


@pytest.mark.parametrize(
    ("old_ref", "new_ref", "message"),
    [
        ("../old.html", "new.html", "canonical portable ref"),
        ("Specs/A.html", "specs/a.html", "cross-platform aliases"),
    ],
)
def test_resealed_receipt_rejects_unsafe_or_cross_platform_alias_refs(
    old_ref: str,
    new_ref: str,
    message: str,
) -> None:
    old = _req("old-receipt-ref", "Clients MUST send frames.")
    new = _req("new-receipt-ref", "Clients MUST send frames promptly.")
    _report_value, report_path, source_root = _report(old, new)
    receipt = create_full_verification_receipt(report_path, source_root=source_root)

    with pytest.raises(SemanticDimensionsError, match=message):
        parse_full_verification_receipt_bytes(
            _reseal_receipt_source_refs(receipt, old_ref=old_ref, new_ref=new_ref)
        )


@pytest.mark.parametrize(
    ("old_ref", "new_ref"),
    [
        pytest.param("Specs/\N{KELVIN SIGN}.html", "specs/k.html", id="nfkc-kelvin"),
        pytest.param(
            "specs/Caf\N{LATIN SMALL LETTER E WITH ACUTE}.html",
            "specs/Cafe\N{COMBINING ACUTE ACCENT}.html",
            id="nfkc-composed-decomposed",
        ),
    ],
)
def test_resealed_receipt_rejects_nfkc_source_ref_aliases(
    old_ref: str,
    new_ref: str,
) -> None:
    old = _req("old-receipt-nfkc", "Clients MUST send frames.")
    new = _req("new-receipt-nfkc", "Clients MUST send frames promptly.")
    _report_value, report_path, source_root = _report(old, new)
    receipt = create_full_verification_receipt(report_path, source_root=source_root)

    with pytest.raises(SemanticDimensionsError, match="cross-platform aliases"):
        parse_full_verification_receipt_bytes(
            _reseal_receipt_source_refs(receipt, old_ref=old_ref, new_ref=new_ref)
        )


@pytest.mark.parametrize("oversize_target", ["report", "source"])
def test_authority_oversize_preflight_runs_before_full_verifier(
    oversize_target: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _req("old-oversize", "Clients MUST send frames.")
    new = _req("new-oversize", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    if oversize_target == "report":
        monkeypatch.setattr(
            authority_module,
            "MAX_AUTHORITY_REPORT_BYTES",
            report_path.stat().st_size - 1,
        )
    else:
        old_source = source_root / report.old_document.path
        monkeypatch.setattr(
            authority_module,
            "MAX_AUTHORITY_SOURCE_BYTES",
            old_source.stat().st_size - 1,
        )

    def unexpected_verifier(*args: object, **kwargs: object) -> None:
        raise AssertionError("FULL verifier ran before bounded preflight")

    monkeypatch.setattr(authority_module, "verify_report_file", unexpected_verifier)
    with pytest.raises(SemanticDimensionsError, match="exceeds size limit"):
        create_full_verification_receipt(report_path, source_root=source_root)


@pytest.mark.parametrize("observed_argument", ["report_path", "source_root"])
def test_full_verifier_receives_only_isolated_snapshot_paths(
    observed_argument: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _req("old-isolated-snapshot", "Clients MUST send frames.")
    new = _req("new-isolated-snapshot", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    original_source_root = source_root
    original_verifier = authority_module.verify_report_file
    calls = 0

    def observing_verifier(
        path: Path,
        *,
        source_root: Path | None = None,
        old_source: Path | None = None,
        new_source: Path | None = None,
        require_sources: bool = True,
    ) -> object:
        nonlocal calls
        calls += 1
        assert source_root is not None
        observed = path if observed_argument == "report_path" else source_root
        original = (
            report_path
            if observed_argument == "report_path"
            else original_source_root
        )
        assert observed.resolve() != original.resolve()
        assert not observed.samefile(original)
        assert not observed.resolve().is_relative_to(original_source_root.resolve())
        assert path.parent == source_root.parent
        assert path.read_bytes() == report_path.read_bytes()
        for snapshot in (report.old_document, report.new_document):
            replay_source = source_root / snapshot.path
            original_source = original_source_root / snapshot.path
            assert replay_source.read_bytes() == original_source.read_bytes()
            assert not replay_source.samefile(original_source)
        return original_verifier(
            path,
            source_root=source_root,
            old_source=old_source,
            new_source=new_source,
            require_sources=require_sources,
        )

    monkeypatch.setattr(authority_module, "verify_report_file", observing_verifier)
    create_full_verification_receipt(report_path, source_root=original_source_root)
    assert calls == 1


@pytest.mark.parametrize("race_target", ["report", "source"])
def test_authority_rejects_report_or_source_race_across_full_verifier(
    race_target: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _req("old-race", "Clients MUST send frames.")
    new = _req("new-race", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    target = (
        report_path
        if race_target == "report"
        else source_root / report.old_document.path
    )
    original_raw = target.read_bytes()
    mutated_raw = (
        original_raw + b" "
        if race_target == "report"
        else original_raw.replace(b"Clients", b"Servers", 1)
    )
    assert mutated_raw != original_raw
    if race_target == "source":
        assert len(mutated_raw) == len(original_raw)
    original_verifier = authority_module.verify_report_file

    def racing_verifier(*args: object, **kwargs: object) -> object:
        result = original_verifier(*args, **kwargs)
        target.write_bytes(mutated_raw)
        return result

    monkeypatch.setattr(authority_module, "verify_report_file", racing_verifier)
    with pytest.raises(SemanticDimensionsError):
        create_full_verification_receipt(report_path, source_root=source_root)


def test_authority_rejects_same_length_source_mutation_with_restored_mtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _req("old-restored-mtime", "Clients MUST send frames.")
    new = _req("new-restored-mtime", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    target = source_root / report.old_document.path
    original_raw = target.read_bytes()
    original_stat = target.stat()
    mutated_raw = original_raw.replace(b"Clients", b"Servers", 1)
    assert mutated_raw != original_raw
    assert len(mutated_raw) == len(original_raw)
    original_verifier = authority_module.verify_report_file

    def racing_verifier(*args: object, **kwargs: object) -> object:
        result = original_verifier(*args, **kwargs)
        target.write_bytes(mutated_raw)
        os.utime(
            target,
            ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
        )
        assert target.stat().st_mtime_ns == original_stat.st_mtime_ns
        return result

    monkeypatch.setattr(authority_module, "verify_report_file", racing_verifier)
    with pytest.raises(
        SemanticDimensionsError,
        match="post-verifier recheck: old source SHA differs from report",
    ):
        create_full_verification_receipt(report_path, source_root=source_root)


@pytest.mark.parametrize("replacement_target", ["report", "source"])
def test_authority_rejects_same_bytes_atomic_identity_replacement(
    replacement_target: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _req("old-atomic-replacement", "Clients MUST send frames.")
    new = _req("new-atomic-replacement", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    target = (
        report_path
        if replacement_target == "report"
        else source_root / report.old_document.path
    )
    original_raw = target.read_bytes()
    original_stat = target.stat()
    replacement = source_root / f".{replacement_target}-identity-replacement"
    replacement.write_bytes(original_raw)
    os.utime(
        replacement,
        ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
    )
    original_verifier = authority_module.verify_report_file

    def racing_verifier(*args: object, **kwargs: object) -> object:
        result = original_verifier(*args, **kwargs)
        os.replace(replacement, target)
        replaced_stat = target.stat()
        assert target.read_bytes() == original_raw
        assert replaced_stat.st_size == original_stat.st_size
        assert replaced_stat.st_mtime_ns == original_stat.st_mtime_ns
        assert (replaced_stat.st_dev, replaced_stat.st_ino) != (
            original_stat.st_dev,
            original_stat.st_ino,
        )
        return result

    monkeypatch.setattr(authority_module, "verify_report_file", racing_verifier)
    with pytest.raises(
        SemanticDimensionsError,
        match="changed across FULL verifier replay",
    ):
        create_full_verification_receipt(report_path, source_root=source_root)


def test_authority_rejects_directory_alias_or_windows_junction_source_root(
    tmp_path: Path,
) -> None:
    old = _req("old-root-alias", "Clients MUST send frames.")
    new = _req("new-root-alias", "Clients MUST send frames promptly.")
    _report_value, report_path, source_root = _report(old, new)
    alias = tmp_path / "source-root-alias"
    _make_directory_alias(target=source_root, alias=alias)
    try:
        with pytest.raises(
            SemanticDimensionsError,
            match="source_root must not be a symlink or junction",
        ):
            create_full_verification_receipt(report_path, source_root=alias)
    finally:
        _remove_directory_alias(alias)


@pytest.mark.parametrize("alias_target", ["report", "source"])
def test_authority_preflight_rejects_hard_link_aliases(
    alias_target: str,
) -> None:
    old = _req("old-hard-link", "Clients MUST send frames.")
    new = _req("new-hard-link", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    target = (
        report_path
        if alias_target == "report"
        else source_root / report.old_document.path
    )
    alias = source_root / f"{alias_target}-alias"
    try:
        os.link(target, alias)
    except OSError as exc:
        pytest.skip(f"hard links unavailable on this filesystem: {exc}")

    with pytest.raises(SemanticDimensionsError, match="hard-link aliases"):
        create_full_verification_receipt(report_path, source_root=source_root)


def test_fake_hex_and_literal_string_anchors_cannot_construct_authority() -> None:
    old = _req("old-fake-anchor", "Clients MUST send frames.")
    new = _req("new-fake-anchor", "Clients MUST send frames promptly.")
    _report_value, report_path, source_root = _report(old, new)
    receipt = create_full_verification_receipt(report_path, source_root=source_root)
    receipt_bytes = full_verification_receipt_json_bytes(receipt)
    report_sha256 = hashlib.sha256(report_path.read_bytes()).hexdigest()

    with pytest.raises(SemanticDimensionsError, match="receipt bytes differ"):
        bind_verified_report_file(
            report_path,
            source_root=source_root,
            receipt_bytes=receipt_bytes,
            expected_report_file_sha256=report_sha256,
            expected_receipt_sha256="f" * 64,
        )

    with pytest.raises(SemanticDimensionsError, match="does not bind"):
        bind_verified_report_file(
            report_path,
            source_root=source_root,
            receipt_bytes=receipt_bytes,
            expected_report_file_sha256="f" * 64,
            expected_receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        )

    literal = b"independent-verifier-receipt-v1"
    with pytest.raises(SemanticDimensionsError, match="FULL verification receipt"):
        bind_verified_report_file(
            report_path,
            source_root=source_root,
            receipt_bytes=literal,
            expected_report_file_sha256=report_sha256,
            expected_receipt_sha256=hashlib.sha256(literal).hexdigest(),
        )


def test_receipt_source_binding_cannot_be_resealed_by_the_caller() -> None:
    old = _req("old-receipt-forgery", "Clients MUST send frames.")
    new = _req("new-receipt-forgery", "Clients MUST send frames promptly.")
    _report_value, report_path, source_root = _report(old, new)
    receipt = create_full_verification_receipt(report_path, source_root=source_root)
    data = receipt.model_dump(mode="json")
    data["old_source"]["content_sha256"] = "f" * 64
    payload = {key: value for key, value in data.items() if key != "receipt_payload_sha256"}
    data["receipt_payload_sha256"] = canonical_sha256(payload)
    forged_bytes = canonical_json_bytes(data)

    with pytest.raises(SemanticDimensionsError, match="fresh source replay"):
        bind_verified_report_file(
            report_path,
            source_root=source_root,
            receipt_bytes=forged_bytes,
            expected_report_file_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
            expected_receipt_sha256=hashlib.sha256(forged_bytes).hexdigest(),
        )


def test_resealed_semantic_report_cannot_create_a_full_receipt() -> None:
    old = _req("old-resealed", "Clients MUST send frames.")
    new = _req("new-resealed", "Clients MUST send frames promptly.")
    report, _report_path, source_root = _report(old, new)
    mutated = report.old_requirements[0].model_copy(update={"actor": "Servers"})
    mutated = mutated.model_copy(
        update={
            "fingerprint": fingerprint_requirement(
                mutated.normalized_text,
                mutated.modality.value,
                mutated.actor,
                mutated.action,
                mutated.condition,
                mutated.exception,
            )
        }
    )
    forged_report = _refresh_report_integrity(
        report.model_copy(update={"old_requirements": [mutated]})
    )
    forged_path = source_root / "resealed-report.json"
    forged_path.write_bytes(canonical_json_bytes(forged_report.model_dump(mode="json")))

    with pytest.raises(SemanticDimensionsError, match="FULL report verification failed"):
        create_full_verification_receipt(forged_path, source_root=source_root)


@pytest.mark.parametrize("source_failure", ["mutated", "deleted"])
def test_bound_authority_replays_and_rejects_source_state_change(
    source_failure: str,
) -> None:
    old = _req("old-source-state", "Clients MUST send frames.")
    new = _req("new-source-state", "Clients MUST send frames promptly.")
    authority, change = _authority(old, new)
    old_source_path = authority.source_root / authority.receipt.old_source.source_ref
    if source_failure == "mutated":
        old_source_path.write_text("<p>Clients MUST drop frames.</p>", encoding="utf-8")
    else:
        old_source_path.unlink()

    with pytest.raises(SemanticDimensionsError, match="FULL report verification failed"):
        build_semantic_dimensions(
            authority=authority,
            primary_change_id=change.change_id,
        )


def test_wrong_source_root_cannot_replay_a_valid_receipt() -> None:
    old = _req("old-wrong-root", "Clients MUST send frames.")
    new = _req("new-wrong-root", "Clients MUST send frames promptly.")
    _report_value, report_path, source_root = _report(old, new)
    receipt = create_full_verification_receipt(report_path, source_root=source_root)
    receipt_bytes = full_verification_receipt_json_bytes(receipt)
    wrong_holder = TemporaryDirectory(prefix="normshift-semantic-wrong-root-")
    _TEMPORARY_AUTHORITIES.append(wrong_holder)

    with pytest.raises(SemanticDimensionsError, match="FULL report verification failed"):
        bind_verified_report_file(
            report_path,
            source_root=Path(wrong_holder.name),
            receipt_bytes=receipt_bytes,
            expected_report_file_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
            expected_receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        )


def test_change_class_enum_exactly_matches_frozen_m2_policy() -> None:
    policy = json.loads((ROOT / "acceptance" / "m1_m2_prereg_v1.json").read_bytes())
    frozen_classes = {item["class"] for item in policy["m2"]["change_classes"]}
    assert {item.value for item in SemanticChangeClass} == frozen_classes


def _rehash_document(data: dict[str, object]) -> bytes:
    change = data["change"]
    assert isinstance(change, dict)
    semantic_payload = {key: value for key, value in change.items() if key != "semantic_change_id"}
    change["semantic_change_id"] = canonical_sha256(semantic_payload)
    document_payload = {key: value for key, value in data.items() if key != "integrity_sha256"}
    data["integrity_sha256"] = canonical_sha256(document_payload)
    return canonical_json_bytes(data)


def test_rehashed_source_forgery_parses_but_exact_replay_fails_closed() -> None:
    old = _req("old-forgery", "Clients MUST send frames.")
    new = _req("new-forgery", "Clients MUST send frames promptly.")
    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )
    data = json.loads(semantic_dimensions_json_bytes(document))
    data["change"]["evidence"]["old_requirement"]["source_locator"] = "id:forged"
    forged = parse_semantic_dimensions_bytes(_rehash_document(data))

    with pytest.raises(SemanticDimensionsError, match="exact replay"):
        verify_semantic_dimensions(
            forged,
            authority=authority,
            primary_change_id=change.change_id,
        )


@pytest.mark.parametrize(
    "target",
    [
        "primary_change_sha256",
        "old_requirement_payload_sha256",
        "verification_receipt_sha256",
        "verification_receipt_payload_sha256",
    ],
)
def test_rehashed_canonical_payload_hash_forgery_fails_exact_replay(target: str) -> None:
    old = _req("old-payload-forgery", "Clients MUST send frames.")
    new = _req("new-payload-forgery", "Clients MUST send frames promptly.")
    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )
    data = json.loads(semantic_dimensions_json_bytes(document))
    evidence = data["change"]["evidence"]
    if target == "primary_change_sha256":
        evidence["primary_change_sha256"] = "0" * 64
    elif target == "old_requirement_payload_sha256":
        evidence["old_requirement"]["requirement_payload_sha256"] = "0" * 64
    else:
        evidence[target] = "0" * 64
    forged = parse_semantic_dimensions_bytes(_rehash_document(data))

    with pytest.raises(SemanticDimensionsError, match="exact replay"):
        verify_semantic_dimensions(
            forged,
            authority=authority,
            primary_change_id=change.change_id,
        )


def test_invalid_observation_hash_and_primary_evidence_fail_closed() -> None:
    old = _req("old-invalid", "Clients MUST send frames.")
    new = _req("new-invalid", "Servers MUST send frames.", actor="Servers")
    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )
    data = json.loads(semantic_dimensions_json_bytes(document))
    old_actor = data["change"]["slots"]["actor"]["old"]
    old_actor["value_sha256"] = "0" * 64
    observation_payload = {
        key: value for key, value in old_actor.items() if key != "evidence_sha256"
    }
    old_actor["evidence_sha256"] = canonical_sha256(observation_payload)

    with pytest.raises(SemanticDimensionsError, match="invalid semantic dimension document"):
        parse_semantic_dimensions_bytes(_rehash_document(data))


def _mutate_alignment_score(change: Change) -> Change:
    assert change.alignment_score is not None
    changed_score = change.alignment_score.model_copy(
        update={"combined": change.alignment_score.combined + 0.125}
    )
    return change.model_copy(update={"alignment_score": changed_score})


@pytest.mark.parametrize(
    ("field_name", "mutator"),
    [
        ("change_id", lambda item: item.model_copy(update={"change_id": "forged"})),
        (
            "old_requirement_id",
            lambda item: item.model_copy(update={"old_requirement_id": "old-forged"}),
        ),
        (
            "new_requirement_id",
            lambda item: item.model_copy(update={"new_requirement_id": "new-forged"}),
        ),
        (
            "classification",
            lambda item: item.model_copy(
                update={"classification": ChangeClassification.POLARITY_FLIP}
            ),
        ),
        ("confidence", lambda item: item.model_copy(update={"confidence": 0.125})),
        (
            "classification_reasons",
            lambda item: item.model_copy(update={"classification_reasons": ["forged"]}),
        ),
        (
            "old_source_locator",
            lambda item: item.model_copy(update={"old_source_locator": "id:forged"}),
        ),
        (
            "new_source_locator",
            lambda item: item.model_copy(update={"new_source_locator": "id:forged"}),
        ),
        ("old_text", lambda item: item.model_copy(update={"old_text": "forged old"})),
        ("new_text", lambda item: item.model_copy(update={"new_text": "forged new"})),
        (
            "modality_transition",
            lambda item: item.model_copy(update={"modality_transition": "MAY->MAY"}),
        ),
        (
            "evidence_hashes",
            lambda item: item.model_copy(update={"evidence_hashes": ["0" * 64]}),
        ),
        ("alignment_score", _mutate_alignment_score),
        (
            "old_section_path",
            lambda item: item.model_copy(update={"old_section_path": "9. Forged"}),
        ),
        (
            "new_section_path",
            lambda item: item.model_copy(update={"new_section_path": "9. Forged"}),
        ),
    ],
)
def test_every_primary_change_field_is_bound_and_fails_replay_when_mutated(
    field_name: str,
    mutator: Callable[[Change], Change],
) -> None:
    old = _req("old-primary-fields", "Clients MUST send frames.")
    new = _req("new-primary-fields", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    authority = _bind_report(report_path, source_root)
    original = report.changes[0]
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=original.change_id,
    )
    mutated = mutator(original)
    assert getattr(mutated, field_name) != getattr(original, field_name)
    stale_authority = replace(
        authority,
        report=authority.report.model_copy(update={"changes": [mutated]}),
    )

    with pytest.raises(SemanticDimensionsError, match="in-memory report"):
        verify_semantic_dimensions(
            document,
            authority=stale_authority,
            primary_change_id=original.change_id,
        )


@pytest.mark.parametrize(
    ("field_name", "mutator"),
    [
        (
            "requirement_id",
            lambda item: item.model_copy(update={"requirement_id": "old-forged"}),
        ),
        (
            "document_sha256",
            lambda item: item.model_copy(update={"document_sha256": "c" * 64}),
        ),
        (
            "document_version",
            lambda item: item.model_copy(update={"document_version": "9"}),
        ),
        (
            "section_path",
            lambda item: item.model_copy(update={"section_path": "9. Forged"}),
        ),
        (
            "source_locator",
            lambda item: item.model_copy(update={"source_locator": "id:forged"}),
        ),
        (
            "original_text",
            lambda item: item.model_copy(update={"original_text": "forged original"}),
        ),
        (
            "normalized_text",
            lambda item: item.model_copy(update={"normalized_text": "forged normalized"}),
        ),
        ("modality", lambda item: item.model_copy(update={"modality": Modality.SHOULD})),
        ("polarity", lambda item: item.model_copy(update={"polarity": Polarity.NEGATIVE})),
        ("actor", lambda item: item.model_copy(update={"actor": "Attackers"})),
        ("action", lambda item: item.model_copy(update={"action": "forge frames"})),
        (
            "condition",
            lambda item: item.model_copy(update={"condition": "when forged"}),
        ),
        (
            "exception",
            lambda item: item.model_copy(update={"exception": "unless checked"}),
        ),
        ("confidence", lambda item: item.model_copy(update={"confidence": 0.125})),
        (
            "extractor_version",
            lambda item: item.model_copy(update={"extractor_version": "forged-v9"}),
        ),
        ("fingerprint", lambda item: item.model_copy(update={"fingerprint": "forged"})),
        (
            "structural_index",
            lambda item: item.model_copy(update={"structural_index": 9}),
        ),
    ],
)
def test_every_requirement_field_is_bound_and_fails_replay_when_mutated(
    field_name: str,
    mutator: Callable[[Requirement], Requirement],
) -> None:
    old = _req("old-requirement-fields", "Clients MUST send frames.")
    new = _req("new-requirement-fields", "Clients MUST send frames promptly.")
    report, report_path, source_root = _report(old, new)
    authority = _bind_report(report_path, source_root)
    change = report.changes[0]
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )
    mutated = mutator(report.old_requirements[0])
    assert getattr(mutated, field_name) != getattr(report.old_requirements[0], field_name)
    stale_authority = replace(
        authority,
        report=authority.report.model_copy(update={"old_requirements": [mutated]}),
    )

    with pytest.raises(SemanticDimensionsError, match="in-memory report"):
        verify_semantic_dimensions(
            document,
            authority=stale_authority,
            primary_change_id=change.change_id,
        )


@pytest.mark.parametrize(
    ("field_name", "new_value"),
    [
        ("normalized_text", "Clients MUST send altered frames."),
        ("modality", Modality.SHOULD),
        ("actor", "Attackers"),
        ("action", "alter frames"),
        ("condition", "when forged"),
        ("exception", "unless audited"),
    ],
)
def test_semantic_field_laundering_fails_even_with_a_reanchored_report(
    field_name: str,
    new_value: object,
) -> None:
    old = _req("old-laundering", "Clients MUST send frames.")
    new = _req("new-laundering", "Clients MUST send frames promptly.")
    report, _report_path, source_root = _report(old, new)
    mutated = report.old_requirements[0].model_copy(update={field_name: new_value})
    forged_report = _refresh_report_integrity(
        report.model_copy(update={"old_requirements": [mutated]})
    )
    forged_path = source_root / "forged-report.json"
    forged_path.write_bytes(canonical_json_bytes(forged_report.model_dump(mode="json")))

    with pytest.raises(SemanticDimensionsError, match="fingerprint"):
        create_full_verification_receipt(
            forged_path,
            source_root=source_root,
        )


def test_recomputed_fingerprint_cannot_bypass_existing_external_anchor() -> None:
    old = _req("old-refingerprinted", "Clients MUST send frames.")
    new = _req("new-refingerprinted", "Clients MUST send frames promptly.")
    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
    )
    mutated = authority.report.old_requirements[0].model_copy(update={"actor": "Attackers"})
    mutated = mutated.model_copy(
        update={
            "fingerprint": fingerprint_requirement(
                mutated.normalized_text,
                mutated.modality.value,
                mutated.actor,
                mutated.action,
                mutated.condition,
                mutated.exception,
            )
        }
    )
    forged_report = _refresh_report_integrity(
        authority.report.model_copy(update={"old_requirements": [mutated]})
    )
    stale_authority = replace(authority, report=forged_report)

    with pytest.raises(SemanticDimensionsError, match="in-memory report"):
        verify_semantic_dimensions(
            document,
            authority=stale_authority,
            primary_change_id=change.change_id,
        )


def test_stale_primary_authority_fails_before_any_dimensions_are_emitted() -> None:
    old = _req("old-stale", "Clients MUST send frames.")
    new = _req("new-stale", "Clients MUST send frames promptly.")
    authority, change = _authority(old, new)
    stale_change = change.model_copy(update={"confidence": change.confidence / 2})
    stale_report = authority.report.model_copy(update={"changes": [stale_change]})
    stale_authority = replace(authority, report=stale_report)

    with pytest.raises(SemanticDimensionsError, match="in-memory report"):
        build_semantic_dimensions(
            authority=stale_authority,
            primary_change_id=change.change_id,
        )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda raw: raw.replace(b'"kind": ', b'"kind" : ', 1),
        lambda raw: raw.replace(b'"kind":', b'"kind":"duplicate","kind":', 1),
    ],
)
def test_noncanonical_and_duplicate_json_are_rejected(
    mutator: Callable[[bytes], bytes],
) -> None:
    old = _req("old-json", "Clients MUST send frames.")
    new = _req("new-json", "Clients MUST send frames.")
    authority, change = _authority(old, new)
    raw = semantic_dimensions_json_bytes(
        build_semantic_dimensions(
            authority=authority,
            primary_change_id=change.change_id,
        )
    )
    with pytest.raises(SemanticDimensionsError):
        parse_semantic_dimensions_bytes(mutator(raw))


def test_invalid_span_and_missing_pair_fail_closed() -> None:
    old = _req("old-span", "Clients MUST send frames.")
    new = _req("new-span", "Clients MUST send packets.")
    authority, change = _authority(old, new)
    with pytest.raises(SemanticDimensionsError, match="exceeds"):
        build_semantic_dimensions(
            authority=authority,
            primary_change_id=change.change_id,
            old_object_span=NormalizedTextSpan(start=0, end=10_000),
        )
    unpaired_authority, unpaired_change = _authority(old, None)
    with pytest.raises(SemanticDimensionsError, match="unpaired"):
        build_semantic_dimensions(
            authority=unpaired_authority,
            primary_change_id=unpaired_change.change_id,
            old_object_span=_span(old, "frames"),
        )


def test_actor_and_modality_token_spans_remain_unverified_unknown_candidates() -> None:
    old = _req("old-role-laundering", "Clients MUST send frames.")
    new = _req(
        "new-role-laundering",
        "Servers MUST NOT send frames.",
        actor="Servers",
        action="send frames",
        modality=Modality.MUST_NOT,
    )
    authority, change = _authority(old, new)
    document = build_semantic_dimensions(
        authority=authority,
        primary_change_id=change.change_id,
        old_object_span=_span(old, "Clients"),
        new_object_span=_span(new, "MUST NOT"),
        old_scope_span=_span(old, "MUST"),
        new_scope_span=_span(new, "Servers"),
    )

    for slot in (document.change.slots.object, document.change.slots.scope):
        assert slot.disposition is DimensionDisposition.UNKNOWN
        assert slot.change_class is None
        assert slot.old is not None
        assert slot.new is not None
        assert slot.old.verification_status is ObservationVerification.ASSERTED_UNVERIFIED
        assert slot.new.verification_status is ObservationVerification.ASSERTED_UNVERIFIED
    assert SemanticChangeClass.OBJECT_CHANGED not in document.change.change_classes
    assert SemanticChangeClass.SCOPE_CHANGED not in document.change.change_classes
    verify_semantic_dimensions(
        document,
        authority=authority,
        primary_change_id=change.change_id,
        old_object_span=_span(old, "Clients"),
        new_object_span=_span(new, "MUST NOT"),
        old_scope_span=_span(old, "MUST"),
        new_scope_span=_span(new, "Servers"),
    )


@pytest.mark.parametrize("cut", ["start", "end"])
def test_inside_token_candidate_spans_fail_closed(cut: str) -> None:
    old = _req("old-inside-token", "Clients MUST send frames.")
    new = _req("new-inside-token", "Clients MUST send packets.")
    authority, change = _authority(old, new)
    whole = _span(old, "frames")
    span = (
        NormalizedTextSpan(start=whole.start + 1, end=whole.end)
        if cut == "start"
        else NormalizedTextSpan(start=whole.start, end=whole.end - 1)
    )

    with pytest.raises(SemanticDimensionsError, match="inside a token"):
        build_semantic_dimensions(
            authority=authority,
            primary_change_id=change.change_id,
            old_object_span=span,
        )


@pytest.mark.parametrize("side", ["old", "new"])
@pytest.mark.parametrize("kind", ["overlap", "reused"])
def test_overlapping_or_reused_candidate_spans_fail_closed(
    side: str,
    kind: str,
) -> None:
    old = _req("old-overlap", "Clients MUST send frames.")
    new = _req("new-overlap", "Clients MUST send packets.")
    authority, change = _authority(old, new)
    requirement = old if side == "old" else new
    noun = "frames" if side == "old" else "packets"
    object_span = _span(requirement, f"send {noun}")
    scope_span = object_span if kind == "reused" else _span(requirement, noun)
    kwargs = {
        f"{side}_object_span": object_span,
        f"{side}_scope_span": scope_span,
    }

    with pytest.raises(SemanticDimensionsError, match="overlap or be reused"):
        build_semantic_dimensions(
            authority=authority,
            primary_change_id=change.change_id,
            **kwargs,
        )
