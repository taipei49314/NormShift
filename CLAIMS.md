# Claims Register (M0)

Claims below are **implementation claims**, not release or production claims.
NormShift operators are not Claim / Evidence / Audit / Release Authority for
production readiness.

| ID | Claim | Status | Evidence |
|----|-------|--------|----------|
| C1 | Local HTML can be extracted into structured requirements under rfc2119/whatwg profiles | asserted | `tests/`, `normshift extract` |
| C2 | Cross-version alignment exposes multi-signal score components | asserted | report `alignment_score` |
| C3 | Fixed adversarial suite (17 cases) is evaluated by `normshift benchmark` | asserted | `benchmark/ground_truth.jsonl` |
| C4 | JSON reports are integrity-hashed; tampering fails `normshift verify` | asserted | case 16 + e2e tests |
| C5 | Two identical executions produce byte-identical JSON reports | asserted | case 17 + e2e tests |
| C6 | No LLM, embedding, network, or DB required for M0 path | asserted | dependency set + offline design |

## Explicit non-claims

- Does **not** understand arbitrary natural-language standards.
- Does **not** certify compliance (WCAG, EN 301 549, legal contracts, …).
- Is **not** production-ready or release-ready under this milestone.
- Passing tests/benchmark is **not** proof of universal semantic correctness.
