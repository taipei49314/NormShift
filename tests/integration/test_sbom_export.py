"""Frozen CycloneDX export and offline schema-validation gate."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path

from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator

ROOT = Path(__file__).resolve().parents[2]


def _normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def test_frozen_runtime_sbom_is_strict_cyclonedx_15(tmp_path: Path) -> None:
    sbom_path = tmp_path / "normshift-sbom.cdx.json"
    completed = subprocess.run(
        [
            "uv",
            "export",
            "--preview-features",
            "sbom-export",
            "--frozen",
            "--no-dev",
            "--no-editable",
            "--format",
            "cyclonedx1.5",
            "--output-file",
            str(sbom_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    raw = sbom_path.read_text(encoding="utf-8")
    validation_error = JsonStrictValidator(SchemaVersion.V1_5).validate_str(raw)
    assert validation_error is None, repr(validation_error)

    payload = json.loads(raw)
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    root_component = payload["metadata"]["component"]
    assert payload["bomFormat"] == "CycloneDX"
    assert payload["specVersion"] == "1.5"
    assert root_component["name"] == project["name"]
    assert root_component["version"] == project["version"]

    component_names = {_normalized_name(item["name"]) for item in payload["components"]}
    direct_names = {
        _normalized_name(re.split(r"[<>=!~;\[]", item, maxsplit=1)[0])
        for item in project["dependencies"]
    }
    assert direct_names <= component_names
    assert len(payload["components"]) >= len(direct_names)

    root_dependency = next(
        item for item in payload["dependencies"] if item["ref"] == root_component["bom-ref"]
    )
    assert len(root_dependency["dependsOn"]) == len(direct_names)
