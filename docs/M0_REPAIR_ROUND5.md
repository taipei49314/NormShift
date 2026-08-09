# M0 Repair Round 5 — implementer notes

**Tool version:** 0.3.2  
**Status at package tip:** `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` (implementer only)  
**package_identity:** `pending_external_attestation`

Correction recorded 2026-08-09: the earlier `externally_attested` label was not
supported by a detached exact-subject audit. R4 remains the latest external verdict;
R5 behavior is implementer-verified and still awaits an authoritative package plus
clean-room re-audit.

## Scope (frozen — no features)

Only closed:

1. **Canonical representation** — payload-byte replay equality; reject signed zero and non-finite floats; clean failure on surrogate encode errors
2. **Portable source identity** — shared PurePosix `validate_portable_ref` + canonical root binding for full and override verify
3. **Clause-level normative authority** — historical only with modifier + specification-class object + reporting frame; fingerprint from current clause

## Frozen accepted R4 behavior preserved

Archive identity, relocation verify, strict JSON duplicates, matrix red tests, benchmark 17/17, measure 15/15, I/O parent-chain, scope FULL/CONTENT_ONLY_OVERRIDE.
