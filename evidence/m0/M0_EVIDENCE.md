# M0 Evidence Package

**Status recorded by implementer (not Claim/Release Authority):**  
`M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`

**Repository:** `C:\Users\G713RW\NormShift`  
**Date (local session):** 2026-08-07  

## Final commit SHA

`83e8797f65b5a097a6a4b2976d81961c2230c95f` (repo tip at evidence closeout; gates re-run green on this history)

## Environment

| Item | Value |
|------|--------|
| Python (uv run) | 3.12.13 |
| Host `python` (unrelated) | 3.9.10 |
| OS | Windows |
| Package manager | uv |
| `uv.lock` SHA-256 | `e3c615fdee45ed69c760b63712b164852d275ab51bde1e30df7cce38bfbf9c6c` |

## Verification commands (clean-gate sequence)

All exit codes below are as observed in the implementation session.

```text
uv sync --all-extras --dev          # packages installed (PowerShell may surface uv deprecation warning)
uv run ruff check .                 # exit 0
uv run mypy src                     # exit 0 — Success: no issues found in 27 source files
uv run pytest -q                    # exit 0 — 32 passed
uv run normshift benchmark \
  --ground-truth benchmark/ground_truth.jsonl
                                    # exit 0 — 17/17 passed, 0 failed
```

### Vertical slice

```text
uv run normshift diff \
  fixtures/synthetic/spec-v1.html \
  fixtures/synthetic/spec-v2.html \
  --profile rfc2119 \
  --json evidence/m0/report.json \
  --markdown evidence/m0/report.md
# exit 0 — 9→11 requirements, 11 changes

uv run normshift verify evidence/m0/report.json
# exit 0 — OK integrity=41eb5ead99c6422f662d095302f478c85aa45790fc83f5b9e5311733cc222c75
```

### Determinism (byte-identical JSON)

Two consecutive `normshift diff` runs writing:

- `evidence/m0/report.json`
- `evidence/m0/report_run2.json`

```text
SHA-256(report.json)      = 33f541d46c27d339d174619533cb4aabe7f5ac0587a68ed71d24fded458a3d72
SHA-256(report_run2.json) = 33f541d46c27d339d174619533cb4aabe7f5ac0587a68ed71d24fded458a3d72
identical = True
```

### Tamper detection

```text
# Mutated summary.change_count without updating integrity.content_sha256
uv run normshift verify evidence/m0/report_tampered.json
# exit 1 — Integrity hash mismatch
```

## Artifact hashes

| Artifact | SHA-256 | Bytes |
|----------|---------|-------|
| `evidence/m0/report.json` | `33f541d46c27d339d174619533cb4aabe7f5ac0587a68ed71d24fded458a3d72` | 36140 |
| `evidence/m0/report_run2.json` | `33f541d46c27d339d174619533cb4aabe7f5ac0587a68ed71d24fded458a3d72` | 36140 |
| `evidence/m0/report.md` | `4471c27045ad3dbe16574e911b99231bff1704d047a88696c5dd7e0433daeb36` | 13566 |
| `evidence/m0/report_tampered.json` | `fab74729f274e112246470ee04b75b55a0e393d633068f2de61fa2142ff294e5` | 37007 |
| `uv.lock` | `e3c615fdee45ed69c760b63712b164852d275ab51bde1e30df7cce38bfbf9c6c` | — |

Report integrity field (`content_sha256` over payload excluding `integrity`):

`41eb5ead99c6422f662d095302f478c85aa45790fc83f5b9e5311733cc222c75`

## Test summary

- **pytest:** 32 passed, 0 failed
- Coverage layers: unit (profiles, normalize, classify, align, hypothesis), integration (extract/diff), e2e (CLI, verify, benchmark)

## Benchmark metrics

| Metric | Value |
|--------|-------|
| Cases total | 17 |
| Passed | 17 |
| Failed | 0 |
| Pass rate | 100% of fixed adversarial suite |

Case IDs 01–17 all PASS (strengthen, weaken, polarity flip, moved, editorial, added, removed, exception, condition, codeblock ignore, mustard, not-required, WHATWG lowercase, similar non-cross-match, relocation, tamper verify, determinism).

## Known limitations

1. **Keyword / heuristic extraction only** — no general NL understanding of arbitrary standards.
2. **Actor/action/condition/exception** are deterministic regex heuristics; complex syntax may be incomplete or AMBIGUOUS.
3. **Informative region detection** relies on tags/classes/roles; custom non-normative widgets may leak or hide text.
4. **Alignment** is greedy multi-signal, not globally optimal assignment; large documents may need better solvers later.
5. **RFC2119 profile** ignores lowercase must/should/may by design; use `--profile whatwg` for lowercase specs.
6. **M0 HTML only** — no PDF, no network, no LLM, no database.

## Unresolved risks

1. Real-world specs with mixed informative/normative markup may need profile extensions.
2. Multi-keyword sentences produce multiple requirements; downstream consumers must handle that granularity.
3. External audit of classification policy vs. standards-community expectations has not been performed.
4. Windows path/encoding edge cases outside UTF-8 HTML are lightly tested.

## Next recommended engineering action

External audit of:

1. Classification policy vs. RFC 2119 / WHATWG keyword practice  
2. Benchmark completeness for additional adversarial patterns  
3. Whether M1 should expand adapters (e.g. plain text / Markdown) without relaxing M0 determinism guarantees  

**Do not treat this package as production or release readiness.**
