# GROK 4.5 REPAIR MISSION — ROUND 3
## Project: NormShift
## Mission: Portable evidence and complete canonical replay

You are repairing the externally audited `NormShift-M0-R2` package.

This is the final M0 trust-core repair, not feature development. M1, M2, M3, new adapters, lineage expansion, dashboards, crawlers, databases, LLMs, MCP, GitHub Apps, and new product surfaces are frozen.

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

Set public status to `M0_PARTIAL` before implementation. Do not restore pending-audit status until every required gate passes on the exact packaged subject and the packaged evidence verifies after relocation.

---

# 1. Fixed external facts

Treat these as acceptance facts. Do not weaken or reinterpret them.

1. The Git bundle is valid and identifies package tip `bb1dbc88...` / tree `7de5cc08...`.
2. The submitted evidence report fails in a clean clone because `provenance.local_path` contains the author machine absolute path.
3. `--source-root` does not currently make evidence portable.
4. The submitted Source.zip changes 160 tracked files from LF to CRLF relative to Git blobs.
5. The report cannot verify against the submitted Source.zip because raw source bytes changed.
6. Manifest artifact hashes match the bundle checkout, not the same paths extracted from Source.zip.
7. `verify` accepts changes to selected non-replayed fields and sub-four-decimal confidence values.
8. `verify` accepts extra summary and integrity properties.
9. `verify` accepts reordered requirement/change arrays.
10. Quoted and `<q>` historical text is handled, but explicit unquoted historical framing still extracts current requirements.
11. Ordinary-file rollback passes fault injection, but output preflight still permits destructive path types and ancestry: a dangling symlink can disappear, an existing directory can be replaced by a file, and an input's parent directory can be accepted as the output.
12. Backup cleanup failures are silently discarded, and destination directories are not fsynced.
13. The external manifest identifies the package but does not record the full command/exit-code, relocation, extracted-archive, source-hash, and archive-to-tree proof contract.
14. Metric accounting, one-read measurement, exact class-token handling, and repeated inline-code offsets passed independent re-audit. Do not redesign them.

---

# 2. Red tests first

Add the following tests, or stricter behavioral equivalents, before implementation.

```text
test_packaged_evidence_verifies_after_repository_relocation
test_packaged_evidence_verifies_from_extracted_source_archive
test_source_archive_tracked_bytes_match_git_blobs
test_manifest_artifact_hashes_match_extracted_archive_files

test_verify_rejects_requirement_confidence_exact_mismatch
test_verify_rejects_change_confidence_exact_mismatch
test_verify_rejects_provenance_adapter_version_mismatch
test_verify_rejects_provenance_content_type_mismatch
test_verify_rejects_provenance_last_modified_mismatch
test_verify_rejects_provenance_fetch_metadata_mismatch
test_verify_rejects_provenance_document_family_mismatch
test_verify_rejects_missing_outer_document_family
test_verify_enforces_tool_version_compatibility
test_verify_enforces_schema_version_compatibility
test_verify_rejects_extra_summary_fields
test_verify_rejects_extra_integrity_fields
test_integrity_namespace_cannot_gain_unsigned_claims
test_verify_rejects_reordered_requirement_array
test_verify_rejects_reordered_change_array
test_verify_has_documented_override_path_semantics

test_unquoted_previous_specification_is_not_current_requirement
test_unquoted_old_version_is_not_current_requirement
test_unquoted_formerly_required_is_not_current_requirement

test_transaction_rejects_dangling_symlink_output_without_modifying_it
test_failed_transaction_preserves_dangling_symlink_entry_and_target
test_existing_directory_output_is_rejected_without_moving_contents
test_output_ancestor_of_input_is_rejected_without_mutation
test_input_output_ancestor_relationships_are_rejected
test_output_output_ancestor_relationships_are_rejected
test_existing_non_regular_output_is_rejected
test_write_transaction_rejects_unsupported_entries_without_cli_preflight
test_preflight_failure_creates_no_parent_directory_or_temp_file
test_backup_cleanup_failure_is_reported_with_backup_paths
test_directory_fsync_called_after_successful_commit
test_directory_fsync_called_after_rollback_restore

test_external_manifest_subject_equals_bundle_head_and_tree
test_in_tree_claims_do_not_pretend_to_self_reference_package_tip
test_manifest_records_exact_commands_exit_codes_and_tool_versions
test_manifest_proves_archive_bytes_match_subject_tree
test_manifest_records_relocation_and_archive_verify_results
```

