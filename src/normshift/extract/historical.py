"""Clause-local historical authority filtering (deterministic, no LLM).

Bare words such as previous/prior/earlier alone do NOT suppress a modal.
Historical suppression requires a specification/version reporting frame
associated with the modal's bounded clause.
"""

from __future__ import annotations

import re

from normshift.extract.profiles import KeywordMatch

# Spec/version/draft object that can host historical reporting
_SPEC_OBJECT = (
    r"(?:specification|standard|version|draft|text|requirement|spec)"
)

# Historical modifier + specification-class object (reporting frame stem)
_HIST_SPEC_FRAME = re.compile(
    rf"\b(?P<mod>previous(?:ly)?|prior|earlier|old|former)\s+{_SPEC_OBJECT}\b",
    re.IGNORECASE,
)

# Reporting / quote framing that attributes a modal to the historical object
_REPORTING = re.compile(
    r"\b(?:said|stated|required|quoted|wrote|read|provided)\b|:\s*[\"']|\bstated\s*:",
    re.IGNORECASE,
)

# Contrast that *reopens* current authority (unlike the previous specification, …)
_CONTRAST = re.compile(
    rf"\b(?:unlike|as\s+opposed\s+to|instead\s+of|rather\s+than)\b"
    rf".{{0,80}}\b(?:previous|prior|earlier|old|former)\s+{_SPEC_OBJECT}\b",
    re.IGNORECASE,
)

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

_FORMERLY_REQUIRED = re.compile(
    r"\b(?:were|was)\s+formerly\s+required\b|\bformerly\s+required\b",
    re.IGNORECASE,
)


def clause_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """Return [left, right) bounds for the authority region of a modal."""
    left = 0
    for m in re.finditer(r"[.!?;]\s+", text[:start]):
        left = m.end()
    for m in _CURRENT_TRANSITION.finditer(text[:start]):
        if m.start() >= start:
            continue
        left = max(left, m.end())
    right = len(text)
    right_m = re.search(
        r"[.!?;]\s+|,?\s*\bbut\b|,?\s*\bhowever\b|,?\s*\balthough\b",
        text[end:],
        re.I,
    )
    if right_m is not None:
        right = end + right_m.start()
    return left, right


def bound_current_clause(text: str, match: KeywordMatch) -> tuple[str, KeywordMatch]:
    """Slice the current authority clause and remap match offsets into it."""
    left, right = clause_bounds(text, match.start, match.end)
    clause = text[left:right]
    local = KeywordMatch(
        modality=match.modality,
        polarity=match.polarity,
        matched_text=match.matched_text,
        start=match.start - left,
        end=match.end - left,
    )
    return clause, local


def is_historical_modal(text: str, match: KeywordMatch) -> bool:
    """True if this modal occurrence is historical/non-authoritative."""
    after = text[match.start : match.end + 12]
    if re.match(r"(?i)must\s+now\b", after) or re.match(r"(?i)shall\s+now\b", after):
        return False

    left, right = clause_bounds(text, match.start, match.end)
    pre = text[left : match.start]
    clause = text[left:right]

    # Contrast frames: "Unlike the previous specification, clients MUST …"
    if _CONTRAST.search(pre) or (
        re.search(r"(?i)\bunlike\b", pre)
        and _HIST_SPEC_FRAME.search(pre)
    ):
        return False

    # Sentence adverb "Previously," (comma required) — not "Previously assigned …"
    sent_pre = pre.lstrip()
    if re.match(r"(?i)previously\s*,", sent_pre):
        return True

    # Formerly-required reporting without a current modal subject
    if (
        _FORMERLY_REQUIRED.search(clause)
        and not re.search(r"(?i)\b(must|shall|should|may|recommended)\b", pre)
        and match.start >= left
    ):
        # "Clients were formerly required to retry" — no current modal kept
        return True

    # Historical only with modifier + specification-class object + reporting
    hist = _HIST_SPEC_FRAME.search(pre)
    if hist is not None:
        # Between frame and modal: need reporting/quote, or frame ends with said
        between = pre[hist.end() :]
        before_and_frame = pre[: hist.end()]
        if _REPORTING.search(between) or _REPORTING.search(before_and_frame) or _REPORTING.search(
            pre
        ):
            return True
        # "In the old version, clients MUST" — comma report without verb
        if re.search(r"(?i)\bin\s+the\s+(old|previous|prior|earlier)\s+", pre):
            return True

    # "the previous specification said" style already covered; do NOT treat
    # bare "previous value/state/section/implementations" as historical.
    return False


def filter_historical_matches(text: str, matches: list[KeywordMatch]) -> list[KeywordMatch]:
    return [m for m in matches if not is_historical_modal(text, m)]
