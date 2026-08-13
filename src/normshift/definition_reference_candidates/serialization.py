from __future__ import annotations

from hashlib import sha256
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from normshift.definition_reference_candidates.errors import DefinitionReferenceCandidateError
from normshift.definition_reference_candidates.models import DefinitionReferenceCandidatesDocument
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.strict_json import StrictJSONError, strict_loads

MAX_DEFINITION_REFERENCE_CANDIDATES_BYTES = 1_000_000
SCHEMA_ID = "https://normshift.local/schemas/definition_reference_candidates_v1.schema.json"


def definition_reference_candidates_json_schema() -> dict[str, Any]:
    schema = DefinitionReferenceCandidatesDocument.model_json_schema()
    schema["required"] = sorted(schema["properties"])
    for definition in schema.get("$defs", {}).values():
        if isinstance(definition, dict) and definition.get("additionalProperties") is False:
            properties = definition.get("properties")
            if isinstance(properties, dict):
                definition["required"] = sorted(properties)
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SCHEMA_ID, **schema}


def definition_reference_candidates_json_bytes(
    document: DefinitionReferenceCandidatesDocument,
) -> bytes:
    raw = canonical_json_bytes(document.model_dump(mode="json"))
    _validate(raw)
    return raw


def parse_definition_reference_candidates_bytes(
    raw: bytes,
) -> DefinitionReferenceCandidatesDocument:
    parsed = _validate(raw)
    if canonical_json_bytes(parsed) != raw:
        raise DefinitionReferenceCandidateError(
            "definition-reference candidates JSON is not canonical"
        )
    try:
        result = DefinitionReferenceCandidatesDocument.model_validate(parsed, strict=False)
    except ValidationError as exc:
        raise DefinitionReferenceCandidateError(
            f"invalid definition-reference candidates: {exc}"
        ) from exc
    if canonical_json_bytes(result.model_dump(mode="json")) != raw:
        raise DefinitionReferenceCandidateError(
            "definition-reference candidates JSON omits typed fields"
        )
    return result


def candidate_file_sha256(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _validate(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_DEFINITION_REFERENCE_CANDIDATES_BYTES:
        raise DefinitionReferenceCandidateError("definition-reference candidates exceed size limit")
    try:
        parsed = strict_loads(raw)
    except StrictJSONError as exc:
        raise DefinitionReferenceCandidateError(
            f"invalid definition-reference candidates JSON: {exc}"
        ) from exc
    if not isinstance(parsed, dict):
        raise DefinitionReferenceCandidateError(
            "definition-reference candidates must be a JSON object"
        )
    errors = sorted(
        Draft202012Validator(definition_reference_candidates_json_schema()).iter_errors(parsed),
        key=lambda e: list(e.path),
    )
    if errors:
        raise DefinitionReferenceCandidateError(
            f"invalid definition-reference candidates schema: {errors[0].message}"
        )
    if parsed["integrity"]["content_sha256"] != integrity_payload_hash(parsed):
        raise DefinitionReferenceCandidateError(
            "definition-reference candidates integrity SHA differs from content"
        )
    return parsed
