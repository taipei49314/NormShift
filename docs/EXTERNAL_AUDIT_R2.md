# NormShift M0 Repair Round 2 — Independent External Audit

**Audit date:** 2026-08-07  
**Audited package tip:** `bb1dbc88a2bb37436a7f1b966490daf3a1c23842`  
**Audited tree:** `7de5cc0845c22004f0eee1de7010b4361e278cc5`  
**Auditor verdict:** `M0_PARTIAL`

## 1. Final adjudication

```text
M0: M0_PARTIAL
M1: NOT_ADJUDICATED
M2: NOT_ADJUDICATED
Production / Release: BLOCKED
```

Round 2 is a substantial repair, not a cosmetic resubmission. The core implementation now performs real source-bound extraction/alignment/classification replay for a freshly generated report, rollback restores ordinary pre-existing files under injected commit and backup failures, classification metrics count unexpected labels correctly, and the fixed benchmark remains green.

M0 still cannot be externally accepted because the submitted evidence is not reproducible from a clean relocated checkout, `verify` still validates only a selected subset of the report rather than the complete canonical replayed report, and output-path preflight still permits destructive filesystem-entry cases, including replacing existing directories and removing a pre-existing dangling symbolic-link entry during failure recovery.

## 2. Materials received

- `NormShift-M0-R2-Source.zip`
- `NormShift-M0-R2.bundle`
- `NormShift-M0-R2-MANIFEST.json`

The two package-level SHA-256 values match the external manifest. The Git bundle is valid, contains complete history, and resolves to the declared HEAD/tree.

## 3. Independent positive results

### Package identity

```text
Bundle HEAD: bb1dbc88a2bb37436a7f1b966490daf3a1c23842
Bundle tree: 7de5cc0845c22004f0eee1de7010b4361e278cc5
Bundle history: complete
Initial cloned worktree: clean
```

### Executable gates

The audit environment had Python 3.13.5 and no network access. Hypothesis, Ruff, and mypy were not available for installation.

```text
pytest excluding tests/unit/test_hypothesis_editorial.py: 90 passed
manual supplemental property samples: 100,000 passed
benchmark: 17/17 passed
measure: 15/15 passed
fresh report verify: PASS
fresh JSON run 1 vs run 2: byte-identical
fresh Markdown run 1 vs run 2: byte-identical
```

The two omitted Hypothesis tests are idempotence properties for editorial and whitespace normalization. They were inspected, and 100,000 deterministic randomized samples were run as a supplemental check. This is not represented as an exact substitute for the declared Python 3.12.13 / Hypothesis run.

### Repair work independently confirmed

- Known round-1 report text, locator, ID, classification, and change-reference modifications are rejected by replay tests.
- Failure during the second final replacement restores ordinary pre-existing regular-file outputs.
- Failure during the second backup operation restores the first moved regular-file output.
- Unexpected labels remain false positives even when `allow_extra=true`.
- `forbid` changes gate status without rewriting TP/FP/FN.
- `run_measure` reuses one immutable old/new source pair per case.
- Exact `non-normative` class handling and repeated inline-code token handling pass the supplied contract tests.

## 4. Blocking findings

## P0-01 — The submitted evidence cannot be replayed from a clean checkout

The submitted command is documented as:

```text
normshift verify evidence/m0-repair-round2/report.json --source-root .
```

On the exact bundle commit, the command fails because the report stores the author machine's absolute provenance paths and the verifier requires them to equal the auditor checkout path:

```text
old: C:/Users/G713RW/NormShift/fixtures/synthetic/spec-v1.html
new: C:/Users/G713RW/NormShift/fixtures/synthetic/spec-v2.html
```

versus the relocated clone paths.

This defeats the purpose of `--source-root`: the source bytes, byte lengths, versions, adapter output, requirements, and changes can all be identical, yet evidence replay fails solely because the repository lives somewhere else.

Relevant implementation:

