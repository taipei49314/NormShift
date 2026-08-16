# Design Decisions

## D023 — Later master CI does not inherit or release (2026-08-15)

**Decision:** Local and CI reproduction of master commit
`fb3c0656b8150e56604502450c46ff0e2ee027f1`, tree
`e9ed7ed05e505231a8ad2241ea6a6d83b15b6d27`, and push CI
[run 31690202157](https://github.com/taipei49314/NormShift/actions/runs/31690202157)
is implementation evidence only. Canonical wheel SHA-256
`20570a5cb65ace7dd4a0366667735491f0118a44273d501172f2c07d4c1b2349` and sdist
SHA-256 `b0588d45aae6a1fad2e051a70d0312d41d996d08d265843da896bee8ab38142d` do
**not** transplant the historical M0 verdict, replace the ancestor delivery
foundation in D022, satisfy the final combined audit, or authorize a software
release. `last_verified_commit` remains null and `release_status` remains
`BLOCKED`.

## D022 — Cross-platform distribution equality is delivery evidence (2026-08-11)

**Decision:** Strict wheel validation normalizes only supported platform metadata
from a raw build into a new exclusive output. Exact master commit
`f6897f71834a50d2273fda033a72b31254c65935`, tree
`34cde504fab42da8f9423cd1ca226fe492307c36`, and push CI
[run 31462052663](https://github.com/taipei49314/NormShift/actions/runs/31462052663)
proved canonical, byte-identical final wheels and sdists across Ubuntu, Windows, and
macOS. Their SHA-256 values are respectively
`b5ebc295dadb63ab2969185551ca62409e9290d9f9fba41916d188e6a833886d` and
`fb8f1f0add5a752cfa3a070edf0ed984835961b4f93a5c672c0f02ea6b2c4760`.
This is an internal delivery foundation. It does not grant M1/M2 acceptance,
transplant the historical M0 verdict, satisfy the final combined audit, or authorize
a software release.

## D021 — Final release evidence is fail-closed and subject-bound (2026-08-11)

**Decision:** `RELEASE_CHECKLIST.md` is the operational release gate. A missing,
skipped, unavailable, non-zero, mismatched, or unrecorded required result leaves the
corresponding item unchecked and release `BLOCKED`. CI, package preflight, external
audit, tag, release, and download-only verification must all name the same final
commit/tree and immutable artifact digests. Release custody uses canonical physical
file identities, bounded singly linked assets, one sealed audited publication root,
before/after identity-size-hash checks, and independent manifest/audit digest anchors;
the detached audit is strict-schema validated before tagging and after download.

## D020 — M1/M2 foundations do not grant milestone acceptance (2026-08-11)

**Decision:** Policy, scorer, source acquisition, development recipes, labeling and
blind-split governance, lineage graph foundations, and typed semantic-change
dimensions remain
`EXPERIMENTAL_NOT_ADJUDICATED`. M1/M2 acceptance requires independently controlled
blind inputs, pre-frozen thresholds and scorer bytes, minimum support and per-class
metrics, retained evidence, and a detached exact-subject external verdict.

## D019 — External verdicts are non-transitive across commits (2026-08-11)

**Decision:** A detached audit applies only to its recorded commit, tree, manifest,
and artifact bytes. Descendant commits may cite that verdict as history but cannot
inherit it. The final combined M0-M2 subject requires a new authoritative manifest
and detached audit.

## D016 — Portable source_ref for external verify (2026-08-07 r3)

**Decision:** Reports store POSIX relative `source_ref` paths. Verify resolves under
`--source-root`. Absolute generation-machine paths are not authoritative.

## D017 — Complete canonical Report replay comparison

**Decision:** Verify rebuilds a full live `Report` via production builder and
compares exact model dumps (order + floats). Typed `ReportSummary` and
`IntegrityEnvelope` use `extra="forbid"`.

## D018 — Output entry-type and ancestry rejection

**Decision:** Preflight rejects existing non-regular outputs, symlinks (including
dangling), directories, and input/output ancestor relationships. No mutation on reject.

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
**Status:** **Feature-freeze prerequisite satisfied** by the detached
`M0_EXTERNAL_AUDIT_PASS` for exact commit
`b3af3dc26e64a3399545d179731222f6e87213c9`, tree
`c629e2d51fc5219514d6068a90d3453725bd8010`, and manifest SHA-256
`7e95576f71fd061fc010c542b7f91dc67075cd2c7bd8bfd2b801f90c846625db`.
This permitted bounded M1/M2 feature work to resume. It does **not** transplant the
M0 verdict to any descendant/current SHA or satisfy the final combined release gate.

**Historical trigger:** External rejection `EXTERNAL_AUDIT.md` (package
20260807-105717).

**Closure evidence:**
[`m0-audit-20260809-b3af3dc`](https://github.com/taipei49314/NormShift/releases/tag/m0-audit-20260809-b3af3dc).

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
