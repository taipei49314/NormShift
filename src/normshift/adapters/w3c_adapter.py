"""W3C TR-style HTML adapter."""

from __future__ import annotations

from pathlib import Path

from lxml import html

from normshift.adapters.base import AdaptedDocument, build_provenance
from normshift.adapters.errors import AdapterParseError
from normshift.adapters.strip import strip_chrome
from normshift.adapters.versioning import version_from_html_bytes
from normshift.model.types import DocumentFamily

ADAPTER_ID = "normshift.adapters.w3c"


class W3cAdapter:
    adapter_id = ADAPTER_ID
    family = DocumentFamily.W3C

    def can_handle(self, path: Path, raw: bytes) -> bool:
        head = raw[:20_000].lower()
        return b"w3c" in head or b"www.w3.org" in head

    def load(self, path: Path, raw: bytes) -> AdaptedDocument:
        if not raw.strip():
            raise AdapterParseError(f"Empty W3C document: {path}", adapter_id=self.adapter_id)
        try:
            tree = html.fromstring(raw)
            # Prefer main content container if present.
            main = tree.find(".//main")
            if main is None:
                xp = "//*[@id='respecDocument' or @id='main' or contains(@class,'body')]"
                for cand in tree.xpath(xp):
                    main = cand
                    break
            if main is not None:
                body_html = html.tostring(main, encoding="unicode", method="html")
                working_src = (
                    "<!DOCTYPE html><html><head><meta charset='utf-8'/></head>"
                    f"<body>{body_html}</body></html>"
                ).encode()
            else:
                working_src = raw
            working = strip_chrome(working_src, DocumentFamily.W3C)
            version = version_from_html_bytes(raw)
        except Exception as exc:  # noqa: BLE001
            raise AdapterParseError(
                f"Failed to parse W3C HTML: {path}: {exc}",
                adapter_id=self.adapter_id,
            ) from exc

        prov = build_provenance(
            path=path,
            raw=raw,
            family=self.family,
            adapter_id=self.adapter_id,
            content_type="text/html",
        )
        return AdaptedDocument(
            path=path,
            raw_bytes=raw,
            working_html=working,
            provenance=prov,
            document_version=version,
            family=self.family,
        )
