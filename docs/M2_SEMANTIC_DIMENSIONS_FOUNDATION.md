# M2 Semantic-Dimensions Foundation

Status: **experimental foundation only; not an M2 acceptance result**.

This module adds a versioned, typed document for dimensions that can occur at
the same time. It is deliberately separate from the primary M0 `Change` model
and does not change `ChangeClassification`, report schema `1.0.0`, the CLI, or
the frozen acceptance scorer.

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
