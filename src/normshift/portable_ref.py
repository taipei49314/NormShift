"""Platform-independent portable source_ref grammar (PurePosix)."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath


class PortableRefError(ValueError):
    """Raised when a source_ref is not a valid portable POSIX relative ref."""


_DRIVE = re.compile(r"^[A-Za-z]:")
_URI = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def validate_portable_ref(ref: str) -> str:
    """Validate and return a canonical portable POSIX relative source_ref.

    Rules (must all hold):
    - non-empty, not \".\" alone
    - relative (not absolute, not drive-like, not UNC)
    - POSIX separators only (no backslash)
    - not URI-like
    - no empty segment, no \".\" segment, no \"..\" segment
    - no repeated separators
    - exactly equal to its PurePosix normalized representation
    """
    if not isinstance(ref, str):
        raise PortableRefError(f"portable ref must be str, got {type(ref).__name__}")
    if ref == "" or ref == ".":
        raise PortableRefError(f"portable ref must be non-empty relative path, got {ref!r}")
    if "\\" in ref:
        raise PortableRefError(f"portable ref must use POSIX separators only: {ref!r}")
    if ref.startswith("/") or ref.startswith("//"):
        raise PortableRefError(f"portable ref must be relative (not absolute/UNC): {ref!r}")
    if _DRIVE.match(ref):
        raise PortableRefError(f"portable ref must not be drive-like: {ref!r}")
    if _URI.match(ref) or "://" in ref:
        raise PortableRefError(f"portable ref must not be URI-like: {ref!r}")
    if "//" in ref:
        raise PortableRefError(f"portable ref has repeated separator: {ref!r}")
    segs = ref.split("/")
    for s in segs:
        if s == "":
            raise PortableRefError(f"portable ref has empty segment: {ref!r}")
        if s == ".":
            raise PortableRefError(f"portable ref has '.' segment: {ref!r}")
        if s == "..":
            raise PortableRefError(f"portable ref has '..' segment: {ref!r}")
    # PurePosix normalization must leave the spelling unchanged
    try:
        norm = PurePosixPath(ref).as_posix()
    except Exception as exc:  # noqa: BLE001
        raise PortableRefError(f"portable ref not POSIX-normalizable: {ref!r}") from exc
    if norm != ref:
        raise PortableRefError(
            f"portable ref is not in canonical POSIX form: {ref!r} != {norm!r}"
        )
    return ref


def resolve_declared_under_root(root: Path, declared: str) -> tuple[Path, str]:
    """Resolve declared portable ref under root; require declared == canonical target.

    Rejects symlink alias spellings when the resolved relative path differs.
    """
    ref = validate_portable_ref(declared)
    root_r = Path(root).resolve()
    if not root_r.is_dir():
        raise PortableRefError(f"source-root is not a directory: {root_r}")
    cand = (root_r / ref).resolve()
    try:
        rel = cand.relative_to(root_r)
    except ValueError as exc:
        raise PortableRefError(f"path escapes source-root: {declared}") from exc
    canonical = rel.as_posix()
    # Host Path.as_posix() is fine for relative parts under root
    if canonical != ref:
        raise PortableRefError(
            f"declared ref is not the canonical root-relative path: "
            f"declared={ref!r} canonical={canonical!r}"
        )
    if not cand.is_file():
        raise PortableRefError(f"source not found under source-root: {declared}")
    # Symlink components must not escape (resolve already followed)
    return cand, ref
