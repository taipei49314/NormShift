# Detached M1/M2 pre-registration approval

```text
approval_schema: normshift-prereg-approval/v1
approval_id: m1-m2-prereg-v1-approval-root-m1-acceptance-review
reviewer_id: /root/m1_acceptance_review
reviewer_role: read-only independent pre-registration policy reviewer
reviewed_path: acceptance/m1_m2_prereg_v1.json
policy_id: normshift-m1-m2-prereg-v1
policy_sha256: 0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773
policy_byte_length: 15310
baseline_commit: b3af3dc26e64a3399545d179731222f6e87213c9
baseline_tree: c629e2d51fc5219514d6068a90d3453725bd8010
decision: APPROVED
approved_at_utc: 2026-08-11T00:26:44Z
```

The reviewer inspected the exact 15,310-byte UTF-8/LF policy identified by the
SHA-256 above and confirmed that it preserves the pre-result M1/M2 minimum-support,
per-class precision/recall/F1, exact-pass, anti-leakage, provenance, evidence, and
no-threshold-lowering rules they approved.

The reviewer did not implement the evaluated M1/M2 system, edit production code,
labels, or expected outcomes, or push repository changes. They inspected only
historical/public AUTO/PROVISIONAL expedition artifacts and existing code for risk
triage; those artifacts are not final gold and did not determine the numeric
thresholds. The reviewer has not received or inspected the final ground-truth files,
blind split membership, final candidate predictions, per-case scores, or holdout
outputs.

This approval authorizes freezing this policy only. It is not ground-truth
adjudication, M1/M2 acceptance, clean-room external audit, production approval, or
release approval. Any byte change to the policy requires a new hash and detached
approval; thresholds and support may not be lowered after candidate or holdout
results.
