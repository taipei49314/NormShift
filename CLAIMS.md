# Claims Register

Implementer is **not** Claim / Evidence / Audit / Release Authority.

## Milestone status (post external audit 2026-08-07)

| Milestone | Status |
|-----------|--------|
| M0 Normative HTML Vertical Slice | `M0_PARTIAL` (trust-chain repair in progress / pending re-audit) |
| M1 Real Standards Adapters | `EXPERIMENTAL_NOT_ADJUDICATED` |
| M2 Requirement Lineage Graph | `EXPERIMENTAL_NOT_ADJUDICATED` |
| Production / Release | **BLOCKED** |

## Active claims

| ID | Claim | Scope | Supporting evidence | Unsupported boundary | Last verified commit | Reviewer status |
|----|-------|-------|---------------------|----------------------|----------------------|-----------------|
| C1 | Local HTML extraction under rfc2119/whatwg | M0 local HTML | extract CLI, fixtures, tests | Real TR dumps, full NL | pending pin | unreviewed |
| C2 | Fixed adversarial 17-case benchmark | frozen labels | `normshift benchmark` | Universal accuracy | pending pin | unreviewed |
| C3 | Report self-hash + **source/evidence chain** verify | M0 repair | `normshift verify --source-root` | Cryptographic signatures | pending pin | unreviewed |
| C4 | Output path safety rejects source/GT overwrite | all write CLIs | `tests/e2e/test_m0_repair_contract.py` | All OS symlink edge cases | pending pin | unreviewed |
| C5 | Classification metrics count unexpected labels as FP | measure scorers | `test_classification_metrics_count_unexpected_labels_as_fp` | Public benchmark leadership | pending pin | unreviewed |
| C6 | Single immutable source snapshot per pipeline input | run_diff/extract | `test_pipeline_uses_single_source_snapshot` | Concurrent multi-process FS races | pending pin | unreviewed |

## Retracted claims

- **Retracted:** “classification F1=1.0” as a general accuracy claim under `allow_extra` FP omission (external audit P0-03).  
  Metrics now count unmatched observed labels as FP. Suite gate pass remains separate from precision.

## Explicit non-claims

- Not production-ready or release-ready.
- M1/M2 not adjudicated complete.
- Does not understand arbitrary natural-language standards.
- Passing tests ≠ universal semantic correctness.
