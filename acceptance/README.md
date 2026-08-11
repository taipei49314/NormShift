# Acceptance policy

`m1_m2_prereg_v1.json` freezes the M1 and M2 acceptance thresholds before any final
gold, blind split, candidate prediction, per-case score, or holdout output is opened
by the implementation authority.

The adjacent SHA-256 sidecar binds the exact policy bytes. The detached approval is
from a read-only reviewer who did not implement the evaluated system and is bound to
that digest and to the accepted M0 baseline commit and tree.

The policy is deliberately fail-closed: a missing class, insufficient support,
unexpected output, unavailable source/license/reviewer, or any open P0/P1 cannot be
hidden by an aggregate score. Future ground-truth, scorer, split, evidence, package,
and audit artifacts must cite this exact policy digest.

## Frozen metric scorer

`scorer_v1_manifest.json` closes the exact source, canonical item-key logic,
interchange schemas, adversarial tests, runtime identity, dependency lock, and
command wrapper used to recompute M1/M2 per-class metrics. Its adjacent sidecar is
only a local integrity convenience: an evaluator must supply the manifest digest
from a detached independent approval via `--scorer-manifest-sha256`. The scorer does
not trust an ambient sidecar.

The scorer accepts only canonical, bounded JSON and evidence-derived item keys.
Missing predictions become false negatives; valid positive predictions outside the
gold universe become false positives; duplicates, malformed keys, unknown source
bytes, or invalid class/slot combinations fail closed. Its fixed output must be
written to a dedicated directory outside the source and evidence inputs.

Scorer output has scope `DECLARED_SUPPORT_METRICS_ONLY`. Source provenance, split
custody, reviewer authority, actual-document and consecutive-lineage coverage,
exact-pass matrices, clean-room replay, and external audit remain explicitly
unevaluated. `external_acceptance_granted` is always false. The exported JSON
Schemas express interchange structure; arithmetic, graph, canonical-key, and
aggregate invariants require the exact hash-bound scorer/models and recomputation.
