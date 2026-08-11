"""Build requirement lineage graphs across multiple document versions."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

from normshift import __version__
from normshift.align.aligner import score_pair
from normshift.align.multi import align_with_multiplicity
from normshift.classify.classifier import classify_pair
from normshift.evidence.hashing import canonical_json_bytes, integrity_payload_hash
from normshift.extract.definitions import (
    definition_change_edges,
    extract_definitions_from_html,
    link_requirements_to_definitions,
)
from normshift.extract.extractor import extract_requirements
from normshift.model.types import (
    AdapterName,
    AmbiguityItem,
    DefinitionRecord,
    DependencyLink,
    LineageEdge,
    LineageGraph,
    LineageNode,
    LineageRelation,
    ProfileName,
    Requirement,
    RequirementInstanceRef,
    RequirementsDocument,
)
from normshift.source import load_immutable_source


def _edge_id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


def _new_lineage_id(seed: str) -> str:
    return "L-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def _initial_lineage_ids(requirements: list[Requirement]) -> dict[str, str]:
    """Bind every initial requirement occurrence to one stable lineage ID.

    A semantic fingerprint is intentionally shared by identical obligations.  It
    therefore cannot be the sole node key: two separately located occurrences
    would overwrite one another.  Preserve the historical semantic ID for a
    unique obligation and add the exact requirement ID only when a semantic
    seed occurs more than once.
    """
    semantic_seeds = {
        requirement.requirement_id: (
            f"{requirement.fingerprint}|{requirement.normalized_text}|"
            f"{requirement.modality.value}"
        )
        for requirement in requirements
    }
    if len(semantic_seeds) != len(requirements):
        raise ValueError("initial document contains duplicate requirement IDs")

    seed_counts = Counter(semantic_seeds.values())
    lineage_ids: dict[str, str] = {}
    owners: dict[str, str] = {}
    for requirement in requirements:
        seed = semantic_seeds[requirement.requirement_id]
        if seed_counts[seed] > 1:
            seed = f"{seed}|occurrence|{requirement.requirement_id}"
        lineage_id = _new_lineage_id(seed)
        prior_owner = owners.get(lineage_id)
        if prior_owner is not None and prior_owner != requirement.requirement_id:
            raise ValueError("initial lineage ID collision")
        owners[lineage_id] = requirement.requirement_id
        lineage_ids[requirement.requirement_id] = lineage_id
    return lineage_ids


def _validate_documents(documents: list[RequirementsDocument]) -> None:
    """Reject ambiguous or internally inconsistent version inputs."""
    document_hashes: set[str] = set()
    document_versions: set[str] = set()
    requirement_ids: set[str] = set()
    for document in documents:
        if document.document_sha256 in document_hashes:
            raise ValueError("lineage contains a duplicate document hash")
        if document.document_version in document_versions:
            raise ValueError("lineage contains a duplicate document version")
        document_hashes.add(document.document_sha256)
        document_versions.add(document.document_version)

        local_ids: set[str] = set()
        for requirement in document.requirements:
            if requirement.requirement_id in local_ids:
                raise ValueError(
                    f"document {document.document_version} contains duplicate requirement IDs"
                )
            if requirement.requirement_id in requirement_ids:
                raise ValueError("lineage contains a repeated requirement ID")
            if requirement.document_sha256 != document.document_sha256:
                raise ValueError("requirement document hash differs from its document")
            if requirement.document_version != document.document_version:
                raise ValueError("requirement version differs from its document")
            local_ids.add(requirement.requirement_id)
            requirement_ids.add(requirement.requirement_id)


def _create_node(
    nodes: dict[str, LineageNode],
    lineage_id: str,
    requirement: Requirement,
    version: str,
) -> None:
    if lineage_id in nodes:
        raise ValueError("lineage ID collision while allocating a new node")
    nodes[lineage_id] = LineageNode(
        lineage_id=lineage_id,
        instances=[_to_instance(requirement, lineage_id)],
        first_version=version,
        last_version=version,
    )


def _require_lineage(
    mapping: dict[str, str],
    nodes: dict[str, LineageNode],
    requirement_id: str,
) -> str:
    lineage_id = mapping.get(requirement_id)
    if lineage_id is None:
        raise ValueError(f"requirement {requirement_id} has no lineage mapping")
    if lineage_id not in nodes:
        raise ValueError(f"lineage mapping references missing node {lineage_id}")
    return lineage_id


def _validate_mapping(
    requirements: list[Requirement],
    mapping: dict[str, str],
    nodes: dict[str, LineageNode],
) -> None:
    expected = {requirement.requirement_id for requirement in requirements}
    if len(expected) != len(requirements):
        raise ValueError("document contains duplicate requirement IDs")
    if set(mapping) != expected:
        raise ValueError("lineage mapping does not cover the exact document requirements")
    for requirement_id in sorted(expected):
        _require_lineage(mapping, nodes, requirement_id)


def _to_instance(req: Requirement, lineage_id: str) -> RequirementInstanceRef:
    return RequirementInstanceRef(
        lineage_id=lineage_id,
        requirement_id=req.requirement_id,
        document_version=req.document_version,
        document_sha256=req.document_sha256,
        section_path=req.section_path,
        source_locator=req.source_locator,
        modality=req.modality,
        original_text=req.original_text,
        normalized_text=req.normalized_text,
        actor=req.actor,
        action=req.action,
        condition=req.condition,
        exception=req.exception,
        fingerprint=req.fingerprint,
    )


def _append_instance(
    nodes: dict[str, LineageNode],
    lid: str,
    req: Requirement,
    version: str,
) -> None:
    if lid not in nodes:
        raise ValueError(f"cannot append to missing lineage node {lid}")
    node = nodes[lid]
    inst = _to_instance(req, lid)
    if any(i.requirement_id == inst.requirement_id for i in node.instances):
        return
    node.instances.append(inst)
    node.last_version = version


def build_lineage_graph(
    paths: list[Path],
    *,
    profile: ProfileName,
    adapter: AdapterName = AdapterName.AUTO,
) -> LineageGraph:
    if len(paths) < 2:
        raise ValueError("lineage requires at least two document versions")

    # Single immutable load per path — extract + definitions share the same bytes
    sources = [load_immutable_source(p, adapter=adapter) for p in paths]
    docs = [
        extract_requirements(p, profile, adapter=adapter, source=s)
        for p, s in zip(paths, sources, strict=True)
    ]
    _validate_documents(docs)
    versions = [d.document_version for d in docs]
    sha256s = [d.document_sha256 for d in docs]

    all_definitions: list[DefinitionRecord] = []
    all_dep_links: list[DependencyLink] = []
    defs_by_version: list[list[DefinitionRecord]] = []
    for src, doc in zip(sources, docs, strict=True):
        defs = extract_definitions_from_html(
            src.working_html,
            document_version=doc.document_version,
            document_sha256=doc.document_sha256,
        )
        links = link_requirements_to_definitions(doc.requirements, defs)
        all_definitions.extend(defs)
        all_dep_links.extend(links)
        defs_by_version.append(defs)

    nodes: dict[str, LineageNode] = {}
    edges: list[LineageEdge] = []

    prev_lineage: dict[str, str] = {}

    initial_lineage_ids = _initial_lineage_ids(docs[0].requirements)
    for req in docs[0].requirements:
        lid = initial_lineage_ids[req.requirement_id]
        prev_lineage[req.requirement_id] = lid
        _create_node(nodes, lid, req, req.document_version)
    _validate_mapping(docs[0].requirements, prev_lineage, nodes)

    for i in range(len(docs) - 1):
        old_doc, new_doc = docs[i], docs[i + 1]
        _validate_mapping(old_doc.requirements, prev_lineage, nodes)
        multi = align_with_multiplicity(old_doc.requirements, new_doc.requirements)
        v_old, v_new = old_doc.document_version, new_doc.document_version

        claimed_new: set[str] = set()
        claimed_old: set[str] = set()
        next_lineage: dict[str, str] = {}

        split_old_ids = set(multi.splits.keys())
        merge_new_ids = set(multi.merges.keys())

        # 1) SPLITS first (consume old + children)
        for oid, children in multi.splits.items():
            if len(children) < 2:
                continue
            parent_lid = _require_lineage(prev_lineage, nodes, oid)
            claimed_old.add(oid)
            for idx, (nreq, sc) in enumerate(children):
                if nreq.requirement_id in claimed_new:
                    continue
                if idx == 0:
                    child_lid = parent_lid
                    _append_instance(nodes, child_lid, nreq, v_new)
                else:
                    child_lid = _new_lineage_id(f"split|{oid}|{nreq.requirement_id}")
                    _create_node(nodes, child_lid, nreq, v_new)
                next_lineage[nreq.requirement_id] = child_lid
                claimed_new.add(nreq.requirement_id)
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("split", oid, nreq.requirement_id, v_old, v_new),
                        relation=LineageRelation.SPLIT_INTO,
                        from_lineage_id=parent_lid,
                        to_lineage_id=child_lid,
                        from_requirement_id=oid,
                        to_requirement_id=nreq.requirement_id,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification="SPLIT",
                        confidence=round(sc, 4),
                        reasons=[
                            f"Split child {idx + 1}/{len(children)} from parent {oid}."
                        ],
                        alignment_combined=round(sc, 4),
                    )
                )

        # 2) MERGES
        for nid, parents in multi.merges.items():
            if len(parents) < 2 or nid in claimed_new:
                continue
            nreq = next(r for r in new_doc.requirements if r.requirement_id == nid)
            parents_sorted = sorted(parents, key=lambda t: (-t[1], t[0].requirement_id))
            primary_old, primary_sc = parents_sorted[0]
            primary_lid = _require_lineage(
                prev_lineage,
                nodes,
                primary_old.requirement_id,
            )
            _append_instance(nodes, primary_lid, nreq, v_new)
            next_lineage[nid] = primary_lid
            claimed_new.add(nid)
            for oreq, sc in parents_sorted:
                claimed_old.add(oreq.requirement_id)
                olid = _require_lineage(prev_lineage, nodes, oreq.requirement_id)
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("merge", oreq.requirement_id, nid, v_old, v_new),
                        relation=LineageRelation.MERGED_FROM,
                        from_lineage_id=olid,
                        to_lineage_id=primary_lid,
                        from_requirement_id=oreq.requirement_id,
                        to_requirement_id=nid,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification="MERGED",
                        confidence=round(sc, 4),
                        reasons=[f"Merged into {nid} (primary score {primary_sc:.4f})."],
                        alignment_combined=round(sc, 4),
                    )
                )

        # 3) Primary continues / add / remove
        for pair in multi.primary:
            if pair.old and pair.new:
                oid, nid = pair.old.requirement_id, pair.new.requirement_id
                if oid in split_old_ids or nid in merge_new_ids:
                    continue
                if oid in claimed_old or nid in claimed_new:
                    continue
                lid = _require_lineage(prev_lineage, nodes, oid)
                ch = classify_pair(pair)
                _append_instance(nodes, lid, pair.new, v_new)
                next_lineage[nid] = lid
                claimed_old.add(oid)
                claimed_new.add(nid)
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("cont", oid, nid, v_old, v_new),
                        relation=LineageRelation.CONTINUES,
                        from_lineage_id=lid,
                        to_lineage_id=lid,
                        from_requirement_id=oid,
                        to_requirement_id=nid,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification=ch.classification.value,
                        confidence=ch.confidence,
                        reasons=list(ch.classification_reasons),
                        alignment_combined=pair.score.combined if pair.score else None,
                    )
                )
            elif pair.old and not pair.new:
                oid = pair.old.requirement_id
                if oid in claimed_old or oid in split_old_ids:
                    continue
                from_lid = _require_lineage(prev_lineage, nodes, oid)
                claimed_old.add(oid)
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("rem", oid, v_old, v_new),
                        relation=LineageRelation.REMOVED,
                        from_lineage_id=from_lid,
                        to_lineage_id=None,
                        from_requirement_id=oid,
                        to_requirement_id=None,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification="REMOVED",
                        confidence=0.95,
                        reasons=["No successor instance in next version."],
                    )
                )
            elif pair.new and not pair.old:
                nid = pair.new.requirement_id
                if nid in claimed_new or nid in merge_new_ids:
                    continue
                nreq = pair.new
                lid = _new_lineage_id(f"add|{nreq.fingerprint}|{nid}")
                _create_node(nodes, lid, nreq, v_new)
                next_lineage[nid] = lid
                claimed_new.add(nid)
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("add", nid, v_old, v_new),
                        relation=LineageRelation.ADDED,
                        from_lineage_id=None,
                        to_lineage_id=lid,
                        from_requirement_id=None,
                        to_requirement_id=nid,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification="ADDED",
                        confidence=0.95,
                        reasons=["No prior instance in previous version."],
                    )
                )

        # Leftover olds
        for oreq in old_doc.requirements:
            if oreq.requirement_id in claimed_old:
                continue
            from_lid2 = _require_lineage(
                prev_lineage,
                nodes,
                oreq.requirement_id,
            )
            edges.append(
                LineageEdge(
                    edge_id=_edge_id("rem2", oreq.requirement_id, v_old, v_new),
                    relation=LineageRelation.REMOVED,
                    from_lineage_id=from_lid2,
                    to_lineage_id=None,
                    from_requirement_id=oreq.requirement_id,
                    to_requirement_id=None,
                    from_version=v_old,
                    to_version=v_new,
                    change_classification="REMOVED",
                    confidence=0.7,
                    reasons=["Unlinked old requirement after multi-align."],
                )
            )

        # Leftover news
        for nreq in new_doc.requirements:
            if nreq.requirement_id in claimed_new:
                continue
            best: tuple[float, Requirement] | None = None
            for oreq in old_doc.requirements:
                sc = score_pair(oreq, nreq).combined
                if best is None or sc > best[0]:
                    best = (sc, oreq)
            if best and best[0] >= 0.62 and best[1].requirement_id in prev_lineage:
                lid = prev_lineage[best[1].requirement_id]
                _append_instance(nodes, lid, nreq, v_new)
                next_lineage[nreq.requirement_id] = lid
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("soft", best[1].requirement_id, nreq.requirement_id),
                        relation=LineageRelation.CONTINUES,
                        from_lineage_id=lid,
                        to_lineage_id=lid,
                        from_requirement_id=best[1].requirement_id,
                        to_requirement_id=nreq.requirement_id,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification="AMBIGUOUS",
                        confidence=round(best[0], 4),
                        reasons=["Soft-linked unmatched new to best old."],
                        alignment_combined=round(best[0], 4),
                    )
                )
            else:
                lid = _new_lineage_id(f"add2|{nreq.fingerprint}|{nreq.requirement_id}")
                _create_node(nodes, lid, nreq, v_new)
                next_lineage[nreq.requirement_id] = lid
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("add2", nreq.requirement_id, v_old, v_new),
                        relation=LineageRelation.ADDED,
                        from_lineage_id=None,
                        to_lineage_id=lid,
                        from_requirement_id=None,
                        to_requirement_id=nreq.requirement_id,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification="ADDED",
                        confidence=0.85,
                        reasons=["Unlinked new requirement after multi-align."],
                    )
                )

        _validate_mapping(new_doc.requirements, next_lineage, nodes)
        prev_lineage = next_lineage

        # Definition change edges between consecutive versions
        if i < len(defs_by_version) - 1:
            for term, old_body, new_body, _note in definition_change_edges(
                defs_by_version[i],
                defs_by_version[i + 1],
                from_version=v_old,
                to_version=v_new,
            ):
                edges.append(
                    LineageEdge(
                        edge_id=_edge_id("defchg", term, v_old, v_new),
                        relation=LineageRelation.DEFINITION_CHANGED,
                        from_lineage_id=None,
                        to_lineage_id=None,
                        from_requirement_id=None,
                        to_requirement_id=None,
                        from_version=v_old,
                        to_version=v_new,
                        change_classification="DEFINITION_CHANGED",
                        confidence=0.9,
                        reasons=[
                            f"Definition of '{term}' changed.",
                            f"old: {old_body[:120]}",
                            f"new: {new_body[:120]}",
                        ],
                    )
                )
                # DEPENDS_ON edges for requirements linked to this term in new version
                for link in all_dep_links:
                    if link.document_version != v_new:
                        continue
                    if link.term.lower() != term.lower():
                        continue
                    dep_lid = _require_lineage(
                        next_lineage,
                        nodes,
                        link.requirement_id,
                    )
                    edges.append(
                        LineageEdge(
                            edge_id=_edge_id(
                                "depends", link.requirement_id, term, v_old, v_new
                            ),
                            relation=LineageRelation.DEPENDS_ON,
                            from_lineage_id=dep_lid,
                            to_lineage_id=dep_lid,
                            from_requirement_id=link.requirement_id,
                            to_requirement_id=link.requirement_id,
                            from_version=v_old,
                            to_version=v_new,
                            change_classification="DEFINITION_CHANGED",
                            confidence=0.85,
                            reasons=[
                                f"Requirement depends on definition term '{term}'.",
                                link.evidence,
                            ],
                        )
                    )

        # Per-version REFERENCES_DEFINITION edges (within new version)
        for link in all_dep_links:
            if link.document_version != v_new:
                continue
            ref_lid = _require_lineage(
                next_lineage,
                nodes,
                link.requirement_id,
            )
            edges.append(
                LineageEdge(
                    edge_id=_edge_id("refdef", link.link_id, v_new),
                    relation=LineageRelation.REFERENCES_DEFINITION,
                    from_lineage_id=ref_lid,
                    to_lineage_id=None,
                    from_requirement_id=link.requirement_id,
                    to_requirement_id=None,
                    from_version=v_new,
                    to_version=v_new,
                    change_classification=None,
                    confidence=0.9,
                    reasons=[link.evidence, f"definition_id={link.definition_id}"],
                )
            )

    ambiguity = _collect_ambiguity(docs)
    node_list = sorted(nodes.values(), key=lambda n: n.lineage_id)
    edge_list = sorted(edges, key=lambda e: (e.from_version, e.to_version, e.edge_id))
    summary: dict[str, Any] = {
        "version_count": len(versions),
        "lineage_count": len(node_list),
        "edge_count": len(edge_list),
        "ambiguity_count": len(ambiguity),
        "definition_count": len(all_definitions),
        "dependency_link_count": len(all_dep_links),
        "relation_counts": _count_relations(edge_list),
    }

    graph = LineageGraph(
        tool_version=__version__,
        profile=profile,
        versions=versions,
        document_sha256s=sha256s,
        nodes=node_list,
        edges=edge_list,
        definitions=sorted(all_definitions, key=lambda d: (d.document_version, d.term)),
        dependency_links=sorted(
            all_dep_links, key=lambda d: (d.document_version, d.requirement_id, d.term)
        ),
        ambiguity_queue=ambiguity,
        summary=summary,
        integrity={"alg": "sha256", "content_sha256": ""},
    )
    data = graph.model_dump(mode="json")
    graph.integrity = {"alg": "sha256", "content_sha256": integrity_payload_hash(data)}
    return graph


def _count_relations(edges: list[LineageEdge]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in edges:
        counts[e.relation.value] = counts.get(e.relation.value, 0) + 1
    return dict(sorted(counts.items()))


def _collect_ambiguity(docs: list[RequirementsDocument]) -> list[AmbiguityItem]:
    items: list[AmbiguityItem] = []
    for i in range(len(docs) - 1):
        multi = align_with_multiplicity(docs[i].requirements, docs[i + 1].requirements)
        pair_key = f"{docs[i].document_version}->{docs[i + 1].document_version}"
        for a in multi.ambiguity:
            kind = str(a.get("kind"))
            olds = a.get("olds")
            news = a.get("news")
            if isinstance(olds, list):
                old_ids = [str(x) for x in olds]
            elif "old" in a:
                old_ids = [str(a["old"])]
            else:
                old_ids = []
            if isinstance(news, list):
                new_ids = [str(x) for x in news]
            elif "new" in a:
                new_ids = [str(a["new"])]
            else:
                new_ids = []
            raw_scores = a.get("scores")
            score_list: list[float] = []
            if isinstance(raw_scores, list):
                score_list = [float(x) for x in raw_scores]
            items.append(
                AmbiguityItem(
                    item_id=_edge_id(pair_key, kind, ",".join(old_ids), ",".join(new_ids)),
                    version_pair=pair_key,
                    kind=kind,
                    old_requirement_ids=old_ids,
                    new_requirement_ids=new_ids,
                    detail=str(a),
                    scores=score_list,
                )
            )
    items.sort(key=lambda x: x.item_id)
    return items


def write_lineage_graph(graph: LineageGraph, path: Path) -> str:
    from normshift.io_safety import atomic_write_bytes

    data = graph.model_dump(mode="json")
    digest = integrity_payload_hash(data)
    data["integrity"] = {"alg": "sha256", "content_sha256": digest}
    raw = canonical_json_bytes(data)
    atomic_write_bytes(path, raw)
    return hashlib.sha256(raw).hexdigest()
