"""Universal path preflight and rollback-safe multi-artifact writes."""

from __future__ import annotations

import os
import stat
import tempfile
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path

ReplaceFn = Callable[[str | os.PathLike[str], str | os.PathLike[str]], None]


class PathSafetyError(ValueError):
    """Raised when input/output path safety rules are violated."""


class CleanupIncompleteError(RuntimeError):
    """Raised when outputs committed but backup cleanup failed."""

    def __init__(self, message: str, *, backup_paths: list[str]) -> None:
        super().__init__(message)
        self.backup_paths = backup_paths


def resolve_path(path: Path) -> Path:
    p = Path(path)
    if os.path.lexists(p):
        try:
            return p.resolve()
        except OSError:
            return p.absolute()
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
    ra, rb = resolve_path(a), resolve_path(b)
    try:
        if ra.exists() and rb.exists() and not ra.is_symlink() and not rb.is_symlink():
            return ra.samefile(rb)
    except OSError:
        pass
    return os.path.normcase(str(ra)) == os.path.normcase(str(rb))


def _is_ancestor(ancestor: Path, descendant: Path) -> bool:
    try:
        a = resolve_path(ancestor)
        d = resolve_path(descendant)
        d.relative_to(a)
        return a != d
    except (ValueError, OSError):
        return False


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _existing_entry_kind(path: Path) -> str | None:
    """Return entry kind if directory entry exists (including dangling symlink)."""
    if not _lexists(path):
        return None
    if path.is_symlink():
        return "symlink"
    try:
        mode = path.lstat().st_mode
    except OSError:
        return "unknown"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISFIFO(mode):
        return "fifo"
    if stat.S_ISSOCK(mode):
        return "socket"
    if stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        return "device"
    return "other"


def assert_outputs_safe(
    *,
    inputs: Sequence[Path],
    outputs: Sequence[Path | None],
    labels: Sequence[str] | None = None,
) -> list[Path]:
    """Non-mutating preflight. Rejects non-regular entries and ancestry."""
    concrete: list[Path] = []
    out_labels: list[str] = []
    for i, o in enumerate(outputs):
        if o is None:
            continue
        concrete.append(Path(o))
        out_labels.append(labels[i] if labels and i < len(labels) else f"output[{i}]")

    if not concrete:
        raise PathSafetyError("No output paths provided")

    input_paths = [Path(p) for p in inputs]

    # Existing destination type checks (lexists, not exists)
    for out, lab in zip(concrete, out_labels, strict=True):
        kind = _existing_entry_kind(out)
        if kind is None:
            continue
        if kind != "file":
            raise PathSafetyError(
                f"Output {lab} must be a regular non-symlink file when it exists "
                f"(found {kind}): {out}"
            )

    # Output/output equality and ancestry
    for i in range(len(concrete)):
        for j in range(i + 1, len(concrete)):
            a, b = concrete[i], concrete[j]
            if same_path(a, b):
                raise PathSafetyError(
                    f"Output path collision: {out_labels[i]} and {out_labels[j]}"
                )
            if _is_ancestor(a, b) or _is_ancestor(b, a):
                raise PathSafetyError(
                    f"Output ancestor relationship: {out_labels[i]} and {out_labels[j]}"
                )

    # Input/output equality and ancestry
    for inp in input_paths:
        for out, lab in zip(concrete, out_labels, strict=True):
            if same_path(inp, out):
                raise PathSafetyError(
                    f"Output {lab} collides with input {inp} (resolved {resolve_path(out)})"
                )
            if _is_ancestor(out, inp) or _is_ancestor(inp, out):
                raise PathSafetyError(
                    f"Output {lab} has ancestor/descendant relationship with input {inp}"
                )
    return concrete


def fsync_dir(path: Path) -> None:
    """Best-effort directory fsync (no-op if unsupported)."""
    import contextlib

    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        with contextlib.suppress(OSError):
            os.fsync(fd)
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    write_transaction({Path(path): data})


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))


