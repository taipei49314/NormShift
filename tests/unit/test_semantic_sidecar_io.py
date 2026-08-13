"""Regression tests for semantic-sidecar bounded input reads."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import normshift.semantic_dimensions.authority as authority_module
from normshift.semantic_dimensions import SemanticDimensionsError, read_bounded_regular_file


def test_sidecar_reader_rejects_symlink_and_hardlink_aliases(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_bytes(b"{}\n")
    hardlink = tmp_path / "hardlink.json"
    os.link(target, hardlink)
    with pytest.raises(SemanticDimensionsError, match="hard-link aliases"):
        read_bounded_regular_file(target, label="receipt", max_bytes=100_000)

    target.unlink()
    hardlink.unlink()
    target.write_bytes(b"{}\n")
    alias = tmp_path / "alias.json"
    try:
        alias.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"file symlink unavailable: {exc}")
    with pytest.raises(SemanticDimensionsError, match="symlink or junction"):
        read_bounded_regular_file(alias, label="sidecar", max_bytes=1_000_000)


def test_sidecar_reader_rejects_same_length_atomic_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "receipt.json"
    target.write_bytes(b"original\n")
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b"replaced\n")
    original_read = authority_module.os.read
    replaced = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        data = original_read(descriptor, size)
        if not replaced:
            replaced = True
            os.replace(replacement, target)
        return data

    monkeypatch.setattr(authority_module.os, "read", racing_read)
    with pytest.raises(SemanticDimensionsError) as captured:
        read_bounded_regular_file(target, label="receipt", max_bytes=100_000)
    assert replaced
    assert str(captured.value)
    if target.read_bytes() == b"replaced\n":
        assert not replacement.exists()
    else:
        # Windows denies replacing an open descriptor; the attempted race still
        # fails closed through the wrapped replace error.
        assert target.read_bytes() == b"original\n"
        assert replacement.read_bytes() == b"replaced\n"
