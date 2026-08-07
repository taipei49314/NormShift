# Claims Register

Implementer is **not** Claim / Evidence / Audit / Release Authority.

## Package identity terminology

- **package_commit / package_tree**: recorded only in the **external** package MANIFEST / bundle HEAD (not self-referenced inside the same commit).
- In-tree documents claim **status** and **behavior**, not that a commit SHA equals itself.

## Milestone status

| Milestone | Status |
|-----------|--------|
| M0 | `M0_PARTIAL` during repair; after green package gate → max `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` |
| M1 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| M2 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| Production / Release | **BLOCKED** |

## Active claims

| ID | Claim | Scope | Supporting evidence | Unsupported boundary | Reviewer status |
|----|-------|-------|---------------------|----------------------|-----------------|
| C1 | Portable reports verify after repository relocation with `--source-root` | M0 | relocation test + round3 evidence | Cryptographic signatures | unreviewed |
| C2 | Verify compares complete canonical replayed Report model | M0 | `verify` + forgery matrix tests | Cryptographic authenticity | unreviewed |
| C3 | Output entry-type/ancestry preflight rejects dirs/symlinks/ancestors | M0 I/O | path safety tests | All exotic OS entry types | unreviewed |
| C4 | Frozen 17-case adversarial benchmark | M0 | benchmark CLI | Universal accuracy | unreviewed |
| C5 | Unexpected classification labels count as FP; forbid is gate-only | measure | unit tests | Public leaderboard | unreviewed |

## Non-claims

- Not production/release ready.
- Not audit-passed until external authority re-audits the R3 package.
- M1/M2 not complete.
