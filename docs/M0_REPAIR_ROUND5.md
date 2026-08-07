# M0 Repair Round 5 — implementer notes

**Tool version:** 0.3.2  
**Status at package tip:** `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT` (implementer only)  
**package_identity:** `externally_attested`

## Scope (frozen — no features)

Only closed:

1. **Canonical representation** — payload-byte replay equality; reject signed zero and non-finite floats; clean failure on surrogate encode errors
2. **Portable source identity** — shared PurePosix `validate_portable_ref` + canonical root binding for full and override verify
3. **Clause-level normative authority** — historical only with modifier + specification-class object + reporting frame; fingerprint from current clause

## Frozen accepted R4 behavior preserved

Archive identity, relocation verify, strict JSON duplicates, matrix red tests, benchmark 17/17, measure 15/15, I/O parent-chain, scope FULL/CONTENT_ONLY_OVERRIDE.
