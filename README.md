# NormShift

Evidence-backed **semantic diff** for technical standards — local HTML M0 core.

> **External re-audit round 2:** implementer status  
> `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` after source-replay verify + rollback-safe commits.  
> M1/M2 = `EXPERIMENTAL_NOT_ADJUDICATED`. Production/release: **BLOCKED**.  
> See `docs/EXTERNAL_REAUDIT.md` and `docs/M0_REPAIR_ROUND2.md`.

## Status

| Layer | Status |
|-------|--------|
| M0 | Repair round 2 complete — **pending external re-audit** |
| M1 / M2 | **Experimental only** — not adjudicated |

## Setup

```bash
uv sync --all-extras --dev
```

## CLI

```bash
uv run normshift extract DOC.html --profile rfc2119 --out out.requirements.json
uv run normshift diff OLD.html NEW.html --profile rfc2119 --json report.json --markdown report.md
uv run normshift verify report.json --source-root .
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl --out metrics.json
```

Profiles: `rfc2119`, `whatwg`. Adapters (experimental): `--adapter auto|html|rfc|w3c|whatwg`.

## Verification gate (M0 repair)

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl --out evidence/m0-repair/metrics.json
uv run normshift diff fixtures/synthetic/spec-v1.html fixtures/synthetic/spec-v2.html \
  --profile rfc2119 --json evidence/m0-repair/report.json --markdown evidence/m0-repair/report.md
uv run normshift verify evidence/m0-repair/report.json --source-root .
```

## License

Apache-2.0