- `src/normshift/verify/verifier.py:289-300` compares resolved absolute `provenance.local_path` values.
- `src/normshift/adapters/base.py:87` records `path.resolve()` in provenance.

A valid M0 evidence artifact must be verifiable after cloning or extracting under a different absolute directory.

### Source ZIP adds a second replay failure

The source archive contains all 167 tracked files, but 160 differ from the Git tree solely by LF → CRLF conversion. In ordinary application source this might be harmless; in NormShift it is not harmless because raw source bytes determine:

- document SHA-256;
- byte length;
- requirement IDs;
- report source binding;
- replayed changes.

Consequently, the packaged report fails verification against the packaged source archive with source-hash, length, requirement, and change mismatches.

The manifest-addressed hashes match the Git bundle checkout, but not the same files extracted from `NormShift-M0-R2-Source.zip`:

| Artifact | Bundle / manifest | Extracted Source.zip |
|---|---|---|
| `uv.lock` | `40424b150fedf7b9d30be4273f6abb7e5db1f636dfd54faffc24676383418978` | `a3d84a644de3d7e70d68aff4b4ed274608cba30cd6d4d747c5b7b55631a72efa` |
| `report.json` | `8cca92c46287715db24d3f572b1ca8e2612d9d7d276bf9fe71bf7f4f2ba6201e` | `13a4c4d7c36034d200dd6f21c1b8c4f5d78e6a97e8897d24a2cd360dc8b94498` |
| `report.md` | `60be30a54c646859225781adb0787cc3a8a1c8ba2496c307b271c6d80f5eb3ad` | `de544fe1aeea4d761a9f2c40431e7448e1c97f36910fa801d2ed1dde616127f7` |
| `metrics.json` | `fb76642f9178b3bfb6e2bd2bb85ded0b75d18aea003f50af461d51314e7a8808` | `dafa2cb09dce0a173f04e4b339a70e87705dfa0eb4f2f08d0a38d3a0aee198f0` |

The Git bundle is usable and auditable; the source ZIP is not a byte-exact source/evidence package.

### Required correction

1. Store a portable source reference, not an authoritative generation-machine absolute path.
2. Add a relocation test: generate in directory A, move/copy to directory B, delete A, and verify under B.
3. Produce the source ZIP directly from Git blobs, for example with `git archive`, without text-mode rewriting.
4. Verify the submitted evidence from both the bundle clone and extracted source archive before packaging.

## P0-02 — `verify` still does not compare the complete canonical replayed report

Round 2 correctly re-runs extraction, alignment, and classification. However, it then compares hand-maintained tuples and selected provenance fields rather than reconstructing and comparing the complete canonical report model.

The following modified reports were rehashed where required and still returned `verify_ok=true` against unchanged sources:

```text
requirement confidence changed by 0.00001
change confidence changed by 0.00001
provenance.adapter_version changed
provenance.content_type changed
provenance.last_modified changed
provenance.fetch_metadata changed
provenance.document_family changed
outer document_family changed to null
tool_version changed
schema_version changed
extra summary status inserted
old requirement array order reversed
change array order reversed
document path changed when explicit source overrides were supplied
extra integrity.signature claim inserted without changing the content hash
```

### Root causes

- `verifier.py:121-140` rounds requirement confidence to four decimals.
- `verifier.py:143-172` rounds change confidence to four decimals.
- `verifier.py:281-304` compares only part of `Provenance`; it omits `document_family`, `adapter_version`, `content_type`, `last_modified`, and `fetch_metadata`.
- `verifier.py:276` skips outer document-family validation when the report sets it to `null`.
- `verifier.py:318-349` sorts requirement/change tuples, so report ordering is not replay-checked.
- Top-level `schema_version` and `tool_version` are parsed but not checked against a declared compatibility policy.
- `Report.summary` is an untyped `dict[str, Any]`; extra semantic fields are ignored.
- `Report.integrity` is an untyped dictionary, and the JSON Schema does not forbid extra integrity properties.
- `integrity_payload_hash()` excludes the entire integrity object, so a new integrity subfield can be inserted without changing the existing digest.

