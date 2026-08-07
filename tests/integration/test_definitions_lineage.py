"""Definition / dependency linkage on multi-version lineage."""

from __future__ import annotations

from pathlib import Path

from normshift.extract.definitions import (
    extract_definitions_from_html,
    link_requirements_to_definitions,
)
from normshift.extract.extractor import extract_requirements
from normshift.lineage.builder import build_lineage_graph
from normshift.model.types import AdapterName, LineageRelation, ProfileName
from normshift.snapshot import snapshot_document

ROOT = Path(__file__).resolve().parents[2]
LIN = ROOT / "fixtures" / "lineage"


def test_definitions_extracted_from_fixture() -> None:
    path = LIN / "v1.html"
    snap, working, _ = snapshot_document(path, adapter=AdapterName.HTML)
    defs = extract_definitions_from_html(
        working,
        document_version=snap.version,
        document_sha256=snap.sha256,
    )
    assert any(d.term.lower() == "session token" for d in defs)
    doc = extract_requirements(path, ProfileName.RFC2119, adapter=AdapterName.HTML)
    links = link_requirements_to_definitions(doc.requirements, defs)
    assert links, "requirements that mention session token must link to definition"
    assert all(link.term.lower() == "session token" for link in links)


def test_lineage_graph_has_dependency_and_def_change() -> None:
    paths = [LIN / "v1.html", LIN / "v2.html", LIN / "v3.html"]
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    assert len(graph.versions) == 3
    assert graph.definitions, "expected definitions on lineage graph"
    assert graph.dependency_links, "expected dependency_links on lineage graph"
    rels = {e.relation for e in graph.edges}
    assert LineageRelation.REFERENCES_DEFINITION in rels
    assert LineageRelation.DEFINITION_CHANGED in rels or LineageRelation.DEPENDS_ON in rels
    # Identity not only add/remove
    rc = graph.summary.get("relation_counts") or {}
    continues = int(rc.get("CONTINUES", 0)) + int(rc.get("SPLIT_INTO", 0))
    assert continues >= 1
    multi = [n for n in graph.nodes if len(n.instances) >= 2]
    assert multi
