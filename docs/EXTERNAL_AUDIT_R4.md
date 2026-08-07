# NormShift M0 Repair Round 4 — External Audit

**Audit date:** 2026-08-07  
**Audited package:** `NormShift-M0-R4` (later re-export set)  
**Bundle HEAD:** `878bfd3a6bb7b649652e81936216277fc8151d5e`  
**Git tree:** `da83272e68f4a5d324f63917d5a52dafac7e04c9`  

## External verdict

```text
M0: M0_PARTIAL
M1: NOT_ADJUDICATED
M2: NOT_ADJUDICATED
Production / Release: BLOCKED
```

Round 4 is the strongest NormShift package so far. It closes most Round-3 findings with substantive implementation, not claim-only changes. The exact package subject is healthy under the externally available test environment, the archive is byte-identical to Git, official evidence is relocatable, and the original Round-4 red cases pass.

M0 is not released because three trust-core invariants remain false under same-class counterexamples:

1. complete canonical replay still accepts a byte-distinct, digest-distinct report containing `-0.0` where production emits `0.0`;
2. source-reference validation is not canonical or platform-independent, and malformed refs can verify successfully;
3. historical-authority filtering still treats a bare word such as `previous` as sufficient history framing, suppressing current obligations and leaking common historical paraphrases.

The latest re-export manifest also splits package attestation from the earlier full gate manifest rather than providing one authoritative, complete manifest.

---

# 1. Package identity and archive integrity

## 1.1 Actual submitted hashes

```text
NormShift-M0-R4.bundle
89427b1773e0b4b792892bc7ad61a1a78c9bc59100c2c0811b8ebaed683e530e

NormShift-M0-R4-Source.zip
4ba5c032ececb4c548fd715911fae48a02ac8444f26052d46b21aaf6442d5961

NormShift-M0-R4-MANIFEST.json
5a2aef267dc487e7eea1e2162f66116192f9b44ed9ab802f4b7a1c762729ee01
```

All three uploaded `.sha256` sidecars match the actual bytes.

## 1.2 Bundle

```text
HEAD = 878bfd3a6bb7b649652e81936216277fc8151d5e
TREE = da83272e68f4a5d324f63917d5a52dafac7e04c9
complete history = yes
git fsck --full --strict = pass
clean clone = yes
```

The last commit adds `.gitattributes` to force LF; the exact final subject, not only its parent implementation commit, was tested externally.

## 1.3 Source.zip versus Git

```text
Git tracked files: 187
Archive files: 187
Missing: 0
Blob mismatches: 0
Extras: 0
Duplicate entries: 0
Unsafe / traversal / backslash entries: 0
```

The archive is a byte-exact representation of the package tree.

## 1.4 Evidence relocation

The packaged Round-4 report verifies in all tested layouts:

```text
bundle clean clone       -> VERIFY OK, FULL
Source.zip extraction    -> VERIFY OK, FULL
unrelated relocated path -> VERIFY OK, FULL
```

Source mutation and deletion are rejected:

```text
mutated old source -> exit 1
missing new source -> exit 1
```

---

# 2. Independent execution

## 2.1 Environment

```text
External Python: 3.13.5
External uv: 0.10.0
Required project Python: 3.12+
```

Network access was unavailable. `uv sync --frozen --all-extras --dev` attempted to obtain Python 3.12 and failed at the network boundary. Hypothesis, Ruff, and mypy were not locally installed.

The absence of these tools is recorded as an external audit limitation, not silently treated as a pass.

## 2.2 Tests

```text
pytest excluding tests/unit/test_hypothesis_editorial.py:
145 passed

Unavailable Hypothesis tests:
2

Manual deterministic idempotence samples:
500,000 passed
```

The manual samples do not replace or impersonate a native Hypothesis run. They provide supplemental evidence only.

The submitted full gate manifest reported:

```text
collected = 147
passed = 147
failed = 0
skipped = 0
```

The external collection confirms that the two unavailable Hypothesis tests account for the difference between 145 and 147.

## 2.3 Functional gates

```text
benchmark: 17/17 passed
measure: 15/15 passed
extract_f1: 1.0
alignment_f1: 1.0
classification_f1: 1.0
fresh report verify: PASS, FULL
```

Fresh generated artifact hashes match the full submitted manifest:

```text
report.json
cb4a2337e8368b3493d76932d4d119cb1fb5b2bae0d4972ed335a34969360187

report.md
bbd3ebab5352c22436c96a4ee04832be62df69fbab796b8a1b6dda3b1784f262

metrics.json
71705ea535f12288c8a99aa61108f9bdbfdf1f120431e086e6975145e4b9c5b4
```

---

# 3. Accepted Round-4 repairs

The following behavior is accepted and should be frozen in the next repair:

