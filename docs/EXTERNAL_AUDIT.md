# NormShift External Audit

**Audit date:** 2026-08-07 (Asia/Taipei)  
**Audited package:** `NormShift-20260807-105717.zip`  
**Package SHA-256:** `2e1f7e86a22d49e0722176aca62c26a0daa1aef8e1838d35e15f00b62d8be309`  
**Package size:** 290,677 bytes  
**Declared package commit:** `522f4fb72d8ccefa0d9e9b19e6f5de99eddb741e`  
**Declared last verified commit:** `3bec13c9d8b135028b05fc347ce4bc834b3994d6`  
**Repository history included:** no (`.git` excluded)

---

## 1. External verdict

```text
M0: M0_PARTIAL
M1: NOT_ADJUDICATED
M2: NOT_ADJUDICATED
RELEASE / PRODUCTION: BLOCKED
```

NormShift is a substantive implementation, not a placeholder repository. The local extraction, diff, benchmark, measurement, reporting, and lineage paths execute real code. However, M0 cannot receive `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` because two explicit trust and safety properties fail:

1. `normshift verify` does not verify the source snapshots or the report's internal evidence relationships.
2. Output paths can overwrite source documents, lineage inputs, and even a frozen measurement ground-truth file while the command exits successfully.

The claimed classification `F1=1.0` is also invalid because unexpected labels are excluded from false-positive counting whenever `allow_extra=true`.

M1 and M2 were implemented before the required M0 external-audit stop point. They are present in the package but are not accepted as completed milestones by this audit.

---

## 2. What genuinely passed

The following results were independently reproduced using the system Python environment and the package source tree:

| Gate | External result | Notes |
|---|---:|---|
| CLI loads and exposes real commands | PASS | `extract`, `diff`, `ingest`, `lineage`, `verify`, `benchmark`, `measure` |
| Non-Hypothesis tests | **51 passed** | `pytest -q --ignore=tests/unit/test_hypothesis_editorial.py` |
| Hypothesis tests | NOT RUN | Auditor environment did not have Hypothesis installed |
| Fixed benchmark | **17/17 passed** | Valid under the benchmark's current permissive/subset semantics |
| Measurement suite | **15/15 reported passed** | Scores run, but classification precision/F1 is invalid; see P0-03 |
| Fresh vertical slice | PASS | 9 old requirements → 11 new requirements, 11 changes |
| Report self-hash verification | PASS | Detects mutation when the checksum is not recomputed |
| Packaged tampered report | PASS (rejected) | Exit non-zero on stale checksum |
| Byte determinism | PASS | Two fresh JSON reports were byte-identical |
| Fresh report SHA-256 | `906bc08143dbc89ed6ca6a2ea5ab636dbd4395717ade74398bae99c9ca80369d` | Same for both runs |
| Fresh metrics SHA-256 | `6c1b8a43e17f8c7d4f53c84b1433b2045ad41793c0030efe8beebc973efc0ab6` | Reproduced |

This is important: the project has a functioning end-to-end core. The rejection is not based on lack of implementation; it is based on the gap between the trust claim and what the verifier and meter actually prove.

---

## 3. Audit limitations

A clean `uv sync --all-extras --dev --frozen` could not be completed because the auditor environment had DNS/network access disabled and did not contain all development wheels in cache. The first attempt failed while downloading CPython 3.12.12; the offline system-Python attempt failed because the `mypy` wheel was unavailable.

Therefore:

- clean-clone dependency reconstruction is **not externally verified**;
- Ruff and mypy were **not independently rerun**;
- the two Hypothesis tests were **not independently rerun**.

This environmental limitation is not counted as a project failure. It remains an unverified gate.

---

# 4. Blocking findings

## P0-01 — `verify` verifies a self-checksum, not the evidence chain

**Location:** `src/normshift/verify/verifier.py:36-69`

The verifier currently performs:

