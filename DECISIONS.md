# Design Decisions

## D014 — Verify must deterministically replay extraction (2026-08-07 r2)

**Decision:** `normshift verify` reloads sources once, re-extracts, re-aligns,
and re-classifies; report content must match replay. Self-consistent forgeries
are rejected.

## D015 — Multi-file writes are rollback-safe

**Decision:** `write_transaction` backups existing finals before replace and
restores all on any commit-phase failure. Not globally atomic visibility.

## D010 — M0 freeze after external audit rejection (2026-08-07)

**Decision:** No new feature work (M1/M2 expansion, adapters, lineage features,
dashboard, crawler, DB, LLM) until M0 is externally re-accepted.  
**Status:** M0_PARTIAL. Existing M1/M2 code remains as experimental slices only.  
**Trigger:** External audit `EXTERNAL_AUDIT.md` (package 20260807-105717).

## D011 — Strict evidence verification is mandatory for M0

**Decision:** `normshift verify` must validate source snapshot hashes, requirement
ownership, change references, summary counts, evidence hashes, and bundled schema.  
Self-checksum alone is insufficient.

## D012 — Universal output safety

**Decision:** All artifact-writing commands use shared path-preflight and
same-directory atomic replace. Input/output collisions fail closed. Pre-existing
outputs are never deleted on rollback.

## D013 — Metrics separate gate pass from precision

**Decision:** `allow_extra` affects only case gate pass. Unmatched observed labels
always count as false positives in precision/recall/F1.

## D009 — M1 adapters are offline-first with provenance sidecars

**Decision:** Real-standard families via local adapters + optional `*.meta.json`.  
**Status:** Experimental; not adjudicated as M1 complete.

## D008 — Official North Star charter adopted as source of truth

**Decision:** `docs/NORTH_STAR.md` is product charter.  
**Status:** Accepted.

## D001 — Package build backend: hatchling

**Decision:** Use hatchling. **Status:** Accepted.

## D002 — Alignment algorithm: greedy multi-signal

**Decision:** Greedy multi-signal aligner. **Status:** Accepted for M0.

## D003 — One requirement per keyword hit per block

**Decision:** One requirement per keyword match. **Status:** Accepted.

## D004 — Informative region detection structural + class/role

**Decision:** Structural ignore + informative classes. **Status:** Amended by D010 repair (no blanket title skip for Security/Appendix).

## D005 — Report integrity hash excludes integrity field

**Decision:** content_sha256 excludes integrity key. **Status:** Accepted; extended by D011.

## D006 — Document version from meta/content

**Decision:** Never filename-only version identity. **Status:** Accepted.

## D007 — jsonschema for report verification

**Decision:** Bundled schemas required; missing schema is verifier failure. **Status:** Amended by D011.
