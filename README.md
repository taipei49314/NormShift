# NormShift

### Evidence-backed semantic diff for technical standards

[![CI](https://img.shields.io/badge/CI-github%20actions-blue)](.github/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-experimental-orange)](#status)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

**NormShift tells you what actually changed in a standard — with source locators you can re-verify offline.**

Not a chatbot. Not an embedding search. A **deterministic pipeline**:

```text
HTML snapshots → extract obligations → align versions → classify changes → evidence report → replay verify
```

---

## The problem

Standards evolve in silence:

| Quiet change | Why it hurts |
|--------------|--------------|
| `SHOULD` → `MUST` | Compliance scope explodes overnight |
| New condition / exception | Implementations become non-conformant |
| Moved + reworded clause | Reviewers think nothing changed |
| Historical “previous specification said MUST…” | Naïve extractors invent false requirements |

Teams need a **local, reproducible** instrument — not another cloud LLM that cannot prove source binding.

---

## 30-second demo

```bash
uv sync --frozen --all-extras --dev

uv run normshift diff \
  fixtures/corpus/rfc/sample-v1.html \
  fixtures/corpus/rfc/sample-v2.html \
  --source-root . --adapter rfc --profile rfc2119 \
  --json /tmp/normshift.json --markdown /tmp/normshift.md

uv run normshift verify /tmp/normshift.json --source-root .
# OK integrity=… verification_scope=FULL

uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
# 17/17
```

Open `/tmp/normshift.md` — every change points back to source text and locators.

---

## What you get

| Capability | Detail |
|------------|--------|
| **Semantic classes** | STRENGTHENED, WEAKENED, POLARITY_FLIP, CONDITION/EXCEPTION, MOVED, ADDED/REMOVED, AMBIGUOUS… |
| **Source-bound verify** | Rebuild extraction→alignment→classification and compare canonical report bytes |
| **Portable evidence** | `--source-root` relative POSIX refs; relocate the repo and re-verify |
| **Override scope** | `--old-source` / `--new-source` print `verification_scope=FULL` or `verification_scope=CONTENT_ONLY_OVERRIDE` (exit 0 only on success) |
| **Strict JSON boundary** | Reject duplicate keys, non-finite numbers, coerced types (M0 trust path) |
| **Adapters** | RFC HTML/XML, W3C, WHATWG, generic HTML |
| **Expedition** | Allowlisted HTTPS acquire, lineage graph, static observatory |

---

## Real standards (expedition run)

On branch `expedition/real-standards-observatory`, live official captures (local store):

| Document | Extracted obligations (run-dependent) |
|----------|--------------------------------------:|
| RFC 9110 (HTTP Semantics) | **400+** |
| RFC 8949 (CBOR) | **40+** |
| RFC 8259 (JSON) via plain `<pre>` HTML | **20+** |
| W3C Trace Context L1 → L2 | **114** classified change events (ambiguity preserved) |

> Numbers are experimental extractions, not adjudicated gold labels.

```bash
# Optional: pull allowlisted official HTML into content-addressed store
uv run normshift acquire https://www.rfc-editor.org/rfc/rfc8259.html \
  --store .normshift/store --policy config/source-policy.json

# Full offline expansion script (uses store + fixtures)
uv run python scripts/expedition_expand.py
uv run python scripts/make_github_demo.py
```

Showcase write-up: [`docs/SHOWCASE.md`](docs/SHOWCASE.md) · Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Architecture (one screen)

```text
Acquire (HTTPS allowlist) ──► Snapshot store (SHA-256)
                                    │ offline
                              Adapters (RFC/W3C/WHATWG)
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
           Extract               Align+Classify        Lineage
              └─────────────────────┬─────────────────────┘
                                    ▼
                         Evidence report (JSON/MD)
                                    ▼
                         Verify = full pipeline replay
                                    ▼
                         Static observatory + feeds
```

Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## CLI map

```text
normshift extract | diff | verify | benchmark | measure
normshift acquire | snapshot show|verify|export
normshift inspect | adapter --out diagnostics.json
normshift lineage build|export|verify|graph
normshift observatory build|verify|poll
normshift benchmark-real
```

---

## Status

| Layer | Status |
|-------|--------|
| M0 trust core | Implementer packages through R4/R5 — **external audit decides** |
| Expedition (M1–M3-shaped) | **`EXPERIMENTAL_NOT_ADJUDICATED`** |
| Production / SaaS | **Not a goal of this repo state** |

We deliberately do **not** claim `AUDIT_PASSED`, `PRODUCTION_READY`, or gold-labeled accuracy.

Authority rules: implementer ≠ auditor. Labels: `AUTO` / `PROVISIONAL` only unless an external adjudicator says otherwise.

---

## Tests & gates

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift benchmark-real --root .
```

CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

---

## Project layout

```text
src/normshift/     pipeline, adapters, verify, acquire, lineage, observatory
fixtures/          synthetic + family corpus (redistributable)
benchmark/         frozen adversarial cases
corpus/            catalog + hash-only official snapshot index
artifacts/         expedition evidence (regenerable)
docs/              charter, architecture, showcase, audit handoffs
```

---

## Contributing / branch policy

- **`master`**: audited M0 packages — treat as frozen during external review.
- **`expedition/real-standards-observatory`**: ambitious observatory work; may move fast.
- Do not invent gold labels. Prefer failing closed and recording ambiguity.

---

## License

Apache-2.0

---

<p align="center">
  <b>Read the standard. Diff the obligations. Verify the evidence.</b>
</p>