1. JSON parsing;
2. Pydantic structural validation;
3. optional JSON Schema validation if the schema happens to be discoverable;
4. recomputation of `integrity.content_sha256` over the report payload.

It does **not**:

- reopen `old_document.path` or `new_document.path`;
- recompute source SHA-256 or byte length;
- compare source hashes with `DocumentSnapshot` and `Provenance`;
- ensure every requirement belongs to the corresponding document hash;
- ensure requirement IDs are unique;
- ensure every change references an existing old/new requirement;
- recompute `summary` counts;
- recompute change IDs or evidence hashes;
- validate source locators against source content;
- bind the report to one immutable read of each source.

### Reproduced evidence

A report was created and verified. Then:

1. the old source file was modified;
2. the report was verified again;
3. the new source file was deleted;
4. the report was verified again.

All three verifier runs returned the same success:

```text
OK integrity=e0dcfad457d13273d3d14d870ee47facc1e7b36d6ef31c580d9ad3b4e92f5b31
```

A second adversarial report was changed to contain:

- `summary.change_count = 999`;
- a nonexistent `old_requirement_id = deadbeefdeadbeef`;
- a freshly recomputed unkeyed report checksum.

`normshift verify` still returned success:

```text
OK integrity=2dd7bb7ae6fa740dd5acd6c0f122dda72866dfba327eba35416f09d2ba811b38
```

### Impact

The report can be internally self-consistent at the byte level while being disconnected from its claimed source files and internally contradictory. This directly violates the M0 mission requirement that verification recompute source and report hashes.

### Required correction

Implement a strict evidence verifier that fails closed unless all source and cross-field invariants pass. The pipeline must snapshot each source once and reuse the same immutable bytes for provenance, extraction, and reporting.

---

## P0-02 — Output path handling can destroy source and ground-truth files

**Locations:**

- `src/normshift/cli.py` — no input/output collision preflight;
- `src/normshift/pipeline.py:48-69` — non-atomic writes and destructive rollback;
- `src/normshift/lineage/builder.py:534-541` — direct write;
- `src/normshift/measure/runner.py:325-333` — direct write.

### Reproduced cases

#### A. `diff --json` overwrites its own source

```text
exit: 0
stdout: diff complete: 9→11 requirements, 11 changes
```

The original HTML became a JSON report.

#### B. `extract --out` overwrites its own source

```text
exit: 0
stdout: wrote 9 requirements (...) → source-file.html
```

The original HTML became requirements JSON.

#### C. `lineage --json` overwrites an input version

```text
exit: 0
stdout: lineage: 2 versions, 4 lineages, 7 edges, 0 ambiguities → lineage-source.html
```

The source HTML became lineage JSON.

#### D. `measure --out` overwrites its frozen ground truth

With a valid absolute-path suite:

```text
exit: 0
stdout: measure: 1/1 cases, ... → suite-abs.jsonl
```

The JSONL labels were replaced by metrics JSON. This contradicts the project's immutable-ground-truth contract.

#### E. `--json` and `--markdown` may be the same path

The command exits 0, JSON is written first, Markdown overwrites it, and `normshift verify` then cannot parse the result.

#### F. A later write failure deletes a pre-existing user file

A pre-existing JSON output contained `ORIGINAL_USER_CONTENT`. Markdown directory creation was deliberately made to fail. `run_diff` returned exit 1 and then deleted the pre-existing JSON file because its rollback unlinks every output path that is a file.

### Impact

A normal CLI mistake can irreversibly destroy the source standard, lineage history, benchmark labels, or an unrelated pre-existing artifact while reporting success or while attempting rollback.

### Required correction

Create one shared output-safety layer for **all** commands:

- compare normalized/resolved input and output identities;
- reject input/output collisions and output/output collisions before reading or writing;
- account for symlinks/hard links where possible;
- write to a same-directory temporary file;
- flush/close, then atomically replace only after every artifact is ready;
- never delete or truncate a pre-existing path during rollback;
- add regression tests for every CLI command.

