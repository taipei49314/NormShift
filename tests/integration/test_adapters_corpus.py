"""M1: three-family corpus replay + fail-closed adapter behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from normshift.adapters.errors import AdapterError, AdapterParseError
from normshift.adapters.registry import load_document
from normshift.extract.extractor import extract_requirements
from normshift.model.types import AdapterName, DocumentFamily, ProfileName
from normshift.pipeline import run_diff

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "fixtures" / "corpus"


def test_rfc_html_provenance_and_extraction() -> None:
    path = CORPUS / "rfc" / "sample-v1.html"
    adapted = load_document(path, adapter=AdapterName.RFC)
    assert adapted.family == DocumentFamily.RFC
    assert adapted.provenance.canonical_source is not None
    assert adapted.provenance.etag is not None
    assert adapted.provenance.content_sha256
    doc = extract_requirements(path, ProfileName.RFC2119, adapter=AdapterName.RFC)
    assert doc.provenance is not None
    assert doc.provenance.etag == adapted.provenance.etag
    texts = " ".join(r.normalized_text for r in doc.requirements)
    assert "establish a connection" in texts
    # note/code ignored
    assert "treat this note" not in texts
    assert "ignore code" not in texts


def test_rfc_xml_adapter() -> None:
    path = CORPUS / "rfc" / "sample.xml"
    adapted = load_document(path, adapter=AdapterName.RFC)
    assert adapted.family == DocumentFamily.RFC
    doc = extract_requirements(path, ProfileName.RFC2119, adapter=AdapterName.RFC)
    assert len(doc.requirements) >= 2
    assert any("frame type" in r.normalized_text for r in doc.requirements)


def test_w3c_family_strips_informative() -> None:
    path = CORPUS / "w3c" / "sample-v1.html"
    adapted = load_document(path, adapter=AdapterName.W3C)
    assert adapted.family == DocumentFamily.W3C
    doc = extract_requirements(path, ProfileName.RFC2119, adapter=AdapterName.W3C)
    texts = " ".join(r.normalized_text for r in doc.requirements)
    assert "open() method" in texts
    assert "Accept headers" not in texts
    assert "informative sections" not in texts


def test_whatwg_lowercase_profile() -> None:
    path = CORPUS / "whatwg" / "sample-v1.html"
    adapted = load_document(path, adapter=AdapterName.WHATWG)
    assert adapted.family == DocumentFamily.WHATWG
    doc = extract_requirements(path, ProfileName.WHATWG, adapter=AdapterName.WHATWG)
    assert len(doc.requirements) >= 3
    assert any(r.modality.value == "MUST" for r in doc.requirements)


def test_three_families_diff_replay(tmp_path: Path) -> None:
    cases = [
        (
            CORPUS / "rfc" / "sample-v1.html",
            CORPUS / "rfc" / "sample-v2.html",
            ProfileName.RFC2119,
            AdapterName.RFC,
            "STRENGTHENED",
        ),
        (
            CORPUS / "w3c" / "sample-v1.html",
            CORPUS / "w3c" / "sample-v2.html",
            ProfileName.RFC2119,
            AdapterName.W3C,
            "STRENGTHENED",
        ),
        (
            CORPUS / "whatwg" / "sample-v1.html",
            CORPUS / "whatwg" / "sample-v2.html",
            ProfileName.WHATWG,
            AdapterName.WHATWG,
            "STRENGTHENED",
        ),
    ]
    for old, new, profile, adapter, expected in cases:
        out = tmp_path / f"{adapter.value}.json"
        report = run_diff(old, new, profile=profile, adapter=adapter, json_out=out)
        assert out.is_file()
        assert report.old_document.provenance is not None
        assert report.new_document.provenance is not None
        classes = {c.classification.value for c in report.changes}
        assert expected in classes, f"{adapter}: {classes}"


def test_adapter_failure_no_artifact(tmp_path: Path) -> None:
    bad = tmp_path / "empty.html"
    bad.write_bytes(b"")
    out = tmp_path / "should-not-exist.json"
    with pytest.raises(AdapterError):
        run_diff(
            bad,
            CORPUS / "rfc" / "sample-v1.html",
            profile=ProfileName.RFC2119,
            adapter=AdapterName.HTML,
            json_out=out,
        )
    assert not out.exists()


def test_auto_detect_families() -> None:
    rfc = load_document(CORPUS / "rfc" / "sample-v1.html", adapter=AdapterName.AUTO)
    assert rfc.family == DocumentFamily.RFC
    w3c = load_document(CORPUS / "w3c" / "sample-v1.html", adapter=AdapterName.AUTO)
    assert w3c.family == DocumentFamily.W3C
    whatwg = load_document(CORPUS / "whatwg" / "sample-v1.html", adapter=AdapterName.AUTO)
    assert whatwg.family == DocumentFamily.WHATWG


def test_corrupt_xml_fails_closed() -> None:
    # Use a temp non-RFC xml without going through auto path issues
    from normshift.adapters.rfc_adapter import RfcAdapter

    with pytest.raises(AdapterParseError):
        RfcAdapter().load(Path("x.xml"), b"<not-rfc></not-rfc>")
