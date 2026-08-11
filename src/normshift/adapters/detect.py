"""Exclusive structural document-family detection (offline and deterministic)."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree

from normshift.adapters.errors import AdapterDetectionError, AdapterParseError
from normshift.adapters.ingress import (
    is_rfc_xml_candidate,
    validate_complete_html,
    validate_rfc_xml,
)
from normshift.model.types import DocumentFamily

_RFC_HEADER_RE = re.compile(r"(?im)^\s*Request\s+for\s+Comments:\s*\d+\b")
_RFC_NUMBER_RE = re.compile(r"\bRFC\s*\d+\b", re.IGNORECASE)
_W3C_PUBLICATION_RE = re.compile(
    r"\bW3C\s+(?:Candidate|Proposed)?\s*(?:Recommendation|Working\s+Draft)\b",
    re.IGNORECASE,
)
_WHATWG_PUBLICATION_RE = re.compile(
    r"\b(?:WHATWG|Living\s+Standard|Review\s+Draft)\b",
    re.IGNORECASE,
)
_W3C_PUBLICATION_TYPES = frozenset(
    {
        "w3p:cr",
        "w3p:note",
        "w3p:pr",
        "w3p:rec",
        "w3p:wd",
    }
)
_W3C_BIBO_NAMESPACE = "http://purl.org/ontology/bibo/"
_W3C_PUBLICATION_NAMESPACE = "http://www.w3.org/2001/02pd/rec54#"
_RDFA_PREFIX_BINDING_RE = re.compile(r"(?:^|\s)([A-Za-z][\w.-]*):\s+(\S+)")
_W3C_TR_PATH_RE = re.compile(r"/TR/(?:[A-Za-z0-9][A-Za-z0-9._~-]*/?)+")
_WHATWG_RESOURCE_PATH_RE = re.compile(r"/(?:spec|review-draft)\.css")
_WHATWG_SPEC_PATH_RE = re.compile(r"/(?:[A-Za-z0-9][A-Za-z0-9._~-]*/?)*")
_WHATWG_SPEC_HOSTS = frozenset(
    {
        "compat.spec.whatwg.org",
        "console.spec.whatwg.org",
        "dom.spec.whatwg.org",
        "encoding.spec.whatwg.org",
        "fetch.spec.whatwg.org",
        "fullscreen.spec.whatwg.org",
        "html.spec.whatwg.org",
        "infra.spec.whatwg.org",
        "mimesniff.spec.whatwg.org",
        "notifications.spec.whatwg.org",
        "storage.spec.whatwg.org",
        "streams.spec.whatwg.org",
        "url.spec.whatwg.org",
        "websockets.spec.whatwg.org",
        "xhr.spec.whatwg.org",
    }
)


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower() if "}" in tag else tag.lower()


def _class_tokens(element: etree._Element) -> set[str]:
    return {token for token in str(element.get("class") or "").lower().split() if token}


def _text(element: etree._Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _rdfa_prefix_bindings(value: str) -> dict[str, str] | None:
    """Return unambiguous RDFa prefix bindings or fail closed on duplicates."""
    bindings: dict[str, str] = {}
    for prefix, namespace in _RDFA_PREFIX_BINDING_RE.findall(value):
        key = prefix.lower()
        if key in bindings:
            return None
        bindings[key] = namespace
    return bindings


def _markup_prefix(raw: bytes) -> bytes:
    prefix = raw.lstrip()
    if prefix.startswith(b"\xef\xbb\xbf"):
        prefix = prefix[3:].lstrip()
    return prefix.lower()


def _is_exact_https_url(
    value: str,
    *,
    hosts: frozenset[str],
    path_pattern: re.Pattern[str],
) -> bool:
    if (
        not value.isascii()
        or "%" in value
        or "\\" in value
        or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value)
    ):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    hostname = parsed.hostname or ""
    return (
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and port is None
        and parsed.netloc == hostname
        and hostname in hosts
        and not parsed.query
        and not parsed.fragment
        and path_pattern.fullmatch(parsed.path) is not None
        and "//" not in parsed.path
        and all(segment not in {".", ".."} for segment in parsed.path.split("/"))
    )


def _rfc_html_signature(tree: etree._Element, raw: bytes) -> bool:
    pre_nodes = tree.xpath("//pre")
    if _markup_prefix(raw).startswith(b"<pre") and pre_nodes:
        first_text = "\n".join(pre_nodes[0].itertext())
        heading_spans = pre_nodes[0].xpath(
            ".//span[contains(concat(' ', normalize-space(@class), ' '), ' h1 ')]"
        )
        if _RFC_HEADER_RE.search(first_text) and heading_spans:
            return True

    rfc_containers = [
        element
        for element in tree.iter()
        if isinstance(element.tag, str) and "rfc" in _class_tokens(element)
    ]
    if not rfc_containers:
        return False
    identity_text = " ".join(
        _text(element)
        for element in tree.xpath("//title|//h1")
        if isinstance(element, etree._Element)
    )
    return _RFC_NUMBER_RE.search(identity_text) is not None


def _w3c_html_signature(tree: etree._Element) -> bool:
    html_nodes = tree.xpath("//html")
    for element in html_nodes:
        typeof = {token.lower() for token in str(element.get("typeof") or "").split()}
        prefixes = _rdfa_prefix_bindings(str(element.get("prefix") or ""))
        if (
            prefixes is not None
            and "bibo:document" in typeof
            and bool(typeof & _W3C_PUBLICATION_TYPES)
            and prefixes.get("bibo") == _W3C_BIBO_NAMESPACE
            and prefixes.get("w3p") == _W3C_PUBLICATION_NAMESPACE
        ):
            return True

    head_nodes = [
        element
        for element in tree.iter()
        if isinstance(element.tag, str) and "head" in _class_tokens(element)
    ]
    canonical = [
        str(value)
        for value in tree.xpath(
            "//link[contains(concat(' ', normalize-space(@rel), ' '), ' canonical ')]/@href"
        )
    ]
    has_tr_canonical = any(
        _is_exact_https_url(
            value,
            hosts=frozenset({"www.w3.org"}),
            path_pattern=_W3C_TR_PATH_RE,
        )
        for value in canonical
    )
    return has_tr_canonical and any(_W3C_PUBLICATION_RE.search(_text(node)) for node in head_nodes)


def _whatwg_html_signature(tree: etree._Element) -> bool:
    stylesheets = [
        str(value)
        for value in tree.xpath(
            "//link[contains(concat(' ', normalize-space(@rel), ' '), ' stylesheet ')]/@href"
        )
    ]
    logo_links = [
        str(value)
        for value in tree.xpath(
            "//a[contains(concat(' ', normalize-space(@class), ' '), ' logo ')]/@href"
        )
    ]
    title_text = " ".join(_text(node) for node in tree.xpath("//title"))
    if (
        any(
            _is_exact_https_url(
                value,
                hosts=frozenset({"resources.whatwg.org"}),
                path_pattern=_WHATWG_RESOURCE_PATH_RE,
            )
            for value in stylesheets
        )
        and any(
            _is_exact_https_url(
                value,
                hosts=frozenset({"whatwg.org"}),
                path_pattern=re.compile(r"/"),
            )
            for value in logo_links
        )
        and _WHATWG_PUBLICATION_RE.search(title_text)
    ):
        return True

    canonical = [
        str(value)
        for value in tree.xpath(
            "//link[contains(concat(' ', normalize-space(@rel), ' '), ' canonical ')]/@href"
        )
    ]
    header_text = " ".join(_text(node) for node in tree.xpath("//header"))
    return (
        any(
            _is_exact_https_url(
                value,
                hosts=_WHATWG_SPEC_HOSTS,
                path_pattern=_WHATWG_SPEC_PATH_RE,
            )
            for value in canonical
        )
        and "whatwg" in header_text.lower()
        and _WHATWG_PUBLICATION_RE.search(title_text + " " + header_text) is not None
    )


def detect_family(path: Path, raw: bytes) -> DocumentFamily:
    """Return exactly one structurally evidenced family or fail on ambiguity."""
    adapter_id = "normshift.adapters.auto"
    if is_rfc_xml_candidate(raw):
        try:
            validate_rfc_xml(raw, path=path, adapter_id=adapter_id)
        except AdapterParseError as exc:
            raise AdapterDetectionError(str(exc), adapter_id=adapter_id) from exc
        return DocumentFamily.RFC

    try:
        tree = validate_complete_html(raw, path=path, adapter_id=adapter_id)
    except AdapterParseError as exc:
        raise AdapterDetectionError(str(exc), adapter_id=adapter_id) from exc

    matches: list[DocumentFamily] = []
    if _rfc_html_signature(tree, raw):
        matches.append(DocumentFamily.RFC)
    if _w3c_html_signature(tree):
        matches.append(DocumentFamily.W3C)
    if _whatwg_html_signature(tree):
        matches.append(DocumentFamily.WHATWG)

    if len(matches) > 1:
        values = ", ".join(family.value for family in matches)
        raise AdapterDetectionError(
            f"Ambiguous structural document family for {path}: {values}",
            adapter_id=adapter_id,
        )
    if matches:
        return matches[0]
    return DocumentFamily.GENERIC_HTML


def can_handle_family(path: Path, raw: bytes, family: DocumentFamily) -> bool:
    """Return whether strict, exclusive detection identifies ``family``."""
    try:
        return detect_family(path, raw) == family
    except (AdapterDetectionError, AdapterParseError):
        return False


def require_family(path: Path, raw: bytes, family: DocumentFamily, *, adapter_id: str) -> None:
    """Fail closed unless strict, exclusive structural detection equals ``family``."""
    try:
        detected = detect_family(path, raw)
    except (AdapterDetectionError, AdapterParseError) as exc:
        raise AdapterParseError(str(exc), adapter_id=adapter_id) from exc
    if detected != family:
        raise AdapterParseError(
            f"Source structural family {detected.value!r} does not match forced "
            f"{family.value!r} adapter: {path}",
            adapter_id=adapter_id,
        )