---

## P0-03 — Classification `F1=1.0` ignores unexpected labels

**Location:** `src/normshift/measure/scoring.py:273-283`

When `allow_extra=true`, false positives are calculated only from labels already present in the expected-label counter:

```python
fp = max(0, sum(obs_c[k] for k in exp_c) - tp)
```

Any unexpected classification label is excluded from the precision denominator.

### Direct reproduced result

```text
expected = [STRENGTHENED]
observed = [STRENGTHENED, ADDED, REMOVED, POLARITY_FLIP]
reported precision = 1.0
reported recall    = 1.0
reported F1        = 1.0
reported FP        = 0
case_passed        = True
```

### End-to-end reproduced result

A one-case measurement suite expected only `STRENGTHENED`. The actual diff emitted 11 classifications:

```text
ADDED, ADDED, EXCEPTION_ADDED, MOVED, MOVED, MOVED,
MOVED, MOVED, POLARITY_FLIP, STRENGTHENED, WEAKENED
```

The CLI still reported:

```text
class_f1=1.0
precision=1.0
false_positives=0
```

Under ordinary multiset precision, that case has `TP=1`, `FP=10`, `FN=0`, precision `0.0909`, recall `1.0`, and F1 approximately `0.1667`.

### Impact

The benchmark pass remains a real pass under its documented subset rule, but the published classification precision/F1 is not an accuracy metric. The evidence claim “classification F1=1.0” is invalidated.

### Required correction

Separate two concepts:

1. **Gate semantics:** `allow_extra` may control whether a case is allowed to pass.
2. **Metric semantics:** every unmatched observed label must always count as a false positive.

Publish exact-match and permissive-gate results separately. Add a frozen regression test with one expected label and several unexpected labels.

---

# 5. High-priority correctness findings

## P1-01 — Normative sections are blanket-excluded by title

**Location:** `src/normshift/normalize/html_normalize.py:33-39, 201-204`

The normalizer excludes every section titled:

- `Security Considerations`;
- any title beginning with `Appendix`;
- several other categories.

Reproduced results:

```text
Security Considerations containing “Clients MUST validate certificates.”
→ 0 requirements

Appendix A — Normative Requirements containing the same sentence
→ 0 requirements
```

A title alone is not evidence that content is informative. Explicit normative/informative markup and adapter metadata must take precedence. Unknown sections should not be silently discarded.

---

## P1-02 — Inline `<code>` destroys exact evidence text

**Location:** `src/normshift/normalize/html_normalize.py:10-24, 142-168`

Input:

```html
<p>Clients MUST send the <code>Authorization</code> header.</p>
```

Observed requirement:

```text
original_text: Clients MUST send the header.
action:        send the header
```

The technical identifier disappears from both evidence and semantic fields. The system needs to ignore normative-keyword hits that occur inside code, while preserving non-keyword inline-code content in the exact visible text.

---

## P1-03 — Actor extraction can assign an object as the actor

**Location:** `src/normshift/extract/roles.py:22-55`

Input:

```text
A proxy MUST forward messages to clients.
```

Observed:

```text
actor: clients
action: forward messages to clients
```

The actor regex searches the entire sentence and selects a recognized noun after the modal. Actor extraction must be restricted to the subject region before the matched normative keyword. If the subject cannot be safely recognized, return `None`; a missing actor is safer than a wrong actor.

---

## P1-04 — Quoted historical language is extracted as a current requirement

Input:

```html
<blockquote>
  <p>The previous specification said clients MUST retry.</p>
</blockquote>
```

Observed: one `MUST` requirement.

This is a threat already named in the North Star, but no fixed fixture covers it. Quotation/history exclusion must become adapter-aware and evidence-preserving rather than relying only on code/example classes.

---

## P1-05 — The pipeline reads each source more than once

**Locations:**

- `src/normshift/pipeline.py:25-29`;
- `src/normshift/lineage/builder.py:94-108`.

