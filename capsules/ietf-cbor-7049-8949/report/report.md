# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `f7f2c527ed398cc9bca14f1462f86b795c14023ff5c48e2911ee4669f0eee8f3`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `rfc7049.html` | `sha256:876898077938` | `87689807793837a99ae24c29b4de07cc861a006531abcf45ab56dcff6d77d9ca` | 156765 |
| new | `rfc8949.html` | `RFC8949` | `6ac12612df1382746ff194ddeef0ce70a6c4f95d9071844c10a9092b0016eeba` | 338064 |

### Provenance

- **old**: family=`rfc` adapter=`normshift.adapters.rfc`@1.0.0 type=`text/html`
  - local_path (portable): `rfc7049.html`
- **new**: family=`rfc` adapter=`normshift.adapters.rfc`@1.0.0 type=`text/html`
  - local_path (portable): `rfc8949.html`

## Summary

- Old requirements: **17**
- New requirements: **43**
- Changes: **56**

### Classification counts

- `ADDED`: 39
- `AMBIGUOUS`: 3
- `CONDITION_ADDED`: 1
- `REMOVED`: 13

## Changes

### `ADDED` — `01f497cf500e1935`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `084160ceed5232f4`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1.2.4|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]/ul/li[4]`
- New text: 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `8ecb776cf1460ecaea9212561bfb55881ed76a3e8b88e67a89b1ead66e8d633b`
  - `d03c1953b2cee06c9607ee47d754f7371c017fdd4c86725ba6278e856e503863`

### `ADDED` — `1da9f29743c8ed6f`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `13f5b3727ea26bc2`
- New section: Concise Binary Object Representation (CBOR) > 2. CBOR Data Models > 2.2. Specific Data Models
- New locator: `id:section-2.2-2|xpath:/body/div[6]/section/div[2]/section/p[2]`
- New text: Specific data models can also specify value equivalency (including values of different types) for the purposes of map keys and encoder freedom. For example, in the generic data model, a valid map MAY have both 0 and 0.0 as keys, and an encoder MUST NOT encode 0.0 as an integer (major type 0, Section 3.1). However, if a specific data model declares that floating-point and integer representations of integral values are equivalent, using both map keys 0 and 0.0 in a single map would be considered duplicates, even while encoded as different major types, and so invalid; and an encoder could encode integral-valued floats as integers or vice versa, perhaps to save encoded bytes.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `0096bfe4f70d404fffeb304c1fe5fcd9841ed3be6267c05c5659bf22d0f7d128`
  - `01e2f977e724fde0d75fbf00096decf08b358007ccf215c3b672849a460d49a8`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `6ad2411e1029db66`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `167c74983b945416`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1.2.2|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]/ul/li[2]`
- New text: 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `0c68e890dde70eb4bef373689ea8b42d60e321f800d84338a32b7f213d50f4bb`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `ed02da10a897c70c477903e2b80aa3c66b85c2b7e6e2be9b3684fa6d76cea334`

### `ADDED` — `0497eb937dc6a924`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `2d99e20f82f529b8`
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding
- New locator: `id:section-3-1|xpath:/body/div[7]/section/p[1]`
- New text: A CBOR data item (Section 2) is encoded to or decoded from a byte string carrying a well-formed encoded data item as described in this section. The encoding is summarized in Table 7 in Appendix B, indexed by the initial byte. An encoder MUST produce only well-formed encoded data items. A decoder MUST NOT return a decoded data item when it encounters input that is not a well-formed encoded CBOR data item (this does not detract from the usefulness of diagnostic and recovery tools that might make available some information from a damaged encoded CBOR data item).¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `00ababa6fea49383870f70cef17fd31bf4acf531606163e05f5b2cb0eec09f87`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `8620387738a637badf51126edf8b6eacca5f5e7aa61cc9d6ddb8abdf1403340e`

### `ADDED` — `585d904aa265c298`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `2e61a639471a7919`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]/p[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `359c7c63a3a57d53613631a941d0fb9a86b6071b50571f2906475112239578cd`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `fb906bbbfc2650dfd0b59256c7a0b0c6cab4e458556e8fd2add3f04a1e83876b`

### `ADDED` — `36943d15f73bb75e`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `30f47b47a4c2597c`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.3.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[3]/p`
- New text: The keys in every map MUST be sorted in the bytewise lexicographic order of their deterministic encodings. For example, the following keys are sorted correctly:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `13a7424877f7c0d670ac063d0698c2337bfc56971627f97ab02f445052cb1a44`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `dd5e0394c230ae0a7852a3513291a31f30f2b8c4447038c239db30923e2b19c5`

### `ADDED` — `5ab61c9fd0521e1b`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `328be9647f2de14c`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols > 5.6. Specifying Keys for Maps
- New locator: `id:section-5.6-4|xpath:/body/div[9]/section/div[6]/section/p[4]`
- New text: A CBOR-based protocol MUST define what to do when a receiving application sees multiple identical keys in a map. The resulting rule in the protocol MUST respect the CBOR data model: it cannot prescribe a specific handling of the entries with the identical keys, except that it might have a rule that having identical keys in a map indicates a malformed map and that the decoder has to stop with an error. When processing maps that exhibit entries with duplicate keys, a generic decoder might do one of the following:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5250e13a5c3bde6865a3be2a300dd1e31734629837ac5268fcf6f6c5f0df6ff0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `f7924766bb38730c60eeda429bc38712b30e2ee1b42e161336868ec7564b0997`

