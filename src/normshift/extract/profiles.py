"""Normative keyword profiles (RFC 2119 and WHATWG-style)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from normshift.model.types import Modality, Polarity, ProfileName


@dataclass(frozen=True)
class KeywordMatch:
    modality: Modality
    polarity: Polarity
    matched_text: str
    start: int
    end: int


# Longer / more specific patterns first to avoid partial conflicts.
# Each pattern uses token boundaries so "mustard" does not match "must".
_RFC2119_PATTERNS: list[tuple[re.Pattern[str], Modality, Polarity]] = [
    (
        re.compile(r"\bMUST\s+NOT\b"),
        Modality.MUST_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bSHALL\s+NOT\b"),
        Modality.MUST_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bSHOULD\s+NOT\b"),
        Modality.SHOULD_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bNOT\s+RECOMMENDED\b"),
        Modality.SHOULD_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bMUST\b"),
        Modality.MUST,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bSHALL\b"),
        Modality.MUST,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bREQUIRED\b"),
        Modality.MUST,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bSHOULD\b"),
        Modality.SHOULD,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bRECOMMENDED\b"),
        Modality.SHOULD,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bMAY\b"),
        Modality.MAY,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bOPTIONAL\b"),
        Modality.MAY,
        Polarity.AFFIRMATIVE,
    ),
]

_WHATWG_PATTERNS: list[tuple[re.Pattern[str], Modality, Polarity]] = [
    (
        re.compile(r"\bmust\s+not\b", re.IGNORECASE),
        Modality.MUST_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bshall\s+not\b", re.IGNORECASE),
        Modality.MUST_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bshould\s+not\b", re.IGNORECASE),
        Modality.SHOULD_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bnot\s+recommended\b", re.IGNORECASE),
        Modality.SHOULD_NOT,
        Polarity.NEGATIVE,
    ),
    (
        re.compile(r"\bmust\b", re.IGNORECASE),
        Modality.MUST,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bshall\b", re.IGNORECASE),
        Modality.MUST,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\brequired\b", re.IGNORECASE),
        Modality.MUST,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bshould\b", re.IGNORECASE),
        Modality.SHOULD,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\brecommended\b", re.IGNORECASE),
        Modality.SHOULD,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\bmay\b", re.IGNORECASE),
        Modality.MAY,
        Polarity.AFFIRMATIVE,
    ),
    (
        re.compile(r"\boptional\b", re.IGNORECASE),
        Modality.MAY,
        Polarity.AFFIRMATIVE,
    ),
]

# Phrases that look normative but must NOT produce a keyword hit.
# Applied as veto windows over the matched span.
_NEGATION_VETO_RES = [
    re.compile(r"\bis\s+not\s+required\s+to\b", re.IGNORECASE),
    re.compile(r"\bare\s+not\s+required\s+to\b", re.IGNORECASE),
    re.compile(r"\bnot\s+required\s+to\b", re.IGNORECASE),
    re.compile(r"\bneed\s+not\b", re.IGNORECASE),
    re.compile(r"\bis\s+not\s+required\b", re.IGNORECASE),
    re.compile(r"\bno\s+requirement\b", re.IGNORECASE),
]


def patterns_for(profile: ProfileName) -> list[tuple[re.Pattern[str], Modality, Polarity]]:
    if profile == ProfileName.RFC2119:
        return _RFC2119_PATTERNS
    if profile == ProfileName.WHATWG:
        return _WHATWG_PATTERNS
    raise ValueError(f"Unknown profile: {profile}")


def find_keyword_matches(text: str, profile: ProfileName) -> list[KeywordMatch]:
    """Find normative keyword matches with token boundaries and negation vetoes."""
    patterns = patterns_for(profile)
    veto_spans = _veto_spans(text)

    matches: list[KeywordMatch] = []
    occupied: list[tuple[int, int]] = []

    for cre, modality, polarity in patterns:
        for m in cre.finditer(text):
            start, end = m.start(), m.end()
            if _overlaps_any(start, end, veto_spans):
                continue
            if _overlaps_any(start, end, occupied):
                continue
            # Extra guard: "mustard" / substring issues already handled by \b,
            # but reject if match is inside a longer alphabetic token (safety).
            if not _is_token_bounded(text, start, end):
                continue
            matches.append(
                KeywordMatch(
                    modality=modality,
                    polarity=polarity,
                    matched_text=m.group(0),
                    start=start,
                    end=end,
                )
            )
            occupied.append((start, end))

    matches.sort(key=lambda km: km.start)
    return matches


def _veto_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for cre in _NEGATION_VETO_RES:
        for m in cre.finditer(text):
            spans.append((m.start(), m.end()))
    return spans


def _overlaps_any(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < e and end > s for s, e in spans)


def _is_token_bounded(text: str, start: int, end: int) -> bool:
    left_ok = start == 0 or not (text[start - 1].isalnum() or text[start - 1] == "_")
    right_ok = end >= len(text) or not (text[end].isalnum() or text[end] == "_")
    return left_ok and right_ok
