"""Pure adjacent-version DefinitionTransition derivation from a verified graph."""

from __future__ import annotations

from hashlib import sha256
from typing import Literal

from normshift.definition_transitions.errors import DefinitionTransitionError
from normshift.definition_transitions.models import (
    DefinitionAnchor,
    DefinitionTransition,
    DefinitionTransitionKind,
    DefinitionTransitionsDocument,
    DefinitionTransitionsIntegrity,
)
from normshift.evidence.hashing import integrity_payload_hash
from normshift.model.types import DefinitionRecord, LineageGraph
from normshift.normalize.html_normalize import normalize_whitespace


def build_definition_transitions(
    graph: LineageGraph, *, graph_file_sha256: str
) -> DefinitionTransitionsDocument:
    """Derive only lexical add/change/remove facts from adjacent graph versions.

    The caller must have obtained ``graph`` through ``verify_lineage_graph_file``.
    This function neither establishes source custody nor infers references or impacts.
    """
    _require_sha256(graph_file_sha256, "graph file SHA-256")
    if len(graph.versions) < 2 or len(graph.versions) != len(graph.document_sha256s):
        raise DefinitionTransitionError("lineage graph has invalid ordered version bindings")
    if graph.schema_version != "1.0.0":
        raise DefinitionTransitionError("lineage graph has an unsupported schema version")
    graph_schema_version: Literal["1.0.0"] = "1.0.0"
    if graph.integrity.get("alg") != "sha256":
        raise DefinitionTransitionError("lineage graph has unsupported integrity algorithm")
    graph_content_sha256 = graph.integrity.get("content_sha256")
    if not isinstance(graph_content_sha256, str):
        raise DefinitionTransitionError("lineage graph is missing its integrity SHA")
    _require_sha256(graph_content_sha256, "graph content SHA-256")

    by_version = _definition_maps(graph)
    transitions: list[DefinitionTransition] = []
    for index in range(len(graph.versions) - 1):
        old_version, new_version = graph.versions[index : index + 2]
        old_defs, new_defs = by_version[old_version], by_version[new_version]
        for term in sorted(set(old_defs) | set(new_defs)):
            old, new = old_defs.get(term), new_defs.get(term)
            if old is None:
                kind = DefinitionTransitionKind.DEFINITION_ADDED
            elif new is None:
                kind = DefinitionTransitionKind.DEFINITION_REMOVED
            elif _normalized_body(old) != _normalized_body(new):
                kind = DefinitionTransitionKind.DEFINITION_CHANGED
            else:
                continue
            transitions.append(_transition(kind, term, old, new))

    payload: dict[str, object] = {
        "schema_version": "normshift-definition-transitions/v1",
        "authority_kind": "LINEAGE_GRAPH_REPLAY_ONLY",
        "external_acceptance": False,
        "graph_file_sha256": graph_file_sha256,
        "graph_content_sha256": graph_content_sha256,
        "graph_schema_version": graph.schema_version,
        "graph_tool_version": graph.tool_version,
        "profile": graph.profile.value,
        "transitions": [item.model_dump(mode="json") for item in transitions],
    }
    return DefinitionTransitionsDocument(
        schema_version="normshift-definition-transitions/v1",
        authority_kind="LINEAGE_GRAPH_REPLAY_ONLY",
        external_acceptance=False,
        graph_file_sha256=graph_file_sha256,
        graph_content_sha256=graph_content_sha256,
        graph_schema_version=graph_schema_version,
        graph_tool_version=graph.tool_version,
        profile=graph.profile.value,
        transitions=transitions,
        integrity=DefinitionTransitionsIntegrity(
            alg="sha256", content_sha256=integrity_payload_hash(payload)
        ),
    )


def _definition_maps(graph: LineageGraph) -> dict[str, dict[str, DefinitionRecord]]:
    expected_hashes = dict(zip(graph.versions, graph.document_sha256s, strict=True))
    maps: dict[str, dict[str, DefinitionRecord]] = {version: {} for version in graph.versions}
    for definition in graph.definitions:
        if definition.document_version not in maps:
            raise DefinitionTransitionError("definition has a version absent from lineage graph")
        if definition.document_sha256 != expected_hashes[definition.document_version]:
            raise DefinitionTransitionError("definition document SHA differs from lineage graph")
        term = _normalized_term(definition)
        if term in maps[definition.document_version]:
            raise DefinitionTransitionError(
                "multiple definitions share one lexical normalized term in a version"
            )
        maps[definition.document_version][term] = definition
    return maps


def _normalized_term(definition: DefinitionRecord) -> str:
    # This deliberately matches DefinitionRecord extraction/ID identity.  Do
    # not use casefold(): it would collapse distinct lexical terms such as ß
    # and ss that the established lower()-based record contract keeps apart.
    value = normalize_whitespace(definition.term).lower()
    if not value:
        raise DefinitionTransitionError("definition term has no lexical normalized identity")
    return value


def _normalized_body(definition: DefinitionRecord) -> str:
    # The graph already carries the exact extraction-time normalized body.
    # Re-normalizing or case-folding here would derive a new, incompatible
    # identity and can silently hide a recorded definition change.
    return definition.normalized_body


def _anchor(definition: DefinitionRecord) -> DefinitionAnchor:
    term = _normalized_term(definition)
    return DefinitionAnchor(
        definition_id=definition.definition_id,
        document_version=definition.document_version,
        document_sha256=definition.document_sha256,
        normalized_term_sha256=_sha(term),
        normalized_body_sha256=_sha(_normalized_body(definition)),
    )


def _transition(
    kind: DefinitionTransitionKind,
    term: str,
    old: DefinitionRecord | None,
    new: DefinitionRecord | None,
) -> DefinitionTransition:
    old_anchor = _anchor(old) if old is not None else None
    new_anchor = _anchor(new) if new is not None else None
    transition_id = _sha(
        "\x1f".join(
            (
                "normshift-definition-transition/v1",
                kind.value,
                term,
                old_anchor.definition_id if old_anchor else "",
                new_anchor.definition_id if new_anchor else "",
                old_anchor.document_sha256 if old_anchor else "",
                new_anchor.document_sha256 if new_anchor else "",
            )
        )
    )
    return DefinitionTransition(
        transition_id=transition_id,
        kind=kind,
        lexical_normalized_term=term,
        old_definition=old_anchor,
        new_definition=new_anchor,
    )


def _sha(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise DefinitionTransitionError(f"{label} must be a lowercase SHA-256 digest")
