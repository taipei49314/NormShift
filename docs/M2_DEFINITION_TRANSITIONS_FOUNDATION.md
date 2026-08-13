# Experimental M2 DefinitionTransition v1

`DefinitionTransition` v1 is a narrow, canonical sidecar for the lexical
definition facts between *adjacent* versions already bound by a successful
`LineageGraph` replay. It emits only `DEFINITION_ADDED`,
`DEFINITION_CHANGED`, and `DEFINITION_REMOVED`.

It is deliberately not a cross-reference or indirect-impact engine. It does
not emit or infer `CROSS_REFERENCE` or `INDIRECT_IMPACT`, does not alter the M0
report or package-manifest contracts, and does not establish source custody,
official identity, adjudication, or M2 acceptance.

## Replay contract

`definition-transitions build` requires a caller-held external lowercase SHA-256
for a canonical LineageGraph and calls `verify-lineage`'s exact ordered
source/profile/adapter replay before deriving bytes. It writes only the canonical
JSON bytes to binary stdout; an external custodian must capture those bytes,
discard any capture from a nonzero exit, and compute the sidecar SHA-256.

`definition-transitions verify` requires external lowercase SHA-256 values for
both the sidecar and graph. It validates bounded, descriptor-stable sidecar
bytes, strict JSON, canonical bytes, schema, integrity, and the graph anchor
before its graph source replay; then it replays the graph and requires exact
canonical sidecar byte equality. Successful verification is fixed to
`DEFINITION_TRANSITIONS_REPLAY_ONLY external_acceptance=false`.

The commands have no source-override, content-only, output-writer,
cross-reference, or impact options. Errors are stderr-only and success is never
printed on a failed replay.

## Deterministic lexical pairing

For each graph version, a definition has the established `DefinitionRecord`
identity `normalize_whitespace(term).lower()` (not Unicode `casefold()`). A duplicate identity in one version is
an error, never a last-wins choice. Pairs are graph-version/document-SHA order,
not file-system path order. A present-to-absent term is `REMOVED`; an
absent-to-present term is `ADDED`, so a term that disappears and later returns
is an `ADDED` transition for the return pair. A common term is `CHANGED` only
when its graph-recorded `normalized_body` differs; unchanged terms are omitted.

Every transition has a deterministic SHA-256 ID, old/new `DefinitionRecord`
IDs as applicable, version/document SHA bindings, and normalized term/body
SHA-256 values. The sidecar also anchors both the external graph-file SHA-256
and the graph integrity content SHA-256.
