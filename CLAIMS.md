# Claims Register

Implementer is **not** Claim / Evidence / Audit / Release Authority.

## Package identity terminology

- **package_commit / package_tree**: recorded only in the **external** package MANIFEST / bundle HEAD.
- **package_identity = pending_external_attestation**: no package equality claim exists yet.
- **package_identity = externally_attested** is permitted only after a detached audit
  binds one frozen authoritative manifest to its exact package bytes.
- One authoritative external MANIFEST per package (no unlinked re-export overlay).

## Milestone status

| Milestone | Status |
|-----------|--------|
| M0 | During repair `M0_PARTIAL`; after green exact-subject gate → max `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` |
| M1 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| M2 | `EXPERIMENTAL_NOT_ADJUDICATED` |
| Production / Release | **BLOCKED** |

## Active claims

| ID | Claim | Scope |
|----|-------|-------|
| C1 | Portable reports verify with `--source-root` using canonical PurePosix refs | M0 |
| C2 | Verify uses strict JSON + canonical payload-byte equality (not Python float equality) | M0 |
| C3 | Historical authority is clause-local reporting-frame based | M0 |
| C4 | Frozen 17-case benchmark / 15-case measure | M0 |

## Non-claims

- Not production/release ready.
- Not audit-passed until external re-audit of the package subject.
- M1/M2 not complete.
