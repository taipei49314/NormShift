# Phase 0 baseline — 20260809T091731Z

- Repository: `https://github.com/taipei49314/NormShift`
- Default branch: `master`
- Starting commit: `4e9dff2a7a37a2a5ea17274daf2e7193da170d43`
- Starting tree: `1e8470c09d28b91dffd7a16e7adcc8c8bc29fb6e`
- Live default CI: `https://github.com/taipei49314/NormShift/actions/runs/31301258728`
- OS: Windows NT `10.0.26200.0` (`x86_64`)
- Python used by `uv`: CPython `3.12.13`
- uv: `0.12.2`
- Git: `2.49.0.windows.1`
- Worktree was clean before dependency sync and baseline output generation.

## Inherited gate results

| Gate | Result |
|---|---|
| `uv sync --python 3.12 --frozen --all-extras --dev` | PASS |
| `uv run ruff check .` | PASS |
| `uv run mypy src` | PASS (`50` source files) |
| `uv run pytest -q` | PASS (`180 passed`) |
| `uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl` | **FAIL on Windows cp1252 stdout** |
| `uv run normshift measure ...` | PASS (`15/15`, extraction/alignment/classification F1 `1.0`) |
| `uv run normshift diff ...` | PASS (`9 -> 11` requirements, `11` changes) |
| `uv run normshift verify ... --source-root .` | PASS (`verification_scope=FULL`) |
| `uv build` | PASS (wheel and sdist) |

The inherited benchmark computed all cases but crashed while printing
`expected⊆observed`; Python raised `UnicodeEncodeError` because the active Windows
stream encoding was cp1252. This is a real cross-platform CLI regression, so the
M0 freeze was not accepted. A CLI-facing regression test was added and observed
failing before the narrow repair changed progress messages to portable ASCII.

## Generated baseline artifacts

- `metrics.json`
- `report.json`
- `report.md`
- `benchmark-windows-cp1252-failure.txt`
- local ignored build outputs: wheel and sdist under `dist/` (not retained as
  authoritative products)

These artifacts describe the inherited starting subject plus the observed local
repair worktree; they are baseline evidence only and are not an authoritative
exact-SHA acceptance package.
