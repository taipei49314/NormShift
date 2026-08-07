# Measurement Instrument + Dependency Linkage Evidence

**Implementer status:** meters + M2 dependency slice landed  
**Not claimed:** PRODUCTION_READY / RELEASE_READY / COMPLETE / external audit done

## Instrument

```text
uv run normshift measure \
  --ground-truth benchmark/measure_suite.jsonl \
  --out evidence/m2/metrics.json
```

Frozen suite: `benchmark/measure_suite.jsonl` (does not alter adversarial expected labels).

### Metrics (15/15 cases)

| Layer | precision | recall | f1 |
|-------|-----------|--------|-----|
| extraction | 1.0 | 1.0 | 1.0 |
| alignment | 1.0 | 1.0 | 1.0 |
| classification | 1.0 | 1.0 | 1.0 |
| classification case_pass_rate | — | — | 1.0 |

### Determinism

Two consecutive measure runs → byte-identical metrics JSON  
SHA-256: `6c1b8a43e17f8c7d4f53c84b1433b2045ad41793c0030efe8beebc973efc0ab6`

### Fail-closed

| Input | exit | artifact written |
|-------|------|------------------|
| missing ground-truth | 2 | no |
| empty suite | 2 | no |

## Dependency / definition linkage

```text
uv run normshift lineage fixtures/lineage/v{1,2,3}.html \
  --adapter html --json evidence/m2/lineage.json
```

Observed:

- definitions present on graph
- dependency_links present
- relations include `REFERENCES_DEFINITION`, `DEFINITION_CHANGED`, `DEPENDS_ON`
- multi-version identity: CONTINUES + SPLIT_INTO (not ADD+REMOVE only)

## Full gate

```text
uv run ruff check .     # 0
uv run mypy src         # 0
uv run pytest -q        # 53 passed
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl  # 17/17
```

## Known limitations

- Measure suite labels extraction/alignment for 15 core cases (not all of M4 public benchmark ambition)
- Definition extraction is deterministic heuristics (dfn + “is defined as”), not full NL
- No production/release claim
