# NormShift M1/M2 Scorer Freeze — Detached Reviewer Approval

- Decision: `APPROVED`
- Scope: `SCORER_FREEZE_ONLY`
- Reviewer: `/root/m1_acceptance_review`
- Reviewer role: `READ_ONLY_INDEPENDENT_REVIEWER`
- Approved at UTC: `2026-08-11T02:07:03Z`
- Repository: `https://github.com/taipei49314/NormShift`
- Frozen policy ID: `normshift-m1-m2-prereg-v1`
- Frozen policy SHA-256: `0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773`
- Policy baseline commit: `b3af3dc26e64a3399545d179731222f6e87213c9`
- Policy baseline tree: `c629e2d51fc5219514d6068a90d3453725bd8010`
- Scorer authority base commit: `60cb8f2012423ed3990bcfaf22cbf0fab96bdb27`
- Scorer authority base tree: `b0470b8e957cac4a455044b6800219b62186f759`
- Approved scorer commit: `1694a807bb040b8f5626ef10dd70fa22e92e2a6d`
- Approved scorer tree: `dda4c09975192fa7695bb2f3b165d6721acab15c`
- Scorer manifest path: `acceptance/scorer_v1_manifest.json`
- Scorer manifest SHA-256: `b1fc10ef04a8e78d2ff016f440b7800f4bcf5c7e82166bceffe472776959ee80`
- Scorer manifest bytes: `4501`
- Frozen runtime identity: `CPython 3.12; Pydantic 2.13.4`
- Open P0 findings: `0`
- Open P1 findings: `0`

## Reviewer disclosure

I performed a detached, read-only review. I did not edit or implement the scorer or the evaluated M1/M2 system. I did not inspect final gold labels, a final label-decision ledger, blind split membership, holdout source identities, candidate predictions, per-case holdout outputs, or final acceptance scores. For this scorer-freeze decision, the reviewed inputs were the scorer source, frozen policy and manifest bytes, structural schemas, relevant transitive local imports, and synthetic unit fixtures. Separately, in the same read-only role, I inspected the disclosed development-only source-curation staging and the acquisition-boundary hardening. Those materials contained no final labels, split membership, predictions, scores, candidate outputs, or blind-holdout identities, and they were not used to approve any scorer outcome.

## Verification basis

The exact approved commit and manifest bind the frozen policy, canonical item-key and locator logic, models, scorer, schemas, wrapper scripts, adversarial tests, relevant transitive local imports, `pyproject.toml`, `uv.lock`, and runtime identity. The manifest was independently strict-parsed and canonicalized; its digest sidecar matched exactly; all 24 declared files matched their frozen byte lengths and SHA-256 values. Relative to the previously reviewed scorer contract, the scorer source, schemas, wrappers, and synthetic tests are byte-identical; the refreshed manifest changes only the frozen `src/normshift/io_safety.py` bytes introduced by the separately reviewed acquisition hardening.

The scorer requires an independently supplied manifest digest, recomputes exact per-class TP/FP/FN, support, precision, recall, and F1 using integer cross-multiplication, counts missing predictions as FN and valid unexpected positive outputs as FP, rejects duplicates and malformed inputs, supports M2 cross-family hard negatives, and leaves every non-metric gate explicitly unevaluated.

Independent verification on the exact subject passed:

- clean worktree at the approved commit;
- `uv run --frozen ruff check .`;
- `uv run --frozen mypy --no-incremental src` — 59 source files;
- `uv run --frozen pytest -p no:cacheprovider` — 376 passed;
- focused scorer suite — 25 passed;
- exact manifest sidecar/hash, 24-file frozen inventory, strict/canonical JSON, schema mirrors, negative binding, arithmetic, output-safety, locator, oversized-input, and cross-family tests.

## Approval boundary

This approval freezes only the exact scorer contract identified above. It is not approval of any actual source corpus, source license conclusion, final gold or decision ledger, blind split or holdout custody, candidate package, candidate outputs, observed metric result, M1 acceptance, M2 acceptance, external audit, release, or publication claim. Scorer results remain `DECLARED_SUPPORT_METRICS_ONLY`; all eight external gates remain `NOT_EVALUATED`; `external_acceptance_granted` remains `false`. CI success alone cannot grant external acceptance.

Any byte change to the scorer manifest or any manifest-hashed file, any runtime/dependency identity change, any threshold/support reduction, or any post-result scorer change invalidates this approval and requires a new manifest digest and new detached review. This statement is intentionally outside `scorer_v1_manifest.json`; it must not be added to that manifest or trigger a manifest regeneration/self-reference cycle.
