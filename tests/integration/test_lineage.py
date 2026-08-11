"""M2 lineage graph integration tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from normshift.extract.extractor import extract_requirements
from normshift.lineage import builder as lineage_builder
from normshift.lineage.builder import build_lineage_graph, write_lineage_graph
from normshift.model.types import AdapterName, LineageRelation, ProfileName

ROOT = Path(__file__).resolve().parents[2]
LIN = ROOT / "fixtures" / "lineage"


def test_three_version_lineage_identity(tmp_path: Path) -> None:
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    assert len(graph.versions) == 3
    assert len(graph.nodes) >= 2

    # At least one lineage spans multiple versions (persistent identity)
    multi = [n for n in graph.nodes if len(n.instances) >= 2]
    assert multi, "expected persistent lineage across versions"

    # Relations present in multi-version graph
    rels = {e.relation for e in graph.edges}
    assert LineageRelation.CONTINUES in rels or LineageRelation.SPLIT_INTO in rels

    out = tmp_path / "lineage.json"
    digest = write_lineage_graph(graph, out)
    assert out.is_file()
    assert len(digest) == 64
    # Integrity present
    import json

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["integrity"]["content_sha256"]


def test_lineage_not_only_add_remove() -> None:
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    rel_counts = graph.summary.get("relation_counts") or {}
    continues = rel_counts.get("CONTINUES", 0) + rel_counts.get("SPLIT_INTO", 0)
    # Must not degrade entirely to add/remove
    assert continues >= 1
    assert graph.summary.get("definition_count", 0) >= 1
    assert graph.summary.get("dependency_link_count", 0) >= 1


def test_identical_requirement_occurrences_keep_distinct_lineages(tmp_path: Path) -> None:
    first = tmp_path / "v1.html"
    second = tmp_path / "v2.html"
    first.write_text(
        "<html><head><title>v1</title></head><body>"
        "<h1>Requirements</h1>"
        "<p>The client MUST store the session token.</p>"
        "<p>The client MUST store the session token.</p>"
        "<p>The server MAY discard an expired token.</p>"
        "</body></html>",
        encoding="utf-8",
    )
    second.write_text(
        "<html><head><title>v2</title></head><body>"
        "<h1>Requirements</h1>"
        "<p>The client MUST store the session token.</p>"
        "<p>The client MUST store the session token.</p>"
        "<p>The server MAY discard an expired token.</p>"
        "<p>The client SHOULD rotate the session token.</p>"
        "</body></html>",
        encoding="utf-8",
    )

    first_doc = extract_requirements(
        first,
        ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    assert len(first_doc.requirements) == 3
    graph = build_lineage_graph(
        [first, second],
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )

    expected_ids = {requirement.requirement_id for requirement in first_doc.requirements}
    first_instances = [
        instance
        for node in graph.nodes
        for instance in node.instances
        if instance.document_sha256 == first_doc.document_sha256
    ]
    assert {instance.requirement_id for instance in first_instances} == expected_ids
    assert len(first_instances) == len(expected_ids)
    assert len({instance.lineage_id for instance in first_instances}) == len(expected_ids)

    initial_ids = lineage_builder._initial_lineage_ids(first_doc.requirements)
    reversed_ids = lineage_builder._initial_lineage_ids(
        list(reversed(first_doc.requirements))
    )
    assert initial_ids == reversed_ids
    unique = next(
        requirement
        for requirement in first_doc.requirements
        if requirement.normalized_text == "The server MAY discard an expired token."
    )
    legacy_seed = f"{unique.fingerprint}|{unique.normalized_text}|{unique.modality.value}"
    expected_legacy_id = "L-" + hashlib.sha256(legacy_seed.encode()).hexdigest()[:12]
    assert initial_ids[unique.requirement_id] == expected_legacy_id


def test_duplicate_requirement_id_in_later_version_fails_closed(tmp_path: Path) -> None:
    first = tmp_path / "v1.html"
    second = tmp_path / "v2.html"
    first.write_text("<p>The client MUST retain a token.</p>", encoding="utf-8")
    second.write_text("<p>The server MAY discard a token.</p>", encoding="utf-8")
    first_doc = extract_requirements(
        first,
        ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    second_doc = extract_requirements(
        second,
        ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    duplicate = second_doc.requirements[0]
    invalid_second = second_doc.model_copy(
        update={"requirements": [duplicate, duplicate.model_copy()]}
    )

    with pytest.raises(ValueError, match="duplicate requirement IDs"):
        lineage_builder._validate_documents([first_doc, invalid_second])


def test_initial_lineage_hash_collision_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "v1.html"
    source.write_text(
        "<p>The client MUST retain a token.</p>"
        "<p>The server MAY discard an expired token.</p>",
        encoding="utf-8",
    )
    document = extract_requirements(
        source,
        ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    assert len(document.requirements) == 2
    monkeypatch.setattr(lineage_builder, "_new_lineage_id", lambda _seed: "L-collision")

    with pytest.raises(ValueError, match="initial lineage ID collision"):
        lineage_builder._initial_lineage_ids(document.requirements)


def test_later_lineage_hash_collision_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "v1.html"
    second = tmp_path / "v2.html"
    first.write_text("<p>The client MUST retain a token.</p>", encoding="utf-8")
    second.write_text(
        "<p>The server MAY erase an expired cache entry after thirty days.</p>",
        encoding="utf-8",
    )
    monkeypatch.setattr(lineage_builder, "_new_lineage_id", lambda _seed: "L-collision")

    with pytest.raises(ValueError, match="lineage ID collision"):
        build_lineage_graph(
            [first, second],
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_empty_requirement_version_fails_closed(tmp_path: Path) -> None:
    first = tmp_path / "v1.html"
    second = tmp_path / "v2.html"
    first.write_text("<p>The client MUST retain a token.</p>", encoding="utf-8")
    second.write_text("<p>This version contains background prose only.</p>", encoding="utf-8")

    with pytest.raises(ValueError, match="contains no requirements"):
        build_lineage_graph(
            [first, second],
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_graph_edge_id_collision_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    monkeypatch.setattr(lineage_builder, "_edge_id", lambda *_parts: "edge-collision")

    with pytest.raises(ValueError, match="duplicate edge IDs"):
        build_lineage_graph(
            paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_graph_evidence_validation_rejects_tampered_instance() -> None:
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    documents = [
        extract_requirements(
            path,
            ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
        for path in paths
    ]
    graph = build_lineage_graph(
        paths,
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    nodes = [node.model_copy(deep=True) for node in graph.nodes]
    nodes[0].instances[0] = nodes[0].instances[0].model_copy(
        update={"source_locator": "id:tampered"}
    )

    with pytest.raises(ValueError, match="differs from exact requirement evidence"):
        lineage_builder._validate_graph_evidence(
            documents,
            nodes,
            graph.edges,
            graph.definitions,
            graph.dependency_links,
            graph.ambiguity_queue,
        )


def test_definition_dependency_edges_trace_consecutive_instances() -> None:
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    graph = build_lineage_graph(
        paths,
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    instances = {
        instance.requirement_id: instance
        for node in graph.nodes
        for instance in node.instances
    }
    dependency_edges = [
        edge for edge in graph.edges if edge.relation == LineageRelation.DEPENDS_ON
    ]
    assert dependency_edges
    for edge in dependency_edges:
        assert edge.from_requirement_id is not None
        assert edge.to_requirement_id is not None
        old_instance = instances[edge.from_requirement_id]
        new_instance = instances[edge.to_requirement_id]
        assert old_instance.document_version == edge.from_version
        assert new_instance.document_version == edge.to_version
        assert old_instance.lineage_id == edge.from_lineage_id
        assert new_instance.lineage_id == edge.to_lineage_id


@pytest.mark.parametrize("missing_field", ["from_lineage_id", "from_requirement_id"])
def test_graph_evidence_rejects_half_bound_edge_side(missing_field: str) -> None:
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    documents = [
        extract_requirements(
            path,
            ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
        for path in paths
    ]
    graph = build_lineage_graph(
        paths,
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    edge_index = next(
        index
        for index, edge in enumerate(graph.edges)
        if edge.from_lineage_id is not None and edge.from_requirement_id is not None
    )
    edges = [edge.model_copy(deep=True) for edge in graph.edges]
    edges[edge_index] = edges[edge_index].model_copy(update={missing_field: None})

    with pytest.raises(ValueError, match="requirement and node must be present together"):
        lineage_builder._validate_graph_evidence(
            documents,
            graph.nodes,
            edges,
            graph.definitions,
            graph.dependency_links,
            graph.ambiguity_queue,
        )


def test_valid_merge_retains_each_parent_edge(tmp_path: Path) -> None:
    first = tmp_path / "v1.html"
    second = tmp_path / "v2.html"
    first.write_text(
        "<p>The client MUST validate the token signature.</p>"
        "<p>The client MUST validate the token expiration.</p>",
        encoding="utf-8",
    )
    second.write_text(
        "<p>The client MUST validate the token signature and token expiration.</p>",
        encoding="utf-8",
    )
    graph = build_lineage_graph(
        [first, second],
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )

    merge_edges = [
        edge for edge in graph.edges if edge.relation == LineageRelation.MERGED_FROM
    ]
    assert len(merge_edges) == 2
    assert len({edge.from_requirement_id for edge in merge_edges}) == 2
    assert len({edge.to_requirement_id for edge in merge_edges}) == 1
