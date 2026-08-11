"""Canonical JSON and JSON Schema support for semantic dimensions."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from normshift.evidence.hashing import canonical_json_bytes
from normshift.semantic_dimensions.errors import SemanticDimensionsError
from normshift.semantic_dimensions.models import SemanticDimensionsDocument
from normshift.strict_json import StrictJSONError, strict_loads

MAX_SEMANTIC_DIMENSIONS_BYTES = 1_000_000
SEMANTIC_DIMENSIONS_SCHEMA_ID = (
    "https://normshift.local/schemas/semantic_change_dimensions_v1.schema.json"
)


def semantic_dimensions_json_bytes(document: SemanticDimensionsDocument) -> bytes:
    """Serialize a validated document to byte-identical canonical JSON."""
    return canonical_json_bytes(document.model_dump(mode="json"))


def parse_semantic_dimensions_bytes(raw: bytes) -> SemanticDimensionsDocument:
    """Parse only canonical, duplicate-free, bounded semantic dimension JSON."""
    if len(raw) > MAX_SEMANTIC_DIMENSIONS_BYTES:
        raise SemanticDimensionsError("semantic dimension document exceeds size limit")
    try:
        parsed = strict_loads(raw)
    except StrictJSONError as exc:
        raise SemanticDimensionsError(str(exc)) from exc
    if not isinstance(parsed, dict):
        raise SemanticDimensionsError("semantic dimension document must be a JSON object")
    if canonical_json_bytes(parsed) != raw:
        raise SemanticDimensionsError("semantic dimension JSON is not canonical")
    try:
        document = SemanticDimensionsDocument.model_validate_json(raw)
    except ValidationError as exc:
        raise SemanticDimensionsError(f"invalid semantic dimension document: {exc}") from exc
    if semantic_dimensions_json_bytes(document) != raw:
        raise SemanticDimensionsError("semantic dimension JSON omits or changes typed fields")
    return document


def semantic_dimensions_json_schema() -> dict[str, Any]:
    """Return the deterministic Draft 2020-12 schema for version 1.0.0."""
    schema = SemanticDimensionsDocument.model_json_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SEMANTIC_DIMENSIONS_SCHEMA_ID,
        **schema,
    }
