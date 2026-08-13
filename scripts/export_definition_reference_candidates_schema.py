from pathlib import Path

from normshift.definition_reference_candidates.serialization import (
    definition_reference_candidates_json_schema,
)
from normshift.evidence.hashing import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw = canonical_json_bytes(definition_reference_candidates_json_schema())
    for path in (
        ROOT / "schemas" / "definition_reference_candidates_v1.schema.json",
        ROOT / "src" / "normshift" / "schemas" / "definition_reference_candidates_v1.schema.json",
    ):
        path.write_bytes(raw)


if __name__ == "__main__":
    main()