- exact final package commit no longer has the Round-3 status-only test failure;
- no tracked post-gate status commit is present in the submitted bundle;
- duplicate JSON keys are rejected at nested and top-level objects;
- explicit `NaN` / `Infinity` tokens, numeric strings, booleans in float fields, missing canonical fields, unknown fields, tool-version changes, provenance changes, and list reordering are rejected by the existing matrix;
- official generation uses `--source-root` and emits relative paths;
- official evidence verifies after relocation and Source.zip extraction;
- source mutation and deletion are detected;
- the fixed benchmark and measurement suites remain green;
- special output entries, input/output collisions, output ancestry, ordinary-file rollback, backup-cleanup reporting, and parent-chain cleanup remain green;
- `verification_scope=FULL` and `verification_scope=CONTENT_ONLY_OVERRIDE` are emitted for successful normal and override verification;
- all exact historical examples named in the Round-4 mission pass;
- Source.zip is byte-exact to the Git tree.

Do not redesign these accepted areas in Round 5.

---

# 4. M0 blocker P0-01 — canonical replay collapses signed zero

## Reproduction

Starting from the production-generated report:

1. find an alignment float whose generated value is `0.0`;
2. change only that value to `-0.0`;
3. recompute the existing unkeyed integrity digest;
4. run the real CLI verifier.

Observed:

```text
$ normshift verify cli-negative-zero.json --source-root <repo>
OK integrity=7e76f9d2aaaaaf7ebda16825561f21bb7c73968b57e688b6064605c7722df892 verification_scope=FULL
exit=0
```

The accepted report is byte-distinct and digest-distinct from the production report. The production pipeline did not emit it.

## Root cause

The verifier first compares canonical submitted data with the Pydantic dump, but the final replay comparison uses Python mapping equality:

```python
if r_wo != l_wo:
    ...
```

Python considers:

```python
-0.0 == 0.0
```

Therefore the claimed exact canonical replay is not exact.

## Required repair

- compare complete report payloads, excluding only the typed integrity envelope, using canonical encoded bytes rather than Python numeric equality;
- define one signed-zero policy: reject negative zero or normalize every generated and submitted zero to positive zero before integrity and comparison;
- recursively reject non-finite floats after parsing, including overflow forms such as an exponent that Python converts to infinity;
- preserve the accepted strict JSON and complete source replay architecture.

This is a trust-core blocker even though signed zero usually has no business meaning: NormShift claims that verification identifies the unique product of the deterministic pipeline. Two different accepted evidence products make that claim false.

---

# 5. M0 blocker P0-02 — source refs are not uniquely portable

## 5.1 Full verification accepts non-normalized aliases

The following reports were created by changing only `DocumentSnapshot.path` and matching `Provenance.local_path`, then recomputing the digest:

```text
./fixtures/synthetic/spec-v1.html
fixtures//synthetic/spec-v1.html
fixtures/./synthetic/spec-v1.html
```

All returned:

```text
verification_scope=FULL
exit=0
```

The generator normalizes these paths, so these accepted reports are not the unique production representation.

## 5.2 Override mode accepts malformed declared refs

With correct source bytes supplied through `--old-source` and `--new-source`, the following declared refs all returned `exit=0` and `CONTENT_ONLY_OVERRIDE`:

```text
""
"."
"..\\outside\\old.html"
"\\server\\share\\old.html"
"file:///tmp/old.html"
"a\\b.html"
```

The backslash traversal and UNC-like values are especially important because validation currently depends on the host platform's native `Path` parsing. A report is specified to contain POSIX refs and must be interpreted identically on Windows and POSIX.

## Root cause

- `_resolve_source_path` validates with native `Path(declared).parts` rather than a platform-independent POSIX grammar;
- override mode bypasses root-based canonical recomputation and then rebinds the live report to the submitted ref;
- full mode resolves source bytes but passes the submitted spelling back into the live report rather than comparing it with the normalized root-relative spelling.

## Required repair

Create one shared portable-ref parser/validator for both generation and verification:

```text
input string
→ reject empty / "."
→ reject backslash, URI syntax, drive form, UNC/rooted form
→ reject empty segments, ".", "..", repeated separators
→ parse as PurePosixPath
→ require normalized_ref == submitted_ref
```

For `FULL` verification:

```text
resolve source under root
→ recompute candidate.resolve().relative_to(root.resolve()).as_posix()
→ require exact equality with declared ref
→ pass recomputed ref into replay
```

For `CONTENT_ONLY_OVERRIDE`:

- retain the content-only scope;
- still require the declared logical ref to pass the same canonical POSIX validator;
- do not claim path attestation.

---

# 6. M0 blocker P0-03 — historical authority still uses bare-word suppression

All exact Round-4 mission examples pass, but same-class cases show that the underlying invariant is not closed.

