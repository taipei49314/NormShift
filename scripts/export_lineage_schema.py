"""Export the exact LineageGraph v1 schema to repository and wheel mirrors."""

from __future__ import annotations

from pathlib import Path

from normshift.evidence.hashing import canonical_json_bytes
from normshift.lineage.serialization import lineage_graph_json_schema

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw = canonical_json_bytes(lineage_graph_json_schema())
    for path in (
        ROOT / "schemas" / "lineage_graph_v1.schema.json",
        ROOT / "src" / "normshift" / "schemas" / "lineage_graph_v1.schema.json",
    ):
        path.write_bytes(raw)


if __name__ == "__main__":
    main()
