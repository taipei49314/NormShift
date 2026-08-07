# M2 Evidence Package — Requirement Lineage Graph

**Implementer status:** `M2_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`  
**Date:** 2026-08-07  
**Push:** deferred (operator instruction)

## Delivered

| Item | Status |
|------|--------|
| Persistent lineage IDs across versions | yes |
| Multi-version CLI `normshift lineage` | yes |
| SPLIT / MERGED relations (strict multiplicity align) | yes |
| CONTINUES / ADDED / REMOVED edges | yes |
| Ambiguity queue | yes (structure ready) |
| Graph JSON export + integrity hash | yes |
| 3-version fixture chain | `fixtures/lineage/v{1,2,3}.html` |
| Instance evidence on each node | yes |

## Commands

```text
uv run ruff check .   # 0
uv run mypy src       # 0
uv run pytest -q      # 44 passed
uv run normshift lineage \
  fixtures/lineage/v1.html \
  fixtures/lineage/v2.html \
  fixtures/lineage/v3.html \
  --adapter html --profile rfc2119 \
  --json evidence/m2/lineage.json
```

## Observed summary (fixture chain)

```text
versions: L1, L2, L3
lineages: 5
edges: 9
relations: CONTINUES=6, SPLIT_INTO=2, ADDED=1
```

## Artifact

| File | SHA-256 | Bytes |
|------|---------|-------|
| `evidence/m2/lineage.json` | `b28ac8a6f8eebdc9d5e0981860e155a699ca14c9a2df7fdd620182a387862713` | 15854 |

## Known limitations

1. Split/merge detection is conservative (strict guards) — some real merges may stay CONTINUES/ADDED until signals improve.
2. Actor/object/scope change classes from full North Star taxonomy are only partially reflected via existing change classifications on CONTINUES edges.
3. Definition / cross-reference graph not yet implemented (deferred).
4. Lineage IDs are alignment-assigned, not external authority IDs.

## Non-claims

- Not release/production ready.
- Not complete North Star M2 exit (definitions/xref graph incomplete).
- External audit required.

## Next

Improve definition/xref dependency edges; then M3 Observatory only after audit priority allows.