Do not skip, xfail, delete, narrow, or relabel these tests to obtain green status.

---

# 3. Workstream A — portable source identity

The report must not require the generation machine's absolute directory.

## Required model

Define a portable source reference, for example:

```text
source_ref: fixtures/synthetic/spec-v1.html
source_ref_mode: source_root_relative
```

Rules:

1. A report intended for external verification must store a normalized POSIX relative source reference.
2. `--source-root` resolves that reference beneath an explicit root and rejects traversal.
3. The authoritative binding is the loaded source bytes plus adapter/profile/version metadata, not an absolute workstation path.
4. Do not store generation-machine absolute paths in the portable evidence report.
5. If a local absolute path is retained for diagnostics, place it in a clearly advisory local log outside the verified portable report.
6. Explicit `--old-source` / `--new-source` behavior must be documented:
   - they may relocate identical bytes;
   - they must still satisfy all content/provenance replay invariants;
   - the verifier output must state that an override was used;
   - they must not silently validate a false source-reference claim.

## Mandatory relocation gate

```text
create clean checkout A
generate report in A
copy exact repository/evidence to unrelated checkout B
delete A
run verify in B with --source-root B
expect exit 0
```

The same submitted evidence must verify from the extracted source archive.

---

# 4. Workstream B — one complete canonical replay comparison

Do not add another list of individual report-field comparisons.

## Required architecture

1. Parse and schema-validate the submitted report.
2. Resolve and load each source exactly once.
3. Replay extraction, alignment, and classification.
4. Build a complete live `Report` using the same production report builder.
5. Apply one explicit canonicalization function only for documented relocatable fields.
6. Compare exact typed model dumps, including:
   - list order;
   - exact float values;
   - every provenance field;
   - every requirement field;
   - every change field;
   - summary;
   - schema/tool compatibility fields.
7. Fail on any non-authorized mismatch.

Remove `_req_key` and `_change_key` as independent hand-maintained truth definitions, or make them mechanically derive from the full model without omissions, rounding, or order loss.

## Typed models

Replace loose dictionaries with typed models using `extra="forbid"`:

```text
ReportSummary
IntegrityEnvelope
```

`ReportSummary` must contain only the defined count fields.

`IntegrityEnvelope` must contain only fields whose semantics are implemented. Do not accept `signature`, `attestation`, `verified`, or similar keys unless a real verification mechanism exists.

## Integrity scope

`integrity_payload_hash()` may exclude the digest value itself, but the model and schema must reject all unknown integrity fields. Clearly state that SHA-256 is an unkeyed consistency digest, not a signature.

## Version policy

Define a deterministic rule:

- supported `schema_version` values;
- whether `tool_version` must exactly equal the running verifier or use an explicit compatibility table.

Do not silently accept arbitrary versions.

---

# 5. Workstream C — byte-exact package construction

Do not create the source archive through text-mode read/write or line-ending conversion.

Required package construction:

```text
git archive --format=zip --prefix=NormShift/ <PACKAGE_COMMIT>
```

or a byte-equivalent implementation reading Git blobs in binary mode.

Requirements:

- all tracked archive bytes match the subject Git blobs exactly;
- forward-slash paths;
- no caches, virtual environments, or working-tree artifacts;
- no path traversal entries;
- the included report verifies against the included fixture bytes;
- manifest artifact hashes state their scope explicitly and match archive-extracted bytes;
- verify archive hash and per-artifact hashes after final packaging.

Do not regenerate or normalize tracked files while packaging.

---

# 6. Workstream D — coherent revision attestation without self-reference

Do not try to place the final commit's own SHA inside that same commit.

Use these distinct concepts:

```text
verification_run_id
verified_code_subject (optional pre-attestation commit)
package_commit
package_tree
external_manifest_sha256
```

The authoritative package subject must be an external manifest, annotated tag, Git note, or equivalent artifact created after the final commit.

Required behavior:

1. The external manifest names exactly one bundle HEAD and tree.
2. The bundle resolves to those values.
3. The source archive is generated from that exact package commit.
4. In-tree documents say that package identity is externally attested; they must not contain three conflicting SHAs.
5. `MISSION_STATE`, `CLAIMS`, and evidence use the same terminology.
6. Remove or rewrite the current test that merely checks for a 40-character string. Test actual package equality through the external manifest/bundle.

