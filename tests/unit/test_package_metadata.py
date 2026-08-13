"""Package identity and reproducible build metadata tests."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from normshift import EXTRACTOR_VERSION, __version__

ROOT = Path(__file__).resolve().parents[2]


def test_package_versions_are_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = project["project"]["version"]

    assert package_version == __version__ == EXTRACTOR_VERSION


def test_build_backend_is_exactly_pinned() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = project["build-system"]["requires"]

    assert requirements == ["hatchling==1.31.0"]
    assert re.fullmatch(r"hatchling==\d+\.\d+\.\d+", requirements[0])


def test_packaged_audit_verifier_declares_requirement_parser_dependency() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "packaging>=24.0" in project["project"]["dependencies"]


def test_m1_source_manifest_schema_is_packaged() -> None:
    repository_schema = ROOT / "schemas" / "m1_source_manifest_v1.schema.json"
    packaged_schema = ROOT / "src" / "normshift" / "schemas" / repository_schema.name
    assert repository_schema.read_bytes() == packaged_schema.read_bytes()


def test_semantic_dimension_schemas_are_packaged() -> None:
    for name in (
        "full_verification_receipt_v1.schema.json",
        "lineage_graph_v1.schema.json",
        "semantic_change_dimensions_v1.schema.json",
    ):
        repository_schema = ROOT / "schemas" / name
        packaged_schema = ROOT / "src" / "normshift" / "schemas" / name
        assert repository_schema.read_bytes() == packaged_schema.read_bytes()
