# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `whatwg`
- Schema version: `1.0.0`
- Integrity: `sha256` `235d99215dc90bf1222a234e47db086037cd9871d9fce5d96b3cacc72a130275`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `fixtures/corpus/whatwg/sample-v1.html` | `LS-excerpt-1` | `cfa04c916868abea8ffc72d7b17cb8f843928b1fb4e8e938d35847a724979297` | 889 |
| new | `fixtures/corpus/whatwg/sample-v2.html` | `LS-excerpt-2` | `85b1dc30504d8676fd9455d4f747283e41c9a6c91c19f4544464bd5834aa0c7f` | 970 |

### Provenance

- **old**: family=`whatwg` adapter=`normshift.adapters.whatwg`@1.0.0 type=`text/html`
  - canonical: `https://html.spec.whatwg.org/multipage/`
  - etag: `W/"whatwg-html-excerpt-v1"`
  - local_path (portable): `fixtures/corpus/whatwg/sample-v1.html`
- **new**: family=`whatwg` adapter=`normshift.adapters.whatwg`@1.0.0 type=`text/html`
  - canonical: `https://html.spec.whatwg.org/multipage/`
  - etag: `W/"whatwg-html-excerpt-v2"`
  - local_path (portable): `fixtures/corpus/whatwg/sample-v2.html`

## Summary

- Old requirements: **3**
- New requirements: **5**
- Changes: **5**

### Classification counts

- `ADDED`: 2
- `STRENGTHENED`: 1
- `UNCHANGED`: 2

## Changes

### `ADDED` — `9118f262517721ce`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `0fe981af55091790`
- New section: HTML (WHATWG-style corpus excerpt) > Forms
- New locator: `id:w4|xpath:/body/p[4]`
- New text: User agents must not submit forms with invalid required controls.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `01ab00650d28b99c92711b2ceae6d8e351675fa365bccb1fb44f904e0194d3a2`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `e7a607101a5084691c5f2db5852db1ff4f0a4b2b561917c12dcf201f2be52359`

### `ADDED` — `44c69761e3ce58f8`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `b6390c428acb094d`
- New section: HTML (WHATWG-style corpus excerpt) > Forms
- New locator: `id:w4|xpath:/body/p[4]`
- New text: User agents must not submit forms with invalid required controls.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `01ab00650d28b99c92711b2ceae6d8e351675fa365bccb1fb44f904e0194d3a2`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `e7a607101a5084691c5f2db5852db1ff4f0a4b2b561917c12dcf201f2be52359`

### `STRENGTHENED` — `fb7a91b84bf9b75d`

- Confidence: `0.92`
- Modality transition: `SHOULD->MUST`
- Old requirement: `9ad8f7df2ef44404`
- New requirement: `ca34655c128469ec`
- Old section: HTML (WHATWG-style corpus excerpt) > Networking
- New section: HTML (WHATWG-style corpus excerpt) > Networking
- Old locator: `id:w2|xpath:/body/p[2]`
- New locator: `id:w2|xpath:/body/p[2]`
- Old text: Authors should provide alternative text for images.
- New text: Authors must provide alternative text for images.
- Reasons:
  - Obligation strengthened: SHOULD -> MUST.
- Alignment score components:
  - combined: `0.8705`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9184`
  - modality_match: `0.4`
  - section_similarity: `1.0`
  - structural_proximity: `1.0`
  - text_similarity: `0.9462`
  - token_similarity: `0.88`
- Evidence hashes:
  - `2125daa64e9e803d4d7a239ef523e5910741174c5871ec4c64b44edcd750e060`
  - `39152fa348751a5d130eeba4b5b43c08d336a201c15d65e50c8d28fc4571f65e`
  - `832ce89d4d066cc91de351a8b96a7eef60a08f65418e84ddff9a9524a2e63abc`
  - `866f6c0225ec8d0f5789cc41a0000c84f45b36965aafbdfb1a6ef6dcf9e19e7b`
  - `d79f24d6b9ae39572a347825489e2b9e76d9039375e1de84ecd615e28892c5eb`

### `UNCHANGED` — `427fc30e154ae86c`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `38fe560239e728a3`
- New requirement: `f3daf26fcd184114`
- Old section: HTML (WHATWG-style corpus excerpt) > Networking
- New section: HTML (WHATWG-style corpus excerpt) > Networking
- Old locator: `id:w1|xpath:/body/p[1]`
- New locator: `id:w1|xpath:/body/p[1]`
- Old text: User agents must close idle sockets after 30 seconds.
- New text: User agents must close idle sockets after 30 seconds.
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
  - `56a30f07341620efa0edce89879d093f8a1e372fd17f4a858dc63aea46851177`
  - `8af5d2547abb43338afceda7780983dc78eeec723ba7693aeb4513e4e94db56a`
  - `9ae76ee7c218d13221a34a65de3f3298c36fa12c70455bdf5199583088fc5deb`
  - `bbceaf96d921df30dd52ffb9629b8ca163bc7d4cb4cb2b31473a5e1435d3f5ca`

### `UNCHANGED` — `941b54974054ab4c`

- Confidence: `0.99`
- Modality transition: `MAY->MAY`
- Old requirement: `3959a6f1dbbc251a`
- New requirement: `080dd3416c87ed58`
- Old section: HTML (WHATWG-style corpus excerpt) > Forms
- New section: HTML (WHATWG-style corpus excerpt) > Forms
- Old locator: `id:w3|xpath:/body/p[3]`
- New locator: `id:w3|xpath:/body/p[3]`
- Old text: Implementations may cache form validation results.
- New text: Implementations may cache form validation results.
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
  - `117f5a8d328b66657c5a0318721b950f4b8d5a04786d947a5664b6ffabdfa529`
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `7d4170a2052290310c3e0d45669c6222dd1a687b53515794e752d182d32b6eee`
  - `c1e5f37e48fe90ed36c9fcf52cbac102287886f9a7f2ec2d435e89ed8de249f8`
  - `f938f436cd4ff5ad9eef30842588743502784b3401b31c1c8604c9cd8b2fd4d3`
