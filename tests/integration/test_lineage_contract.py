"""Adversarial coverage for the experimental external LineageGraph v1 contract."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import Callable
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from typer.testing import CliRunner

import normshift.lineage.verify as lineage_verify
import normshift.semantic_dimensions.authority as authority_module
from normshift.adapters.errors import AdapterError
from normshift.cli import app
from normshift.evidence.hashing import canonical_json_bytes
from normshift.lineage import (
    LineageContractError,
    build_lineage_graph,
    lineage_graph_json_bytes,
    lineage_graph_json_schema,
    parse_lineage_graph_bytes,
    verify_lineage_graph_file,
)
from normshift.lineage import builder as lineage_builder
from normshift.model.types import AdapterName, ProfileName

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "lineage"


def _documents(root: Path) -> list[Path]:
    root.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in ("v1.html", "v2.html"):
        destination = root / name
        shutil.copyfile(FIXTURES / name, destination)
        paths.append(destination)
    return paths


def _graph_bytes(paths: list[Path]) -> bytes:
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    return lineage_graph_json_bytes(graph)


def _write_graph(root: Path, paths: list[Path]) -> tuple[Path, str]:
    graph_path = root / "graph.json"
    raw = _graph_bytes(paths)
    graph_path.write_bytes(raw)
    return graph_path, hashlib.sha256(raw).hexdigest()


def test_lineage_schema_mirrors_are_byte_identical_and_strict() -> None:
    raw = canonical_json_bytes(lineage_graph_json_schema())
    for path in (
        ROOT / "schemas" / "lineage_graph_v1.schema.json",
        ROOT / "src" / "normshift" / "schemas" / "lineage_graph_v1.schema.json",
    ):
        assert path.read_bytes() == raw


def test_lineage_schema_is_available_through_package_resources() -> None:
    expected = (ROOT / "schemas" / "lineage_graph_v1.schema.json").read_bytes()
    packaged = files("normshift.schemas").joinpath("lineage_graph_v1.schema.json").read_bytes()
    assert packaged == expected


@pytest.mark.parametrize(
    "remove_nested_field",
    [
        lambda graph: graph["nodes"][0]["instances"][0].pop("actor"),
        lambda graph: graph["edges"][0].pop("reasons"),
        lambda graph: graph["edges"][0].pop("confidence"),
    ],
)
def test_lineage_schema_requires_nested_typed_fields(
    remove_nested_field: Callable[[dict[str, Any]], Any],
) -> None:
    graph = json.loads(
        _graph_bytes([FIXTURES / "v1.html", FIXTURES / "v2.html"])
    )
    remove_nested_field(graph)
    errors = list(Draft202012Validator(lineage_graph_json_schema()).iter_errors(graph))
    assert errors

    relation_counts = lineage_graph_json_schema()["properties"]["summary"]["properties"][
        "relation_counts"
    ]
    assert "required" not in relation_counts


def test_public_lineage_builder_rejects_one_path_before_loading(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        lineage_builder,
        "load_immutable_source",
        lambda *_args, **_kwargs: pytest.fail("one-path build must not read a source"),
    )
    with pytest.raises(ValueError, match="at least two"):
        build_lineage_graph(
            [FIXTURES / "v1.html"],
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


@pytest.mark.parametrize(
    "transform",
    [
        lambda raw: raw.replace(b"\n", b"", 1),
        lambda raw: raw.replace(b"{", b'{"schema_version":"1.0.0",', 1),
        lambda raw: raw + b" ",
        lambda raw: raw.replace(b'"confidence": 0.9', b'"confidence": -0.0', 1),
        lambda raw: raw.replace(b'"confidence": 0.9', b'"confidence": NaN', 1),
    ],
)
def test_lineage_parser_rejects_noncanonical_or_duplicate_json(transform: object) -> None:
    raw = _graph_bytes([FIXTURES / "v1.html", FIXTURES / "v2.html"])
    with pytest.raises(LineageContractError):
        parse_lineage_graph_bytes(transform(raw))  # type: ignore[operator]


def test_verify_lineage_replays_ordered_descriptor_stable_sources(tmp_path: Path) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    graph = verify_lineage_graph_file(
        graph_path,
        graph_sha256=digest,
        documents=paths,
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    assert graph.integrity["content_sha256"]

    with pytest.raises(LineageContractError, match="SHA differs from graph binding"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=list(reversed(paths)),
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    paths[1].write_bytes(paths[1].read_bytes() + b"\n<!-- mutation -->\n")
    with pytest.raises(LineageContractError, match="SHA differs from graph binding"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_graph_anchor_canonical_and_integrity_fail_before_any_source_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    raw = graph_path.read_bytes().replace(b'"content_sha256": "', b'"content_sha256": "0', 1)
    graph_path.write_bytes(raw)
    monkeypatch.setattr(
        lineage_verify,
        "build_lineage_graph_from_sources",
        lambda *_args, **_kwargs: pytest.fail("source replay must not run"),
    )
    with pytest.raises(LineageContractError):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=hashlib.sha256(raw).hexdigest(),
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    with pytest.raises(LineageContractError, match="external SHA"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_profile_and_ordered_hash_bindings_fail_before_adapter_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    original_read = lineage_verify.read_bounded_regular_file

    def graph_only_read(*args: object, **kwargs: object) -> object:
        if kwargs["label"] != "lineage graph":
            pytest.fail("source reader must not run")
        return original_read(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        lineage_verify,
        "read_bounded_regular_file",
        graph_only_read,
    )
    with pytest.raises(LineageContractError, match="profile differs"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.WHATWG,
            adapter=AdapterName.HTML,
        )

    monkeypatch.undo()
    monkeypatch.setattr(
        lineage_verify,
        "load_immutable_source",
        lambda *_args, **_kwargs: pytest.fail("adapter callback must not run"),
    )
    with pytest.raises(LineageContractError, match="SHA differs from graph binding"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=list(reversed(paths)),
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_graph_tool_version_fails_before_any_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, _digest = _write_graph(tmp_path, paths)
    parsed = __import__("json").loads(graph_path.read_text(encoding="utf-8"))
    parsed["tool_version"] = "0.0.0"
    payload = {key: value for key, value in parsed.items() if key != "integrity"}
    parsed["integrity"]["content_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    raw = canonical_json_bytes(parsed)
    graph_path.write_bytes(raw)
    original_read = lineage_verify.read_bounded_regular_file

    def graph_only_read(*args: object, **kwargs: object) -> object:
        if kwargs["label"] != "lineage graph":
            pytest.fail("source reader must not run")
        return original_read(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(lineage_verify, "read_bounded_regular_file", graph_only_read)
    with pytest.raises(LineageContractError, match="tool version differs"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=hashlib.sha256(raw).hexdigest(),
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_adapter_failure_is_wrapped_and_cli_has_no_stdout_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)

    def fail_adapter(*_args: object, **_kwargs: object) -> object:
        raise AdapterError("synthetic malformed source")

    monkeypatch.setattr(lineage_verify, "load_immutable_source", fail_adapter)
    with pytest.raises(LineageContractError, match="lineage source replay failed"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    result = CliRunner().invoke(
        app,
        [
            "verify-lineage",
            str(graph_path),
            *(str(item) for item in paths),
            "--graph-sha256",
            digest,
            "--adapter",
            "html",
        ],
    )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "lineage source replay failed" in result.stderr


def test_isolated_snapshot_loader_must_retain_exact_captured_raw_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    original_load = lineage_verify.load_immutable_source

    def tampered_load(*args: object, **kwargs: object) -> object:
        loaded = original_load(*args, **kwargs)  # type: ignore[arg-type]
        return replace(loaded, raw_bytes=b"tampered")

    monkeypatch.setattr(lineage_verify, "load_immutable_source", tampered_load)
    with pytest.raises(LineageContractError, match="snapshot differs"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_graph_tamper_reseal_and_orphan_cannot_pass_replay(tmp_path: Path) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, _digest = _write_graph(tmp_path, paths)
    parsed = __import__("json").loads(graph_path.read_text(encoding="utf-8"))
    parsed["nodes"].pop()
    payload = {key: value for key, value in parsed.items() if key != "integrity"}
    parsed["integrity"]["content_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    raw = canonical_json_bytes(parsed)
    graph_path.write_bytes(raw)
    with pytest.raises(LineageContractError, match="differs from fresh ordered"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=hashlib.sha256(raw).hexdigest(),
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_graph_and_source_aliases_are_rejected(tmp_path: Path) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    alias = tmp_path / "graph-alias.json"
    try:
        alias.symlink_to(graph_path)
    except OSError as exc:
        pytest.skip(f"file symlink unavailable: {exc}")
    with pytest.raises(LineageContractError, match="symlink or junction"):
        verify_lineage_graph_file(
            alias,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    with pytest.raises(LineageContractError, match="alias one physical"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=[paths[0], paths[0]],
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    hardlink = tmp_path / "v1-hardlink.html"
    os.link(paths[0], hardlink)
    with pytest.raises(LineageContractError, match="hard-link aliases"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=[hardlink, paths[1]],
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_source_sidecar_is_not_an_undeclared_replay_input(tmp_path: Path) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    paths[0].with_suffix(".html.meta.json").write_text(
        "not JSON; hostile metadata is not a replay input\n", encoding="utf-8"
    )
    assert verify_lineage_graph_file(
        graph_path,
        graph_sha256=digest,
        documents=paths,
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    ).integrity["content_sha256"]


def test_source_atomic_replacement_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    replacement = tmp_path / "replacement.html"
    replacement.write_bytes(paths[0].read_bytes() + b"\n<!-- replacement -->\n")
    original_read = authority_module.os.read
    attempted = False
    reads = 0

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal attempted, reads
        raw = original_read(descriptor, size)
        reads += 1
        # The graph has been read first; race the first ordered source descriptor.
        if reads == 2 and not attempted:
            attempted = True
            os.replace(replacement, paths[0])
        return raw

    monkeypatch.setattr(authority_module.os, "read", racing_read)
    with pytest.raises(LineageContractError):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    assert attempted


def test_original_source_post_recheck_rejects_same_bytes_inode_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _documents(tmp_path / "sources")
    graph_path, digest = _write_graph(tmp_path, paths)
    replacement = tmp_path / "same-bytes-replacement.html"
    replacement.write_bytes(paths[0].read_bytes())
    original_read = lineage_verify.read_bounded_regular_file
    labels: list[str] = []

    def replace_before_post_recheck(*args: object, **kwargs: object) -> object:
        label = str(kwargs["label"])
        labels.append(label)
        if label == "post-replay lineage source 1":
            os.replace(replacement, paths[0])
        return original_read(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(lineage_verify, "read_bounded_regular_file", replace_before_post_recheck)
    with pytest.raises(LineageContractError, match="changed after isolated replay"):
        verify_lineage_graph_file(
            graph_path,
            graph_sha256=digest,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    assert "post-replay lineage source 1" in labels


@pytest.mark.parametrize("progress", [0, -1, 999])
def test_isolated_snapshot_writer_rejects_invalid_write_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, progress: int
) -> None:
    target = tmp_path / "snapshot.html"
    monkeypatch.setattr(lineage_verify.os, "write", lambda *_args: progress)
    with pytest.raises(LineageContractError, match="invalid write progress"):
        lineage_verify._write_snapshot_bytes(target, b"source bytes")


def test_relocation_two_runs_and_cli_fail_closed(tmp_path: Path) -> None:
    first = _documents(tmp_path / "one")
    second = _documents(tmp_path / "two")
    raw = _graph_bytes(first)
    assert raw == _graph_bytes(second)
    graph_path = tmp_path / "graph.json"
    graph_path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    runner = CliRunner()
    failed = runner.invoke(
        app,
        [
            "verify-lineage",
            str(graph_path),
            *(str(item) for item in second),
            "--graph-sha256",
            "0" * 64,
            "--adapter",
            "html",
        ],
    )
    assert failed.exit_code == 1
    assert failed.stdout == ""
    assert "external SHA-256" in failed.stderr
    assert "OK experimental" not in failed.stdout
    passed = runner.invoke(
        app,
        [
            "verify-lineage",
            str(graph_path),
            *(str(item) for item in second),
            "--graph-sha256",
            digest,
            "--adapter",
            "html",
        ],
    )
    assert passed.exit_code == 0, passed.output
    assert "LINEAGE_GRAPH_REPLAY_ONLY external_acceptance=false" in passed.stdout
    help_result = runner.invoke(app, ["verify-lineage", "--help"])
    assert help_result.exit_code == 0
    for forbidden in ("--json", "--source-root", "--content-only", "--role", "--object-span"):
        assert forbidden not in help_result.stdout
