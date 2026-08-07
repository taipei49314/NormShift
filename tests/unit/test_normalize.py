"""Unit tests for HTML normalization."""

from __future__ import annotations

from normshift.normalize.html_normalize import normalize_html


def test_strips_code_and_example() -> None:
    raw = b"""<!DOCTYPE html><html><body>
    <div class="example"><p>Example: client MUST heartbeat.</p></div>
    <pre><code>x MUST y</code></pre>
    <p>Implementers MUST validate input.</p>
    </body></html>"""
    blocks = normalize_html(raw)
    informative = [b for b in blocks if b.is_informative]
    normative = [b for b in blocks if not b.is_informative]
    assert any("validate input" in b.text for b in normative)
    assert all("heartbeat" not in b.text or b.is_informative for b in blocks)
    assert len(informative) >= 1


def test_section_path_from_headings() -> None:
    raw = b"""<!DOCTYPE html><html><body>
    <h2>Routing</h2>
    <p>Implementers MUST reject unknown critical extensions.</p>
    </body></html>"""
    blocks = normalize_html(raw)
    assert blocks
    assert "Routing" in blocks[0].section_path
