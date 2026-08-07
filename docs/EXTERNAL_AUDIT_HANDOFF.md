# External Audit Handoff — Real Standards Observatory Expedition

## Package

Submit:

- `NormShift-Expedition.bundle`
- `NormShift-Expedition-Source.zip`
- `NormShift-Expedition-MANIFEST.json`

## Claims boundary

- Status at most: `EXPEDITION_CANDIDATE_PENDING_EXTERNAL_AUDIT`
- M1/M2/M3 remain `EXPERIMENTAL_NOT_ADJUDICATED`
- Baseline R4 deferred M0 debt is **not** closed by this branch

## Suggested checks

1. Clean clone of package tip from expedition branch
2. `uv run pytest -q` (includes `tests/expedition/`)
3. Offline acquire via `--import-file`, pair diffs, lineage export byte identity, observatory verify
4. Confirm main baseline `878bfd3` is still recoverable and not mutated by merge

## Do not accept as

- Production / release ready
- Gold-labeled corpus
- Resolution of M0 R4/R5 trust-boundary blockers
