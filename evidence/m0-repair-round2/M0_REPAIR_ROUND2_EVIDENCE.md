# M0 Repair Round 2 Evidence

**Status (implementer):** `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`  
**Not:** PRODUCTION_READY / RELEASE_READY / AUDIT PASSED

## Verified revision

| Field | Value |
|-------|--------|
| Commit | `a4dd46a01ed8d7af577c456d1e209274868d0d4e` |
| Tree | `bfb0f11614f1f217f10094be6ad429bee4973cd2` |
| Dirty | clean |

## Defects fixed (re-audit)

| ID | Fix |
|----|-----|
| P0-01 | Deterministic source-bound **replay** inside `verify` (re-extract + re-classify) |
| P0-02 | Rollback-safe multi-file commit (backup → replace → restore on failure) |
| P0-03 | One commit identity + git bundle + external manifest (packaging) |
| P1-01 | `run_measure` single `ImmutableSource` pair per case |
| P1-02 | Class tokens: `non-normative` informative; exact `normative` only |
| P1-03 | Offset-accurate protected spans for inline code |
| P1-04 | Inline `<q>` + historical quote framing protected |
| P1-05 | `forbid` affects gate flags only, not TP/FP/FN |

## Gates (this revision)

```text
uv run ruff check .     # 0
uv run mypy src         # 0
uv run pytest -q        # 92 passed
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl  # 17/17
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl \
  --out evidence/m0-repair-round2/metrics.json
uv run normshift diff fixtures/synthetic/spec-v1.html fixtures/synthetic/spec-v2.html \
  --profile rfc2119 --json evidence/m0-repair-round2/report.json \
  --markdown evidence/m0-repair-round2/report.md
uv run normshift verify evidence/m0-repair-round2/report.json --source-root .  # 0
```

## Artifact hashes

| File | SHA-256 |
|------|---------|
| report.json | `8cca92c46287715db24d3f572b1ca8e2612d9d7d276bf9fe71bf7f4f2ba6201e` |
| report.md | `60be30a54c646859225781adb0787cc3a8a1c8ba2496c307b271c6d80f5eb3ad` |
| metrics.json | `fb76642f9178b3bfb6e2bd2bb85ded0b75d18aea003f50af461d51314e7a8808` |
| uv.lock | `40424b150fedf7b9d30be4273f6abb7e5db1f636dfd54faffc24676383418978` |

## Metrics semantics (scoped)

Forbid-gate contract case:

```text
expected=[STRENGTHENED] observed=[STRENGTHENED, ADDED] forbid=[ADDED]
TP=1 FP=1 FN=0 precision=0.5 recall=1.0 F1=0.6667 case_passed=false
```

## Packaging products (external)

- Git bundle: `NormShift-M0-R2.bundle`
- Source archive: `NormShift-M0-R2-Source.zip` (forward-slash entries)
- Manifest: `NormShift-M0-R2-MANIFEST.json`

## Known limitations

- Replay proves deterministic derivation, not cryptographic signatures.
- Multi-file commit is rollback-safe, not single-system-call atomic across dirs.
- M1/M2 remain experimental / not adjudicated.

## Next

Independent external re-audit. No M1/M2 feature work.
