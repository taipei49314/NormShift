"""Single immutable source read for one pipeline run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from normshift.adapters.base import AdaptedDocument
from normshift.adapters.registry import load_document
from normshift.model.types import AdapterName, DocumentFamily, DocumentSnapshot, Provenance


@dataclass(frozen=True)
class ImmutableSource:
    """One filesystem read; all downstream stages must reuse these bytes."""

    path: Path
    resolved_path: Path
    display_path: str
    raw_bytes: bytes
    working_html: bytes
    sha256: str
    byte_length: int
    document_version: str
    provenance: Provenance
    family: DocumentFamily
    adapter_name: AdapterName

    def to_snapshot(self) -> DocumentSnapshot:
        return DocumentSnapshot(
            path=self.display_path,
            sha256=self.sha256,
            version=self.document_version,
            byte_length=self.byte_length,
            provenance=self.provenance,
            document_family=self.family,
        )


def load_immutable_source(
    path: Path,
    adapter: AdapterName = AdapterName.AUTO,
) -> ImmutableSource:
    """Read and adapt a source exactly once."""
    path = Path(path)
    if not path.is_file():
        from normshift.adapters.errors import AdapterError

        raise AdapterError(f"Source file not found: {path}")

    adapted: AdaptedDocument = load_document(path, adapter=adapter)
    resolved = path.resolve()
    return ImmutableSource(
        path=path,
        resolved_path=resolved,
        display_path=str(path.as_posix()),
        raw_bytes=adapted.raw_bytes,
        working_html=adapted.working_html,
        sha256=adapted.provenance.content_sha256,
        byte_length=adapted.provenance.byte_length,
        document_version=adapted.document_version,
        provenance=adapted.provenance,
        family=adapted.family,
        adapter_name=adapter,
    )
