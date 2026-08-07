# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `3516699e783608c62b94b506a35ba1932bc663c3acfba3cb75c3dd07a7065100`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `rfc7159.html` | `sha256:17dfda25ae6c` | `17dfda25ae6cd5715b08e2c96e257101a1d7f9eb27e1711e5b6544138bb35954` | 35554 |
| new | `rfc8259.html` | `sha256:5302d6ccb6cf` | `5302d6ccb6cf221817bdd1f8cd7221661d4519372e0ac0b4cf641e11e8037de7` | 37946 |

### Provenance

- **old**: family=`rfc` adapter=`normshift.adapters.rfc`@1.0.0 type=`text/html`
  - local_path (portable): `rfc7159.html`
- **new**: family=`rfc` adapter=`normshift.adapters.rfc`@1.0.0 type=`text/html`
  - local_path (portable): `rfc8259.html`

## Summary

- Old requirements: **19**
- New requirements: **21**
- Changes: **31**

### Classification counts

- `ADDED`: 12
- `AMBIGUOUS`: 3
- `REMOVED`: 10
- `UNCHANGED`: 6

## Changes

### `ADDED` — `fcdd1ef676132f48`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `0e4cb07af1ac4d2f`
- New section: (pre-text)
- New locator: `xpath:/div/pre[8]#p93`
- New text: The representation of strings is similar to conventions used in the C family of programming languages. A string begins and ends with quotation marks. All Unicode characters may be placed within the quotation marks, except for the characters that MUST be escaped: quotation mark, reverse solidus, and the control characters (U+0000 through U+001F).
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5574f571db0415b53027537fb5fffc31e6b4224f96ed2c31458a410312e3964c`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `8821a010ac0dac00dc13bb309514a8bb4e8b65c6ce66e3a098133912e77cc07d`

### `ADDED` — `87aa98ce46f740e4`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `144b3913d81738a0`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `31f7ac64c1c6622e`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `16899d32621992b9`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `a93c0206927539be`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD_NOT`
- New requirement: `19479c87162428fd`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `c518fb125f957729`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `775296b73940305d`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `ea80fde18aaf6712`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `7bca2e3417142206`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `3a5ceed5198959e3`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `9a0b791f6419a0e0`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `fbd1c88e01df8c85`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `cc6130e1bdb2bdd9`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `a2bbc905685981ca`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `d0b3a0937ca536c2`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `9142e00c2746429f`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD_NOT`
- New requirement: `dbf235dbc73f485a`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `0011c3166e3c0a8e`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `e0c79d8a4a317770`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `41492b27befa2c92`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `eb149b88b61d2013`
- New section: (pre-text)
- New locator: `xpath:/div/pre[4]#p27`
- New text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `435dcb3c6f44a43e88f3a7375aff8b824940c1f23f1635c0afdc49a5712c3a35`
  - `5aaca0096ba77700d25666f80c2eb2e579b8aceb997c5aa85d294f6f542f5dee`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `AMBIGUOUS` — `3f5bcbeda70ea632`

- Confidence: `0.55`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `8cc5a5debd43bb93`
- New requirement: `a0fdf8c679c130a0`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[9]#p104`
- New locator: `xpath:/div/pre[9]#p108`
- Old text: Implementations MUST NOT add a byte order mark to the beginning of a JSON text. In the interests of interoperability, implementations that parse JSON texts MAY ignore the presence of a byte order mark rather than treating it as an error.
- New text: Implementations MUST NOT add a byte order mark (U+FEFF) to the beginning of a networked-transmitted JSON text. In the interests of interoperability, implementations that parse JSON texts MAY ignore the presence of a byte order mark rather than treating it as an error.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9698`
  - actor_action_similarity: `0.9268`
  - editorial_similarity: `0.9416`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.8`
  - text_similarity: `1.0`
  - token_similarity: `0.9386`
- Evidence hashes:
  - `1d39b3846d190b7c444b75255143e4919a4babe9131d881a8c722715b9ff994b`
  - `2208dfc022b8d446f26ae6a6dfbe189aa010a4ee4f49588cbece91d106b8d111`
  - `237cc1c1f5826386881db0a141e10ef5925303f8584b6e505064b5689f97a300`
  - `41946d72b61b41121f2cd7e614780e6efb5b907979077e4cfb61e35848fe638f`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`

### `AMBIGUOUS` — `a51e5377653ad221`

- Confidence: `0.45`
- Modality transition: `MUST->MUST`
- Old requirement: `98e9d82eec864132`
- New requirement: `3a7aba2ae9ae9efc`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[9]#p103`
- New locator: `xpath:/div/pre[9]#p106`
- Old text: JSON text SHALL be encoded in UTF-8, UTF-16, or UTF-32. The default encoding is UTF-8, and JSON texts that are encoded in UTF-8 are interoperable in the sense that they will be read successfully by the maximum number of implementations; there are many implementations that cannot successfully read texts in other encodings (such as UTF-16 and UTF-32).
- New text: JSON text exchanged between systems that are not part of a closed ecosystem MUST be encoded using UTF-8 [RFC3629].
- Reasons:
  - Insufficient evidence for a confident classification → AMBIGUOUS.
