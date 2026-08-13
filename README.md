# NormShift

Evidence-backed **semantic diff** for technical standards (local HTML M0 core).

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-M1%2FM2%20experimental-orange.svg)](CLAIMS.md)

NormShift extracts normative statements from standards documents, diffs them
across versions with portable source identity, and verifies that a report still
matches the source bytes it claims. Built for **adjudicable** change analysis —
not "LLM said these paragraphs look similar."

> **Status:** The exact M0 package at `b3af3dc...` has a detached historical
> `M0_EXTERNAL_AUDIT_PASS`; that verdict applies only to that package. Current
> master adds M1 policy/acquisition/scorer/development-recipe/governance work and
> M2 graph and typed semantic-dimensions foundations, all
> **EXPERIMENTAL_NOT_ADJUDICATED**. It also includes the
> strict canonical-wheel and three-OS distribution-equality delivery foundation
> from [#14](https://github.com/taipei49314/NormShift/pull/14), verified internally
> on ancestor master commit `f6897f71834a50d2273fda033a72b31254c65935`; that
> CI evidence is not an
> external verdict. The combined
> exact-subject audit and final software release remain **BLOCKED**. See
> [`CLAIMS.md`](CLAIMS.md), [`CHANGELOG.md`](CHANGELOG.md), and
> [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md).

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
a published M1/M2 precision or acceptance claim, until the combined exact subject
passes its independent gates.

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

## Experimental M1 source acquisition

The strict source-acquisition primitive is documented in
`docs/M1_SOURCE_ACQUISITION.md`. It binds a reviewer-frozen policy and curator
source manifest before pinned reacquisition, commits only after every
source/provenance/adapter check succeeds, and replays those source bindings offline.
It does **not** include labels, inspect holdouts, run M1 quality measurement, or claim
M1 acceptance.

The synthetic-tested labeling and blind-split governance primitive is documented in
`docs/M1_M2_GOVERNANCE_CONTRACT.md`. It verifies neutral reviewer packets, independent
submissions, retained adjudication history, whole-document/whole-lineage split rules,
candidate-freeze/pre-prediction ordering, source-scope binding, independent reviewer
authority, and portable exact-root custody. V1 fails closed on post-result corrections
until a separate evaluation-attempt trust anchor exists. It contains no actual labels or
holdout membership and cannot grant M1/M2 acceptance.

## Experimental M2 semantic dimensions

The versioned semantic-dimensions foundation is documented in
`docs/M2_SEMANTIC_DIMENSIONS_FOUNDATION.md`. It can describe move/rewrite form
and eight independent semantic slots while retaining exact requirement
provenance from a typed-receipt FULL source replay and the unchanged primary M0
classification. It is not embedded in the M0 report or standard `diff`/`verify`
flow; caller object/scope spans remain unverified `UNKNOWN` candidates and
cannot emit classes. The separate opt-in `semantic-dimensions build` and
`semantic-dimensions verify` commands use canonical sidecars only through a
FULL source-replay binding; they do not alter the M0 report format or its bytes.
`build` writes exact canonical bytes only to binary standard output, leaving
capture, storage, and SHA-256 computation to an external custodian; that stream
is not custody or atomic-file authority. Capture must preserve bytes; Windows
PowerShell text pipelines or text redirection can transcode Unicode and are not
safe capture mechanisms. Discard any capture from a nonzero command exit, then
hash a successful capture externally before `verify`. The commands require pre-existing
receipts and caller-provided report, receipt, and sidecar SHA-256 anchors as
applicable, but those anchors do not prove independent custody or adjudication.
Neither command claims M2 acceptance.

`normshift verify-lineage GRAPH DOC... --graph-sha256 SHA --profile PROFILE
--adapter ADAPTER` is a separate opt-in LineageGraph v1 check. It reads the graph
and each ordered document through bounded descriptor-stable snapshots, rejects a
bad external graph digest, strict/canonical/schema/integrity failure before any
source replay, and compares a fresh isolated replay byte-for-byte. A success is
explicitly `LINEAGE_GRAPH_REPLAY_ONLY external_acceptance=false`: it binds only
the caller-supplied ordered source bytes, profile, and adapter. It deliberately
does not assert source custody, official identity, adjudication, or M2 acceptance.

## What this is not

- Not a general HTML pretty-diff for arbitrary web pages
- Not production-ready standards tooling (the combined M0-M2 release is blocked)
- Not an LLM summarizer of RFCs

## License

Apache-2.0
