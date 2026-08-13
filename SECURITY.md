# Security Policy

## Support status

NormShift has no final production software release and offers no security-support
SLA. The current default branch is development software: M1 and M2 are
`EXPERIMENTAL_NOT_ADJUDICATED`, and the combined release is `BLOCKED`.

| Subject | Support status |
|---|---|
| Current `master` | Best-effort development triage only; not production supported |
| `m0-audit-20260809-b3af3dc` | Immutable historical M0 audit evidence, not a supported software release |
| Any unmerged branch or local build | Unsupported |

The historical M0 audit verdict is bound only to commit
`b3af3dc26e64a3399545d179731222f6e87213c9` and its recorded package bytes. It
does not certify descendant commits or a final M0-M2 release.

## Reporting a vulnerability

This repository has GitHub Issues enabled. It does not currently publish a private
security email address, and GitHub private vulnerability reporting is not configured.
Do not guess an address or send a report to an unrelated account.

- For a non-sensitive security hardening issue, open a
  [GitHub issue](https://github.com/taipei49314/NormShift/issues/new).
- If the report contains an exploit, secret, private source, or other details that
  should not be public, do **not** post those details. Open only a minimal issue with
  the title `Security contact request`, the affected commit/version, and a broad
  impact category. Ask the repository owner to provide a private route before
  transmitting reproduction details.
- If no private route is provided, keep sensitive details out of the public issue.
  This project does not claim confidential intake that it has not configured.

Include, when safe to disclose:

- the exact commit, package, operating system, and Python version;
- the command and untrusted input shape that triggers the behavior;
- expected versus observed behavior and whether the result is a false success;
- a minimal reproduction without credentials, proprietary standards text, blind
  labels, holdout membership, or personal data;
- relevant hashes, exit codes, and logs with secrets removed.

Do not upload live credentials, undisclosed blind-evaluation material, copyrighted
source bodies that the repository is not authorized to retain, or weaponized public
proofs of concept.

## Security-relevant scope

Reports are especially useful for:

- path traversal, symlink, junction, hardlink, archive-alias, or case-collision
  acceptance;
- verifier, scorer, provenance, manifest, checksum, or package false-success paths;
- duplicate-key, non-canonical JSON, unsafe URL/redirect, source-identity, or
  exact-root custody bypasses;
- output overwrite, rollback, or input/output ancestry failures;
- wheel ZIP flag, metadata, layout, decompression-bound, canonicalization, or
  concurrent-output replacement bypasses;
- release asset, SBOM, distribution, or tag/commit identity mismatches.

The threat model is documented in [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).
Source and third-party licensing boundaries are documented in
[`corpus/m1-development/curator/LICENSE-INVENTORY.md`](corpus/m1-development/curator/LICENSE-INVENTORY.md)
and [`LICENSE`](LICENSE).

## Triage and disclosure

Maintainers may reproduce a report in an isolated environment, classify the affected
subject, add a failing regression test, and fix it through a reviewed PR. No response
or remediation deadline is promised. A fix is not considered released until the
applicable exact-SHA CI, package, audit, tag, and download-verification gates in
[`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) pass. Historical evidence is retained;
it is not silently edited into a PASS for a different subject.