No cryptographic-signature claim is required.

---

# 7. Workstream E — complete explicit historical framing

Current quoted-span handling is accepted. Extend deterministic historical handling to unquoted explicit framing.

At minimum, these must not become current requirements:

```text
The previous specification said clients MUST retry.
In the old version, clients MUST retry.
Clients were formerly required to retry.
The earlier draft required clients to retry.
Historically, clients MUST retry.
```

Use conservative deterministic rules. Do not add an LLM.

Do not suppress a genuinely current requirement merely because a paragraph also mentions history. If one block contains both historical and current propositions, split or conservatively mark only the historical modal span as non-authoritative.

---

# 8. Workstream F — path-entry safety and narrow durability completion

The ordinary regular-file rollback algorithm passed external fault injection. Do not redesign it. Close the unhandled filesystem-entry and durability edges only.

## Output entry-type and ancestry policy

Perform one complete, non-mutating preflight before creating parent directories, temporary files, or backups.

For M0:

- an existing final output must be a regular, non-symlink file;
- reject symbolic links, including dangling links;
- reject directories, FIFOs, sockets, devices, and all other non-regular entries;
- reject equality and ancestor/descendant relationships between every input and output;
- reject equality and ancestor/descendant relationships among outputs;
- use `os.path.lexists()` and/or `Path.is_symlink()`; do not rely on `Path.exists()`;
- if any destination fails preflight, return non-zero and modify no path;
- enforce output entry-type validation again inside `write_transaction` as defense in depth, even when CLI preflight is bypassed;
- leave rejected directory contents, symbolic-link entries/targets, and sibling files exactly unchanged;
- add platform-aware tests or mocks where native symlink/FIFO creation is unavailable.

Do not move an existing directory to a hidden backup and replace it with a report file. Do not accept an input's parent directory as an output.

## Cleanup and durability

Add only:

- best-effort destination-directory fsync after successful backup/replace commit;
- directory fsync after rollback restoration where supported;
- deterministic reporting when committed-output backup cleanup fails, including retained backup paths;
- platform-aware tests/mocks;
- accurate documentation of limitations.

Do not claim global atomic visibility across directories. Do not report a fully clean success when cleanup is incomplete.

---

# 9. Frozen accepted behavior

The following must remain green and unchanged in semantics:

```text
17/17 frozen benchmark
15/15 measurement suite
unexpected labels count as FP
forbid affects gate only
one immutable source pair per measurement case
exact-path and alias-based input/output collision prevention
rollback restoration for ordinary regular files under commit and backup failure
non-normative exact class token handling
repeated inline-code token offset handling
quoted and <q> historical protection
```

---

# 10. Exact clean-package gate

Run from a fresh clone of the final bundle subject using Python 3.12:

```text
uv sync --frozen --all-extras --dev
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

Then:

```text
clone/extract to a different absolute directory
run the same verify command against the unchanged packaged report
expect exit 0
```

Then extract the final Source.zip and run:

```text
normshift verify evidence/m0-repair-round3/report.json --source-root .
```

It must return exit 0 without editing or regenerating any tracked artifact.

Run the full verifier modification matrix and prove every unauthorized change returns non-zero.

---

# 11. Required package products

Submit exactly:

```text
NormShift-M0-R3.bundle
NormShift-M0-R3-Source.zip
NormShift-M0-R3-MANIFEST.json
```

The external manifest must include:

- package commit;
- package tree;
- bundle SHA-256;
- source archive SHA-256;
- explicit artifact-hash scope;
- per-artifact SHA-256 values measured from extracted Source.zip;
- Python/platform;
- exact gate commands and per-command exit codes;
- `uv` version;
- source fixture SHA-256 values;
- machine-checkable archive-to-Git-tree byte comparison result;
- relocation-verify result;
- extracted-archive-verify result;
- `dirty=false` before packaging;
- status no higher than `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.

---

# 12. Final response contract

Return only one status:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Include:

- package commit/tree;
- external manifest hash;
- exact verification commands;
- test and benchmark counts;
- relocation result;
- extracted archive verification result;
- output entry-type/ancestry preflight results, including dangling symlink and existing-directory cases;
- backup-cleanup fault-injection result;
- artifact hashes;
- known limitations;
- unresolved risks.

Never claim audit passage or release readiness.
