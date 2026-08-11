# M1/M2 labeling and blind-split governance contract

Status: **governance primitive only**. The implementation and tests use generated
synthetic identities. This contract contains no actual labels, gold data, holdout
membership, candidate predictions, scores, thresholds, or M1/M2 acceptance claim.

## Labeling custody

The labeling verifier consumes three separately frozen layers:

1. A neutral packet that binds each task/evaluation slot to exact source SHA-256,
   canonical portable locator, and evidence SHA-256. Its strict schema has no field
   for a model proposal, confidence, or candidate prediction.
2. An exact-root directory containing at least two complete independent labeler
   submissions. Every submission binds the packet hash and attests that the labeler
   viewed neither other answers nor system outputs and did not implement the system.
3. An append-only adjudication ledger. A separate adjudicator records reviewer IDs,
   task, slot, source/locator/evidence binding, explicit decision/class-or-null,
   reason, UTC second, and hashes of every submitted response. Conflict, abstention,
   ambiguity, and superseded correction events remain in the graph.

The caller must supply the exact source manifest and blind-split manifest bytes as well as
independent packet, ledger, source-manifest, and split-manifest SHA-256 trust anchors. The
verifier loads the frozen acquisition schema, requires its compact canonical JSON form,
checks the split covers exactly the source IDs and immutable source facts, and then checks
every packet SHA/locator belongs to the packet's declared split. A digest string alone is
not treated as membership proof. M1 items may reference only `m1_in_scope` documents;
all M2 items may reference only `m2_in_scope` documents. Cross-family/cross-lineage
`M2_IDENTITY` hard negatives remain valid, while other multi-source M2 tasks must remain
within one declared family/lineage chain.

The split's implementation-author identities must be disjoint from the packet preparer,
all labelers, and all adjudicators. The submissions root rejects missing/extra files and
directories, Unicode/case aliases, hard links, symlinks, junctions/reparse points, and
special files. Custody paths use ASCII, bounded POSIX segments and a bounded concrete
destination so the same evidence can be materialized on all three supported operating
systems. All governance JSON is bounded, strictly parsed, schema-validated, and required
to equal its canonical UTF-8 encoding. Each response is timestamped no earlier than both
its packet and review-round opening (equality is allowed) and no later than submission;
each adjudication event must occur no later than its own round completion.

Post-freeze correction ledgers require both the prior canonical ledger bytes and an
independent prior-ledger hash. The verifier requires the old review rounds, submissions,
and decisions to be exact prefixes; a claimed prior hash cannot authorize rewritten
history. Appended rounds open strictly after the prior ledger freeze and after the prior
round completes. Appended decisions may use only appended-round authority. The extension
lists all invalidated affected measurement hashes, retains a new correction event, and
requires at least two new reviewers who saw neither prior decisions nor predictions, did
not implement the system, and are separate from all prior labelers and adjudicators.

For an initial freeze, the ledger must be frozen strictly before the split's recorded
prediction start. V1 deliberately rejects a correction ledger paired with a split that
already records prediction access: immutable packet bytes bind the old split hash, so
rewriting that timestamp would not prove a new evaluation cycle. A post-result correction
therefore remains ineligible for final evidence until a separately hash-bound evaluation-
attempt contract binds the corrected ledger, exact candidate/split, and a new prediction
start. The governance CLI never upgrades that unsupported case by assertion.

```text
normshift governance verify-labeling PACKET.json \
  --packet-sha256 EXPECTED_PACKET_SHA256 \
  --source-manifest SOURCE_MANIFEST.json \
  --source-manifest-sha256 EXPECTED_SOURCE_MANIFEST_SHA256 \
  --blind-split-manifest SPLIT.json \
  --split-manifest-sha256 EXPECTED_SPLIT_MANIFEST_SHA256 \
  --submissions-root DEDICATED_EXACT_ROOT \
  --ledger LEDGER.json \
  --ledger-sha256 EXPECTED_LEDGER_SHA256 \
  --acceptance-policy acceptance/m1_m2_prereg_v1.json
```

For `POST_FREEZE_CORRECTION`, also pass `--prior-ledger` and
`--prior-ledger-sha256`.

## Blind split custody

The split manifest binds the frozen source manifest and records independent custodians,
implementation authors, exact raw and derived hashes, whole source-document entries,
M1/M2 scope, and standard-lineage identity. Semantic validation enforces:

- holdout documents are at least 40% of all evaluation documents by exact integer
  comparison;
- each RFC, W3C TR, and WHATWG M1 family contributes at least one whole holdout version;
- development and holdout raw/derived hash sets are disjoint;
- RFC, W3C TR, and WHATWG each contribute an M2 lineage chain; every declared chain
  contains at least three whole versions and every member has one split (the independent
  custodian remains responsible for the semantic chain ID and true consecutiveness);
- split custodians and implementation authors are disjoint;
- holdout membership/gold/predictions were not exposed to implementation before exact
  candidate freeze;
- any holdout opening and prediction start occur only after commit, tree, wheel, sdist,
  source ZIP, and bundle hashes are all frozen; equality with the freeze/open timestamp
  is rejected, so ordering is strict.

```text
normshift governance verify-blind-split SPLIT.json \
  --manifest-sha256 EXPECTED_SPLIT_SHA256 \
  --source-manifest SOURCE_MANIFEST.json \
  --source-manifest-sha256 EXPECTED_SOURCE_MANIFEST_SHA256 \
  --acceptance-policy acceptance/m1_m2_prereg_v1.json
```

Both commands return exit `0` only for a structurally and cryptographically consistent
governance graph, exit `2` for a rejected contract, and exit `1` for an unexpected
runtime failure. Even on exit `0`, output is fixed to
`scope=GOVERNANCE_CONTRACT_ONLY`, `metrics_evaluated=false`, and
`external_acceptance_granted=false`.

The repository and packaged schema mirrors are:

- `labeling_packet_v1.schema.json`
- `label_submission_v1.schema.json`
- `decision_ledger_v1.schema.json`
- `blind_split_manifest_v1.schema.json`

JSON Schema alone is not authority for the cross-artifact or custody checks; use the
CLI verifier with independent expected hashes.
