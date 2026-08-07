"""Adapter selection and document loading (fail-closed)."""

from __future__ import annotations

from pathlib import Path

from normshift.adapters.base import AdaptedDocument
from normshift.adapters.detect import detect_family
from normshift.adapters.errors import AdapterError, AdapterParseError
from normshift.adapters.html_adapter import HtmlAdapter
from normshift.adapters.rfc_adapter import RfcAdapter
from normshift.adapters.w3c_adapter import W3cAdapter
from normshift.adapters.whatwg_adapter import WhatwgAdapter
from normshift.model.types import AdapterName, DocumentFamily

_ADAPTERS: dict[DocumentFamily, HtmlAdapter | RfcAdapter | W3cAdapter | WhatwgAdapter] = {
    DocumentFamily.GENERIC_HTML: HtmlAdapter(),
    DocumentFamily.RFC: RfcAdapter(),
    DocumentFamily.W3C: W3cAdapter(),
    DocumentFamily.WHATWG: WhatwgAdapter(),
}


def _family_for_adapter_name(name: AdapterName) -> DocumentFamily | None:
    if name == AdapterName.AUTO:
        return None
    if name == AdapterName.HTML:
        return DocumentFamily.GENERIC_HTML
    if name == AdapterName.RFC:
        return DocumentFamily.RFC
    if name == AdapterName.W3C:
        return DocumentFamily.W3C
    if name == AdapterName.WHATWG:
        return DocumentFamily.WHATWG
    raise AdapterError(f"Unknown adapter: {name}")


def load_document(path: Path, adapter: AdapterName = AdapterName.AUTO) -> AdaptedDocument:
    """Load a local document via the selected adapter. Never returns partial success."""
    if not path.is_file():
        raise AdapterError(f"Source file not found: {path}", adapter_id="normshift.adapters")

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise AdapterError(f"Failed to read source file: {path}: {exc}") from exc

    if not raw:
        raise AdapterParseError(f"Empty source file: {path}")

    forced = _family_for_adapter_name(adapter)
    family = detect_family(path, raw) if forced is None else forced

    impl = _ADAPTERS[family]
    # Always attempt load for the selected/detected family. `can_handle` is a
    # soft hint for tooling; load() is the fail-closed gate.
    try:
        return impl.load(path, raw)
    except AdapterError:
        # If auto-detection picked a specialized family but parse fails, fall
        # back to generic HTML when the bytes look like HTML.
        if forced is None and family != DocumentFamily.GENERIC_HTML:
            head = raw[:2000].lower()
            if b"<html" in head or b"<!doctype html" in head or path.suffix.lower() in {
                ".html",
                ".htm",
                ".xhtml",
            }:
                return _ADAPTERS[DocumentFamily.GENERIC_HTML].load(path, raw)
        raise
