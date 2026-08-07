# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `d926f06e257b40b57ab609e0b22445a8a14c7fb9e403a74dee662cb63719c34c`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `split-old.html` | `sha256:d63972e3179c` | `d63972e3179c1218a0ac59755e72d32facf5340f1f2815279159ed698244207b` | 113 |
| new | `split-new.html` | `sha256:9a21cd2f0625` | `9a21cd2f0625f04ded1d6a79ce93bdfd5197ad95f38d83afe10d39d77aef5d55` | 165 |

### Provenance

- **old**: family=`generic_html` adapter=`normshift.adapters.html`@1.0.0 type=`text/html`
  - local_path (portable): `split-old.html`
- **new**: family=`generic_html` adapter=`normshift.adapters.html`@1.0.0 type=`text/html`
  - local_path (portable): `split-new.html`

## Summary

- Old requirements: **1**
- New requirements: **2**
- Changes: **2**

### Classification counts

- `ADDED`: 1
- `AMBIGUOUS`: 1

## Changes

### `ADDED` — `b2bb3a7ff9f3920f`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `4a5aea876c7aed61`
- New section: (root)
- New locator: `xpath:/body/p[2]`
- New text: Clients MUST refresh expired tokens before retrying.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `bf49ac2f2d792de2157e9d50366646b7b99a429f4fc5f23206b63510929d7f2b`
  - `f24e53db9a2e3fa710db2b8bccc2688c2f554e7485841ec6d8f45ef722d9a8cc`

### `AMBIGUOUS` — `37946a6e6cf7e4b8`

- Confidence: `0.55`
- Modality transition: `MUST->MUST`
- Old requirement: `20d9c1b256208673`
- New requirement: `529b466bfbee5cb4`
- Old section: (root)
- New section: (root)
- Old locator: `xpath:/body/p`
- New locator: `xpath:/body/p[1]`
- Old text: Clients MUST authenticate every request using a bearer token.
- New text: Clients MUST present a bearer token on every request.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.8538`
  - actor_action_similarity: `0.8675`
  - editorial_similarity: `0.5893`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `1.0`
  - text_similarity: `0.7895`
  - token_similarity: `0.7193`
- Evidence hashes:
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `902ab284e009bf705dee955091aaae62568d1a8dcbf8fca802437c439e9c6121`
  - `c67a4f493c588a40736a33b01d44e53e44a72cd91d036ad7ea6dba47ddd8b9ff`
  - `da23192ee3d9af77a695a5776db83721d991c099ac3dffc7a050662090b1c4d7`
  - `e4a72738163301db329fd65b944ad9bae258bdf9c047c4579524c46a38342733`
