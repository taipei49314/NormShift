# M1 development source recipes

Status ceiling: `EXPERIMENTAL_NOT_ADJUDICATED` / `NOT_INCLUDED`.

This directory contains ten development-only acquisition recipes for official
RFC Editor, dated W3C TR, and frozen WHATWG Review Draft resources. It contains
no standards source bytes, replay bytes, labels, gold records, split or holdout
membership, predictions, scores, or acceptance result. Verifying this directory
does not establish M1 acceptance.

## Included evidence

- `source-manifest.json` is a strict `normshift-m1-source-manifest/v1`
  contract with three RFC, three W3C, and four WHATWG recipes. Every recipe is
  `fetch_recipe_only` and binds the frozen preregistration policy at SHA-256
  `0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773`.
- `curation-provenance.json` binds the independent curation inventory, report,
  license inventory, and historical partial-checksum identities. It records the
  deterministic field mapping, maps each original
  `acquisition_recipe_or_snapshot_ref` to the manifest acquisition URL and
  `fetch_recipe_only` boundary, and records all ten timestamp precision
  transformations.
- `license-inventory.json` is the canonical schema-mapped repository subset of
  the curator's ten per-source license assertions. Verification requires every
  manifest license block to match it exactly. The full curator inventory remains
  under `curator/`; this subset binds five external license-page identities but
  includes none of their response bodies.
- `curation-headers/` contains 27 hash-linked, sanitized source, independent
  replay, license, policy, and WHATWG-chain HTTP header records. Sanitizer v1.0.0
  retains only Content-Encoding, Content-Length, Content-Type, ETag,
  Last-Modified, and one exact frozen W3C Location; values use bounded
  field-specific grammars. Link and every other unknown field are dropped, as
  is every continuation line. Only the exact observed `HTTP/1.1 200 OK` and
  `HTTP/1.1 301 Moved Permanently` status forms are accepted.
  `header-sanitization.json` records each
  original staging SHA-256 and byte length, sanitized identity, and removed
  field names without retaining sensitive values. Its complete canonical bytes
  also have a frozen SHA-256 cross-bound from `curation-provenance.json`. No
  original response-header capture or response body is present.
- `curator/` preserves the original independent `SOURCE-INVENTORY.json`,
  `SOURCE-CURATION-REPORT.md`, and `LICENSE-INVENTORY.md` bytes. The stale
  helper, partial historical checksum, source bodies, and license bodies are
  deliberately not adopted as authority.
- `EVIDENCE.sha256` hashes every content file in this exact evidence root, but
  deliberately excludes itself and its sidecar to avoid a checksum self-cycle.
  `EVIDENCE.sha256.sha256` is the canonical human-readable inventory digest.

The original curator timestamps had fractional seconds. The manifest schema
accepts whole-second UTC only, so each timestamp was truncated to the preceding
second, never rounded. The exact before/after values are preserved in
`curation-provenance.json`.

The historical staging `acquire.ps1` was not imported. It is not the canonical
ten-source acquisition implementation. Only `normshift corpus acquire`, which
requires independently supplied manifest and policy digests, is authoritative.

## Network-free repository gate

The recipe-evidence verifier requires two external trust anchors. It compares
the supplied inventory digest to `EVIDENCE.sha256`, checks the digest sidecar,
requires the declared content hashes, and derives the only allowed file and
directory set. It rejects extras, empty directories, non-portable names,
casefold/NFKC aliases, symlinks, junctions, hard links, special files, oversized
inputs, and files that change during verification. It then strictly loads the
source manifest and frozen policy, validates the bounded canonical curation
provenance against the exact copied curator artifacts and sanitizer report, and
requires every recipe to remain `fetch_recipe_only`.

```bash
uv run normshift corpus verify-recipe-evidence corpus/m1-development \
  --inventory-sha256 "$INVENTORY_SHA256" \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --acceptance-policy acceptance/m1_m2_prereg_v1.json
```

CI runs only this network-free recipe/load/inventory gate. CI does not contact
the standards hosts and does not create a local source corpus.

## Optional pinned acquisition

An authorized operator may later acquire the ten development sources into a
separate, dedicated, empty root. The acquisition is live and intentionally not
part of CI:

```bash
uv run normshift corpus acquire corpus/m1-development/source-manifest.json \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --acceptance-policy acceptance/m1_m2_prereg_v1.json \
  --snapshot-root /dedicated/empty/development-root
```

The command requires every current response URL, redirect, ETag, Last-Modified,
media type, charset, byte length, SHA-256, adapter family, and document version
to match the frozen recipe before committing any output. Upstream response or
byte drift therefore fails closed; this manifest is not permission to silently
refresh the corpus.

## Licensing boundary

No RFC, W3C, WHATWG, or license-page response bodies are distributed in this
directory. The small sanitized HTTP header records are provenance metadata only;
original response headers and cookie or authentication values are excluded.
The manifest preserves the independent curator's per-family redistribution
basis so a later authorized acquisition has a reviewable provenance record, but
all repository entries remain `fetch_recipe_only`:

- RFC recipes point to complete RFC Editor resources and record the applicable
  document notices/IETF Trust basis. Any later redistribution must retain the
  complete unmodified document, notices, legends, attribution, and disclaimers.
- W3C recipes point to dated Micropub versions and record the W3C Software and
  Document License. Any later redistribution must satisfy that license's notice
  and attribution conditions.
- WHATWG recipes point to immutable MIME Sniffing Review Drafts and record CC BY
  4.0/WHATWG IPR policy attribution conditions.

Those statements are provenance boundaries, not legal advice and not approval
for any future blind source. Changed bytes, modified excerpts, or a future
holdout require a fresh independent license review.

## Remaining acceptance gates

This evidence does not evaluate extraction, region labeling, modality, support
minimums, blind whole-document custody, determinism, or clean-room audit. No
holdout membership exists here. Those gates remain external and unresolved; the
only valid acceptance implication of this directory is `NONE`.
