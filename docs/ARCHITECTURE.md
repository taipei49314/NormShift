# Architecture

```text
┌──────────────┐     HTTPS allowlist      ┌─────────────────────┐
│ Official URL │ ───────────────────────► │ Snapshot Store      │
└──────────────┘     (acquire only)       │ content-addressed   │
                                          │ SHA-256 objects     │
                                          └──────────┬──────────┘
                                                     │ offline
                                          ┌──────────▼──────────┐
                                          │ Adapters            │
                                          │ RFC / W3C / WHATWG  │
                                          │ generic HTML        │
                                          └──────────┬──────────┘
                                                     │
                    ┌────────────────────────────────┼────────────────────────┐
                    ▼                                ▼                        ▼
           ┌────────────────┐              ┌─────────────────┐      ┌──────────────────┐
           │ Extract        │              │ Align + Classify│      │ Lineage Graph    │
           │ BCP14 / WHATWG │              │ multi-signal    │      │ SQLite + JSONL   │
           └────────┬───────┘              └────────┬────────┘      └────────┬─────────┘
                    │                               │                        │
                    └───────────────────────────────┼────────────────────────┘
                                                    ▼
                                         ┌────────────────────┐
                                         │ Evidence Report    │
                                         │ JSON + Markdown    │
                                         │ integrity digest   │
                                         └─────────┬──────────┘
                                                   │
                                         ┌─────────▼──────────┐
                                         │ Verify (replay)    │
                                         │ strict JSON + full │
                                         │ pipeline rebuild   │
                                         └─────────┬──────────┘
                                                   │
                                         ┌─────────▼──────────┐
                                         │ Observatory site   │
                                         │ static + feeds     │
                                         └────────────────────┘
```

## Design rules

1. **Network is acquisition-only.** Diff, extract, lineage, and observatory build run offline.
2. **No LLM authority.** Optional explanations must never change IDs, verdicts, or metrics.
3. **Ambiguity is data.** Do not force one-to-one matches when evidence is weak.
4. **Labels have authority levels.** AUTO / PROVISIONAL ≠ adjudicated gold.
5. **M0 trust core** is separate from the expedition branch; main stays frozen for audits.

## Identities (do not collapse)

| Identity | Meaning |
|----------|---------|
| Document snapshot | Exact bytes + provenance |
| Requirement instance | One obligation in one snapshot |
| Requirement lineage | Hypothesized continuing obligation |
| Change event | Transition with scores + reasons |
