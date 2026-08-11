"""Export identical strict governance schemas to source and repository mirrors."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from normshift.evidence.hashing import canonical_json_bytes
from normshift.governance.models import (
    BlindSplitManifest,
    DecisionLedger,
    LabelingPacket,
    LabelSubmission,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_COMMENT = (
    "Structural JSON Schema validation alone does not verify canonical bytes, artifact hashes, "
    "reviewer independence, exact-root custody, blind-split invariants, or grant M1/M2 acceptance; "
    "use `normshift governance verify-*` with independent trust anchors."
)
MODELS: dict[str, type[BaseModel]] = {
    "blind_split_manifest_v1.schema.json": BlindSplitManifest,
    "decision_ledger_v1.schema.json": DecisionLedger,
    "label_submission_v1.schema.json": LabelSubmission,
    "labeling_packet_v1.schema.json": LabelingPacket,
}


def main() -> None:
    for filename, model in MODELS.items():
        schema = model.model_json_schema(mode="validation")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://normshift.example/schemas/{filename}"
        schema["$comment"] = SCHEMA_COMMENT
        raw = canonical_json_bytes(schema)
        for parent in (ROOT / "schemas", ROOT / "src" / "normshift" / "schemas"):
            destination = parent / filename
            destination.write_bytes(raw)


if __name__ == "__main__":
    main()
