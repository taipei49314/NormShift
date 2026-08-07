# M0 Trust-Chain Repair Evidence

**Status (implementer, not Audit Authority):** `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`  
**Date:** 2026-08-07  
**External audit input:** `docs/EXTERNAL_AUDIT.md` (package NormShift-20260807-105717)

## Final commit

Recorded at closeout tip (must equal pack tip). See `git rev-parse HEAD` after final commit.

## Environment

| Item | Value |
|------|--------|
| Python (uv) | 3.12.x |
| Platform | Windows |
| `uv.lock` SHA-256 | `40424b150fedf7b9d30be4273f6abb7e5db1f636dfd54faffc24676383418978` |

## Commands and exit codes

```text
uv run ruff check .                                          # 0
uv run mypy src                                              # 0
uv run pytest -q                                             # 0 — 71 passed
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
                                                             # 0 — 17/17
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl \
  --out evidence/m0-repair/metrics.json                      # 0 — 15/15
uv run normshift diff fixtures/synthetic/spec-v1.html \
  fixtures/synthetic/spec-v2.html --profile rfc2119 \
  --json evidence/m0-repair/report.json \
  --markdown evidence/m0-repair/report.md                    # 0
uv run normshift verify evidence/m0-repair/report.json --source-root .
                                                             # 0
```

## Artifact hashes

| File | SHA-256 |
|------|---------|
| `evidence/m0-repair/report.json` | `7b6b949fbb721f5894167a007534f8e81b673e7fc83e66983b1776a1b64c77d1` |
| `evidence/m0-repair/report.md` | `abf7efb1c45912d696c36b1ae4cb84a6b4d6d4da9dc46841c6395b9825257af2` |
| `evidence/m0-repair/metrics.json` | `fb76642f9178b3bfb6e2bd2bb85ded0b75d18aea003f50af461d51314e7a8808` |
| Report integrity content_sha256 | `1a1fd45a8c74455c3f242c1731b7d3f99c58f90233edaaa6127795b3aef04e08` |

## Corrected metrics semantics

Unit contract (unexpected labels as FP):

```text
expected=[STRENGTHENED]
observed=[STRENGTHENED, ADDED, REMOVED, POLARITY_FLIP]
TP=1 FP=3 FN=0 precision=0.25 recall=1.0 F1=0.4
case_passed (allow_extra)=True; exact_pass=False
```

Suite macro F1 on focused cases may still read 1.0 when observed labels match gold after focus filtering — this is **not** a universal accuracy claim. Prior “classification F1=1.0” under FP-omission is **retracted**.

## Negative adversarial results

| Test | Exit |
|------|------|
| verify after old source mutation | 1 |
| verify after new source deletion | 1 |
| extract --out equals source | 2 |
| measure --out equals ground-truth | 2 |
| rehashed dangling ID / wrong summary / evidence hashes | fail (pytest) |
| json/markdown same path | fail (pytest) |

Logs under `evidence/m0-repair/negative/`.

## Repair summary vs audit P0/P1

| Finding | Repair |
|---------|--------|
| P0-01 verify self-checksum only | Strict source SHA, ownership, summary, evidence hashes, required schema |
| P0-02 destructive I/O | `io_safety` preflight + atomic write_transaction |
| P0-03 FP omission | Unmatched observed always FP; gate pass separate |
| P1-01 section title blanket skip | Removed Security/Appendix title kill; explicit markers win |
| P1-02 inline code | Preserve text; protect keyword ranges |
| P1-03 actor | Pre-modal subject only |
| P1-04 blockquote | Informative/quote regions excluded |
| P1-05 multi-read | `ImmutableSource` single load |

## Known failures / residual risks

- M1/M2 code remains experimental; not re-adjudicated.
- Symlink/hardlink edge cases on all platforms not exhaustively proven.
- Locator re-resolution against adapted HTML is structural (xpath/id) not full re-render.
- External re-audit required before any higher milestone claim.

## Non-claims

- Not PRODUCTION_READY / RELEASE_READY / COMPLETE.
- Maximum status: `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.
