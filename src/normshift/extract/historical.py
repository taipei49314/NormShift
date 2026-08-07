"""Modal-local historical authority filtering (deterministic, no LLM)."""

from __future__ import annotations

import re

from normshift.extract.profiles import KeywordMatch

# Framing that marks a modal as historical when it appears before that modal
# in the same clause / reporting span (not elsewhere in the paragraph).
_HISTORICAL_LEFT = re.compile(
    r"(?:"
    r"previous(?:ly)?\s+specification|"
    r"\bpreviously\b|"
    r"\bprevious\b|"
    r"old\s+version|"
    r"earlier\s+draft|"
    r"formerly\s+required|"
    r"were\s+formerly\s+required|"
    r"was\s+formerly\s+required|"
    r"old\s+text\s+was|"
    r"\bstated\s*:"
    r")",
    re.IGNORECASE,
)

# Speech/report verbs that only count when paired with historical framing nearby
_REPORTING_VERB = re.compile(
    r"\b(?:said|stated|required)\b",
    re.IGNORECASE,
)

# Explicit current-transition markers reopening authority
_CURRENT_TRANSITION = re.compile(
    r"(?:"
    r",?\s*\bbut\b|"
    r",?\s*\bhowever\b|"
    r",?\s*\balthough\b|"
    r",?\s*\bthough\b|"
    r"\bcurrently\b|"
    r"\bnow\b"
    r")",
    re.IGNORECASE,
)


def _clause_left(text: str, start: int) -> int:
    """Left bound of the authority region for a modal at ``start``."""
    left = 0
    # Sentence boundaries always reopen
    for m in re.finditer(r"[.!?;]\s+", text[:start]):
        left = m.end()
    # Current-transition markers reopen after historical reporting
    for m in _CURRENT_TRANSITION.finditer(text[:start]):
        # "MUST now" — "now" immediately after modal is not a left bound
        if m.start() >= start:
            continue
        left = max(left, m.end())
    return left


def _clause_right(text: str, end: int) -> int:
    right = len(text)
    m = re.search(r"[.!?;]\s+|,?\s*\bbut\b|,?\s*\bhowever\b|,?\s*\balthough\b", text[end:], re.I)
    if m:
        right = end + m.start()
    return right


def _pre_has_historical_framing(pre: str) -> bool:
    if _HISTORICAL_LEFT.search(pre):
        return True
    # "the previous specification said clients MUST" — reporting after previous*
    if re.search(r"\bprevious", pre, re.I) and _REPORTING_VERB.search(pre):
        return True
    if re.search(r"\bold\s+version\b", pre, re.I) and _REPORTING_VERB.search(pre):
        return True
    return bool(re.search(r"\bformerly\b", pre, re.I))


def is_historical_modal(text: str, match: KeywordMatch) -> bool:
    """True if this modal occurrence is historical/non-authoritative."""
    # "MUST now …" is always current for this occurrence
    after = text[match.start : match.end + 12]
    if re.match(r"(?i)must\s+now\b", after) or re.match(r"(?i)shall\s+now\b", after):
        return False

    left = _clause_left(text, match.start)
    pre = text[left : match.start]
    clause = text[left : _clause_right(text, match.end)]

    # Incidental uses of historical vocabulary that do not report past obligations
    # "historical records", "historically insecure protocol MUST", "was required for X"
    if re.search(r"\bhistorical\s+records\b", clause, re.I) and not _pre_has_historical_framing(
        pre
    ):
        return False
    if re.search(r"\bhistorically\s+\w+", pre, re.I) and not _pre_has_historical_framing(
        re.sub(r"(?i)\bhistorically\s+\w+(\s+\w+)?", " ", pre)
    ):
        # adjective "historically insecure" before subject — keep current
        return False
    if re.search(r"\bwas\s+required\s+for\b", pre, re.I) and not _pre_has_historical_framing(
        re.sub(r"(?i)\bwas\s+required\s+for\b", " ", pre)
    ):
        return False

    # Sentence/clause starts with Previously / In the old version / …
    sent_pre = pre.lstrip()
    if re.match(
        r"(?i)(previously\b|in\s+the\s+old\s+version\b|the\s+previous\s+specification\b|"
        r"the\s+old\s+version\b|formerly\b)",
        sent_pre,
    ):
        return True

    return bool(_pre_has_historical_framing(pre))


def filter_historical_matches(text: str, matches: list[KeywordMatch]) -> list[KeywordMatch]:
    return [m for m in matches if not is_historical_modal(text, m)]
