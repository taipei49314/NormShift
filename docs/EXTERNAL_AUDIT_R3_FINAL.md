# NormShift M0 Repair Round 3 — Final External Audit

**Audit date:** 2026-08-07 (Asia/Taipei)  
**Audit subject:** `NormShift-M0-R3-MANIFEST.json`, `NormShift-M0-R3.bundle`, `NormShift-M0-R3-Source.zip`  
**Package commit:** `bf7ee8dfbf9e5ef3740c4a28efffdb94f6ae32d3`  
**Package tree:** `c546ef3ee2250e70a4aa1ca424aa78b09a478a7f`

## Verdict

```text
M0: M0_PARTIAL
M1: NOT_ADJUDICATED
M2: NOT_ADJUDICATED
Production / Release: BLOCKED
```

`P0` in this report means **M0 acceptance blocker**. It does not imply that every finding is a remote-security vulnerability.

Round 3 is materially better than Round 2. The package identity is coherent, `Source.zip` is byte-exact, the official evidence relocates, full extraction/alignment/classification replay exists, ordinary filesystem rollback is much safer, and the benchmark/measurement gates remain green.

M0 is still not accepted because four required trust invariants remain false:

1. the exact package commit does not pass the test gate claimed by its manifest/state;
2. the verifier accepts non-canonical or parser-ambiguous JSON before replay;
3. report generation can emit absolute paths while labeling them `source_root_relative`;
4. historical-framing logic both hides current requirements and leaks historical requirements.

A smaller transaction-preflight defect also remains: a failed multi-output staging operation can leave a parent directory that the invocation created.

---

# 1. Package identity and source archive

## 1.1 Recomputed artifact hashes

```text
NormShift-M0-R3-MANIFEST.json
  af552fe2f5f499a870cef0f24de47e8f826c3fa0d294407e630ede573b13fa3b

NormShift-M0-R3.bundle
  54f484a3f892a23d75c0c57193a267c6f7759614a4ba713c364d0aa6329cd6ad

NormShift-M0-R3-Source.zip
  ef9c631aa2ecce1a5b7ae41ad7567bf637ee53646a79370dfcefcdbf0862a4c9
```

## 1.2 Bundle verification

```text
bundle HEAD: bf7ee8dfbf9e5ef3740c4a28efffdb94f6ae32d3
bundle tree: c546ef3ee2250e70a4aa1ca424aa78b09a478a7f
complete history: PASS
git fsck --full --strict: PASS
clean clone: PASS
```

## 1.3 Source archive versus Git blobs

```text
Git-tracked files: 175
Source.zip tracked files: 175
Missing: 0
Blob mismatches: 0
Extra files: 0
Unsafe/traversal paths: 0
Backslash paths: 0
Duplicate ZIP names: 0
Cache/virtual-environment entries: 0
```

All 46 manifest-listed fixture hashes matched bytes extracted from `Source.zip`. All four listed artifact hashes also matched extracted archive bytes.

**Accepted conclusion:** Round 2's split identity and line-ending conversion problem is closed.

---

# 2. External execution results

The audit runtime had Python 3.13.5 and the runtime dependencies already present. It did not have Python 3.12, Hypothesis, Ruff, or mypy available offline. `uv sync --frozen --offline --all-extras --dev` could not complete because the locked Pygments wheel was absent from the local cache.

This limitation is recorded precisely; it does not erase the deterministic package-subject failure or the independently reproduced runtime defects below.

| Gate | External result |
|---|---|
| Complete bundle clone | PASS |
| Git fsck | PASS |
| Source.zip versus Git tree | PASS, 175/175 |
| Packaged report verification | PASS |
| Extracted Source.zip report verification | PASS |
| Relocation to unrelated directory with spaces | PASS |
| JSON determinism | PASS, byte-identical |
| Markdown determinism | PASS, byte-identical |
| Benchmark | PASS, 17/17 |
| Measurement suite | PASS, 15/15; extraction/alignment/classification F1 = 1.0 |
| Exact package commit tests, excluding unavailable Hypothesis file | **FAIL: 105 passed, 1 failed** |
| Parent implementation commit `e512cb7`, same exclusions | PASS: 106 passed |
| Manual editorial-normalization property samples | PASS: 100,000 |
| Manual whitespace-normalization property samples | PASS: 100,000 |
| Ruff / mypy | NOT EXTERNALLY RERUN |
| Two Hypothesis tests | NOT NATIVELY RERUN |

