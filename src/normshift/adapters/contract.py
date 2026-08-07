"""Versioned adapter contract diagnostics (expedition M1-B)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from normshift.adapters.base import AdaptedDocument
from normshift.adapters.errors import AdapterError
from normshift.adapters.registry import load_document
from normshift.extract.extractor import extract_from_source
from normshift.model.types import AdapterName, ProfileName
from normshift.source import load_immutable_source

ADAPTER_SEMVER = {
    AdapterName.HTML: ("generic-html", "1.0.0"),
    AdapterName.RFC: ("ietf-rfc-html", "1.0.0"),
    AdapterName.W3C: ("w3c-html", "1.0.0"),
    AdapterName.WHATWG: ("whatwg-html", "1.0.0"),
    AdapterName.AUTO: ("auto", "1.0.0"),
}


def diagnose_document(
    path: Path,
    *,
    adapter: AdapterName = AdapterName.AUTO,
    profile: ProfileName = ProfileName.RFC2119,
) -> dict[str, Any]:
    """Return adapter diagnostics without writing artifacts."""
    try:
        adapted: AdaptedDocument = load_document(path, adapter=adapter)
        src = load_immutable_source(path, adapter=adapter)
        doc = extract_from_source(src, profile)
    except AdapterError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "path": str(path),
            "adapter_requested": adapter.value,
        }

    name, ver = ADAPTER_SEMVER.get(adapter, (adapter.value, "0.0.0"))
    # Prefer family-specific name when auto
    if adapter == AdapterName.AUTO:
        fam = adapted.family.value
        name = {
            "rfc": "ietf-rfc-html",
            "w3c": "w3c-html",
            "whatwg": "whatwg-html",
            "html": "generic-html",
        }.get(fam, f"auto-{fam}")

    modalities: dict[str, int] = {}
    for r in doc.requirements:
        modalities[r.modality.value] = modalities.get(r.modality.value, 0) + 1

    return {
        "ok": True,
        "schema_version": "1.0.0",
        "path": str(path),
        "adapter": {
            "name": name,
            "semantic_version": ver,
            "requested": adapter.value,
            "document_family": adapted.family.value,
            "confidence": 0.85 if adapter != AdapterName.AUTO else 0.7,
        },
        "document": {
            "title": None,
            "declared_version": adapted.document_version,
            "publication_status": None,
            "content_type": adapted.provenance.content_type,
            "content_sha256": adapted.provenance.content_sha256,
            "byte_length": adapted.provenance.byte_length,
        },
        "extraction": {
            "profile": profile.value,
            "requirement_count": len(doc.requirements),
            "modality_counts": dict(sorted(modalities.items())),
            "sample_locators": [r.source_locator for r in doc.requirements[:10]],
        },
        "provenance": adapted.provenance.model_dump(mode="json"),
        "diagnostics": {
            "working_html_sha256": __import__("hashlib")
            .sha256(adapted.working_html)
            .hexdigest(),
            "raw_sha256": adapted.provenance.content_sha256,
            "label_authority": "AUTO",
            "experimental": True,
            "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        },
    }
