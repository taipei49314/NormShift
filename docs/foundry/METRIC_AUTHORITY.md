# Metric Authority

| Layer | Truth source | Allowed metrics |
|-------|--------------|-----------------|
| A Synthetic Gold | Frozen fixtures | precision/recall/F1 |
| B Real Provisional | Real docs, AUTO only | counts, ambiguity, replay, capsule verify |
| C Externally Reviewed | Imported external ledger only | acceptance, relabel, F1 |

Never score AUTO as expected truth.
When no external decisions: `reviewed_metrics.status = NOT_AVAILABLE`.
