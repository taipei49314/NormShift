"""Adversarial exact-root tests for source-recipe evidence."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from normshift.corpus.evidence_inventory import (
    INVENTORY_REF,
    INVENTORY_SIDECAR_REF,
    EvidenceInventoryError,
    verify_evidence_root,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_seal(root: Path, files: dict[str, bytes]) -> str:
    root.mkdir()
    for ref, data in files.items():
        path = root / Path(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    inventory = "".join(
        f"{_sha256(data)}  {ref}\n"
        for ref, data in sorted(files.items(), key=lambda item: item[0].encode("ascii"))
    ).encode("ascii")
    digest = _sha256(inventory)
    (root / INVENTORY_REF).write_bytes(inventory)
    (root / INVENTORY_SIDECAR_REF).write_bytes(
        f"{digest}  {INVENTORY_REF}\n".encode("ascii")
    )
    return digest


def _write_manual_inventory(root: Path, inventory: bytes) -> str:
    digest = _sha256(inventory)
    (root / INVENTORY_REF).write_bytes(inventory)
    (root / INVENTORY_SIDECAR_REF).write_bytes(
        f"{digest}  {INVENTORY_REF}\n".encode("ascii")
    )
    return digest


def test_exact_root_inventory_accepts_only_declared_content(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    digest = _write_seal(
        root,
        {
            "README.md": b"development recipes only\n",
            "nested/source-manifest.json": b"{}\n",
        },
    )

    result = verify_evidence_root(root, expected_inventory_sha256=digest)

    assert result.inventory_sha256 == digest
    assert result.content_file_count == 2
    assert result.content_refs == ("README.md", "nested/source-manifest.json")


@pytest.mark.parametrize("extra_kind", ["file", "empty-directory"])
def test_exact_root_inventory_rejects_every_extra_entry(
    tmp_path: Path,
    extra_kind: str,
) -> None:
    root = tmp_path / "evidence"
    digest = _write_seal(root, {"README.md": b"recipe\n"})
    if extra_kind == "file":
        (root / "extra.txt").write_bytes(b"not declared\n")
    else:
        (root / "extra-directory").mkdir()

    with pytest.raises(EvidenceInventoryError, match="differs from inventory contract"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_rejects_tampered_content(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    digest = _write_seal(root, {"README.md": b"recipe\n"})
    (root / "README.md").write_bytes(b"tampered\n")

    with pytest.raises(EvidenceInventoryError, match="content SHA-256 mismatch"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_requires_independent_digest_anchor(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    _write_seal(root, {"README.md": b"recipe\n"})

    with pytest.raises(EvidenceInventoryError, match="independent trust anchor"):
        verify_evidence_root(root, expected_inventory_sha256="0" * 64)


def test_exact_root_inventory_rejects_rewritten_sidecar(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    digest = _write_seal(root, {"README.md": b"recipe\n"})
    (root / INVENTORY_SIDECAR_REF).write_bytes(
        f"{'0' * 64}  {INVENTORY_REF}\n".encode("ascii")
    )

    with pytest.raises(EvidenceInventoryError, match="digest sidecar"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_rejects_checksum_self_cycle(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "README.md").write_bytes(b"recipe\n")
    readme_digest = _sha256(b"recipe\n")
    inventory = (
        f"{readme_digest}  README.md\n"
        f"{'0' * 64}  {INVENTORY_REF}\n"
    ).encode("ascii")
    digest = _write_manual_inventory(root, inventory)

    with pytest.raises(EvidenceInventoryError, match="self-cycle"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_rejects_unsorted_records(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "a.txt").write_bytes(b"a")
    (root / "b.txt").write_bytes(b"b")
    inventory = (
        f"{_sha256(b'b')}  b.txt\n"
        f"{_sha256(b'a')}  a.txt\n"
    ).encode("ascii")
    digest = _write_manual_inventory(root, inventory)

    with pytest.raises(EvidenceInventoryError, match="must be sorted"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_rejects_portable_case_aliases(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "A.txt").write_bytes(b"same")
    inventory = (
        f"{_sha256(b'same')}  A.txt\n"
        f"{_sha256(b'same')}  a.txt\n"
    ).encode("ascii")
    digest = _write_manual_inventory(root, inventory)

    with pytest.raises(EvidenceInventoryError, match="alias collision"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_rejects_nonportable_entry_name(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    digest = _write_seal(root, {"README.md": b"recipe\n"})
    (root / "café.txt").write_bytes(b"extra")

    with pytest.raises(EvidenceInventoryError, match="portable ASCII"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_rejects_hard_link_alias(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    digest = _write_seal(root, {"README.md": b"recipe\n"})
    try:
        os.link(root / "README.md", root / "README-copy.md")
    except OSError as exc:
        pytest.skip(f"filesystem cannot create hard links: {exc}")

    with pytest.raises(EvidenceInventoryError, match="hard-linked evidence file"):
        verify_evidence_root(root, expected_inventory_sha256=digest)


def test_exact_root_inventory_rejects_symlink(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    digest = _write_seal(root, {"README.md": b"recipe\n"})
    try:
        (root / "README-link.md").symlink_to(root / "README.md")
    except OSError as exc:
        pytest.skip(f"filesystem cannot create symlinks: {exc}")

    with pytest.raises(EvidenceInventoryError, match="symlink or junction"):
        verify_evidence_root(root, expected_inventory_sha256=digest)
