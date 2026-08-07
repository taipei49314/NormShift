# Expedition Evidence — Real Standards Observatory (expanded)

**Status:** `EXPEDITION_CANDIDATE_PENDING_EXTERNAL_AUDIT`  
**Baseline:** `878bfd3a6bb7b649652e81936216277fc8151d5e`  
**Branch:** `expedition/real-standards-observatory`  
**Labels:** `EXPERIMENTAL_NOT_ADJUDICATED` / AUTO only  

## Headline results (this push)

| Metric | Value |
|--------|------:|
| Live official acquisitions | 6+ (RFC 8259, 8949, 9110, 3986; W3C Trace Context 1 & 2) |
| Store snapshots (local) | ~20 |
| Requirement instances extracted | **~727** (across store materializations) |
| RFC 9110 alone | **437** requirements |
| W3C Trace Context pair | 75 → 89 reqs, **114** change events (39 ADDED, 25 REMOVED, 37 MOVED, 12 AMBIGUOUS) |
| Discovery queue items | **83** AUTO |
| benchmark-real | **7/7** provisional offline |
| pytest | **154 passed** |

## Real pair of note

`w3c-trace-context` (official TR snapshots, content-addressed in local store):

- Level 1 REC 2021-11-23 vs Level 2 current TR
- Offline replay from frozen store bytes
- Ambiguity preserved (12 AMBIGUOUS) — not forced into false certainty

## What is committed vs local-only

| Committed | Local only (gitignored) |
|-----------|-------------------------|
| Hash-only manifests under `corpus/snapshots/` | `.normshift/store` object bytes |
| Expand script, CLI, tests | `artifacts/expedition/real/*.html` |
| lineage.jsonl, corpus-summary, discovery queue | Full official HTML materializations |
| benchmark-real metrics | |

## Commands

```text
uv run python scripts/expedition_expand.py
uv run normshift benchmark-real --root . --out artifacts/expedition/benchmark-real-metrics.json
uv run normshift observatory poll --watchlist config/watchlist.yaml
uv run normshift lineage build … --db artifacts/expedition/lineage.db
uv run pytest -q
```

## Limitations

1. Some RFCs (e.g. 8259, 3986 HTML) yield 0 extractions — adapter structure gap (not p/li-centric).
2. Duplicate store entries if re-acquired (content-addressed objects shared).
3. Discovery/classifications are AUTO — not gold.
4. M0 deferred audit debt still open on baseline.
5. Do not merge expedition into main/audited tip.
