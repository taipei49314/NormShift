# NormShift

Evidence-backed **semantic diff** for technical standards (local HTML M0 core).

> **Status:** M0 trust-core repair (round 3). Production/release **BLOCKED**.  
> M1/M2 code may exist as **EXPERIMENTAL_NOT_ADJUDICATED** only.  
> See `docs/EXTERNAL_AUDIT_R2.md` and `docs/M0_REPAIR_ROUND3.md`.

## Setup

```bash
uv sync --frozen --all-extras --dev
```

## CLI

```bash
uv run normshift extract DOC.html --profile rfc2119 --out out.requirements.json
uv run normshift diff OLD.html NEW.html --profile rfc2119 \
  --json report.json --markdown report.md
uv run normshift verify report.json --source-root .
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl --out metrics.json
```

Reports store **portable** POSIX source references (not generation-machine absolute paths).
Verify with explicit `--source-root` after relocating a checkout.

## Verification gate (M0)

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl \
  --out evidence/m0-repair-round3/metrics.json
uv run normshift diff fixtures/synthetic/spec-v1.html fixtures/synthetic/spec-v2.html \
  --profile rfc2119 \
  --json evidence/m0-repair-round3/report.json \
  --markdown evidence/m0-repair-round3/report.md
uv run normshift verify evidence/m0-repair-round3/report.json --source-root .
```

## License

Apache-2.0