- Alignment score components:
  - combined: `0.6318`
  - actor_action_similarity: `0.5714`
  - editorial_similarity: `0.37`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.85`
  - text_similarity: `0.5`
  - token_similarity: `0.357`
- Evidence hashes:
  - `05822773f40030c0583c68a81cc858c5e17928feb63487266e9d2cf3487d9c15`
  - `4279a5439a8fef7cbdcc4de13f0b9ed18dd684114bd054155ae8607981b1a01c`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `a5b6fec7ec83440f288df815132078787da2ded6e22683b9311a6c230e036ee2`
  - `c23a6c2ea38d9b496cf06b02f70e1304167fb36b74305d227800caaaa44c8e9d`

### `AMBIGUOUS` — `8fb1093bca759620`

- Confidence: `0.55`
- Modality transition: `MAY->MAY`
- Old requirement: `9f960d7a415536b5`
- New requirement: `6066b69fc8a2e940`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[9]#p104`
- New locator: `xpath:/div/pre[9]#p108`
- Old text: Implementations MUST NOT add a byte order mark to the beginning of a JSON text. In the interests of interoperability, implementations that parse JSON texts MAY ignore the presence of a byte order mark rather than treating it as an error.
- New text: Implementations MUST NOT add a byte order mark (U+FEFF) to the beginning of a networked-transmitted JSON text. In the interests of interoperability, implementations that parse JSON texts MAY ignore the presence of a byte order mark rather than treating it as an error.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9808`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9416`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.8`
  - text_similarity: `1.0`
  - token_similarity: `0.9386`
- Evidence hashes:
  - `1d39b3846d190b7c444b75255143e4919a4babe9131d881a8c722715b9ff994b`
  - `2208dfc022b8d446f26ae6a6dfbe189aa010a4ee4f49588cbece91d106b8d111`
  - `237cc1c1f5826386881db0a141e10ef5925303f8584b6e505064b5689f97a300`
  - `41946d72b61b41121f2cd7e614780e6efb5b907979077e4cfb61e35848fe638f`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`

### `REMOVED` — `445c37fdd1de4561`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `016e3f2d5d1f9fa5`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `13a9550ace7678d6`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `44cfcc470de919bd`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `55d08f76103e0736`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `50888b4346538df5`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `1efd9072008cfccc`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `5df5118f4ac40875`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `8091b6fa727b6dd4`

- Confidence: `0.95`
- Modality transition: `MUST_NOT->∅`
- Old requirement: `5ee3001139336809`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `9a7f253924cccd4a`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `a422612a3b387fd3`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `a1351ff84955471a`

- Confidence: `0.95`
- Modality transition: `SHOULD_NOT->∅`
- Old requirement: `e38bada977dab4a5`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `97e116b78aa7b683`

- Confidence: `0.95`
- Modality transition: `MUST_NOT->∅`
- Old requirement: `e66f2c0d274a5698`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `775028dad26cb116`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `ea5829528cd6fa31`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `8505e220aa2c10df`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `fcc4bef40b2275d8`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[4]#p27`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC2119].
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `459c215d060a3561baeeeef0bb970fa96a1a45f9657745aab8b5f08097348584`
  - `45c03dc15aaa96e35c9256a6de26208a1fc4de66ff4d4028ed6c048b5e2682e6`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `UNCHANGED` — `af3828a63d5685fa`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `04c3d2e94b80119f`
- New requirement: `c160efcada0586b7`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[10]#p112`
- New locator: `xpath:/div/pre[10]#p116`
- Old text: A JSON parser transforms a JSON text into another representation. A JSON parser MUST accept all texts that conform to the JSON grammar. A JSON parser MAY accept non-JSON forms or extensions.
- New text: A JSON parser transforms a JSON text into another representation. A JSON parser MUST accept all texts that conform to the JSON grammar. A JSON parser MAY accept non-JSON forms or extensions.
- Reasons:
  - Identical normalized text, modality, and section → UNCHANGED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.8`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `1dc5fff384bc812772f4c219fb25d70793d5d2e98e4b77088690bf7aa227846c`
  - `216b16880e4a9b3699d539909bbc6b9b9ec8ad2350b63f48452177a8253c70fc`
  - `7c28ca3ee77cf2fc263bc0cd38c20cea0856108ad2f8ddb48495bc445b672123`
  - `cd0edb58d5cc5bbfc228f285cb37c7f5066fd8d8d9a94faecdc815b0e65a5c16`

### `UNCHANGED` — `04efbc00b8e8547f`

- Confidence: `0.99`
- Modality transition: `MAY->MAY`
- Old requirement: `0f41b9417a4e9bf1`
- New requirement: `91ac169615871f3a`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[10]#p112`
- New locator: `xpath:/div/pre[10]#p116`
- Old text: A JSON parser transforms a JSON text into another representation. A JSON parser MUST accept all texts that conform to the JSON grammar. A JSON parser MAY accept non-JSON forms or extensions.
- New text: A JSON parser transforms a JSON text into another representation. A JSON parser MUST accept all texts that conform to the JSON grammar. A JSON parser MAY accept non-JSON forms or extensions.
- Reasons:
  - Identical normalized text, modality, and section → UNCHANGED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.8`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `1dc5fff384bc812772f4c219fb25d70793d5d2e98e4b77088690bf7aa227846c`
  - `216b16880e4a9b3699d539909bbc6b9b9ec8ad2350b63f48452177a8253c70fc`
  - `7c28ca3ee77cf2fc263bc0cd38c20cea0856108ad2f8ddb48495bc445b672123`
  - `cd0edb58d5cc5bbfc228f285cb37c7f5066fd8d8d9a94faecdc815b0e65a5c16`

### `UNCHANGED` — `5b874a986c7fd1b2`

- Confidence: `0.99`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `4a536649d09b72b8`
- New requirement: `e4c467f70e2f97db`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[6]#p62`
- New locator: `xpath:/div/pre[6]#p64`
- Old text: An object structure is represented as a pair of curly brackets surrounding zero or more name/value pairs (or members). A name is a string. A single colon comes after each name, separating the name from the value. A single comma separates a value from a following name. The names within an object SHOULD be unique.
- New text: An object structure is represented as a pair of curly brackets surrounding zero or more name/value pairs (or members). A name is a string. A single colon comes after each name, separating the name from the value. A single comma separates a value from a following name. The names within an object SHOULD be unique.
- Reasons:
  - Identical normalized text, modality, and section → UNCHANGED.
