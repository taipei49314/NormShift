# GROK 4.5 REPAIR MISSION — ROUND 2
## Project: NormShift
## Mission: Close the remaining M0 evidence and transaction gaps

You are repairing the externally re-audited `NormShift-M0-Repair` candidate.

This is not feature development. M1, M2, M3, dashboards, crawlers, databases, LLMs, MCP, GitHub Apps, new adapters, and new product surfaces are frozen.

## Authority boundary

You are not Claim Authority, Evidence Authority, Audit Authority, or Release Authority.

Allowed final statuses:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Forbidden claims:

- COMPLETE
- VERIFIED
- AUDIT PASSED
- PRODUCTION_READY
- RELEASE_READY
- M1/M2 complete

Set public status to `M0_PARTIAL` before implementation. Do not restore the pending-audit status until every gate below is rerun on one exact clean commit.

---

# 1. Fixed external findings

Treat these as facts. Do not weaken tests, rename the contract, or argue that a self-consistent forged report is valid.

1. A rehashed report with an impossible source locator passes `verify`.
2. A rehashed report with fabricated requirement text passes `verify` while source bytes remain unchanged.
3. An arbitrary requirement ID passes after internal references are updated.
4. A paired semantic change with both requirement IDs null passes.
5. Forged provenance paths/canonical metadata pass.
6. Failure on the second final-file replacement overwrites the first pre-existing output.
7. `run_measure` reads each source twice within one case.
8. `class="non-normative"` content is extracted as normative.
9. Repeated identical text inside/outside `<code>` protects the wrong occurrence.
10. Inline `<q>` and plain historical quotation can be extracted as current requirements.
11. A forbidden classification label zeros valid TP/FN metrics instead of affecting only the gate.
12. Package commit and verified commit differ; no Git bundle or manifest proves the submitted tree.

---

# 2. Red tests first

Add these tests, or exact behavioral equivalents, before implementation. Record the failing baseline.

```text
test_verify_rejects_unresolvable_source_locator_after_rehash
test_verify_rejects_fabricated_requirement_text_after_rehash
test_verify_recomputes_requirement_id
test_verify_requires_both_ids_for_every_paired_class
test_verify_rejects_arbitrary_added_removed_change_id
test_verify_rejects_duplicate_change_ids
test_verify_rejects_duplicate_requirement_coverage
test_verify_validates_provenance_metadata
test_verify_replay_rejects_changed_classification_after_rehash

test_transaction_restores_first_output_when_second_replace_fails
test_transaction_removes_only_new_files_created_by_this_invocation
test_transaction_restores_all_preexisting_outputs_after_commit_failure

test_measure_reads_each_source_once_per_case

test_non_normative_class_is_informative
test_exact_normative_class_token_is_normative
test_repeated_inline_code_token_protects_the_code_occurrence
test_inline_q_historical_requirement_is_not_authoritative
test_plain_historical_quote_is_conservative_or_ambiguous

test_forbid_changes_gate_not_tp_fp_fn

test_package_revision_equals_verified_revision
test_claims_pin_exact_verified_commit
```

Do not skip, xfail, delete, or relabel these tests to obtain green status.

---

# 3. Workstream A — deterministic source replay in `verify`

Do not patch the verifier with more report-to-report comparisons. The core defect is that both sides of each comparison currently come from the same untrusted report.

`normshift verify REPORT` must perform deterministic replay.

## Required sequence

1. Parse and schema-validate the report.
2. Validate canonical report self-hash.
3. Resolve old/new sources only through:
   - explicit `--old-source` / `--new-source`; or
   - the exact declared relative path under explicit `--source-root`; or
   - an explicitly defined immutable embedded snapshot mode.
4. Do not fall back to basename guessing.
5. Load each source exactly once as `ImmutableSource`.
6. Recompute and compare raw hash, byte length, version, document family, adapter identity, normalization version, and provenance.
7. Re-run extraction from those immutable objects using the report profile.
8. Compare the complete canonical old/new requirement arrays to the report:
   - requirement ID;
   - document hash/version;
   - section path;
   - source locator;
   - original and normalized text;
   - modality and polarity;
   - actor/action/condition/exception;
   - confidence;
   - extractor version;
   - fingerprint;
   - structural index.
9. Re-run alignment and classification from the replayed requirements.
10. Compare complete canonical changes, including IDs, references, classifications, reasons, locators, texts, modality transitions, evidence hashes, alignment scores, and section paths.
11. Recompute summary and compare it.
12. Fail closed on every mismatch.

This replay must reject all provided forged reports without relying on their stale self-hash.

## Referential invariants

Independently enforce:

- requirement IDs unique per side;
- change IDs unique;
- ADDED: old ID null, new ID valid;
- REMOVED: new ID null, old ID valid;
- every other classification: both IDs non-null and valid;
- one requirement occurrence cannot be silently consumed by multiple ordinary one-to-one changes;
- unknown or duplicate references fail;
- all change IDs are recomputed, including ADDED and REMOVED;
- provenance local/canonical metadata conforms to documented structure.

Do not claim cryptographic authenticity. This is deterministic source-bound replay with unkeyed hashes.

---

# 4. Workstream B — rollback-safe multi-artifact commit

The current staging design is acceptable; the commit phase is not.

Implement a transaction journal that preserves user files when any replacement fails.

Required behavior:

