# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `6f1ab51899ca64f9ce768559991e87a77a0623a6c982da343b4fdae670deecaf`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `merge-old.html` | `sha256:9c0d2dbc6850` | `9c0d2dbc6850f9b67f284e82222cc9e3bd52772f4fc06aba328b12c6a061ebc6` | 140 |
| new | `merge-new.html` | `sha256:79fa6b92b261` | `79fa6b92b26144ae0dddc2a525e330c74c23240b5454ec9b4801b5dab1b8b999` | 119 |

### Provenance

- **old**: family=`generic_html` adapter=`normshift.adapters.html`@1.0.0 type=`text/html`
  - local_path (portable): `merge-old.html`
- **new**: family=`generic_html` adapter=`normshift.adapters.html`@1.0.0 type=`text/html`
  - local_path (portable): `merge-new.html`

## Summary

- Old requirements: **2**
- New requirements: **1**
- Changes: **2**

### Classification counts

- `AMBIGUOUS`: 1
- `REMOVED`: 1

## Changes

### `AMBIGUOUS` — `d513768e4e053925`

- Confidence: `0.55`
- Modality transition: `MUST->MUST`
- Old requirement: `c15486f7c059c691`
- New requirement: `476187ffa2576aea`
- Old section: (root)
- New section: (root)
- Old locator: `xpath:/body/p[2]`
- New locator: `xpath:/body/p`
- Old text: Servers MUST log authorization denials.
- New text: Servers MUST log authentication failures and authorization denials.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9579`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.7308`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.95`
  - text_similarity: `1.0`
  - token_similarity: `0.7358`
- Evidence hashes:
  - `30b70ee8a8489431d38676cd57abe4b3aba7538134ff53685cd3d2dfdaf3b508`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `68633d84e334fd48899ddbd5082d232cf478b6826fe9505a19237c11c3746ced`
  - `accbf74a74d75d871df23178f086541a59a21f1f3c28b522fb60e072cc30b330`
  - `d940f8979b54a6a9c366fa041bd46964e9a8a5895507a5dfebdd6aef3728cd17`

### `REMOVED` — `492bc2a90532fed7`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `e704f04ca743ed8a`
- Old section: (root)
- Old locator: `xpath:/body/p[1]`
- Old text: Servers MUST log authentication failures.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `9a65fff802bef2d9c7c40d48960194d30aa003d288c60c6f73eb1726ec511e37`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `e787ba8e250fcba81732435347ef19085613102fcc0f8f7c169e92befbd42606`
