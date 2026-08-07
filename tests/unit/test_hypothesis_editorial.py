"""Property-style checks for editorial normalization stability."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from normshift.normalize.html_normalize import editorial_normalize, normalize_whitespace

_ALPH = "abcdefghijklmnopqrstuvwxyzMUST SHOULD MAY  \t\n.,;:"


@given(st.text(alphabet=_ALPH, min_size=0, max_size=80))
def test_editorial_normalize_idempotent(s: str) -> None:
    once = editorial_normalize(s)
    twice = editorial_normalize(once)
    assert once == twice


@given(st.text(min_size=0, max_size=40))
def test_whitespace_normalize_idempotent(s: str) -> None:
    once = normalize_whitespace(s)
    assert normalize_whitespace(once) == once
