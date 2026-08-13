# Experimental lexical DefinitionReferenceCandidate v1

This separate sidecar derives only `LEXICAL_TERM_OCCURRENCE_CANDIDATE`
records from the exact-replayed `LineageGraph` dependency links. It binds each
link to its exact requirement and definition IDs, same-version document hashes,
normalized-term hash, and graph file/integrity
anchors.

It is a lexical token-boundary candidate, not a semantic cross-reference
verdict: homographs, context, intent, and causal consequences are unadjudicated.
It does not emit or infer `CROSS_REFERENCE` or `INDIRECT_IMPACT`, establishes no
source custody or official identity, and cannot establish M2 acceptance.

Build and verify require external lowercase digests and replay the ordered
caller-supplied graph sources using `verify-lineage`; build writes canonical
bytes only to binary stdout. Any nonzero capture must be discarded. Verify
requires exact canonical reconstruction. There are no role, span, score,
semantic, causal, output-writer, or source-override options.
