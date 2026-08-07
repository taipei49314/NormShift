"""Generation/source-root path resolution for portable reports."""

from __future__ import annotations

from pathlib import Path

from normshift.portable_ref import PortableRefError, validate_portable_ref


class SourceRootError(ValueError):
    """Raised when a source cannot be represented under the declared root."""


def resolve_under_source_root(root: Path, path: Path) -> tuple[Path, str]:
    """Resolve path under root; return (absolute_file, portable_posix_ref).

    Rejects traversal and symlink escape. Portable ref is always canonical
    PurePosix root-relative form (no '.', '..', repeated separators, absolute).
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise SourceRootError(f"source-root is not a directory: {root}")

    p = Path(path)
    s = str(p)
    if re_abs(s) and not p.is_absolute():
        raise SourceRootError(f"Illegal absolute-like source path: {path}")

    if p.is_absolute():
        try:
            resolved = p.resolve()
            rel = resolved.relative_to(root)
        except ValueError as exc:
            raise SourceRootError(
                f"Source path outside source-root: {p} (root={root})"
            ) from exc
        p = resolved
    else:
        # Input may contain ".." segments; portable ref is always normalized.
        cand = (root / Path(p.as_posix())).resolve()
        try:
            rel = cand.relative_to(root)
        except ValueError as exc:
            raise SourceRootError(
                f"Source path escapes source-root: {path}"
            ) from exc
        p = cand

    if not p.is_file():
        raise SourceRootError(f"Source file not found under source-root: {path}")

    cur = root
    for part in Path(rel).parts:
        cur = cur / part
        if cur.is_symlink():
            try:
                cur.resolve().relative_to(root)
            except ValueError as exc:
                raise SourceRootError(f"Symlink escape: {cur}") from exc
    try:
        p.resolve().relative_to(root)
    except ValueError as exc:
        raise SourceRootError(f"Symlink escape under source-root: {path}") from exc

    portable = Path(rel).as_posix()
    try:
        portable = validate_portable_ref(portable)
    except PortableRefError as exc:
        raise SourceRootError(str(exc)) from exc
    return p.resolve(), portable


def re_abs(s: str) -> bool:
    return bool(s) and (s[0] == "/" or (len(s) > 2 and s[1] == ":" and s[0].isalpha()))


def default_source_root() -> Path:
    return Path.cwd().resolve()
