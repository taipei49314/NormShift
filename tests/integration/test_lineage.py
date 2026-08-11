"""M2 lineage graph integration tests."""

from __future__ import annotations

from pathlib import Path

from normshift.extract.extractor import extract_requirements
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
        "</body></html>",
        encoding="utf-8",
    )
    second.write_text(
        "<html><head><title>v2</title></head><body>"
        "<h1>Requirements</h1>"
        "<p>The client MUST store the session token.</p>"
        "<p>The client MUST store the session token.</p>"
        "<p>The server MAY discard an expired token.</p>"
        "</body></html>",
        encoding="utf-8",
    )

    first_doc = extract_requirements(
        first,
        ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    assert len(first_doc.requirements) == 2
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
