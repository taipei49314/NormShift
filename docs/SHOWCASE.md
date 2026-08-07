# NormShift Showcase

> Evidence-backed **semantic diff** for technical standards.
> Deterministic. Offline-replayable. No LLM as authority.

## Why this matters

Standards change quietly. A SHOULD becomes a MUST. A condition appears.
An exception vanishes. Teams ship against the wrong obligation.

NormShift turns two HTML snapshots into an **evidence-linked change report**
you can re-verify from source bytes — without trusting a chat model.

## Headline numbers (expedition run)

- Live official documents processed: **8**
- Normative requirement instances extracted: **729**
- Provisional real benchmark: **7/7**

### Top extractions

| Requirements | Document |
|-------------:|----------|
| 437 | `https://www.rfc-editor.org/rfc/rfc9110.html` |
| 89 | `https://www.w3.org/TR/trace-context-2/` |
| 75 | `https://www.w3.org/TR/2021/REC-trace-context-1-20211123/` |
| 43 | `https://www.rfc-editor.org/rfc/rfc8949.html` |
| 43 | `https://www.rfc-editor.org/rfc/rfc8949.html` |
| 21 | `https://www.rfc-editor.org/rfc/rfc8259.html` |
| 21 | `https://www.rfc-editor.org/rfc/rfc8259.html` |
| 0 | `https://www.rfc-editor.org/rfc/rfc3986.html` |

## Semantic change example (fixture RFC-like pair)

```text
ADDED  conf=0.95
  + new: Receivers MUST acknowledge STREAM frames promptly.

STRENGTHENED  conf=0.92
  - old: A server SHOULD retry a handshake when the first attempt fails.
  + new: A server MUST retry a handshake when the first attempt fails.

```

## Trust properties

| Property | Behavior |
|----------|----------|
| Source identity | Content SHA-256 + portable refs |
| Verify | Strict JSON + full pipeline replay |
| Offline | Analysis path needs no network |
| Authority | Explicit AUTO/PROVISIONAL labels only |
| Ambiguity | Surfaced, not silently forced |

## One-command demo

```bash
uv sync --frozen --all-extras --dev
uv run normshift diff fixtures/corpus/rfc/sample-v1.html \
  fixtures/corpus/rfc/sample-v2.html --source-root . --adapter rfc \
  --json /tmp/ns.json --markdown /tmp/ns.md
uv run normshift verify /tmp/ns.json --source-root .
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
```

## Expedition mode

Branch `expedition/real-standards-observatory` adds:

- HTTPS allowlisted acquisition store
- Multi-version lineage (SQLite + JSONL)
- Static local observatory + discovery feed

See `docs/EXPEDITION_CHARTER.md` and `artifacts/expedition/EXPEDITION_EVIDENCE.md`.

---

*Not production-ready. Not externally audit-passed. Experimental where stated.*
