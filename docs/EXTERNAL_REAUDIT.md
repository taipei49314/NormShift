# NormShift M0 Repair — External Re-audit

**Audit date:** 2026-08-07  
**Audited package:** `NormShift-M0-Repair.zip`  
**Package SHA-256:** `bf3eab8db1cf2525182201f3e88e734d4399dd228ae02fd9153b0ec7f3ffa878`  
**Audit scope:** M0 trust-chain repair only. M1/M2 were not adjudicated.

## Final verdict

```text
M0: M0_PARTIAL
M1: NOT_ADJUDICATED
M2: NOT_ADJUDICATED
Release / Production: BLOCKED
```

The repair is substantive and fixes several original counterexamples. It is not an empty or cosmetic patch. However, two central M0 contracts remain bypassable:

1. `normshift verify` still validates an internally self-consistent report rather than proving that each stored requirement and change was derived from the declared source bytes.
2. The multi-artifact writer still cannot preserve all pre-existing outputs when failure occurs during the replacement phase.

The package also fails the exact-revision evidence requirement: the package commit and verified commit differ, and no Git history, bundle, or manifest is included to establish what changed between them.

These are release-blocking trust-foundation defects. The highest defensible status remains `M0_PARTIAL`.

---

## Audit environment and limitations

| Item | Result |
|---|---|
| Host Python | 3.13.5 |
| Project target | Python >= 3.12 |
| Pytest | 9.0.2 |
| Full dependency sync | BLOCKED by offline environment: `uv` attempted to download CPython 3.12.12 |
| Ruff / mypy | NOT_RUN; unavailable locally |
| Hypothesis | NOT_RUN; unavailable locally |
| Non-Hypothesis tests | **69 passed** |
| Claimed full suite | 71 passed in implementer evidence |
| Manual replacement for two idempotence properties | 20,000 + 20,000 deterministic random cases passed |

The inability to rerun Ruff, mypy, and the two Hypothesis tests is an audit-environment limitation, not counted as a repository defect. The functional rejection below comes from independently reproduced behavior.

---

# What passed independently

## Package hygiene

- 159 ZIP entries.
- No unsafe absolute or `..` paths.
- No symlink entries.
- No backslash path separators.
- No `.git`, `.venv`, `.hypothesis`, `.pytest_cache`, `__pycache__`, or bytecode in the submitted ZIP.
- The submitted evidence artifacts reproduce byte-for-byte.

## Gates reproduced

```text
pytest excluding the unavailable Hypothesis module: 69 passed
benchmark: 17/17 passed
measure: 15/15 cases
spec-v1 -> spec-v2: 9 -> 11 requirements, 11 changes
verify unmodified report: exit 0
repeat JSON report: byte-identical
repeat Markdown report: byte-identical
```

Reproduced artifact hashes:

| Artifact | SHA-256 |
|---|---|
| `report.json` | `7b6b949fbb721f5894167a007534f8e81b673e7fc83e66983b1776a1b64c77d1` |
| `report.md` | `abf7efb1c45912d696c36b1ae4cb84a6b4d6d4da9dc46841c6395b9825257af2` |
| `metrics.json` | `fb76642f9178b3bfb6e2bd2bb85ded0b75d18aea003f50af461d51314e7a8808` |
| `uv.lock` | `40424b150fedf7b9d30be4273f6abb7e5db1f636dfd54faffc24676383418978` |

## Original findings that are genuinely improved

The following original attacks now behave correctly in their direct form:

