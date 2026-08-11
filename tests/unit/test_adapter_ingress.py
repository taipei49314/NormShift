"""Fail-closed adapter-ingress and exclusive-family regressions."""

from __future__ import annotations

from pathlib import Path

import pytest

from normshift.adapters.detect import detect_family
from normshift.adapters.errors import AdapterDetectionError, AdapterParseError
from normshift.adapters.ingress import validate_acquisition_terminal
from normshift.adapters.registry import load_document
from normshift.model.types import AdapterName, DocumentFamily

RFC_HTML = b"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>RFC 9000 Example</title></head><body><div class="rfc">
<h1>RFC 9000 Example</h1><p>Endpoints MUST validate input.</p>
</div></body></html>"""
W3C_HTML = b"""<!DOCTYPE html>
<html typeof="bibo:Document w3p:REC"
prefix="bibo: http://purl.org/ontology/bibo/ w3p: http://www.w3.org/2001/02pd/rec54#">
<head><meta charset="utf-8"><title>Example API</title></head>
<body><main><h1>Example API</h1><p>Clients MUST validate input.</p></main></body></html>"""
WHATWG_HTML = b"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Example Living Standard</title>
<link rel="stylesheet" href="https://resources.whatwg.org/spec.css"></head>
<body><a class="logo" href="https://whatwg.org/">Standards publisher</a>
<p>User agents must validate input.</p></body></html>"""
GENERIC_HTML = b"""<!DOCTYPE html><html><body>
<p>Implementations MUST validate input.</p></body></html>"""

SPECIALIZED_CASES = (
    (AdapterName.RFC, DocumentFamily.RFC, RFC_HTML),
    (AdapterName.W3C, DocumentFamily.W3C, W3C_HTML),
    (AdapterName.WHATWG, DocumentFamily.WHATWG, WHATWG_HTML),
)


@pytest.mark.parametrize(("adapter", "family", "raw"), SPECIALIZED_CASES)
def test_structural_family_detection_is_path_independent(
    tmp_path: Path,
    adapter: AdapterName,
    family: DocumentFamily,
    raw: bytes,
) -> None:
    first = tmp_path / "neutral-a.html"
    second_dir = tmp_path / "relocated"
    second_dir.mkdir()
    second = second_dir / "neutral-b.html"
    first.write_bytes(raw)
    second.write_bytes(raw)

    first_document = load_document(first, AdapterName.AUTO)
    second_document = load_document(second, adapter)

    assert first_document.family == family
    assert second_document.family == family
    assert first_document.working_html == second_document.working_html
    assert first_document.document_version == second_document.document_version


@pytest.mark.parametrize(
    ("expected", "raw", "forced"),
    [
        (expected, raw, forced)
        for expected, _family, raw in SPECIALIZED_CASES
        for forced in (AdapterName.RFC, AdapterName.W3C, AdapterName.WHATWG)
        if forced != expected
    ],
)
def test_forced_specialized_adapter_rejects_every_wrong_family(
    tmp_path: Path,
    expected: AdapterName,
    raw: bytes,
    forced: AdapterName,
) -> None:
    path = tmp_path / "neutral.html"
    path.write_bytes(raw)

    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, forced)


@pytest.mark.parametrize("raw", [RFC_HTML, W3C_HTML, WHATWG_HTML])
def test_forced_generic_adapter_cannot_launder_specialized_family(
    tmp_path: Path,
    raw: bytes,
) -> None:
    path = tmp_path / "neutral.html"
    path.write_bytes(raw)

    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, AdapterName.HTML)


