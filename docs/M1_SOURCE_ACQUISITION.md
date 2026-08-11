# M1 source acquisition contract

Status ceiling: **M1_EXPERIMENTAL / NOT_ADJUDICATED**.

This gate establishes a fail-closed source and provenance boundary for later M1
evaluation. It does not contain labels, inspect holdout output, measure adapter
quality, or claim M1 acceptance.

## What the contract proves

An actual-source manifest must:

- bind `acceptance/m1_m2_prereg_v1.json` at exact SHA-256
  `0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773`;
- contain at least two versions from each of RFC, W3C, and WHATWG;
- give every source a `standard_id` and `version_or_date`; every actual source
  must have a globally unique hash, acquisition URL, and canonical URL; adapter
  document versions must be unique within one family/standard lineage, each
  family must provide at least two distinct `(standard_id, document_version)`
  pairs, and RFC records must also name distinct RFC numbers;
- use immutable family-authoritative URL forms: exact RFC Editor resources,
  dated W3C `/TR/` versions, or frozen WHATWG commit/review snapshots;
- record the curator's prior retrieval assertion, ETag and Last-Modified (including
  explicit null when absent), media type, charset (including explicit null), byte
  length, SHA-256, adapter/profile/identity-preflight versions, local portable ref,
  and a non-empty license/redistribution basis;
- cap source count at 24, each source at 64 MiB, and the total at 256 MiB; and
- remain `EXPERIMENTAL_NOT_ADJUDICATED` with `ground_truth_status=NOT_INCLUDED`.

Here `canonical_url` means the immutable dated/versioned download identity and must
equal the final URL in the frozen redirect chain. A document's mutable HTML
`rel=canonical` (for example an undated W3C `/TR/name/` URL) may be retained as
curator auxiliary evidence, but it is not the frozen source identity.

`normshift corpus acquire` requires both the externally frozen manifest digest and
the policy file. It follows only the exact predeclared HTTPS redirect chain, requests
identity encoding, compares response metadata and bytes, and preflights the forced
adapter/family/version through an M1-only identity gate (without changing the M0
adapter contract). All sources pass before source bytes, metadata sidecars, and
receipts are committed in one rollback-safe transaction. Portable path aliases,
existing partial state, extra files/directories, symlinks, and junctions are rejected.
Generated refs use a conservative ASCII segment grammar, a 255-byte segment cap,
and a 1,024-byte relative-ref cap so invalid platform-specific names fail before
any network fetch. The concrete final, temporary, and backup paths under the
chosen snapshot root must also fit a conservative 240-byte transaction budget;
choose a shorter dedicated root if that preflight rejects the location.

Adapter preflight decodes source bytes as strict UTF-8. Supported UTF-8 and
US-ASCII declaration aliases are canonicalized only for parser input while raw
snapshot bytes and provenance hashes remain unchanged; conflicting declarations,
non-ASCII bytes under an ASCII declaration, decoding replacement, binary controls,
and unsupported encodings fail closed. RFC XML is parsed without network or entity
resolution and is identified from the namespace-local `rfc` root plus `middle`
structure, so a legal declaration followed by a DOCTYPE, comment, or processing
instruction does not require an unsafe second parse.

After that transaction, `acquire` immediately runs the complete network-free
inventory, provenance, byte, and adapter replay before it can report `ACQUIRED`.
If this final replay fails, the command exits nonzero and the dedicated root is
quarantined: later invocations re-verify the existing inventory and cannot refetch,
repair, or report success. Discard and recreate that root before retrying. This is
fail-closed quarantine, not an automatic rollback-to-empty guarantee.

The externally frozen manifest byte length and SHA-256 remain the authority for
snapshot completeness. As a separate defense-in-depth check, acquisition replay
requires a reviewed terminal form for each currently frozen family format: an
explicit HTML document terminal for complete RFC/W3C/WHATWG documents, terminal
legal matter in the RFC Editor paginated format, or the reviewed terminal
bibliography and bounded generation-profile structure in the frozen WHATWG Review
Draft format. No exact generator hash or bibliography content identifier is treated
as proof of completeness. This rejects the proper-prefix truncation matrix for all
ten development recipes. It is not a claim that a byte-only parser can prove the
semantic completeness of arbitrary HTML. A new publisher serialization or source
family requires an independently reviewed terminal rule before it can enter the
production acquisition contract; generic local adapter use promises strict UTF-8
and lexical structure only.

