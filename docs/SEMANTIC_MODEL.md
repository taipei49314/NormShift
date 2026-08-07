# Semantic Model (M0)

## Requirement

A requirement is a normative clause with:

- modality: MUST | MUST_NOT | SHOULD | SHOULD_NOT | MAY
- polarity: AFFIRMATIVE | NEGATIVE
- optional actor / action / condition / exception (deterministic heuristics only)
- source locator and section path
- fingerprint over normalized semantic fields

## Change classifications

| Class | Meaning |
|-------|---------|
| UNCHANGED | Same obligation, same section (normalized) |
| MOVED | Same obligation, different section |
| EDITORIAL | Formatting/whitespace/punctuation only |
| ADDED | New requirement with no prior alignment |
| REMOVED | Prior requirement with no successor |
| STRENGTHENED | Stronger modality (e.g. SHOULD→MUST) |
| WEAKENED | Weaker modality (e.g. MUST→SHOULD/MAY) |
| POLARITY_FLIP | Affirmative↔negative pair (e.g. MUST→MUST NOT) |
| CONDITION_ADDED / REMOVED | Guard condition introduced or dropped |
| EXCEPTION_ADDED / REMOVED | Exception clause introduced or dropped |
| AMBIGUOUS | Insufficient evidence for a substantive class |

AMBIGUOUS is a valid and necessary result. M0 does not force a substantive
label when evidence is thin.

## Alignment signals

Combined score components exposed in the report:

- text similarity
- modality match
- section similarity
- token similarity
- actor/action similarity
- structural proximity

## Profiles

- **rfc2119**: uppercase-oriented RFC 2119 keywords (MUST, SHOULD, MAY, …)
- **whatwg**: case-insensitive keywords (must, should, may, …)
