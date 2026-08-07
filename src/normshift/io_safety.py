"""Universal path preflight and rollback-safe multi-artifact writes."""

from __future__ import annotations

import os
import tempfile
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path

ReplaceFn = Callable[[str | os.PathLike[str], str | os.PathLike[str]], None]


class PathSafetyError(ValueError):
    """Raised when input/output path safety rules are violated."""


def resolve_path(path: Path) -> Path:
    """Resolve path without requiring existence of the final component."""
    p = Path(path)
    if p.exists():
        return p.resolve()
    parent = p.parent if p.parent.as_posix() not in {"", "."} else Path.cwd()
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
    return os.path.normcase(str(ra)) == os.path.normcase(str(rb))


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

    for i in range(len(concrete)):
        for j in range(i + 1, len(concrete)):
            if same_path(concrete[i], concrete[j]):
                raise PathSafetyError(
                    f"Output path collision: {out_labels[i]} and {out_labels[j]} "
                    f"resolve to the same path ({resolve_path(concrete[i])})"
                )

    for inp in inputs:
        for out, lab in zip(concrete, out_labels, strict=True):
            if same_path(Path(inp), out):
                raise PathSafetyError(
                    f"Output {lab} collides with input {Path(inp)} "
                    f"(resolved {resolve_path(out)})"
                )
    return concrete


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write a single file via same-directory temp + replace."""
    write_transaction({Path(path): data})


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))


def write_transaction(
    artifacts: Mapping[Path, bytes],
    *,
    replace_fn: ReplaceFn | None = None,
) -> None:
    """Rollback-safe multi-file commit (not globally atomic visibility).

    1. Stage and fsync all temporary files.
    2. Move each existing final to a transaction-owned backup.
    3. Replace finals one by one.
    4. On any failure: restore all backups, remove only newly created finals.
    5. Delete backups only after full success.

    ``replace_fn`` defaults to ``os.replace`` and is injectable for tests.
    """
    if not artifacts:
        return
    replacer: ReplaceFn = replace_fn or os.replace

    temps: list[Path] = []
    backups: list[tuple[Path, Path]] = []  # (backup, final)
    newly_created: list[Path] = []
    staged: list[tuple[Path, Path, bool]] = []  # tmp, final, existed_before

    try:
        # Stage all temps first
        for final, data in artifacts.items():
            final = Path(final)
            final.parent.mkdir(parents=True, exist_ok=True)
            existed = final.exists()
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
            staged.append((tmp_path, final, existed))

        # Backup existing finals
        for _tmp, final, existed in staged:
            if not existed:
                continue
            bak = final.parent / f".{final.name}.bak.{uuid.uuid4().hex}"
            replacer(final, bak)
            backups.append((bak, final))

        # Commit replacements
        for tmp_path, final, existed in staged:
            replacer(tmp_path, final)
            if tmp_path in temps:
                temps.remove(tmp_path)
            if not existed:
                newly_created.append(final)

        # Success: remove backups
        for bak, _final in backups:
            try:
                if bak.exists():
                    bak.unlink()
            except OSError:
                pass
        backups.clear()
    except Exception as primary:
        # Restore backups (pre-existing finals)
        restore_errors: list[str] = []
        for bak, final in reversed(backups):
            try:
                if bak.exists():
                    # Remove partial new final if present
                    if final.exists():
                        try:
                            final.unlink()
                        except OSError as exc:
                            restore_errors.append(f"unlink partial {final}: {exc}")
                    replacer(bak, final)
            except Exception as exc:  # noqa: BLE001
                restore_errors.append(f"restore {final} from {bak}: {exc}")
        # Remove only newly created finals by this transaction
        for final in newly_created:
            try:
                if final.exists():
                    final.unlink()
            except OSError as exc:
                restore_errors.append(f"remove new final {final}: {exc}")
        # Clean remaining temps
        for t in list(temps):
            try:
                if t.exists():
                    t.unlink()
            except OSError as exc:
                restore_errors.append(f"cleanup temp {t}: {exc}")
        if restore_errors:
            raise RuntimeError(
                f"write_transaction failed: {primary}; rollback errors: {restore_errors}"
            ) from primary
        raise
    finally:
        # Leftover temps only (success path already emptied)
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
