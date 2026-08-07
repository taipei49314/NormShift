"""Deterministic actor/action/condition/exception extraction heuristics."""

from __future__ import annotations

import re

from normshift.extract.profiles import KeywordMatch
from normshift.normalize.html_normalize import normalize_whitespace

# Exception markers
_EXCEPTION_RE = re.compile(
    r"\b(?P<ex>(?:unless|except\s+when|except\s+if|except)\b[^.;]*)",
    re.IGNORECASE,
)

# Condition markers
_CONDITION_RE = re.compile(
    r"\b(?P<cond>(?:when|if|while|whenever|where)\b[^.;]*)",
    re.IGNORECASE,
)

_ACTOR_RE = re.compile(
    r"\b(?P<actor>"
    r"implementers?|implementations?|user\s+agents?|servers?|clients?|"
    r"authors?|UAs?|browsers?|applications?|systems?|senders?|receivers?"
    r")\b",
    re.IGNORECASE,
)


def extract_roles(
    text: str, keyword: KeywordMatch
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return (actor, action, condition, exception) when deterministically extractable."""
    exception = _first_group(_EXCEPTION_RE, text, "ex")
    condition = _first_group(_CONDITION_RE, text, "cond")

    # Avoid treating exception clause as condition when both match same region.
    if exception and condition and condition.lower() in exception.lower():
        condition = None

    actor_m = _ACTOR_RE.search(text)
    actor = normalize_whitespace(actor_m.group("actor")) if actor_m else None

    # Action: text after keyword match, stripped of condition/exception tails.
    after = text[keyword.end :].strip()
    after = _EXCEPTION_RE.sub("", after)
    after = _CONDITION_RE.sub("", after)
    after = re.sub(r"^[,\s]+", "", after)
    after = re.sub(r"[.\s]+$", "", after)
    action = normalize_whitespace(after) if after else None
    if action and len(action) > 200:
        action = action[:200].rstrip()

    return actor, action, condition, exception


def _first_group(cre: re.Pattern[str], text: str, name: str) -> str | None:
    m = cre.search(text)
    if not m:
        return None
    val = normalize_whitespace(m.group(name))
    return val or None
