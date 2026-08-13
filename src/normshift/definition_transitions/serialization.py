"""Strict canonical DefinitionTransition v1 interchange support."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from normshift.definition_transitions.errors import DefinitionTransitionError
from normshift.definition_transitions.models import DefinitionTransitionsDocument
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.strict_json import StrictJSONError, strict_loads

DEFINITION_TRANSITIONS_SCHEMA_VERSION = "normshift-definition-transitions/v1"
DEFINITION_TRANSITIONS_SCHEMA_ID = (
    "https://normshift.local/schemas/definition_transitions_v1.schema.json"
)
MAX_DEFINITION_TRANSITIONS_BYTES = 1_000_000


def definition_transitions_json_schema() -> dict[str, Any]:
    """Return the exact strict Draft 2020-12 DefinitionTransition v1 schema."""
    schema = DefinitionTransitionsDocument.model_json_schema()
    schema["required"] = sorted(schema["properties"])
    for definition in schema.get("$defs", {}).values():
        if (
            isinstance(definition, dict)
            and definition.get("additionalProperties") is False
            and isinstance(definition.get("properties"), dict)
        ):
            definition["required"] = sorted(definition["properties"])
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": DEFINITION_TRANSITIONS_SCHEMA_ID,
        **schema,
    }


def definition_transitions_json_bytes(document: DefinitionTransitionsDocument) -> bytes:
    """Serialize one integrity-valid transition document to canonical bounded bytes."""
    raw = canonical_json_bytes(document.model_dump(mode="json"))
    if len(raw) > MAX_DEFINITION_TRANSITIONS_BYTES:
        raise DefinitionTransitionError("definition transitions exceed size limit")
    parsed = _validate_document_object(raw)
    if canonical_json_bytes(parsed) != raw:
        raise DefinitionTransitionError("definition transitions JSON is not canonical")
    return raw


def parse_definition_transitions_bytes(raw: bytes) -> DefinitionTransitionsDocument:
    """Parse a canonical, schema-valid, integrity-bound transition document."""
    parsed = _validate_document_object(raw)
    if canonical_json_bytes(parsed) != raw:
        raise DefinitionTransitionError("definition transitions JSON is not canonical")
    try:
        # JSON schema has already checked primitive types.  Enum values arrive
        # from JSON as strings, so retain typed/frozen models without demanding
        # pre-instantiated Python enum objects at this interchange boundary.
        document = DefinitionTransitionsDocument.model_validate(parsed, strict=False)
    except ValidationError as exc:
        raise DefinitionTransitionError(f"invalid definition transitions: {exc}") from exc
    if canonical_json_bytes(document.model_dump(mode="json")) != raw:
        raise DefinitionTransitionError("definition transitions JSON omits or changes typed fields")
    return document


def definition_transitions_sha256(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _validate_document_object(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_DEFINITION_TRANSITIONS_BYTES:
        raise DefinitionTransitionError("definition transitions exceed size limit")
    try:
        parsed = strict_loads(raw)
    except StrictJSONError as exc:
        raise DefinitionTransitionError(f"invalid definition transitions JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise DefinitionTransitionError("definition transitions must be a JSON object")
    errors = sorted(
        Draft202012Validator(definition_transitions_json_schema()).iter_errors(parsed),
        key=lambda item: list(item.path),
    )
    if errors:
        raise DefinitionTransitionError(
            f"invalid definition transitions schema: {errors[0].message}"
        )
    integrity = parsed["integrity"]
    if integrity["content_sha256"] != integrity_payload_hash(parsed):
        raise DefinitionTransitionError("definition transitions integrity SHA differs from content")
    return parsed
