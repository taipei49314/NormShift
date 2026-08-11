"""Export the exact semantic-dimensions schema to repository and wheel mirrors."""

from __future__ import annotations

from pathlib import Path

from normshift.evidence.hashing import canonical_json_bytes
from normshift.semantic_dimensions.authority import full_verification_receipt_json_schema
from normshift.semantic_dimensions.serialization import semantic_dimensions_json_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "full_verification_receipt_v1.schema.json": full_verification_receipt_json_schema,
    "semantic_change_dimensions_v1.schema.json": semantic_dimensions_json_schema,
}


def main() -> None:
    for schema_name, schema_factory in SCHEMAS.items():
        raw = canonical_json_bytes(schema_factory())
        for path in (
            ROOT / "schemas" / schema_name,
            ROOT / "src" / "normshift" / "schemas" / schema_name,
        ):
            path.write_bytes(raw)


if __name__ == "__main__":
    main()
