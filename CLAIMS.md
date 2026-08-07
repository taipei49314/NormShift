# Claims Register

Implementer is **not** Claim / Evidence / Audit / Release Authority.

## Package identity terminology

- **package_commit / package_tree**: recorded only in the **external** package MANIFEST / bundle HEAD (not self-referenced inside the same commit).
- In-tree documents claim **status** and **behavior**, not that a commit SHA equals itself.
- **package_identity = externally_attested**: package equality is attested outside the tree by the external package verifier (bundle HEAD + Source.zip + MANIFEST), not by embedding a commit's own SHA in that commit.

## Milestone status

| Milestone | Status |
|-----------|--------|
| M0 | `M0_PARTIAL` during repair; after green exact-subject package gate → max `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` |
| M1 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| M2 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| Production / Release | **BLOCKED** |

## Active claims

| ID | Claim | Scope | Supporting evidence | Unsupported boundary | Reviewer status |
|----|-------|-------|---------------------|----------------------|-----------------|
| C1 | Portable reports verify after repository relocation with `--source-root` | M0 | relocation test + round4 evidence | Cryptographic signatures | unreviewed |
| C2 | Verify applies strict JSON boundary then complete canonical Report replay | M0 | `verify` + strict matrix tests | Cryptographic authenticity | unreviewed |
| C3 | Output entry-type/ancestry preflight rejects dirs/symlinks/ancestors; parent-chain cleanup | M0 I/O | path safety tests | All exotic OS entry types | unreviewed |
| C4 | Frozen 17-case adversarial benchmark | M0 | benchmark CLI | Universal accuracy | unreviewed |
| C5 | Unexpected classification labels count as FP; forbid is gate-only | measure | unit tests | Public leaderboard | unreviewed |
| C6 | Generation requires `--source-root` (or CWD); never labels absolute refs `source_root_relative` | M0 | generation matrix | All symlink OS edge cases | unreviewed |
| C7 | Historical authority is modal/clause-local, not whole-paragraph kill | M0 extract | historical matrix | Full natural-language coverage | unreviewed |

## Non-claims

- Not production/release ready.
- Not audit-passed until external authority re-audits the package subject.
- M1/M2 not complete.
- Package tip SHA is not self-pinned inside the repository tree.
