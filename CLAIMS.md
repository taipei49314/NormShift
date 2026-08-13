# Claims Register

The implementer is **not** Claim, Evidence, Audit, or Release Authority. A CI pass
is implementation evidence; it is not an external-audit verdict.

## Subject-bound package terminology

- `package_commit` and `package_tree` identify only the exact subject recorded in
  an external authoritative manifest.
- `package_identity = pending_external_attestation` means the current combined
  repository state has no external package-equality or acceptance claim.
- `externally_attested` may describe only the exact bytes named by a detached
  audit. It does not propagate through Git ancestry.
- A later M1/M2 commit may preserve audited M0 behavior, but it does not inherit
  the M0 verdict until the later combined subject is packaged and independently
  re-audited.

## Milestone status

| Subject / milestone | Status | Authority boundary |
|---|---|---|
| M0 package at `b3af3dc26e64a3399545d179731222f6e87213c9` | `M0_EXTERNAL_AUDIT_PASS` | Historical exact subject only; detached audit hash `88127b2a0d5985e4e00f392f031fdce7c3cc8281bdec2fb118e7fe86d83f2aac` |
| M0 in the future combined release subject | At most `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` before a new detached audit | The historical verdict is non-transitive |
| M1 | `EXPERIMENTAL_NOT_ADJUDICATED` | No blind acceptance result or external M1 verdict |
| M2 | `EXPERIMENTAL_NOT_ADJUDICATED` | Foundations only; no blind acceptance result or external M2 verdict |
| Distribution delivery foundation at `f6897f71834a50d2273fda033a72b31254c65935` | `INTERNAL_CI_PASS_NOT_EXTERNAL_ACCEPTANCE` | Three-OS canonical wheel and final distribution equality only; not a combined package audit |
| Final combined package / release | **`BLOCKED`** | Exact subject is not frozen, audited, tagged, or released |

The historical M0 evidence is published as the
[`m0-audit-20260809-b3af3dc` prerelease](https://github.com/taipei49314/NormShift/releases/tag/m0-audit-20260809-b3af3dc).
Its manifest SHA-256 is
`7e95576f71fd061fc010c542b7f91dc67075cd2c7bd8bfd2b801f90c846625db`.
That evidence explicitly records M1 and M2 as `NOT_ADJUDICATED` and product
release as `BLOCKED`.

## Active implementation claims

| ID | Claim | Evidence scope | Status |
|---|---|---|---|
| C1 | Reports use portable, root-relative POSIX source references and fail closed on unsafe source identity | M0 implementation and regression tests | Implemented; historical external acceptance is bound only to the M0 subject above |
| C2 | Verification uses strict JSON, canonical payload-byte equality, source replay, and bundled schemas | M0 implementation and regression tests | Implemented; a final combined subject still needs detached re-audit |
| C3 | Historical authority is determined within a bounded clause/reporting frame | M0 implementation and R4/R5 matrices | Deterministic heuristic, not universal language understanding |
| C4 | The retained M0 suites contain 17 benchmark cases and 15 measurement cases | `benchmark/` and exact-subject evidence | Local M0 evidence only; not an M1/M2 real-world accuracy claim |
| C5 | Frozen M1/M2 policy and scorer artifacts, fail-closed M1 acquisition/replay, labeling/blind-split governance, and canonical development source recipes exist | `acceptance/`, `src/normshift/{acceptance,corpus,governance}/`, and `corpus/m1-development/` | `EXPERIMENTAL_NOT_ADJUDICATED` |
| C6 | M2 lineage foundations preserve instance identity and validate graph evidence/integrity; LineageGraph v1 can be externally anchored and byte-compared to an isolated replay of caller-supplied ordered source bytes/profile/adapter | `src/normshift/lineage/`, bundled schema, CLI, and lineage tests | `EXPERIMENTAL_NOT_ADJUDICATED`; replay-only is not source custody, official identity, adjudication, or the complete M2 acceptance scope |
| C7 | Typed M2 semantic-change dimensions require a strict FULL source-replay receipt and bind primary change/requirement payloads; opt-in CLI sidecars require pre-existing receipts and caller-provided digest anchors, while unverified caller object/scope spans remain `UNKNOWN` | `src/normshift/semantic_dimensions/`, CLI, bundled schemas, and semantic-dimensions tests | `EXPERIMENTAL_NOT_ADJUDICATED`; caller-provided anchors do not establish independent custody, adjudication, or an M2 verdict |
| C8 | The exact ancestor master tree `34cde504fab42da8f9423cd1ca226fe492307c36` produced byte-identical canonical wheels and sdists on Ubuntu, Windows, and macOS | Push CI [run 31462052663](https://github.com/taipei49314/NormShift/actions/runs/31462052663); wheel SHA-256 `b5ebc295dadb63ab2969185551ca62409e9290d9f9fba41916d188e6a833886d`; sdist SHA-256 `fb8f1f0add5a752cfa3a070edf0ed984835961b4f93a5c672c0f02ea6b2c4760` | Internal delivery foundation only; rerun and re-audit the later final subject |

## Non-claims

- The current default branch is not externally accepted as one combined M0-M2
  subject.
- Development recipe evidence is not a committed real-source corpus, label set,
  holdout, prediction set, or acceptance result.
- No M1 or M2 precision, recall, F1, minimum-support, or milestone PASS is claimed.
- No final software release, production readiness, hosted service, adoption,
  universal standards coverage, cryptographic authenticity, or universal
  natural-language correctness is claimed.
- A green Linux, Windows, and macOS CI run is not a substitute for the required
  detached external audit.

The executable remaining gates are in [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md).