def write_transaction(
    artifacts: Mapping[Path, bytes],
    *,
    replace_fn: ReplaceFn | None = None,
    fsync_directories: bool = True,
) -> None:
    """Rollback-safe multi-file commit for regular-file destinations only.

    Guarantee: rollback-safe multi-file commit, not globally atomic visibility.
    """
    if not artifacts:
        return
    # Defense in depth: re-validate destinations without mutating
    assert_outputs_safe(inputs=[], outputs=list(artifacts.keys()))

    replacer: ReplaceFn = replace_fn or os.replace
    temps: list[Path] = []
    backups: list[tuple[Path, Path]] = []
    newly_created: list[Path] = []
    staged: list[tuple[Path, Path, bool]] = []
    dirs_to_fsync: set[Path] = set()

    try:
        for final, data in artifacts.items():
            final = Path(final)
            # Do not create parents if final's parent would require creating under
            # a path we rejected — only mkdir when preflight already passed
            final.parent.mkdir(parents=True, exist_ok=True)
            kind = _existing_entry_kind(final)
            if kind is not None and kind != "file":
                raise PathSafetyError(
                    f"Refusing to replace non-regular output entry ({kind}): {final}"
                )
            existed = kind == "file"
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
            dirs_to_fsync.add(final.parent)

        for _tmp, final, existed in staged:
            if not existed:
                continue
            bak = final.parent / f".{final.name}.bak.{uuid.uuid4().hex}"
            replacer(final, bak)
            backups.append((bak, final))
            dirs_to_fsync.add(final.parent)

        for tmp_path, final, existed in staged:
            replacer(tmp_path, final)
            if tmp_path in temps:
                temps.remove(tmp_path)
            if not existed:
                newly_created.append(final)
            dirs_to_fsync.add(final.parent)

        if fsync_directories:
            for d in dirs_to_fsync:
                fsync_dir(d)

        cleanup_errors: list[str] = []
        retained: list[str] = []
        for bak, _final in backups:
            try:
                if bak.exists() or os.path.lexists(bak):
                    bak.unlink()
            except OSError as exc:
                cleanup_errors.append(f"{bak}: {exc}")
                retained.append(str(bak))
        backups.clear()
        if cleanup_errors:
            raise CleanupIncompleteError(
                "Outputs committed but backup cleanup incomplete: "
                + "; ".join(cleanup_errors),
                backup_paths=retained,
            )
    except CleanupIncompleteError:
        raise
    except Exception as primary:
        restore_errors: list[str] = []
        for bak, final in reversed(backups):
            try:
                if os.path.lexists(final) and not final.is_dir():
                    try:
                        final.unlink()
                    except OSError as exc:
                        restore_errors.append(f"unlink partial {final}: {exc}")
                if os.path.lexists(bak):
                    replacer(bak, final)
            except Exception as exc:  # noqa: BLE001
                restore_errors.append(f"restore {final} from {bak}: {exc}")
        for final in newly_created:
            try:
                if os.path.lexists(final) and final.is_file():
                    final.unlink()
            except OSError as exc:
                restore_errors.append(f"remove new final {final}: {exc}")
        for t in list(temps):
            try:
                if os.path.lexists(t):
                    t.unlink()
            except OSError as exc:
                restore_errors.append(f"cleanup temp {t}: {exc}")
        if fsync_directories:
            for d in dirs_to_fsync:
                fsync_dir(d)
        if restore_errors:
            raise RuntimeError(
                f"write_transaction failed: {primary}; rollback errors: {restore_errors}"
            ) from primary
        raise
    finally:
        for t in temps:
            try:
                if os.path.lexists(t):
                    t.unlink()
            except OSError:
                pass


def ensure_inputs_exist(paths: Iterable[Path]) -> None:
    for p in paths:
        if not Path(p).is_file():
            raise PathSafetyError(f"Input file not found: {p}")
