# Claims Register

Claims below are **implementation claims**, not release or production claims.
The implementing agent is not Claim / Evidence / Audit / Release Authority.

Governance (North Star §14): each public claim records claim, scope, evidence,
unsupported boundary, last verified commit, and reviewer status.

## Active claims (M0)

| ID | Claim | Scope | Supporting evidence | Unsupported boundary | Last verified commit | Reviewer status |
|----|-------|-------|---------------------|----------------------|----------------------|-----------------|
| C1 | Local HTML can be extracted into structured requirements under rfc2119/whatwg profiles | M0 local HTML only | `tests/`, `normshift extract`, fixtures | Real RFC/W3C corpora, non-HTML formats | pending pin on push tip | unreviewed |
| C2 | Cross-version alignment exposes multi-signal score components | one-to-one greedy aligner | report `alignment_score` fields | one-to-many / many-to-one / lineage IDs | pending pin on push tip | unreviewed |
| C3 | Fixed adversarial suite (17 cases) is evaluated by `normshift benchmark` | frozen `benchmark/ground_truth.jsonl` | case 01–17 PASS | Universal semantic correctness | pending pin on push tip | unreviewed |
| C4 | JSON reports are integrity-hashed; tampering fails `normshift verify` | canonical JSON integrity | case 16 + e2e + `evidence/m0/report_tampered.json` | Cryptographic signatures / key management | pending pin on push tip | unreviewed |
| C5 | Two identical executions produce byte-identical JSON reports | same tool version + inputs | case 17 + dual run hashes | Non-UTF8 / non-canonical external mutation | pending pin on push tip | unreviewed |
| C6 | No LLM, embedding, network, or DB required for M0 path | M0 correctness path | dependency set + offline design | Future optional LLM assist (must not be authority) | pending pin on push tip | unreviewed |
| C7 | M0 milestone implements North Star M0 exit items (deterministic HTML vertical slice) | M0 only | `docs/NORTH_STAR.md` §10 M0 + `evidence/m0/` | M1–M6 capabilities | pending pin on push tip | unreviewed |

## Explicit non-claims

- Does **not** understand arbitrary natural-language standards.
- Does **not** certify compliance (WCAG, EN 301 549, legal contracts, …).
- Is **not** production-ready or release-ready.
- Passing tests/benchmark is **not** proof of universal semantic correctness.
- Does **not** claim Requirement Lineage Graph (M2), Observatory (M3), or public benchmark standard (M4) are implemented.
- Maximum milestone status allowed for implementer: `M*_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.

| C8 | Three offline document families (RFC/W3C/WHATWG) replay via adapters with provenance | M1 local corpus | `fixtures/corpus/`, `evidence/m1/`, adapter tests | Live network fetch / full TR dumps | pending pin | unreviewed |
| C9 | Adapter failure does not write success artifacts | M1 pipeline | `test_adapter_failure_no_artifact` | Partial mid-write OS crashes | pending pin | unreviewed |

## Milestone status

| Milestone | Status |
|-----------|--------|
| M0 Normative HTML Vertical Slice | `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` |
| M1 Real Standards Adapters | `M1_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` |
| M2 Requirement Lineage Graph | `M2_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` (core; def/xref partial) |
| M3 Observatory | not started |
| M4 Public Benchmark | not started |
| M5 Implementation Impact Mapping | not started |
| M6 Standards Time Graph | not started |