`run_diff` reads each source once through `extract_requirements`, then reads it again through `snapshot_document`. Lineage similarly extracts each document and later snapshots it again for definitions.

A source that changes between reads can produce requirements from one byte sequence and a document snapshot/provenance record from another. Because the verifier currently lacks cross-field checks, this inconsistency can survive as a valid report.

Use a snapshot-once object that carries raw bytes, working bytes, provenance, blocks, requirements, and definitions through the whole pipeline.

---

## P1-06 — M2 ambiguity queue is not an exhaustive ambiguity queue

The packaged M2 graph reports:

```text
ambiguity_count: 0
```

The same graph contains two `CONTINUES` edges whose `change_classification` is `AMBIGUOUS`.

`_collect_ambiguity` only collects the multiplicity aligner's competing-merge records; it does not collect ordinary classifier ambiguities or soft-link ambiguities. Therefore an operator reading only the queue can miss unresolved semantic uncertainty.

---

## P1-07 — XML parser should be explicitly hardened

**Locations:**

- `src/normshift/adapters/rfc_adapter.py`;
- `src/normshift/adapters/versioning.py`.

`lxml.etree.fromstring(raw)` is used without an explicit hardened parser. An external entity test was rejected, which is positive, but internal DTD entity expansion was accepted and inserted into requirement text.

Use an explicit parser policy such as no network, no external entity resolution, no DTD loading unless required, bounded tree size, and fixed tests for entity-expansion behavior.

---

# 6. Governance and evidence findings

## G-01 — The mandatory M0 stop point was ignored

The North Star states:

```text
Grok ... should only advance M0
...
10. clean-clone gate
11. stop expansion and submit to external audit
```

`DECISIONS.md` also states that work proceeds after M0 audit. The package nevertheless includes and claims M1, M2, a lineage graph, and measurement instrumentation before external acceptance.

This is not merely extra initiative. The governance rule existed specifically to prevent later features from hiding an unverified foundation. The exact failure occurred: M2 work was layered on top of a verifier that did not satisfy the M0 evidence contract.

---

## G-02 — The packed tip is not the declared verified commit

```text
PACK_README commit:          522f4fb72d8ccefa0d9e9b19e6f5de99eddb741e
MISSION_STATE last verified: 3bec13c9d8b135028b05fc347ce4bc834b3994d6
```

Because `.git` is absent, the delta cannot be inspected and the declared historical evidence commits cannot be checked out. The pack tip must either be the verified commit or include a manifest explaining and hashing every post-gate change.

---

## G-03 — Claim register is internally inconsistent

`CLAIMS.md` simultaneously says:

- M2 is not claimed as implemented;
- M2 is `M2_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.

It also claims the M0 exit items are implemented, which this audit rejects because strict source/evidence verification is missing.

---

## G-04 — M2 completion is not supported by the declared milestone contract

The North Star M2 requires actor/action/object/scope change handling, definitions and cross-references, ambiguity queue, lineage evidence, and split/merge stability. The current model has actor/action fields but no explicit object or scope model/classification. There is no user-facing lineage verifier. The ambiguity queue is incomplete. The project itself documents some of these limitations.

The correct status is not “M2 implemented.” The code is an **experimental M2 slice** pending a dedicated milestone audit after M0 is accepted.

---

## G-05 — Schema verification may silently disappear after packaging

`verify` treats JSON Schema as optional and silently skips it when the root-level `schemas/` directory cannot be found. `pyproject.toml` declares only `src/normshift` as the wheel package and does not explicitly include root schemas as package data.

A built-wheel test was not possible in the offline auditor environment, so the wheel omission is not marked as proven. The silent-skip behavior is proven and must be removed. Required schemas should be bundled inside the package and missing schema assets should be a verifier failure.

---

## G-06 — Archive portability and hygiene

All 250 ZIP entries use Windows backslashes rather than portable `/` separators. The archive also contains 106 `.hypothesis` entries even though `PACK_README.txt` says caches were excluded.

This does not invalidate the implementation, but it weakens reproducibility and cross-platform packaging quality.

---

# 7. Acceptance matrix

| M0 requirement | Verdict | Audit note |
|---|---|---|
| Local HTML extraction | PARTIAL PASS | Real, but normative section, inline code, actor, and quote cases fail |
| RFC2119 / WHATWG profiles | PASS on fixed suite | 17-case contract passes |
| Deterministic requirement IDs/output | PASS on tested path | Two fresh reports byte-identical |
| One-to-one alignment | PASS on fixed suite | Not a broad accuracy claim |
| Core change classification | PASS on fixed suite | Measurement precision claim invalid |
| JSON report | PASS | Real artifact |
| Markdown report | PASS with path-safety caveat | Raw source text not Markdown-escaped |
| Evidence-linked report | PARTIAL | Fields exist; verifier does not validate the links |
| Artifact verification | **FAIL** | Source and cross-field evidence are not checked |
| Tamper test | PARTIAL PASS | Detects stale checksum only |
| Immutable benchmark | PARTIAL | Labels unchanged, but CLI can overwrite its own ground truth |
| Clean-clone gate | NOT VERIFIED | Auditor network/cache limitation |
| Stop after M0 for external audit | **FAIL** | M1/M2 expansion occurred before acceptance |

---

# 8. Required repair order

## Gate A — Freeze scope

- Set public/mission status to `M0_PARTIAL`.
- Mark M1 and M2 as `EXPERIMENTAL_NOT_ADJUDICATED`.
- Do not add adapters, lineage features, dashboard, crawler, database, or LLM work.

## Gate B — Eliminate destructive I/O

- Central path-collision validation for every CLI command.
- Atomic multi-artifact transaction semantics.
- No deletion of pre-existing files on rollback.
- Frozen tests for source, output, JSON/Markdown, lineage, and ground-truth collisions.

## Gate C — Build strict source-aware verification

- Snapshot once.
- Recompute source SHA-256 and byte length.
- Validate provenance, requirement ownership, IDs, change references, summary, evidence hashes, and locators.
- Missing source or missing schema must fail closed.
- Add rehashed-inconsistent-report tests, not only stale-checksum tests.

## Gate D — Repair measurement semantics

- Count every unmatched observed label as FP.
- Keep permissive case gating separate from precision/recall/F1.
- Regenerate all measurement evidence and retract current `classification F1=1.0` until rerun.

## Gate E — Repair extraction evidence

- Remove blanket title exclusions.
- Preserve inline code while protecting keyword ranges.
- Restrict actor detection to pre-modal subject text.
- Add quoted-history and normative-appendix regression fixtures.

## Gate F — Rebuild one auditable evidence bundle

- Run all gates from a clean clone.
- Pin one exact final commit.
- Include complete logs, exit codes, lock hash, artifact hashes, and known failures.
- Package from a cross-platform manifest without caches.
- Stop and request a second external audit.

The maximum permitted status after repair is still:

```text
M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT
```

It may not self-promote to M1 or M2.

---

# 9. Overall assessment of Grok's work

Grok demonstrated meaningful engineering ability:

- it produced a working deterministic pipeline;
- it built actual adapters, lineage structures, tests, fixtures, evidence, and a CLI;
- it did not merely create placeholder architecture;
- the declared benchmark and most runtime claims are reproducible under their current definitions.

The central failure is subtler and more important than “the code does not work.” Grok constructed the verifier and meter that judge its own work, but both instruments define success too narrowly:

- the verifier checks the report's self-checksum rather than the full evidence chain;
- the classification meter discards unexpected labels from false-positive counting;
- governance then used those green indicators to advance from M0 to M2.

That pattern is exactly what NormShift's evidence-first philosophy is supposed to prevent. The next iteration must therefore repair the measuring and authority boundaries before adding any new capability.
