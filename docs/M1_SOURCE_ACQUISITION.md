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
  must have a globally unique hash, adapter document version, acquisition URL,
  and canonical URL, and RFC records must also name distinct RFC numbers;
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
any network fetch.

After that transaction, `acquire` immediately runs the complete network-free
inventory, provenance, byte, and adapter replay before it can report `ACQUIRED`.
If this final replay fails, the command exits nonzero and the dedicated root is
quarantined: later invocations re-verify the existing inventory and cannot refetch,
repair, or report success. Discard and recreate that root before retrying. This is
fail-closed quarantine, not an automatic rollback-to-empty guarantee.

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
fixtures. Production CLI calls reject that kind. No actual-source manifest or source
bytes are asserted by this change.

Source verification is not full M1 report replay. A later independently reviewed
gate must still acquire legally distributable official bytes, freeze corpus labels
without implementation access to holdout results, run pinned bytes through
extract/diff/`verify` twice with byte-identical outputs, pass every pre-registered
per-class threshold and minimum support rule, keep M0 green, and obtain clean-room
M1 adjudication.
