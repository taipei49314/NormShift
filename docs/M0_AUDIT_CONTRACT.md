# M0 Exact-Subject External Audit Contract

This contract governs the independent review of one frozen NormShift M0 package.
It does not authorize the reviewer to edit production code, fixtures, labels,
thresholds, or the authoritative pre-audit manifest.

## Subject and authority

The audit subject is identified only by the authoritative manifest's
`package_commit`, `package_tree`, package version, run ID, and artifact hashes.
The implementation authority may prepare a candidate with status
`M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`; only a detached reviewer attestation can
grant an externally accepted M0 verdict for those exact bytes.

M1 and M2 remain `EXPERIMENTAL_NOT_ADJUDICATED`, and release remains `BLOCKED`,
throughout this M0 audit. This contract makes no production, hosted-service,
cryptographic-authenticity, universal-language-correctness, accuracy, adoption,
M1, M2, or M3+ claim.

## Reviewer isolation

The reviewer must:

1. start from the frozen package in a filesystem location unrelated to the
   implementer's checkout;
2. use a fresh Python 3.12 environment and no editable package installation;
3. receive only the package products, this contract, the frozen expected-label
   files, and the public exact commit reference;
4. refrain from changing production code or expected outcomes;
5. retain commands, exit codes, environment details, hashes, and findings in a
   detached `EXTERNAL-AUDIT.md`.

## Required package products

- authoritative pre-audit manifest and its JSON schema;
- full Git bundle and canonical-prefix `Source.zip`;
- wheel and sdist;
- CycloneDX 1.5 SBOM exported from the frozen runtime dependency graph;
- checksums, command logs, JUnit results, benchmark/measure evidence, deterministic
  report pairs, and this audit contract.

The manifest must not hash itself. Its SHA-256 is recorded by the detached audit
attestation after the candidate is frozen.

All build-gate environments, caches, Hypothesis state, pytest state, and Python
bytecode must live in an ephemeral directory outside the exact Git checkout. The
checkout must remain free of tracked, untracked, and ignored state after all gates.

The bundled package verifier is a fail-closed package **preflight**. Its `ok`
field only means that the retained candidate passed its declared byte, structure,
rebuild, install, and replay checks. It never grants an external-audit verdict,
never changes M0 beyond `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`, and never
unblocks release. The independent reviewer must still rerun every procedure below
and issue a detached attestation.

## Required procedure

The reviewer must complete every item below. `SKIP`, `XFAIL`, `XPASS`, `NOT_RUN`,
`BLOCKED`, a non-zero required command, a missing log, or a subject/hash mismatch
is not a PASS.

1. Strictly parse and schema-validate the manifest, rejecting duplicate keys,
   non-finite numbers, negative zero, unknown critical fields, unresolved
   references, and dishonest milestone states.
2. Verify every declared artifact and log by byte length and SHA-256.
3. Run `git bundle verify`, clone the bundle, run `git fsck --full --strict`, and
   confirm exact HEAD and tree.
4. Inspect `Source.zip` before extraction. Reject duplicate, ambiguous-case,
   backslash, rooted, traversal, symlink, special, extra, missing, or wrong-prefix
   entries; validate original central-directory names before platform path
   normalization, require matching local-header names, and compare every archived
   byte to the matching Git blob.
5. Run frozen dependency sync, Ruff, strict mypy, the complete pytest suite, all
   M0 R4/R5 regression modules, benchmark 17/17, measure 15/15, diff, and FULL
   verification.
6. Confirm the canonical numeric, strict JSON, portable source reference,
   source mutation/deletion, modal-local history, transaction, path-entry,
   rollback, cleanup, Unicode, archive, relocation, and package corruption
   matrices all return their frozen expected outcomes through public paths.
7. Generate two independent report JSON, Markdown, and metrics runs and compare
   each logical product byte-for-byte.
8. Verify a valid report with `verification_scope=FULL` in an unrelated relocated
   directory and from the extracted source archive.
9. Install the wheel and sdist into separate fresh environments outside both
   source trees. Confirm metadata name/version, `normshift` entry point,
   `normshift --version`, packaged schemas, help, diff, and FULL verify.
10. Validate the CycloneDX SBOM structure, exact NormShift root identity, generator
    record, non-empty dependency inventory, lockfile digest, normalized
    name/version/source inventory, and wheel/sdist runtime requirements.
11. Recompute all reported counts, outcomes, metrics, and hashes from retained raw
    inputs rather than accepting prose summaries.

Portable-path evidence must include Windows and Linux. macOS must pass the exact
commit's required CI job; a separate macOS clean-room run is optional and must not
be claimed when unavailable.

## Verdict and failure policy

The detached attestation records the manifest SHA-256, run ID, commit, tree,
artifact digests, commands, results, residual limitations, and P0/P1/P2 findings.
Any P0/P1, false-success artifact, changed expected label, missing required case,
or mismatch invalidates the candidate. A repair requires a new PR, new exact
commit/tree, new package run ID, and complete re-audit; audited artifacts are never
patched in place.
