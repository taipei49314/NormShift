"""External-anchor verification for DefinitionTransition v1 sidecars."""

from __future__ import annotations

from pathlib import Path

from normshift.definition_transitions.builder import build_definition_transitions
from normshift.definition_transitions.errors import DefinitionTransitionError
from normshift.definition_transitions.models import DefinitionTransitionsDocument
from normshift.definition_transitions.serialization import (
    MAX_DEFINITION_TRANSITIONS_BYTES,
    definition_transitions_json_bytes,
    definition_transitions_sha256,
    parse_definition_transitions_bytes,
)
from normshift.lineage import LineageContractError, verify_lineage_graph_file
from normshift.lineage.serialization import (
    MAX_LINEAGE_GRAPH_BYTES,
    lineage_graph_sha256,
    parse_lineage_graph_bytes,
)
from normshift.model.types import AdapterName, ProfileName
from normshift.semantic_dimensions import SemanticDimensionsError, read_bounded_regular_file


def verify_definition_transitions_file(
    transitions_path: Path,
    *,
    transitions_sha256: str,
    graph_path: Path,
    graph_sha256: str,
    documents: list[Path],
    profile: ProfileName,
    adapter: AdapterName,
) -> DefinitionTransitionsDocument:
    """Verify a sidecar only by an external digest and exact LineageGraph replay."""
    _require_sha256(transitions_sha256, "definition transitions SHA-256")
    try:
        raw = read_bounded_regular_file(
            transitions_path,
            label="definition transitions",
            max_bytes=MAX_DEFINITION_TRANSITIONS_BYTES,
        ).raw
    except SemanticDimensionsError as exc:
        raise DefinitionTransitionError(str(exc)) from exc
    if definition_transitions_sha256(raw) != transitions_sha256:
        raise DefinitionTransitionError("definition transitions bytes differ from external SHA-256")
    document = parse_definition_transitions_bytes(raw)
    if document.graph_file_sha256 != graph_sha256:
        raise DefinitionTransitionError("definition transitions graph file SHA differs from input")
    # Bind every graph metadata claim before the exact replay opens any source.
    # verify_lineage_graph_file rereads this descriptor-stably and rejects a
    # graph-path swap between this preflight and replay.
    try:
        graph_raw = read_bounded_regular_file(
            graph_path,
            label="lineage graph for definition transitions",
            max_bytes=MAX_LINEAGE_GRAPH_BYTES,
        ).raw
    except SemanticDimensionsError as exc:
        raise DefinitionTransitionError(str(exc)) from exc
    if lineage_graph_sha256(graph_raw) != graph_sha256:
        raise DefinitionTransitionError("lineage graph bytes differ from external SHA-256")
    try:
        graph_preflight = parse_lineage_graph_bytes(graph_raw)
    except LineageContractError as exc:
        raise DefinitionTransitionError(f"invalid lineage graph anchor: {exc}") from exc
    if (
        document.graph_content_sha256 != graph_preflight.integrity["content_sha256"]
        or document.graph_schema_version != graph_preflight.schema_version
        or document.graph_tool_version != graph_preflight.tool_version
        or document.profile != profile.value
    ):
        raise DefinitionTransitionError(
            "definition transitions graph metadata differs from replay input"
        )
    try:
        graph = verify_lineage_graph_file(
            graph_path,
            graph_sha256=graph_sha256,
            documents=documents,
            profile=profile,
            adapter=adapter,
        )
    except LineageContractError as exc:
        raise DefinitionTransitionError(f"lineage graph replay failed: {exc}") from exc
    expected = build_definition_transitions(graph, graph_file_sha256=graph_sha256)
    if definition_transitions_json_bytes(expected) != raw:
        raise DefinitionTransitionError("definition transitions differ from exact graph replay")
    return document


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise DefinitionTransitionError(f"{label} must be a lowercase SHA-256 digest")