### `ADDED` — `85d5e6f5bc02850d`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `34529919ec1afc50`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1.2.3|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]/ul/li[3]`
- New text: 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `74867d0daf9118fdc8ef54f74fa31543ca0f2df5bf8881510da0d6a360b7deae`
  - `78181921a7ee709e134cb93ae55c15cfdaeb5f2fb7555fd5851eddc56c82453a`

### `ADDED` — `2f047cac0ed4eb32`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `34b9744bf7e38430`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.3|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[3]`
- New text: The keys in every map MUST be sorted in the bytewise lexicographic order of their deterministic encodings. For example, the following keys are sorted correctly:¶ 10, encoded as 0x0a.¶ 100, encoded as 0x1864.¶ -1, encoded as 0x20.¶ "z", encoded as 0x617a.¶ "aa", encoded as 0x626161.¶ [100], encoded as 0x811864.¶ [-1], encoded as 0x8120.¶ false, encoded as 0xf4.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7bea08762dc66580e41aada0f0633891ab92366244859c91ebc66b29626117bb`
  - `eae38fed894e469a50aca3ea8b44a064879478853348fb726d411f9c7376ff44`

### `ADDED` — `b451d4c88c23d5f2`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `370fc8a285f50a8a`
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding > 3.3. Floating-Point Numbers and Values with No Content
- New locator: `id:section-3.3-5|xpath:/body/div[7]/section/div[3]/section/p[3]`
- New text: An encoder MUST NOT issue two-byte sequences that start with 0xf8 (major type 7, additional information 24) and continue with a byte less than 0x20 (32 decimal). Such sequences are not well-formed. (This implies that an encoder cannot encode false, true, null, or undefined in two-byte sequences and that only the one-byte variants of these are well-formed; more generally speaking, each simple value only has a single representation variant).¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `149c0390a5eeeb79c51f37f211a2a87cb81a3a3ed0562addd397f8dece313d84`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `bdda7e21d2e6f9703e910bdb390c9e2dd3165069960c3d90c021b0e3e9bcf775`

### `ADDED` — `b9dc62d549ad8efd`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `466b9fd7d4f5cb75`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶ 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶ 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶ 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶ 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶ Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `31596c0e3f256f88f2c45c24d20730eea3fec350260b2a75293d17b7dd99769a`
  - `365625e59fa744fd68ba7f3836d789856faf2c85d4c1a47484b7ec89480fbf57`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `1135c107b0eeee1c`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `6227c5628168c10d`
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding
- New locator: `id:section-3-1|xpath:/body/div[7]/section/p[1]`
- New text: A CBOR data item (Section 2) is encoded to or decoded from a byte string carrying a well-formed encoded data item as described in this section. The encoding is summarized in Table 7 in Appendix B, indexed by the initial byte. An encoder MUST produce only well-formed encoded data items. A decoder MUST NOT return a decoded data item when it encounters input that is not a well-formed encoded CBOR data item (this does not detract from the usefulness of diagnostic and recovery tools that might make available some information from a damaged encoded CBOR data item).¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `00ababa6fea49383870f70cef17fd31bf4acf531606163e05f5b2cb0eec09f87`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `8620387738a637badf51126edf8b6eacca5f5e7aa61cc9d6ddb8abdf1403340e`

### `ADDED` — `4a8f65478d3c9f3c`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `630c98e6f86dc4a5`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols > 5.6. Specifying Keys for Maps
- New locator: `id:section-5.6-4|xpath:/body/div[9]/section/div[6]/section/p[4]`
- New text: A CBOR-based protocol MUST define what to do when a receiving application sees multiple identical keys in a map. The resulting rule in the protocol MUST respect the CBOR data model: it cannot prescribe a specific handling of the entries with the identical keys, except that it might have a rule that having identical keys in a map indicates a malformed map and that the decoder has to stop with an error. When processing maps that exhibit entries with duplicate keys, a generic decoder might do one of the following:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5250e13a5c3bde6865a3be2a300dd1e31734629837ac5268fcf6f6c5f0df6ff0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `f7924766bb38730c60eeda429bc38712b30e2ee1b42e161336868ec7564b0997`

### `ADDED` — `132bed032cab6b15`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `67f97748519b954b`
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding > 3.4. Tagging of Items
- New locator: `id:section-3.4-11|xpath:/body/div[7]/section/div[4]/section/p[10]`
- New text: IANA allocated tag numbers 65535, 4294967295, and 18446744073709551615 (binary all-ones in 16-bit, 32-bit, and 64-bit). These can be used as a convenience for implementers who want a single-integer data structure to indicate either the presence of a specific tag or absence of a tag. That allocation is described in Section 10 of [CBOR-TAGS]. These tags are not intended to occur in actual CBOR data items; implementations MAY flag such an occurrence as an error.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `c71192b84313aff62f1cd7773ed8025f8a326e41306c96c341681e06e39b4461`
  - `d22e720a4f7b8b86b3be84887639baa20c9176d4f9e86c034e98f033e5b82e44`

### `ADDED` — `5190e24b65853847`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `680843337b47f3e1`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶ 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶ 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶ 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶ 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶ Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `31596c0e3f256f88f2c45c24d20730eea3fec350260b2a75293d17b7dd99769a`
  - `365625e59fa744fd68ba7f3836d789856faf2c85d4c1a47484b7ec89480fbf57`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `fd82f9b56f7cf6e6`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `6909ce5b3cb32c90`
- New section: Concise Binary Object Representation (CBOR) > 9. IANA Considerations > 9.5. Structured Syntax Suffix Registry
- New locator: `id:section-9.5-2.12|xpath:/body/div[13]/section/div[5]/section/dl/dd[11]`
- New text: The syntax and semantics of fragment identifiers specified for +cbor SHOULD be as specified for "application/cbor". (At publication of RFC 8949, there is no fragment identification syntax defined for "application/cbor".)¶ The syntax and semantics for fragment identifiers for a specific "xxx/yyy+cbor" SHOULD be processed as follows:¶ For cases defined in +cbor, where the fragment identifier resolves per the +cbor rules, then process as specified in +cbor.¶ For cases defined in +cbor, where the fragment identifier does not resolve per the +cbor rules, then process as specified in "xxx/yyy+cbor".¶ For cases not defined in +cbor, then process as specified in "xxx/yyy+cbor".¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7480ddbbf206f0378b2f900adf1282762352221f809822e23c439d846f000cd1`
  - `87cb93ff1a87cd4f6f73c64b8a08c45168ed2f3bdfa8c882dfa6d315f4730079`

