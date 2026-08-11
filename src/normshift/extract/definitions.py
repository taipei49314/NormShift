"""Deterministic definition and cross-reference extraction (offline)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from lxml import html

from normshift.model.types import DefinitionRecord, DependencyLink, Requirement
from normshift.normalize.html_normalize import normalize_whitespace

# Prefer multi-word or capitalized single-token terms for prose definitions.
_DEFINED_AS_RE = re.compile(
    r"\b(?P<term>(?:[A-Za-z][A-Za-z0-9_-]{1,40}\s+){0,4}[A-Za-z][A-Za-z0-9_-]{1,40})\b"
    r"\s+(?:is|are|means|shall mean)\s+(?:defined\s+as\s+)?(?P<body>.+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExtractedDefinition:
    term: str
    body: str
    source_locator: str


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower() if "}" in tag else tag.lower()


def extract_definitions_from_html(
    raw_html: bytes,
    *,
    document_version: str,
    document_sha256: str,
) -> list[DefinitionRecord]:
    """Extract definitions from <dfn>, data-term, and 'X is defined as' sentences."""
    try:
        tree = html.fromstring(
            raw_html,
            parser=html.HTMLParser(encoding="utf-8"),
        )
    except Exception:
        return []

    found: list[ExtractedDefinition] = []

    for dfn in tree.xpath("//dfn"):
        term = (dfn.get("data-lt") or dfn.get("title") or "".join(dfn.itertext())).strip()
        if not term:
            continue
        parent = dfn.getparent()
        body = ""
        if parent is not None:
            body = normalize_whitespace("".join(parent.itertext()))
        if not body:
            body = term
        el_id = dfn.get("id") or (parent.get("id") if parent is not None else None)
        locator = f"id:{el_id}" if el_id else f"dfn:{term}"
        found.append(ExtractedDefinition(term=term, body=body, source_locator=locator))

    # Paragraph-level "Term is defined as ..."
    for el in tree.iter():
        if not isinstance(el.tag, str):
            continue
        if _local_name(el.tag) not in {"p", "li", "dd"}:
            continue
        text = normalize_whitespace("".join(el.itertext()))
        m = _DEFINED_AS_RE.search(text)
        if not m:
            continue
        term = normalize_whitespace(m.group("term"))
        body = m.group("body").strip()
        # Drop single-token lowercase noise (e.g. trailing "token" from a dfn phrase)
        if " " not in term and term.islower() and len(term) < 12:
            continue
        el_id = el.get("id")
        locator = f"id:{el_id}" if el_id else f"xpath-def:{term}"
        if any(f.term.lower() == term.lower() for f in found):
            continue
        # Skip if this term is a proper substring of an existing dfn term
        if any(term.lower() in f.term.lower() and term.lower() != f.term.lower() for f in found):
            continue
        found.append(ExtractedDefinition(term=term, body=body, source_locator=locator))

    records: list[DefinitionRecord] = []
    for f in found:
        did = hashlib.sha256(
            f"{document_sha256}\x1f{f.term.lower()}\x1f{normalize_whitespace(f.body)}".encode()
        ).hexdigest()[:16]
        records.append(
            DefinitionRecord(
                definition_id=did,
                term=f.term,
                body=f.body,
                document_version=document_version,
                document_sha256=document_sha256,
                source_locator=f.source_locator,
                normalized_body=normalize_whitespace(f.body).lower(),
            )
        )
    records.sort(key=lambda r: (r.term.lower(), r.definition_id))
    return records


def link_requirements_to_definitions(
    requirements: list[Requirement],
    definitions: list[DefinitionRecord],
) -> list[DependencyLink]:
    """Link requirements that mention a defined term (token-aware)."""
    if not definitions:
        return []
    # Prefer longer terms first to avoid partial overlaps
    terms = sorted({d.term: d for d in definitions}.values(), key=lambda d: -len(d.term))
    links: list[DependencyLink] = []
    for req in requirements:
        text = req.normalized_text
        matched_spans: list[tuple[int, int]] = []
        for dfn in terms:
            term = dfn.term.strip()
            if not term:
                continue
            parts = [re.escape(p) for p in term.split() if p]
            if not parts:
                continue
            pattern = re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.IGNORECASE)
            m = pattern.search(text)
            if not m:
                continue
            # Skip pure definition sentences
            if re.search(r"\bis\s+defined\s+as\b", text, re.I) and m.start() < 80:
                continue
            # Skip if this match is fully inside a longer already-matched span
            span = (m.start(), m.end())
            if any(s <= span[0] and span[1] <= e for s, e in matched_spans):
                continue
            matched_spans.append(span)
            lid = hashlib.sha256(
                f"{req.requirement_id}\x1f{dfn.definition_id}".encode()
            ).hexdigest()[:16]
            links.append(
                DependencyLink(
                    link_id=lid,
                    requirement_id=req.requirement_id,
                    definition_id=dfn.definition_id,
                    document_version=req.document_version,
                    term=dfn.term,
                    evidence=f"term '{dfn.term}' occurs in requirement text",
                )
            )
    links.sort(key=lambda x: (x.document_version, x.requirement_id, x.definition_id))
    return links


def definition_change_edges(
    old_defs: list[DefinitionRecord],
    new_defs: list[DefinitionRecord],
    *,
    from_version: str,
    to_version: str,
) -> list[tuple[str, str, str, str]]:
    """Return (term, old_body, new_body, relation_note) for changed definitions."""
    old_by = {d.term.lower(): d for d in old_defs}
    new_by = {d.term.lower(): d for d in new_defs}
    changes: list[tuple[str, str, str, str]] = []
    for term, nd in sorted(new_by.items()):
        od = old_by.get(term)
        if od is None:
            continue
        if od.normalized_body != nd.normalized_body:
            changes.append((nd.term, od.body, nd.body, "DEFINITION_CHANGED"))
    return changes
