"""Strict canonical LineageGraph v1 interchange support."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.lineage.errors import LineageContractError
from normshift.model.types import LineageGraph, LineageRelation
from normshift.strict_json import StrictJSONError, strict_loads

LINEAGE_GRAPH_SCHEMA_VERSION = "1.0.0"
LINEAGE_GRAPH_SCHEMA_ID = "https://normshift.local/schemas/lineage_graph_v1.schema.json"
MAX_LINEAGE_GRAPH_BYTES = 25_000_000


def lineage_graph_json_schema() -> dict[str, Any]:
    """Return the exact strict Draft 2020-12 LineageGraph v1 schema."""
    schema = LineageGraph.model_json_schema()
    properties = schema["properties"]
    properties["schema_version"] = {"const": LINEAGE_GRAPH_SCHEMA_VERSION}
    schema["required"] = sorted(properties)
    for definition in schema.get("$defs", {}).values():
        if (
            isinstance(definition, dict)
            and definition.get("additionalProperties") is False
            and isinstance(definition.get("properties"), dict)
        ):
            definition["required"] = sorted(definition["properties"])
    properties["summary"] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "version_count",
            "lineage_count",
            "edge_count",
            "ambiguity_count",
            "definition_count",
            "dependency_link_count",
            "relation_counts",
        ],
        "properties": {
            "version_count": {"type": "integer", "minimum": 2},
            "lineage_count": {"type": "integer", "minimum": 0},
            "edge_count": {"type": "integer", "minimum": 0},
            "ambiguity_count": {"type": "integer", "minimum": 0},
            "definition_count": {"type": "integer", "minimum": 0},
            "dependency_link_count": {"type": "integer", "minimum": 0},
            "relation_counts": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    relation.value: {"type": "integer", "minimum": 0}
                    for relation in LineageRelation
                },
            },
        },
    }
    properties["integrity"] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["alg", "content_sha256"],
        "properties": {
            "alg": {"const": "sha256"},
            "content_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LINEAGE_GRAPH_SCHEMA_ID,
        **schema,
    }


def lineage_graph_json_bytes(graph: LineageGraph) -> bytes:
    """Serialize one integrity-valid graph to canonical bounded bytes."""
    raw = canonical_json_bytes(graph.model_dump(mode="json"))
    if len(raw) > MAX_LINEAGE_GRAPH_BYTES:
        raise LineageContractError("lineage graph exceeds size limit")
    parsed = _validate_graph_object(raw)
    if canonical_json_bytes(parsed) != raw:
        raise LineageContractError("lineage graph JSON is not canonical")
    return raw


def parse_lineage_graph_bytes(raw: bytes) -> LineageGraph:
    """Parse a canonical, schema-valid, integrity-bound LineageGraph v1."""
    parsed = _validate_graph_object(raw)
    if canonical_json_bytes(parsed) != raw:
        raise LineageContractError("lineage graph JSON is not canonical")
    try:
        graph = LineageGraph.model_validate(parsed)
    except ValidationError as exc:
        raise LineageContractError(f"invalid lineage graph: {exc}") from exc
    if lineage_graph_json_bytes_unchecked(graph) != raw:
        raise LineageContractError("lineage graph JSON omits or changes typed fields")
    return graph


def lineage_graph_sha256(raw: bytes) -> str:
    """Return the external anchor digest after parsing caller-provided bytes."""
    return sha256(raw).hexdigest()


def lineage_graph_json_bytes_unchecked(graph: LineageGraph) -> bytes:
    """Canonical bytes after the parser has established schema and integrity."""
    return canonical_json_bytes(graph.model_dump(mode="json"))


def _validate_graph_object(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_LINEAGE_GRAPH_BYTES:
        raise LineageContractError("lineage graph exceeds size limit")
    try:
        parsed = strict_loads(raw)
    except StrictJSONError as exc:
        raise LineageContractError(f"invalid lineage graph JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise LineageContractError("lineage graph must be a JSON object")
    validator = Draft202012Validator(lineage_graph_json_schema())
    errors = sorted(validator.iter_errors(parsed), key=lambda item: list(item.path))
    if errors:
        raise LineageContractError(f"invalid lineage graph schema: {errors[0].message}")
    integrity = parsed["integrity"]
    if integrity["content_sha256"] != integrity_payload_hash(parsed):
        raise LineageContractError("lineage graph integrity SHA differs from content")
    return parsed
