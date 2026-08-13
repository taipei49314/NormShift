"""Synthetic adversarial coverage for DefinitionTransition v1 replay sidecars."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from typer.testing import CliRunner

import normshift.cli as cli_module
import normshift.definition_transitions.verify as transitions_verify
from normshift.cli import app
from normshift.definition_transitions import (
    DefinitionTransitionError,
    DefinitionTransitionKind,
    build_definition_transitions,
    definition_transitions_json_bytes,
    definition_transitions_json_schema,
    parse_definition_transitions_bytes,
    verify_definition_transitions_file,
)
from normshift.evidence.hashing import canonical_json_bytes
from normshift.lineage import build_lineage_graph, lineage_graph_json_bytes
from normshift.model.types import AdapterName, ProfileName

ROOT = Path(__file__).resolve().parents[2]


def _source(version: str, definitions: list[tuple[str, str]]) -> bytes:
    definition_html = "".join(
        f'<p><dfn id="{term.replace(" ", "-")}">{term}</dfn> is defined as {body}.</p>'
        for term, body in definitions
    )
    return (
        f'<!doctype html><html><head><meta name="version" content="{version}"></head><body>'
        f"{definition_html}<p>Implementations MUST retain state.</p></body></html>"
    ).encode()


def _sources(tmp_path: Path) -> list[Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    values = [
        ("D1", [("Alpha Term", "the old meaning"), ("Gone Term", "a vanished meaning")]),
        ("D2", [("Alpha Term", "the new meaning"), ("Fresh Term", "a fresh meaning")]),
        ("D3", [("Alpha Term", "the new meaning"), ("Gone Term", "a restored meaning")]),
    ]
    paths = []
    for index, (version, definitions) in enumerate(values):
        path = tmp_path / f"v{index + 1}.html"
        path.write_bytes(_source(version, definitions))
        paths.append(path)
    return paths


def _graph(tmp_path: Path) -> tuple[list[Path], Path, str]:
    paths = _sources(tmp_path / "sources")
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    raw = lineage_graph_json_bytes(graph)
    path = tmp_path / "graph.json"
    path.write_bytes(raw)
    return paths, path, hashlib.sha256(raw).hexdigest()


def _sidecar(tmp_path: Path) -> tuple[list[Path], Path, str, Path, str]:
    paths, graph_path, graph_sha = _graph(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    document = build_definition_transitions(graph, graph_file_sha256=graph_sha)
    raw = definition_transitions_json_bytes(document)
    path = tmp_path / "transitions.json"
    path.write_bytes(raw)
    return paths, graph_path, graph_sha, path, hashlib.sha256(raw).hexdigest()


def test_build_emits_adjacent_add_change_remove_and_reintroduced_is_added(
    tmp_path: Path,
) -> None:
    paths, graph_path, graph_sha, sidecar_path, sidecar_sha = _sidecar(tmp_path)
    document = verify_definition_transitions_file(
        sidecar_path,
        transitions_sha256=sidecar_sha,
        graph_path=graph_path,
        graph_sha256=graph_sha,
        documents=paths,
        profile=ProfileName.RFC2119,
        adapter=AdapterName.HTML,
    )
    observed = {(item.lexical_normalized_term, item.kind) for item in document.transitions}
    assert observed == {
        ("alpha term", DefinitionTransitionKind.DEFINITION_CHANGED),
        ("gone term", DefinitionTransitionKind.DEFINITION_REMOVED),
        ("fresh term", DefinitionTransitionKind.DEFINITION_ADDED),
        ("fresh term", DefinitionTransitionKind.DEFINITION_REMOVED),
        ("gone term", DefinitionTransitionKind.DEFINITION_ADDED),
    }
    assert all(len(item.transition_id) == 64 for item in document.transitions)
    assert document.authority_kind == "LINEAGE_GRAPH_REPLAY_ONLY"
    assert document.external_acceptance is False


def test_same_version_lexical_normalization_collision_fails_closed(tmp_path: Path) -> None:
    paths, graph_path, graph_sha = _graph(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    duplicate = graph.definitions[0].model_copy(update={"term": "  ALPHA   TERM  "})
    graph = graph.model_copy(update={"definitions": [*graph.definitions, duplicate]})
    with pytest.raises(DefinitionTransitionError, match="lexical normalized term"):
        build_definition_transitions(graph, graph_file_sha256=graph_sha)


def test_unicode_lexical_identity_matches_definition_records_without_casefold(
    tmp_path: Path,
) -> None:
    paths, _graph_path, graph_sha = _graph(tmp_path)
    graph = build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML)
    old, new = graph.definitions[:2]
    first_version, second_version = graph.versions[:2]
    first_sha, second_sha = graph.document_sha256s[:2]
    old_sharp_s = old.model_copy(
        update={
            "definition_id": "old-sharp-s",
            "term": "ß",
            "body": "Straße",
            "normalized_body": "straße",
            "document_version": first_version,
            "document_sha256": first_sha,
        }
    )
    old_ss = old.model_copy(
        update={
            "definition_id": "old-ss",
            "term": "ss",
            "body": "same",
            "normalized_body": "same",
            "document_version": first_version,
            "document_sha256": first_sha,
        }
    )
    new_ss = new.model_copy(
        update={
            "definition_id": "new-ss",
            "term": "ss",
            "body": "same",
            "normalized_body": "same",
            "document_version": second_version,
            "document_sha256": second_sha,
        }
    )
    new_term = new.model_copy(
        update={
            "definition_id": "new-term",
            "term": "Term",
            "body": "Strasse",
            "normalized_body": "strasse",
            "document_version": second_version,
            "document_sha256": second_sha,
        }
    )
    old_term = old.model_copy(
        update={
            "definition_id": "old-term",
            "term": "Term",
            "body": "Straße",
            "normalized_body": "straße",
            "document_version": first_version,
            "document_sha256": first_sha,
        }
    )
    custom = graph.model_copy(
        update={
            "versions": [first_version, second_version],
            "document_sha256s": [first_sha, second_sha],
            "definitions": [old_sharp_s, old_ss, old_term, new_ss, new_term],
        }
    )
    document = build_definition_transitions(custom, graph_file_sha256=graph_sha)
    observed = {(item.lexical_normalized_term, item.kind) for item in document.transitions}
    assert observed == {
        ("ß", DefinitionTransitionKind.DEFINITION_REMOVED),
        ("term", DefinitionTransitionKind.DEFINITION_CHANGED),
    }
    assert all(
        item.lexical_normalized_term != "ss"
        or item.kind is not DefinitionTransitionKind.DEFINITION_ADDED
        for item in document.transitions
    )

    sharp_only = graph.model_copy(
        update={
            "versions": [first_version, second_version],
            "document_sha256s": [first_sha, second_sha],
            "definitions": [old_sharp_s, new_ss],
        }
    )
    sharp_document = build_definition_transitions(sharp_only, graph_file_sha256=graph_sha)
    assert {(item.lexical_normalized_term, item.kind) for item in sharp_document.transitions} == {
        ("ß", DefinitionTransitionKind.DEFINITION_REMOVED),
        ("ss", DefinitionTransitionKind.DEFINITION_ADDED),
    }


def test_schema_mirrors_package_and_requires_nested_anchors() -> None:
    raw = canonical_json_bytes(definition_transitions_json_schema())
    for path in (
        ROOT / "schemas" / "definition_transitions_v1.schema.json",
        ROOT / "src" / "normshift" / "schemas" / "definition_transitions_v1.schema.json",
    ):
        assert path.read_bytes() == raw
    packaged = files("normshift.schemas").joinpath("definition_transitions_v1.schema.json")
    assert packaged.read_bytes() == raw

    sample = json.loads(
        definition_transitions_json_bytes(
            build_definition_transitions(
                build_lineage_graph(
                    [
                        ROOT / "fixtures" / "lineage" / "v1.html",
                        ROOT / "fixtures" / "lineage" / "v2.html",
                    ],
                    profile=ProfileName.RFC2119,
                    adapter=AdapterName.HTML,
                ),
                graph_file_sha256="0" * 64,
            )
        )
    )
    sample["transitions"][0]["new_definition"].pop("normalized_body_sha256")
    assert list(Draft202012Validator(definition_transitions_json_schema()).iter_errors(sample))


@pytest.mark.parametrize(
    "transform",
    [
        lambda raw: raw + b" ",
        lambda raw: raw.replace(b"{", b'{"schema_version":"x",', 1),
        lambda raw: raw.replace(b'"content_sha256": "', b'"content_sha256": "0', 1),
    ],
)
def test_parser_rejects_noncanonical_duplicate_or_integrity_tamper(
    transform: object, tmp_path: Path
) -> None:
    _paths, _graph_path, _graph_sha, path, _sidecar_sha = _sidecar(tmp_path)
    with pytest.raises(DefinitionTransitionError):
        parse_definition_transitions_bytes(transform(path.read_bytes()))  # type: ignore[operator]


def test_transition_anchor_and_graph_replay_fail_before_source_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, graph_path, graph_sha, sidecar_path, sidecar_sha = _sidecar(tmp_path)
    parsed = json.loads(sidecar_path.read_bytes())
    parsed["graph_file_sha256"] = "0" * 64
    payload = {key: value for key, value in parsed.items() if key != "integrity"}
    parsed["integrity"]["content_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    sidecar_path.write_bytes(canonical_json_bytes(parsed))
    monkeypatch.setattr(
        transitions_verify,
        "verify_lineage_graph_file",
        lambda *_args, **_kwargs: pytest.fail("graph/source replay must not run"),
    )
    with pytest.raises(DefinitionTransitionError, match="graph file SHA"):
        verify_definition_transitions_file(
            sidecar_path,
            transitions_sha256=hashlib.sha256(sidecar_path.read_bytes()).hexdigest(),
            graph_path=graph_path,
            graph_sha256=graph_sha,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    assert sidecar_sha != hashlib.sha256(sidecar_path.read_bytes()).hexdigest()


def test_graph_integrity_anchor_fails_before_source_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, graph_path, graph_sha, sidecar_path, _sidecar_sha = _sidecar(tmp_path)
    parsed = json.loads(sidecar_path.read_bytes())
    parsed["graph_content_sha256"] = "0" * 64
    payload = {key: value for key, value in parsed.items() if key != "integrity"}
    parsed["integrity"]["content_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    sidecar_path.write_bytes(canonical_json_bytes(parsed))
    monkeypatch.setattr(
        transitions_verify,
        "verify_lineage_graph_file",
        lambda *_args, **_kwargs: pytest.fail("source replay must not run"),
    )
    with pytest.raises(DefinitionTransitionError, match="metadata differs"):
        verify_definition_transitions_file(
            sidecar_path,
            transitions_sha256=hashlib.sha256(sidecar_path.read_bytes()).hexdigest(),
            graph_path=graph_path,
            graph_sha256=graph_sha,
            documents=paths,
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )


def test_order_or_sidecar_tamper_fails_and_cli_never_emits_false_success(tmp_path: Path) -> None:
    paths, graph_path, graph_sha, sidecar_path, sidecar_sha = _sidecar(tmp_path)
    with pytest.raises(DefinitionTransitionError):
        verify_definition_transitions_file(
            sidecar_path,
            transitions_sha256=sidecar_sha,
            graph_path=graph_path,
            graph_sha256=graph_sha,
            documents=list(reversed(paths)),
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
        )
    result = CliRunner().invoke(
        app,
        [
            "definition-transitions",
            "verify",
            str(sidecar_path),
            str(graph_path),
            *(str(path) for path in reversed(paths)),
            "--transitions-sha256",
            sidecar_sha,
            "--graph-sha256",
            graph_sha,
            "--adapter",
            "html",
        ],
    )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "replay binding failed" in result.stderr


def test_cli_build_is_exact_canonical_binary_output(tmp_path: Path) -> None:
    paths, graph_path, graph_sha = _graph(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "definition-transitions",
            "build",
            str(graph_path),
            *(str(path) for path in paths),
            "--graph-sha256",
            graph_sha,
            "--adapter",
            "html",
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert result.stdout_bytes == definition_transitions_json_bytes(
        build_definition_transitions(
            build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML),
            graph_file_sha256=graph_sha,
        )
    )


def test_cli_build_failure_is_stderr_only_and_has_no_override_or_writer_surface(
    tmp_path: Path,
) -> None:
    paths, graph_path, _graph_sha = _graph(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "definition-transitions",
            "build",
            str(graph_path),
            *(str(path) for path in paths),
            "--graph-sha256",
            "0" * 64,
            "--adapter",
            "html",
        ],
    )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "replay binding failed" in result.stderr
    help_result = CliRunner().invoke(app, ["definition-transitions", "build", "--help"])
    assert help_result.exit_code == 0
    for forbidden in ("--source-root", "--old-source", "--new-source", "--content-only", "--json"):
        assert forbidden not in help_result.stdout


def test_cli_build_short_and_zero_progress_binary_writers_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, graph_path, graph_sha = _graph(tmp_path)
    args = [
        "definition-transitions",
        "build",
        str(graph_path),
        *(str(path) for path in paths),
        "--graph-sha256",
        graph_sha,
        "--adapter",
        "html",
    ]

    class ShortWritingStream:
        def __init__(self) -> None:
            self.captured = bytearray()
            self.flushed = False

        def write(self, value: memoryview) -> int:
            written = min(5, len(value))
            self.captured.extend(value[:written])
            return written

        def flush(self) -> None:
            self.flushed = True

    short_stream = ShortWritingStream()
    monkeypatch.setattr(cli_module.typer, "get_binary_stream", lambda _: short_stream)
    short_result = CliRunner().invoke(app, args)
    assert short_result.exit_code == 0, short_result.stderr
    assert short_stream.flushed
    assert bytes(short_stream.captured) == definition_transitions_json_bytes(
        build_definition_transitions(
            build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML),
            graph_file_sha256=graph_sha,
        )
    )

    class ZeroProgressAfterPrefixStream:
        def __init__(self) -> None:
            self.captured = bytearray()
            self.calls = 0

        def write(self, value: memoryview) -> int:
            self.calls += 1
            if self.calls == 1:
                self.captured.extend(value[:1])
                return 1
            return 0

        def flush(self) -> None:
            raise AssertionError("failed binary output must not be flushed")

    zero_stream = ZeroProgressAfterPrefixStream()
    monkeypatch.setattr(cli_module.typer, "get_binary_stream", lambda _: zero_stream)
    zero_result = CliRunner().invoke(app, args)
    assert zero_result.exit_code == 1
    assert bytes(zero_stream.captured) == definition_transitions_json_bytes(
        build_definition_transitions(
            build_lineage_graph(paths, profile=ProfileName.RFC2119, adapter=AdapterName.HTML),
            graph_file_sha256=graph_sha,
        )
    )[:1]
    assert "DEFINITION_TRANSITIONS_REPLAY_ONLY" not in zero_result.stdout
    assert "binary stdout made invalid write progress" in zero_result.stderr
