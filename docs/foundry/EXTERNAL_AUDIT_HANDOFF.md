# External Audit Handoff — Corpus Foundry 24h

## Package

`NormShift-Foundry-24h-Package.zip` containing:

- Source.zip (`git archive`)
- git bundle
- MANIFEST.json (+ sha256 sidecars)

## Start / branch

| Field | Value |
|-------|--------|
| Branch | `expedition/corpus-foundry-24h` |
| Parent expedition tip | `f80b3f631a85c635903570fd63b494ec95c89571` |
| Frozen M0 baseline | `878bfd3a6bb7b649652e81936216277fc8151d5e` |

## Max claim

`CORPUS_FOUNDRY_CANDIDATE_PENDING_EXTERNAL_AUDIT`

## Suggested checks

```text
uv sync --frozen --all-extras --dev
uv run pytest -q
uv run normshift campaign validate config/campaigns/foundry-24h.json
uv run normshift campaign run config/campaigns/foundry-24h.json --mode offline
# (offline requires prior local store for official URLs)
uv run normshift campaign verify artifacts/foundry-24h/run-manifest.json
uv run normshift capsule verify capsules/fixture-rfc
uv run normshift capsule verify capsules/w3c-trace-context
```

## Do not accept as

- Gold labels / EXTERNAL adjudication invented by implementer
- M0 R4/R5 debt closed
- Production readiness