### `ADDED` — `f0d82341d099d003`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `6b8a8ed633d26460`
- New section: Concise Binary Object Representation (CBOR) > 2. CBOR Data Models > 2.2. Specific Data Models
- New locator: `id:section-2.2-2|xpath:/body/div[6]/section/div[2]/section/p[2]`
- New text: Specific data models can also specify value equivalency (including values of different types) for the purposes of map keys and encoder freedom. For example, in the generic data model, a valid map MAY have both 0 and 0.0 as keys, and an encoder MUST NOT encode 0.0 as an integer (major type 0, Section 3.1). However, if a specific data model declares that floating-point and integer representations of integral values are equivalent, using both map keys 0 and 0.0 in a single map would be considered duplicates, even while encoded as different major types, and so invalid; and an encoder could encode integral-valued floats as integers or vice versa, perhaps to save encoded bytes.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `0096bfe4f70d404fffeb304c1fe5fcd9841ed3be6267c05c5659bf22d0f7d128`
  - `01e2f977e724fde0d75fbf00096decf08b358007ccf215c3b672849a460d49a8`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `5c9db0adc4db8af5`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `6e3a9f3d94fddb64`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols > 5.6. Specifying Keys for Maps
- New locator: `id:section-5.6-7|xpath:/body/div[9]/section/div[6]/section/p[6]`
- New text: The CBOR data model for maps does not allow ascribing semantics to the order of the key/value pairs in the map representation. Thus, a CBOR-based protocol MUST NOT specify that changing the key/value pair order in a map changes the semantics, except to specify that some orders are disallowed, for example, where they would not meet the requirements of a deterministic encoding (Section 4.2). (Any secondary effects of map ordering such as on timing, cache usage, and other potential side channels are not considered part of the semantics but may be enough reason on their own for a protocol to require a deterministic encoding format.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `102d06100111c769927ca63705a5980308b9038926532de288c7d029cf1ae790`
  - `59c10715a317d483310eb2ea7cf4548ceb0d7fc1379312bfa5a163f186710642`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `012ebabf6c10c69b`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `78910fe9edd3e0ec`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶ 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶ 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶ 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶ 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶ Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `31596c0e3f256f88f2c45c24d20730eea3fec350260b2a75293d17b7dd99769a`
  - `365625e59fa744fd68ba7f3836d789856faf2c85d4c1a47484b7ec89480fbf57`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `9cfc9401992a2d66`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `7b1dcb19088be964`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols > 5.3. Validity of Items
- New locator: `id:section-5.3-3|xpath:/body/div[9]/section/div[3]/section/p[2]`
- New text: A CBOR-based protocol MUST specify which of these options its decoders take for each kind of invalid item they might encounter.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `551eec9cfd993120d691977d15e6eba7d73acaefb0204b42840b383987293011`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `c8b76d0252416c0d649c313523b6c3bac7c76a4f782d47b299611c7edf177649`

### `ADDED` — `4d97a5fa4103d505`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `7c8915608f203b79`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols > 5.1. CBOR in Streaming Applications
- New locator: `id:section-5.1-2|xpath:/body/div[9]/section/div[1]/section/p[2]`
- New text: Not all of the bytes making up a data item may be immediately available to the decoder; some decoders will buffer additional data until a complete data item can be presented to the application. Other decoders can present partial information about a top-level data item to an application, such as the nested data items that could already be decoded, or even parts of a byte string that hasn't completely arrived yet. Such an application also MUST have a matching streaming security mechanism, where the desired protection is available for incremental data presented to the application.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5ac5a64d53fde74433353cc110e9c0fcb1e317df1d33cecbf2ce74c871138ff7`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `93a603d21847398aa0eb9ea3bf50d329c00ea54ba9069a3d1a76781c70f49262`

### `ADDED` — `8ef3e21ebed141eb`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `87c55a6545a6b47e`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols
- New locator: `id:section-5-3|xpath:/body/div[9]/section/p[3]`
- New text: CBOR-based protocols MUST specify how their decoders handle invalid and other unexpected data. CBOR-based protocols MAY specify that they treat arbitrary valid data as unexpected. Encoders for CBOR-based protocols MUST produce only valid items, that is, the protocol cannot be designed to make use of invalid items. An encoder can be capable of encoding as many or as few types of values as is required by the protocol in which it is used; a decoder can be capable of understanding as many or as few types of values as is required by the protocols in which it is used. This lack of restrictions allows CBOR to be used in extremely constrained environments.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `58f07fe9e98ba47b7150256250c1ccd0131bfb6a7538df6f31026e7ebd0c81d0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `932077847f6f6a25bcefdc67647e36292a32eb39ad95724337a518d783145e35`

### `ADDED` — `63e76f923ad67af9`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `8ca63a8bd67e6cbd`
- New section: Concise Binary Object Representation (CBOR) > 9. IANA Considerations > 9.5. Structured Syntax Suffix Registry
- New locator: `id:section-9.5-2.12|xpath:/body/div[13]/section/div[5]/section/dl/dd[11]`
- New text: The syntax and semantics of fragment identifiers specified for +cbor SHOULD be as specified for "application/cbor". (At publication of RFC 8949, there is no fragment identification syntax defined for "application/cbor".)¶ The syntax and semantics for fragment identifiers for a specific "xxx/yyy+cbor" SHOULD be processed as follows:¶ For cases defined in +cbor, where the fragment identifier resolves per the +cbor rules, then process as specified in +cbor.¶ For cases defined in +cbor, where the fragment identifier does not resolve per the +cbor rules, then process as specified in "xxx/yyy+cbor".¶ For cases not defined in +cbor, then process as specified in "xxx/yyy+cbor".¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7480ddbbf206f0378b2f900adf1282762352221f809822e23c439d846f000cd1`
  - `87cb93ff1a87cd4f6f73c64b8a08c45168ed2f3bdfa8c882dfa6d315f4730079`

### `ADDED` — `73be315494f83836`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD_NOT`
- New requirement: `9756a5800d3a0583`
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding > 3.4. Tagging of Items
- New locator: `id:section-3.4-10|xpath:/body/div[7]/section/div[4]/section/p[9]`
- New text: Conceptually, tags are interpreted in the generic data model, not at (de-)serialization time. A small number of tags (at this time, tag number 25 and tag number 29 [IANA.cbor-tags]) have been registered with semantics that may require processing at (de-)serialization time: the decoder needs to be aware of, and the encoder needs to be in control of, the exact sequence in which data items are encoded into the CBOR data item. This means these tags cannot be implemented on top of an arbitrary generic CBOR encoder/decoder (which might not reflect the serialization order for entries in a map at the data model level and vice versa); their implementation therefore typically needs to be integrated into the generic encoder/decoder. The definition of new tags with this property is NOT RECOMMENDED.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `8619aa544d53171d77c695157b742f0e5240d587892fc9721be38bef19bc6801`
  - `d9ad6f94759bba0ba66a0b68334f0e67496c222457150dbcc9abee4ec1c99e2b`

### `ADDED` — `3598a02c2a2daa49`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `adea50f37d401dc9`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶ 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶ 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶ 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶ 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶ Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `31596c0e3f256f88f2c45c24d20730eea3fec350260b2a75293d17b7dd99769a`
  - `365625e59fa744fd68ba7f3836d789856faf2c85d4c1a47484b7ec89480fbf57`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `9bafa94154f9c318`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `af0b47940d1c029f`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.3. Length-First Map Key Ordering
- New locator: `id:section-4.2.3-2|xpath:/body/div[8]/section/div[2]/section/div[3]/section/p[2]`
- New text: A CBOR encoding satisfies the "length-first core deterministic encoding requirements" if it satisfies the core deterministic encoding requirements except that the keys in every map MUST be sorted such that:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5d828250220f918c3bf9395a2efde1534ad7931fc33c02f08e8a9d3f6aaa526b`
  - `6b4e6bd1ed2332b4ea0005c14b567589e61c4191ca5177a1a3e04b50dd8cec82`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `dca86a0754cfeba1`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `b9142679738e8a58`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols
- New locator: `id:section-5-3|xpath:/body/div[9]/section/p[3]`
- New text: CBOR-based protocols MUST specify how their decoders handle invalid and other unexpected data. CBOR-based protocols MAY specify that they treat arbitrary valid data as unexpected. Encoders for CBOR-based protocols MUST produce only valid items, that is, the protocol cannot be designed to make use of invalid items. An encoder can be capable of encoding as many or as few types of values as is required by the protocol in which it is used; a decoder can be capable of understanding as many or as few types of values as is required by the protocols in which it is used. This lack of restrictions allows CBOR to be used in extremely constrained environments.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `58f07fe9e98ba47b7150256250c1ccd0131bfb6a7538df6f31026e7ebd0c81d0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `932077847f6f6a25bcefdc67647e36292a32eb39ad95724337a518d783145e35`

### `ADDED` — `0a6458e74d7b0ad4`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `bbc27c4a456d0672`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶ 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶ 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶ 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶ 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶ Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `31596c0e3f256f88f2c45c24d20730eea3fec350260b2a75293d17b7dd99769a`
  - `365625e59fa744fd68ba7f3836d789856faf2c85d4c1a47484b7ec89480fbf57`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `9bf5d58e08bbcd3b`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `bc93919cf577a886`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]/p[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `359c7c63a3a57d53613631a941d0fb9a86b6071b50571f2906475112239578cd`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `fb906bbbfc2650dfd0b59256c7a0b0c6cab4e458556e8fd2add3f04a1e83876b`

### `ADDED` — `bea66d5f6d5b0a45`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `c1cfd486ac91529f`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1.2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]/ul/li[1]`
- New text: 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `45330721b19c7b482cbb79e51c10a967351c51290c8f4fe829746165a6e91981`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `e7431e629fdee909278a4b19d34b0f5a2f93c20e65aa79aeede863cc18596a0d`

### `ADDED` — `a190e97cebe3394e`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `cb6dd3be207f9339`
- New section: Concise Binary Object Representation (CBOR) > 6. Converting Data between CBOR and JSON
- New locator: `id:section-6-1|xpath:/body/div[10]/section/p[1]`
- New text: This section gives non-normative advice about converting between CBOR and JSON. Implementations of converters MAY use whichever advice here they want.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9b3864644210644b147c333b834a1fce983e45f51ccf1ec8e3f27427d557b3fc`
  - `e459542a7a0bff3ee573971464f0d909f8f7d11bd737b174b6b7fb694c304b17`

### `ADDED` — `c4b8f6082819c04f`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `cc76bb2388f4f4bc`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶ 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶ 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶ 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶ 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶ Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `31596c0e3f256f88f2c45c24d20730eea3fec350260b2a75293d17b7dd99769a`
  - `365625e59fa744fd68ba7f3836d789856faf2c85d4c1a47484b7ec89480fbf57`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `16aa4d36c139af6a`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `dc9a7c49161c2f88`
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding > 3.4. Tagging of Items > 3.4.2. Epoch-Based Date/Time
- New locator: `id:section-3.4.2-2|xpath:/body/div[7]/section/div[4]/section/div[3]/section/p[2]`
- New text: The tag content MUST be an unsigned or negative integer (major types 0 and 1) or a floating-point number (major type 7 with additional information 25, 26, or 27). Other contained types are invalid.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `3b00f2a580bc0b6a944e46b46fe225e1983303bf01ef597e575438734001d2f0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `a98875f810a309687851ef0172d89a90a3f83acf0ca90dff3350017709820d67`

### `ADDED` — `87f4722bdfe12415`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `df03f2e8279bacb7`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]`
- New text: Preferred serialization MUST be used. In particular, this means that arguments (see Section 3) for integers, lengths in major types 2 through 5, and tags MUST be as short as possible, for instance:¶ 0 to 23 and -1 to -24 MUST be expressed in the same byte as the major type;¶ 24 to 255 and -25 to -256 MUST be expressed only with an additional uint8_t;¶ 256 to 65535 and -257 to -65536 MUST be expressed only with an additional uint16_t;¶ 65536 to 4294967295 and -65537 to -4294967296 MUST be expressed only with an additional uint32_t.¶ Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `31596c0e3f256f88f2c45c24d20730eea3fec350260b2a75293d17b7dd99769a`
  - `365625e59fa744fd68ba7f3836d789856faf2c85d4c1a47484b7ec89480fbf57`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `719786d9dab0b9ce`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `e77f770c40dcc2e1`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.1.3|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[1]/p[2]`
- New text: Floating-point values also MUST use the shortest form that preserves the value, e.g., 1.5 is encoded as 0xf93e00 (binary16) and 1000000.5 as 0xfa49742408 (binary32). (One implementation of this is to have all floats start as a 64-bit float, then do a test conversion to a 32-bit float; if the result is the same numeric value, use the shorter form and repeat the process with a test conversion to a 16-bit float. This also works to select 16-bit float for positive and negative Infinity as well.)¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `f8871ce79b1ad7a971584aa237b9b2660f0cbe5acbad6cb3475a029fd596a33a`
  - `f9f3c08d66717675d076a6fc125bce02a1e954bba0b2801af41b0a5592d1607a`

### `ADDED` — `545e165297631e05`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `ea36dfe24f378dde`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols > 5.3. Validity of Items
- New locator: `id:section-5.3-1|xpath:/body/div[9]/section/div[3]/section/p[1]`
- New text: A well-formed but invalid CBOR data item (Section 1.2) presents a problem with interpreting the data encoded in it in the CBOR data model. A CBOR-based protocol could be specified in several layers, in which the lower layers don't process the semantics of some of the CBOR data they forward. These layers can't notice any validity errors in data they don't process and MUST forward that data as-is. The first layer that does process the semantics of an invalid CBOR item MUST pick one of two choices:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `80cceb62dda9f78ea1c4119a5800184dc871a65407f448ad0866466525f778b7`
  - `a537c5d386bde98c3bba50603787e98f3c41aa056aae92fbf98883c68fd8b10e`

### `ADDED` — `50ae68e14e836df3`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `ec64dd083bb3b543`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols
- New locator: `id:section-5-3|xpath:/body/div[9]/section/p[3]`
- New text: CBOR-based protocols MUST specify how their decoders handle invalid and other unexpected data. CBOR-based protocols MAY specify that they treat arbitrary valid data as unexpected. Encoders for CBOR-based protocols MUST produce only valid items, that is, the protocol cannot be designed to make use of invalid items. An encoder can be capable of encoding as many or as few types of values as is required by the protocol in which it is used; a decoder can be capable of understanding as many or as few types of values as is required by the protocols in which it is used. This lack of restrictions allows CBOR to be used in extremely constrained environments.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `58f07fe9e98ba47b7150256250c1ccd0131bfb6a7538df6f31026e7ebd0c81d0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `932077847f6f6a25bcefdc67647e36292a32eb39ad95724337a518d783145e35`

### `ADDED` — `460d5389575f4098`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `f8539a8749a7ec83`
- New section: Concise Binary Object Representation (CBOR) > 5. Creating CBOR-Based Protocols > 5.3. Validity of Items
- New locator: `id:section-5.3-1|xpath:/body/div[9]/section/div[3]/section/p[1]`
- New text: A well-formed but invalid CBOR data item (Section 1.2) presents a problem with interpreting the data encoded in it in the CBOR data model. A CBOR-based protocol could be specified in several layers, in which the lower layers don't process the semantics of some of the CBOR data they forward. These layers can't notice any validity errors in data they don't process and MUST forward that data as-is. The first layer that does process the semantics of an invalid CBOR item MUST pick one of two choices:¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `80cceb62dda9f78ea1c4119a5800184dc871a65407f448ad0866466525f778b7`
  - `a537c5d386bde98c3bba50603787e98f3c41aa056aae92fbf98883c68fd8b10e`

### `ADDED` — `0b7f251f1309302e`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `fe2380e0e1ebfc6c`
- New section: Concise Binary Object Representation (CBOR) > 4. Serialization Considerations > 4.2. Deterministically Encoded CBOR > 4.2.1. Core Deterministic Encoding Requirements
- New locator: `id:section-4.2.1-2.2|xpath:/body/div[8]/section/div[2]/section/div[1]/section/ul/li[2]`
- New text: Indefinite-length items MUST NOT appear. They can be encoded as definite-length items instead.¶
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `735534918f0a4ee4876d892842277523742b937b5b7225a8a0a32fe8d828465f`
  - `d5f7fc7c54171e34b01f9b8b3caee7c8943fba372d3a94d1b7acaac178877adc`

### `AMBIGUOUS` — `958f1b4330cc6989`

- Confidence: `0.55`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `016c84159cf49e8c`
- New requirement: `50169f8d584f25d4`
- Old section: (pre-text)
- New section: Concise Binary Object Representation (CBOR) > 9. IANA Considerations > 9.5. Structured Syntax Suffix Registry
- Old locator: `xpath:/div/pre[37]#p394`
- New locator: `id:section-9.5-2.12.1|xpath:/body/div[13]/section/div[5]/section/dl/dd[11]/p[1]`
- Old text: Fragment Identifier Considerations: The syntax and semantics of fragment identifiers specified for +cbor SHOULD be as specified for "application/cbor". (At publication of this document, there is no fragment identification syntax defined for "application/cbor".)
- New text: The syntax and semantics of fragment identifiers specified for +cbor SHOULD be as specified for "application/cbor". (At publication of RFC 8949, there is no fragment identification syntax defined for "application/cbor".)¶
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.7987`
  - actor_action_similarity: `0.9301`
  - editorial_similarity: `0.8793`
  - modality_match: `1.0`
  - section_similarity: `0.1468`
  - structural_proximity: `0.0`
  - text_similarity: `0.9048`
  - token_similarity: `0.8838`
- Evidence hashes:
  - `0068e7c784a5946260c59c402672a8a10e2e89932c60c44378723d5b83f6eb05`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `6a7982723f2ebcc5d0493f62a97fd935669f3789b626cfdb6a2d6ff8ce2182cb`
  - `8b303e3e674a12e58e8297d5ba92e20b1c181d63fce747a8592d3d6ca90b63f8`
  - `ac907eca7011bb49e9200b772c85374d74cddd7ba03ced14bb359d24ba73e2f1`

### `AMBIGUOUS` — `9e9fea153a9d2075`

- Confidence: `0.55`
- Modality transition: `MUST->MUST`
- Old requirement: `85f2de6dcf5a75ad`
- New requirement: `476fd508acfc2093`
- Old section: (pre-text)
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding > 3.4. Tagging of Items > 3.4.4. Decimal Fractions and Bigfloats
- Old locator: `xpath:/div/pre[17]#p149`
- New locator: `id:section-3.4.4-4|xpath:/body/div[7]/section/div[4]/section/div[5]/section/p[4]`
- Old text: A decimal fraction or a bigfloat is represented as a tagged array that contains exactly two integer numbers: an exponent e and a mantissa m. Decimal fractions (tag 4) use base-10 exponents; the value of a decimal fraction data item is m*(10**e). Bigfloats (tag 5) use base-2 exponents; the value of a bigfloat data item is m*(2**e). The exponent e MUST be represented in an integer of major type 0 or 1, while the mantissa also can be a bignum (Section 2.4.2).
- New text: A decimal fraction or a bigfloat is represented as a tagged array that contains exactly two integer numbers: an exponent e and a mantissa m. Decimal fractions (tag number 4) use base-10 exponents; the value of a decimal fraction data item is m*(10e). Bigfloats (tag number 5) use base-2 exponents; the value of a bigfloat data item is m*(2e). The exponent e MUST be represented in an integer of major type 0 or 1, while the mantissa can also be a bignum (Section 3.4.3). Contained items with other structures are invalid.¶
- Reasons:
  - Condition text changed; insufficient specificity → AMBIGUOUS.
- Alignment score components:
  - combined: `0.8215`
  - actor_action_similarity: `0.9434`
  - editorial_similarity: `0.9137`
  - modality_match: `1.0`
  - section_similarity: `0.1029`
  - structural_proximity: `0.0`
  - text_similarity: `0.9524`
  - token_similarity: `0.9246`
- Evidence hashes:
  - `02d29e630583c04b209b159a8f5bfa6f927cc41a069a74a9e525b7a4eff82c03`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `76e4570792c95b4b9a8c6532726652069b4ce7557422625d24de61f2bcbc4f5a`
  - `a565d5e64af493928882b527c84d9f52861a1dec9bbff97a2294db953a28ec91`
  - `e1ed485d99ef8fe64b43a83d956e3234ed7551aaefdd7364ce658724d05c063e`

### `AMBIGUOUS` — `3c026f9b0e3154b4`

- Confidence: `0.55`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `9cecd5af540e0920`
- New requirement: `fefff28edf2823f8`
- Old section: (pre-text)
- New section: Concise Binary Object Representation (CBOR) > 9. IANA Considerations > 9.5. Structured Syntax Suffix Registry
- Old locator: `xpath:/div/pre[37]#p395`
- New locator: `id:section-9.5-2.12.2|xpath:/body/div[13]/section/div[5]/section/dl/dd[11]/p[2]`
- Old text: The syntax and semantics for fragment identifiers for a specific "xxx/yyy+cbor" SHOULD be processed as follows:
- New text: The syntax and semantics for fragment identifiers for a specific "xxx/yyy+cbor" SHOULD be processed as follows:¶
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.8591`
  - actor_action_similarity: `0.9796`
  - editorial_similarity: `0.9908`
  - modality_match: `1.0`
  - section_similarity: `0.1468`
  - structural_proximity: `0.0`
  - text_similarity: `0.9953`
  - token_similarity: `0.9955`
- Evidence hashes:
  - `084bfb2543107dd28e156529e50c116c5131c926c29b701ad4a5da18978b7961`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `64e50167e535314ccbc3287e78ceee3ede46f858172775e4c9c1bc28690e3f54`
  - `bf5bb970d6b72717d3dd891dfa2c427bd7a5335412d6ad1209706fff84b24255`
  - `ff41b98dc76ccd70b1a01d259725f8acb59647b7d1211716bf6677f9129e9063`

### `CONDITION_ADDED` — `5c5f4f8c81b05642`

- Confidence: `0.88`
- Modality transition: `MUST->MUST`
- Old requirement: `d5c12b884b44eb7e`
- New requirement: `6c0cf32c8a539895`
- Old section: (pre-text)
- New section: Concise Binary Object Representation (CBOR) > 3. Specification of the CBOR Encoding > 3.4. Tagging of Items > 3.4.3. Bignums
- Old locator: `xpath:/div/pre[16]#p141`
- New locator: `id:section-3.4.3-2|xpath:/body/div[7]/section/div[4]/section/div[4]/section/p[2]`
- Old text: Bignums are integers that do not fit into the basic integer representations provided by major types 0 and 1. They are encoded as a byte string data item, which is interpreted as an unsigned integer n in network byte order. For tag value 2, the value of the bignum is n. For tag value 3, the value of the bignum is -1 - n. Decoders that understand these tags MUST be able to decode bignums that have leading zeroes.
- New text: Bignums are encoded as a byte string data item, which is interpreted as an unsigned integer n in network byte order. Contained items of other types are invalid. For tag number 2, the value of the bignum is n. For tag number 3, the value of the bignum is -1 - n. The preferred serialization of the byte string is to leave out any leading zeroes (note that this means the preferred serialization for n = 0 is the empty byte string, but see below). Decoders that understand these tags MUST be able to decode bignums that do have leading zeroes. The preferred serialization of an integer that can be represented using major type 0 or 1 is to encode it this way instead of as a bignum (which means that the empty string never occurs in a bignum when using preferred serialization). Note that this means the non-preferred choice of a bignum representation instead of a basic integer for encoding a number is not intended to have application semantics (just as the choice of a longer basic integer representation than needed, such as 0x1800 for 0x00, does not).¶
- Reasons:
  - Condition introduced: 'when using preferred serialization)'.
- Alignment score components:
  - combined: `0.7426`
  - actor_action_similarity: `0.9247`
  - editorial_similarity: `0.4119`
  - modality_match: `1.0`
  - section_similarity: `0.125`
  - structural_proximity: `0.0`
  - text_similarity: `0.9014`
  - token_similarity: `0.5391`
- Evidence hashes:
  - `011e174795681a81bd676e150c45f8e5c0c896aa0d144f37513f5c4751a9f6e1`
  - `392ad809503e978ee2847a13ca99fe63ec7ca6f6a9525ce75841f1a6ff355b77`
  - `89b6582968fe4a15ec1c8309c8721abf872c51ba0750c66c0e900263ffe2e04b`
  - `cec256a9e2cd85f19943c5bf14824cd7e4537e467972c9e2094f027a36b78de4`
  - `f10dd319668f0da98eda80e01378584ddaddb22637e1c15f8b095fc920d9338d`

### `REMOVED` — `23f361e15b732c66`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `1901bad6e7fad750`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `66752d4f0a33ff78`

- Confidence: `0.95`
- Modality transition: `SHOULD_NOT->∅`
- Old requirement: `227d26fd37181df4`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `34738c4bc3933404`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `44d04188cd008ea5`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `6cd5f1c18b9f2ca1`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `539560845cf154a0`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `3f4fbc3862b8d3da`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `6853e5ef02355be5`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[20]#p186`
- Old text: This section discusses some considerations in creating CBOR-based protocols. It is advisory only and explicitly excludes any language from RFC 2119 other than words that could be interpreted as "MAY" in the sense of RFC 2119.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `d0a3cbaa9a8cc44d2710161325f4e3d8f6457c57b88a74e51333a9bf2ce812fc`
  - `d9b400b78aec3fded7befe4523b20ed4a4f93dee66d9ac23aa8230edc2b3abba`

### `REMOVED` — `ac9264b953dfae5a`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `7c5a0c7bd646b8e6`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `c257e82d8605f32b`

- Confidence: `0.95`
- Modality transition: `MUST_NOT->∅`
- Old requirement: `82ce6dcee0ce65e9`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `42e2ca10b8c278f0`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `9f47ccad824cac2b`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `c1527dbab8a3f494`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `b0f0b3aceb2dd7a3`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[12]#p111`
- Old text: Text strings with indefinite lengths act the same as byte strings with indefinite lengths, except that all their chunks MUST be definite-length text strings. Note that this implies that the bytes of a single UTF-8 character cannot be spread between chunks: a new chunk can only be started at a character boundary.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8d148f8f266f63469a2626804ab145c44a58f587802cd2bb7d579c8a0242d830`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `b59b0845a4edee87867ab807e50b4783067099ec03c32f835aa9f3169d8f440f`

### `REMOVED` — `3dd1632232cd2a6c`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `be3180449e7c8dfe`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `f6e9b9404927d627`

- Confidence: `0.95`
- Modality transition: `MUST_NOT->∅`
- Old requirement: `e95873ac212fc328`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `78f4c94f9e4fcc87`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `f49220c5cc2f56c6`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[5]#p44`
- Old text: The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119, BCP 14 [RFC2119] and indicate requirement levels for compliant CBOR implementations.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `8e6b785ba4f699b4e3bd1f6f4a47b3c258b900f1baa87c21170ba88b08c9efe0`
  - `98435e9a3e64a453c3c6707f1c5e78c72397d86f90f6942c81713b0795accc3c`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `1ef945b7fdea7bcd`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `fbad2bac9cb7a3a6`
- Old section: (pre-text)
- Old locator: `xpath:/div/pre[12]#p106`
- Old text: For indefinite-length byte strings, every data item (chunk) between the indefinite-length indicator and the "break" MUST be a definite- length byte string item; if the parser sees any item type other than a byte string before it sees the "break", it is an error.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `16e70f275b74e1ad92c181855a47e000add4d344e8a881b84966b26ace0e171b`
  - `974a4ea58b76dfabdd48f2e186aa2e6be95b09e778d0210b6faca52f58de17f1`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
