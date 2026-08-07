# GROK 4.5 REPAIR MISSION — ROUND 5
## Project: NormShift
## Mission: Close canonical equality, portable-ref grammar, and historical authority

You are repairing the externally audited `NormShift-M0-R4` package at:

```text
commit 878bfd3a6bb7b649652e81936216277fc8151d5e
tree   da83272e68f4a5d324f63917d5a52dafac7e04c9
```

This is a final narrow M0 trust-core repair. Do not add product features.

Frozen:

```text
M1/M2/M3
new adapters
lineage expansion
new benchmark labels
new measurement labels
dashboards / UI / hosted services
databases
LLMs / embeddings
MCP / GitHub Apps / IDE integrations
```

## Authority boundary

You are not Claim Authority, Evidence Authority, Audit Authority, or Release Authority.

Allowed final statuses:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Forbidden:

- COMPLETE
- VERIFIED
- AUDIT_PASSED
- PRODUCTION_READY
- RELEASE_READY
- M1/M2 complete

Set status to `M0_PARTIAL` while editing. Restore pending-audit status only in the final package commit before the exact-subject gate. Make no tracked commit afterward.

---

# 1. Frozen accepted behavior

Do not redesign or weaken:

- exact bundle/source archive identity;
- 187/187 archive-to-Git blob equality;
- official report relocation and Source.zip verification;
- source mutation/deletion detection;
- full extraction/alignment/classification replay;
- duplicate-key rejection;
- numeric-string/bool/default/unknown-field rejection;
- array-order, provenance, version, and known-field comparison;
- 17/17 benchmark semantics;
- 15/15 measurement semantics;
- unexpected labels as FP;
- forbid as gate-only;
- one immutable source read per measurement case;
- special-entry and ancestry rejection;
- regular-file rollback;
- parent-chain cleanup;
- backup cleanup reporting;
- directory fsync hooks;
- deterministic official JSON/Markdown/metrics;
- successful scope output (`FULL` / `CONTENT_ONLY_OVERRIDE`).

---

# 2. Fixed external facts

Do not weaken or reinterpret:

1. A rehashed report changing generated `0.0` to `-0.0` returns `VERIFY OK FULL`.
2. Full verification accepts `./path`, repeated separators, and `segment/./path` after path/provenance rebinding.
3. Override verification accepts empty, `.`, backslash traversal, UNC-like, URI-like, and backslash refs.
4. `The previous value MUST be retained.` is suppressed.
5. `Unlike the previous specification, clients MUST retry.` is suppressed.
6. `The prior specification said clients MUST retry.` is extracted as current.
7. A historical quote change can create an `AMBIGUOUS` event for an unchanged current obligation.
8. An escaped unpaired surrogate causes an unhandled traceback.
9. The later re-export manifest pins the correct bundle bytes but no longer contains the full gate contract.

---

# 3. Red tests first

Add real CLI-facing tests before implementation. Do not skip, xfail, weaken, or add unconditional truth branches.

## A. Exact canonical numeric equality

```text
test_verify_rejects_negative_zero_alignment_field
test_verify_rejects_negative_zero_component_field
test_verify_rejects_overflow_to_positive_infinity
test_verify_rejects_overflow_to_negative_infinity
test_live_replay_comparison_uses_canonical_bytes_not_python_numeric_equality
test_valid_production_zero_still_verifies
test_unpaired_surrogate_returns_clean_failure_without_traceback
```

## B. Portable-ref grammar and canonical root binding

```text
test_full_verify_rejects_dot_prefixed_ref
test_full_verify_rejects_repeated_separator_ref
test_full_verify_rejects_dot_component_ref
test_full_verify_rejects_symlink_alias_when_declared_ref_is_not_canonical_target
test_override_rejects_empty_ref
test_override_rejects_dot_ref
test_override_rejects_backslash_ref
test_override_rejects_backslash_traversal_ref
test_override_rejects_unc_ref
test_override_rejects_rooted_backslash_ref
test_override_rejects_uri_like_ref
test_portable_ref_validation_is_host_platform_independent
test_valid_posix_relative_override_ref_returns_content_only_scope
```

## C. Historical authority generalization

```text
test_previous_value_is_current
test_previous_state_is_current
test_previous_section_is_current
test_previous_implementations_is_current
test_previously_assigned_identifiers_is_current
test_unlike_previous_spec_current_modal_is_kept
test_prior_spec_reported_modal_is_historical
test_earlier_version_reported_modal_is_historical
test_current_modal_then_prior_report_keeps_current_only
test_prior_report_but_current_modal_keeps_current_only
test_historical_comment_change_does_not_change_current_requirement_fingerprint
test_historical_comment_change_does_not_emit_semantic_change_for_current_clause
```

## D. Final package attestation

```text
test_one_authoritative_manifest_contains_current_bundle_hash
test_manifest_contains_exact_subject_commands_and_exit_codes
test_manifest_contains_gate_log_hashes_and_pytest_counts
test_manifest_contains_all_matrix_results
test_manifest_subject_equals_bundle_head_and_tree
test_manifest_source_zip_matches_git_tree
test_no_unlinked_reexport_overlay_manifest
```

---

# 4. Workstream A — exact canonical replay

Keep the strict parser and production replay. Replace only the final equality semantics and missing numeric boundary.

Required flow:

