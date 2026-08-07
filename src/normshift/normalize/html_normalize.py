"""Structural normalization of local HTML documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from lxml import etree, html

IGNORE_TAGS = frozenset(
    {
        "script",
        "style",
        "noscript",
        "pre",
        "code",
        "samp",
        "kbd",
        "var",
        "textarea",
        "svg",
        "math",
    }
)

INFORMATIVE_CLASS_RE = re.compile(
    r"\b(example|note|informative|non-normative|nonnormative|illustration|"
    r"sample|issue|warning|advisement|annotation|ednote|editor-note|"
    r"impl|implementation-note|prac|practice|xxx|todo)\b",
    re.IGNORECASE,
)

# Section titles that are typically informative / non-implementer normative.
INFORMATIVE_SECTION_RE = re.compile(
    r"^(appendix\b|acknowledg|security considerations$|iana considerations$|"
    r"references$|normative references$|informative references$|"
    r"change log$|changelog$|revision history$)",
    re.IGNORECASE,
)

HEADING_TAGS = frozenset({f"h{i}" for i in range(1, 7)})
WS_RE = re.compile(r"\s+")


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
        if an in IGNORE_TAGS:
            return True
        if INFORMATIVE_CLASS_RE.search(_class_attr(anc)):
            return True
        if (anc.get("data-normative") or "").lower() in {"false", "0", "no"}:
            return True
        # W3C/ReSpec often uses class="informative" on section
        classes = _class_attr(anc)
        if re.search(r"\binformative\b", classes, re.I) and not re.search(
            r"\bnormative\b", classes, re.I
        ):
            return True
        role = (anc.get("role") or "").lower()
        if role in {"note", "doc-example", "doc-note", "doc-tip"}:
            return True
        anc = anc.getparent()
    return False


def extract_block_text(el: etree._Element) -> str:
    """Collect visible text, omitting ignored subtrees and nested headings."""
    parts: list[str] = []

    def walk(node: etree._Element, ignored: bool) -> None:
        nname = _local_name(node.tag) if isinstance(node.tag, str) else ""
        if nname in HEADING_TAGS:
            return
        now_ignored = ignored or nname in IGNORE_TAGS
        if node.text and not now_ignored:
            parts.append(node.text)
        for child in node:
            if isinstance(child.tag, str):
                walk(child, now_ignored)
            if child.tail and not ignored:
                parts.append(child.tail)

    root_name = _local_name(el.tag)
    root_ignored = root_name in IGNORE_TAGS
    if el.text and not root_ignored:
        parts.append(el.text)
    for child in el:
        if isinstance(child.tag, str):
            walk(child, root_ignored)
        if child.tail and not root_ignored:
            parts.append(child.tail)
    return normalize_whitespace("".join(parts))


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

        # Skip blocks under informative-titled leaf sections.
        leaf_section = section_stack[-1][1] if section_stack else ""
        if leaf_section and INFORMATIVE_SECTION_RE.search(leaf_section.strip()):
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

        is_info = _is_informative_region(el)
        text = extract_block_text(el)
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
            )
        )
        structural_index += 1

    return blocks