This is narrower than the round-1 defect: source-derived requirements and changes are now genuinely replayed. It is still blocking because the mission explicitly required complete canonical comparison and rejection of every non-authorized mismatch.

### Required correction

Do not add more individual field checks. Replace the manual key lists with one canonical replay model:

```text
load sources once
→ replay extraction/alignment/classification
→ build a complete live Report through the same builder
→ normalize only explicitly documented relocatable fields
→ compare exact typed model dumps, including order and exact numbers
```

Also:

- replace `summary: dict[str, Any]` with a typed, `extra="forbid"` model;
- replace `integrity: dict[str, str]` with a typed, `extra="forbid"` model;
- set `additionalProperties: false` for nested JSON Schema objects;
- define and enforce a tool/schema compatibility rule;
- compare every provenance field or explicitly mark a field advisory and outside verification scope;
- never present advisory fields under an integrity namespace.

## P0-03 — Unsafe output path types and ancestry can replace directories or remove symlinks

The ordinary regular-file rollback path passed the supplied fault-injection tests. The preflight and transaction layers still accept filesystem entries that must never be treated as replaceable report files.

Three independent cases were reproduced:

```text
Case A — dangling symlink + later commit failure
transaction result: failure
second ordinary file: restored
first dangling symlink: removed

Case B — existing directory used as --out
CLI exit: 0
existing directory: replaced by a regular JSON file
original directory contents: left in an undisclosed .bak directory

Case C — output path is the parent directory of the input
CLI exit: 0
working/input directory: replaced by a regular JSON file
input and sibling files: left in an undisclosed .bak directory
```

Case C is especially severe: a command can report success while removing the visible directory that contained the very source it just processed.

### Root causes

- `assert_outputs_safe()` checks same-path identity but not ancestor/descendant relationships between inputs and outputs or between multiple outputs.
- `write_transaction()` uses `Path.exists()` to classify a destination. It therefore treats a dangling symbolic link as absent even though the directory entry exists.
- Every existing destination is eligible for backup/replacement; existing directories and other non-regular entries are not rejected.
- Backup cleanup calls `unlink()` and discards errors, so a moved directory backup remains hidden after the command reports success.

This violates the M0 destructive-I/O boundary: rejection or failure must preserve the complete pre-call filesystem state, including path type, symlink target, directory contents, and path visibility.

### Required correction

Perform one non-mutating preflight over all inputs and outputs before creating parent directories or temporary files:

1. an existing output must be a regular, non-symlink file;
2. reject symbolic links, including dangling links, directories, FIFOs, sockets, devices, and all other non-regular entries;
3. reject every input/output ancestor or descendant relationship, not just equality;
4. reject every ancestor or descendant relationship among outputs;
5. if any destination fails preflight, modify no path;
6. use `os.path.lexists()` / `Path.is_symlink()` rather than `Path.exists()` for directory-entry identity.

The safe M0 policy is rejection, not preservation of arbitrary entry types. Add tests that snapshot the directory tree before the command and prove exact preservation after each rejected or injected-failure case.

## 5. Non-blocking but required findings

## P1-01 — Revision identity is externally auditable but internally split across three commits

The external manifest and bundle identify package tip `bb1dbc88...`, which is a real improvement. Internally:

```text
M0_REPAIR_ROUND2_EVIDENCE.md: a4dd46a0...
MISSION_STATE.json / CLAIMS.md: 261ef505...
external manifest / PACK_README: bb1dbc88...
```

The external manifest explicitly reports `pin_matches_tip=false`. This is not a reason to reject the Git bundle itself, but it is not one exact repository-state claim.

Use distinct concepts instead of trying to self-reference one SHA:

```text
verified_code_commit
package_commit
package_tree
external_attestation_sha256
```

Alternatively use an annotated tag or external attestation whose subject is the final package commit/tree. The current `test_package_revision_equals_verified_revision` checks only that a 40-character string exists; it does not enforce package equality.

