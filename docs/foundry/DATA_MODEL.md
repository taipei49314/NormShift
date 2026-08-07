# Foundry Data Model

| Object | Role |
|--------|------|
| CampaignPlan | Declarative inputs (snapshots, pairs, chains) |
| CampaignRunManifest | One authoritative run record + artifact hashes |
| PairCapsule | Self-contained pair evidence package |
| ReviewPacket | AUTO proposal for external review |
| ReviewDecision | Append-only; TEST_FIXTURE or external only |
| LineageCandidate | Continuity / split / merge hypothesis |
| CorpusMetrics | Layer A/B/C separated metrics |
| ObservatoryManifest | Verified projection of run assets |
