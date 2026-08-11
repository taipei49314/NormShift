#!/usr/bin/env python3
"""Regenerate the frozen acceptance JSON Schema mirrors."""

from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from normshift.acceptance.models import (  # noqa: E402
    AcceptanceResult,
    GoldDocument,
    PredictionDocument,
)
from normshift.evidence.hashing import canonical_json_bytes  # noqa: E402
from normshift.io_safety import write_transaction  # noqa: E402


def main() -> None:
    documents = {
        "acceptance_gold_v1.schema.json": GoldDocument.model_json_schema(mode="validation"),
        "acceptance_predictions_v1.schema.json": PredictionDocument.model_json_schema(
            mode="validation"
        ),
        "acceptance_result_v1.schema.json": AcceptanceResult.model_json_schema(mode="validation"),
    }
    artifacts: dict[Path, bytes] = {}
    for name, document in documents.items():
        document["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        document["$comment"] = (
            "Structural interchange schema only. Arithmetic, canonical item-key, graph, "
            "timestamp, aggregate, and frozen-policy invariants require validation and "
            "recomputation by the exact hash-bound NormShift scorer/models; JSON Schema "
            "validation alone never grants acceptance."
        )
        raw = canonical_json_bytes(document)
        artifacts[ROOT / "schemas" / name] = raw
        artifacts[ROOT / "src" / "normshift" / "schemas" / name] = raw
    write_transaction(artifacts)


if __name__ == "__main__":
    main()