- Modifying the old source after report creation causes `verify` to exit 1.
- Deleting the new source causes `verify` to exit 1.
- `extract --out SOURCE`, `diff --json SOURCE`, `lineage --json INPUT`, and `measure --out GROUND_TRUTH` are rejected before truncation.
- JSON and Markdown outputs resolving to the same path are rejected.
- Existing hardlink and symlink aliases of the source are rejected.
- Unexpected classification labels now count as false positives in the required `allow_extra=true` example: `TP=1`, `FP=3`, `FN=0`, precision `0.25`, recall `1.0`, F1 `0.4`.
- Security Considerations and a simple explicitly normative appendix are no longer blanket-suppressed.
- The simple `Authorization` inline-code fixture preserves the identifier.
- `A proxy MUST ... to clients` no longer selects the post-modal `clients` object as actor.
- A block-level `<blockquote>` historical quotation is excluded.
- `run_diff` can consume caller-provided immutable source snapshots.
- Required schemas are present under package resources and work from an empty current directory when the source package is on `PYTHONPATH`.

These are meaningful repairs. They are not sufficient for M0 acceptance because the general invariants remain incomplete.

---

# P0-01 — The verifier still does not bind requirements to source evidence

## Required contract

The repair mission required the verifier to recompute requirement IDs and fingerprints, resolve source locators against the same adapted snapshot, and prove that exact evidence text matches source-visible text.

## Actual behavior

The verifier checks source-file SHA-256 and byte length, then checks only internal relationships inside the report. It does **not** re-extract or locate the requirements in the verified source bytes.

Five independently rehashed forgeries were accepted with exit 0:

### A. Impossible source locator accepted

A valid old requirement locator was replaced with:

```text
id:THIS-ID-DOES-NOT-EXIST|xpath:/html/body/div[999]/p[999]
```

The referencing change and evidence hashes were updated, then the report integrity hash was recomputed.

Observed:

```text
OK integrity=fbfe9bf87dd0df7e595d29357f9ee4adfdd1675297ee672c5c7e9dfae8d039d8
exit=0
```

### B. Fabricated requirement text accepted

The source file remained unchanged, but a stored requirement was changed to:

```text
Fabricated clients SHOULD upload secrets to example.invalid.
```

Its fingerprint, referencing change, change ID, evidence hashes, and report hash were recomputed. The original requirement ID was deliberately left unchanged even though the ID algorithm includes normalized text.

Observed:

```text
OK integrity=3972b91b6315d3f3c3e424a8d157aa9d6ffbed6142fd8d4775ad367397e80977
exit=0
```

### C. Arbitrary requirement ID accepted

A requirement ID was changed from its deterministic value to:

```text
0123456789abcdef
```

All internal references and hashes were updated. The verifier accepted it. This proves requirement ID recomputation is absent.

### D. Paired change with no requirement IDs accepted

An `EXCEPTION_ADDED` change was rewritten with:

```json
{
  "old_requirement_id": null,
  "new_requirement_id": null,
  "old_text": null,
  "new_text": null,
  "old_source_locator": null,
  "new_source_locator": null
}
```

The evidence hash and report hash were recomputed. The verifier accepted it, even though the mission explicitly requires paired classes to have both IDs.

### E. Forged provenance path accepted

`provenance.local_path` and `canonical_source` were changed to fabricated values while source hashes remained valid. The verifier accepted them, despite the mission requiring provenance path/canonical metadata to be structurally validated.

## Root cause

`src/normshift/verify/verifier.py` currently:

- hashes the source file but does not replay adapter + extraction;
- recomputes `fingerprint`, but not `requirement_id`;
- compares change text/locator only to the report's own requirement objects;
- does not resolve locators into the adapted source;
- does not compare evidence text to located source text;
- does not require both IDs for non-ADDED/non-REMOVED classes;
- recomputes change IDs only when both IDs happen to be present;
- does not reject duplicate change IDs or duplicate coverage;
- validates only two provenance fields.

## Impact

A report can refer to authentic source bytes while carrying invented requirements and invented change evidence. Therefore the current command proves only:

> The report is internally self-consistent and still points at source files with matching hashes.

It does not prove:

> The report's requirements and semantic changes were actually derived from those source bytes.

That is the primary M0 trust claim, so this remains P0.

## Required correction

The narrowest robust solution is deterministic replay inside `verify`:

