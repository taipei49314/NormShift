from __future__ import annotations

from hashlib import sha256

from normshift.definition_reference_candidates.errors import DefinitionReferenceCandidateError
from normshift.definition_reference_candidates.models import (
    DefinitionAnchor,
    DefinitionReferenceCandidate,
    DefinitionReferenceCandidatesDocument,
    Integrity,
    RequirementAnchor,
)
from normshift.evidence.hashing import integrity_payload_hash
from normshift.model.types import DefinitionRecord, LineageGraph, RequirementInstanceRef
from normshift.normalize.html_normalize import normalize_whitespace

MAX_CANDIDATES = 10_000


def build_definition_reference_candidates(
    graph: LineageGraph, *, graph_file_sha256: str
) -> DefinitionReferenceCandidatesDocument:
    """Derive lexical evidence candidates only from an exact-replayed LineageGraph."""
    _sha_required(graph_file_sha256, "graph file SHA-256")
    if graph.schema_version != "1.0.0" or graph.integrity.get("alg") != "sha256":
        raise DefinitionReferenceCandidateError("lineage graph has unsupported contract metadata")
    graph_hash = graph.integrity.get("content_sha256")
    if not isinstance(graph_hash, str):
        raise DefinitionReferenceCandidateError("lineage graph is missing integrity SHA")
    _sha_required(graph_hash, "graph content SHA-256")
    versions = dict(zip(graph.versions, graph.document_sha256s, strict=True))
    definitions = {item.definition_id: item for item in graph.definitions}
    if len(definitions) != len(graph.definitions):
        raise DefinitionReferenceCandidateError("lineage graph contains duplicate definition IDs")
    _reject_ambiguous_terms(graph.definitions)
    requirements = _requirements(graph)
    candidates: list[DefinitionReferenceCandidate] = []
    link_ids: set[str] = set()
    candidate_ids: set[str] = set()
    semantic_tuples: set[tuple[str, str, str, str]] = set()
    for link in graph.dependency_links:
        if link.link_id in link_ids:
            raise DefinitionReferenceCandidateError(
                "lineage graph contains duplicate dependency-link IDs"
            )
        link_ids.add(link.link_id)
        requirement = requirements.get(link.requirement_id)
        definition = definitions.get(link.definition_id)
        if requirement is None or definition is None:
            raise DefinitionReferenceCandidateError(
                "dependency link has an orphan requirement or target"
            )
        if (
            link.document_version != requirement.document_version
            or link.document_version != definition.document_version
            or versions.get(link.document_version) != requirement.document_sha256
            or definition.document_sha256 != requirement.document_sha256
            or _term(link.term) != _term(definition.term)
        ):
            raise DefinitionReferenceCandidateError(
                "dependency link target differs from exact graph evidence"
            )
        candidate = _candidate(link.link_id, requirement, definition)
        if candidate.candidate_id in candidate_ids:
            raise DefinitionReferenceCandidateError("definition-reference candidate ID collision")
        semantic_key = (
            requirement.requirement_id,
            definition.definition_id,
            requirement.document_version,
            requirement.document_sha256,
        )
        if semantic_key in semantic_tuples:
            raise DefinitionReferenceCandidateError(
                "duplicate definition-reference candidate evidence"
            )
        candidate_ids.add(candidate.candidate_id)
        semantic_tuples.add(semantic_key)
        candidates.append(candidate)
        if len(candidates) > MAX_CANDIDATES:
            raise DefinitionReferenceCandidateError(
                "definition-reference candidate count exceeds limit"
            )
    candidates.sort(key=lambda item: item.candidate_id)
    payload: dict[str, object] = {
        "schema_version": "normshift-definition-reference-candidates/v1",
        "authority_kind": "LINEAGE_GRAPH_REPLAY_ONLY",
        "external_acceptance": False,
        "graph_file_sha256": graph_file_sha256,
        "graph_content_sha256": graph_hash,
        "graph_schema_version": "1.0.0",
        "graph_tool_version": graph.tool_version,
        "profile": graph.profile.value,
        "candidates": [item.model_dump(mode="json") for item in candidates],
    }
    return DefinitionReferenceCandidatesDocument(
        schema_version="normshift-definition-reference-candidates/v1",
        authority_kind="LINEAGE_GRAPH_REPLAY_ONLY",
        external_acceptance=False,
        graph_file_sha256=graph_file_sha256,
        graph_content_sha256=graph_hash,
        graph_schema_version="1.0.0",
        graph_tool_version=graph.tool_version,
        profile=graph.profile.value,
        candidates=candidates,
        integrity=Integrity(alg="sha256", content_sha256=integrity_payload_hash(payload)),
    )


def _requirements(graph: LineageGraph) -> dict[str, RequirementInstanceRef]:
    result: dict[str, RequirementInstanceRef] = {}
    for node in graph.nodes:
        for item in node.instances:
            if item.requirement_id in result:
                raise DefinitionReferenceCandidateError(
                    "lineage graph contains duplicate requirement IDs"
                )
            result[item.requirement_id] = item
    return result


def _reject_ambiguous_terms(definitions: list[DefinitionRecord]) -> None:
    seen: set[tuple[str, str]] = set()
    for definition in definitions:
        key = (definition.document_version, _term(definition.term))
        if key in seen:
            raise DefinitionReferenceCandidateError(
                "version has ambiguous lower-normalized definition term"
            )
        seen.add(key)


def _candidate(
    link_id: str,
    requirement: RequirementInstanceRef,
    definition: DefinitionRecord,
) -> DefinitionReferenceCandidate:
    requirement_anchor = RequirementAnchor(
        requirement_id=requirement.requirement_id,
        document_version=requirement.document_version,
        document_sha256=requirement.document_sha256,
    )
    definition_anchor = DefinitionAnchor(
        definition_id=definition.definition_id,
        document_version=definition.document_version,
        document_sha256=definition.document_sha256,
        normalized_term_sha256=_sha(_term(definition.term)),
    )
    candidate_id = _sha(
        "\x1f".join(
            (
                "definition-reference-candidate/v1",
                link_id,
                requirement.requirement_id,
                definition.definition_id,
            )
        )
    )
    return DefinitionReferenceCandidate(
        candidate_id=candidate_id,
        link_id=link_id,
        method="LEXICAL_TERM_OCCURRENCE_CANDIDATE",
        requirement=requirement_anchor,
        definition=definition_anchor,
    )


def _term(value: str) -> str:
    normalized = normalize_whitespace(value).lower()
    if not normalized:
        raise DefinitionReferenceCandidateError("definition term is empty after normalization")
    return normalized


def _sha(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def _sha_required(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise DefinitionReferenceCandidateError(f"{label} must be a lowercase SHA-256 digest")
