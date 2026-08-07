# Branch architecture

```text
master
└── M0 R5 trust core          ← default product / audit subject for M0

expedition/real-standards-observatory
└── 真實標準遠征              ← first live-RFC/W3C vertical slice

expedition/corpus-foundry-24h
└── 最新研究型 showcase       ← campaign / capsules / review foundry
```

## Rules

| Branch | May merge into master? | Role |
|--------|------------------------|------|
| `master` | — | Frozen M0 trust core (R5). External M0 audit subject. |
| `expedition/real-standards-observatory` | **No** (by default) | Real-standards acquisition + observatory prototype |
| `expedition/corpus-foundry-24h` | **No** (by default) | Corpus foundry, capsules, review ledger, layered metrics |

- Expedition labels remain `EXPERIMENTAL_NOT_ADJUDICATED` / `AUTO`.
- Do not claim expedition work closes deferred M0 R4/R5 audit debt.
- Do not merge foundry or observatory into `master` without an explicit product decision.

## Tips (implementer)

| Branch | Commit (short) | Status ceiling |
|--------|----------------|----------------|
| `master` | R5 tip | `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` |
| `expedition/real-standards-observatory` | showcase tip | `EXPEDITION_CANDIDATE_PENDING_EXTERNAL_AUDIT` |
| `expedition/corpus-foundry-24h` | foundry tip | `CORPUS_FOUNDRY_CANDIDATE_PENDING_EXTERNAL_AUDIT` |

Update this file when tips change after packaging.
