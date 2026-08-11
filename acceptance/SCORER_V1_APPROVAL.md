# NormShift M1/M2 Scorer Freeze — Detached Reviewer Approval

- Decision: `APPROVED`
- Scope: `SCORER_FREEZE_ONLY`
- Reviewer: `/root/m1_acceptance_review`
- Reviewer role: `READ_ONLY_INDEPENDENT_REVIEWER`
- Approved at UTC: `2026-08-11T01:23:45Z`
- Repository: `https://github.com/taipei49314/NormShift`
- Frozen policy ID: `normshift-m1-m2-prereg-v1`
- Frozen policy SHA-256: `0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773`
- Policy baseline commit: `b3af3dc26e64a3399545d179731222f6e87213c9`
- Policy baseline tree: `c629e2d51fc5219514d6068a90d3453725bd8010`
- Scorer base commit: `e6a09a2197ee721b73ca32cf03a3f524b6270bff`
- Scorer base tree: `86b97fee0dc0205483c953861ea379b71c64b17c`
- Approved scorer commit: `df4a02694636836426867f279b83116380b98c63`
- Approved scorer tree: `7196da6a902a523159d6bb514abe22239bccce0a`
- Scorer manifest path: `acceptance/scorer_v1_manifest.json`
- Scorer manifest SHA-256: `da34c33acb20b41fbacfcb58358a6a55287cf8e2d0b270e4779032fdf150b6ed`
- Scorer manifest bytes: `4501`
- Frozen runtime identity: `CPython 3.12; Pydantic 2.13.4`
- Open P0 findings: `0`
- Open P1 findings: `0`

## Reviewer disclosure

I performed a detached, read-only review. I did not edit or implement the scorer or the evaluated M1/M2 system. I did not inspect final gold labels, a final label-decision ledger, blind split membership, holdout source identities, candidate predictions, per-case holdout outputs, or final acceptance scores. For this scorer-freeze decision, the reviewed inputs were the scorer source, frozen policy and manifest bytes, structural schemas, and synthetic unit fixtures. Separately, in the same read-only role, I inspected the disclosed development-only source-curation staging (raw/replay/header/license/chain evidence). That staging contained no labels, split membership, predictions, scores, candidate outputs, or blind-holdout identities, and it was not used to approve any scorer outcome.

## Verification basis

The exact approved commit and manifest bind the frozen policy, canonical item-key and locator logic, models, scorer, schemas, wrapper scripts, adversarial tests, relevant transitive local imports, `pyproject.toml`, `uv.lock`, and runtime identity. The scorer requires an independently supplied manifest digest, recomputes exact per-class TP/FP/FN, support, precision, recall, and F1 using integer cross-multiplication, counts missing predictions as FN and valid unexpected positive outputs as FP, rejects duplicates and malformed inputs, supports M2 cross-family hard negatives, and leaves every non-metric gate explicitly unevaluated.

Independent verification on the exact subject passed:

- clean worktree at the approved commit;
- `uv run --frozen ruff check .`;
- `uv run --frozen mypy --no-incremental src` — 59 source files;
- `uv run --frozen pytest -p no:cacheprovider -q` — 354 passed;
- focused scorer suite — 25 passed;
- exact manifest sidecar/hash, frozen-file inventory, schema mirrors, canonical JSON, negative binding, arithmetic, output-safety, locator, oversized-input, and cross-family tests.

## Approval boundary

This approval freezes only the exact scorer contract identified above. It is not approval of any actual source corpus, source license conclusion, final gold or decision ledger, blind split or holdout custody, candidate package, candidate outputs, observed metric result, M1 acceptance, M2 acceptance, external audit, release, or publication claim. Scorer results remain `DECLARED_SUPPORT_METRICS_ONLY`; all eight external gates remain `NOT_EVALUATED`; `external_acceptance_granted` remains `false`. CI success alone cannot grant external acceptance.

Any byte change to the scorer manifest or any manifest-hashed file, any runtime/dependency identity change, any threshold/support reduction, or any post-result scorer change invalidates this approval and requires a new manifest digest and new detached review. This statement is intentionally outside `scorer_v1_manifest.json`; it must not be added to that manifest or trigger a manifest regeneration/self-reference cycle.
