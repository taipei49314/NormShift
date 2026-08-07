"""Universal path preflight and atomic multi-artifact writes."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path


class PathSafetyError(ValueError):
    """Raised when input/output path safety rules are violated."""


def resolve_path(path: Path) -> Path:
    """Resolve path without requiring existence of the final component."""
    p = Path(path)
    if p.exists():
        return p.resolve()
    parent = p.parent if p.parent.as_posix() not in {"", "."} else Path.cwd()
    # Walk up until an existing parent is found
    cur = parent
    missing: list[str] = [p.name]
    while not cur.exists() and cur != cur.parent:
        missing.append(cur.name)
        cur = cur.parent
    base = cur.resolve() if cur.exists() else Path.cwd().resolve()
    for part in reversed(missing):
        base = base / part
    return base


def same_path(a: Path, b: Path) -> bool:
    """True if two paths refer to the same filesystem identity."""
    ra, rb = resolve_path(a), resolve_path(b)
    try:
        if ra.exists() and rb.exists():
            return ra.samefile(rb)
    except OSError:
        pass
    # Compare normalized absolute paths (case-normalize on Windows)
    na = os.path.normcase(str(ra))
    nb = os.path.normcase(str(rb))
    return na == nb


def assert_outputs_safe(
    *,
    inputs: Sequence[Path],
    outputs: Sequence[Path | None],
    labels: Sequence[str] | None = None,
) -> list[Path]:
    """Reject input/output and output/output collisions. Return concrete outputs."""
    concrete: list[Path] = []
    out_labels: list[str] = []
    for i, o in enumerate(outputs):
        if o is None:
            continue
        concrete.append(Path(o))
        out_labels.append(labels[i] if labels and i < len(labels) else f"output[{i}]")

    if not concrete:
        raise PathSafetyError("No output paths provided")

    # Output/output collisions
    for i in range(len(concrete)):
        for j in range(i + 1, len(concrete)):
            if same_path(concrete[i], concrete[j]):
                raise PathSafetyError(
                    f"Output path collision: {out_labels[i]} and {out_labels[j]} "
                    f"resolve to the same path ({resolve_path(concrete[i])})"
                )

    # Input/output collisions
    for inp in inputs:
        for out, lab in zip(concrete, out_labels, strict=True):
            if same_path(Path(inp), out):
                raise PathSafetyError(
                    f"Output {lab} collides with input {Path(inp)} "
                    f"(resolved {resolve_path(out)})"
                )
    return concrete


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write bytes via same-directory temp file then atomic replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))


def write_transaction(artifacts: Mapping[Path, bytes]) -> None:
    """Write multiple artifacts atomically; leave finals untouched until all ready.

    On failure after some temps exist, only temps are cleaned — never finals.
    """
    if not artifacts:
        return
    temps: list[Path] = []
    try:
        staged: list[tuple[Path, Path]] = []  # (tmp, final)
        for final, data in artifacts.items():
            final = Path(final)
            final.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{final.name}.",
                suffix=".tmp",
                dir=str(final.parent),
            )
            tmp_path = Path(tmp_name)
            temps.append(tmp_path)
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            staged.append((tmp_path, final))
        # All temps ready — replace
        for tmp_path, final in staged:
            os.replace(tmp_path, final)
            if tmp_path in temps:
                temps.remove(tmp_path)
    finally:
        for t in temps:
            try:
                if t.exists():
                    t.unlink()
            except OSError:
                pass


def ensure_inputs_exist(paths: Iterable[Path]) -> None:
    for p in paths:
        if not Path(p).is_file():
            raise PathSafetyError(f"Input file not found: {p}")
