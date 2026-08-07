# Threat Model (M0)

## Assets

- Integrity of diff reports (classification claims + evidence hashes)
- Deterministic reproducibility of JSON outputs
- Correct non-extraction of non-normative contexts

## Threats in scope (M0)

1. **Tampered report**: modified classifications/confidence without hash update  
   → Mitigated by `integrity.content_sha256` over canonical JSON excluding integrity.
2. **False keyword hits**: substrings ("mustard"), negation ("is not required to")  
   → Token boundaries + veto patterns.
3. **Informative context leakage**: code/pre/example treated as normative  
   → HTML structural ignore + informative class/role heuristics.
4. **Cross-matching similar clauses**: two near-duplicate requirements swapped  
   → Multi-signal alignment + ambiguity margin + action similarity guards.
5. **Non-determinism**: floating order / unstable serialization  
   → Sorted keys, stable IDs, fixed rounding, ordered walks.

## Out of scope (M0)

- Adversarial HTML designed to exploit browser quirks (no browser runtime)
- Cryptographic signature / key management
- Supply-chain compromise of dependencies beyond lockfile hashing in evidence
- Natural-language understanding of arbitrary legal text