## False negatives: current obligations suppressed

```text
The previous value MUST be retained.
→ 0 requirements

The previous section MUST be ignored by legacy parsers.
→ 0 requirements

Unlike the previous specification, clients MUST retry.
→ 0 requirements
```

These are current requirements. The word `previous` describes an object or contrast; it does not make the modal historical.

## False positives: historical obligations extracted

```text
The prior specification said clients MUST retry.
→ extracted as current MUST

The earlier version said clients MUST retry.
→ extracted as current MUST
```

Mixed example:

```text
Clients MUST abort, because the prior specification said servers MUST retry.
→ two current MUST requirements extracted
```

Only the first modal is current.

## Root cause

The historical-left regex includes a bare `\bprevious\b`, while other common historical framing is absent. The result is still keyword proximity, not a bounded relationship between:

```text
historical modifier
+ specification/version/draft/text noun
+ reporting verb
+ the specific modal occurrence
```

## Required repair

- remove bare `previous` as a sufficient historical marker;
- require a bounded reporting frame for `previous/prior/earlier/old` when it describes a standard, specification, version, draft, or quoted text;
- preserve current uses such as previous value/state/section, previous implementations, and previously assigned identifiers;
- evaluate each modal occurrence separately;
- retain current clauses in mixed historical/current sentences;
- suppress only the historical clause.

---

# 7. High-priority non-blocking findings

## P1-01 — historical commentary contaminates current requirement identity

Changing only a historical quote while leaving the current requirement unchanged:

```text
old: previous spec said SHOULD retry, but clients MUST reconnect
new: previous spec said MUST retry, but clients MUST reconnect
```

produces:

```text
AMBIGUOUS
```

The current `MUST reconnect` obligation did not change. The false event occurs because `normalized_text`, fingerprint, and alignment evidence retain the entire block, including the filtered historical clause.

Recommended repair: keep `original_text` as source evidence, but derive the current requirement's semantic text/fingerprint from the bounded current modal clause.

## P1-02 — malformed Unicode produces an unhandled traceback

A valid JSON string containing an escaped unpaired surrogate passes parsing and later crashes canonical UTF-8 encoding:

```text
UnicodeEncodeError: surrogates not allowed
exit=1 with traceback
```

The command does fail, so this is not a false PASS. It should nevertheless return a clean verifier error and machine-readable scope, not an internal traceback.

## P1-03 — final attestation is split across two manifests

The first/full Round-4 manifest records the exact commands, gate-log hashes, `147 passed`, benchmark, measurement, artifact hashes, and matrices, but it pins a different bundle byte hash from the later re-export.

The later re-export manifest correctly pins the submitted bundle hash and same commit/tree, but omits the full gate data required by the Round-4 package contract. It does not cryptographically reference the earlier full manifest.

The code subject can still be externally audited, and the source archive is unchanged, but the three-file package is not self-contained as one authoritative attestation.

Required packaging repair: produce one final complete manifest containing the current bundle hash and every required gate field. Do not use an unlinked overlay manifest.

## P1-04 — exact-package red-test contract is only partly represented in-tree

The code contains the behavioral strict/path/history/transaction tests. Several exact-package tests named in the mission are not present as executable in-tree or submitted external-verifier code, including manifest/log parsing and archive equality tests.

This external audit independently performed those checks. Round 5 should include the external package verifier as a reproducible script or fully record its output in the single authoritative manifest.

---

# 8. Why this is not a rollback to R3

Round 4 materially improved NormShift:

```text
R3: final subject had a deterministic pytest failure
R4: exact final subject passes all externally runnable tests

R3: duplicate/coerced/defaulted JSON passed
R4: named strict cases are rejected

R3: official generation could emit nonportable absolute paths
R4: official package evidence is portable and relocatable

R3: required mixed historical examples failed
R4: required examples pass

R3: staging could leave invocation-created parents
R4: parent-chain cleanup tests pass
```

The remaining work is a narrow generalization step. Do not reopen accepted metrics, benchmark, ordinary rollback, archive identity, adapters, lineage, M1, or M2.

---

# 9. External limitations

The external runtime did not provide:

- Python 3.12;
- native Hypothesis;
- Ruff;
- mypy;
- network access required for `uv sync` to obtain missing artifacts.

Accordingly, this audit does not claim an independent native rerun of those four gates. The submitted full manifest records them as green; the external audit independently ran every available functional and behavioral gate and found deterministic blockers that do not depend on those unavailable tools.

---

# 10. Next action

Execute only `GROK_M0_REPAIR_ROUND5.md`.

Maximum implementer status after repair remains:

```text
M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT
```

Do not start M1/M2, add adapters, expand lineage, build a dashboard, or change benchmark labels.
