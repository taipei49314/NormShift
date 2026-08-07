"""Family-aware stripping of navigation, boilerplate, and non-content chrome."""

from __future__ import annotations

from lxml import etree, html

from normshift.model.types import DocumentFamily

HEADING_TAGS = frozenset({f"h{i}" for i in range(1, 7)})


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[-1].lower()
    return tag.lower()


def _remove_matches(tree: etree._Element, xpath: str) -> None:
    for el in list(tree.xpath(xpath)):
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)


_COMMON_STRIP_XPATHS = [
    "//script",
    "//style",
    "//noscript",
    "//nav",
    "//footer",
    "//*[@id='toc' or @id='table-of-contents' or @id='contents']",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' toc ')]",
    "//*[contains(@class,'sidebar')]",
    "//*[contains(@class,'breadcrumbs')]",
]

_RFC_STRIP = [
    "//*[contains(@class,'noprint')]",
]

_W3C_STRIP = [
    "//*[@id='toc' or @id='toc-nav']",
    "//p[@role='navigation']",
    "//*[contains(@class,'copyright')]",
]

_WHATWG_STRIP = [
    "//*[@id='toc' or @id='contents']",
    "//header",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' status ')]",
]

_BOILERPLATE_TITLES = frozenset(
    {
        "status of this memo",
        "copyright notice",
        "table of contents",
        "abstract",
        "authors' addresses",
        "status of this document",
        "document conventions",
    }
)


def _heading_level(el: etree._Element) -> int:
    name = _local_name(el.tag)
    if name in HEADING_TAGS:
        return int(name[1])
    return 7


def _remove_section_from_heading(heading: etree._Element) -> None:
    """Remove heading and following siblings until next heading of same/higher level."""
    parent = heading.getparent()
    if parent is None:
        return
    level = _heading_level(heading)
    # Collect nodes to remove: heading + following siblings
    remove: list[etree._Element] = [heading]
    sib = heading.getnext()
    while sib is not None:
        if (
            isinstance(sib.tag, str)
            and _local_name(sib.tag) in HEADING_TAGS
            and _heading_level(sib) <= level
        ):
            break
        remove.append(sib)
        sib = sib.getnext()
    for node in remove:
        p = node.getparent()
        if p is not None:
            p.remove(node)


def strip_chrome(raw_html: bytes, family: DocumentFamily) -> bytes:
    """Remove navigation/boilerplate chrome; return serialized HTML bytes."""
    try:
        tree = html.fromstring(raw_html)
    except Exception:
        return raw_html

    xpaths = list(_COMMON_STRIP_XPATHS)
    if family == DocumentFamily.RFC:
        xpaths.extend(_RFC_STRIP)
    elif family == DocumentFamily.W3C:
        xpaths.extend(_W3C_STRIP)
    elif family == DocumentFamily.WHATWG:
        xpaths.extend(_WHATWG_STRIP)

    for xp in xpaths:
        try:
            _remove_matches(tree, xp)
        except Exception:
            continue

    for heading in list(tree.xpath("//h1|//h2|//h3|//h4|//h5|//h6")):
        text = " ".join(heading.itertext()).strip().lower()
        text = " ".join(text.split())
        if text in _BOILERPLATE_TITLES or text.startswith("status of this"):
            _remove_section_from_heading(heading)

    return html.tostring(tree, encoding="utf-8", method="html")
