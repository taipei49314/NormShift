# Review Protocol

1. Campaign run emits AUTO `packets.jsonl`.
2. External reviewers append `ReviewDecision` JSONL with `label_authority` EXTERNAL_*.
3. Implementer may only mint `TEST_FIXTURE` decisions in tests.
4. `normshift review ledger validate` rejects agent-minted EXTERNAL_* rows.
5. Conflicts stay DISAGREED until explicit external adjudication.