```text
raw bytes
→ strict JSON parse (duplicates + constants)
→ recursively reject every non-finite float
→ strict field presence / primitive representation checks
→ typed Report
→ integrity validation
→ immutable source replay
→ production Report
→ canonical payload-byte equality excluding only typed integrity envelope
```

Requirements:

1. Do not compare complete reports with ordinary Python dict equality.
2. Compare canonical encoded payload bytes or an equivalently exact recursive comparator.
3. Define signed zero explicitly:
   - preferred: reject any submitted negative-zero float; and ensure production never emits it; or
   - normalize signed zero before both generation and integrity, with one documented representation.
4. Detect exponent overflow that becomes `inf` even though `parse_constant` was not invoked.
5. Catch Unicode surrogate / canonical encoding failures and return a clean non-zero verifier result.
6. CLI failures must print `verification_scope=...` without a traceback.
7. SHA-256 remains an unkeyed consistency digest, not a signature.

Do not remove full source replay.

---

# 5. Workstream B — one portable source-ref grammar

Create one shared function used by:

- generation;
- full verification;
- override verification;
- snapshot/provenance construction tests.

Use platform-independent POSIX semantics, such as `PurePosixPath`, not host-native `Path.parts` alone.

A valid ref must be:

```text
non-empty
not "."
relative
POSIX separator only
not URI-like
not drive-like
not UNC/rooted
no empty segment
no "." segment
no ".." segment
no repeated separator
exactly equal to its normalized POSIX representation
```

For full verification:

```text
root = root.resolve()
candidate = (root / declared).resolve()
require candidate under root
canonical_ref = candidate.relative_to(root).as_posix()
require declared == canonical_ref
load source once
replay with canonical_ref
```

This must also reject a submitted symlink alias spelling when generation would have stored the canonical resolved target ref.

For overrides:

- validate the declared ref with the same grammar before reading override bytes;
- retain `CONTENT_ONLY_OVERRIDE`;
- do not attest the logical path;
- successful valid relative refs remain supported.

---

# 6. Workstream C — bounded historical reporting, not bare words

The filter must classify each modal occurrence using a bounded relationship.

Do not treat these words alone as historical authority:

```text
previous
prior
earlier
old
former
previously
historically
```

Historical suppression should require a pattern such as:

```text
historical modifier
+ specification / standard / version / draft / text / requirement
+ reporting verb or quote frame
+ the target modal occurrence
```

Required current outcomes:

```text
The previous value MUST be retained.
The previous state MUST remain available.
The previous section MUST be ignored.
Previous implementations MUST be rejected.
Previously assigned identifiers MUST remain unique.
Unlike the previous specification, clients MUST retry.
```

Required historical outcomes:

```text
The previous specification said clients MUST retry.
The prior specification said clients MUST retry.
The earlier version stated clients MUST retry.
Previously, clients MUST retry.
```

Mixed clauses must retain only current modals.

## Semantic text boundary

For a retained current modal:

- keep full `original_text` and source locator as evidence;
- derive `normalized_text`, roles, and fingerprint from the bounded current clause rather than unrelated historical commentary;
- changing only a suppressed historical quote must not create a change event for an unchanged current obligation.

If a deterministic clause boundary cannot be established, emit or preserve explicit uncertainty rather than silently converting historical commentary into a current requirement.

---

# 7. Workstream D — one authoritative package manifest

Do not submit a full manifest and then replace it with an unlinked re-export overlay.

Required sequence:

```text
1. finish code/tests with status M0_PARTIAL
2. create final package commit
3. clean-clone that exact commit
4. run all gates and matrices
5. make no tracked commit afterward
6. create bundle once
7. create Source.zip once from exact commit
8. compute their final hashes
9. create one complete external manifest
10. run external package verifier
11. do not re-export any product without regenerating the one complete manifest
```

The single manifest must include:

- commit/tree;
- actual final bundle/source hashes;
- verification run ID and timestamp;
- Python/platform/uv/tool versions;
- exact commands and exits;
- gate-log hashes;
- parsed pytest collected/passed/failed/skipped counts;
- benchmark and measure results;
- report/Markdown/metrics/lock hashes;
- fixture hashes;
- archive-to-tree counts;
- relocation and extracted-archive verify;
- signed-zero/canonical matrix;
- portable-ref matrix;
- historical matrix;
- frozen I/O regression matrix;
- `dirty=false`;
- status no higher than `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.

Include or submit the external package-verifier script/output needed to reproduce those assertions.

---

# 8. Exact clean-subject gate

Use Python 3.12 in a fresh clone of the final commit:

```text
uv sync --frozen --all-extras --dev
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

Then run:

```text
canonical numeric matrix
portable-ref full/override matrix
historical authority and clause-identity matrix
source mutation/deletion regression
frozen special-entry/rollback/parent-chain regressions
relocation verification
Source.zip verification
archive-to-Git-tree comparison
external package verifier
```

Every unauthorized report must return non-zero through the real CLI.

---

# 9. Required products

Submit one final set:

```text
NormShift-M0-R5.bundle
NormShift-M0-R5-Source.zip
NormShift-M0-R5-MANIFEST.json
```

Optional `.sha256` sidecars are allowed, but they do not replace fields in the authoritative manifest.

---

# 10. Final response contract

Return one status only:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Include commit/tree, authoritative manifest hash, exact gate results, test counts, matrix results, package hashes, known limitations, unresolved risks, and the next single engineering action.

Never claim external audit passage, release readiness, production readiness, or M1/M2 completion.
