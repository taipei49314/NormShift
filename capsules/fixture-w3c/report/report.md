# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `45a97c5bf326e9c14eb914b002b52b8c372d93bca3da094d1ef67da585430778`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `fixture-w3c-v1.html` | `WD-excerpt-1` | `7ddf62a67fa7086e06338ee02c87241ade81feeccf1878144f151850a05580da` | 1202 |
| new | `fixture-w3c-v2.html` | `WD-excerpt-2` | `da83242c7bf6a6258c8160755e207b0420feb85526d18c3a8693e25cf3c945db` | 1307 |

### Provenance

- **old**: family=`w3c` adapter=`normshift.adapters.w3c`@1.0.0 type=`text/html`
  - local_path (portable): `fixture-w3c-v1.html`
- **new**: family=`w3c` adapter=`normshift.adapters.w3c`@1.0.0 type=`text/html`
  - local_path (portable): `fixture-w3c-v2.html`

## Summary

- Old requirements: **2**
- New requirements: **3**
- Changes: **3**

### Classification counts

- `ADDED`: 1
- `STRENGTHENED`: 1
- `UNCHANGED`: 1

## Changes

### `ADDED` — `6781222b58325f58`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `9379f3e96f842acf`
- New section: Sample API (W3C-style corpus) > 4. Networking
- New locator: `id:c3|xpath:/body/main/p[5]`
- New text: Clients MUST NOT send credentials on cross-origin redirects.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `827b456108330e6f0852a09a09442618b6215886931b2815c2a4d74414b6c632`
  - `acaf4649bc69965e56c492868b21229d5d690758de2b8f531faaba1c98368d06`

### `STRENGTHENED` — `f5e782249ebae371`

- Confidence: `0.92`
- Modality transition: `SHOULD->MUST`
- Old requirement: `1963d29573c5481e`
- New requirement: `f5ab399284b861ee`
- Old section: Sample API (W3C-style corpus) > 2. Conformance
- New section: Sample API (W3C-style corpus) > 2. Conformance
- Old locator: `id:c2|xpath:/body/main/p[3]`
- New locator: `id:c2|xpath:/body/main/p[3]`
- Old text: User agents SHOULD display a warning when certificates are invalid.
- New text: User agents MUST display a warning when certificates are invalid.
- Reasons:
  - Obligation strengthened: SHOULD -> MUST.
- Alignment score components:
  - combined: `0.8849`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9385`
  - modality_match: `0.4`
  - section_similarity: `1.0`
  - structural_proximity: `1.0`
  - text_similarity: `0.96`
  - token_similarity: `0.9394`
- Evidence hashes:
  - `1c11863b6b774f0b8bb7c30ce9d6c035e656a8288e2e12a89331aaa549e9f42e`
  - `2ef8c469dff12e49d89b997f5353f5a08fad9441a76f91cd15762d211be243f4`
  - `832ce89d4d066cc91de351a8b96a7eef60a08f65418e84ddff9a9524a2e63abc`
  - `8fa01b2aee8f690d1b32add7c24acb4f534f202a5b75c45c3af3890e9aeef22f`
  - `a8ea75a9ca1c340ef9b2b0ed62442f1caaee76ff09a92a88cac3bfe011cb72fa`

### `UNCHANGED` — `b2218654bfb38bac`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `8093ff9f005d0c87`
- New requirement: `6981672b1f125c4a`
- Old section: Sample API (W3C-style corpus) > 2. Conformance
- New section: Sample API (W3C-style corpus) > 2. Conformance
- Old locator: `id:c1|xpath:/body/main/p[2]`
- New locator: `id:c1|xpath:/body/main/p[2]`
- Old text: Implementations MUST support the open() method.
- New text: Implementations MUST support the open() method.
- Reasons:
  - Identical normalized text, modality, and section → UNCHANGED.
- Alignment score components:
  - combined: `1.0`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `1.0`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `b44ea53990dd0e340a7c32b81f66768638cabc66364d275a480145f542dfcfaa`
  - `dde31389c645d07ce071a535194e9b8691ccbed9838cb43cee4a35c02e77243f`
  - `e250f73404a71be5d0bb3d9db68fac3fc888edcbec3de091081010f3bc898eda`
  - `e86970d7961980e3c55735dc254d961f08c297d8372db5bb4813e1cb3b337056`
