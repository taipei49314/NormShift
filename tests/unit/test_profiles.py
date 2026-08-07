"""Unit tests for keyword profiles and vetoes."""

from __future__ import annotations

from normshift.extract.profiles import find_keyword_matches
from normshift.model.types import Modality, ProfileName


def test_mustard_does_not_match_must() -> None:
    text = "The mustard configuration key is popular among mustard lovers."
    assert find_keyword_matches(text, ProfileName.RFC2119) == []
    assert find_keyword_matches(text, ProfileName.WHATWG) == []


def test_not_required_to_veto() -> None:
    text = "A legacy peer is not required to support compression."
    assert find_keyword_matches(text, ProfileName.RFC2119) == []
    assert find_keyword_matches(text, ProfileName.WHATWG) == []


def test_rfc2119_uppercase_must() -> None:
    text = "Implementers MUST send an acknowledgment."
    matches = find_keyword_matches(text, ProfileName.RFC2119)
    assert len(matches) == 1
    assert matches[0].modality == Modality.MUST


def test_rfc2119_ignores_lowercase_must() -> None:
    text = "Implementers must send an acknowledgment."
    assert find_keyword_matches(text, ProfileName.RFC2119) == []


def test_whatwg_lowercase_must() -> None:
    text = "User agents must close idle sockets."
    matches = find_keyword_matches(text, ProfileName.WHATWG)
    assert len(matches) == 1
    assert matches[0].modality == Modality.MUST


def test_must_not() -> None:
    text = "Clients MUST NOT log secrets."
    matches = find_keyword_matches(text, ProfileName.RFC2119)
    assert len(matches) == 1
    assert matches[0].modality == Modality.MUST_NOT