- Alignment score components:
  - combined: `0.995`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.9`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `9b8e8fcfb4baaae50204bda71f9eec6666e43a37be853f80a8cdd8e1c3ec9fc2`
  - `bc9f26e219e6cb07dbe4f130b8cd06af5f60437875e4634b513135a141e469f8`
  - `da044119705560edb1dcdc54d6d39f6bd00ccf4037afd53d8bd4c678535a0231`
  - `f27175d93152eab85c1804e461bcb457d1beccd74cb854d5aca0ebc5e85d2306`

### `UNCHANGED` — `3b61c4ff839d4af8`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `7d1aab9a37cd75be`
- New requirement: `addbf03b6f184101`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p53`
- New locator: `xpath:/div/pre[6]#p57`
- Old text: A JSON value MUST be an object, array, number, or string, or one of the following three literal names:
- New text: A JSON value MUST be an object, array, number, or string, or one of the following three literal names:
- Reasons:
  - Identical normalized text, modality, and section → UNCHANGED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.8`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `36a7eb2fb7b47cbf61f9f8ad8b103b3450cecc31c1a6e0fb172fc24ba973d2c3`
  - `3f8b3fafb0900878120a1eb0e8803fa25cd12dcbb99a0b39e67db00d1e2d5e5c`
  - `81d4c288d4f3d404ebe66fdeeaa034ffc869cbbc73147ebaefb8705ece2598a6`
  - `c29a6df112ebd3d17d08255def0f8bb499a7d82333cbcbccfcf4b33d8d644140`

### `UNCHANGED` — `1b29d5b159e13af9`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `82e289c208b93685`
- New requirement: `f14890f738036cc1`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p55`
- New locator: `xpath:/div/pre[6]#p59`
- Old text: The literal names MUST be lowercase. No other literal names are allowed.
- New text: The literal names MUST be lowercase. No other literal names are allowed.
- Reasons:
  - Identical normalized text, modality, and section → UNCHANGED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.8`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `05f2b223dfdd531eb8be328ef4017c2116b0f23a9593d02218547d5a090ed096`
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `434082485f3e910176ccd45b1f1ef29fcd503ff51f6741d50fc75ee17ff1db2b`
  - `6603c496ffa89e385fdd1a796a69a7acfc9a07e788e5e41fbbad45a64b15037e`
  - `b1d9ec56f08aeefb70fb25c542f063adc5c348668c27191cf12f5f0606d8cbf4`

### `UNCHANGED` — `368399f73654f9f8`

- Confidence: `0.99`
- Modality transition: `MUST->MUST`
- Old requirement: `e5706e135b4ac61a`
- New requirement: `a4e16b4dd9f6cd3d`
- Old section: (pre-text)
- New section: (pre-text)
- Old locator: `xpath:/div/pre[10]#p115`
- New locator: `xpath:/div/pre[10]#p119`
- Old text: A JSON generator produces JSON text. The resulting text MUST strictly conform to the JSON grammar.
- New text: A JSON generator produces JSON text. The resulting text MUST strictly conform to the JSON grammar.
- Reasons:
  - Identical normalized text, modality, and section → UNCHANGED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.8`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `09d6a563a1ef86a3ed32999fc987f7a6ecdabf6eb6badf40a3569513ebdfeab1`
  - `157de662f416648e6c03ba742491efbe1df6b4773fa04459dd0e1cb3e671d338`
  - `194afbae0af3a8c9831e751964061892c157145e076f68d9da1505b73b44f610`
  - `42f6ac21cd29fc57bbeaa7250e4b7049dfb141d42194e8e121b408242269434b`
  - `bb1bfc4f106efd5eea97bd6c428afe67500aed4d20d69246e249f364fdbb45ad`
