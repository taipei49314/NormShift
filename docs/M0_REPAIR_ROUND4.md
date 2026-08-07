# M0 Repair Round 4 — implementer notes

**Tool version:** 0.3.1  
**Status at package tip:** `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` (implementer only; not external audit passage)  
**Package identity:** `externally_attested` (equality lives in external MANIFEST / bundle HEAD)

## Scope closed (relative to R3 external audit)

| ID | Finding | Repair |
|----|---------|--------|
| P0-01 | Exact package subject failed claimed gate; `or True`; self-ref SHA | External-attestation contract; no post-gate status commit; no self-pin SHA |
| P0-02 | Verifier accepted coerced / duplicate / omitted-default JSON | `strict_json.strict_loads` + field presence + complete typed dump equality before replay |
| P0-03 | Absolute paths labeled `source_root_relative` | Generation `--source-root`; fail closed outside root |
| P0-04 | Historical framing false pos/neg | Modal/clause-local `extract/historical.py` |
| P1-01 | Failed multi-output staging left created parents | Parent-chain tracking + reverse empty-dir cleanup |
| P1-02 | Override scope warning-only | `verification_scope=FULL\|CONTENT_ONLY_OVERRIDE`; declared ref still validated |
| P1-03 | Incomplete red tests / vacuous assertion | `tests/e2e/test_m0_repair_round4.py` matrices |
| P1-04 | Manifest / version / description | Version 0.3.1; description does not claim adjudicated M1/M2 |

## Frozen accepted R3 behavior

Preserved: archive identity, relocation verify, source mutation detection, full replay, special-entry rejection, ordinary rollback, 17/17 benchmark, 15/15 measure, FP accounting, forbid gate-only.

## Known limitations

- Historical rules are deterministic regex/clause heuristics, not full NL understanding.
- Parent-chain cleanup is best-effort for empty dirs created by the invocation; not global multi-dir atomic visibility.
- Override verification is content-only; logical path is not re-attested.
- M1/M2 remain `EXPERIMENTAL_NOT_ADJUDICATED`.
