"""Strict, deterministic byte and markup checks shared by source adapters."""

from __future__ import annotations

import codecs
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal, Never

from lxml import etree, html

from normshift.adapters.errors import AdapterParseError
from normshift.model.types import DocumentFamily
from normshift.normalize.html_normalize import normalize_html

_SUPPORTED_ENCODINGS = frozenset({"ascii", "utf-8"})
_UNSUPPORTED_BOMS = (
    b"\x00\x00\xfe\xff",
    b"\xff\xfe\x00\x00",
    b"\xfe\xff",
    b"\xff\xfe",
)
_XML_ENCODING_RE = re.compile(
    r"\A\ufeff?[ \t\r\n]*<\?xml(?=[ \t\r\n])[^>]*\bencoding[ \t\r\n]*="
    r"[ \t\r\n]*['\"]([^'\"]+)['\"]",
)
_CONTENT_TYPE_CHARSET_RE = re.compile(
    r"(?:^|;)\s*charset\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^;\s]+))",
    re.IGNORECASE,
)
_CUSTOM_XML_ENTITY_REF_RE = re.compile(r"&([A-Za-z_:][A-Za-z0-9_.:-]*);")
_XML_NAME_RE = re.compile(r"[A-Za-z_:][A-Za-z0-9_.:-]*")
_XML_PREDEFINED_ENTITIES = frozenset({"amp", "apos", "gt", "lt", "quot"})
_RFC_XML_NAMESPACES = frozenset({"", "urn:ietf:params:xml:ns:rfc"})
_HTML_TAG_NAME_RE = re.compile(r"[A-Za-z][^\t\n\r\f />]*")
_HTML_RAW_TEXT_ELEMENTS = frozenset(
    {
        "iframe",
        "noembed",
        "noframes",
        "script",
        "style",
        "textarea",
        "title",
        "xmp",
    }
)

_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_OPTIONAL_END_ELEMENTS = frozenset(
    {
        "body",
        "colgroup",
        "dd",
        "dt",
        "head",
        "html",
        "li",
        "optgroup",
        "option",
        "p",
        "rb",
        "rp",
        "rt",
        "rtc",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
    }
)
_P_IMPLICIT_CLOSE_STARTS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "div",
        "dl",
        "fieldset",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hgroup",
        "hr",
        "main",
        "menu",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "ul",
    }
)

_RFC_EDITOR_TERMINAL_MARKERS = ("full copyright statement",)
_WHATWG_MIN_REFERENCE_PAIRS = 1
_WHATWG_MAX_REFERENCE_PAIRS = 4_096
_WHATWG_MIN_TRAILING_SCRIPT_BUNDLE = 3
_WHATWG_MAX_TRAILING_SCRIPT_BUNDLE = 16


