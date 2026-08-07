"""Structural normalization of local HTML documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lxml import etree, html

# Tags whose *entire* content is non-extractable for keyword hits AND evidence.
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

# Inline code: preserve text in evidence, but protect from keyword matches.
INLINE_CODE_TAGS = frozenset({"code", "var"})

INFORMATIVE_CLASS_RE = re.compile(
    r"\b(example|note|informative|non-normative|nonnormative|illustration|"
    r"sample|issue|warning|advisement|annotation|ednote|editor-note|"
    r"impl|implementation-note|prac|practice|xxx|todo)\b",
    re.IGNORECASE,
)

# Only clearly non-normative section titles (not Security Considerations / Appendix).
INFORMATIVE_SECTION_RE = re.compile(
    r"^(acknowledg|"
    r"references$|normative references$|informative references$|"
    r"change log$|changelog$|revision history$|"
    r"table of contents$|authors'? addresses$)$",
    re.IGNORECASE,
)

HEADING_TAGS = frozenset({f"h{i}" for i in range(1, 7)})
WS_RE = re.compile(r"\s+")
QUOTE_TAGS = frozenset({"blockquote", "q"})


@dataclass(frozen=True)
class NormalizedBlock:
    """A normalized text block with structural context."""

    text: str
    normalized_text: str
    section_path: str
    source_locator: str
    structural_index: int
    is_informative: bool
    xpath: str
    # Ranges in `text` that are protected from keyword matching (inline code).
    protected_spans: tuple[tuple[int, int], ...] = ()


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[-1].lower()
    return tag.lower()


def _class_attr(el: etree._Element) -> str:
    return str(el.get("class") or "")


def normalize_whitespace(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def editorial_normalize(text: str) -> str:
    """Normalize for editorial comparison (whitespace/punct-insensitive core)."""
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


def _is_informative_region(el: etree._Element) -> bool:
    anc: etree._Element | None = el
    while anc is not None:
        an = _local_name(anc.tag)
        if an in BLOCK_IGNORE_TAGS:
            return True
        if an in QUOTE_TAGS:
            return True
        if INFORMATIVE_CLASS_RE.search(_class_attr(anc)):
            return True
        # Explicit markers take precedence
        dn = (anc.get("data-normative") or "").lower()
        if dn in {"false", "0", "no"}:
            return True
        if dn in {"true", "1", "yes"}:
            return False
        classes = _class_attr(anc)
        if re.search(r"\binformative\b", classes, re.I) and not re.search(
            r"\bnormative\b", classes, re.I
        ):
            return True
        if re.search(r"\bnormative\b", classes, re.I):
            return False
        role = (anc.get("role") or "").lower()
        if role in {"note", "doc-example", "doc-note", "doc-tip"}:
            return True
        anc = anc.getparent()
    return False


def _is_explicitly_normative(el: etree._Element) -> bool:
    anc: etree._Element | None = el
    while anc is not None:
        dn = (anc.get("data-normative") or "").lower()
        if dn in {"true", "1", "yes"}:
            return True
        if re.search(r"\bnormative\b", _class_attr(anc), re.I):
            return True
        anc = anc.getparent()
    return False


def extract_block_text_with_spans(
    el: etree._Element,
) -> tuple[str, tuple[tuple[int, int], ...]]:
    """Collect visible text; preserve inline code; omit block-ignore subtrees.

    Returns (text, protected_spans) where protected_spans are code ranges in text.
    """
    parts: list[str] = []
    protected: list[tuple[int, int]] = []

    def emit(s: str, *, protect: bool) -> None:
        if not s:
            return
        start = sum(len(p) for p in parts)
        parts.append(s)
        if protect:
            protected.append((start, start + len(s)))

    def walk(node: etree._Element, ignored: bool, in_code: bool) -> None:
        nname = _local_name(node.tag) if isinstance(node.tag, str) else ""
        if nname in HEADING_TAGS:
            return
        if nname in BLOCK_IGNORE_TAGS:
            return
        now_code = in_code or nname in INLINE_CODE_TAGS
        now_ignored = ignored  # only block ignore skips entirely
        if node.text and not now_ignored:
            emit(node.text, protect=now_code)
        for child in node:
            if isinstance(child.tag, str):
                walk(child, now_ignored, now_code)
            if child.tail and not ignored:
                # Tail belongs to parent context, not child's code protection
                emit(child.tail, protect=in_code)

    root_name = _local_name(el.tag)
    if root_name in BLOCK_IGNORE_TAGS:
        return "", ()
    root_code = root_name in INLINE_CODE_TAGS
    if el.text:
        emit(el.text, protect=root_code)
    for child in el:
        if isinstance(child.tag, str):
            walk(child, False, root_code)
        if child.tail:
            emit(child.tail, protect=False)

    raw = "".join(parts)
    # Build mapping from raw offsets to normalized text offsets while collapsing WS.
    # Simpler approach: normalize full string, re-find protected content substrings.
    text = normalize_whitespace(raw)
    # Map protected spans by finding protected substrings after normalize
    prot_out: list[tuple[int, int]] = []
    for s, e in protected:
        frag = normalize_whitespace(raw[s:e])
        if not frag:
            continue
        # Find non-overlapping occurrences
        start = 0
        while True:
            idx = text.find(frag, start)
            if idx < 0:
                break
            span = (idx, idx + len(frag))
            if not any(a <= span[0] and span[1] <= b for a, b in prot_out):
                prot_out.append(span)
                break
            start = idx + 1
    return text, tuple(prot_out)


def normalize_html(raw: bytes) -> list[NormalizedBlock]:
    """Parse HTML and emit ordered normalized blocks for extraction."""
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

        # Soft section title hints only when not explicitly normative
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