1. Resolve both source files without basename guessing.
2. Load each source once into `ImmutableSource`.
3. Recompute and compare snapshots/provenance.
4. Re-run extraction using the report profile and declared adapter identity.
5. Compare the complete canonical requirement arrays, including IDs, locators, text, roles, modality, polarity, versions, fingerprints, and structural indexes.
6. Re-run alignment and classification.
7. Compare complete canonical changes and summary.
8. Fail closed on every difference.

Manual locator checks may still be retained, but replay is necessary to close the forgery class rather than patching individual fields.

---

# P0-02 — Multi-artifact output is not rollback-safe during commit

## Required contract

If a later artifact replacement fails, every pre-existing output must remain unchanged.

## Current test gap

The repository test named `test_failed_second_write_preserves_preexisting_json` forces failure while staging the second temporary file. No final output has been replaced at that point, so the test does not exercise the dangerous phase.

## Independent reproduction

`os.replace` was injected to succeed for the first final output and fail for the second.

Observed:

```text
raised OSError injected second commit failure
a=NEW_A
b=ORIGINAL_B
first_output_preserved=False
second_output_preserved=True
```

## Root cause

`write_transaction()` stages every temporary file, then performs sequential `os.replace()` calls without backups or a rollback journal. After the first successful replacement, the original first file is already lost.

## Impact

A disk, permission, antivirus, race, or filesystem error during the commit phase can leave a mixed output set and overwrite user content despite the command returning failure.

## Required correction

Implement a tested rollback journal:

- stage and fsync all temporary artifacts first;
- atomically move every existing final to a transaction-owned backup;
- replace finals one by one;
- on any failure, restore all backups and remove only new finals created by this transaction;
- never delete an unrelated or pre-existing path;
- clean backups only after all replacements succeed;
- document that multi-file visibility is rollback-safe, not globally atomic across directories.

The acceptance test must inject failure on the **second replacement**, not during staging.

---

# P0-03 — The package does not identify one auditable Git revision

The repair contract required proof that package tip equals verified commit and required Git history, a Git bundle, or equivalent inspectable commit material.

Submitted metadata conflicts:

```text
PACK_README.txt commit:          abe375b6a1c5c55b8cd355aaf976429c406388d9
MISSION_STATE.last_verified:    7b63dbdd23a97058085bf917d52edd3fc144fc24
M0_REPAIR_EVIDENCE final commit:7b63dbdd23a97058085bf917d52edd3fc144fc24
CLAIMS last verified commit:     pending pin
```

The ZIP contains:

- no `.git` history;
- no Git bundle;
- no signed or hash-locked evidence manifest;
- no tree hash proving that package contents equal either declared commit.

The later commit may contain only packaging metadata, or it may contain code changes. The package provides no way to determine which. Therefore the exact state that produced the evidence cannot be audited.

## Required correction

- Pin the same final verified commit in `MISSION_STATE`, `CLAIMS`, evidence, and package metadata.
- Include a `git bundle` containing that revision and its parent history.
- Include a package manifest with commit SHA, tree SHA, clean/dirty state, file hashes, artifact hashes, and the final ZIP hash.
- Generate the archive from the verified commit, not from a later unverified working tree.

---

# P1 findings

## P1-01 — `run_measure` still reads each source twice

A one-case measurement run produced:

```text
old_read_bytes_calls=2
new_read_bytes_calls=2
```

`run_measure` extracts old/new documents, then calls `run_diff`, which loads both paths again. Extraction metrics and semantic classification can therefore come from different snapshots if the filesystem changes during the case.

**Fix:** load each source once per case and pass the same immutable objects to extraction and diff.

## P1-02 — Explicit `non-normative` class is extracted as normative

Input:

```html
<section class="non-normative">
  <p>Clients MUST upload diagnostics.</p>
</section>
```

Observed: one requirement extracted.

`_is_explicitly_normative()` searches for the word `normative` inside the class string, so `non-normative` is accidentally treated as an explicit normative marker and overrides the informative decision.

**Fix:** tokenize class values and recognize exact, non-negated markers. Add direct precedence tests.

## P1-03 — Repeated inline-code token protects the wrong occurrence