def test_ambiguous_structural_family_fails_closed(tmp_path: Path) -> None:
    ambiguous = W3C_HTML.replace(
        b"</head>",
        b'<link rel="stylesheet" href="https://resources.whatwg.org/spec.css"></head>',
    ).replace(
        b"<body>",
        b'<body><a class="logo" href="https://whatwg.org/">WHATWG Review Draft</a>',
    ).replace(b"<title>Example API</title>", b"<title>Example Living Standard</title>")
    path = tmp_path / "ambiguous.html"
    path.write_bytes(ambiguous)

    with pytest.raises(AdapterDetectionError, match="Ambiguous structural document family"):
        detect_family(path, ambiguous)
    with pytest.raises(AdapterDetectionError, match="Ambiguous structural document family"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize("raw", [RFC_HTML, W3C_HTML, WHATWG_HTML, GENERIC_HTML])
@pytest.mark.parametrize("control", [b"\x00", b"\x01", b"\x7f"])
def test_binary_controls_are_rejected(tmp_path: Path, raw: bytes, control: bytes) -> None:
    midpoint = len(raw) // 2
    path = tmp_path / "control.html"
    path.write_bytes(raw[:midpoint] + control + raw[midpoint:])

    with pytest.raises(AdapterDetectionError, match="forbidden binary control"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize("raw", [RFC_HTML, W3C_HTML, WHATWG_HTML, GENERIC_HTML])
def test_half_truncated_html_is_rejected(tmp_path: Path, raw: bytes) -> None:
    path = tmp_path / "truncated.html"
    path.write_bytes(raw[: len(raw) // 2])

    with pytest.raises(AdapterDetectionError, match="truncated|incomplete"):
        load_document(path, AdapterName.AUTO)


def test_unclosed_non_optional_outer_structure_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "incomplete.html"
    path.write_bytes(b"<html><body><section><p>Complete text node.</p>")

    with pytest.raises(AdapterDetectionError, match="unclosed element <section>"):
        load_document(path, AdapterName.AUTO)


def test_unterminated_markup_token_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "incomplete-comment.html"
    path.write_bytes(b"<html><body><p>Complete text node.</p><!-- unfinished>")

    with pytest.raises(AdapterDetectionError, match="unterminated markup token"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize(
    ("adapter", "family", "raw"),
    [
        *SPECIALIZED_CASES,
        (AdapterName.HTML, DocumentFamily.GENERIC_HTML, GENERIC_HTML),
    ],
)
def test_quoted_angle_brackets_are_valid_but_their_proper_prefixes_fail_closed(
    tmp_path: Path,
    adapter: AdapterName,
    family: DocumentFamily,
    raw: bytes,
) -> None:
    complete = raw.replace(
        b"<body>",
        b'<body data-boundary="left > center < nested > right">',
        1,
    )
    path = tmp_path / "quoted-angle-boundary.html"
    path.write_bytes(complete)

    assert load_document(path, AdapterName.AUTO).family == family
    assert load_document(path, adapter).family == family

    prefixes = (
        complete[: complete.index(b"left >") + len(b"left >")],
        complete[: complete.index(b"center <") + len(b"center <")],
        complete[: complete.index(b"nested >") + len(b"nested >")],
    )
    for prefix in prefixes:
        path.write_bytes(prefix)
        with pytest.raises(AdapterDetectionError, match="truncated|incomplete|unterminated"):
            load_document(path, AdapterName.AUTO)
        with pytest.raises(AdapterParseError, match="truncated|incomplete|unterminated"):
            load_document(path, adapter)


@pytest.mark.parametrize(
    "fragment",
    [
        b'<div title="unfinished>',
        b'</div invalid="unfinished>',
        b'<!DOCTYPE html SYSTEM "unfinished>',
        b'<?probe value="unfinished>',
        b'<!-- unfinished>',
    ],
)
def test_each_incomplete_html_lexical_token_type_fails_closed(
    tmp_path: Path,
    fragment: bytes,
) -> None:
    path = tmp_path / "incomplete-lexical-token.html"
    path.write_bytes(b"<html><body><p>Complete text.</p>" + fragment)

    with pytest.raises(AdapterDetectionError, match="incomplete|unterminated"):
        load_document(path, AdapterName.AUTO)


def test_complete_raw_text_comments_and_quoted_markup_remain_valid(tmp_path: Path) -> None:
    path = tmp_path / "complete-lexical-boundaries.html"
    path.write_bytes(
        b"<!DOCTYPE html><html><head>"
        b"<script>const a = '<!--'; const b = '<meta charset=us-ascii>'; "
        b"const c = '<div title=\"unfinished>\"';</script></head>"
        b'<body data-example="<!-- quoted > and < marker -->">'
        b'<noscript><p title="prefix </noscript> <div data-x=\'unfinished > suffix">'
        b"Fallback text.</p></noscript>"
        b"<svg><![CDATA[prefix > <div data-x='unfinished >]]></svg>"
        b"<!-- <div title='quoted > and <'>comment</div> -->"
        b"<p>Clients MUST validate input.</p></body></html>"
    )

    document = load_document(path, AdapterName.AUTO)

    assert document.family == DocumentFamily.GENERIC_HTML
    assert b"Clients MUST validate input." in document.working_html


@pytest.mark.parametrize(
    "raw",
    [
        WHATWG_HTML.decode("utf-8").encode("utf-16"),
        GENERIC_HTML.replace(b'<body>', b'<head><meta charset="windows-1252"></head><body>'),
        b"<html><body><p>\xff</p></body></html>",
    ],
)
def test_unsupported_text_encodings_are_rejected(tmp_path: Path, raw: bytes) -> None:
    path = tmp_path / "encoding.html"
    path.write_bytes(raw)

    with pytest.raises(AdapterDetectionError, match="encoding|strict UTF-8"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize("alias", ["utf-8", "UTF8", "utf_8"])
def test_utf8_encoding_aliases_preserve_non_ascii_text(tmp_path: Path, alias: str) -> None:
    path = tmp_path / "utf8-alias.html"
    path.write_bytes(
        (
            f'<html><head><meta charset="{alias}">'
            "<meta name='version' "
            "content='Caf\N{LATIN SMALL LETTER E WITH ACUTE}-v1'></head>"
            "<body><p>Caf\N{LATIN SMALL LETTER E WITH ACUTE} MUST remain exact.</p>"
            "</body></html>"
        ).encode()
    )

    document = load_document(path, AdapterName.HTML)

    assert "Caf\N{LATIN SMALL LETTER E WITH ACUTE}".encode() in document.working_html
    assert b"Caf?" not in document.working_html
    assert document.document_version == "Caf\N{LATIN SMALL LETTER E WITH ACUTE}-v1"


@pytest.mark.parametrize("alias", ["ascii", "US-ASCII", "ansi_x3.4-1968"])
def test_ascii_encoding_aliases_accept_only_ascii_bytes(tmp_path: Path, alias: str) -> None:
    path = tmp_path / "ascii-alias.html"
    path.write_bytes(
        (
            f'<html><head><meta charset="{alias}"></head>'
            "<body><p>Clients MUST remain exact.</p></body></html>"
        ).encode()
    )

    document = load_document(path, AdapterName.HTML)

    assert b"Clients MUST remain exact." in document.working_html


def test_ascii_declaration_rejects_non_ascii_utf8_bytes(tmp_path: Path) -> None:
    path = tmp_path / "ascii-conflict.html"
    path.write_bytes(
        "<html><head><meta charset='us-ascii'></head>"
        "<body><p>Caf\N{LATIN SMALL LETTER E WITH ACUTE} MUST remain exact.</p>"
        "</body></html>".encode("utf-8")
    )

    with pytest.raises(AdapterDetectionError, match="US-ASCII.*non-ASCII"):
        load_document(path, AdapterName.AUTO)


def test_conflicting_supported_encoding_declarations_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "conflicting-declarations.html"
    path.write_bytes(
        b"<html><head><meta charset='utf8'><meta charset='US-ASCII'></head>"
        b"<body><p>Clients MUST remain exact.</p></body></html>"
    )

    with pytest.raises(AdapterDetectionError, match="Conflicting declared source encodings"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize(
    "content",
    [
        "text/html; charset=utf-8; charset=us-ascii",
        "text/html; charset=us-ascii; charset=utf-8",
        "text/html; charset=UTF8; charset=utf_8",
    ],
)
def test_one_http_equiv_content_rejects_every_duplicate_charset_parameter(
    tmp_path: Path,
    content: str,
) -> None:
    path = tmp_path / "duplicate-content-charset.html"
    path.write_bytes(
        (
            "<html><head><meta http-equiv='content-type' "
            f'content="{content}"></head>'
            "<body><p>Clients MUST validate input.</p></body></html>"
        ).encode()
    )

    with pytest.raises(AdapterDetectionError, match="multiple charset parameters"):
        load_document(path, AdapterName.AUTO)
    with pytest.raises(AdapterParseError, match="multiple charset parameters"):
        load_document(path, AdapterName.HTML)


def test_late_http_equiv_content_still_rejects_duplicate_charset_parameters(
    tmp_path: Path,
) -> None:
    path = tmp_path / "late-duplicate-content-charset.html"
    path.write_bytes(
        (
            "<html><head><title>Generic</title></head><body>"
            + ("x" * 70_000)
            + "<meta http-equiv='content-type' "
            "content='text/html; charset=utf8; charset=UTF8'>"
            "<p>Clients MUST validate input.</p></body></html>"
        ).encode()
    )

    with pytest.raises(AdapterDetectionError, match="multiple charset parameters"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize(
    "declarations",
    [
        (
            "<meta charset='utf-8'>"
            "<meta http-equiv='content-type' content='text/html; charset=us-ascii'>"
        ),
        (
            "<meta http-equiv='content-type' content='text/html; charset=us-ascii'>"
            "<meta charset='utf-8'>"
        ),
        (
            "<meta charset='utf-8' http-equiv='content-type' "
            "content='text/html; charset=us-ascii'>"
        ),
    ],
)
def test_direct_and_http_equiv_charset_conflicts_fail_in_every_order(
    tmp_path: Path,
    declarations: str,
) -> None:
    path = tmp_path / "cross-declaration-conflict.html"
    path.write_bytes(
        (
            f"<html><head>{declarations}</head>"
            "<body><p>Clients MUST validate input.</p></body></html>"
        ).encode()
    )

    with pytest.raises(AdapterDetectionError, match="Conflicting declared source encodings"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize("bom", [b"", b"\xef\xbb\xbf"])
@pytest.mark.parametrize(
    ("adapter", "family", "raw"),
    [
        (
            AdapterName.HTML,
            DocumentFamily.GENERIC_HTML,
            b"<html><head><meta name='version' content='Caf\xc3\xa9-v1'></head>"
            b"<body><p>Caf\xc3\xa9 MUST remain exact.</p></body></html>",
        ),
        (
            AdapterName.RFC,
            DocumentFamily.RFC,
            RFC_HTML.replace(b'<meta charset="utf-8">', b"").replace(
                b"Endpoints", b"Caf\xc3\xa9 endpoints"
            ),
        ),
        (
            AdapterName.W3C,
            DocumentFamily.W3C,
            W3C_HTML.replace(b'<meta charset="utf-8">', b"").replace(
                b"Clients", b"Caf\xc3\xa9 clients"
            ),
        ),
        (
            AdapterName.WHATWG,
            DocumentFamily.WHATWG,
            WHATWG_HTML.replace(b'<meta charset="utf-8">', b"").replace(
                b"User agents", b"Caf\xc3\xa9 user agents"
            ),
        ),
    ],
)
def test_undeclared_utf8_is_explicitly_parsed_without_latin1_fallback(
    tmp_path: Path,
    bom: bytes,
    adapter: AdapterName,
    family: DocumentFamily,
    raw: bytes,
) -> None:
    path = tmp_path / "undeclared-utf8.html"
    path.write_bytes(bom + raw)

    automatic = load_document(path, AdapterName.AUTO)
    forced = load_document(path, adapter)

    assert automatic.family == family
    assert automatic.working_html == forced.working_html
    assert b"Caf\xc3\xa9" in automatic.working_html
    assert b"Caf\xc3\x83\xc2\xa9" not in automatic.working_html
    if family == DocumentFamily.GENERIC_HTML:
        assert automatic.document_version == "Caf\N{LATIN SMALL LETTER E WITH ACUTE}-v1"


@pytest.mark.parametrize(
    "fake_declaration",
    [
        "<!-- <meta charset='us-ascii'> -->",
        "<script>const fake = \"<meta charset='us-ascii'>\";</script>",
        "<meta data-charset='us-ascii'>",
        "<meta content='text/html; charset=us-ascii'>",
    ],
)
def test_non_meta_encoding_text_cannot_create_a_declaration(
    tmp_path: Path,
    fake_declaration: str,
) -> None:
    path = tmp_path / "fake-meta.html"
    raw = (
        f"<html><head>{fake_declaration}</head>"
        "<body><p>Caf\N{LATIN SMALL LETTER E WITH ACUTE} MUST remain exact.</p>"
        "</body></html>"
    ).encode()
    path.write_bytes(raw)

    document = load_document(path, AdapterName.HTML)

    assert b"Caf\xc3\xa9" in document.working_html


def test_real_http_equiv_charset_is_enforced(tmp_path: Path) -> None:
    path = tmp_path / "http-equiv.html"
    path.write_bytes(
        "<html><head><meta http-equiv='Content-Type' "
        "content='text/html; charset=US-ASCII'></head>"
        "<body><p>Caf\N{LATIN SMALL LETTER E WITH ACUTE}</p></body></html>".encode()
    )

    with pytest.raises(AdapterDetectionError, match="US-ASCII.*non-ASCII"):
        load_document(path, AdapterName.AUTO)


def test_duplicate_encoding_sensitive_meta_attribute_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "duplicate-meta-attribute.html"
    path.write_bytes(
        b"<html><head><meta charset='utf-8' charset='US-ASCII'></head>"
        b"<body><p>Clients MUST validate input.</p></body></html>"
    )

    with pytest.raises(AdapterDetectionError, match="duplicate.*charset"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize("state", ["WD", "CR", "PR", "REC", "NOTE"])
def test_reviewed_w3c_publication_states_are_recognized(tmp_path: Path, state: str) -> None:
    path = tmp_path / "reviewed-state.html"
    path.write_bytes(W3C_HTML.replace(b"w3p:REC", f"w3p:{state}".encode()))

    assert load_document(path, AdapterName.AUTO).family == DocumentFamily.W3C


def test_fake_w3c_publication_token_cannot_launder_generic_html(tmp_path: Path) -> None:
    path = tmp_path / "fake-w3c.html"
    raw = W3C_HTML.replace(b"w3p:REC", b"w3p:not-a-reviewed-state")
    path.write_bytes(raw)

    assert detect_family(path, raw) == DocumentFamily.GENERIC_HTML
    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, AdapterName.W3C)


def test_w3c_publication_state_without_prefix_identity_is_generic(tmp_path: Path) -> None:
    path = tmp_path / "unbound-w3c-state.html"
    raw = (
        b'<html typeof="bibo:Document w3p:REC"><head><title>Generic</title></head>'
        b"<body><p>Clients MUST validate input.</p></body></html>"
    )
    path.write_bytes(raw)

    assert detect_family(path, raw) == DocumentFamily.GENERIC_HTML
    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, AdapterName.W3C)


@pytest.mark.parametrize(
    "prefix",
    [
        "bibo: http://purl.org/ontology/bibo/ w3p: https://example.invalid/rec54#",
        "bibo: https://example.invalid/bibo/ w3p: http://www.w3.org/2001/02pd/rec54#",
        (
            "bibo: http://purl.org/ontology/bibo/ "
            "w3p: https://example.invalid/rec54# "
            "other: http://www.w3.org/2001/02pd/rec54#"
        ),
        (
            "bibo: http://purl.org/ontology/bibo/ "
            "w3p: http://www.w3.org/2001/02pd/rec54# "
            "w3p: https://example.invalid/duplicate"
        ),
    ],
)
def test_w3c_publication_state_rejects_misbound_prefixes(
    tmp_path: Path,
    prefix: str,
) -> None:
    path = tmp_path / "misbound-w3c-state.html"
    raw = W3C_HTML.replace(
        (
            b'prefix="bibo: http://purl.org/ontology/bibo/ '
            b'w3p: http://www.w3.org/2001/02pd/rec54#"'
        ),
        f'prefix="{prefix}"'.encode(),
    )
    path.write_bytes(raw)

    assert detect_family(path, raw) == DocumentFamily.GENERIC_HTML
    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, AdapterName.W3C)


W3C_CANONICAL_FALLBACK = b"""<!DOCTYPE html><html><head>
<title>Example API</title><link rel="canonical" href="https://www.w3.org/TR/example/">
</head><body><div class="head"><h1>W3C Recommendation</h1></div>
<main><p>Clients MUST validate input.</p></main></body></html>"""


@pytest.mark.parametrize(
    "url",
    [
        "https://attacker@www.w3.org/TR/example/",
        "https://www.w3.org:443/TR/example/",
        "https://www.w3.org/TR/example/?target=evil",
        "https://www.w3.org/\nTR/example/",
        "https://www.w3.org/TR/../example/",
        "https://www.w3.org.evil.invalid/TR/example/",
        "javascript:https://www.w3.org/TR/example/",
        "/TR/example/",
    ],
)
def test_w3c_canonical_url_laundering_is_rejected(tmp_path: Path, url: str) -> None:
    path = tmp_path / "w3c-url.html"
    raw = W3C_CANONICAL_FALLBACK.replace(
        b"https://www.w3.org/TR/example/",
        url.encode(),
    )
    path.write_bytes(raw)

    assert detect_family(path, raw) == DocumentFamily.GENERIC_HTML
    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, AdapterName.W3C)


def test_exact_w3c_canonical_fallback_is_recognized(tmp_path: Path) -> None:
    path = tmp_path / "w3c-url.html"
    path.write_bytes(W3C_CANONICAL_FALLBACK)

    assert load_document(path, AdapterName.AUTO).family == DocumentFamily.W3C


@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        (
            b"https://resources.whatwg.org/spec.css",
            b"https://attacker@resources.whatwg.org/spec.css",
        ),
        (
            b"https://resources.whatwg.org/spec.css",
            b"https://resources.whatwg.org/spec.css?target=evil",
        ),
        (
            b"https://resources.whatwg.org/spec.css",
            b"https://resources.whatwg.org.evil.invalid/spec.css",
        ),
        (b"https://whatwg.org/", b"https://whatwg.org:443/"),
        (b"https://whatwg.org/", b"javascript:https://whatwg.org/"),
    ],
)
def test_whatwg_primary_url_laundering_is_rejected(
    tmp_path: Path,
    original: bytes,
    replacement: bytes,
) -> None:
    path = tmp_path / "whatwg-url.html"
    raw = WHATWG_HTML.replace(original, replacement)
    path.write_bytes(raw)

    assert detect_family(path, raw) == DocumentFamily.GENERIC_HTML
    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, AdapterName.WHATWG)


WHATWG_CANONICAL_FALLBACK = b"""<!DOCTYPE html><html><head>
<title>Example Living Standard</title>
<link rel="canonical" href="https://html.spec.whatwg.org/multipage/">
</head><body><header>WHATWG Living Standard</header>
<p>User agents must validate input.</p></body></html>"""


@pytest.mark.parametrize(
    "url",
    [
        "https://attacker@html.spec.whatwg.org/multipage/",
        "https://html.spec.whatwg.org:443/multipage/",
        "https://html.spec.whatwg.org/multipage/?target=evil",
        "https://html.spec.whatwg.org/\tmultipage/",
        "https://evil.spec.whatwg.org/multipage/",
        "https://html.spec.whatwg.org/../multipage/",
        "javascript:https://html.spec.whatwg.org/multipage/",
        "/multipage/",
    ],
)
def test_whatwg_canonical_url_laundering_is_rejected(tmp_path: Path, url: str) -> None:
    path = tmp_path / "whatwg-canonical-url.html"
    raw = WHATWG_CANONICAL_FALLBACK.replace(
        b"https://html.spec.whatwg.org/multipage/",
        url.encode(),
    )
    path.write_bytes(raw)

    assert detect_family(path, raw) == DocumentFamily.GENERIC_HTML
    with pytest.raises(AdapterParseError, match="does not match forced"):
        load_document(path, AdapterName.WHATWG)


def test_exact_whatwg_canonical_fallback_is_recognized(tmp_path: Path) -> None:
    path = tmp_path / "whatwg-canonical-url.html"
    path.write_bytes(WHATWG_CANONICAL_FALLBACK)

    assert load_document(path, AdapterName.AUTO).family == DocumentFamily.WHATWG


@pytest.mark.parametrize(
    "preamble",
    [
        b"",
        b"<!DOCTYPE rfc>\n",
        b"<!-- generated by xml2rfc -->\n",
        b'<?xml-stylesheet type="text/xsl" href="rfc.xsl"?>\n',
        (
            b"<!DOCTYPE rfc>\n"
            b"<!-- generated by xml2rfc -->\n"
            b'<?xml-stylesheet type="text/xsl" href="rfc.xsl"?>\n'
        ),
    ],
)
def test_rfc_xml_safe_preamble_variants_are_recognized(
    tmp_path: Path,
    preamble: bytes,
) -> None:
    path = tmp_path / "rfc.xml"
    path.write_bytes(
        b'<?xml version="1.0" encoding="US-ASCII"?>\n'
        + preamble
        + (
            b'<rfc xmlns="urn:ietf:params:xml:ns:rfc" number="9999">'
            b"<middle><section><name>Scope</name>"
            b"<t>Clients MUST validate input.</t></section></middle></rfc>"
        )
    )

    document = load_document(path, AdapterName.AUTO)

    assert document.family == DocumentFamily.RFC
    assert b"Clients MUST validate input." in document.working_html


def test_rfc_xml_external_subset_is_not_loaded(tmp_path: Path) -> None:
    path = tmp_path / "rfc.xml"
    path.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<!DOCTYPE rfc SYSTEM "https://invalid.example.test/rfc.dtd">\n'
        b'<rfc number="9999"><middle><section title="Scope">'
        b"<t>Clients MUST validate input.</t></section></middle></rfc>"
    )

    document = load_document(path, AdapterName.AUTO)

    assert document.family == DocumentFamily.RFC


def test_xml_stylesheet_pi_encoding_is_not_an_xml_declaration(tmp_path: Path) -> None:
    path = tmp_path / "rfc-with-stylesheet-pi.data"
    path.write_bytes(
        b'<?xml-stylesheet type="text/xsl" encoding="windows-1252"?>\n'
        b'<rfc number="9999"><middle><section title="Scope">'
        b"<t>Caf\xc3\xa9 MUST remain exact.</t></section></middle></rfc>"
    )

    automatic = load_document(path, AdapterName.AUTO)
    forced = load_document(path, AdapterName.RFC)

    assert automatic.family == DocumentFamily.RFC
    assert automatic.working_html == forced.working_html
    assert b"Caf\xc3\xa9" in automatic.working_html


@pytest.mark.parametrize("alias", ["utf-8", "UTF8", "utf_8"])
def test_rfc_xml_utf8_aliases_preserve_non_ascii_text(tmp_path: Path, alias: str) -> None:
    path = tmp_path / "rfc.xml"
    path.write_bytes(
        (
            f'<?xml version="1.0" encoding="{alias}"?>\n'
            '<rfc number="9999"><middle><section title="Scope">'
            "<t>Caf\N{LATIN SMALL LETTER E WITH ACUTE} MUST remain exact.</t>"
            "</section></middle></rfc>"
        ).encode()
    )

    document = load_document(path, AdapterName.AUTO)

    assert "Caf\N{LATIN SMALL LETTER E WITH ACUTE}".encode() in document.working_html
    assert b"Caf?" not in document.working_html


def test_rfc_xml_custom_entity_reference_is_rejected_without_resolution(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("MUST NOT BE READ", encoding="utf-8")
    path = tmp_path / "rfc.xml"
    path.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        + f'<!DOCTYPE rfc [<!ENTITY external SYSTEM "{sentinel.as_uri()}">]>\n'.encode()
        + (
            b'<rfc number="9999"><middle><section title="Scope">'
            b"<t>&external;</t></section></middle></rfc>"
        )
    )

    with pytest.raises(AdapterDetectionError, match="internal subsets/entity declarations"):
        load_document(path, AdapterName.AUTO)


def test_rfc_xml_custom_attribute_entity_is_rejected_before_parse(tmp_path: Path) -> None:
    path = tmp_path / "rfc-with-attribute-entity.data"
    path.write_bytes(
        b'<rfc number="9999"><middle><section title="&custom;">'
        b"<t>Clients MUST validate input.</t></section></middle></rfc>"
    )

    with pytest.raises(AdapterDetectionError, match="custom entity references"):
        load_document(path, AdapterName.AUTO)


@pytest.mark.parametrize("suffix", ["", ".xml", ".html", ".txt"])
def test_rfc_xml_identity_is_suffix_independent_with_full_safe_prolog(
    tmp_path: Path,
    suffix: str,
) -> None:
    raw = (
        b"<!-- leading comment -->\n"
        b'<?xml-stylesheet type="text/xsl" href="rfc.xsl"?>\n'
        b'<!DOCTYPE rfc SYSTEM "https://invalid.example.test/rfc.dtd">\n'
        b'<rfc xmlns="urn:ietf:params:xml:ns:rfc" number="9999">'
        b"<middle><section><name>Scope</name>"
        b"<t>Clients MUST validate input.</t></section></middle></rfc>"
    )
    path = tmp_path / f"neutral{suffix}"
    path.write_bytes(raw)

    automatic = load_document(path, AdapterName.AUTO)
    forced = load_document(path, AdapterName.RFC)

    assert automatic.family == DocumentFamily.RFC
    assert automatic.working_html == forced.working_html
    assert automatic.document_version == forced.document_version == "9999"


@pytest.mark.parametrize(
    "raw",
    [
        b'<rfc xmlns="https://evil.invalid/rfc"><middle/></rfc>',
        (
            b'<rfc xmlns="urn:ietf:params:xml:ns:rfc">'
            b'<middle xmlns=""><section/></middle></rfc>'
        ),
        b"<rfc><front/></rfc>",
        b"<rfc><front><middle/></front></rfc>",
        b"<!DOCTYPE rfc><html><body><p>Not RFC XML.</p></body></html>",
    ],
)
def test_rfc_xml_requires_exact_root_namespace_and_middle_identity(
    tmp_path: Path,
    raw: bytes,
) -> None:
    path = tmp_path / "wrong-rfc-identity.bin"
    path.write_bytes(raw)

    with pytest.raises(AdapterDetectionError, match="RFC XML|middle"):
        load_document(path, AdapterName.AUTO)
    with pytest.raises(AdapterParseError, match="RFC XML|middle"):
        load_document(path, AdapterName.RFC)


def test_frozen_whatwg_terminal_is_content_neutral_and_structural(
    tmp_path: Path,
) -> None:
    prefix = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="generator" content="arbitrary tool build 123"></head>
<body class="status-RD unrelated-token"><h2>References</h2>
<h3>Normative references</h3>
<dl><dt id="arbitrary-one">[ONE]</dt><dd>First reference.</dd></dl>
<h3>Informative references</h3>
<dl><dt id="arbitrary-two">[TWO]</dt><dd>Second reference.</dd></dl>"""
    segments = (
        b"<script>window.alpha = 1;</script>",
        b"<script>window.beta = 2;</script>",
        b"<script>window.gamma = 3;</script>",
    )
    complete = prefix + b"".join(segments)
    modern_prefix = prefix.replace(
        b"</head>",
        b'<meta name="color-scheme" content="light dark"></head>',
    )
    path = tmp_path / "frozen-whatwg.html"

    validate_acquisition_terminal(
        modern_prefix,
        path=path,
        family=DocumentFamily.WHATWG,
        adapter_id="test",
    )
    validate_acquisition_terminal(
        complete,
        path=path,
        family=DocumentFamily.WHATWG,
        adapter_id="test",
    )
    validate_acquisition_terminal(
        complete.replace(b"arbitrary tool build 123", b"unrelated generator value"),
        path=path,
        family=DocumentFamily.WHATWG,
        adapter_id="test",
    )
    for count in (0, 1, 2):
        with pytest.raises(AdapterParseError, match="terminal"):
            validate_acquisition_terminal(
                prefix + b"".join(segments[:count]),
                path=path,
                family=DocumentFamily.WHATWG,
                adapter_id="test",
            )

    with pytest.raises(AdapterParseError, match="scriptless profile"):
        validate_acquisition_terminal(
            modern_prefix + b"".join(segments),
            path=path,
            family=DocumentFamily.WHATWG,
            adapter_id="test",
        )

    with pytest.raises(AdapterParseError, match="reference pairs"):
        validate_acquisition_terminal(
            modern_prefix.replace(b"<dd>Second reference.</dd>", b""),
            path=path,
            family=DocumentFamily.WHATWG,
            adapter_id="test",
        )


def test_empty_normalized_body_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "empty-body.html"
    path.write_bytes(b"<html><body><script>only chrome</script></body></html>")

    with pytest.raises(AdapterParseError, match="empty normalized body"):
        load_document(path, AdapterName.HTML)


def test_generic_html_and_repeated_load_remain_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "plain.html"
    path.write_bytes(GENERIC_HTML)

    first = load_document(path, AdapterName.AUTO)
    second = load_document(path, AdapterName.AUTO)

    assert first.family == DocumentFamily.GENERIC_HTML
    assert first.working_html == second.working_html
    assert first.document_version == second.document_version
