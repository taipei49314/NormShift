"""RFC Editor plain <pre> HTML extraction."""

from __future__ import annotations

from pathlib import Path

from normshift.extract.extractor import extract_from_source
from normshift.model.types import AdapterName, ProfileName
from normshift.normalize.html_normalize import normalize_html
from normshift.source import load_immutable_source


def test_pre_only_rfc_html_yields_blocks() -> None:
    raw = b"""<!DOCTYPE html><html><body><pre>
Request for Comments: 9999

The client MUST send a token.
The server SHOULD reject unknown schemes.

Appendix A. Examples
</pre></body></html>"""
    blocks = normalize_html(raw)
    assert len(blocks) >= 1
    joined = " ".join(b.text for b in blocks)
    assert "MUST send" in joined


def test_pre_rfc_extracts_requirements(tmp_path: Path) -> None:
    p = tmp_path / "rfc.html"
    p.write_bytes(
        b"""<!DOCTYPE html><html><body><pre>
RFC 9999

Implementations MUST validate UTF-8.
Receivers MUST NOT accept truncated sequences.
</pre></body></html>"""
    )
    src = load_immutable_source(p, adapter=AdapterName.RFC)
    doc = extract_from_source(src, ProfileName.RFC2119)
    assert len(doc.requirements) >= 2
    mods = {r.modality.value for r in doc.requirements}
    assert "MUST" in mods
