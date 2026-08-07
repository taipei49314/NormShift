# M1 Evidence Package — Real Standards Adapters & Provenance

**Implementer status (not Release Authority):**  
`M1_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`

**Date:** 2026-08-07  
**Repo:** local `C:\Users\G713RW\NormShift` (push deferred per operator instruction)

## Scope delivered

| Requirement | Status |
|-------------|--------|
| RFC HTML/XML adapter | yes (`normshift.adapters.rfc`) |
| W3C TR-style adapter | yes (`normshift.adapters.w3c`) |
| WHATWG-style adapter | yes (`normshift.adapters.whatwg`) |
| Generic HTML adapter | yes (`normshift.adapters.html`) |
| snapshot metadata / ETag / checksum / canonical source | yes (sidecar `*.meta.json` + `Provenance`) |
| normative/informative region detection | improved (class/role/section titles) |
| boilerplate / nav / example/code exclusion | yes (`strip_chrome` + normalize) |
| offline 3-family regression corpus | `fixtures/corpus/{rfc,w3c,whatwg}` |
| adapter failure fail-closed (no false success artifact) | tested |
| M0 adversarial benchmark still green | 17/17 |

## Commands

```text
uv run ruff check .                 # exit 0
uv run mypy src                     # exit 0
uv run pytest -q                    # exit 0 — 42 passed
uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl  # 17/17

uv run normshift ingest fixtures/corpus/rfc/sample-v1.html --adapter rfc --out evidence/m1/rfc.prov.json
uv run normshift ingest fixtures/corpus/w3c/sample-v1.html --adapter w3c --out evidence/m1/w3c.prov.json
uv run normshift ingest fixtures/corpus/whatwg/sample-v1.html --adapter whatwg --out evidence/m1/whatwg.prov.json

uv run normshift diff fixtures/corpus/rfc/sample-v1.html fixtures/corpus/rfc/sample-v2.html \
  --adapter rfc --profile rfc2119 --json evidence/m1/rfc.diff.json --markdown evidence/m1/rfc.diff.md
uv run normshift diff fixtures/corpus/w3c/sample-v1.html fixtures/corpus/w3c/sample-v2.html \
  --adapter w3c --profile rfc2119 --json evidence/m1/w3c.diff.json
uv run normshift diff fixtures/corpus/whatwg/sample-v1.html fixtures/corpus/whatwg/sample-v2.html \
  --adapter whatwg --profile whatwg --json evidence/m1/whatwg.diff.json

uv run normshift verify evidence/m1/rfc.diff.json     # exit 0
uv run normshift verify evidence/m1/w3c.diff.json     # exit 0
uv run normshift verify evidence/m1/whatwg.diff.json  # exit 0
```

## Artifact SHA-256

| File | SHA-256 | Bytes |
|------|---------|-------|
| `rfc.prov.json` | `87bfaadd2935cc42fbfea396e3f92bf612b0c766fdc35ae8acad09e0ce7a8d5a` | 841 |
| `w3c.prov.json` | `5d2468a05c52f0ba985ecececbbcaccbb7ed09a91d3c73c70397938e78b5025e` | 820 |
| `whatwg.prov.json` | `a84c543645849dbb0750e0447d356b6ea6060ae6c84a473db001fe2b1e65822e` | 854 |
| `rfc.diff.json` | `47f049de483d651b9c5f9d843313487d8e440bd7ed0f3cb6e1816d3723f6700e` | 15014 |
| `w3c.diff.json` | `826d452162cdbfed9c361f698d4ee21236f74798f62f7239e695012c38eae027` | 11142 |
| `whatwg.diff.json` | `c73470449636c01ce19ef9b731cbf986a83745a65a8fcc961e8a5daae8b253a7` | 16295 |
| `rfc.diff.md` | `00747e1f08b6495a755b81539b64fac137bff4ffcbe593907c5466c970871146` | 5709 |

Integrity examples:

- rfc.diff `content_sha256` = `eeff758a34eb2c51819246eebc20f48333e03a6795f29c0ee714f8bd169dea9d`
- w3c.diff `content_sha256` = `baf443cadddeb15d82f8bf2b425dc15b4222c774cc4738c20f3627c32a3501f3`
- whatwg.diff `content_sha256` = `888a01039a3ccf4cb16ec10b8321825adaf282d847066c34c168df36d82a48c2`

## Tests

- **42 passed** (M0 suite retained + M1 adapter/provenance/corpus tests)
- Fail-closed empty source → no JSON artifact written

## Known limitations

1. Corpus files are **structure-faithful offline excerpts**, not full live TR/RFC dumps (network-free replay).
2. Family auto-detection is heuristic; use `--adapter` to force.
3. Boilerplate stripping is heading/xpath based; atypical chrome may leak or over-strip.
4. RFC XML conversion supports a minimal rfcxml subset (`section`/`t`/`sourcecode`/`aside`).
5. Full North Star M1 “real download provenance fetch” is modeled via sidecars, not live HTTP (Observatory is M3).

## Unresolved risks

1. External audit of M0+M1 not performed.
2. Real multi-megabyte standards may need streaming/chunking later.
3. W3C ReSpec-generated docs vary; may need adapter profile extensions.

## Non-claims

- Not production/release ready.
- Not semantic correctness beyond benchmark + corpus regression.
- No network crawler / Observatory (M3).

## Next action

External audit of M0+M1; then M2 Requirement Lineage Graph (persistent lineage IDs, split/merge).