Regenerated official artifacts matched the package:

```text
report.json
  7d581bc2bb85d5114b53b2f513f50f96bf1a5f856021a3e513bff4a318ffed54

report.md
  f3df26977286de31c977f2d85d7522372f98e9c675b62132c7d786b50a8e3c42

metrics.json
  fb76642f9178b3bfb6e2bd2bb85ded0b75d18aea003f50af461d51314e7a8808
```

---

# 3. Accepted Round-3 work — freeze it

The next repair must preserve these behaviors rather than rewrite them:

1. Bundle HEAD/tree and archive identity are coherent.
2. `Source.zip` is a byte-exact Git archive with safe paths.
3. The official packaged report verifies in a clean clone, after relocation, and from the extracted archive.
4. Source mutation and source deletion are detected.
5. Extraction, alignment, and classification are replayed through the production pipeline.
6. Exact changes to requirement/change confidence, known provenance fields, document family, versions, list order, summary, and known integrity fields are rejected.
7. Extra nested model fields are rejected by closed Pydantic models.
8. Existing directory, live symlink, dangling symlink, FIFO, Unix socket, device, hardlink alias, and input/output ancestry cases are rejected.
9. Ordinary existing-file rollback restores prior bytes under tested commit failures.
10. Backup-cleanup failure reports retained backup paths.
11. Destination-directory fsync hooks run after success and rollback restoration.
12. Benchmark 17/17, measurement 15/15, false-positive accounting, gate-only `forbid`, and deterministic output remain green.

---

# 4. M0 acceptance blockers

## P0-01 — The exact packaged subject did not pass its claimed test gate

### Submitted claim

The package identifies commit `bf7ee8df...` and records a green `pytest -q` result with `108 passed`.

### External result

On that exact package commit, excluding only the two unavailable Hypothesis-decorated tests:

```text
105 passed, 1 failed
```

The deterministic failing test is:

```text
tests/e2e/test_m0_repair_round2.py::test_claims_pin_exact_verified_commit
```

At package tip:

```text
MISSION_STATE.status = M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT
MISSION_STATE.last_verified_commit = null
```

The test requires a non-null 40-character commit when the status is pending external audit.

The immediately preceding implementation commit, `e512cb7...`, returns:

```text
106 passed
```

The final commit changes only `MISSION_STATE.json`: it promotes the status and inserts the claimed gate results. The evidence is therefore consistent with a gate run on the parent implementation state, followed by a status-only commit that was not retested. Even if both unavailable Hypothesis tests pass, the exact package subject would be `107 passed, 1 failed`, not `108 passed`.

A new Round-3 test also contains:

```python
assert "externally attested" in claims.lower() \
    or "package identity" in claims.lower() \
    or True
```

The terminal `or True` makes the assertion incapable of failing.

### Why this blocks M0

The package's own exact-subject evidence claim is false, and its failure list is empty despite a deterministic failing test.

### Required repair

- Return in-tree status to `M0_PARTIAL` during repair.
- Remove every unconditional truth branch.
- Replace the obsolete self-referential SHA test with coherent external-attestation semantics.
- Create the final package commit **before** running gates.
- Clone and test that exact commit.
- Make no tracked commit after the successful gate.
- Derive manifest counts from captured exact-subject logs.

---

## P0-02 — The verifier accepts non-canonical and parser-ambiguous JSON

Round 3 correctly catches many semantic field changes after replay. The remaining defect is earlier: malformed or non-canonical submitted JSON is normalized before comparison.

