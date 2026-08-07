# Claims Register

Implementer is **not** Claim / Evidence / Audit / Release Authority.

## Milestone status

| Milestone | Status |
|-----------|--------|
| M0 | `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` (round-2 repair; pending re-audit) |
| M1 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| M2 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| Production / Release | **BLOCKED** |

## Active claims

| ID | Claim | Scope | Supporting evidence | Unsupported boundary | Last verified commit | Reviewer status |
|----|-------|-------|---------------------|----------------------|----------------------|-----------------|
| C1 | Local HTML extraction under rfc2119/whatwg | M0 | extract path + fixtures | Full NL standards | 34cdbd724b9fab636d72e1680325fffda55f1379 | unreviewed |
| C2 | Frozen 17-case adversarial benchmark | M0 | `normshift benchmark` | Universal accuracy | 34cdbd724b9fab636d72e1680325fffda55f1379 | unreviewed |
| C3 | Verify is source-bound via deterministic replay | M0 | `verify` + round2 tests | Cryptographic authenticity | 34cdbd724b9fab636d72e1680325fffda55f1379 | unreviewed |
| C4 | Multi-artifact writes are rollback-safe on commit failure | M0 I/O | `write_transaction` tests | Cross-directory single-syscall atomicity | 34cdbd724b9fab636d72e1680325fffda55f1379 | unreviewed |
| C5 | Classification FP includes unexpected labels; forbid is gate-only | measure | scoring unit tests | Public leaderboard claims | 34cdbd724b9fab636d72e1680325fffda55f1379 | unreviewed |
| C6 | Single immutable source pair per measure case | measure | read-count test | Multi-process FS races | 34cdbd724b9fab636d72e1680325fffda55f1379 | unreviewed |

## Retracted

- Classification F1=1.0 under FP-omission (audit P0-03, round 1).
- Report self-hash alone as evidence of source derivation (re-audit P0-01).

## Non-claims

- Not production/release ready.
- M1/M2 not complete.
- Not “audit passed” until external authority re-audits this pin.
