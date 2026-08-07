"""Adapter diagnose contract tests."""

from __future__ import annotations

from pathlib import Path

from normshift.adapters.contract import diagnose_document
from normshift.model.types import AdapterName, ProfileName

ROOT = Path(__file__).resolve().parents[2]


def test_diagnose_three_families() -> None:
    cases = [
        (ROOT / "fixtures/corpus/rfc/sample-v1.html", AdapterName.RFC, ProfileName.RFC2119),
        (ROOT / "fixtures/corpus/w3c/sample-v1.html", AdapterName.W3C, ProfileName.RFC2119),
        (ROOT / "fixtures/corpus/whatwg/sample-v1.html", AdapterName.WHATWG, ProfileName.WHATWG),
    ]
    for path, adapter, profile in cases:
        diag = diagnose_document(path, adapter=adapter, profile=profile)
        assert diag["ok"] is True, diag
        assert diag["extraction"]["requirement_count"] >= 1
        assert diag["diagnostics"]["status"] == "EXPERIMENTAL_NOT_ADJUDICATED"