1. Serialize and validate all artifacts in memory.
2. Stage and fsync all temporary files in their destination directories.
3. For every existing final path, move it to a unique transaction-owned backup.
4. Replace finals.
5. If any backup or replacement fails:
   - restore every pre-existing final from its backup;
   - remove only finals newly created by this transaction;
   - remove only transaction-owned temporary/backup files;
   - re-raise the original error, attaching rollback errors if any.
6. Delete backups only after all final replacements succeed.
7. Fsync destination directories where supported.
8. Accurately document the guarantee as rollback-safe multi-file commit, not globally atomic visibility across directories.

The mandatory test must inject failure on the second `os.replace` after the first final has already changed.

---

# 5. Workstream C — one immutable source pair per measurement case

Refactor `run_measure` so each case creates exactly one old and one new `ImmutableSource`.

The same objects must feed:

- old extraction scoring;
- new extraction scoring;
- diff alignment;
- semantic classification;
- snapshot metadata.

No source path may be reopened within the case. Add a read-count test and a mutation-after-snapshot test.

---

# 6. Workstream D — extraction context correctness

## Class markers

Do not detect normative state by substring search.

- Tokenize HTML class values.
- `normative` as an exact positive token may mark normative content.
- `non-normative`, `nonnormative`, `informative`, `example`, and equivalent negative markers must remain informative.
- Explicit `data-normative` values must have documented precedence.
- Add paired positive and negative tests.

## Protected inline spans

Replace substring-based protected-span recovery.

Build normalized text and offset mapping in one traversal so every emitted character maps to its source context. Repeated identical fragments must not move protection to the wrong occurrence.

Required fixture:

```html
<p>Clients MUST compare the literal <code>MUST</code> token.</p>
```

The normative match must be the first, non-code `MUST`, and the action must retain the complete post-modal phrase.

## Quotation/history

Treat descendant `<q>` text as protected from normative keyword authority, just as block quotations are treated conservatively. Add deterministic handling for explicit historical framing such as `previous specification`, `old version`, or `formerly required`.

When history cannot be classified safely, do not assert a current requirement. Preserve text for evidence and lower confidence or omit/mark ambiguity according to the existing M0 model; do not add an LLM.

---

# 7. Workstream E — metrics remain independent of gate policy

Always compute classification metrics by multiset intersection first:

```text
TP = multiset intersection(expected, observed)
FN = expected items not matched
FP = every observed item not matched
```

Then compute precision, recall, and F1.

Only after metrics are fixed may `allow_extra` and `forbid` determine:

- `case_passed`;
- `exact_pass`;
- `permissive_pass`.

Required case:

```text
expected = [STRENGTHENED]
observed = [STRENGTHENED, ADDED]
forbid   = [ADDED]
```

Expected:

```text
TP=1 FP=1 FN=0 precision=0.5 recall=1.0 F1=0.6667
case_passed=false
```

Do not use a forbidden-label early return that rewrites metric counts.

---

# 8. Workstream F — one exact auditable revision

The final evidence must describe one repository state.

Required closeout:

1. Finish all code, tests, docs, claims, and evidence templates.
2. Create one final repair commit.
3. Ensure the worktree is clean.
4. Rerun every gate on that exact commit.
5. Pin the same commit in:
   - `MISSION_STATE.json`;
   - every active row in `CLAIMS.md`;
   - `M0_REPAIR_EVIDENCE.md`;
   - package manifest.
6. Record the Git tree SHA and dirty state.
7. Create a Git bundle containing the verified commit and enough history to inspect the repair.
8. Generate the source archive directly from the verified commit.
9. Add an external package manifest containing:
   - schema version;
   - verified commit and tree SHA;
   - Git bundle SHA-256;
   - source archive SHA-256;
   - `uv.lock` SHA-256;
   - source fixture hashes;
   - report/metrics hashes;
   - commands and exit codes;
   - Python, uv, platform, NormShift versions.
10. Do not create a later code/docs commit after verification.

A bare commit string without history or a tree hash is not inspectable evidence.

---

# 9. Required final gate

From a clean checkout of the exact pinned revision:

```text
uv sync --all-extras --dev --frozen
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure \
  --ground-truth benchmark/measure_suite.jsonl \
  --out evidence/m0-repair-round2/metrics.json
uv run normshift diff \
  fixtures/synthetic/spec-v1.html \
  fixtures/synthetic/spec-v2.html \
  --profile rfc2119 \
  --json evidence/m0-repair-round2/report.json \
  --markdown evidence/m0-repair-round2/report.md
uv run normshift verify \
  evidence/m0-repair-round2/report.json \
  --source-root .
```

Also run every negative forgery and commit-phase failure test. Record exact exit codes and hashes.

Required packaging smoke gates:

```text
git status --porcelain                 # empty
git rev-parse HEAD                     # exact pinned commit
git rev-parse HEAD^{tree}              # recorded tree
git bundle verify <bundle>
extract source archive to empty dir
uv sync --all-extras --dev --frozen
run full gate again from extracted archive
```

---

# 10. Final response contract

Return exactly one allowed status:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Then provide:

- exact verified commit and tree SHA;
- clean/dirty state;
- defects fixed;
- defects still open;
- exact tests added;
- gate commands and exit codes;
- scoped metrics;
- forged-report rejection results;
- second-replacement rollback result;
- source read counts;
- evidence manifest path and SHA-256;
- Git bundle SHA-256;
- source archive SHA-256;
- known limitations;
- next action: independent external re-audit.

Stop after packaging. Do not begin M1/M2 work.
