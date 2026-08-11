"""RFC adapter identity regressions."""

from pathlib import Path

from normshift.adapters.rfc_adapter import RfcAdapter


def test_rfc_editor_preformatted_html_fragment_is_recognized() -> None:
    raw = b"""<pre>
Network Working Group                                      Example Author
Request for Comments: 2246
Category: Standards Track

                    <span class="h1">Example RFC</span>
</pre>
"""

    assert RfcAdapter().can_handle(Path("rfc2246.html"), raw)
