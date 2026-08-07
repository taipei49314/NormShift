# NormShift

Evidence-backed **semantic diff** for technical standards (local HTML M0 core).

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-M0%20repair-orange.svg)](docs/EXTERNAL_AUDIT_R4.md)

NormShift extracts normative statements from standards documents, diffs them
across versions with portable source identity, and verifies that a report still
matches the source bytes it claims. Built for **adjudicable** change analysis —
not "LLM said these paragraphs look similar."

> **Status:** M0 trust-core repair (round 5). Production/release **BLOCKED**.  
> M1/M2 code may exist as **EXPERIMENTAL_NOT_ADJUDICATED** only.  
> See `docs/EXTERNAL_AUDIT_R4.md` and `docs/GROK_M0_REPAIR_ROUND5.md`.

## Why this exists

Technical standards change quietly: a SHOULD becomes a MUST, a condition is
narrowed, a requirement is relocated. Line-oriented diffs bury that under noise;
model summaries invent confidence without source binding.

NormShift aims for:

| Goal | Approach |
|---|---|
| **Semantic units** | Extract requirement-like statements (e.g. RFC 2119 profile) |
| **Portable identity** | Reports store root-relative POSIX refs, not absolute machine paths |
| **Replayable verify** | `normshift verify` re-resolves sources and checks the report |
| **Fail closed** | Traversal, symlink escape, and broken scope do not become silent passes |

## Setup

```bash
git clone https://github.com/taipei49314/NormShift.git
cd NormShift
uv sync --frozen --all-extras --dev
```

## Sixty-second demo

```bash
# Diff two synthetic fixture specs
uv run normshift diff \
  fixtures/synthetic/spec-v1.html fixtures/synthetic/spec-v2.html \
  --profile rfc2119 \
  --source-root . \
  --json report.json --markdown report.md

# Re-verify the report against source under the same root
uv run normshift verify report.json --source-root .
```

Typical markdown report fragments look like requirement-level adds/removes/changes
with source refs, not a free-form essay. Treat metrics as **local evidence**, not
a published precision claim, until M0 is unblocked.

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
  --out evidence/m0-repair-round5/metrics.json
uv run normshift diff fixtures/synthetic/spec-v1.html fixtures/synthetic/spec-v2.html \
  --source-root . \
  --profile rfc2119 \
  --json evidence/m0-repair-round5/report.json \
  --markdown evidence/m0-repair-round5/report.md
uv run normshift verify evidence/m0-repair-round5/report.json --source-root .
```

## What this is not

- Not a general HTML pretty-diff for arbitrary web pages
- Not production-ready standards tooling (M0 still blocked)
- Not an LLM summarizer of RFCs

## License

Apache-2.0
