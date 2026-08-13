from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

import normshift.cli as cli_module
import normshift.definition_reference_candidates.builder as candidate_builder
import normshift.definition_reference_candidates.verify as candidate_verify
from normshift.cli import app
from normshift.definition_reference_candidates import (
    DefinitionReferenceCandidateError,
    build_definition_reference_candidates,
    definition_reference_candidates_json_bytes,
    verify_definition_reference_candidates_file,
)
from normshift.evidence.hashing import canonical_json_bytes
from normshift.lineage import build_lineage_graph, lineage_graph_json_bytes
from normshift.model.types import AdapterName, ProfileName

ROOT = Path(__file__).resolve().parents[2]


def _inputs(tmp_path: Path) -> tuple[list[Path], Path, str]:
    source = ROOT / "fixtures" / "lineage"
    paths = []
    for name in ("v1.html", "v2.html"):
        path = tmp_path / name
        shutil.copyfile(source / name, path)
        paths.append(path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    raw = lineage_graph_json_bytes(graph)
    graph_path = tmp_path / "graph.json"
    graph_path.write_bytes(raw)
    return paths, graph_path, hashlib.sha256(raw).hexdigest()


def test_candidate_replay_is_canonical_and_binds_exact_target(tmp_path: Path) -> None:
    paths, graph_path, graph_sha = _inputs(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    raw = definition_reference_candidates_json_bytes(
        build_definition_reference_candidates(graph, graph_file_sha256=graph_sha)
    )
    candidate_path = tmp_path / "candidates.json"
    candidate_path.write_bytes(raw)
    document = verify_definition_reference_candidates_file(
        candidate_path,
        candidates_sha256=hashlib.sha256(raw).hexdigest(),
        graph_path=graph_path,
        graph_sha256=graph_sha,
        documents=paths,
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    assert document.candidates
    assert all(item.method == "LEXICAL_TERM_OCCURRENCE_CANDIDATE" for item in document.candidates)
    assert document.authority_kind == "LINEAGE_GRAPH_REPLAY_ONLY"


def test_orphan_target_ambiguous_term_and_tamper_fail_closed(tmp_path: Path) -> None:
    paths, _graph_path, graph_sha = _inputs(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    orphan = graph.dependency_links[0].model_copy(update={"definition_id": "missing"})
    with pytest.raises(DefinitionReferenceCandidateError, match="orphan"):
        build_definition_reference_candidates(
            graph.model_copy(update={"dependency_links": [orphan]}), graph_file_sha256=graph_sha
        )
    duplicate = graph.definitions[0].model_copy(
        update={"definition_id": "other", "term": "  SESSION   TOKEN"}
    )
    with pytest.raises(DefinitionReferenceCandidateError, match="ambiguous"):
        build_definition_reference_candidates(
            graph.model_copy(update={"definitions": [*graph.definitions, duplicate]}),
            graph_file_sha256=graph_sha,
        )


def test_tampered_candidate_fails_before_graph_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, graph_path, graph_sha = _inputs(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    raw = definition_reference_candidates_json_bytes(
        build_definition_reference_candidates(graph, graph_file_sha256=graph_sha)
    )
    candidate_path = tmp_path / "candidates.json"
    candidate_path.write_bytes(raw + b" ")
    monkeypatch.setattr(
        candidate_verify,
        "verify_lineage_graph_file",
        lambda *_a, **_k: pytest.fail("replay must not run"),
    )
    with pytest.raises(DefinitionReferenceCandidateError):
        verify_definition_reference_candidates_file(
            candidate_path,
            candidates_sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            graph_path=graph_path,
            graph_sha256=graph_sha,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_cli_binary_build_order_and_failure_boundary(tmp_path: Path) -> None:
    paths, graph_path, graph_sha = _inputs(tmp_path)
    args = [
        "definition-reference-candidates",
        "build",
        str(graph_path),
        *(str(p) for p in paths),
        "--graph-sha256",
        graph_sha,
        "--adapter",
        "html",
    ]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout_bytes)["authority_kind"] == "LINEAGE_GRAPH_REPLAY_ONLY"
    failed = CliRunner().invoke(app, [*args[:-3], "--graph-sha256", "0" * 64, "--adapter", "html"])
    assert failed.exit_code == 1
    assert failed.stdout == ""
    assert (
        "CROSS_REFERENCE"
        not in CliRunner().invoke(app, ["definition-reference-candidates", "--help"]).stdout
    )


def test_cli_binary_short_write_retries_and_zero_progress_is_stderr_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, graph_path, graph_sha = _inputs(tmp_path)
    args = [
        "definition-reference-candidates",
        "build",
        str(graph_path),
        *(str(path) for path in paths),
        "--graph-sha256",
        graph_sha,
        "--adapter",
        "html",
    ]

    class ShortStream:
        def __init__(self) -> None:
            self.raw = bytearray()

        def write(self, value: memoryview) -> int:
            count = min(3, len(value))
            self.raw.extend(value[:count])
            return count

        def flush(self) -> None:
            pass

    short_stream = ShortStream()
    monkeypatch.setattr(cli_module.typer, "get_binary_stream", lambda _name: short_stream)
    short = CliRunner().invoke(app, args)
    assert short.exit_code == 0, short.stderr
    assert json.loads(bytes(short_stream.raw))["candidates"]

    class ZeroAfterPrefixStream(ShortStream):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def write(self, value: memoryview) -> int:
            self.calls += 1
            if self.calls == 1:
                self.raw.extend(value[:1])
                return 1
            return 0

        def flush(self) -> None:
            pytest.fail("zero-progress output must not flush")

    zero_stream = ZeroAfterPrefixStream()
    monkeypatch.setattr(cli_module.typer, "get_binary_stream", lambda _name: zero_stream)
    zero = CliRunner().invoke(app, args)
    assert zero.exit_code == 1
    assert bytes(zero_stream.raw)
    assert "DEFINITION_REFERENCE_CANDIDATES_REPLAY_ONLY" not in zero.stdout
    assert "binary stdout made invalid write progress" in zero.stderr


@pytest.mark.parametrize(
    "mutation, message",
    [
        (
            lambda graph: graph.model_copy(
                update={"dependency_links": [*graph.dependency_links] * 2}
            ),
            "duplicate",
        ),
        (
            lambda graph: graph.model_copy(
                update={
                    "dependency_links": [
                        graph.dependency_links[0].model_copy(update={"link_id": "second-link"}),
                        graph.dependency_links[0],
                    ]
                }
            ),
            "duplicate",
        ),
        (
            lambda graph: graph.model_copy(
                update={
                    "dependency_links": [
                        graph.dependency_links[0].model_copy(update={"term": "wrong term"})
                    ]
                }
            ),
            "differs",
        ),
    ],
)
def test_duplicate_and_mismatched_graph_link_evidence_fails_closed(
    tmp_path: Path, mutation: object, message: str
) -> None:
    paths, _graph_path, graph_sha = _inputs(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    with pytest.raises(DefinitionReferenceCandidateError, match=message):
        build_definition_reference_candidates(mutation(graph), graph_file_sha256=graph_sha)  # type: ignore[operator]


def test_candidate_count_cap_and_resealed_candidate_tamper_fail(tmp_path: Path) -> None:
    paths, graph_path, graph_sha = _inputs(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    original_cap = candidate_builder.MAX_CANDIDATES
    candidate_builder.MAX_CANDIDATES = 0
    try:
        with pytest.raises(DefinitionReferenceCandidateError, match="count exceeds"):
            build_definition_reference_candidates(graph, graph_file_sha256=graph_sha)
    finally:
        candidate_builder.MAX_CANDIDATES = original_cap

    raw = definition_reference_candidates_json_bytes(
        build_definition_reference_candidates(graph, graph_file_sha256=graph_sha)
    )
    parsed = json.loads(raw)
    parsed["candidates"][0]["candidate_id"] = "0" * 64
    payload = {key: value for key, value in parsed.items() if key != "integrity"}
    parsed["integrity"]["content_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    candidate_path = tmp_path / "resealed.json"
    candidate_path.write_bytes(canonical_json_bytes(parsed))
    with pytest.raises(DefinitionReferenceCandidateError, match="exact graph replay"):
        verify_definition_reference_candidates_file(
            candidate_path,
            candidates_sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            graph_path=graph_path,
            graph_sha256=graph_sha,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


@pytest.mark.parametrize(
    "field, value",
    [
        ("graph_tool_version", "0.0.0"),
        ("profile", "whatwg"),
        ("graph_content_sha256", "0" * 64),
    ],
)
def test_candidate_metadata_rejects_before_lineage_source_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: str
) -> None:
    paths, graph_path, graph_sha = _inputs(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    parsed = json.loads(
        definition_reference_candidates_json_bytes(
            build_definition_reference_candidates(graph, graph_file_sha256=graph_sha)
        )
    )
    parsed[field] = value
    payload = {key: item for key, item in parsed.items() if key != "integrity"}
    parsed["integrity"]["content_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    path = tmp_path / f"metadata-{field}.json"
    path.write_bytes(canonical_json_bytes(parsed))
    monkeypatch.setattr(
        candidate_verify,
        "verify_lineage_graph_file",
        lambda *_args, **_kwargs: pytest.fail("source replay must not run"),
    )
    with pytest.raises(DefinitionReferenceCandidateError):
        verify_definition_reference_candidates_file(
            path,
            candidates_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            graph_path=graph_path,
            graph_sha256=graph_sha,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