### Accepted wrong primitive types

After updating the unkeyed digest, each of these independently returned `exit 0`:

```text
old_document.byte_length: integer → decimal string
old_document.provenance.byte_length: integer → decimal string
old_requirements[0].confidence: number → decimal string
old_requirements[0].structural_index: integer → decimal string
changes[0].confidence: number → decimal string
alignment_score.actor_action_similarity: number → true
alignment_score.actor_action_similarity: number → decimal string
```

### Accepted omitted canonical fields

Each of these also returned `exit 0` when the current value could be recreated from a model default:

```text
old_document.source_ref_mode removed
old_requirements[0].structural_index removed
old_requirements[0].condition removed when null
old_document.provenance.fetch_metadata removed when empty
```

### Accepted conflicting duplicate keys

A raw report containing duplicate top-level `tool_version` keys returned `exit 0` when the final occurrence held the expected value. A duplicate nested `byte_length` key behaved the same way.

Python's ordinary `json.loads()` uses last-key-wins semantics. Another consumer can use first-key-wins semantics and interpret the same bytes differently.

### Root cause

```text
ordinary json.loads()
+ no duplicate-key detector
+ shallow nested JSON Schema
+ non-strict Pydantic coercion/defaulting
+ comparison only after input normalization
```

### Why this blocks M0

The verifier proves equality of a repaired/coerced in-memory model, not exact canonical validity of the submitted evidence representation. This contradicts the Round-3 claim of complete canonical replay.

### Required repair

Before source replay:

1. Reject duplicate keys at every object depth.
2. Reject non-finite constants such as `NaN` and `Infinity`.
3. Enforce exact JSON primitive types without bool/string-to-number coercion.
4. Require all canonical report fields rather than silently creating omitted defaults.
5. Compare the parsed submitted object with the complete JSON-mode typed dump before replay.
6. Keep object-key order and whitespace non-authoritative; keep list order authoritative.
7. Then run the accepted full source replay and exact live-report comparison.

---

## P0-03 — Report generation can make a false portability claim

From a working directory unrelated to the sources, this command pattern succeeds:

```text
normshift diff /absolute/outside/root/old.html \
               /absolute/outside/root/new.html ...
```

The resulting report contains:

```text
old_document.path = /absolute/outside/root/old.html
provenance.local_path = /absolute/outside/root/old.html
source_ref_mode = source_root_relative
```

Results:

```text
verify --source-root <another-root>  → FAIL
verify without --source-root         → PASS while original absolute path exists
```

The verifier correctly rejects the absolute ref under `--source-root`; the generator is the component violating the invariant.

### Why this blocks M0

A report must never label an absolute workstation path as root-relative. Portability currently depends on callers happening to use relative paths beneath the current working directory.

### Required repair

Add an explicit generation root, for example:

```text
normshift diff OLD NEW --source-root ROOT ...
```

Then:

- resolve both inputs once beneath `ROOT`;
- reject traversal and symlink escape;
- store normalized relative POSIX refs in both snapshot and provenance;
- never fall back to an absolute ref under `source_root_relative` mode;
- fail closed when a portable ref cannot be represented truthfully.

---

## P0-04 — Historical framing is not scoped to the modal clause

The current filter protects broad sentence segments based on history-related words. It therefore creates both false negatives and false positives.

External matrix:

```text
The previous specification said clients MUST retry.
→ 0 requirements                                  [correct]

The previous specification said clients MUST retry
and clients MUST reconnect.
→ 1 requirement: reconnect                        [wrong historical leak]

Clients MUST retain historical records.
→ 0 requirements                                  [wrong current requirement lost]

The historically insecure protocol MUST be disabled.
→ 0 requirements                                  [wrong current requirement lost]

The previous specification said clients SHOULD retry,
but clients MUST reconnect.
→ 0 requirements                                  [wrong current requirement lost]

Clients MUST now abort, although the old version said
clients MUST retry.
→ 0 requirements                                  [wrong current requirement lost]

Because low latency was required for interoperability,
clients MUST retry.
→ 0 requirements                                  [wrong current requirement lost]

Previously, clients MUST retry.
→ 1 requirement                                   [wrong historical leak]
```

