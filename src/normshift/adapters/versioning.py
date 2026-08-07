"""Document version extraction shared by adapters."""

from __future__ import annotations

import hashlib
import re

from lxml import etree, html


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version_from_html_bytes(raw: bytes) -> str:
    try:
        tree = html.fromstring(raw)
    except Exception:
        return f"sha256:{sha256_bytes(raw)[:12]}"

    for name in ("version", "doc-version", "document-version", "spec-version"):
        metas = tree.xpath(f'//meta[@name="{name}"]/@content')
        if metas and str(metas[0]).strip():
            return str(metas[0]).strip()

    for attr in ("data-version", "data-spec-version"):
        vals = tree.xpath(f"//*[@{attr}]/@{attr}")
        if vals and str(vals[0]).strip():
            return str(vals[0]).strip()

    # RFC number + series info
    titles = tree.xpath("//title")
    if titles:
        t = " ".join(titles[0].itertext()).strip()
        m = re.search(r"\bRFC\s*(\d+)\b", t, re.I)
        if m:
            return f"RFC{m.group(1)}"

    h1s = tree.xpath("//h1")
    if h1s:
        text = " ".join(h1s[0].itertext()).strip()
        m = re.search(r"\bv(?:ersion\s*)?(\d+(?:\.\d+)*)\b", text, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"\bRFC\s*(\d+)\b", text, re.I)
        if m:
            return f"RFC{m.group(1)}"

    return f"sha256:{sha256_bytes(raw)[:12]}"


def version_from_rfc_xml(raw: bytes) -> str:
    try:
        root = etree.fromstring(raw)
    except Exception:
        return f"sha256:{sha256_bytes(raw)[:12]}"
    doc_name = root.get("docName") or root.get("number")
    if doc_name:
        return str(doc_name)
    return f"sha256:{sha256_bytes(raw)[:12]}"
