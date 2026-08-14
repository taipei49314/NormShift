# Changelog

This file records delivered repository changes and subject-bound audit history.
It does not promote an implementation or CI result to an external verdict.

## Unreleased

### Added

- Frozen M1/M2 pre-registration policy and an exact, independently approved scorer
  manifest. The scorer recomputes gates but cannot grant milestone acceptance.
- Fail-closed M1 source acquisition, offline replay, and source identity checks.
- Canonical development-only fetch recipes for ten RFC, W3C, and WHATWG document
  versions, with hash-linked sanitized response headers and license/source review
  records. Source bodies, labels, holdouts, predictions, and scores are not stored
  in this evidence root.
- Labeling, adjudication-history, and whole-document/whole-lineage blind-split
  governance contracts.
- M2 lineage-instance identity and graph-integrity foundations.
- Typed M2 semantic-change dimensions bound to strict FULL source-replay receipts;
  caller-supplied object and scope spans remain unverified `UNKNOWN` candidates.
- Strict, bounded wheel ZIP validation and platform-metadata normalization to a
  new exclusive output, plus a three-operating-system final-distribution byte
  equality gate.
- A fail-closed final release checklist with handle/dev-inode custody, sealed-root
  publication, before/after identity-size-hash snapshots, external manifest/audit
  digest anchors, and a strict detached combined-audit schema; plus explicit
  security reporting guidance.

### Changed

- Repository status now distinguishes the historical exact-subject M0 audit from
  the current descendant implementation. M1, M2, and the final combined release
  remain `EXPERIMENTAL_NOT_ADJUDICATED` / `BLOCKED` as applicable.
- Linux, Windows, and macOS CI now exercise the deterministic gates, distribution
  build/install smoke, M0 replay, development source-recipe verification, canonical
  wheel checking, and final wheel/sdist byte equality.
- PR [#14](https://github.com/taipei49314/NormShift/pull/14) established an
  internal delivery foundation on master commit
  `f6897f71834a50d2273fda033a72b31254c65935`, tree
  `34cde504fab42da8f9423cd1ca226fe492307c36`, and push CI
  [run 31462052663](https://github.com/taipei49314/NormShift/actions/runs/31462052663).
  The retained Ubuntu, Windows, and macOS final wheels were canonical and shared
  SHA-256 `b5ebc295dadb63ab2969185551ca62409e9290d9f9fba41916d188e6a833886d`;
  the sdists shared SHA-256
  `fb8f1f0add5a752cfa3a070edf0ed984835961b4f93a5c672c0f02ea6b2c4760`.
  This is internal delivery evidence, not a combined audit or release verdict.
- Master commit `fb3c0656b8150e56604502450c46ff0e2ee027f1`, tree
  `e9ed7ed05e505231a8ad2241ea6a6d83b15b6d27`, and push CI
  [run 31690202157](https://github.com/taipei49314/NormShift/actions/runs/31690202157)
  reproduced the deterministic gates locally (ruff 0, mypy 87 files, pytest 904,
  benchmark 17/17, measure 15/15) and produced byte-identical canonical wheels and
  sdists across Ubuntu, Windows, and macOS. The retained final wheel SHA-256 was
  `20570a5cb65ace7dd4a0366667735491f0118a44273d501172f2c07d4c1b2349`; the sdist
  SHA-256 was
  `b0588d45aae6a1fad2e051a70d0312d41d996d08d265843da896bee8ab38142d`.
  This is internal delivery evidence, not a combined audit or release verdict.

### Not yet delivered

- Independently controlled real blind labels, holdout membership, predictions,
  per-class M1/M2 support and metric results, and M1/M2 external verdicts.
- Integrate and independently adjudicate the M2 semantic-dimensions foundation;
  complete the definition/cross-reference graph and all pre-registered
  split/merge/moved-and-rewritten acceptance evidence.
- A final combined exact-SHA authoritative package, detached audit PASS, annotated
  software-release tag, published release, and downloaded-asset re-verification.

## Historical M0 audit evidence (not a software release)

On 2026-08-09, detached audit evidence recorded
`M0_EXTERNAL_AUDIT_PASS` for this exact subject only:

- commit: `b3af3dc26e64a3399545d179731222f6e87213c9`;
- tree: `c629e2d51fc5219514d6068a90d3453725bd8010`;
- package version: `0.3.2`;
- run ID: `20260809T132157Z-b3af3dc-m0`;
- authoritative manifest SHA-256:
  `7e95576f71fd061fc010c542b7f91dc67075cd2c7bd8bfd2b801f90c846625db`;
- detached audit JSON SHA-256:
  `88127b2a0d5985e4e00f392f031fdce7c3cc8281bdec2fb118e7fe86d83f2aac`;
- evidence publication:
  [`m0-audit-20260809-b3af3dc`](https://github.com/taipei49314/NormShift/releases/tag/m0-audit-20260809-b3af3dc).

The audit recorded P0=0, P1=0, P2=0 for its M0 scope, with M1 and M2
`NOT_ADJUDICATED` and product release `BLOCKED`. A later download-only check found
Windows backslashes in the raw names of four members of the external-audit transport
ZIP. That transport ZIP and affected inventories were replaced using the same nine
retained audit files; the audited commit, tree, candidate manifest, detached audit
JSON/Markdown, and their hashes were unchanged. This correction did not expand the
M0 verdict or turn the prerelease evidence publication into a software release.

All later commits require a new combined exact-subject package and detached audit;
Git ancestry does not carry the historical verdict forward.
