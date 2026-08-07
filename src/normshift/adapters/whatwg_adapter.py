"""WHATWG Living Standard-style HTML adapter."""

from __future__ import annotations

from pathlib import Path

from lxml import html

from normshift.adapters.base import AdaptedDocument, build_provenance
from normshift.adapters.errors import AdapterParseError
from normshift.adapters.strip import strip_chrome
from normshift.adapters.versioning import version_from_html_bytes
from normshift.model.types import DocumentFamily

ADAPTER_ID = "normshift.adapters.whatwg"


class WhatwgAdapter:
    adapter_id = ADAPTER_ID
    family = DocumentFamily.WHATWG

    def can_handle(self, path: Path, raw: bytes) -> bool:
        head = raw[:20_000].lower()
        return b"whatwg" in head or b"living standard" in head

    def load(self, path: Path, raw: bytes) -> AdaptedDocument:
        if not raw.strip():
            raise AdapterParseError(
                f"Empty WHATWG document: {path}",
                adapter_id=self.adapter_id,
            )
        try:
            html.fromstring(raw)
            working = strip_chrome(raw, DocumentFamily.WHATWG)
            version = version_from_html_bytes(raw)
        except Exception as exc:  # noqa: BLE001
            raise AdapterParseError(
                f"Failed to parse WHATWG HTML: {path}: {exc}",
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
