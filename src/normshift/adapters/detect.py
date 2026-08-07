"""Document family auto-detection from path + content (offline, deterministic)."""

from __future__ import annotations

import re
from pathlib import Path

from normshift.adapters.errors import AdapterDetectionError
from normshift.model.types import DocumentFamily

_RFC_HTML_MARKERS = (
    re.compile(rb"docName\s*=\s*[\"']?rfc", re.I),
    re.compile(rb"id=[\"']rfc\.", re.I),
    re.compile(rb"Internet.Draft|Internet.Engineering.Task.Force|RFC\s+\d+", re.I),
    re.compile(rb"class=[\"'][^\"']*rfc[^\"']*[\"']", re.I),
)
_RFC_XML_MARKERS = (
    re.compile(rb"<rfc[\s>]", re.I),
    re.compile(rb"xmlns=.*ietf", re.I),
    re.compile(rb"<middle>", re.I),
)
_W3C_MARKERS = (
    re.compile(rb"www\.w3\.org", re.I),
    re.compile(rb"W3C\s+(Recommendation|Working\s+Draft|Candidate)", re.I),
    re.compile(rb"id=[\"']w3c-state[\"']", re.I),
    re.compile(rb"class=[\"'][^\"']*head[^\"']*[\"']", re.I),
)
_WHATWG_MARKERS = (
    re.compile(rb"whatwg\.org", re.I),
    re.compile(rb"Living\s+Standard", re.I),
    re.compile(rb"id=[\"']whatwg[\"']", re.I),
    re.compile(rb"rel=[\"']canonical[\"'][^>]+whatwg", re.I),
)


def detect_family(path: Path, raw: bytes) -> DocumentFamily:
    """Score content markers; require a clear winner or fall back to generic HTML."""
    suffix = path.suffix.lower()
    scores: dict[DocumentFamily, int] = {
        DocumentFamily.RFC: 0,
        DocumentFamily.W3C: 0,
        DocumentFamily.WHATWG: 0,
        DocumentFamily.GENERIC_HTML: 0,
    }

    # Path hints are weak (never sole identity) — content markers dominate.
    name = path.name.lower()
    parent = path.parent.name.lower()
    if "rfc" in name or "rfc" in parent or (suffix == ".xml" and b"<rfc" in raw[:2000].lower()):
        scores[DocumentFamily.RFC] += 1
    if "w3c" in name or "w3c" in parent or "tr-" in name:
        scores[DocumentFamily.W3C] += 1
    if "whatwg" in name or "whatwg" in parent or "html-ls" in name:
        scores[DocumentFamily.WHATWG] += 1

    head = raw[:80_000]
    for cre in _RFC_XML_MARKERS:
        if cre.search(head):
            scores[DocumentFamily.RFC] += 3
    for cre in _RFC_HTML_MARKERS:
        if cre.search(head):
            scores[DocumentFamily.RFC] += 2
    for cre in _W3C_MARKERS:
        if cre.search(head):
            scores[DocumentFamily.W3C] += 2
    for cre in _WHATWG_MARKERS:
        if cre.search(head):
            scores[DocumentFamily.WHATWG] += 2

    # XML that is not RFC is not auto-handled as HTML.
    if suffix == ".xml" and scores[DocumentFamily.RFC] == 0 and b"<html" not in head.lower():
        raise AdapterDetectionError(
            f"XML file is not recognized as RFC XML: {path}",
            adapter_id="normshift.adapters.auto",
        )

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0].value))
    best_family, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    if best_score == 0:
        if suffix in {".html", ".htm", ".xhtml"} or b"<html" in head.lower():
            return DocumentFamily.GENERIC_HTML
        raise AdapterDetectionError(
            f"Unable to detect document family for: {path}",
            adapter_id="normshift.adapters.auto",
        )

    # Ambiguous top scores → prefer explicit path family, else generic if HTML.
    if best_score == second_score and best_score > 0:
        if suffix in {".html", ".htm"}:
            return DocumentFamily.GENERIC_HTML
        raise AdapterDetectionError(
            f"Ambiguous document family for: {path} (scores={dict(scores)})",
            adapter_id="normshift.adapters.auto",
        )

    return best_family
