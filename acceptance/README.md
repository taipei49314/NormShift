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
