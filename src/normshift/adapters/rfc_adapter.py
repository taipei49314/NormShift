"""RFC HTML and RFC XML (rfcxml-ish) adapter."""

from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree, html

from normshift.adapters.base import AdaptedDocument, build_provenance
from normshift.adapters.detect import can_handle_family, require_family
from normshift.adapters.errors import AdapterParseError
from normshift.adapters.ingress import (
    canonicalize_supported_html,
    is_rfc_xml_candidate,
    require_nonempty_normalized_body,
    validate_rfc_xml,
)
from normshift.adapters.strip import strip_chrome
from normshift.adapters.versioning import version_from_html_bytes, version_from_rfc_xml
from normshift.model.types import DocumentFamily

ADAPTER_ID = "normshift.adapters.rfc"
_RFC_EDITOR_HEADING_CLASSES = frozenset({f"h{level}" for level in range(1, 7)})
_PARAGRAPH_BREAK_RE = re.compile(r"(?:\r?\n)[ \t]*(?:\r?\n)+")


def _local(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower() if "}" in tag else tag.lower()


def rfc_xml_to_html(root: etree._Element) -> bytes:
    """Convert a minimal subset of RFC XML into HTML for the shared normalizer."""
    has_middle = (
        root.find("middle") is not None
        or root.find("{*}middle") is not None
        or root.find(".//middle") is not None
        or root.find(".//{*}middle") is not None
    )
    if _local(root.tag) != "rfc" or not has_middle:
        raise AdapterParseError("XML root is not RFC format", adapter_id=ADAPTER_ID)

    parts: list[str] = ["<!DOCTYPE html><html><head><meta charset='utf-8'/>"]
    doc_name = root.get("docName") or root.get("number") or "RFC"
    parts.append(f"<title>{escape(str(doc_name))}</title></head><body>")
    parts.append(f"<h1>{escape(str(doc_name))}</h1>")

    middle = root.find("middle")
    if middle is None:
        middle = root.find("{*}middle")
    sections = []
    if middle is not None:
        sections = [c for c in middle if _local(c.tag) == "section"]
    else:
        sections = [c for c in root.iter() if _local(c.tag) == "section"]

    def emit_section(sec: etree._Element, level: int) -> None:
        title = sec.get("title") or ""
        if not title:
            name_el = sec.find("name")
            if name_el is None:
                name_el = sec.find("{*}name")
            if name_el is not None:
                title = "".join(name_el.itertext()).strip()
        h = max(2, min(level, 6))
        parts.append(f"<h{h}>{escape(title or 'Section')}</h{h}>")
        for child in sec:
            cn = _local(child.tag)
            if cn in {"t", "p"}:
                text = "".join(child.itertext()).strip()
                if text:
                    parts.append(f"<p>{escape(text)}</p>")
            elif cn in {"artwork", "sourcecode", "figure"}:
                # Informative code-like block
                text = "".join(child.itertext())
                parts.append(f"<pre><code>{escape(text)}</code></pre>")
            elif cn == "section":
                emit_section(child, level + 1)
            elif cn in {"ul", "ol", "dl", "list"}:
                for li in child:
                    if _local(li.tag) in {"li", "t"}:
                        text = "".join(li.itertext()).strip()
                        if text:
                            parts.append(f"<li>{escape(text)}</li>")
            elif cn == "aside" or (child.get("type") or "").lower() in {
                "note",
                "example",
            }:
                text = "".join(child.itertext()).strip()
                if text:
                    parts.append(f"<div class='note'><p>{escape(text)}</p></div>")

        # Direct text-only sections
        direct = (sec.text or "").strip()
        if not list(sec) and direct:
            parts.append(f"<p>{escape(direct)}</p>")

    for sec in sections:
        emit_section(sec, 2)

    parts.append("</body></html>")
    return "".join(parts).encode("utf-8")


def _paragraphs_from_pre_text(value: str) -> list[str]:
    paragraphs: list[str] = []
    for chunk in _PARAGRAPH_BREAK_RE.split(value):
        paragraph = " ".join(chunk.split())
        if paragraph:
            paragraphs.append(paragraph)
    return paragraphs


def _flush_pre_text(pending: list[str], parts: list[str]) -> None:
    combined = "".join(pending)
    pending.clear()
    for paragraph in _paragraphs_from_pre_text(combined):
        parts.append(f"<p>{escape(paragraph)}</p>")


def rfc_editor_pre_to_html(raw: bytes) -> bytes:
    """Convert RFC Editor paginated ``pre`` HTML into shared-normalizer blocks."""
    try:
        tree = html.fromstring(raw, parser=html.HTMLParser(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise AdapterParseError(
            f"Invalid RFC Editor HTML: {exc}",
            adapter_id=ADAPTER_ID,
        ) from exc
    pre_nodes = tree.xpath("//pre")
    if not pre_nodes:
        raise AdapterParseError(
            "RFC Editor HTML has no paginated preformatted body",
            adapter_id=ADAPTER_ID,
        )

    parts: list[str] = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>",
        "<title>RFC Editor document</title></head><body>",
    ]
    for pre in pre_nodes:
        pending: list[str] = [pre.text or ""]

        for child in pre:
            class_tokens = {
                token for token in str(child.get("class") or "").lower().split() if token
            }
            heading_classes = sorted(class_tokens & _RFC_EDITOR_HEADING_CLASSES)
            if "grey" in class_tokens:
                # RFC Editor page headers/footers are presentational duplicates.
                _flush_pre_text(pending, parts)
            elif heading_classes:
                _flush_pre_text(pending, parts)
                level = int(heading_classes[0][1])
                heading = " ".join("".join(child.itertext()).split())
                if heading:
                    parts.append(f"<h{level}>{escape(heading)}</h{level}>")
            else:
                pending.append("".join(child.itertext()))
            if child.tail:
                pending.append(child.tail)
        _flush_pre_text(pending, parts)

    parts.append("</body></html>")
    return "".join(parts).encode("utf-8")


class RfcAdapter:
    adapter_id = ADAPTER_ID
    family = DocumentFamily.RFC

    def can_handle(self, path: Path, raw: bytes) -> bool:
        return can_handle_family(path, raw, self.family)

    def load(self, path: Path, raw: bytes) -> AdaptedDocument:
        try:
            require_family(path, raw, self.family, adapter_id=self.adapter_id)
            prefix = raw.lstrip()
            if prefix.startswith(b"\xef\xbb\xbf"):
                prefix = prefix[3:].lstrip()
            prefix = prefix.lower()
            if is_rfc_xml_candidate(raw):
                root = validate_rfc_xml(raw, path=path, adapter_id=self.adapter_id)
                working_src = rfc_xml_to_html(root)
                version = version_from_rfc_xml(root, raw)
                content_type = "application/rfc+xml"
            elif prefix.startswith(b"<pre"):
                canonical = canonicalize_supported_html(raw, path=path, adapter_id=self.adapter_id)
                working_src = rfc_editor_pre_to_html(canonical)
                version = version_from_html_bytes(raw, parse_bytes=canonical)
                content_type = "text/html"
            else:
                canonical = canonicalize_supported_html(
                    raw,
                    path=path,
                    adapter_id=self.adapter_id,
                )
                working_src = canonical
                version = version_from_html_bytes(raw, parse_bytes=canonical)
                content_type = "text/html"

            working = strip_chrome(working_src, DocumentFamily.RFC)
            require_nonempty_normalized_body(working, path=path, adapter_id=self.adapter_id)
        except AdapterParseError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise AdapterParseError(
                f"Failed to parse RFC document: {path}: {exc}",
                adapter_id=self.adapter_id,
            ) from exc

        prov = build_provenance(
            path=path,
            raw=raw,
            family=self.family,
            adapter_id=self.adapter_id,
            content_type=content_type,
        )
        return AdaptedDocument(
            path=path,
            raw_bytes=raw,
            working_html=working,
            provenance=prov,
            document_version=version,
            family=self.family,
        )
