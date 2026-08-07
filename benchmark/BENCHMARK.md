# NormShift M0 Benchmark

## Purpose

Fixed adversarial cases that define the M0 correctness contract for local HTML
normative extraction, alignment, classification, integrity verification, and
determinism.

## Ground truth

Cases live in `ground_truth.jsonl` (one JSON object per line). Expected labels
are part of the mission contract and must not be weakened to force a pass.

## Cases (immutable intent)

| ID | Intent |
|----|--------|
| 01 | SHOULD → MUST = STRENGTHENED |
| 02 | MUST → SHOULD = WEAKENED |
| 03 | MUST send → MUST NOT send = POLARITY_FLIP |
| 04 | Same requirement, new section = MOVED |
| 05 | Whitespace / heading-number only ≠ substantive |
| 06 | New normative clause = ADDED |
| 07 | Removed normative clause = REMOVED |
| 08 | "unless private mode is active" = EXCEPTION_ADDED |
| 09 | "when a network is available" = CONDITION_ADDED |
| 10 | Keywords in code/pre/example ignored |
| 11 | "mustard" ≠ "must" |
| 12 | "is not required to" ≠ MUST_NOT |
| 13 | WHATWG lowercase must/should/may |
| 14 | Similar requirements not cross-matched |
| 15 | Relocation ≠ REMOVED + ADDED |
| 16 | Tampered report fails `normshift verify` |
| 17 | Two runs → byte-identical JSON |

## Running

```bash
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl
```

Non-zero exit code on any failure.
