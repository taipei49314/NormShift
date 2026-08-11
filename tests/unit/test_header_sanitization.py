"""Focused tests for the deterministic M1 header-evidence sanitizer."""

from __future__ import annotations

import pytest

from normshift.corpus.header_sanitization import (
    HeaderSanitizationError,
    sanitize_header_bytes,
    validate_sanitized_header_bytes,
)


def test_sanitizer_keeps_only_allowlisted_fields_and_drops_continuations() -> None:
    sensitive_field = b"Set-" + b"Cookie"
    authentication_field = b"Author" + b"ization"
    raw = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b" folded-private-metadata-after-allowlisted-field\r\n"
        b'ETag: "frozen"\r\n'
        b"Link: <https://example.test/frozen>; rel=canonical\r\n"
        + sensitive_field
        + b": redacted-value\r\n"
        + authentication_field
        + b": redacted-value\r\n"
        + b"X-Unrecognized: private-metadata\r\n"
        + b" folded-private-metadata\r\n"
        + b"Last-Modified: Tue, 11 Aug 2026 00:00:00 GMT\r\n\r\n"
    )

    sanitized, removed, retained = sanitize_header_bytes(
        raw,
        source_ref="synthetic.headers.txt",
    )

    assert sanitized == (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b'ETag: "frozen"\r\n'
        b"Last-Modified: Tue, 11 Aug 2026 00:00:00 GMT\r\n\r\n"
    )
    assert removed == ["authorization", "link", "set-cookie", "x-unrecognized"]
    assert retained == ["content-type", "etag", "last-modified"]
    assert b"redacted-value" not in sanitized
    assert b"private-metadata" not in sanitized


def test_sanitizer_rejects_sensitive_marker_in_allowlisted_value() -> None:
    marker = b"gh" + b"p_" + b"synthetic"
    raw = b'HTTP/1.1 200 OK\r\nETag: "' + marker + b'"\r\n\r\n'

    with pytest.raises(HeaderSanitizationError, match="sensitive-value marker"):
        sanitize_header_bytes(raw, source_ref="synthetic.headers.txt")


def test_sanitized_header_validator_rejects_every_continuation() -> None:
    raw = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n folded-metadata\r\n\r\n"

    with pytest.raises(HeaderSanitizationError, match="continuation"):
        validate_sanitized_header_bytes(raw, source_ref="synthetic.headers.txt")


@pytest.mark.parametrize(
    "raw",
    [
        b'HTTP/1.1 200 OK\r\nETag: "' + (b"x" * (2 * 1024 * 1024)) + b'"\r\n\r\n',
        b"HTTP/1.1 200 OK\r\nContent-Type: text/" + (b"x" * 2048) + b"\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nContent-Length: " + (b"9" * 5000) + b"\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nContent-Type:  text/plain\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nContent-Type:text/plain\r\n\r\n",
    ],
    ids=[
        "oversized-total-etag",
        "oversized-content-type",
        "oversized-content-length",
        "extra-leading-space",
        "missing-required-space",
    ],
)
def test_sanitized_header_validator_rejects_unbounded_or_noncanonical_values(
    raw: bytes,
) -> None:
    with pytest.raises(HeaderSanitizationError):
        validate_sanitized_header_bytes(raw, source_ref="synthetic.headers.txt")


@pytest.mark.parametrize(
    "raw",
    [
        b"HTTP/1.1 200 OK\nContent-Type: text/plain\n\n",
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n",
        b"HTTP/1.1 200 OK\r\nInvalid line\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nBad_Field: value\r\n\r\n",
        b"HTTP/1.1 201 Arbitrary Status Text\r\nContent-Type: text/plain\r\n\r\n",
    ],
)
def test_sanitizer_rejects_noncanonical_http_header_framing(raw: bytes) -> None:
    with pytest.raises(HeaderSanitizationError):
        sanitize_header_bytes(raw, source_ref="synthetic.headers.txt")