Custom fetch callbacks are restricted to explicitly enabled test-only contracts.
Actual-source receipts can only be produced by the pinned HTTPS acquisition path;
embedded snapshot import must use a separately attested delivery contract rather
than impersonating an observed HTTP response.

The receipt preserves `curator_retrieved_at_utc` as an assertion from the frozen
manifest. This command performs pinned **reacquisition**; it does not claim to have
observed or attested the curator's original retrieval time. Receipts state this scope
explicitly.

`normshift corpus verify-sources` is network-free. It checks the exact root inventory,
policy and manifest hashes, source bytes, canonical metadata/receipts, and adapter
provenance replay. Local reads are size-checked before bounded allocation and reject
stat/read races.

## Repository development recipes

`corpus/m1-development/source-manifest.json` materializes ten official
development-only recipes: RFC 2246/4346/5246, three dated Micropub W3C TR
versions, and four MIME Sniffing WHATWG Review Drafts including 2025-01. Every
entry is `fetch_recipe_only`; no standards response body or license-page body is
stored in Git. The repository retains 27 small, hash-linked sanitized HTTP
header records and a canonical recipe-only license inventory as source-curation
provenance. Sanitizer v1.0.0 retains only bounded field-specific
Content-Encoding, Content-Length, Content-Type, ETag, Last-Modified, and one
exact frozen W3C Location. It drops unknown fields and every continuation line,
including continuations of allowlisted fields. Link is not retained, and only
the exact observed `HTTP/1.1 200 OK` and `HTTP/1.1 301 Moved Permanently`
status forms are accepted. The canonical sanitizer report preserves the exact
27 original staging hashes and byte lengths without preserving original
response-header bytes or sensitive values; its complete SHA-256 is frozen.

The exact evidence root uses a no-self-cycle inventory. `EVIDENCE.sha256` hashes
every content file except itself and its digest sidecar; callers must supply its
independently frozen SHA-256. The verifier checks that external anchor, the
sidecar, all content hashes, the exact file and directory set, portable aliases,
regular-file identity, the compact canonical source manifest/policy, exact
agreement between the manifest and canonical license inventory, and the
original-to-sanitized header identity map. It repeats the complete root
verification after loading those JSON contracts. The strict canonical curation
provenance additionally binds the exact copied curator inventory/report/license
bytes and each source's original acquisition recipe to its manifest acquisition
URL, `fetch_recipe_only` boundary, and explicit no-body-in-repository state.

CI runs only this network-free gate:

```bash
uv run normshift corpus verify-recipe-evidence corpus/m1-development \
  --inventory-sha256 0eb3e50d0c35eb091b181f8cfe2007cc88b6496d38147870570e0219d92b5938 \
  --manifest-sha256 a2cfd4efa43fc2e90a76ded6e6c461bbf42ccd445cd674009cc083faa7102aaf \
  --acceptance-policy acceptance/m1_m2_prereg_v1.json
```

The curator supplied subsecond timestamps while the manifest schema permits
whole-second UTC. `curation-provenance.json` preserves every original value and
documents deterministic truncation to the preceding second without rounding.
The staging acquisition helper was not imported and has no authority.

```bash
uv run normshift corpus acquire sources.json \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --acceptance-policy acceptance/m1_m2_prereg_v1.json \
  --snapshot-root /dedicated/empty/root

uv run normshift corpus verify-sources sources.json \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --acceptance-policy acceptance/m1_m2_prereg_v1.json \
  --snapshot-root /dedicated/sealed/root
```

## Deliberate non-claims and remaining gates

The schema and tests use a `SOURCE_CONTRACT_TEST` kind for local structure-faithful
fixtures. Production CLI calls reject that kind. The repository actual-source
manifest asserts only frozen development acquisition recipes and prior curator
header/hash facts; it does not embed, reacquire, or attest current source bytes.

Source verification is not full M1 report replay. A later independently reviewed
gate must still acquire legally distributable official bytes, freeze corpus labels
without implementation access to holdout results, run pinned bytes through
extract/diff/`verify` twice with byte-identical outputs, pass every pre-registered
per-class threshold and minimum support rule, keep M0 green, and obtain clean-room
M1 adjudication.
