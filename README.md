# NormShift (M0)

Evidence-backed **semantic diff** for technical standards — local HTML vertical slice.

NormShift tracks how **normative requirements** change between document versions
(MUST / SHOULD / MAY and relatives), not merely which words changed.

> M0 status values are limited to `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`,
> `M0_PARTIAL`, or `M0_BLOCKED`. This project does **not** claim production or
> release readiness.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

## Setup

```bash
uv sync --all-extras --dev
```

## CLI

```bash
uv run normshift extract OLD.html --profile rfc2119 --out artifacts/old.requirements.json

uv run normshift diff OLD.html NEW.html \
  --profile rfc2119 \
  --json artifacts/report.json \
  --markdown artifacts/report.md

uv run normshift verify artifacts/report.json

uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
```

Profiles: `rfc2119`, `whatwg`.

## Verification gate

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
```

## Vertical slice demo

```bash
uv run normshift diff \
  fixtures/synthetic/spec-v1.html \
  fixtures/synthetic/spec-v2.html \
  --profile rfc2119 \
  --json evidence/m0/report.json \
  --markdown evidence/m0/report.md

uv run normshift verify evidence/m0/report.json
```

## Design docs

- [North Star charter](docs/NORTH_STAR.md) — product end-state, milestones M0–M6, governance
- [Semantic model](docs/SEMANTIC_MODEL.md) — M0 operational model (subset of full taxonomy)
- [Threat model](docs/THREAT_MODEL.md)
- [Benchmark method](docs/BENCHMARK_METHOD.md)
- [Decisions](DECISIONS.md)
- [Claims](CLAIMS.md)

**Current implementer status:**  
- M0 — `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`  
- M1 — `M1_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`  

Adapters: `--adapter auto|html|rfc|w3c|whatwg`. Offline corpus: `fixtures/corpus/`.  
`normshift ingest` writes provenance JSON. No live crawler (M3).

## License

Apache-2.0