## P1-02 — Explicit unquoted historical framing still becomes a current requirement

These inputs still extract one `MUST` requirement:

```html
<p>The previous specification said clients MUST retry.</p>
<p>In the old version, clients MUST retry.</p>
<p>Clients were formerly required to retry and MUST reconnect.</p>
```

Quoted text and `<q>` are now correctly protected, but `HISTORICAL_FRAMING_RE` only protects quoted spans (`html_normalize.py:256-263`). It does not suppress or conservatively classify the unquoted historical proposition.

This was part of the round-2 mission and remains open.

## P1-03 — Destination directories are not fsynced

`write_transaction` fsyncs staged file descriptors, but never fsyncs destination directories after backup/replace/restore operations. The round-2 contract explicitly required directory fsync where supported.

The regular-file rollback logic passed independent injected-failure tests and should not be redesigned. Add a narrow best-effort directory-fsync helper and tests/mocks for call coverage.

## P1-04 — Backup cleanup failures are silently discarded

After a successful replacement, backup deletion errors are swallowed. The command can therefore report success while leaving transaction backup artifacts without identifying their paths or the incomplete cleanup state.

Do not attempt a second broad rollback after the outputs have been committed. Surface a deterministic cleanup-incomplete result, preserve the backup paths in diagnostics, and test the behavior with injected unlink failures.

## P1-05 — The external manifest does not contain the full replay contract

The external manifest identifies bundle/archive hashes, a package commit/tree, artifact hashes, environment, and summarized gate results. It does not record all information required by the round-2 package contract, including:

- exact gate commands and per-command exit codes;
- `uv` version;
- source fixture hashes used by the evidence report;
- a machine-checkable assertion that every tracked archive byte equals the named Git tree;
- a relocation verification result and extracted-archive verification result.

This does not invalidate the bundle identity already established, but it prevents the manifest from functioning as a complete independent package attestation.

## P2-01 — README verification example still points to round-1 evidence paths

`README.md` uses `evidence/m0-repair/...` in the verification gate while the submitted evidence and manifest use `evidence/m0-repair-round2/...`.

## 6. What is accepted from Round 2

The next repair must not reopen or rewrite these areas without a demonstrated regression:

- rollback-safe restoration of ordinary existing regular files;
- removal of genuinely new regular-file outputs on failure;
- classification FP accounting;
- `forbid` gate/metric separation;
- single immutable source pair in measurement;
- exact class-token handling;
- repeated inline-code token offset handling;
- original fixed 17-case benchmark labels.

## 7. Required status and next action

Public status must return to:

```text
M0_PARTIAL
```

M1/M2 remain frozen and unadjudicated.

The next engineering round should contain only:

1. portable evidence/source references;
2. byte-exact packaging;
3. complete typed canonical report replay;
4. non-destructive output type and path-ancestry preflight;
5. one coherent external revision attestation and complete package manifest;
6. unquoted historical-framing handling;
7. directory fsync, cleanup-failure reporting, and documentation cleanup.

After those changes, package the exact final Git commit with a byte-exact archive and prove the included report verifies after relocation. The maximum implementer claim remains:

```text
M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT
```

## 8. Reproduction index

- `reproductions/package_identity.txt`
- `reproductions/source_archive_tree_comparison.txt`
- `reproductions/official_evidence_verify_bundle.txt`
- `reproductions/official_evidence_verify_source_zip.txt`
- `reproductions/gate_results.txt`
- `reproductions/verifier_scope_results.txt`
- `reproductions/verifier_cases/*.json`
- `reproductions/historical_context_results.txt`
- `reproductions/transaction_results.txt`
- `reproductions/output_path_type_results.txt`
- `scripts/reproduce_verifier_scope.py`
- `scripts/reproduce_historical_context.py`
- `scripts/reproduce_transaction.py`
- `scripts/reproduce_output_path_types.py`
