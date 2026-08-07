# Offline regression corpus (M1)

Three **document families** for adapter + provenance regression:

| Family | Path | Adapter |
|--------|------|---------|
| RFC HTML/XML | `rfc/` | `rfc` |
| W3C TR-style HTML | `w3c/` | `w3c` |
| WHATWG-style HTML | `whatwg/` | `whatwg` |

Each file may have a `*.meta.json` sidecar with:

- `canonical_source`
- `etag`
- `last_modified`
- `content_type`
- corpus notes

These are **structure-faithful offline excerpts**, not full redistributions of
live standards. They exist so clean clones can replay M1 without network access.

## Replay

```bash
uv run normshift ingest fixtures/corpus/rfc/sample-v1.html --adapter rfc --out artifacts/rfc.prov.json
uv run normshift diff fixtures/corpus/rfc/sample-v1.html fixtures/corpus/rfc/sample-v2.html \
  --adapter rfc --profile rfc2119 --json artifacts/rfc.diff.json
```
