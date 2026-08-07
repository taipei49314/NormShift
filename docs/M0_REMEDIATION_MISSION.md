# GROK 4.5 REPAIR MISSION
## Project: NormShift
## Mission: M0 Trust-Chain Repair — No Feature Expansion

You are repairing an externally rejected M0 candidate.

This is not an M1, M2, or feature-development mission. Existing M1/M2 code may remain in the repository, but it must be marked experimental and must not be used to claim milestone completion.

## Authority boundary

You are not Claim Authority, Evidence Authority, Audit Authority, or Release Authority.

The only allowed final statuses are:

- `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`
- `M0_PARTIAL`
- `M0_BLOCKED`

Do not use `M1_*`, `M2_*`, `COMPLETE`, `VERIFIED`, `PRODUCTION_READY`, or `RELEASE_READY`.

---

# 1. External audit findings you must treat as fixed facts

Do not debate, relabel, delete, or weaken these findings:

1. `verify` accepts a report after its source is modified or deleted.
2. `verify` accepts a rehashed report with an impossible summary and dangling requirement ID.
3. `extract`, `diff`, and `lineage` can overwrite source inputs and exit 0.
4. `measure --out` can overwrite the frozen ground-truth file and exit 0.
5. `diff --json X --markdown X` exits 0 but leaves Markdown where JSON was promised.
6. rollback can delete a pre-existing output file after a later artifact write fails.
7. classification scoring reports F1=1.0 while ignoring unexpected labels under `allow_extra=true`.
8. `Security Considerations` and normative appendices are blanket-skipped.
9. inline `<code>` content is removed from exact evidence text.
10. actor extraction can select an object after the modal as the actor.
11. quoted historical normative wording is extracted as a current requirement.
12. sources are read multiple times in one pipeline, permitting snapshot/extraction mismatch.
13. M1/M2 were advanced before the required M0 external-audit stop point.

All must become fixed regression cases.

---

# 2. Scope freeze

Before code changes:

- set `MISSION_STATE.status` to `M0_PARTIAL`;
- record all external findings under `known_failures`;
- mark M1/M2 in README and CLAIMS as `EXPERIMENTAL_NOT_ADJUDICATED`;
- remove or retract the current public claim of classification F1=1.0;
- add a decision stating that no new feature work is allowed until M0 is externally accepted.

Do not remove existing M1/M2 implementation merely to hide it.

---

# 3. Workstream A — one immutable source read

Refactor around a source snapshot object created exactly once per input.

It must carry at minimum:

- resolved/display path;
- raw bytes;
- raw SHA-256;
- byte length;
- adapted working bytes;
- document version;
- provenance;
- document family.

Extraction, definitions, snapshot metadata, and report construction must all consume this same object. Do not reopen the source inside one run.

Add a test that mutates the filesystem path after the snapshot is created and proves the in-flight report remains internally tied to the original bytes.

---

# 4. Workstream B — strict evidence verifier

`normshift verify REPORT` must fail closed unless every applicable invariant passes.

Required checks:

## Report and schema

- JSON parse;
- Pydantic model;
- required bundled JSON Schema;
- report payload integrity hash;
- supported algorithm exactly `sha256`.

Missing schema assets are an error, not an optional skip.

## Source snapshots

For both old and new sources:

- source exists, unless an explicit immutable embedded-snapshot mode is implemented;
- current source SHA-256 equals `DocumentSnapshot.sha256`;
- current source byte length equals `DocumentSnapshot.byte_length`;
- provenance content hash and byte length agree with the snapshot;
- provenance local path/canonical metadata is structurally valid.

Provide an explicit `--source-root` or `--old-source` / `--new-source` mechanism so reports using relative paths can be verified from another working directory. Do not silently guess.

## Requirements

- IDs are unique on each side;
- every old requirement has `document_sha256 == old_document.sha256`;
- every new requirement has `document_sha256 == new_document.sha256`;
- document version agrees with the snapshot;
- requirement ID and fingerprint are recomputed from the declared algorithm/version;
- source locator is resolvable against the same adapted snapshot where feasible;
- exact evidence text matches the located source-visible text under the declared normalizer version.

## Changes

- every non-null old ID exists in old requirements;
- every non-null new ID exists in new requirements;
- ADDED has no old ID; REMOVED has no new ID; paired classes have both IDs;
- old/new text and locators agree with referenced requirements;
- modality transition agrees with referenced modalities;
- change ID is recomputed;
- every evidence hash is recomputed;
- duplicate or unknown references fail.

## Summary

Recompute and compare:

- old requirement count;
- new requirement count;
- change count;
- classification counts.

Create fixed failing tests for:

- source modified;
- source deleted;
- source swapped;
- requirement document hash changed and report rehashed;
- dangling old/new requirement ID and report rehashed;
- summary count changed and report rehashed;
- evidence hash changed and report rehashed;
- missing bundled schema.

A stale-checksum test alone is insufficient.

---

# 5. Workstream C — universal output safety

Create one shared path-preflight and atomic-write utility used by:

- `extract`;
- `diff`;
- `ingest`;
- `lineage`;
- `measure`;
- any future artifact-writing command.

Before processing:

