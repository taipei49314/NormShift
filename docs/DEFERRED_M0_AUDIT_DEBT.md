# Deferred M0 Audit Debt

**Baseline:** `878bfd3a6bb7b649652e81936216277fc8151d5e` (NormShift-M0-R4)  
**Expedition branch:** `expedition/real-standards-observatory`  
**Status:** Deferred — not adjudicated by this expedition

This expedition does **not** claim that R4 open trust-boundary issues are resolved.

## Deferred topics (from R4 external audit / Round 5 mission)

1. **Exact canonical representation edge cases**  
   Signed-zero (`-0.0`) acceptance via Python float equality; non-finite overflow forms; canonical payload-byte equality for live replay.

2. **Portable logical source-reference grammar**  
   Non-canonical aliases (`./path`, `//`, `segment/./path`), override acceptance of empty/backslash/UNC/URI-like refs; platform-independent PurePosix canonical binding.

3. **Clause-level historical normative authority**  
   Bare `previous`/`prior`/`earlier` words suppressing current obligations; leakage of paraphrased historical reporting; fingerprint pollution from historical commentary.

4. **Single authoritative attestation manifest**  
   Re-export overlay manifests vs one complete gate-contract manifest; reproducible external package verifier.

## Rules

- Do not spend expedition effort repairing these unless one **directly blocks** expedition function.
- Unavoidable core changes → `docs/CORE_DEVIATION_LOG.md` with reason, files, tests, impact.
- No expedition feature may alter M0 evidence meaning without an explicit migration record.
