#!/usr/bin/env python3
"""Reproduce external package identity assertions for a NormShift M0 package.

Usage (from extracted Source.zip or clean clone of package tip)::

    python scripts/external_package_verify.py \\
        --repo . \\
        --manifest path/to/NormShift-M0-R5-MANIFEST.json \\
        --bundle path/to/NormShift-M0-R5.bundle \\
        --source-zip path/to/NormShift-M0-R5-Source.zip

Exit 0 only when commit/tree, artifact hashes, and archive-to-git checks match.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--source-zip", type=Path, required=True)
    args = ap.parse_args()

    errors: list[str] = []
    man = json.loads(args.manifest.read_text(encoding="utf-8"))
    commit = man["package_commit"]
    tree = man["package_tree"]

    head = subprocess.check_output(
        ["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True
    ).strip()
    tip_tree = subprocess.check_output(
        ["git", "-C", str(args.repo), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    if head != commit:
        errors.append(f"repo HEAD {head} != manifest commit {commit}")
    if tip_tree != tree:
        errors.append(f"repo tree {tip_tree} != manifest tree {tree}")

    b_hash = sha256_file(args.bundle)
    z_hash = sha256_file(args.source_zip)
    if b_hash != man["artifacts"]["bundle"]["sha256"]:
        errors.append("bundle sha256 mismatch")
    if z_hash != man["artifacts"]["source_zip"]["sha256"]:
        errors.append("source_zip sha256 mismatch")

    tracked = subprocess.check_output(
        ["git", "-C", str(args.repo), "ls-tree", "-r", "--name-only", commit],
        text=True,
    ).splitlines()
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(args.source_zip) as zf:
            zf.extractall(td)
        root = Path(td) / "NormShift"
        if not root.is_dir():
            # prefix may vary
            kids = list(Path(td).iterdir())
            root = kids[0] if kids else Path(td)
        arch_files = [
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file()
        ]
        tset, aset = set(tracked), set(arch_files)
        if tset != aset:
            errors.append(
                f"archive/git set mismatch missing={sorted(tset - aset)[:5]} "
                f"extra={sorted(aset - tset)[:5]}"
            )
        for rel in sorted(tset & aset):
            blob = subprocess.check_output(
                ["git", "-C", str(args.repo), "rev-parse", f"{commit}:{rel}"],
                text=True,
            ).strip()
            data = (root / rel).read_bytes()
            tmp = Path(td) / "_blob"
            tmp.write_bytes(data)
            got = subprocess.check_output(
                ["git", "hash-object", str(tmp)], text=True
            ).strip()
            if got != blob:
                errors.append(f"blob mismatch: {rel}")
                break

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("PASS external package verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
