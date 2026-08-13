# M2 Semantic-Dimensions Foundation

Status: **experimental foundation only; not an M2 acceptance result**.

This module adds a versioned, typed document for dimensions that can occur at
the same time. It is deliberately separate from the primary M0 `Change` model
and does not change `ChangeClassification`, report schema `1.0.0`, or the
frozen acceptance scorer. Its opt-in CLI creates separate sidecars; it never
changes an M0 report's canonical bytes.

## Version 1.0.0 contract

`normshift.semantic_dimensions.build_semantic_dimensions` consumes a primary
change ID through a `VerifiedReportAuthority`. The only binding factory accepts
an exact report file, source root, canonical typed FULL-verification receipt
bytes, and independently held report-file/receipt SHA-256 values. Receipt
creation runs the existing non-writing `verify_report_file` path with
`verification_scope=FULL`, requires `OK` with no override or errors, and binds
the verifier version plus both portable source refs, source hashes, byte
lengths, and document versions. Every build and replay reruns that FULL source
verification and also rechecks each requirement fingerprint and the complete
primary-to-requirement bindings. It produces:

- `structural_form`: `NONE`, `MOVE_ONLY`, `REWRITE_ONLY`, or
  `MOVED_AND_REWRITTEN`;
- independent actor, action, object, scope, modality, polarity, condition, and
  exception slots;
- the exact preregistered M2 change classes supported by those slots;
- the unchanged primary change ID/classification/evidence hashes and a hash of
  the complete canonical primary `Change` payload;
- old/new requirement IDs, document hashes, text hashes, fingerprints, section
  paths, locators, and hashes of the complete canonical `Requirement` payloads;
- deterministic semantic and document integrity hashes.

The canonical JSON Schema is mirrored byte-for-byte at
`schemas/semantic_change_dimensions_v1.schema.json` and
`src/normshift/schemas/semantic_change_dimensions_v1.schema.json`.

The hashes are binding mechanisms, not signatures. Production callers must
custody the expected report-file and receipt SHA-256 values outside the report
being verified. A literal string or arbitrary 64-hex value is not a receipt,
and a self-resealed report cannot create a FULL receipt unless exact source
replay reproduces it.

## Experimental CLI sidecars

`normshift semantic-dimensions build REPORT CHANGE_ID --source-root ROOT
--receipt RECEIPT --report-sha256 SHA --receipt-sha256 SHA`
requires a pre-existing receipt. It accepts no source override and will not
write bytes until the receipt matches the caller-provided digest and a fresh
FULL replay reproduces every bound input. On success it writes only exact
canonical semantic-document bytes to binary standard output; an external
custodian must capture, persist, and hash that stream. Standard output is not
custody or atomic-file authority. Capture must be byte-preserving: Windows
PowerShell text pipelines or text redirection can transcode Unicode. Discard a
capture after any nonzero exit, then externally hash a successful capture before
using `verify`. Caller-provided digest anchors are binding inputs only: they do
not prove independent custody, approval, adjudication, or M2 acceptance. The
sidecar contains only the existing conservative builder output: object and
scope remain `UNKNOWN`, and no caller span or M2 acceptance result is introduced
by this command.

`normshift semantic-dimensions verify SIDECAR CHANGE_ID --semantic-sha256 SHA
--receipt RECEIPT --report REPORT --report-sha256 SHA --receipt-sha256 SHA
--source-root ROOT` accepts only bounded regular receipt/sidecar files,
requires all three externally held lowercase digests, parses canonical bytes,
and reconstructs the exact sidecar through the same FULL source-replay binding. It has no
source override, content-only mode, spans, or semantic-role option.

## Experimental LineageGraph v1 replay contract

`normshift verify-lineage GRAPH DOC... --graph-sha256 SHA --profile PROFILE
--adapter ADAPTER` verifies a separately stored LineageGraph v1. The graph must
have a caller-provided lowercase SHA-256 and be bounded, duplicate-free,
canonical JSON that passes the root/package-identical strict schema and its exact
SHA-256 integrity envelope. Those checks run before any document or adapter is
opened. Each ordered source is then read through a bounded descriptor-stable
snapshot and replayed from an isolated temporary root; the canonical replay bytes
must equal the graph bytes exactly. Source filesystem references intentionally do
not enter the graph, so equal source bytes can relocate without changing it.
Only each declared document's bounded snapshot bytes enter that replay: adjacent
`.meta.json` files are neither read nor copied, and cannot become undeclared
authority inputs. Before the isolated root is removed, every original declared
path is read again through the same descriptor guard and must retain the exact
initial identity, bytes, and SHA-256; a same-byte inode replacement is rejected.

The sole success meaning is `LINEAGE_GRAPH_REPLAY_ONLY
external_acceptance=false`: an exact replay of caller-supplied ordered document
bytes with the explicit profile and adapter. This is not source custody, official
identity, independent review, adjudication, a blind result, or M2 acceptance.

## Conservative boundary

- Object and scope are not extracted or adjudicated by this foundation. A
  caller may provide token-boundary spans into `Requirement.normalized_text`,
  but these are recorded as `ASSERTED_UNVERIFIED` candidates only. Object and
  scope remain `UNKNOWN` and emit no class even when both candidates differ.
  Overlapping or reused object/scope candidates are rejected. Emitting those
  classes requires a future independently anchored semantic-role authority.
- Missing actor/action evidence also remains `UNKNOWN`.
- A changed non-empty condition or exception is `AMBIGUOUS`, because the frozen
  policy defines only added/removed classes for those dimensions.
- Add/remove primary events have no old/new comparison pair, so every semantic
  slot is `NOT_APPLICABLE` rather than pretending each field was added/removed.
- `verify_semantic_dimensions` resolves the same FULL source-replayed report
  and rejects deleted/mutated sources, a wrong source root, a forged receipt,
  or a rehashed document whose full primary/requirement payload hashes, IDs,
  locators, values, spans, or classes do not match replay.

## Claims boundary

This foundation does **not**:

- extract or adjudicate object/scope semantics;
- treat caller-selected text coordinates as proof of a semantic role;
- alter or improve the existing alignment decision;
- become a second primary classification authority;
- integrate the new document into the M0 report or lineage graph;
- inspect blind labels/holdouts or establish M1/M2 precision, recall, F1, or
  acceptance.

Those steps require separately governed evidence and evaluation.
