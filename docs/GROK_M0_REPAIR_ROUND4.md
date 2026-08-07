# GROK 4.5 REPAIR MISSION — ROUND 4
## Project: NormShift
## Mission: Close the final M0 evidence-boundary invariants

You are repairing the externally audited `NormShift-M0-R3` package.

This is a narrow M0 closeout. Do not add features. M1, M2, M3, new adapters, lineage expansion, dashboards, hosted services, databases, LLMs, embeddings, MCP, GitHub Apps, IDE integrations, and product UI are frozen.

## Authority boundary

You are not Claim Authority, Evidence Authority, Audit Authority, or Release Authority.

Allowed final statuses:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Forbidden claims:

- COMPLETE
- VERIFIED
- AUDIT_PASSED
- PRODUCTION_READY
- RELEASE_READY
- M1/M2 complete

Set public status to `M0_PARTIAL` before editing. Restore pending-audit status only in the final code commit, before the exact-subject gate. Do not create any tracked commit after that gate.

---

# 1. Fixed external facts

Do not weaken, relabel, or reinterpret these facts.

1. R3 bundle HEAD is `bf7ee8dfbf9e5ef3740c4a28efffdb94f6ae32d3`; tree is `c546ef3ee2250e70a4aa1ca424aa78b09a478a7f`.
2. R3 Source.zip contains 175/175 byte-identical tracked Git blobs, with no missing, mismatched, extra, unsafe, cache, or backslash-path entries.
3. The official R3 evidence verifies in a clean clone, an unrelated relocated directory, and the extracted Source.zip.
4. Source mutation/deletion detection passes.
5. Known exact changes to requirement/change confidence, provenance, versions, list order, summary, and known integrity fields are rejected.
6. Existing directory, live/dangling symlink, FIFO, socket, device, hardlink alias, and ancestry rejection pass.
7. Ordinary regular-file rollback, backup-cleanup reporting, and directory fsync pass.
8. Benchmark is 17/17; measure is 15/15; packaged output is byte-deterministic.
9. The exact R3 package commit has `105 passed, 1 failed` when only the unavailable Hypothesis file is excluded.
10. The parent implementation commit has `106 passed` under the same exclusions.
11. The final status-only commit activates the failing `test_claims_pin_exact_verified_commit` while recording `108 passed`.
12. A Round-3 test ends with unconditional `or True`.
13. `verify` accepts numeric strings, a boolean in a float field, omitted defaulted fields, and conflicting duplicate JSON keys.
14. `diff` can emit absolute paths labeled `source_root_relative`.
15. Historical framing loses current obligations and leaks historical obligations.
16. A failed multi-output staging operation can leave a parent directory created by that invocation.
17. Explicit source overrides warn about content-only replay, but malformed absolute/invented declared refs can still return success.

---

# 2. Frozen accepted behavior

Do not redesign or weaken:

```text
bundle/source archive byte identity
official evidence relocation and extracted-archive verification
source mutation/deletion detection
production extraction/alignment/classification replay
exact known-field and list-order replay comparison
closed extra-field models
17-case benchmark semantics
15-case measurement semantics
unexpected labels as FP
forbid as gate-only
one immutable source read per measurement case
ordinary existing-file rollback
existing special-entry rejection
input/output and output/output ancestry checks
backup-cleanup error reporting
destination-directory fsync hooks
deterministic JSON/Markdown/metrics
```

---

# 3. Red tests first

Add these tests before implementation. Do not skip, xfail, delete, weaken, rewrite expected labels, or add unconditional truth branches.

## A. Exact package subject

```text
test_final_package_commit_passes_full_gate
test_manifest_pytest_count_is_parsed_from_exact_subject_log
test_no_repository_commit_after_verified_gate
test_external_manifest_subject_equals_bundle_head_and_tree
test_source_archive_is_git_archive_of_manifest_commit
test_external_attestation_contract_has_no_noop_assertion
test_manifest_records_sync_command_and_gate_log_hashes
```

## B. Strict canonical JSON boundary

```text
test_verify_rejects_duplicate_top_level_key
test_verify_rejects_duplicate_nested_key
test_verify_rejects_document_byte_length_string
test_verify_rejects_provenance_byte_length_string
test_verify_rejects_requirement_confidence_string
test_verify_rejects_requirement_structural_index_string
test_verify_rejects_change_confidence_string
test_verify_rejects_alignment_float_bool
test_verify_rejects_alignment_float_string
test_verify_rejects_missing_source_ref_mode
test_verify_rejects_missing_structural_index
test_verify_rejects_missing_null_condition_field
test_verify_rejects_missing_empty_fetch_metadata_field
test_verify_rejects_nan_and_infinity
test_submitted_json_equals_complete_typed_dump_before_replay
```