- reject any output path that resolves to any input path;
- reject JSON and Markdown output paths that resolve to each other;
- reject `measure --out` equal to its ground truth;
- detect existing-path identity using `samefile` where available;
- handle normalized parent paths for non-existing outputs;
- reject source overwrite through symlinks/hard links where detectable.

Writing rules:

- never truncate the final path directly;
- write every artifact to a same-directory temporary file;
- complete and validate all temporary artifacts first;
- atomically replace final paths only after the transaction is ready;
- preserve pre-existing outputs if any later step fails;
- never use blanket `unlink()` rollback against final paths.

Add fixed tests for every collision and failure mode listed by the external audit.

---

# 6. Workstream D — honest metrics

Repair `score_classification`:

- `TP = multiset intersection(expected, observed)`;
- `FN = expected items not matched`;
- `FP = all observed items not matched`, including labels not present in expected;
- `allow_extra` may affect only `case_passed`, never precision/recall/F1 counts.

The following case must report `TP=1`, `FP=3`, `FN=0`, precision `0.25`, recall `1.0`, F1 `0.4`, while `case_passed` may remain true under a permissive gate:

```text
expected: STRENGTHENED
observed: STRENGTHENED, ADDED, REMOVED, POLARITY_FLIP
allow_extra: true
```

Add separate output fields for:

- exact-label pass;
- permissive gate pass;
- precision/recall/F1.

Regenerate measurement artifacts. Do not claim universal or public-benchmark accuracy.

---

# 7. Workstream E — extraction evidence correctness

## Section handling

Remove blanket exclusion based only on section title for:

- Security Considerations;
- Appendix;
- any section that may be explicitly normative.

Precedence must be:

1. explicit normative marker;
2. explicit informative marker;
3. adapter-specific metadata;
4. conservative unknown handling.

An unknown section with a normative keyword must not be silently discarded solely because of its title.

## Inline code

Preserve inline code text in visible/exact evidence while preventing keyword matches originating inside protected code spans.

Required case:

```html
Clients MUST send the <code>Authorization</code> header.
```

Expected evidence/action must retain `Authorization`.

A separate case with `<code>MUST</code>` and no normative modal outside code must extract zero requirements.

## Actor

Search actor candidates only in the subject region before the matched modal. If no safe actor is found, return `None`.

Required case:

```text
A proxy MUST forward messages to clients.
```

`actor` must not be `clients`.

## Quotes/history

Add explicit handling and fixtures for quoted or historical normative language. Do not treat a quotation of an earlier requirement as a current requirement without adapter evidence.

---

# 8. Required fixed regression tests

Add named tests equivalent to:

```text
test_verify_fails_when_old_source_changes
test_verify_fails_when_new_source_missing
test_verify_fails_rehashed_dangling_requirement_reference
test_verify_fails_rehashed_wrong_summary
test_verify_recomputes_evidence_hashes
test_diff_rejects_output_equal_old_source
test_extract_rejects_output_equal_source
test_lineage_rejects_output_equal_any_input
test_measure_rejects_output_equal_ground_truth
test_diff_rejects_json_markdown_same_path
test_failed_second_write_preserves_preexisting_json
test_classification_metrics_count_unexpected_labels_as_fp
test_security_considerations_can_be_normative
test_normative_appendix_is_not_blanket_skipped
test_inline_code_identifier_preserved_but_code_modal_protected
test_actor_is_never_taken_from_post_modal_object
test_historical_blockquote_not_current_requirement
test_pipeline_uses_single_source_snapshot
```

These tests are part of the repair contract. Do not skip, xfail, weaken, or delete them to obtain green status.

---

# 9. Required full gate

From a clean clone at one final commit:

```text
uv sync --all-extras --dev --frozen
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
uv run normshift measure \
  --ground-truth benchmark/measure_suite.jsonl \
  --out evidence/m0-repair/metrics.json
uv run normshift diff \
  fixtures/synthetic/spec-v1.html \
  fixtures/synthetic/spec-v2.html \
  --profile rfc2119 \
  --json evidence/m0-repair/report.json \
  --markdown evidence/m0-repair/report.md
uv run normshift verify evidence/m0-repair/report.json --source-root .
```

Also execute and record every negative adversarial command, including source mutation, source deletion, rehashed internal inconsistency, and output collisions.

---

# 10. Evidence closeout

Create `evidence/m0-repair/M0_REPAIR_EVIDENCE.md` containing:

- exact final commit SHA;
- proof that package tip equals verified commit;
- Python/uv/platform versions;
- `uv.lock` SHA-256;
- exact commands and exit codes;
- full test count;
- benchmark result;
- corrected metrics;
- generated artifact hashes;
- negative-test evidence;
- known failures;
- unresolved risks.

Update CLAIMS so every active claim has:

- exact scope;
- supporting artifact;
- unsupported boundary;
- final verified commit;
- reviewer status.

Package with portable `/` ZIP separators and exclude `.git`, `.venv`, `.hypothesis`, caches, and temporary artifacts. Include either `.git` history, a `git bundle`, or enough signed/hashed commit material for an external auditor to inspect the verified revision.

Then stop. Do not begin M1/M2 work. Return one allowed status and request external re-audit.
