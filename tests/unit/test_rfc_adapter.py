"""RFC adapter identity and paginated-HTML regressions."""

from pathlib import Path

from normshift.adapters.registry import load_document
from normshift.adapters.rfc_adapter import RfcAdapter
from normshift.extract.extractor import extract_requirements
from normshift.model.types import AdapterName, ProfileName
from normshift.normalize.html_normalize import normalize_html

PAGINATED_RFC = b"""<pre>Network Working Group                         Example Author
Request for Comments: 9999                    Example Org
Category: Standards Track                     January 2026

<span class="h1">Example Protocol</span>
<span class="h2">1 . Introduction</span>

   Clients MUST validate every message before processing it.

<span class="grey">Example Author  Standards Track  [Page 1]</span>
</pre><hr><pre><span class="grey">RFC 9999  Example Protocol  January 2026</span>

<span class="h3">1.1 . Retry behavior</span>

   Servers SHOULD retry a request after a transient failure.

<span class="grey">Example Author  Standards Track  [Page 2]</span>
</pre>"""


def test_rfc_editor_preformatted_html_fragment_is_recognized() -> None:
    raw = b"""<pre>
Network Working Group                                      Example Author
Request for Comments: 2246
Category: Standards Track

                    <span class="h1">Example RFC</span>
</pre>
"""

    assert RfcAdapter().can_handle(Path("rfc2246.html"), raw)


def test_paginated_rfc_editor_html_becomes_sections_and_requirements(tmp_path: Path) -> None:
    path = tmp_path / "neutral.html"
    path.write_bytes(PAGINATED_RFC)

    adapted = load_document(path, adapter=AdapterName.RFC)
    blocks = normalize_html(adapted.working_html)
    requirements = extract_requirements(
        path,
        ProfileName.RFC2119,
        adapter=AdapterName.RFC,
    ).requirements

    assert b"<pre" not in adapted.working_html
    assert b"[Page 1]" not in adapted.working_html
    assert {block.section_path for block in blocks} >= {
        "Example Protocol > 1 . Introduction",
        "Example Protocol > 1 . Introduction > 1.1 . Retry behavior",
    }
    assert len(requirements) == 2
    assert {requirement.modality.value for requirement in requirements} == {"MUST", "SHOULD"}


def test_paginated_rfc_conversion_is_repeatable_and_relocation_invariant(tmp_path: Path) -> None:
    first = tmp_path / "first.html"
    relocated_dir = tmp_path / "elsewhere"
    relocated_dir.mkdir()
    relocated = relocated_dir / "renamed.html"
    first.write_bytes(PAGINATED_RFC)
    relocated.write_bytes(PAGINATED_RFC)

    a = load_document(first, adapter=AdapterName.RFC)
    b = load_document(first, adapter=AdapterName.RFC)
    c = load_document(relocated, adapter=AdapterName.RFC)

    assert a.working_html == b.working_html == c.working_html
    assert a.document_version == b.document_version == c.document_version


def test_utf8_bom_does_not_change_paginated_rfc_family(tmp_path: Path) -> None:
    path = tmp_path / "neutral.html"
    path.write_bytes(b"\xef\xbb\xbf" + PAGINATED_RFC)

    adapted = load_document(path, adapter=AdapterName.AUTO)

    assert adapted.family.value == "rfc"
    assert normalize_html(adapted.working_html)
