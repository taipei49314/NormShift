# Expedition Evidence — Real Standards Observatory

**Status:** `EXPEDITION_CANDIDATE_PENDING_EXTERNAL_AUDIT`  
**Baseline:** `878bfd3a6bb7b649652e81936216277fc8151d5e`  
**Branch:** `expedition/real-standards-observatory`  
**Labels:** `EXPERIMENTAL_NOT_ADJUDICATED`

## Vertical slices demonstrated

| Slice | Evidence |
|-------|----------|
| Acquisition / snapshot store | `normshift acquire --import-file` → `.normshift/store` (6 snapshots) |
| Offline snapshot verify | store verify after import; tamper detection in tests |
| Adapter diagnose | `tests/expedition/test_adapter_diagnose.py` (IETF/W3C/WHATWG fixtures) |
| Real pair diffs | `artifacts/expedition/{rfc,w3c,whatwg}-pair.json` + verify FULL |
| Lineage 3-version | `artifacts/expedition/lineage.db` + deterministic `lineage.jsonl` |
| Observatory offline | `artifacts/expedition/site/` + `observatory verify` ok |
| Corpus catalog | `corpus/catalog.yaml` (3 families, 5 pairs, redistributable fixtures) |

## Deferred M0 debt

See `docs/DEFERRED_M0_AUDIT_DEBT.md` — not claimed closed by this expedition.

## Known limitations

- Live HTTPS acquisition not required for offline gates; fixtures imported with official-domain URL placeholders under allowlist policy.
- Corpus counts below full expedition numeric targets for live official multi-version sets (network/redistribution constrained).
- Split/merge candidates not yet densely populated.
- Old CLI `normshift lineage DOCS` moved to `normshift lineage graph DOCS`.
