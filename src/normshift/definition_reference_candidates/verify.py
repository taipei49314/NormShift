from pathlib import Path

from normshift.definition_reference_candidates.builder import build_definition_reference_candidates
from normshift.definition_reference_candidates.errors import DefinitionReferenceCandidateError
from normshift.definition_reference_candidates.models import DefinitionReferenceCandidatesDocument
from normshift.definition_reference_candidates.serialization import (
    MAX_DEFINITION_REFERENCE_CANDIDATES_BYTES,
    candidate_file_sha256,
    definition_reference_candidates_json_bytes,
    parse_definition_reference_candidates_bytes,
)
from normshift.lineage import LineageContractError, verify_lineage_graph_file
from normshift.lineage.serialization import (
    MAX_LINEAGE_GRAPH_BYTES,
    lineage_graph_sha256,
    parse_lineage_graph_bytes,
)
from normshift.model.types import AdapterName, ProfileName
from normshift.semantic_dimensions import SemanticDimensionsError, read_bounded_regular_file


def verify_definition_reference_candidates_file(
    transitions_path: Path,
    *,
    candidates_sha256: str,
    graph_path: Path,
    graph_sha256: str,
    documents: list[Path],
    profile: ProfileName,
    adapter: AdapterName,
) -> DefinitionReferenceCandidatesDocument:
    _require(candidates_sha256, "candidate SHA-256")
    try:
        raw = read_bounded_regular_file(
            transitions_path,
            label="definition-reference candidates",
            max_bytes=MAX_DEFINITION_REFERENCE_CANDIDATES_BYTES,
        ).raw
    except SemanticDimensionsError as exc:
        raise DefinitionReferenceCandidateError(str(exc)) from exc
    if candidate_file_sha256(raw) != candidates_sha256:
        raise DefinitionReferenceCandidateError("candidate bytes differ from external SHA-256")
    document = parse_definition_reference_candidates_bytes(raw)
    if document.graph_file_sha256 != graph_sha256 or document.profile != profile.value:
        raise DefinitionReferenceCandidateError("candidate graph binding differs from replay input")
    try:
        graph_raw = read_bounded_regular_file(
            graph_path,
            label="lineage graph for definition-reference candidates",
            max_bytes=MAX_LINEAGE_GRAPH_BYTES,
        ).raw
    except SemanticDimensionsError as exc:
        raise DefinitionReferenceCandidateError(str(exc)) from exc
    if lineage_graph_sha256(graph_raw) != graph_sha256:
        raise DefinitionReferenceCandidateError("lineage graph bytes differ from external SHA-256")
    try:
        graph_preflight = parse_lineage_graph_bytes(graph_raw)
    except LineageContractError as exc:
        raise DefinitionReferenceCandidateError(f"invalid lineage graph anchor: {exc}") from exc
    if (
        document.graph_content_sha256 != graph_preflight.integrity["content_sha256"]
        or document.graph_schema_version != graph_preflight.schema_version
        or document.graph_tool_version != graph_preflight.tool_version
    ):
        raise DefinitionReferenceCandidateError(
            "candidate graph metadata differs from replay input"
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
        raise DefinitionReferenceCandidateError(f"lineage graph replay failed: {exc}") from exc
    expected = build_definition_reference_candidates(graph, graph_file_sha256=graph_sha256)
    if definition_reference_candidates_json_bytes(expected) != raw:
        raise DefinitionReferenceCandidateError("candidates differ from exact graph replay")
    return document


def _require(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise DefinitionReferenceCandidateError(f"{label} must be a lowercase SHA-256 digest")
