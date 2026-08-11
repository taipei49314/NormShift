"""RFC HTML and RFC XML (rfcxml-ish) adapter."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree, html

from normshift.adapters.base import AdaptedDocument, build_provenance
from normshift.adapters.errors import AdapterParseError
from normshift.adapters.strip import strip_chrome
from normshift.adapters.versioning import version_from_html_bytes, version_from_rfc_xml
from normshift.model.types import DocumentFamily

ADAPTER_ID = "normshift.adapters.rfc"


def _local(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower() if "}" in tag else tag.lower()


def rfc_xml_to_html(raw: bytes) -> bytes:
    """Convert a minimal subset of RFC XML into HTML for the shared normalizer."""
    try:
        root = etree.fromstring(raw)
    except Exception as exc:  # noqa: BLE001
        raise AdapterParseError(f"Invalid RFC XML: {exc}", adapter_id=ADAPTER_ID) from exc

    has_middle = (
        root.find("middle") is not None
        or root.find("{*}middle") is not None
        or root.find(".//middle") is not None
        or root.find(".//{*}middle") is not None
    )
    if _local(root.tag) != "rfc" and not has_middle:
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


class RfcAdapter:
    adapter_id = ADAPTER_ID
    family = DocumentFamily.RFC

    def can_handle(self, path: Path, raw: bytes) -> bool:
        head = raw[:8000].lower()
        if path.suffix.lower() == ".xml":
            return b"<rfc" in head or b"<middle>" in head
        return b"rfc" in head and (
            b"<html" in head
            or b"internet engineering" in head
            or b"request for comments:" in head
        )

    def load(self, path: Path, raw: bytes) -> AdaptedDocument:
        if not raw.strip():
            raise AdapterParseError(f"Empty RFC document: {path}", adapter_id=self.adapter_id)

        try:
            is_xml_like = (
                path.suffix.lower() == ".xml"
                or raw.lstrip().startswith(b"<?xml")
                or b"<rfc" in raw[:2000]
            )
            if is_xml_like and b"<html" not in raw[:500].lower():
                working_src = rfc_xml_to_html(raw)
                version = version_from_rfc_xml(raw)
                content_type = "application/rfc+xml"
            elif is_xml_like:
                working_src = raw
                version = version_from_html_bytes(raw)
                content_type = "text/html"
            else:
                # Validate parseable HTML
                html.fromstring(raw)
                working_src = raw
                version = version_from_html_bytes(raw)
                content_type = "text/html"

            working = strip_chrome(working_src, DocumentFamily.RFC)
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