## C. Portable generation and override scope

```text
test_generation_rejects_source_outside_declared_source_root
test_generation_rejects_source_symlink_escape
test_generation_never_labels_absolute_ref_source_root_relative
test_generation_normalizes_relative_posix_source_refs
test_override_rejects_absolute_declared_source_ref
test_override_rejects_traversal_declared_source_ref
test_override_returns_machine_readable_content_only_scope
test_readme_documents_override_scope_and_exit_semantics
```

## D. Modal-local historical authority

```text
test_previous_spec_single_modal_is_suppressed
test_previous_spec_coordinated_modals_are_both_suppressed
test_current_historical_object_is_extracted
test_current_historically_adjective_is_extracted
test_previous_spec_but_current_must_keeps_current_only
test_current_must_then_old_version_keeps_current_only
test_incidental_was_required_does_not_hide_current_must
test_previously_modal_is_historical
test_historical_sentence_then_current_sentence_keeps_current_only
```

## E. Transaction parent-chain restoration

```text
test_preflight_rejects_output_whose_existing_ancestor_is_file
test_multi_output_preflight_is_non_mutating_across_all_destinations
test_failed_staging_removes_only_directories_created_by_invocation
test_existing_parent_directories_are_never_removed
test_sibling_files_survive_parent_cleanup
```

---

# 4. Workstream A — exact-subject gate discipline

The final package commit must exist before verification.

Required sequence:

```text
1. implement code and tests while status = M0_PARTIAL
2. update coherent in-tree status/claims
3. create the final package commit
4. clone that exact commit into a fresh directory
5. run the complete gate in that clone
6. make no tracked repository commit afterward
7. build bundle and git-archive Source.zip from that exact commit
8. generate the external manifest from captured gate logs
9. run an external package verifier over all three products
```

Requirements:

- Remove the `or True` assertion.
- Replace the obsolete self-referential `last_verified_commit` rule with external-attestation semantics.
- Do not place a commit's own SHA inside itself.
- In-tree claims may state `package_identity=externally_attested`; package equality belongs to the external verifier.
- The manifest's pytest counts must be parsed from the exact-subject log.
- Record collected/passed/failed/skipped counts, not only `passed`.
- Hash every gate log and record those hashes in the manifest.
- Include a unique `verification_run_id`.
- If the exact final subject has any failure, final status is `M0_PARTIAL`.

No post-gate status-only commit is allowed.

---

# 5. Workstream B — strict canonical submitted JSON

Keep the accepted full source replay. Add a strict boundary before it.

Required architecture:

```text
read raw bytes
→ strict JSON parse
  - reject duplicate keys at every depth
  - reject NaN / Infinity / -Infinity
→ complete recursive schema or strict typed validation
  - exact primitive types
  - required canonical fields
  - unknown fields rejected
→ canonical submitted-object equality with complete typed JSON dump
→ resolve/load each source once
→ extraction/alignment/classification replay
→ build production Report
→ exact complete live-report comparison
```

Implementation requirements:

1. Use `object_pairs_hook` or an equivalent duplicate-key detector.
2. Use `parse_constant` or equivalent to reject non-finite constants.
3. Do not use ordinary last-key-wins evidence parsing.
4. Prevent bool/string-to-number coercion.
5. Require canonical fields even when their value is `null`, `0`, an empty object, or a default string.
6. Before replay, require:

```python
canonical_json_bytes(submitted_data) == canonical_json_bytes(
    validated_report.model_dump(mode="json")
)
```

The exact implementation may differ, but it must preserve primitive types and field presence. JSON object key order and whitespace remain non-authoritative.

7. Replace shallow nested schema entries such as `{"type":"object"}` with a complete generated/maintained schema or equivalent recursive strict validation.
8. Continue to preserve array order and reject unknown fields.
9. SHA-256 remains an unkeyed consistency digest, not a signature.
10. Every red case must fail through the real CLI, not only a private helper.

---

# 6. Workstream C — truthful portable source identity

Add an explicit generation root:

```text
normshift diff OLD NEW --source-root ROOT ...
```

Rules:

1. Resolve `ROOT` once.
2. Resolve OLD and NEW once beneath `ROOT`.
3. Reject traversal and symlink escape.
4. Store normalized POSIX references relative to `ROOT`.
5. Store the same relative reference in `DocumentSnapshot.path` and `Provenance.local_path`.
6. Never emit an absolute path with `source_ref_mode=source_root_relative`.
7. When no root is supplied, either define CWD as the explicit root and reject outside-CWD sources, or fail closed when portability cannot be represented.
8. Do not reduce identity to a basename.

