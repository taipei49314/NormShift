# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `a612ba833f8449d650e678f57b221a659ff93b3d51422baf226512930bcd9443`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `fixture-rfc-v1.html` | `RFC9000-excerpt-1` | `ce963be51d85848e4b405d887ebbd35828251766c20807082f534eb052307f0f` | 1163 |
| new | `fixture-rfc-v2.html` | `RFC9000-excerpt-2` | `73b2aa2b39edd7b509823a90c161efbc961b8493328294ca223ab2f9ba906db9` | 1236 |

### Provenance

- **old**: family=`rfc` adapter=`normshift.adapters.rfc`@1.0.0 type=`text/html`
  - local_path (portable): `fixture-rfc-v1.html`
- **new**: family=`rfc` adapter=`normshift.adapters.rfc`@1.0.0 type=`text/html`
  - local_path (portable): `fixture-rfc-v2.html`

## Summary

- Old requirements: **3**
- New requirements: **4**
- Changes: **4**

### Classification counts

- `ADDED`: 1
- `STRENGTHENED`: 1
- `UNCHANGED`: 2

## Changes

### `ADDED` — `f93f794491edba95`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `2593f1c3f0090050`
- New section: RFC 9000: QUIC Excerpt (synthetic corpus) > 3. Frames
- New locator: `id:req-ack|xpath:/body/div/p[5]`
- New text: Receivers MUST acknowledge STREAM frames promptly.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `07ee953b49345bd0bf91dc428648140933d191fb86b1b0129731dd49a2a8224a`
  - `1ae9fc93f3442129837bf34ef1c9e64f502c1be0d271d66cd7eddcd19cc7409e`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `STRENGTHENED` — `08b604dfaaf99bbd`

- Confidence: `0.92`
- Modality transition: `SHOULD->MUST`
- Old requirement: `210cca233d92c95f`
- New requirement: `947f69ba9ba99c24`
- Old section: RFC 9000: QUIC Excerpt (synthetic corpus) > 2. Connections
- New section: RFC 9000: QUIC Excerpt (synthetic corpus) > 2. Connections
- Old locator: `id:req-retry|xpath:/body/div/p[3]`
- New locator: `id:req-retry|xpath:/body/div/p[3]`
- Old text: A server SHOULD retry a handshake when the first attempt fails.
- New text: A server MUST retry a handshake when the first attempt fails.
- Reasons:
  - Obligation strengthened: SHOULD -> MUST.
- Alignment score components:
  - combined: `0.8832`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9344`
  - modality_match: `0.4`
  - section_similarity: `1.0`
  - structural_proximity: `1.0`
  - text_similarity: `0.9573`
  - token_similarity: `0.9355`
- Evidence hashes:
  - `215456f8aa68e98ae80cf131d2ac6c9d8cbee04188404b9f7be434aff1cc2459`
  - `2a74a83c20d5849903c6bec435316ef3e79d1bf6260e994bd2a42ae053399915`
  - `832ce89d4d066cc91de351a8b96a7eef60a08f65418e84ddff9a9524a2e63abc`
  - `9c1ac7eb8441de5e710ca70440c6087eed954453fe97d5942a81745ac9fc3342`
  - `c52cd244180c0f4a4da9d994eb3ce4c9899528912cfd36ede59a6bfe1fe3ba17`

### `UNCHANGED` — `78412bc6caa6b574`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `50b6babcd1c50c5e`
- New requirement: `564e44e536b7b0ee`
- Old section: RFC 9000: QUIC Excerpt (synthetic corpus) > 3. Frames
- New section: RFC 9000: QUIC Excerpt (synthetic corpus) > 3. Frames
- Old locator: `id:req-frame|xpath:/body/div/p[4]`
- New locator: `id:req-frame|xpath:/body/div/p[4]`
- Old text: Senders MUST include a frame type on every frame.
- New text: Senders MUST include a frame type on every frame.
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
  - `6ec92d8e4423aa884aec090742fc4a3c612e72ee7ab0909e9c0a0551ba1f0bca`
  - `d7598611110b4ec751799d4c1b2d2bff19468f0a524efb3e5321a71067e09fd0`
  - `f26413b36d4492dc35f6067367bee6f8f253ddabf127739008667c7190bc4900`
  - `ff45999d7e31771c6d15f8f456ecfaeddeae41317891dff72d868aebde748316`

### `UNCHANGED` — `51cc0e8dda45891f`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `ce20bc64f75e0d15`
- New requirement: `87a0255e114475b1`
- Old section: RFC 9000: QUIC Excerpt (synthetic corpus) > 2. Connections
- New section: RFC 9000: QUIC Excerpt (synthetic corpus) > 2. Connections
- Old locator: `id:req-conn|xpath:/body/div/p[2]`
- New locator: `id:req-conn|xpath:/body/div/p[2]`
- Old text: Endpoints MUST establish a connection before exchanging application data.
- New text: Endpoints MUST establish a connection before exchanging application data.
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
  - `0626949ffb0056d6c607c3646ba66dec039900b5d7a1aba12a511ab9ef7c983d`
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `8e552ac3de6abed223e712af8c482b2c9a2c7746876b2c85c602b8e52f48acab`
  - `95e4995cba80ec676310846e15b4195867c9bb32635167b9fb0b2a5a6e350ceb`
  - `f325c11b1b5c27e2182fcf8e58da0bb5f9ec06343a32c2757bca17c6a057478c`
