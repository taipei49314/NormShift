# Benchmark Method

## Design principles

1. **Immutable expected labels** — cases are the contract; do not relabel to pass.
2. **Focused assertions** — many cases use `focus_substrings` so unrelated
   collateral changes in multi-clause fixtures do not hide the target signal.
3. **Negative cases** — codeblocks / mustard / not-required assert zero
   extractions / forbidden classes.
4. **Integrity & determinism** — first-class cases, not side tests only.

## Pass criteria

A case passes when observed classifications satisfy its JSONL rule
(`expected_classifications`, optional `forbid_classifications`, optional
`check_verify_tamper` / `check_determinism`).

The CLI exits non-zero if any case fails.

## Non-claims

Passing the benchmark does **not** mean NormShift understands arbitrary
natural-language standards. It means the implementation satisfies the fixed
adversarial suite under the documented profiles.