Override contract:

- Validate the report's declared ref even when `--old-source` / `--new-source` is used.
- Reject absolute and traversal declared refs.
- Overrides relocate source bytes; they do not attest the declared logical path.
- Return machine-readable verification scope, for example:

```text
verification_scope=FULL
verification_scope=CONTENT_ONLY_OVERRIDE
```

- Keep a visible human warning.
- Document exit/status semantics in README and CLI help.

---

# 7. Workstream D — modal-local historical filtering

Do not suppress a whole paragraph merely because it contains:

```text
historical
historically
was required
previous specification
old version
previously
```

Evaluate authority per modal occurrence or tightly bounded clause.

Required outcomes:

```text
The previous specification said clients MUST retry.
→ none

The previous specification said clients MUST retry and clients MUST reconnect.
→ none

Clients MUST retain historical records.
→ current MUST

The historically insecure protocol MUST be disabled.
→ current MUST

The previous specification said clients SHOULD retry, but clients MUST reconnect.
→ current MUST reconnect only

Clients MUST now abort, although the old version said clients MUST retry.
→ current MUST abort only

Because low latency was required for interoperability, clients MUST retry.
→ current MUST retry only

Previously, clients MUST retry.
→ none
```

Deterministic strategy:

1. locate each modal token;
2. determine its bounded clause;
3. inspect reporting/history framing associated with that modal, not unrelated words elsewhere;
4. keep coordinated historical clauses historical;
5. recognize explicit current transitions and sentence boundaries;
6. suppress only the historical modal clause;
7. fail conservatively on unresolved ambiguity.

Do not add an LLM.

---

# 8. Workstream E — parent-chain preflight and rollback

Before creating any parent, temp file, or backup:

- inspect every destination's nearest existing ancestor;
- require supported existing ancestors to be directories;
- reject existing file, FIFO, socket, device, or unsupported ancestors;
- validate all outputs as a set before mutating any path.

During the transaction:

- track every directory created by this invocation;
- on staging or commit failure, remove created directories in reverse order only when empty;
- never remove a pre-existing directory;
- preserve sibling files;
- retain the accepted regular-file backup/restore algorithm;
- retain cleanup reporting and fsync behavior.

Do not claim global atomic visibility across different directories.

---

# 9. Workstream F — tests, version, and public metadata

- Add real behavioral assertions for the critical missing Round-3 tests; do not create name-only placeholders.
- Restore specific invariant assertions where prior tests were broadened to generic `assert errors`.
- Bump the patch version because verifier and report-generation semantics change.
- Regenerate all evidence under the new tool version.
- Change package description so it does not publicly imply adjudicated M1/M2 completion.
- Record known limitations honestly.

---

# 10. Exact clean-package gate

Run using Python 3.12 from a fresh clone of the final package subject:

```text
uv sync --frozen --all-extras --dev
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

Then run, on the same exact subject:

```text
strict canonical JSON boundary matrix
mixed historical/current authority matrix
absolute/out-of-root/symlink-escape generation matrix
override verification-scope matrix
parent-chain/staging rollback matrix
frozen special-entry and ordinary rollback regressions
relocation verification
extracted Source.zip verification
archive-to-Git-tree blob comparison
external package verifier
```

Every unauthorized report representation in the strict matrix must return non-zero.

---

# 11. Required package products

Submit exactly:

```text
NormShift-M0-R4.bundle
NormShift-M0-R4-Source.zip
NormShift-M0-R4-MANIFEST.json
```

Create Source.zip with:

```text
git archive --format=zip --prefix=NormShift/ <PACKAGE_COMMIT>
```

or a byte-equivalent Git-blob implementation.

The external manifest must include:

- package commit/tree;
- bundle/source archive SHA-256;
- verification run ID;
- Python/platform/uv/tool versions;
- exact commands and exit codes, including dependency sync;
- gate-log SHA-256 values;
- parsed pytest collected/passed/failed/skipped counts;
- benchmark and measurement results;
- report/Markdown/metrics/lock hashes from extracted Source.zip;
- fixture hashes from extracted Source.zip;
- archive-to-Git-tree result;
- relocation and extracted-archive verification results;
- strict canonical matrix result;
- portable-generation and override-scope matrix result;
- historical-authority matrix result;
- parent-chain rollback matrix result;
- `dirty=false` before packaging;
- status no higher than `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.

---

# 12. Final response contract

Return only one status:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Include package commit/tree, external manifest hash, exact gate commands/exits, test counts, matrix counts, artifact hashes, known limitations, unresolved risks, and the next single engineering action.

Never claim audit passage, production readiness, or release readiness.
