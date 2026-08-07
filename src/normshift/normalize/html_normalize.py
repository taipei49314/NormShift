"""Structural normalization of local HTML documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lxml import etree, html

BLOCK_IGNORE_TAGS = frozenset(
    {
        "script",
        "style",
        "noscript",
        "pre",
        "samp",
        "kbd",
        "textarea",
        "svg",
        "math",
    }
)

INLINE_CODE_TAGS = frozenset({"code", "var"})
QUOTE_TAGS = frozenset({"blockquote", "q"})

INFORMATIVE_CLASS_TOKENS = frozenset(
    {
        "example",
        "note",
        "informative",
        "non-normative",
        "nonnormative",
        "illustration",
        "sample",
        "issue",
        "warning",
        "advisement",
        "annotation",
        "ednote",
        "editor-note",
        "impl",
        "implementation-note",
        "prac",
        "practice",
        "xxx",
        "todo",
    }
)

# Soft section-title hints (never override explicit normative markers)
INFORMATIVE_SECTION_RE = re.compile(
    r"^(acknowledg|"
    r"references$|normative references$|informative references$|"
    r"change log$|changelog$|revision history$|"
    r"table of contents$|authors'? addresses$)$",
    re.IGNORECASE,
)

HISTORICAL_FRAMING_RE = re.compile(
    r"\b(previous\s+specification|old\s+version|formerly\s+required|"
    r"old\s+text\s+was|historical(?:ly)?|earlier\s+draft|"
    r"were\s+formerly\s+required|was\s+formerly\s+required|"
    r"was\s+required|said\s+clients|stated:)\b",
    re.IGNORECASE,
)

HEADING_TAGS = frozenset({f"h{i}" for i in range(1, 7)})
WS_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedBlock:
    text: str
    normalized_text: str
    section_path: str
    source_locator: str
    structural_index: int
    is_informative: bool
    xpath: str
    protected_spans: tuple[tuple[int, int], ...] = ()


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[-1].lower()
    return tag.lower()


def _class_tokens(el: etree._Element) -> set[str]:
    return {t for t in str(el.get("class") or "").lower().split() if t}


def normalize_whitespace(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def editorial_normalize(text: str) -> str:
    t = text.lower()
    t = WS_RE.sub(" ", t).strip()
    t = re.sub(r"[\"'`“”‘’]", "", t)
    t = re.sub(r"[,.;:!?()\[\]{}]", " ", t)
    t = WS_RE.sub(" ", t).strip()
    return t


def strip_heading_number(text: str) -> str:
    t = re.sub(r"^(?:§\s*)?\d+(?:\.\d+)*\.?\s+", "", text)
    t = re.sub(r"^section\s+\d+(?:\.\d+)*\.?\s+", "", t, flags=re.IGNORECASE)
    return t.strip()


def _heading_text(el: etree._Element) -> str:
    return normalize_whitespace("".join(el.itertext()))


def _element_xpath(el: etree._Element, root: etree._Element) -> str:
    parts: list[str] = []
    node: etree._Element | None = el
    while node is not None:
        parent = node.getparent()
        name = _local_name(node.tag) or "node"
        if parent is None:
            parts.append(name)
            break
        siblings = [c for c in parent if _local_name(c.tag) == name]
        if len(siblings) == 1:
            parts.append(name)
        else:
            try:
                idx = siblings.index(node) + 1
            except ValueError:
                idx = 1
            parts.append(f"{name}[{idx}]")
        if node is root:
            break
        node = parent
    parts.reverse()
    return "/" + "/".join(parts)


def _explicit_normative_token(el: etree._Element) -> bool | None:
    """Return True/False if explicit marker, None if unknown."""
    anc: etree._Element | None = el
    while anc is not None:
        dn = (anc.get("data-normative") or "").lower()
        if dn in {"true", "1", "yes"}:
            return True
        if dn in {"false", "0", "no"}:
            return False
        tokens = _class_tokens(anc)
        if "non-normative" in tokens or "nonnormative" in tokens:
            return False
        if "informative" in tokens and "normative" not in tokens:
            return False
        if "normative" in tokens:
            return True
        if tokens & INFORMATIVE_CLASS_TOKENS:
            return False
        role = (anc.get("role") or "").lower()
        if role in {"note", "doc-example", "doc-note", "doc-tip"}:
            return False
        anc = anc.getparent()
    return None


def _is_informative_region(el: etree._Element) -> bool:
    # Quote ancestors are informative for keyword authority
    anc: etree._Element | None = el
    while anc is not None:
        if _local_name(anc.tag) in BLOCK_IGNORE_TAGS:
            return True
        if _local_name(anc.tag) in QUOTE_TAGS:
            return True
        anc = anc.getparent()
    marker = _explicit_normative_token(el)
    if marker is False:
        return True
    if marker is True:
        return False
    return False


def _is_explicitly_normative(el: etree._Element) -> bool:
    return _explicit_normative_token(el) is True


def extract_block_text_with_spans(
    el: etree._Element,
) -> tuple[str, tuple[tuple[int, int], ...]]:
    """Build normalized text with offset-accurate protected spans.

    Protection covers inline code and quotation descendants. Historical framing
    also protects double/single quoted spans for keyword matching.
    """
    # Stream of (char, protected)
    stream: list[tuple[str, bool]] = []

    def emit(s: str, *, protect: bool) -> None:
        for ch in s:
            stream.append((ch, protect))

    def walk(node: etree._Element, in_code: bool, in_quote: bool) -> None:
        nname = _local_name(node.tag) if isinstance(node.tag, str) else ""
        if nname in HEADING_TAGS:
            return
        if nname in BLOCK_IGNORE_TAGS:
            return
        now_code = in_code or nname in INLINE_CODE_TAGS
        now_quote = in_quote or nname in QUOTE_TAGS
        protect = now_code or now_quote
        if node.text:
            emit(node.text, protect=protect)
        for child in node:
            if isinstance(child.tag, str):
                walk(child, now_code, now_quote)
            if child.tail:
                # tail belongs to parent context
                emit(child.tail, protect=in_code or in_quote)

    root_name = _local_name(el.tag)
    if root_name in BLOCK_IGNORE_TAGS:
        return "", ()
    root_code = root_name in INLINE_CODE_TAGS
    root_quote = root_name in QUOTE_TAGS
    if el.text:
        emit(el.text, protect=root_code or root_quote)
    for child in el:
        if isinstance(child.tag, str):
            walk(child, root_code, root_quote)
        if child.tail:
            emit(child.tail, protect=False)

    # Collapse whitespace while tracking protection of non-space chars
    out_chars: list[str] = []
    out_prot: list[bool] = []
    prev_space = True  # strip leading
    for ch, prot in stream:
        if ch.isspace():
            if prev_space:
                continue
            out_chars.append(" ")
            out_prot.append(False)
            prev_space = True
        else:
            out_chars.append(ch)
            out_prot.append(prot)
            prev_space = False
    # strip trailing space
    while out_chars and out_chars[-1] == " ":
        out_chars.pop()
        out_prot.pop()

    text = "".join(out_chars)

    # Quoted spans remain protected for keyword authority; unquoted historical
    # authority is decided modal-locally in extract.historical (not whole-paragraph).
    for m in re.finditer(r'"([^"]+)"|\'([^\']+)\'', text):
        s, e = m.start(0), m.end(0)
        for i in range(s, min(e, len(out_prot))):
            out_prot[i] = True

    # Collapse protected flags into spans
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(out_prot)
    while i < n:
        if not out_prot[i]:
            i += 1
            continue
        j = i
        while j < n and out_prot[j]:
            j += 1
        spans.append((i, j))
        i = j
    return text, tuple(spans)


def normalize_html(raw: bytes) -> list[NormalizedBlock]:
    try:
        tree = html.fromstring(raw)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to parse HTML: {exc}") from exc

    if not isinstance(tree, etree._Element):
        raise ValueError("HTML root is not an element")

    body = tree.find(".//body")
    root = body if body is not None else tree

    section_stack: list[tuple[int, str]] = []
    blocks: list[NormalizedBlock] = []
    structural_index = 0

    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        name = _local_name(el.tag)

        if name in HEADING_TAGS:
            level = int(name[1])
            title = _heading_text(el)
            while section_stack and section_stack[-1][0] >= level:
                section_stack.pop()
            section_stack.append((level, title))
            continue

        if name not in {"p", "li", "dd", "td", "th", "div"}:
            continue

        if name == "div":
            block_child_tags = {
                "p",
                "li",
                "div",
                "ul",
                "ol",
                "table",
                "section",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
            }
            child_blocks = [
                c
                for c in el
                if isinstance(c.tag, str) and _local_name(c.tag) in block_child_tags
            ]
            if child_blocks:
                continue

        explicit_norm = _is_explicitly_normative(el)
        is_info = _is_informative_region(el) and not explicit_norm

        leaf_section = section_stack[-1][1] if section_stack else ""
        if (
            not explicit_norm
            and leaf_section
            and INFORMATIVE_SECTION_RE.search(leaf_section.strip())
        ):
            is_info = True

        text, protected = extract_block_text_with_spans(el)
        if not text or len(text) < 3:
            continue

        # Whole-block historical quotation without remaining unquoted modal text
        # stays extractable only for unprotected spans; keyword finder handles spans.

        section_path = " > ".join(t for _, t in section_stack) if section_stack else "(root)"
        xpath = _element_xpath(el, root)
        el_id = el.get("id")
        locator = f"xpath:{xpath}"
        if el_id:
            locator = f"id:{el_id}|{locator}"

        blocks.append(
            NormalizedBlock(
                text=text,
                normalized_text=normalize_whitespace(text),
                section_path=section_path,
                source_locator=locator,
                structural_index=structural_index,
                is_informative=is_info,
                xpath=xpath,
                protected_spans=protected,
            )
        )
        structural_index += 1

    return blocks
