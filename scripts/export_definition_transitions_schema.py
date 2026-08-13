"""Export exact DefinitionTransition v1 schemas to source and wheel mirrors."""

from __future__ import annotations

from pathlib import Path

from normshift.definition_transitions.serialization import definition_transitions_json_schema
from normshift.evidence.hashing import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw = canonical_json_bytes(definition_transitions_json_schema())
    for path in (
        ROOT / "schemas" / "definition_transitions_v1.schema.json",
        ROOT / "src" / "normshift" / "schemas" / "definition_transitions_v1.schema.json",
    ):
        path.write_bytes(raw)


if __name__ == "__main__":
    main()
