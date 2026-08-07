# NormShift

Evidence-backed **semantic diff** for technical standards (local HTML M0 core).

> **Status:** M0 trust-core repair (round 4). Production/release **BLOCKED**.  
> M1/M2 code may exist as **EXPERIMENTAL_NOT_ADJUDICATED** only.  
> See `docs/EXTERNAL_AUDIT_R3_FINAL.md` and `docs/GROK_M0_REPAIR_ROUND4.md`.

## Setup

```bash
uv sync --frozen --all-extras --dev
```

## CLI

```bash
uv run normshift extract DOC.html --profile rfc2119 --out out.requirements.json
uv run normshift diff OLD.html NEW.html --profile rfc2119 \
  --source-root . \
  --json report.json --markdown report.md
uv run normshift verify report.json --source-root .
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl --out metrics.json
```

### Portable source identity (`--source-root`)

- Reports store **portable** POSIX source references relative to a declared root.
- Generation: `normshift diff ... --source-root ROOT` resolves OLD/NEW under `ROOT`, rejects traversal and symlink escape, and never emits an absolute path with `source_ref_mode=source_root_relative`.
- When `--source-root` is omitted, the process CWD is the root; sources outside CWD fail closed.
- Verify: `normshift verify report.json --source-root ROOT` resolves declared refs under `ROOT`.

### Override scope (`--old-source` / `--new-source`)

- Overrides relocate source **bytes** for content replay; they do **not** attest the declared logical path.
- Declared refs in the report must still be portable relative paths (absolute/traversal rejected).
- Successful verify always prints a machine-readable scope:
  - `verification_scope=FULL` — normal source-root resolution
  - `verification_scope=CONTENT_ONLY_OVERRIDE` — override path(s) used
- Exit code: `0` only on success; non-zero on any failure (including strict JSON rejection).

## Verification gate (M0)

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure --ground-truth benchmark/measure_suite.jsonl \
  --out evidence/m0-repair-round4/metrics.json
uv run normshift diff fixtures/synthetic/spec-v1.html fixtures/synthetic/spec-v2.html \
  --source-root . \
  --profile rfc2119 \
  --json evidence/m0-repair-round4/report.json \
  --markdown evidence/m0-repair-round4/report.md
uv run normshift verify evidence/m0-repair-round4/report.json --source-root .
```

## License

Apache-2.0