### Root cause

- Bare terms such as `historical`, `historically`, and `was required` trigger broad protection.
- Splitting on ordinary `and` incorrectly ends historical scope.
- Contrast/current-transition clauses are not modeled reliably.

### Why this blocks M0

NormShift's core object is the normative requirement. A deterministic rule that hides valid current requirements or emits obsolete ones is a semantic correctness blocker, especially because Round 3 explicitly required mixed historical/current handling.

### Required repair

Evaluate authority per modal occurrence or tightly bounded clause:

- historical reporting before a modal suppresses only that modal clause;
- ordinary coordinated historical clauses remain historical;
- explicit current transitions (`but now`, `currently`, a new sentence, equivalent deterministic markers) reopen current authority;
- incidental object/adjective uses of “historical” do not suppress a modal;
- ambiguous cases fail conservatively rather than inventing a current requirement.

Do not add an LLM.

---

# 5. Additional high-priority findings

## P1-01 — Failed multi-output staging can leave an invocation-created parent directory

Reproduction:

```text
output A: newparent/a.json
output B: existing-regular-file/b.json
```

The first parent is created and its temp file is staged. The second `mkdir()` fails because an ancestor is a regular file. Temporary files are cleaned, but `newparent/` remains as an empty directory.

This violates the requested invariant:

```text
preflight failure creates no parent directory or temporary file
```

Required repair:

- validate every destination's nearest existing ancestor before any mutation;
- reject non-directory ancestors before staging any output;
- track directories created by the invocation;
- remove only those created directories, in reverse order and only when empty, after staging/commit failure;
- never remove a pre-existing directory.

The accepted ordinary-file rollback must remain unchanged.

## P1-02 — Override verification scope is warning-only and permits malformed declared refs

With explicit `--old-source` / `--new-source`, reports containing invented or absolute declared source refs can return `exit 0`. The CLI prints a human-readable suffix indicating content-bound replay, which is better than silence, but automation still receives the same success exit and no structured scope value.

Required repair:

- validate that declared portable refs are relative and non-traversing even in override mode;
- expose `FULL` versus `CONTENT_ONLY_OVERRIDE` in machine-readable output;
- document that overrides relocate bytes and do not attest the declared logical location.

## P1-03 — The mandatory Round-3 red-test contract is incomplete

Only 15 of the 40 requested exact test names are present. Behavioral equivalents cover some missing names, but important package-subject, strict-input, override, cleanup, fsync, and external-manifest checks are absent. The unconditional `or True` demonstrates why executable assertions matter.

Round 4 must add real package-level checks, not name-only placeholders.

## P1-04 — Evidence metadata and versioning need alignment

- The manifest's exact-command list omits the required `uv sync --frozen --all-extras --dev` gate.
- It does not bind captured gate-log hashes to the package subject.
- The verifier behavior changed substantially while the tool version remains `0.3.0`.
- `pyproject.toml` still describes `M0–M2` even though M1/M2 are explicitly unadjudicated.

Round 4 should bump the patch version and regenerate evidence under the new version.

---

# 6. Final adjudication

```text
M0: M0_PARTIAL
M1: NOT_ADJUDICATED
M2: NOT_ADJUDICATED
Production / Release: BLOCKED
```

This is not a return to zero. Round 3 successfully closed package-byte identity, official evidence relocation, most full-replay omissions, and dangerous output-entry handling. Those repairs are accepted and frozen.

Round 4 must be a narrow closeout of:

```text
exact-subject attestation
strict canonical JSON input
truthful portable generation
modal-local historical authority
transaction parent-chain cleanup
```

The maximum implementer-declared status after a genuinely green exact-subject package gate remains:

```text
M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT
```
