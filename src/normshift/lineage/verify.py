"""External-anchor verification for experimental LineageGraph v1 sidecars."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from normshift import __version__
from normshift.adapters.base import provisional_portable_ref
from normshift.adapters.errors import AdapterError
from normshift.lineage.builder import build_lineage_graph_from_sources
from normshift.lineage.errors import LineageContractError
from normshift.lineage.serialization import (
    MAX_LINEAGE_GRAPH_BYTES,
    lineage_graph_json_bytes,
    lineage_graph_sha256,
    parse_lineage_graph_bytes,
)
from normshift.model.types import AdapterName, LineageGraph, ProfileName
from normshift.semantic_dimensions.authority import BoundedFileRead, read_bounded_regular_file
from normshift.semantic_dimensions.errors import SemanticDimensionsError
from normshift.source import load_immutable_source

MAX_LINEAGE_SOURCE_BYTES = 100_000_000
MAX_TOTAL_LINEAGE_SOURCE_BYTES = 200_000_000


def verify_lineage_graph_file(
    graph_path: Path,
    *,
    graph_sha256: str,
    documents: list[Path],
    profile: ProfileName,
    adapter: AdapterName,
) -> LineageGraph:
    """Verify an anchored graph before replaying descriptor-stable source snapshots."""
    _require_sha256(graph_sha256, "graph SHA-256")
    if len(documents) < 2:
        raise LineageContractError("lineage verification requires at least two ordered documents")

    # This entire block precedes any source document open or adapter callback.
    try:
        graph_raw = read_bounded_regular_file(
            graph_path, label="lineage graph", max_bytes=MAX_LINEAGE_GRAPH_BYTES
        ).raw
    except SemanticDimensionsError as exc:
        raise LineageContractError(str(exc)) from exc
    if lineage_graph_sha256(graph_raw) != graph_sha256:
        raise LineageContractError("lineage graph bytes differ from external SHA-256")
    graph = parse_lineage_graph_bytes(graph_raw)
    if graph.tool_version != __version__:
        raise LineageContractError("lineage graph tool version differs from this verifier")
    if graph.profile != profile:
        raise LineageContractError("lineage graph profile differs from explicit replay profile")
    if len(documents) != len(graph.document_sha256s) or len(documents) != len(graph.versions):
        raise LineageContractError("lineage graph ordered source count differs from replay inputs")

    snapshots: list[tuple[Path, BoundedFileRead]] = []
    identities: set[tuple[int, int, int, int, int, int, int]] = set()
    total_source_bytes = 0
    for index, path in enumerate(documents):
        try:
            file_read = read_bounded_regular_file(
                path,
                label=f"ordered lineage source {index + 1}",
                max_bytes=MAX_LINEAGE_SOURCE_BYTES,
            )
        except SemanticDimensionsError as exc:
            raise LineageContractError(str(exc)) from exc
        if file_read.final in identities:
            raise LineageContractError("ordered lineage sources must not alias one physical file")
        if file_read.content_sha256 != graph.document_sha256s[index]:
            raise LineageContractError(
                f"ordered lineage source {index + 1} SHA differs from graph binding"
            )
        identities.add(file_read.final)
        total_source_bytes += len(file_read.raw)
        if total_source_bytes > MAX_TOTAL_LINEAGE_SOURCE_BYTES:
            raise LineageContractError("ordered lineage sources exceed total size limit")
        snapshots.append((Path(path), file_read))

    try:
        with TemporaryDirectory(prefix="normshift-lineage-replay-") as temp:
            root = Path(temp)
            sources = []
            for index, (declared, captured) in enumerate(snapshots):
                suffix = declared.suffix or ".source"
                snapshot_path = root / f"source-{index:04d}{suffix}"
                _write_snapshot_bytes(snapshot_path, captured.raw)
                try:
                    snapshot_read = read_bounded_regular_file(
                        snapshot_path,
                        label=f"isolated lineage snapshot {index + 1}",
                        max_bytes=MAX_LINEAGE_SOURCE_BYTES,
                    )
                except SemanticDimensionsError as exc:
                    raise LineageContractError(str(exc)) from exc
                if (
                    snapshot_read.raw != captured.raw
                    or snapshot_read.content_sha256 != captured.content_sha256
                ):
                    raise LineageContractError(
                        "isolated lineage snapshot bytes differ from capture"
                    )
                loaded = load_immutable_source(
                    snapshot_path,
                    adapter=adapter,
                    portable_ref=provisional_portable_ref(declared),
                )
                if loaded.raw_bytes != captured.raw or loaded.sha256 != captured.content_sha256:
                    raise LineageContractError(
                        "isolated lineage snapshot differs from captured source bytes"
                    )
                sources.append(loaded)
            replayed = build_lineage_graph_from_sources(sources, profile=profile)
            replayed_raw = lineage_graph_json_bytes(replayed)
            if replayed_raw != graph_raw:
                raise LineageContractError("lineage graph differs from fresh ordered source replay")
            _assert_original_sources_unchanged(snapshots)
    except LineageContractError:
        raise
    except (AdapterError, ValueError) as exc:
        raise LineageContractError(f"lineage source replay failed: {exc}") from exc
    return graph


def _write_snapshot_bytes(path: Path, raw: bytes) -> None:
    """Write one replay-only snapshot completely and durably before any adapter reads it."""
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
        0o600,
    )
    try:
        view = memoryview(raw)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            remaining = len(view) - offset
            if type(written) is not int or written <= 0 or written > remaining:
                raise LineageContractError("isolated lineage snapshot made invalid write progress")
            offset += written
        os.fsync(descriptor)
    except OSError as exc:
        raise LineageContractError(f"cannot write isolated lineage snapshot: {exc}") from exc
    finally:
        os.close(descriptor)


def _assert_original_sources_unchanged(
    snapshots: list[tuple[Path, BoundedFileRead]],
) -> None:
    """Reject any original-path change after isolated replay, including inode swaps."""
    for index, (path, initial) in enumerate(snapshots):
        try:
            current = read_bounded_regular_file(
                path,
                label=f"post-replay lineage source {index + 1}",
                max_bytes=MAX_LINEAGE_SOURCE_BYTES,
            )
        except SemanticDimensionsError as exc:
            raise LineageContractError(str(exc)) from exc
        if (
            current.before != initial.final
            or current.after != initial.final
            or current.final != initial.final
            or current.raw != initial.raw
            or current.content_sha256 != initial.content_sha256
        ):
            raise LineageContractError(
                f"ordered lineage source {index + 1} changed after isolated replay"
            )


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise LineageContractError(f"{label} must be a lowercase SHA-256 digest")