class _HtmlCompletenessParser(HTMLParser):
    """Track non-optional open elements without repairing truncated input."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.saw_element = False

    def _close_top_if(self, names: frozenset[str]) -> None:
        if self.stack and self.stack[-1] in names:
            self.stack.pop()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        name = tag.lower()
        self.saw_element = True
        if name in _VOID_ELEMENTS:
            return
        if self.stack and self.stack[-1] == "p" and name in _P_IMPLICIT_CLOSE_STARTS:
            self.stack.pop()
        if name == "li":
            self._close_top_if(frozenset({"li"}))
        elif name in {"dt", "dd"}:
            self._close_top_if(frozenset({"dt", "dd"}))
        elif name == "tr":
            self._close_top_if(frozenset({"tr"}))
        elif name in {"td", "th"}:
            self._close_top_if(frozenset({"td", "th"}))
        elif name == "option":
            self._close_top_if(frozenset({"option"}))
        elif name == "optgroup":
            self._close_top_if(frozenset({"option", "optgroup"}))
        self.stack.append(name)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag, attrs
        self.saw_element = True

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name in _VOID_ELEMENTS:
            return
        if name not in self.stack:
            self.errors.append(f"closing tag </{name}> has no open element")
            return
        while self.stack and self.stack[-1] != name:
            top = self.stack[-1]
            if top not in _OPTIONAL_END_ELEMENTS:
                self.errors.append(f"element <{top}> is still open before </{name}>")
                return
            self.stack.pop()
        if self.stack:
            self.stack.pop()


class _EncodingDeclarationParser(HTMLParser):
    """Collect only encoding declarations on genuine ``meta`` start tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.declarations: list[str] = []
        self.errors: list[str] = []

    def _handle_meta(self, attrs: list[tuple[str, str | None]]) -> None:
        values: dict[str, list[str]] = {}
        for name, value in attrs:
            key = name.lower()
            if key in {"charset", "content", "http-equiv"}:
                values.setdefault(key, []).append(value or "")
        duplicated = sorted(name for name, items in values.items() if len(items) > 1)
        if duplicated:
            self.errors.append(
                "duplicate encoding-sensitive meta attribute(s): " + ", ".join(duplicated)
            )
            return
        charset = values.get("charset")
        if charset:
            self.declarations.append(charset[0].strip())
        http_equiv = values.get("http-equiv")
        content = values.get("content")
        if (
            http_equiv
            and content
            and http_equiv[0].strip().casefold() == "content-type"
        ):
            matches = list(_CONTENT_TYPE_CHARSET_RE.finditer(content[0]))
            if len(matches) > 1:
                self.errors.append(
                    "one http-equiv content attribute has multiple charset parameters"
                )
            elif matches:
                self.declarations.append(
                    next(value for value in matches[0].groups() if value is not None)
                )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "meta":
            self._handle_meta(attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _html_declared_encodings(
    text: str,
    *,
    path: Path,
    adapter_id: str,
) -> set[str]:
    parser = _EncodingDeclarationParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # pragma: no cover - defensive stdlib parser boundary
        raise AdapterParseError(
            f"Failed to tokenize HTML encoding declarations: {path}: {exc}",
            adapter_id=adapter_id,
        ) from exc
    if parser.errors:
        raise AdapterParseError(
            f"Ambiguous HTML encoding declaration ({parser.errors[0]}): {path}",
            adapter_id=adapter_id,
        )
    return {value.strip().lower() for value in parser.declarations}


def _declared_encodings(text: str, *, kind: Literal["html", "xml"]) -> set[str]:
    if kind == "html":
        raise AssertionError("HTML declarations require lexical parser context")
    xml_match = _XML_ENCODING_RE.search(text)
    return {xml_match.group(1).strip().lower()} if xml_match is not None else set()


def _canonical_declared_encodings(
    text: str,
    *,
    path: Path,
    adapter_id: str,
    kind: Literal["html", "xml"],
) -> set[str]:
    canonical: set[str] = set()
    declarations = (
        _html_declared_encodings(text, path=path, adapter_id=adapter_id)
        if kind == "html"
        else _declared_encodings(text, kind=kind)
    )
    for declaration in sorted(declarations):
        try:
            name = codecs.lookup(declaration).name
        except LookupError as exc:
            raise AdapterParseError(
                f"Unsupported declared source encoding {declaration!r}: {path}",
                adapter_id=adapter_id,
            ) from exc
        if name not in _SUPPORTED_ENCODINGS:
            raise AdapterParseError(
                f"Unsupported declared source encoding {declaration!r}: {path}",
                adapter_id=adapter_id,
            )
        canonical.add(name)
    if len(canonical) > 1:
        values = ", ".join(sorted(canonical))
        raise AdapterParseError(
            f"Conflicting declared source encodings ({values}): {path}",
            adapter_id=adapter_id,
        )
    return canonical


def _replace_encoding_value(match: re.Match[str]) -> str:
    value = match.group(0)
    start = match.start(1) - match.start(0)
    end = match.end(1) - match.start(0)
    return value[:start] + "utf-8" + value[end:]


def _canonicalize_xml_encoding_declaration(text: str) -> str:
    return _XML_ENCODING_RE.sub(_replace_encoding_value, text)


def decode_supported_text(
    raw: bytes,
    *,
    path: Path,
    adapter_id: str,
    kind: Literal["html", "xml"] = "html",
) -> str:
    """Return strict UTF-8 text after rejecting binary controls and other encodings."""
    if not raw.strip():
        raise AdapterParseError(f"Empty source document: {path}", adapter_id=adapter_id)
    if raw.startswith(_UNSUPPORTED_BOMS):
        raise AdapterParseError(
            f"Unsupported UTF-16/UTF-32 source encoding: {path}",
            adapter_id=adapter_id,
        )
    try:
        text = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise AdapterParseError(
            f"Source is not strict UTF-8: {path}: {exc}",
            adapter_id=adapter_id,
        ) from exc

    for char in text:
        if unicodedata.category(char) == "Cc" and char not in {"\t", "\n", "\r"}:
            raise AdapterParseError(
                f"Source contains forbidden binary control U+{ord(char):04X}: {path}",
                adapter_id=adapter_id,
            )

    declared = _canonical_declared_encodings(
        text,
        path=path,
        adapter_id=adapter_id,
        kind=kind,
    )
    if "ascii" in declared and not raw.isascii():
        raise AdapterParseError(
            f"US-ASCII source declaration conflicts with non-ASCII bytes: {path}",
            adapter_id=adapter_id,
        )
    return text


def canonicalize_supported_html(raw: bytes, *, path: Path, adapter_id: str) -> bytes:
    """Return strict UTF-8 HTML bytes after validating real encoding declarations."""
    text = decode_supported_text(raw, path=path, adapter_id=adapter_id)
    return text.encode("utf-8")


def _html_markup_end(text: str, start: int) -> int | None:
    """Return the first unquoted ``>`` after ``start``, or ``None`` at EOF."""
    quote: str | None = None
    index = start
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == ">":
            return index + 1
        index += 1
    return None


def _raise_incomplete_html_token(
    detail: str,
    *,
    path: Path,
    adapter_id: str,
) -> Never:
    raise AdapterParseError(
        f"Structurally incomplete HTML source ({detail}): {path}",
        adapter_id=adapter_id,
    )


def _validate_html_lexical_tokens(text: str, *, path: Path, adapter_id: str) -> None:
    """Reject markup tokens or attribute quotes that remain open at EOF.

    HTMLParser repairs several such proper prefixes when ``close()`` is called.
    This independent scan treats quoted angle brackets as data and skips the
    contents of raw-text elements until their matching end tag.
    """
    index = 0
    while index < len(text):
        token_start = text.find("<", index)
        if token_start < 0:
            return
        if text.startswith("<![CDATA[", token_start):
            cdata_end = text.find("]]>", token_start + 9)
            if cdata_end < 0:
                _raise_incomplete_html_token(
                    "unterminated markup token (CDATA)",
                    path=path,
                    adapter_id=adapter_id,
                )
            index = cdata_end + 3
            continue
        if text.startswith("<!--", token_start):
            comment_end = text.find("-->", token_start + 4)
            if comment_end < 0:
                _raise_incomplete_html_token(
                    "unterminated markup token (comment)",
                    path=path,
                    adapter_id=adapter_id,
                )
            index = comment_end + 3
            continue

        next_index = token_start + 1
        if next_index >= len(text):
            _raise_incomplete_html_token(
                "unterminated start-tag token",
                path=path,
                adapter_id=adapter_id,
            )
        next_char = text[next_index]
        token_kind: str | None = None
        tag_name: str | None = None
        if next_char == "/":
            token_kind = "end-tag"
        elif next_char == "!":
            token_kind = "declaration"
        elif next_char == "?":
            token_kind = "processing-instruction"
        else:
            name_match = _HTML_TAG_NAME_RE.match(text, next_index)
            if name_match is not None:
                token_kind = "start-tag"
                tag_name = name_match.group(0).casefold()

        if token_kind is None:
            index = next_index
            continue
        markup_end = _html_markup_end(text, next_index + 1)
        if markup_end is None:
            _raise_incomplete_html_token(
                f"unterminated {token_kind} token or attribute quote",
                path=path,
                adapter_id=adapter_id,
            )

        token_text = text[token_start:markup_end]
        index = markup_end
        if (
            token_kind == "start-tag"
            and tag_name in _HTML_RAW_TEXT_ELEMENTS
            and not token_text[:-1].rstrip().endswith("/")
        ):
            assert tag_name is not None
            end_match = re.search(
                rf"</{re.escape(tag_name)}(?=[\t\n\r\f />])",
                text[index:],
                re.IGNORECASE,
            )
            if end_match is None:
                _raise_incomplete_html_token(
                    f"unterminated raw-text element <{tag_name}>",
                    path=path,
                    adapter_id=adapter_id,
                )
            index += end_match.start()


def validate_complete_html(raw: bytes, *, path: Path, adapter_id: str) -> etree._Element:
    """Validate strict text plus lexically complete HTML, then return its parsed tree."""
    text = decode_supported_text(raw, path=path, adapter_id=adapter_id)
    if not text.rstrip().endswith(">"):
        raise AdapterParseError(
            f"HTML source is truncated before a closing tag boundary: {path}",
            adapter_id=adapter_id,
        )
    _validate_html_lexical_tokens(text, path=path, adapter_id=adapter_id)

    parser = _HtmlCompletenessParser()
    try:
        parser.feed(text)
    except Exception as exc:  # pragma: no cover - defensive stdlib parser boundary
        raise AdapterParseError(
            f"Failed to tokenize HTML source: {path}: {exc}",
            adapter_id=adapter_id,
        ) from exc
    if parser.rawdata:
        _raise_incomplete_html_token(
            "unterminated markup token retained by HTML tokenizer",
            path=path,
            adapter_id=adapter_id,
        )
    try:
        parser.close()
    except Exception as exc:  # pragma: no cover - defensive stdlib parser boundary
        raise AdapterParseError(
            f"Failed to close HTML tokenizer: {path}: {exc}",
            adapter_id=adapter_id,
        ) from exc
    non_optional_open = [name for name in parser.stack if name not in _OPTIONAL_END_ELEMENTS]
    if not parser.saw_element or parser.errors or non_optional_open:
        detail = parser.errors[0] if parser.errors else (
            f"unclosed element <{non_optional_open[-1]}>"
            if non_optional_open
            else "no HTML element"
        )
        raise AdapterParseError(
            f"Structurally incomplete HTML source ({detail}): {path}",
            adapter_id=adapter_id,
        )

    try:
        tree = html.fromstring(
            text.encode("utf-8"),
            parser=html.HTMLParser(encoding="utf-8"),
        )
    except Exception as exc:  # noqa: BLE001
        raise AdapterParseError(
            f"Failed to parse HTML source: {path}: {exc}",
            adapter_id=adapter_id,
        ) from exc
    if not isinstance(tree, etree._Element):
        raise AdapterParseError(f"HTML root is not an element: {path}", adapter_id=adapter_id)
    return tree


def _xml_markup_end(text: str, start: int, *, doctype: bool) -> tuple[int, bool]:
    quote: str | None = None
    subset_depth = 0
    saw_subset = False
    index = start
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif doctype and char == "[":
            subset_depth += 1
            saw_subset = True
        elif doctype and char == "]" and subset_depth:
            subset_depth -= 1
        elif char == ">" and subset_depth == 0:
            return index + 1, saw_subset
        index += 1
    return len(text), saw_subset


def _validate_xml_lexical_policy(text: str, *, path: Path, adapter_id: str) -> None:
    """Reject custom DTD/entity semantics before invoking any XML parser."""
    index = 0
    while index < len(text):
        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            index = len(text) if end < 0 else end + 3
            continue
        if text.startswith("<![CDATA[", index):
            end = text.find("]]>", index + 9)
            index = len(text) if end < 0 else end + 3
            continue
        if text.startswith("<?", index):
            end = text.find("?>", index + 2)
            index = len(text) if end < 0 else end + 2
            continue
        if text[index : index + 9].casefold() == "<!doctype":
            end, saw_subset = _xml_markup_end(text, index + 9, doctype=True)
            if saw_subset:
                raise AdapterParseError(
                    f"XML DTD internal subsets/entity declarations are not supported: {path}",
                    adapter_id=adapter_id,
                )
            index = end
            continue
        if text[index : index + 8].casefold() == "<!entity":
            raise AdapterParseError(
                f"XML entity declarations are not supported: {path}",
                adapter_id=adapter_id,
            )
        if text[index] == "&":
            match = _CUSTOM_XML_ENTITY_REF_RE.match(text, index)
            if match is not None and match.group(1) not in _XML_PREDEFINED_ENTITIES:
                raise AdapterParseError(
                    f"XML custom entity references are not supported: {path}",
                    adapter_id=adapter_id,
                )
        index += 1


def _xml_prolog_identity(text: str) -> tuple[bool, str | None, str | None]:
    index = 0
    explicit_xml = False
    doctype_name: str | None = None
    while True:
        while index < len(text) and text[index].isspace():
            index += 1
        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            if end < 0:
                return explicit_xml, doctype_name, None
            index = end + 3
            continue
        if text.startswith("<?", index):
            target = _XML_NAME_RE.match(text, index + 2)
            if target is not None and target.group(0).casefold() == "xml":
                explicit_xml = True
            end = text.find("?>", index + 2)
            if end < 0:
                return explicit_xml, doctype_name, None
            index = end + 2
            continue
        if text[index : index + 9].casefold() == "<!doctype":
            cursor = index + 9
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            name = _XML_NAME_RE.match(text, cursor)
            if name is not None:
                doctype_name = name.group(0)
            index, _saw_subset = _xml_markup_end(text, cursor, doctype=True)
            continue
        break
    if index >= len(text) or text[index] != "<":
        return explicit_xml, doctype_name, None
    root = _XML_NAME_RE.match(text, index + 1)
    return explicit_xml, doctype_name, root.group(0) if root is not None else None


def is_rfc_xml_candidate(raw: bytes) -> bool:
    """Sniff an RFC/XML prolog from bytes without consulting a filename suffix."""
    try:
        text = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        return False
    explicit_xml, doctype_name, root_name = _xml_prolog_identity(text)

    def local(value: str | None) -> str:
        return "" if value is None else value.rsplit(":", 1)[-1].casefold()

    return explicit_xml or local(doctype_name) == "rfc" or local(root_name) == "rfc"


def validate_complete_xml(raw: bytes, *, path: Path, adapter_id: str) -> etree._Element:
    """Validate strict text and a complete, network-free XML tree."""
    text = decode_supported_text(raw, path=path, adapter_id=adapter_id, kind="xml")
    _validate_xml_lexical_policy(text, path=path, adapter_id=adapter_id)
    canonical = _canonicalize_xml_encoding_declaration(text).encode("utf-8")
    parser = etree.XMLParser(
        attribute_defaults=False,
        dtd_validation=False,
        encoding="utf-8",
        load_dtd=False,
        no_network=True,
        recover=False,
        resolve_entities=False,
    )
    try:
        root = etree.fromstring(canonical, parser=parser)
    except Exception as exc:  # noqa: BLE001
        raise AdapterParseError(
            f"Failed to parse complete XML source: {path}: {exc}",
            adapter_id=adapter_id,
        ) from exc
    if not isinstance(root, etree._Element):
        raise AdapterParseError(f"XML root is not an element: {path}", adapter_id=adapter_id)
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise AdapterParseError(
            f"XML entity references are not supported: {path}",
            adapter_id=adapter_id,
        )
    return root


def validate_rfc_xml(raw: bytes, *, path: Path, adapter_id: str) -> etree._Element:
    """Return one safe RFC XML root with namespace-consistent ``middle`` structure."""
    root = validate_complete_xml(raw, path=path, adapter_id=adapter_id)
    root_qname = etree.QName(root)
    namespace = root_qname.namespace or ""
    if root_qname.localname != "rfc" or namespace not in _RFC_XML_NAMESPACES:
        raise AdapterParseError(
            f"XML source is not structurally recognized as RFC XML: {path}",
            adapter_id=adapter_id,
        )
    direct_middle = [
        element
        for element in root
        if isinstance(element.tag, str)
        and etree.QName(element).localname == "middle"
        and (etree.QName(element).namespace or "") == namespace
    ]
    if len(direct_middle) != 1:
        raise AdapterParseError(
            f"RFC XML source lacks one direct namespace-consistent middle structure: {path}",
            adapter_id=adapter_id,
        )
    return root


def _explicit_html_terminal(text: str) -> bool:
    return re.search(r"</html\s*>\s*\Z", text, re.IGNORECASE) is not None


def _validate_rfc_editor_terminal(
    tree: etree._Element,
    text: str,
    *,
    path: Path,
    adapter_id: str,
) -> None:
    pre_nodes = tree.xpath("//pre")
    final_classes = (
        {token.casefold() for token in str(pre_nodes[-1].get("class") or "").split()}
        if pre_nodes
        else set()
    )
    if (
        len(pre_nodes) < 2
        or "newpage" not in final_classes
        or re.search(r"</pre\s*>\r?\n\Z", text, re.IGNORECASE) is None
    ):
        raise AdapterParseError(
            f"RFC Editor source lacks its terminal preformatted page: {path}",
            adapter_id=adapter_id,
        )
    final_page = " ".join("".join(pre_nodes[-1].itertext()).split()).lower()
    if not any(marker in final_page for marker in _RFC_EDITOR_TERMINAL_MARKERS):
        raise AdapterParseError(
            f"RFC Editor source lacks reviewed terminal legal matter: {path}",
            adapter_id=adapter_id,
        )


def _validate_whatwg_review_draft_terminal(
    tree: etree._Element,
    text: str,
    *,
    path: Path,
    adapter_id: str,
) -> None:
    bodies = tree.xpath("//body")
    if len(bodies) != 1 or "status-rd" not in {
        token.casefold() for token in str(bodies[0].get("class") or "").split()
    }:
        raise AdapterParseError(
            f"WHATWG terminal lacks reviewed Review Draft body structure: {path}",
            adapter_id=adapter_id,
        )
    children = [element for element in bodies[0] if isinstance(element.tag, str)]
    trailing_scripts: list[etree._Element] = []
    while children and str(children[-1].tag).casefold() == "script":
        trailing_scripts.append(children.pop())
    trailing_scripts.reverse()
    color_scheme_profiles = [
        str(element.get("content") or "")
        for element in tree.xpath("//head/meta")
        if str(element.get("name") or "").casefold() == "color-scheme"
    ]
    if len(color_scheme_profiles) > 1 or (
        color_scheme_profiles
        and set(color_scheme_profiles[0].casefold().split()) != {"dark", "light"}
    ):
        raise AdapterParseError(
            f"WHATWG terminal has an ambiguous generation profile: {path}",
            adapter_id=adapter_id,
        )
    scriptless_profile = bool(color_scheme_profiles)
    if scriptless_profile and trailing_scripts:
        raise AdapterParseError(
            f"WHATWG terminal has scripts outside its scriptless profile: {path}",
            adapter_id=adapter_id,
        )
    if not scriptless_profile and not (
        _WHATWG_MIN_TRAILING_SCRIPT_BUNDLE
        <= len(trailing_scripts)
        <= _WHATWG_MAX_TRAILING_SCRIPT_BUNDLE
    ):
        raise AdapterParseError(
            f"WHATWG terminal has an incomplete trailing script bundle: {path}",
            adapter_id=adapter_id,
        )
    if any(
        script.get("src") is not None
        or len(script) != 0
        or not (script.text or "").strip()
        for script in trailing_scripts
    ):
        raise AdapterParseError(
            f"WHATWG terminal has a non-inline or empty script: {path}",
            adapter_id=adapter_id,
        )
    if len(children) < 5 or [str(element.tag).casefold() for element in children[-5:]] != [
        "h2",
        "h3",
        "dl",
        "h3",
        "dl",
    ]:
        raise AdapterParseError(
            f"WHATWG terminal lacks paired reference sections: {path}",
            adapter_id=adapter_id,
        )
    for references in (children[-3], children[-1]):
        terms = [element for element in references if isinstance(element.tag, str)]
        pair_count = len(terms) // 2
        if (
            len(terms) % 2
            or not (_WHATWG_MIN_REFERENCE_PAIRS <= pair_count <= _WHATWG_MAX_REFERENCE_PAIRS)
            or any(
                str(element.tag).casefold() != ("dt" if index % 2 == 0 else "dd")
                for index, element in enumerate(terms)
            )
        ):
            raise AdapterParseError(
                f"WHATWG terminal has incomplete reference pairs: {path}",
                adapter_id=adapter_id,
            )
    expected_end = r"</script\s*>\s*\Z" if trailing_scripts else r"</dl\s*>\s*\Z"
    if re.search(expected_end, text, re.IGNORECASE) is None:
        raise AdapterParseError(
            f"WHATWG terminal lacks its reviewed serialization: {path}",
            adapter_id=adapter_id,
        )


def validate_acquisition_terminal(
    raw: bytes,
    *,
    path: Path,
    family: DocumentFamily,
    adapter_id: str,
) -> None:
    """Require a reviewed family terminal for an acquisition source snapshot.

    Exact manifest byte length and SHA-256 remain authoritative. This additional
    gate rejects known balanced-prefix truncations for the frozen M1 source
    formats; it is not a generic proof that arbitrary HTML is semantically whole.
    """
    prefix = raw.lstrip()
    if prefix.startswith(b"\xef\xbb\xbf"):
        prefix = prefix[3:].lstrip()
    lowered = prefix.lower()
    if family == DocumentFamily.RFC and is_rfc_xml_candidate(raw):
        validate_rfc_xml(raw, path=path, adapter_id=adapter_id)
        return

    text = decode_supported_text(raw, path=path, adapter_id=adapter_id)
    tree = validate_complete_html(raw, path=path, adapter_id=adapter_id)
    if _explicit_html_terminal(text):
        return
    if family == DocumentFamily.RFC and lowered.startswith(b"<pre"):
        _validate_rfc_editor_terminal(tree, text, path=path, adapter_id=adapter_id)
        return
    if family == DocumentFamily.WHATWG:
        _validate_whatwg_review_draft_terminal(tree, text, path=path, adapter_id=adapter_id)
        return
    raise AdapterParseError(
        f"Acquisition source lacks a reviewed {family.value} document terminal: {path}",
        adapter_id=adapter_id,
    )


def require_nonempty_normalized_body(
    working_html: bytes,
    *,
    path: Path,
    adapter_id: str,
) -> None:
    """Reject adapter output that cannot produce at least one normalized text block."""
    try:
        blocks = normalize_html(working_html)
    except ValueError as exc:
        raise AdapterParseError(
            f"Adapter output normalization failed: {path}: {exc}",
            adapter_id=adapter_id,
        ) from exc
    if not blocks:
        raise AdapterParseError(
            f"Adapter output has an empty normalized body: {path}",
            adapter_id=adapter_id,
        )