Input:

```html
<p>Clients MUST compare the literal <code>MUST</code> token.</p>
```

Observed requirement action:

```text
token
```

The protected-span reconstruction searches for the normalized code fragment with `text.find()`, so it protects the first identical `MUST` outside code and leaves the actual code token unprotected. The extractor then matches the code token.

**Fix:** construct normalized text and protected offsets in one offset-aware pass. Do not recover offsets by substring search.

## P1-04 — Inline quotation/history remains authoritative

Both forms were extracted as current requirements:

```html
<p>The old text was <q>Clients MUST retry.</q></p>
<p>The previous specification stated: "Clients MUST retry."</p>
```

`QUOTE_TAGS` only affects an extracted block when the block itself or an ancestor is `<q>`/`<blockquote>`. A `<q>` descendant inside a paragraph remains part of the paragraph's matchable text.

**Fix:** protect or exclude descendant quotation spans, and add conservative historical-language fixtures. A blockquote-only regression is insufficient for the stated rule.

## P1-05 — `forbid` still corrupts classification metrics

Input:

```text
expected = [STRENGTHENED]
observed = [STRENGTHENED, ADDED]
forbid   = [ADDED]
```

The gate should fail, but ordinary multiset metrics should remain:

```text
TP=1 FP=1 FN=0 precision=0.5 recall=1.0 F1=0.6667
```

Observed:

```text
TP=0 FP=1 FN=1 precision=0 recall=0 F1=0
```

The early forbidden-label branch replaces measurement semantics with gate semantics. This violates the repair rule that gate policy must not alter TP/FP/FN.

**Fix:** always calculate multiset metrics first; apply `forbid` only to `case_passed`, `exact_pass`, and `permissive_pass`.

## P1-06 — Required evidence closeout remains incomplete

- `CLAIMS.md` leaves every `last_verified_commit` as `pending pin`.
- README/CLAIMS retain `M0_PARTIAL`, while `MISSION_STATE` and repair evidence use `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`.
- Required proof that package tip equals verified commit is absent.
- The required regression set does not include explicit source-swap, rehashed requirement-document-hash, or packaged-schema tests, although current behavior for basic source hashing/schema absence is improved.
- Negative logs are stored as UTF-16 PowerShell output and are difficult to inspect portably; this is not a correctness failure but weakens audit usability.

---

# Gate summary

| Gate | External result |
|---|---|
| ZIP path/cache hygiene | PASS |
| Non-Hypothesis pytest | PASS — 69 |
| Two Hypothesis tests | NOT_RUN — dependency unavailable |
| Manual normalization idempotence probes | PASS — 40,000 total cases |
| Benchmark | PASS — 17/17 |
| Measure suite | PASS — 15/15 |
| Deterministic JSON/Markdown | PASS |
| Submitted artifact hashes reproduce | PASS |
| Source mutation/deletion direct attacks | PASS |
| Input/output collision direct attacks | PASS |
| Hardlink/symlink collision | PASS |
| Required extra-label F1 example | PASS |
| Source-locator/evidence binding | **FAIL** |
| Requirement ID recomputation | **FAIL** |
| Paired change referential invariant | **FAIL** |
| Commit-phase multi-output rollback | **FAIL** |
| Exact verified-revision evidence | **FAIL** |
| Ruff | NOT_RUN |
| mypy | NOT_RUN |

---

# Adjudication

NormShift has progressed materially. The repair shows that Grok understood the concrete counterexamples and implemented real defenses around source hashes, path aliases, packaged schemas, and classification false positives.

The remaining issue is architectural rather than cosmetic:

> The project still trusts a report once the report has been made internally coherent, instead of reconstructing the report from the source evidence it claims to represent.

Likewise, the output writer stages safely but does not transact safely once replacement begins.

Accordingly:

```text
M0_PARTIAL
```

is the only defensible status. M1/M2 must remain frozen and unadjudicated. No new feature work should begin until the round-two repair mission passes an independent re-audit.
