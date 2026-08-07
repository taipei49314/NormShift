"""Single immutable source read for one pipeline run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from normshift.adapters.base import AdaptedDocument, portable_source_ref
from normshift.adapters.registry import load_document
from normshift.model.types import AdapterName, DocumentFamily, DocumentSnapshot, Provenance


@dataclass(frozen=True)
class ImmutableSource:
    """One filesystem read; all downstream stages must reuse these bytes."""

    path: Path
    resolved_path: Path
    display_path: str  # portable source_ref
    raw_bytes: bytes
    working_html: bytes
    sha256: str
    byte_length: int
    document_version: str
    provenance: Provenance
    family: DocumentFamily
    adapter_name: AdapterName

    def to_snapshot(self) -> DocumentSnapshot:
        # Ensure provenance.local_path matches portable display path
        prov = self.provenance
        if prov.local_path != self.display_path:
            prov = prov.model_copy(update={"local_path": self.display_path})
        return DocumentSnapshot(
            path=self.display_path,
            sha256=self.sha256,
            version=self.document_version,
            byte_length=self.byte_length,
            provenance=prov,
            document_family=self.family,
            source_ref_mode="source_root_relative",
        )


def load_immutable_source(
    path: Path,
    adapter: AdapterName = AdapterName.AUTO,
    *,
    portable_ref: str | None = None,
) -> ImmutableSource:
    """Read and adapt a source exactly once.

    ``portable_ref`` is the external verification identity (POSIX relative).
    When omitted, it is derived from ``path`` without recording absolute workstation paths
    when a relative form is available.
    """
    path = Path(path)
    if not path.is_file():
        from normshift.adapters.errors import AdapterError

        raise AdapterError(f"Source file not found: {path}")

    adapted: AdaptedDocument = load_document(path, adapter=adapter)
    resolved = path.resolve()
    ref = portable_ref if portable_ref is not None else portable_source_ref(path)
    # Re-bind provenance.local_path to portable ref for external verify
    prov = adapted.provenance.model_copy(update={"local_path": ref})
    return ImmutableSource(
        path=path,
        resolved_path=resolved,
        display_path=ref,
        raw_bytes=adapted.raw_bytes,
        working_html=adapted.working_html,
        sha256=prov.content_sha256,
        byte_length=prov.byte_length,
        document_version=adapted.document_version,
        provenance=prov,
        family=adapted.family,
        adapter_name=adapter,
    )
