# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `308607b1b8f9b82a42b5312ead9eb20722b63ef9358e7c64ba11a958d550ace7`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `w3c-trace-context-1.html` | `sha256:9e7228d2a91c` | `9e7228d2a91c5aa4bef6e7f610366a2000274ee51699053e10c8ac3f0b8965be` | 100612 |
| new | `w3c-trace-context-2.html` | `sha256:eb6c25460036` | `eb6c2546003639d6884e8357d90c5dfde95c70494e6e1339ba2219bebb29be11` | 115810 |

### Provenance

- **old**: family=`w3c` adapter=`normshift.adapters.w3c`@1.0.0 type=`text/html`
  - local_path (portable): `w3c-trace-context-1.html`
- **new**: family=`w3c` adapter=`normshift.adapters.w3c`@1.0.0 type=`text/html`
  - local_path (portable): `w3c-trace-context-2.html`

## Summary

- Old requirements: **75**
- New requirements: **89**
- Changes: **114**

### Classification counts

- `ADDED`: 39
- `AMBIGUOUS`: 12
- `CONDITION_REMOVED`: 1
- `MOVED`: 37
- `REMOVED`: 25

## Changes

### `ADDED` — `850c234f263f9cb8`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `029c3508fdbd1a3b`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/ul[3]/li[2]`
- New text: If a component needs to make a recording decision - it SHOULD respect the sampled flag value. Security considerations SHOULD be applied to protect from abusive or malicious use of this flag.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `2524f60c94f7c44d96c31fbb7be4dcff27f5f475a96fe79f37601b4e39b8df23`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `8df1faf4ed2efa7aa81ed714963a06a68feddf6c63edaf11f497e7e96e8d1950`

### `ADDED` — `3b81efe2ed9ff875`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `141cb06d006b936c`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- New text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either at the end of the string or followed by a dash. If all three values were parsed successfully, the vendor should use them.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9291d517f8b1ecab38bb228b3d545c7608c33e865f0c1750196ea387f47bbf9c`
  - `9c14d40dae36f18cd53dbe7d3d0b63ea92011f9247289b6679d4a8d6cde809dd`

### `ADDED` — `c58a25a4629bbfde`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `17ef5eadb30979eb`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/ul[3]/li[2]`
- New text: If a component needs to make a recording decision - it SHOULD respect the sampled flag value. Security considerations SHOULD be applied to protect from abusive or malicious use of this flag.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `2524f60c94f7c44d96c31fbb7be4dcff27f5f475a96fe79f37601b4e39b8df23`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `8df1faf4ed2efa7aa81ed714963a06a68feddf6c63edaf11f497e7e96e8d1950`

### `ADDED` — `8b1451d6ef1482d3`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `186b912111bad9d7`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- New locator: `xpath:/body/section[5]/section[5]/ul/li[1]`
- New text: Add a new key/value pair. The new key/value pair SHOULD be added to the beginning of the list. Adding a key/value pair MUST NOT result in the same key being present multiple times.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `27fd1fba19f7219f2272d1e5b98959d20b635f8a66a6cdf2645176918ce29dd5`
  - `4825774e28b7dd0c93187ec34184ef02f5f0863f422a0c61a7cd2dfc08efc2ca`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `fd960ac0c9bfeb37`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `1b4186298285ff7f`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- New locator: `xpath:/body/section[5]/section[5]/p[1]`
- New text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys MUST be moved to the beginning (left) of the list.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `43f4f3e330f35dc4b521e1b44e22b0452d146ec7f88ad3d73d8a80464c5e34c1`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `b223e3d1aba74678f11212f115bd03c883d3a4b1cf3854ea903bf219dfc75fd8`

### `ADDED` — `c5aff9cecf39d73d`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `265d996b64cb3975`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header
- New locator: `xpath:/body/section[5]/section[3]/p[2]`
- New text: If the vendor failed to parse traceparent, it MUST NOT attempt to parse tracestate. Note that the opposite is not true: failure to parse tracestate MUST NOT affect the parsing of traceparent.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5adb443b09a36b664d2eddc0d99e161599e54b5dccada547fcc2df8844fe50f0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `eddd6551c294559b408fcb1a51e4496a2a46e28e4ff224642e87c85e9aeed7c5`

### `ADDED` — `ee9ce9a8d7261ec4`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `2d12837e1fe66438`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.3 trace-id
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[3]/p[2]`
- New text: The value of trace-id SHOULD be globally unique. One recommended method to ensure global uniqueness, as well as to address some privacy and security considerations, to a satisfactory degree of certainty is to randomly (or pseudo-randomly) generate the trace-id. Implementers SHOULD use a trace-id generation method which randomly (or pseudo-randomly) generates at least the right-most 7 bytes of the ID. If the right-most 7 bytes are randomly (or pseudo-randomly) generated, the corresponding random trace id flag SHOULD be set. For more details, see considerations for trace-id field generation.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `c0e81f5c1cee9cff73101d51861a19d89dd417c72c7a82da4428f0a67d99fb13`
  - `e361fc4595bf0e36b52065880e3c5fd85dc512490a1a3fc82a09f990e577b061`

### `ADDED` — `00428807e2ae6a01`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `32fe3aeb3df53552`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- New locator: `xpath:/body/section[5]/section[4]/p[1]`
- New text: A vendor receiving a request without a traceparent header SHOULD generate traceparent headers for outbound requests, effectively starting a new trace. A possible reason for not doing this could be a performance sensitive scenario when the vendor decides to not sample a request. Note that for most scenarios, vendors are expected to generate the header even when not sampling, to propagate the sampling decision downstream.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `b33a2debfa9073d1d49c708694c038c86199e04cf2f666201ba506f03febfd21`
  - `e17a8c7ea16f23f6e284e46fe8ee728116121471faf0f945ea4412a5b07d71eb`

### `ADDED` — `5698274b693553c5`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `469c3961c337e0b2`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[1]`
- New text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC9110 Section 5.3 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC9110. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC9110.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7cdbc2c684bfe85a725b8492c0b964d02b4416ed7831de8abc67125874562199`
  - `ef7ec2e849b3e20b87eee5c6ac64be286e32d77c298046da7e081aee67196bd1`

### `ADDED` — `e94f60edf05583f1`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `498e3e4334ad8331`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- New locator: `xpath:/body/section[5]/section[5]/p[1]`
- New text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys MUST be moved to the beginning (left) of the list.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `43f4f3e330f35dc4b521e1b44e22b0452d146ec7f88ad3d73d8a80464c5e34c1`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `b223e3d1aba74678f11212f115bd03c883d3a4b1cf3854ea903bf219dfc75fd8`

### `ADDED` — `bd194db79649ce17`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `4eb9c3254b78bf4d`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[1]`
- New text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC9110 Section 5.3 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC9110. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC9110.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7cdbc2c684bfe85a725b8492c0b964d02b4416ed7831de8abc67125874562199`
  - `ef7ec2e849b3e20b87eee5c6ac64be286e32d77c298046da7e081aee67196bd1`

### `ADDED` — `efc13c395caf4b21`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `5c57187a87fde9cf`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[1]`
- New text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC9110 Section 5.3 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC9110. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC9110.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7cdbc2c684bfe85a725b8492c0b964d02b4416ed7831de8abc67125874562199`
  - `ef7ec2e849b3e20b87eee5c6ac64be286e32d77c298046da7e081aee67196bd1`

### `ADDED` — `433e7ed6fa29e0fe`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `6d6c0407abb545fe`
- New section: Trace Context Level 2 > 6. Privacy Considerations > 6.1 Privacy of traceparent field
- New locator: `xpath:/body/section[8]/section[1]/p[1]`
- New text: The traceparent field MUST NOT contain any personally identifiable information. One way to achieve this is to randomly generate all trace IDs using a random number generator that does not expose any personally identifiable information. Any random number generator used for generating trace IDs MUST NOT rely on any information as input or seed state that can potentially be personally identifiable.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `61697c1ef1724d127485e37dbea123199e5e2c794da31c97e5146444d5ae8062`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `af3b7980dbad0f4eae22a9f52a3f08321f288de4864ae7566cdd994f177d508b`

### `ADDED` — `068cf9bcb51f7a79`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `6fe53da4eda164e2`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.2 Random Trace ID Flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[2]/ul[2]/li[2]`
- New text: If the flag is unset in the incoming traceparent header, it MUST also be unset in any outgoing traceparent headers which use the same trace-id.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `be51fb67be109d8e20b4e392d7406cee6d7933ae89ad13b5487a1b5b264a2989`
  - `e889270c9de435d7583807940c2a341f4d9a0b5a17e37f2f58d61cd07fb16caf`

### `ADDED` — `c9400adf07ddbdf3`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `75189dd1cb124e7a`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.2 Random Trace ID Flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[2]/ul[1]/li[2]`
- New text: If the flag is not set, the trace-id MAY still be randomly (or pseudo-randomly) generated.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `4b821a91096d9b45d39363bfd8a72fb598970e1a56516e4dd1a73d5bb54de86a`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `b78a230679764d9aecb03b7b51cac21d38d820fe14aa9f5ec240c5a78d0e05d5`

### `ADDED` — `a994a809bcc070b3`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `79d4ba58ccda0305`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.2 Random Trace ID Flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[2]/ul[1]/li[4]`
- New text: When at least the right-most 7 bytes of the trace-id are randomly (or pseudo-randomly) generated, the random-trace-id flag SHOULD be set to 1.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `08b23a495551ff7eafbc4dd6131c155b2488379dc3cc8a2b5e7ed65733cb6786`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9768bf1b2510d3d22953a8dbb962edd109823102248cd3e36c273e7bb93858bb`

### `ADDED` — `81e6e72bc5934002`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `7e2b84c14ba2999d`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.2 Random Trace ID Flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[2]/ul[1]/li[1]`
- New text: If that flag is set, at least the right-most 7 bytes of the trace-id MUST be selected randomly (or pseudo-randomly) with uniform distribution over the interval [0..2^56-1].
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `930ef526114f3e79f1ca98faa279ec055905b9d46c316898ff42e9e4f19ebbc9`
  - `b31f53683b41584abe4e1bf86caafdadc33c6eee019461af7efd2c8ddfe613ac`

### `ADDED` — `4f49d95ee119174b`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `83d8d92dfc6106f0`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.3 Combined Header Value > 3.3.3.1 tracestate Limits:
- New locator: `xpath:/body/section[5]/section[3]/section[3]/section/p[2]`
- New text: There are systems where propagating of 512 characters of tracestate may be expensive. In this case, the maximum size of the propagated tracestate header SHOULD be documented and explained. The cost of propagating tracestate SHOULD be weighted against the value of monitoring scenarios enabled for the end users.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `05c786b77b3e1653b4cfa40138668ad43f572e4cdf6de8f45c2f519d86fe5547`
  - `6997c2a5c4dca1bf75a08b3d89267ece4d7e219a6f194d5d3fc5c54c5de42f98`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `f7837493244a43b5`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `8fbe118f8798fcde`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- New locator: `xpath:/body/section[5]/section[4]/ul/li[3]`
- New text: Restart trace: All properties (trace-id, parent-id, trace-flags) are regenerated. This mutation is used in services that are defined as a front gate into secure networks and eliminates a potential denial-of-service attack surface. Vendors SHOULD clean up tracestate collection on traceparent restart. There are rare cases when the original tracestate entries must be preserved after a restart. This typically happens when the trace-id is reverted back at some point of the trace flow, for instance, when it leaves the secure network. However, it SHOULD be an explicit decision, and not the default behavior.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `0379f62039ce1ba0999ad0b365d56b2216c02e278912f359525af1ba4ee6903b`
  - `678890fe2c18c22630623ccaf929d0faedd6399156c0546f57c4ed4c0c052b95`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `054298c0c6e20409`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `a3a94f89eeb142e6`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- New locator: `xpath:/body/section[5]/section[4]/ul/li[3]`
- New text: Restart trace: All properties (trace-id, parent-id, trace-flags) are regenerated. This mutation is used in services that are defined as a front gate into secure networks and eliminates a potential denial-of-service attack surface. Vendors SHOULD clean up tracestate collection on traceparent restart. There are rare cases when the original tracestate entries must be preserved after a restart. This typically happens when the trace-id is reverted back at some point of the trace flow, for instance, when it leaves the secure network. However, it SHOULD be an explicit decision, and not the default behavior.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `0379f62039ce1ba0999ad0b365d56b2216c02e278912f359525af1ba4ee6903b`
  - `678890fe2c18c22630623ccaf929d0faedd6399156c0546f57c4ed4c0c052b95`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `2028fc633389ec34`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `a8aef688fb018da4`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values > 3.3.2.2 list-members > 3.3.2.2.2 Value
- New locator: `xpath:/body/section[5]/section[3]/section[2]/section[2]/section[2]/p`
- New text: The value is an opaque string containing up to 256 printable ASCII [RFC0020] characters (i.e., the range 0x20 to 0x7E) except comma (,) and (=). The string must end with a character which is not a space (0x20). Note that this also excludes tabs, newlines, carriage returns, etc. All leading spaces MUST be preserved as part of the value. All trailing spaces are considered to be optional whitespace characters not part of the value. Optional trailing whitespace MAY be excluded when propagating the header.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `d523f3eea0fb99ca403c5712789bde3f8f8a491481f4ce38291c75a5b9c9d213`
  - `fcc5cfcad684077413882cdcd34397de47a42ac0fd533d65bcebfa2f65e50fda`

### `ADDED` — `fcc918a8b4f63b6d`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `b4197d8c8868eda8`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.3 trace-id
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[3]/p[2]`
- New text: The value of trace-id SHOULD be globally unique. One recommended method to ensure global uniqueness, as well as to address some privacy and security considerations, to a satisfactory degree of certainty is to randomly (or pseudo-randomly) generate the trace-id. Implementers SHOULD use a trace-id generation method which randomly (or pseudo-randomly) generates at least the right-most 7 bytes of the ID. If the right-most 7 bytes are randomly (or pseudo-randomly) generated, the corresponding random trace id flag SHOULD be set. For more details, see considerations for trace-id field generation.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `c0e81f5c1cee9cff73101d51861a19d89dd417c72c7a82da4428f0a67d99fb13`
  - `e361fc4595bf0e36b52065880e3c5fd85dc512490a1a3fc82a09f990e577b061`

### `ADDED` — `84f52fcf2b3f7943`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `b9e548ab3b8e4650`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.3 trace-id
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[3]/p[2]`
- New text: The value of trace-id SHOULD be globally unique. One recommended method to ensure global uniqueness, as well as to address some privacy and security considerations, to a satisfactory degree of certainty is to randomly (or pseudo-randomly) generate the trace-id. Implementers SHOULD use a trace-id generation method which randomly (or pseudo-randomly) generates at least the right-most 7 bytes of the ID. If the right-most 7 bytes are randomly (or pseudo-randomly) generated, the corresponding random trace id flag SHOULD be set. For more details, see considerations for trace-id field generation.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `c0e81f5c1cee9cff73101d51861a19d89dd417c72c7a82da4428f0a67d99fb13`
  - `e361fc4595bf0e36b52065880e3c5fd85dc512490a1a3fc82a09f990e577b061`

### `ADDED` — `9bb2dd1834c7ac3f`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `c5d9afd968bb865d`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- New text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either at the end of the string or followed by a dash. If all three values were parsed successfully, the vendor should use them.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9291d517f8b1ecab38bb228b3d545c7608c33e865f0c1750196ea387f47bbf9c`
  - `9c14d40dae36f18cd53dbe7d3d0b63ea92011f9247289b6679d4a8d6cde809dd`

### `ADDED` — `1d9179e4aa947130`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `cbde858c68f10181`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header
- New locator: `xpath:/body/section[5]/section[3]/p[3]`
- New text: The tracestate HTTP header MUST NOT be used for any properties that are not defined by a tracing system. [BAGGAGE] MAY be used for defining and propagating such application level properties.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `50798971a7c28defb05ec4f7cc74124cbd78d104adfa8ffd9e263b078f5204b8`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `cfc41f2f0c7f97691fda409827a55dee9f3ba10e3628b6f115095f60b0ca2931`

### `ADDED` — `27744e2b3cd5a060`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `cc32ac5d2e357764`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.3 Combined Header Value > 3.3.3.1 tracestate Limits:
- New locator: `xpath:/body/section[5]/section[3]/section[3]/section/p[3]`
- New text: In a situation where tracestate is truncated due to the total size of the header value, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Other truncation strategies like safe list entries, blocked list entries, or size-based truncation SHOULD NOT be used.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `a1909ec03808c690da1a174888eae94ee1974d0da8f2aed22d94379474e21e2b`
  - `a610abf3336813ee4e2e23c264149c448bd45b3af9eda98cd6fa900cf8429e45`

### `ADDED` — `b486d9f4dd634c57`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `cc595f7621884ce8`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.3 Combined Header Value > 3.3.3.1 tracestate Limits:
- New locator: `xpath:/body/section[5]/section[3]/section[3]/section/p[3]`
- New text: In a situation where tracestate is truncated due to the total size of the header value, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Other truncation strategies like safe list entries, blocked list entries, or size-based truncation SHOULD NOT be used.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `a1909ec03808c690da1a174888eae94ee1974d0da8f2aed22d94379474e21e2b`
  - `a610abf3336813ee4e2e23c264149c448bd45b3af9eda98cd6fa900cf8429e45`

### `ADDED` — `e1c47ff3a104099d`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD_NOT`
- New requirement: `ce12bdfc65569a00`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.3 Combined Header Value > 3.3.3.1 tracestate Limits:
- New locator: `xpath:/body/section[5]/section[3]/section[3]/section/p[3]`
- New text: In a situation where tracestate is truncated due to the total size of the header value, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Other truncation strategies like safe list entries, blocked list entries, or size-based truncation SHOULD NOT be used.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `a1909ec03808c690da1a174888eae94ee1974d0da8f2aed22d94379474e21e2b`
  - `a610abf3336813ee4e2e23c264149c448bd45b3af9eda98cd6fa900cf8429e45`

### `ADDED` — `36273069e92b7291`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `d10e3e02abe408dc`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- New locator: `xpath:/body/section[5]/section[5]/p[1]`
- New text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys MUST be moved to the beginning (left) of the list.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `43f4f3e330f35dc4b521e1b44e22b0452d146ec7f88ad3d73d8a80464c5e34c1`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `b223e3d1aba74678f11212f115bd03c883d3a4b1cf3854ea903bf219dfc75fd8`

### `ADDED` — `04cb0aa7d7827f2e`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `d2d6562fd6d40efc`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header
- New locator: `xpath:/body/section[5]/section[3]/p[2]`
- New text: If the vendor failed to parse traceparent, it MUST NOT attempt to parse tracestate. Note that the opposite is not true: failure to parse tracestate MUST NOT affect the parsing of traceparent.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5adb443b09a36b664d2eddc0d99e161599e54b5dccada547fcc2df8844fe50f0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `eddd6551c294559b408fcb1a51e4496a2a46e28e4ff224642e87c85e9aeed7c5`

### `ADDED` — `24fcc7fc30837933`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `d92f1122bf96bf80`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values > 3.3.2.2 list-members > 3.3.2.2.2 Value
- New locator: `xpath:/body/section[5]/section[3]/section[2]/section[2]/section[2]/p`
- New text: The value is an opaque string containing up to 256 printable ASCII [RFC0020] characters (i.e., the range 0x20 to 0x7E) except comma (,) and (=). The string must end with a character which is not a space (0x20). Note that this also excludes tabs, newlines, carriage returns, etc. All leading spaces MUST be preserved as part of the value. All trailing spaces are considered to be optional whitespace characters not part of the value. Optional trailing whitespace MAY be excluded when propagating the header.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `d523f3eea0fb99ca403c5712789bde3f8f8a491481f4ce38291c75a5b9c9d213`
  - `fcc5cfcad684077413882cdcd34397de47a42ac0fd533d65bcebfa2f65e50fda`

### `ADDED` — `3425c79b836ea702`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `d9ecdbb6db9f3984`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[1]`
- New text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC9110 Section 5.3 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC9110. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC9110.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7cdbc2c684bfe85a725b8492c0b964d02b4416ed7831de8abc67125874562199`
  - `ef7ec2e849b3e20b87eee5c6ac64be286e32d77c298046da7e081aee67196bd1`

### `ADDED` — `9efe499f8f6cbb97`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `dbf63a93d9addf7b`
- New section: Trace Context Level 2 > 2. Overview > 2.3 Design Overview
- New locator: `xpath:/body/section[4]/section[3]/ul[2]/li[2]`
- New text: In addition they MAY also choose to participate in a trace by modifying the traceparent header and relevant parts of the tracestate header containing their proprietary information. This is also referred to as participating in a trace.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `3c84299ea0f4d523a85f3f9a3d60c1d14750ac71ae7e7e63716f2910342b05e4`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9496cf1fc21c720c844fe3d8f96affcec397f9c1f962d5bc136857f8d1fecb0c`

### `ADDED` — `7287d9ffda3ce374`

- Confidence: `0.95`
- Modality transition: `∅->SHOULD`
- New requirement: `de163dbb7e74437f`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.3 Combined Header Value > 3.3.3.1 tracestate Limits:
- New locator: `xpath:/body/section[5]/section[3]/section[3]/section/p[2]`
- New text: There are systems where propagating of 512 characters of tracestate may be expensive. In this case, the maximum size of the propagated tracestate header SHOULD be documented and explained. The cost of propagating tracestate SHOULD be weighted against the value of monitoring scenarios enabled for the end users.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `05c786b77b3e1653b4cfa40138668ad43f572e4cdf6de8f45c2f519d86fe5547`
  - `6997c2a5c4dca1bf75a08b3d89267ece4d7e219a6f194d5d3fc5c54c5de42f98`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `d5c45e0d2ac4703d`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `e23d5bd2e0cb1a42`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.2 Random Trace ID Flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[2]/ul[2]/li[1]`
- New text: If the flag is set in the incoming traceparent header, it MUST also be set in all outgoing traceparent headers which use the same trace-id.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `1794e1f3b737be18d14ba6678b688b8776a0ed2b6615712aa3e174a188d11bd6`
  - `6ced6c1b7c6f280827e1902953336db9d1fc2c21bcd3b11bd5e6f599c991b45e`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `f981ccd9895dffcf`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `e4c09b229f1b254e`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.2 Random Trace ID Flag
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[2]/ul[1]/li[3]`
- New text: When unset, the trace-id MAY be generated in any way that satisfies the requirements of the trace ID format.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `148abffb6c4711e1566d5e768ac5ae33aef22c59f0c9d03204146018290747e7`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9dd7a77bf6273811d8bc0d491712fd75fa10a40c09a5ef17e05202d43c6e885d`

### `ADDED` — `e0e8945b83e019d4`

- Confidence: `0.95`
- Modality transition: `∅->MAY`
- New requirement: `ef774150e121dd92`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- New locator: `xpath:/body/section[5]/section[5]/ul/li[3]`
- New text: Delete a key/value pair. Any key/value pair MAY be deleted. Vendors SHOULD NOT delete keys that were not generated by them. The deletion of an unknown key/value pair will break correlation in other systems. This mutation enables three scenarios. The first is that proxies can block certain tracestate keys for privacy and security concerns. The second scenario is a truncation of long tracestates. Finally, vendors MAY also discard duplicate keys that were not generated by them.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `58c776ce3d60af4bac8f2865db8788f414ab03616c441a5b6805eb7052301746`
  - `6302df120d5bd370e02bdbc749bbf40613038421eeb9e7d37efe868fe63e73a0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`

### `ADDED` — `2e1db91fbdc50419`

- Confidence: `0.95`
- Modality transition: `∅->MUST_NOT`
- New requirement: `f2ce9a6e11aeab2e`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header
- New locator: `xpath:/body/section[5]/section[3]/p[3]`
- New text: The tracestate HTTP header MUST NOT be used for any properties that are not defined by a tracing system. [BAGGAGE] MAY be used for defining and propagating such application level properties.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `50798971a7c28defb05ec4f7cc74124cbd78d104adfa8ffd9e263b078f5204b8`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `cfc41f2f0c7f97691fda409827a55dee9f3ba10e3628b6f115095f60b0ca2931`

### `ADDED` — `d30b0a556508d2ec`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `fe089368ff8e7009`
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- New text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either at the end of the string or followed by a dash. If all three values were parsed successfully, the vendor should use them.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9291d517f8b1ecab38bb228b3d545c7608c33e865f0c1750196ea387f47bbf9c`
  - `9c14d40dae36f18cd53dbe7d3d0b63ea92011f9247289b6679d4a8d6cde809dd`

### `AMBIGUOUS` — `74396afacae5f152`

- Confidence: `0.55`
- Modality transition: `SHOULD_NOT->SHOULD_NOT`
- Old requirement: `0b368eaee5a329f9`
- New requirement: `832ad0a2d2f8aebb`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/ul/li[3]`
- New locator: `xpath:/body/section[5]/section[5]/ul/li[3]`
- Old text: Delete a key/value pair. Any key/value pair MAY be deleted. Vendors SHOULD NOT delete keys that were not generated by them. The deletion of an unknown key/value pair will break correlation in other systems. This mutation enables two scenarios. The first is that proxies can block certain tracestate keys for privacy and security concerns. The second scenario is a truncation of long tracestates.
- New text: Delete a key/value pair. Any key/value pair MAY be deleted. Vendors SHOULD NOT delete keys that were not generated by them. The deletion of an unknown key/value pair will break correlation in other systems. This mutation enables three scenarios. The first is that proxies can block certain tracestate keys for privacy and security concerns. The second scenario is a truncation of long tracestates. Finally, vendors MAY also discard duplicate keys that were not generated by them.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9512`
  - actor_action_similarity: `0.9791`
  - editorial_similarity: `0.8998`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `0.9942`
  - token_similarity: `0.8947`
- Evidence hashes:
  - `4a89012a439f1dc9854483421f618e6b335536045a0a0a74ee2d02d3ff93ffbc`
  - `4bb618b56fb46b608f20f92df70fb540471c5c9fc35093d7ffe65985ccb3370b`
  - `58c776ce3d60af4bac8f2865db8788f414ab03616c441a5b6805eb7052301746`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `6302df120d5bd370e02bdbc749bbf40613038421eeb9e7d37efe868fe63e73a0`

### `AMBIGUOUS` — `10d65d8a1a178983`

- Confidence: `0.55`
- Modality transition: `MUST->MUST`
- Old requirement: `141f9c7f4b8a2b73`
- New requirement: `1aa41b8bcc0caebf`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.3 list-members > 3.3.1.3.1 Key
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values > 3.3.2.2 list-members > 3.3.2.2.1 Key
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[3]/section[1]/p[2]`
- New locator: `xpath:/body/section[5]/section[3]/section[2]/section[2]/section[1]/p[2]`
- Old text: Note: Identifiers MUST begin with a lowercase letter or a digit, and can only contain lowercase letters (a-z), digits (0-9), underscores (_), dashes (-), asterisks (*), and forward slashes (/).
- New text: A key MUST begin with a lowercase letter or a digit and contain up to 256 characters including lowercase letters (a-z), digits (0-9), underscores (_), dashes (-), asterisks (*), forward slashes (/), and at signs (@).
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.8798`
  - actor_action_similarity: `0.9301`
  - editorial_similarity: `0.8098`
  - modality_match: `1.0`
  - section_similarity: `0.9655`
  - structural_proximity: `0.4`
  - text_similarity: `0.8762`
  - token_similarity: `0.8215`
- Evidence hashes:
  - `1a687515ab820ee576eaca157924c66006ed035759a0214e26ca3dee4e00fc30`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `717f1972ae044c4d609812de0e5c7f734ece61a4e57a219631e37e46b8a632b3`
  - `9bcab12e6bdf6db976ad31691a7e59c8e40bcb7be119b2d0d64dac90f0a7f1b7`
  - `d0b23382dfd353c6f17145279151421543124564b7424a77fb5c223f30c5bb09`

### `AMBIGUOUS` — `40db84e74d766186`

- Confidence: `0.55`
- Modality transition: `MUST->MUST`
- Old requirement: `21c5a22174d02bf6`
- New requirement: `7c8abde670e241aa`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.5 tracestate Limits:
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.3 Combined Header Value > 3.3.3.1 tracestate Limits:
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[5]/p[3]`
- New locator: `xpath:/body/section[5]/section[3]/section[3]/section/p[3]`
- Old text: In a situation where tracestate needs to be truncated due to size limitations, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Note that other truncation strategies like safe list entries, blocked list entries, or size-based truncation MAY be used, but are highly discouraged. Those strategies decrease the interoperability of various tracing vendors.
- New text: In a situation where tracestate is truncated due to the total size of the header value, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Other truncation strategies like safe list entries, blocked list entries, or size-based truncation SHOULD NOT be used.
- Reasons:
  - Condition text changed; insufficient specificity → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9122`
  - actor_action_similarity: `0.9558`
  - editorial_similarity: `0.8129`
  - modality_match: `1.0`
  - section_similarity: `0.9606`
  - structural_proximity: `0.5`
  - text_similarity: `0.9331`
  - token_similarity: `0.8304`
- Evidence hashes:
  - `0061aeb33d51d724c2296beff726298a8311d1d1ceb763cf03ed61c7c416f188`
  - `1429050b414a67c4f13e6b2af8a0186a56d56352619c888e2314b5a7a75e21a2`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `a1909ec03808c690da1a174888eae94ee1974d0da8f2aed22d94379474e21e2b`
  - `a610abf3336813ee4e2e23c264149c448bd45b3af9eda98cd6fa900cf8429e45`

### `AMBIGUOUS` — `78f72e34969c1e96`

- Confidence: `0.45`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `2e5ae3e48aaf2398`
- New requirement: `8d84c9fcdc842158`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.1 Header Name
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.1 Header Name
- Old locator: `xpath:/body/section[5]/section[2]/section[1]/p[3]`
- New locator: `xpath:/body/section[5]/section[2]/section[1]/p[3]`
- Old text: Vendors MUST expect the header name in any case (upper, lower, mixed), and SHOULD send the header name in lowercase.
- New text: In order to increase interoperability across multiple protocols and encourage successful integration, tracing systems SHOULD encode the header name as ASCII lowercase.
- Reasons:
  - Insufficient evidence for a confident classification → AMBIGUOUS.
- Alignment score components:
  - combined: `0.7222`
  - actor_action_similarity: `0.8621`
  - editorial_similarity: `0.5382`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.85`
  - text_similarity: `0.5522`
  - token_similarity: `0.53`
- Evidence hashes:
  - `5aa55eb47af4179f28c619cd009648599fd7a900663e30cc5ea9b519997389bd`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `92fc168886b1b3999eaa1ef36523983a5f4af124256091314935850fdf20f40e`
  - `984bcfee842b30946d6281e0f696f642b11994966c59c28a9338c52604f00463`
  - `e323c5b7a3feb1c5c77854081c81aeb447a85568aa45c1dff905400836e84622`

### `AMBIGUOUS` — `d08caa4e17db38df`

- Confidence: `0.55`
- Modality transition: `MUST->MUST`
- Old requirement: `3978b37ce79be3cf`
- New requirement: `108c15ab7891c44d`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[1]`
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[1]`
- Old text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC7230 Section 3.2.2 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC7230. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC7230.
- New text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC9110 Section 5.3 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC9110. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC9110.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9435`
  - actor_action_similarity: `0.945`
  - editorial_similarity: `0.9779`
  - modality_match: `1.0`
  - section_similarity: `0.9635`
  - structural_proximity: `0.4`
  - text_similarity: `0.9718`
  - token_similarity: `0.9783`
- Evidence hashes:
  - `1e671a1c09d576a42416fb624bf020d55ada4a3192c6af58c9256ed90382599f`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `7216f0edf619d7f02aa8f90c954f192a2f501d90d0484da9a6ac7c8521407e37`
  - `7cdbc2c684bfe85a725b8492c0b964d02b4416ed7831de8abc67125874562199`
  - `ef7ec2e849b3e20b87eee5c6ac64be286e32d77c298046da7e081aee67196bd1`

### `AMBIGUOUS` — `8bd11ffca1547ed6`

- Confidence: `0.45`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `3b88e44651b34313`
- New requirement: `bef645b721c413ab`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/p[3]`
- New locator: `xpath:/body/section[5]/section[3]/section[1]/p[3]`
- Old text: Vendors MUST expect the header name in any case (upper, lower, mixed), and SHOULD send the header name in lowercase.
- New text: In order to increase interoperability across multiple protocols and encourage successful integration, tracing systems SHOULD encode the header name as ASCII lowercase.
- Reasons:
  - Insufficient evidence for a confident classification → AMBIGUOUS.
- Alignment score components:
  - combined: `0.6997`
  - actor_action_similarity: `0.8621`
  - editorial_similarity: `0.5382`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.4`
  - text_similarity: `0.5522`
  - token_similarity: `0.53`
- Evidence hashes:
  - `2a5b6d4c39d1ad1a4875728e6cf6e9b48cd5d47fe1ff912d3eeaa5fb6aafc8bc`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `92fc168886b1b3999eaa1ef36523983a5f4af124256091314935850fdf20f40e`
  - `984bcfee842b30946d6281e0f696f642b11994966c59c28a9338c52604f00463`
  - `dfc538765aa1766c9778756c99a61218a5fdf4a4965d582ccd556397fa81e74e`

### `AMBIGUOUS` — `918bfad8a59c50cc`

- Confidence: `0.55`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `3d1ebd0c62e44017`
- New requirement: `7d2c6fe4cba37243`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- Old text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either the end of the string or a dash. If all three values were parsed successfully, the vendor should use them.
- New text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either at the end of the string or followed by a dash. If all three values were parsed successfully, the vendor should use them.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9711`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9902`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `0.9905`
- Evidence hashes:
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `9291d517f8b1ecab38bb228b3d545c7608c33e865f0c1750196ea387f47bbf9c`
  - `9c14d40dae36f18cd53dbe7d3d0b63ea92011f9247289b6679d4a8d6cde809dd`
  - `a29da8069a7d1da149f91b08d81077795ad94d6099e2d544ec1caa9b0d52daf5`
  - `aa23c8ea35e31aaac0255c5fd6b92ec774c1c1902ea0a5180d1d813a91aa2ed3`

### `AMBIGUOUS` — `2e2e058805361855`

- Confidence: `0.55`
- Modality transition: `MAY->MAY`
- Old requirement: `5402e09a7af9191f`
- New requirement: `387fa76e97d54a15`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/p[1]`
- New locator: `xpath:/body/section[5]/section[5]/p[1]`
- Old text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys SHOULD be moved to the beginning (left) of the list.
- New text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys MUST be moved to the beginning (left) of the list.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9664`
  - actor_action_similarity: `0.9787`
  - editorial_similarity: `0.9867`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `0.9805`
- Evidence hashes:
  - `43f4f3e330f35dc4b521e1b44e22b0452d146ec7f88ad3d73d8a80464c5e34c1`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `a8cbd51eb45d9ee5157232bfb8fd5f2b7e2895ab3368de56ef46f03c2f66b8df`
  - `b223e3d1aba74678f11212f115bd03c883d3a4b1cf3854ea903bf219dfc75fd8`
  - `ccf1f3e4e71116e174bfd28485e9550d3f874ceed1bab4144b1ec3757f0aaebe`

### `AMBIGUOUS` — `ef6b8dd5b2868729`

- Confidence: `0.55`
- Modality transition: `MAY->MAY`
- Old requirement: `5c85a5d054ced453`
- New requirement: `85cf949a7e117c75`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/ul/li[3]`
- New locator: `xpath:/body/section[5]/section[5]/ul/li[3]`
- Old text: Delete a key/value pair. Any key/value pair MAY be deleted. Vendors SHOULD NOT delete keys that were not generated by them. The deletion of an unknown key/value pair will break correlation in other systems. This mutation enables two scenarios. The first is that proxies can block certain tracestate keys for privacy and security concerns. The second scenario is a truncation of long tracestates.
- New text: Delete a key/value pair. Any key/value pair MAY be deleted. Vendors SHOULD NOT delete keys that were not generated by them. The deletion of an unknown key/value pair will break correlation in other systems. This mutation enables three scenarios. The first is that proxies can block certain tracestate keys for privacy and security concerns. The second scenario is a truncation of long tracestates. Finally, vendors MAY also discard duplicate keys that were not generated by them.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9528`
  - actor_action_similarity: `0.9896`
  - editorial_similarity: `0.8998`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `0.9942`
  - token_similarity: `0.8947`
- Evidence hashes:
  - `4a89012a439f1dc9854483421f618e6b335536045a0a0a74ee2d02d3ff93ffbc`
  - `4bb618b56fb46b608f20f92df70fb540471c5c9fc35093d7ffe65985ccb3370b`
  - `58c776ce3d60af4bac8f2865db8788f414ab03616c441a5b6805eb7052301746`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `6302df120d5bd370e02bdbc749bbf40613038421eeb9e7d37efe868fe63e73a0`

### `AMBIGUOUS` — `fb3fe25eb20cab41`

- Confidence: `0.55`
- Modality transition: `MUST->MUST`
- Old requirement: `7809f5ec54a4b5a2`
- New requirement: `15be968e39500ef6`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/ul/li[4]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/ul/li[4]`
- Old text: Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either the end of the string or a dash.
- New text: Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either at the end of the string or followed by a dash.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9654`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9515`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `0.9527`
- Evidence hashes:
  - `0148b143f1524cbee1064eeced65f52e2e3f6e94cf88b71f70b107fa155be80e`
  - `13ed51ff95cd7215a1cab4c0952efb9d88b0ef8095458ab12b744aaa3bdbb2cd`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `d9458c4d28349b19e39231d15f60523d295020e042d0872ddc6dd07d061c6beb`
  - `e2746b48f30ecdbce500cad5d7d21986e47d4d5a8089af82c36e7f50b0509c5c`

### `AMBIGUOUS` — `0d6a3188eef4d842`

- Confidence: `0.55`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `c1c57653e1c4e234`
- New requirement: `bd269e0748c82185`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/ul/li[1]`
- New locator: `xpath:/body/section[5]/section[5]/ul/li[1]`
- Old text: Add a new key/value pair. The new key/value pair SHOULD be added to the beginning of the list.
- New text: Add a new key/value pair. The new key/value pair SHOULD be added to the beginning of the list. Adding a key/value pair MUST NOT result in the same key being present multiple times.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9131`
  - actor_action_similarity: `0.918`
  - editorial_similarity: `0.684`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `0.6861`
- Evidence hashes:
  - `27fd1fba19f7219f2272d1e5b98959d20b635f8a66a6cdf2645176918ce29dd5`
  - `28cedc9d66934ee3a653cdca49d2d0c9b1d2bd086ee38509d0390d2a4f37871a`
  - `4825774e28b7dd0c93187ec34184ef02f5f0863f422a0c61a7cd2dfc08efc2ca`
  - `4ac428e984d2dd76f88d26358145394566cda2395e7e7f575a082b2e9cdec824`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`

### `AMBIGUOUS` — `173449baaf8e5783`

- Confidence: `0.55`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `e781e39319ff0de4`
- New requirement: `47adb3e2e3a48f48`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[1]`
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[1]`
- Old text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC7230 Section 3.2.2 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC7230. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC7230.
- New text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC9110 Section 5.3 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC9110. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC9110.
- Reasons:
  - Aligned with residual non-editorial text differences; insufficient evidence for a substantive class → AMBIGUOUS.
- Alignment score components:
  - combined: `0.9518`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9779`
  - modality_match: `1.0`
  - section_similarity: `0.9635`
  - structural_proximity: `0.4`
  - text_similarity: `0.9718`
  - token_similarity: `0.9783`
- Evidence hashes:
  - `1e671a1c09d576a42416fb624bf020d55ada4a3192c6af58c9256ed90382599f`
  - `5cd7501a75ccc821d3a72744273b007c6440da648360630b29dba17044a45696`
  - `7216f0edf619d7f02aa8f90c954f192a2f501d90d0484da9a6ac7c8521407e37`
  - `7cdbc2c684bfe85a725b8492c0b964d02b4416ed7831de8abc67125874562199`
  - `ef7ec2e849b3e20b87eee5c6ac64be286e32d77c298046da7e081aee67196bd1`

### `CONDITION_REMOVED` — `cef6ef721526ef88`

- Confidence: `0.88`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `626b401967394aa6`
- New requirement: `4bdac18d273978c5`
- Old section: Trace Context > 6. Privacy Considerations > 6.1 Privacy of traceparent field
- New section: Trace Context Level 2 > 6. Privacy Considerations > 6.1 Privacy of traceparent field
- Old locator: `xpath:/body/section[8]/section[1]/p[1]`
- New locator: `xpath:/body/section[8]/section[1]/p[1]`
- Old text: The traceparent field is comprised of randomly-generated numbers. If a random number generator leverages any user identifiable information like IP address as seed state, this information may be exposed. Random number generators MUST NOT rely on any information that can potentially be user-identifiable.
- New text: The traceparent field MUST NOT contain any personally identifiable information. One way to achieve this is to randomly generate all trace IDs using a random number generator that does not expose any personally identifiable information. Any random number generator used for generating trace IDs MUST NOT rely on any information as input or seed state that can potentially be personally identifiable.
- Reasons:
  - Condition removed: 'If a random number generator leverages any user identifiable information like IP address as seed state, this information may be exposed'.
- Alignment score components:
  - combined: `0.7949`
  - actor_action_similarity: `0.8393`
  - editorial_similarity: `0.6311`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `0.741`
  - token_similarity: `0.6676`
- Evidence hashes:
  - `61697c1ef1724d127485e37dbea123199e5e2c794da31c97e5146444d5ae8062`
  - `9eb1bf3542180357d62d7349c12064d0a6d2d25bb06897618caaad6bf99ea3a6`
  - `acdea1733000ff3b9ee414d472b113ea5d0ccfb68416f91ebb89354ca102e226`
  - `af3b7980dbad0f4eae22a9f52a3f08321f288de4864ae7566cdd994f177d508b`
  - `e59ef7bc9224800c4aca818fa9d402d481a84f91f04b49492c7f094ec80d0108`

### `MOVED` — `255466c2549a177c`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `0938d4d538a14d5a`
- New requirement: `9a5c29908f1fff7e`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.4 Mutating the traceparent Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- Old locator: `xpath:/body/section[5]/section[4]/p[1]`
- New locator: `xpath:/body/section[5]/section[4]/p[2]`
- Old text: A vendor receiving a traceparent request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing it to outgoing requests.
- New text: A vendor receiving a traceparent request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing it to outgoing requests.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `7681230d221fc5018675e267f7c376ad7b8004a8166e20a8b7412d974a2a8ab9`
  - `abbf8f90bf21454e65b0594afe5366bbaf31f366c58250ac4b5b98fdc24de6a4`
  - `c3540fb7e9f6adc672584712481001ba1fdbb2b4baabf443281681e97385a8f2`
  - `fc8d25edee02e6a3cee69b370c98cb007ca3b387bd6179f6533526f22bdf6e42`

### `MOVED` — `a52931b97b875608`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `0d75a207fcfc69c9`
- New requirement: `0c6977234d0cd1dd`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/ul[3]/li[1]`
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/ul[3]/li[1]`
- Old text: If a component made definitive recording decision - this decision SHOULD be reflected in the sampled flag.
- New text: If a component made definitive recording decision - this decision SHOULD be reflected in the sampled flag.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9975`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.95`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `904ee78bc4df6d06e2ef3f12f53e1955dd7a6e86f5a471441fb9804f4cc05fb9`
  - `afe283c66c3035457e3ae2bebcb4af8751d2bc048c22ea4d973b7b89906b7ba0`
  - `c0cc93dfda06079274ee5545990be65ce2f9c50b3c4606d9a8ca65cfe1aa0651`
  - `d23e614b43e51eacab7eb02df1f2f1575cde3be2291724d5dc9c6ada083fdc16`

### `MOVED` — `da5702a4adaf65dc`

- Confidence: `0.93`
- Modality transition: `MAY->MAY`
- Old requirement: `0e3600d1b138592c`
- New requirement: `eb4da77b03decb6d`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.4 Mutating the traceparent Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- Old locator: `xpath:/body/section[5]/section[4]/p[1]`
- New locator: `xpath:/body/section[5]/section[4]/p[2]`
- Old text: A vendor receiving a traceparent request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing it to outgoing requests.
- New text: A vendor receiving a traceparent request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing it to outgoing requests.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `7681230d221fc5018675e267f7c376ad7b8004a8166e20a8b7412d974a2a8ab9`
  - `abbf8f90bf21454e65b0594afe5366bbaf31f366c58250ac4b5b98fdc24de6a4`
  - `c3540fb7e9f6adc672584712481001ba1fdbb2b4baabf443281681e97385a8f2`
  - `fc8d25edee02e6a3cee69b370c98cb007ca3b387bd6179f6533526f22bdf6e42`

### `MOVED` — `988599bca050ad90`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `18e562bc7b0f2ee5`
- New requirement: `66509855fa7a36ad`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.5 tracestate Limits:
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.3 Combined Header Value > 3.3.3.1 tracestate Limits:
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[5]/p[1]`
- New locator: `xpath:/body/section[5]/section[3]/section[3]/section/p[1]`
- Old text: Vendors SHOULD propagate at least 512 characters of a combined header. This length includes commas required to separate list items and optional white space (OWS) characters.
- New text: Vendors SHOULD propagate at least 512 characters of a combined header. This length includes commas required to separate list items and optional white space (OWS) characters.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9606`
  - structural_proximity: `0.5`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `1f65e46ee3e610dfc2cf9e2f0f9028124fd799b3e4af0602fcccc87ca19b6898`
  - `39c04f434ce7de80c9145c273cdb31b55c7ad7500be1047eb5202f2d5de6348a`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `cde3a2ca94281963d757aa773de57c43c36049d3a9de354cb1c635d6d12ce35f`
  - `dbce56da7edc10dc5b42be08ccda893d4f9b27b0d7ecbd2760d51d2e5a27fd12`

### `MOVED` — `2c0ef0a56b2f558c`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `1c3a620073937a02`
- New requirement: `e96f2943275ef2b6`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/ul/li[2]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/ul/li[2]`
- Old text: Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-).
- New text: Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-).
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `b806417db545ee61a58767187c90fc3fa9579a9534cae75b33790167916d24f8`
  - `e1adea1a63d8dfba34e8e8b738201c698ffeb4b3769f18217eb676ed595b159b`
  - `e314dba1813e096b2a3e6d043825c5b05438104cbcf9571c327b8824a38263b6`
  - `e65ff67cad8f40258a053ec89e0e4fc0e25869e8976891fa3e9c4e5e11636daa`

### `MOVED` — `ba0e6eede9d19b86`

- Confidence: `0.93`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `1d0c3032bc6e6233`
- New requirement: `3f6f054ceb69d88d`
- Old section: Trace Context > 1. Conformance
- New section: Trace Context Level 2 > 1. Conformance
- Old locator: `xpath:/body/section[3]/p[2]`
- New locator: `xpath:/body/section[3]/p[2]`
- Old text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- New text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
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
  - `048781f4acf7d8510f51a23a3a480e40d943f9a4c71613381c2daf271c1fb921`
  - `08a32d54884e97b9658284fec6fd5dad2c0f7a099d33f501b1500873ef85d0aa`
  - `142bca48e3eacc9a9415c5e1d63c3383b104e60659b0b3e1198328231731d6b5`
  - `2983f82374cb0a653a8f81255194ab65aa9d4f488404f320ab37462bd806396e`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`

### `MOVED` — `92fc27543880743b`

- Confidence: `0.93`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `24135e61661ca424`
- New requirement: `6b22899c0fda2e32`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.4 Mutating the traceparent Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- Old locator: `xpath:/body/section[5]/section[4]/p[2]`
- New locator: `xpath:/body/section[5]/section[4]/p[3]`
- Old text: If the value of the traceparent field wasn't changed before propagation, tracestate MUST NOT be modified as well. Unmodified header propagation is typically implemented in pass-through services like proxies. This behavior may also be implemented in a service which currently does not collect distributed tracing information.
- New text: If the value of the traceparent field wasn't changed before propagation, tracestate MUST NOT be modified as well. Unmodified header propagation is typically implemented in pass-through services like proxies. This behavior may also be implemented in a service which currently does not collect distributed tracing information.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `046f1a1a43938cf3b179c4873e20352db4d279b7864d187ab11c83db1dde8c61`
  - `2800e3b99324b6a606bfb16f0b2725a64ee20422741baaa911717a5b2499b972`
  - `5676b5a6556f05af3a38adc994996e9cef2d385602321176cf752d90e1b4f7fb`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `76d159a857276473e317236581e7581ef1f911685b41cb1849b09a9e36674803`

### `MOVED` — `87175aea4f0f01fe`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `2b16f6e4e53b30e0`
- New requirement: `c4990cffe98e6632`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/p[1]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/p[1]`
- Old text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following:
- New text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following:
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `1e4f1c7c94ac4b9df70a39ed573af332dd90e2a90b4f3358c126aae4d9339355`
  - `38934d4f3f5b69cc2cd0439de52d433ca2189fda88c9e78a04f28faf842ce72b`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `7a57e20b7c5c245fbef94f52d37004af8a545c1875ea2d8d83101f40825ac44e`
  - `a910ad27cefdc068f4e8b3b9f7e0fe7e9022d0d9d3c5e1cdae885998d62f824e`

### `MOVED` — `4fefcccec7cf2a7d`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `2d55fb19d075b266`
- New requirement: `70ab3c9421ad9733`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.3 trace-id
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.3 trace-id
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[3]/p[2]`
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[3]/p[3]`
- Old text: If the trace-id value is invalid (for example if it contains non-allowed characters or all zeros), vendors MUST ignore the traceparent.
- New text: If the trace-id value is invalid (for example if it contains non-allowed characters or all zeros), vendors MUST ignore the traceparent.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9925`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.85`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `40d2abe4418a617afff06b0bea19fc960eed4006e8ba8d4ffba5389374598c24`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `718ad85d123be79f16e2b6501e30e8113d656039cd850733f75a9e325c0567b4`
  - `a60d1523f3cc825ec666404a5f594a4563e1c1156fee206583fd62fa341e45af`
  - `e4e1c296260bdfe1d3f86f6d8845d7373e9774c98a97fa30817423d9f1849a25`

### `MOVED` — `8a599cffc2a5d6ef`

- Confidence: `0.93`
- Modality transition: `MAY->MAY`
- Old requirement: `361116c9b907935a`
- New requirement: `8a17b998c9bf6fb9`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/p[11]`
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/p[10]`
- Old text: There are two additional options that vendors MAY follow:
- New text: There are two additional options that vendors MAY follow:
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9975`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.95`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `2bd2459698d594f234c0b13974a90d43e983de8f03af338f1cc9db7200741280`
  - `60f945dd1708c850f56e7d5febf0848f1837c5463719ba43267f4996752090c8`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `d54fe7dd9c3df6a614e3f3da81f5681adbfee108e158f919814de5a0c2953e26`
  - `fbfbb22281599c70a1b73304657464e77e19b39a7a031d6fbc14c46ac7752f69`

### `MOVED` — `7a4619c9170ea722`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `4418b73549d3245d`
- New requirement: `a9a4535a29110e24`
- Old section: Trace Context > 1. Conformance
- New section: Trace Context Level 2 > 1. Conformance
- Old locator: `xpath:/body/section[3]/p[2]`
- New locator: `xpath:/body/section[3]/p[2]`
- Old text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- New text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
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
  - `048781f4acf7d8510f51a23a3a480e40d943f9a4c71613381c2daf271c1fb921`
  - `08a32d54884e97b9658284fec6fd5dad2c0f7a099d33f501b1500873ef85d0aa`
  - `142bca48e3eacc9a9415c5e1d63c3383b104e60659b0b3e1198328231731d6b5`
  - `2983f82374cb0a653a8f81255194ab65aa9d4f488404f320ab37462bd806396e`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`

### `MOVED` — `dd7afa605565fea8`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `48298c5b818813fb`
- New requirement: `c08468e186994d5f`
- Old section: Trace Context > 2. Overview > 2.3 Design Overview
- New section: Trace Context Level 2 > 2. Overview > 2.3 Design Overview
- Old locator: `xpath:/body/section[4]/section[3]/ul[2]/li[1]`
- New locator: `xpath:/body/section[4]/section[3]/ul[2]/li[1]`
- Old text: At a minimum they MUST propagate the traceparent and tracestate headers and guarantee traces are not broken. This behavior is also referred to as forwarding a trace.
- New text: At a minimum they MUST propagate the traceparent and tracestate headers and guarantee traces are not broken. This behavior is also referred to as forwarding a trace.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9925`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.85`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0d5d2fcc007c851755fb4fa7102c6917509f95e6c5b5619204aeca7fa4682243`
  - `3f1f2693539ccf3384d3b6946da59a7a0f3543c97750acb210302fbb3f615269`
  - `4a3ea3d8ffc8c47485cc4148d2ad549239885c98ce51b5be1c7dc6293818478f`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `a46e1aaea0daa2aba75a7b46503b8bf12e26e0f8db8d3952eeb634705c0024fd`

### `MOVED` — `2a8540ed831287ba`

- Confidence: `0.93`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `528842b57097a131`
- New requirement: `d893cfb474cdc0d7`
- Old section: Trace Context > 6. Privacy Considerations > 6.2 Privacy of tracestate field
- New section: Trace Context Level 2 > 6. Privacy Considerations > 6.2 Privacy of tracestate field
- Old locator: `xpath:/body/section[8]/section[2]/p[2]`
- New locator: `xpath:/body/section[8]/section[2]/p[2]`
- Old text: Vendors MUST NOT include any personally identifiable information in the tracestate header.
- New text: Vendors MUST NOT include any personally identifiable information in the tracestate header.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `08f0094854eaf494c277333e4750868cbaf5267ae0d9d9187e45e56eb267a6f8`
  - `3f3bd12cd618e1476b8a89eabf06cd4b17d881ac75cac614941b296dac7d0cfb`
  - `5d1a507dc00d800f860a8672731008e8b57264e310b33493d7a09472e8e5f988`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `a519847ea39e6c949058ec632fa5d6372f6d3ba1e8545eee43d6a8cc48f8d249`

### `MOVED` — `80dca2a48e75a79d`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `5739c52169fec1cf`
- New requirement: `8412b80b396d4571`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[7]`
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[7]`
- Old text: Empty and whitespace-only list members are allowed. Vendors MUST accept empty tracestate headers but SHOULD avoid sending them. Empty list members are allowed in tracestate because it is difficult for a vendor to recognize the empty value when multiple tracestate headers are sent. Whitespace characters are allowed for a similar reason, as some vendors automatically inject whitespace after a comma separator, even in the case of an empty header.
- New text: Empty and whitespace-only list members are allowed. Vendors MUST accept empty tracestate headers but SHOULD avoid sending them. Empty list members are allowed in tracestate because it is difficult for a vendor to recognize the empty value when multiple tracestate headers are sent. Whitespace characters are allowed for a similar reason, as some vendors automatically inject whitespace after a comma separator, even in the case of an empty header.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9635`
  - structural_proximity: `0.4`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `2efd2aeffa0d96d09405e47c44c55983a185757c9463cdbbb1055bb450ed7c87`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `8af46c70bf194a335d3e4d7804329dad68b456f5e1cbe340a37571e857957680`
  - `99f5095706e6ea8c84d04990926b4dacb6f1d07f98e63f86768dee46068367b5`
  - `9fdccb745080c8619c2b9d211e931abb5ccd7bf110c95f6859f3aee03fc50e62`

### `MOVED` — `6a105328e34ef08b`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `654f5f23625f4cd0`
- New requirement: `6a54c377f0d45c9a`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.2 Other Flags
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.3 Other Flags
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[2]/p`
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[3]/p`
- Old text: The behavior of other flags, such as (00000100) is not defined and is reserved for future use. Vendors MUST set those to zero.
- New text: The behavior of other flags, such as (00000100) is not defined and is reserved for future use. Vendors MUST set those to zero.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0d7d9b8ed0f4b4ea0cf957c5138d77b55381ad1ce982e583ab1e761a34154a84`
  - `6c5bbddc52188a863c76af49802e7efb0a520a60e63627d9a7fd391456116815`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `cec7f9f23f39d62ec04a288c93723ea7cbc3d35d6f2b78fd6545a8ec8e40b487`
  - `e421154906713efd19aeda489cd8bb73c60a3e3f13d0aa420bd2fe837acd8825`

### `MOVED` — `806488a5b28c9517`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `6811232b26022d96`
- New requirement: `3710568e0102163f`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/p[3]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/p[3]`
- Old text: Vendors MUST NOT parse or assume anything about unknown fields for this version. Vendors MUST use these fields to construct the new traceparent field according to the highest version of the specification known to the implementation (in this specification it is 00).
- New text: Vendors MUST NOT parse or assume anything about unknown fields for this version. Vendors MUST use these fields to construct the new traceparent field according to the highest version of the specification known to the implementation (in this specification it is 00).
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `139b27d455ab4c5d9484c0d386c275d157ce8f7e952334bce457c5fe1bb06181`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `77645dd06a1c5a9436e7620fd6746690217cc658d1d1770b4430c71e60d3b2c0`
  - `95555e6d43075d24a73b1a326ab4f4b427b719e23d60a4f9fb7edc657e8f31c7`
  - `9fe07abac704a2a4bf2490ebad7de35e78e050f0b8f68be4b564b51e7044d57a`

### `MOVED` — `cca6ff959fc5e2a0`

- Confidence: `0.93`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `685b1a9b8f7dbe41`
- New requirement: `9708971a78375a22`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.4 Mutating the traceparent Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- Old locator: `xpath:/body/section[5]/section[4]/p[4]`
- New locator: `xpath:/body/section[5]/section[4]/p[5]`
- Old text: Vendors MUST NOT make any other mutations to the traceparent header.
- New text: Vendors MUST NOT make any other mutations to the traceparent header.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `3ae2c8531665eb46f716d53c82b1f1e4036858401e4cf6910c212db6b7b89601`
  - `4c08a9ca2db14c87aacab04a3d20e6a0b58556282d2cfa68b2888f43461876ee`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `89aea54d3674ad984764d3551651d8e4eab0893729184c983bd7846a9aeac708`
  - `f9c989a09b0e914c8ff4f941f4b7e5514448cd53fa1fe58fb917ffa6ffd4f47b`

### `MOVED` — `322a21e37dec01f1`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `6c3f06d0d3180e50`
- New requirement: `1092f1ee90385591`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[7]`
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[7]`
- Old text: Empty and whitespace-only list members are allowed. Vendors MUST accept empty tracestate headers but SHOULD avoid sending them. Empty list members are allowed in tracestate because it is difficult for a vendor to recognize the empty value when multiple tracestate headers are sent. Whitespace characters are allowed for a similar reason, as some vendors automatically inject whitespace after a comma separator, even in the case of an empty header.
- New text: Empty and whitespace-only list members are allowed. Vendors MUST accept empty tracestate headers but SHOULD avoid sending them. Empty list members are allowed in tracestate because it is difficult for a vendor to recognize the empty value when multiple tracestate headers are sent. Whitespace characters are allowed for a similar reason, as some vendors automatically inject whitespace after a comma separator, even in the case of an empty header.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9635`
  - structural_proximity: `0.4`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `2efd2aeffa0d96d09405e47c44c55983a185757c9463cdbbb1055bb450ed7c87`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `8af46c70bf194a335d3e4d7804329dad68b456f5e1cbe340a37571e857957680`
  - `99f5095706e6ea8c84d04990926b4dacb6f1d07f98e63f86768dee46068367b5`
  - `9fdccb745080c8619c2b9d211e931abb5ccd7bf110c95f6859f3aee03fc50e62`

### `MOVED` — `f79ea6cb3d1e219f`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `6e26ab93bb5582d1`
- New requirement: `3af5cff758e4b46a`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/ul/li[2]`
- New locator: `xpath:/body/section[5]/section[5]/ul/li[2]`
- Old text: Update an existing value. The value for any given key can be updated. Modified keys SHOULD be moved to the beginning (left) of the list.
- New text: Update an existing value. The value for any given key can be updated. Modified keys SHOULD be moved to the beginning (left) of the list.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `023085adfb6f76a9c66a21d84fdfb4096151dd094df972814d8748a5d8d007c5`
  - `0246ff9b424e5d8a53994bc2e1c721c3bbc2b15c222c093dfd6f54c6dc343f8a`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `7d3b22cf4a84bc28c384c357dcd84d7dfbe29bd528884663bc27d875a6df81b9`
  - `a05d646154d36ef15c721f6b3118190f688d59db18d07a44999802e6944401c3`

### `MOVED` — `fc273e72288b70e8`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `7712c0f14fffd652`
- New requirement: `0bf62768e4f78a0e`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/ul/li[3]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]/ul/li[3]`
- Old text: Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash.
- New text: Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `140206a0000110e2ea304b595b77a4265b022da4b13adca2d283219a3553580a`
  - `227c3e463e192383edf12e208c08e4979d0a427bc48aa4e32a0e0db0c5361a01`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `dbe7d9504a6ac96198dfb63db4d61826ebedf6be73b6fb9084d44b31c052f052`
  - `fce95ab5ad65ada78baf734bd53078e154d4d24adca715433b1f0f20ae1172ae`

### `MOVED` — `5f55668d1a55ade6`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `7b0178a06f97a8ce`
- New requirement: `6b85617aedb80158`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[5]`
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[5]`
- Old text: The caller SHOULD generate the optional whitespace as a single space; otherwise, a caller SHOULD NOT generate optional whitespace. See details in the corresponding RFC.
- New text: The caller SHOULD generate the optional whitespace as a single space; otherwise, a caller SHOULD NOT generate optional whitespace. See details in the corresponding RFC.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9635`
  - structural_proximity: `0.4`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `2b5b1ca414542393555ce41778612a3f4d052d966c74a45c0ae105f941bd18f2`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `86dda820379b2d7cab5424b29e61233172b755a9e31280af66858f4d43ba7fac`
  - `9cffd261cb4ffc5b5617e3f31eec1b1aadc259f182b515937c7531855a20dbd9`
  - `bc9afe9f86360ee06fdf61fb600e1c8e3bb420f2df916c2a7fb2ca492ced606d`

### `MOVED` — `c28bbc87dfcf6fe3`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `7d5b968a8c576908`
- New requirement: `b4f2c3463ff373d7`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/p[10]`
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/p[9]`
- Old text: The following are a set of suggestions that vendors SHOULD use to increase vendor interoperability.
- New text: The following are a set of suggestions that vendors SHOULD use to increase vendor interoperability.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9975`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.95`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `400074a98249d65a2efa58f8e26ed74885bea1fcb32c7cd6b07b3112c7fb6ff5`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `8e5be1aac3161a152816c76125e82d373780b089ad1aa811007c83dd508b0f46`
  - `bdec661f4dd383cbe0a08c793b00bf94f9c4171ad1c703e770b7647696c3c2a1`
  - `efb4abb0cf9939f48dd0424b118894f3021f4309cf0dae5f542e525e1e3a0c90`

### `MOVED` — `cbfb68d7f3fde420`

- Confidence: `0.93`
- Modality transition: `SHOULD_NOT->SHOULD_NOT`
- Old requirement: `843228a63d15697f`
- New requirement: `7b13585c155c9f56`
- Old section: Trace Context > 6. Privacy Considerations > 6.2 Privacy of tracestate field
- New section: Trace Context Level 2 > 6. Privacy Considerations > 6.2 Privacy of tracestate field
- Old locator: `xpath:/body/section[8]/section[2]/p[3]`
- New locator: `xpath:/body/section[8]/section[2]/p[3]`
- Old text: Vendors extremely sensitive to personal information exposure MAY implement selective removal of values corresponding to the unknown keys. Vendors SHOULD NOT mutate the tracestate field, as it defeats the purpose of allowing multiple tracing systems to collaborate.
- New text: Vendors extremely sensitive to personal information exposure MAY implement selective removal of values corresponding to the unknown keys. Vendors SHOULD NOT mutate the tracestate field, as it defeats the purpose of allowing multiple tracing systems to collaborate.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `1479f81abbd1d0aa51e074d83c1e3c604250cecd6777124d208674434e3371e0`
  - `447016b8dd772377a1e5801f5dee9d7699bc46d721f5fdea65ed5c6c78afedd5`
  - `4b62c87256040df0c1db7c228c76c0d2a36ad171d5f638cd8595132535594626`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `ee625872cef2f24bf706be993c7981ad5cfc068ec511c5c81fcea3704c8badbd`

### `MOVED` — `64f4620dbfeac13c`

- Confidence: `0.93`
- Modality transition: `MAY->MAY`
- Old requirement: `8fbcbc54991e1d0b`
- New requirement: `caab0f4c01ab6a5f`
- Old section: Trace Context > 1. Conformance
- New section: Trace Context Level 2 > 1. Conformance
- Old locator: `xpath:/body/section[3]/p[2]`
- New locator: `xpath:/body/section[3]/p[2]`
- Old text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- New text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
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
  - `048781f4acf7d8510f51a23a3a480e40d943f9a4c71613381c2daf271c1fb921`
  - `08a32d54884e97b9658284fec6fd5dad2c0f7a099d33f501b1500873ef85d0aa`
  - `142bca48e3eacc9a9415c5e1d63c3383b104e60659b0b3e1198328231731d6b5`
  - `2983f82374cb0a653a8f81255194ab65aa9d4f488404f320ab37462bd806396e`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`

### `MOVED` — `94a06967741f1bb5`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `96031a6f7b3f7a6b`
- New requirement: `b7b766f15cb8c97a`
- Old section: Trace Context > 6. Privacy Considerations > 6.1 Privacy of traceparent field
- New section: Trace Context Level 2 > 6. Privacy Considerations > 6.1 Privacy of traceparent field
- Old locator: `xpath:/body/section[8]/section[1]/p[3]`
- New locator: `xpath:/body/section[8]/section[1]/p[3]`
- Old text: Note that these privacy concerns of the traceparent field are theoretical rather than practical. Some services initiating or receiving a request MAY choose to restart a traceparent field to eliminate those risks completely. Vendors SHOULD find a way to minimize the number of distributed trace restarts to promote interoperability of tracing vendors. Instead of restarts, different techniques may be used. For example, services may define trust boundaries of upstream and downstream connections and the level of exposure that any requests may bring. For instance, a vendor might only restart traceparent for authentication requests from or to external services.
- New text: Note that these privacy concerns of the traceparent field are theoretical rather than practical. Some services initiating or receiving a request MAY choose to restart a traceparent field to eliminate those risks completely. Vendors SHOULD find a way to minimize the number of distributed trace restarts to promote interoperability of tracing vendors. Instead of restarts, different techniques may be used. For example, services may define trust boundaries of upstream and downstream connections and the level of exposure that any requests may bring. For instance, a vendor might only restart traceparent for authentication requests from or to external services.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0ae4286b69b78ef89016ac61b1758b34770c9f809df511308501666adc1fb475`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `73a6b47de7426790c570ab03f6872227db332395ab9ea4d424992dd041d53697`
  - `b35a3c613df4e117b312d7abf485d268631a3b6b96f954652cee4b499a7ff472`
  - `e0264269305c5f7d55381af7149e4107602643844644528fd05b008b2cde7a51`

### `MOVED` — `0fd1b84d5df7f8ff`

- Confidence: `0.93`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `96b8d4c55cd44cf0`
- New requirement: `90e62cbf5c78c7d2`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/p[3]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/p[3]`
- Old text: Vendors MUST NOT parse or assume anything about unknown fields for this version. Vendors MUST use these fields to construct the new traceparent field according to the highest version of the specification known to the implementation (in this specification it is 00).
- New text: Vendors MUST NOT parse or assume anything about unknown fields for this version. Vendors MUST use these fields to construct the new traceparent field according to the highest version of the specification known to the implementation (in this specification it is 00).
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `139b27d455ab4c5d9484c0d386c275d157ce8f7e952334bce457c5fe1bb06181`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `77645dd06a1c5a9436e7620fd6746690217cc658d1d1770b4430c71e60d3b2c0`
  - `95555e6d43075d24a73b1a326ab4f4b427b719e23d60a4f9fb7edc657e8f31c7`
  - `9fe07abac704a2a4bf2490ebad7de35e78e050f0b8f68be4b564b51e7044d57a`

### `MOVED` — `97176580efe2996c`

- Confidence: `0.93`
- Modality transition: `MUST_NOT->MUST_NOT`
- Old requirement: `9ac747aa8d61f429`
- New requirement: `d78b1ef7644fec9d`
- Old section: Trace Context > 6. Privacy Considerations
- New section: Trace Context Level 2 > 6. Privacy Considerations
- Old locator: `xpath:/body/section[8]/p[1]`
- New locator: `xpath:/body/section[8]/p[1]`
- Old text: Requirements to propagate headers to downstream services, as well as storing values of these headers, open up potential privacy concerns. Tracing vendors MUST NOT use traceparent and tracestate fields for any personally identifiable or otherwise sensitive information. The only purpose of these fields is to enable trace correlation.
- New text: Requirements to propagate headers to downstream services, as well as storing values of these headers, open up potential privacy concerns. Tracing vendors MUST NOT use traceparent and tracestate fields for any personally identifiable or otherwise sensitive information. The only purpose of these fields is to enable trace correlation.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0b07ba6fa3727a6f9bf12abcdb3e14cfc84ba1c15de14ba04785637578c0995d`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `a91099e3e86438c3d1a2dfe840ea500e6b14e3d7fd4a53a6209db369644ad2d8`
  - `e311d84d6db47354760e2839a84ef3d0b54f38090184f5f8404f91cc158de408`
  - `f6a6e4f123c90332cfcb3d7fe4ddb5503598df113ee3c1ce288cbdd89c3310c2`

### `MOVED` — `ffe194155dff2146`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `9e7da2797452b0c3`
- New requirement: `d65b4bd24e034675`
- Old section: Trace Context > 2. Overview > 2.3 Design Overview
- New section: Trace Context Level 2 > 2. Overview > 2.3 Design Overview
- Old locator: `xpath:/body/section[4]/section[3]/ul[1]/li[1]`
- New locator: `xpath:/body/section[4]/section[3]/ul[1]/li[1]`
- Old text: traceparent describes the position of the incoming request in its trace graph in a portable, fixed-length format. Its design focuses on fast parsing. Every tracing tool MUST properly set traceparent even when it only relies on vendor-specific information in tracestate
- New text: traceparent describes the position of the incoming request in its trace graph in a portable, fixed-length format. Its design focuses on fast parsing. Every tracing tool MUST properly set traceparent even when it only relies on vendor-specific information in tracestate
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9925`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.85`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0c3e07615d40de8f31d01143b7d7b051357e7bf52811c8a827bb1ffe7536200a`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `9b48604aa47cddb4bca41647b8fa34d59fdcf9e5825d2482ed0bf959e551d806`
  - `b6bf3aa0502c0db9c67a1d3b143c727139efd6a420bba4aefaff997b74cd3cad`
  - `ca4b22b6eb14bc074096bda646c16af37d6912e6e820b4c251fba6bb1ca2c139`

### `MOVED` — `def15ab0352c4f38`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `adc15f99b8e00876`
- New requirement: `1196765c313f6793`
- Old section: Trace Context > 6. Privacy Considerations
- New section: Trace Context Level 2 > 6. Privacy Considerations
- Old locator: `xpath:/body/section[8]/p[2]`
- New locator: `xpath:/body/section[8]/p[2]`
- Old text: Vendors MUST assess the risk of header abuse. This section provides some considerations and initial assessment of the risk associated with storing and propagating these headers. Tracing vendors may choose to inspect and remove sensitive information from the fields before allowing the tracing system to execute code that can potentially propagate or store these fields. All mutations should, however, conform to the list of mutations defined in this specification.
- New text: Vendors MUST assess the risk of header abuse. This section provides some considerations and initial assessment of the risk associated with storing and propagating these headers. Tracing vendors may choose to inspect and remove sensitive information from the fields before allowing the tracing system to execute code that can potentially propagate or store these fields. All mutations should, however, conform to the list of mutations defined in this specification.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0dcb3901d9433e59544f4548943efc1ac02a4d6824d9b1f37e07bacc10ae0787`
  - `1c36d0b5f140c6e319b46b82a9ffb2900431907eb20ea1e20275a0df1bfed832`
  - `2f60d5064d9e3592958f2ed054a0a9080e35f1c118c1fd321ac5cc8fd89c06ad`
  - `644cc87bbb3198b229c5da69e2922d64d3b6ea310adb4776c4deb2e49e34e889`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`

### `MOVED` — `3fae68d637949d26`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `b6d27c998faf8be6`
- New requirement: `0dd39b5fc4aab117`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.4 parent-id
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.4 parent-id
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[4]/p[2]`
- New locator: `xpath:/body/section[5]/section[2]/section[2]/section[4]/p[2]`
- Old text: Vendors MUST ignore the traceparent when the parent-id is invalid (for example, if it contains non-lowercase hex characters).
- New text: Vendors MUST ignore the traceparent when the parent-id is invalid (for example, if it contains non-lowercase hex characters).
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
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
  - `2e499c26b527f011fea8dcb05d877473555c58da82df622ca48af1bafa6c9edf`
  - `59e27cc7a98066c237fdddf4a3c318478fa0773b554c67e8d2862a4c6fc3b673`
  - `610dfb3cfd396b1e72ce00a709bf456870eabbfd688f97363e18df14a7d34604`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `abc94024385de6a70f826828f9c8e9d77d5279cf1641e61787ef904a10ae1db6`

### `MOVED` — `13f19c173e8e14aa`

- Confidence: `0.93`
- Modality transition: `SHOULD_NOT->SHOULD_NOT`
- Old requirement: `bb0f7b03068594c8`
- New requirement: `e6a224c1d3b7543d`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.3 Tracestate Header > 3.3.2 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[5]`
- New locator: `xpath:/body/section[5]/section[3]/section[2]/p[5]`
- Old text: The caller SHOULD generate the optional whitespace as a single space; otherwise, a caller SHOULD NOT generate optional whitespace. See details in the corresponding RFC.
- New text: The caller SHOULD generate the optional whitespace as a single space; otherwise, a caller SHOULD NOT generate optional whitespace. See details in the corresponding RFC.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9635`
  - structural_proximity: `0.4`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `2b5b1ca414542393555ce41778612a3f4d052d966c74a45c0ae105f941bd18f2`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `86dda820379b2d7cab5424b29e61233172b755a9e31280af66858f4d43ba7fac`
  - `9cffd261cb4ffc5b5617e3f31eec1b1aadc259f182b515937c7531855a20dbd9`
  - `bc9afe9f86360ee06fdf61fb600e1c8e3bb420f2df916c2a7fb2ca492ced606d`

### `MOVED` — `10fcda4df07d4fe3`

- Confidence: `0.93`
- Modality transition: `MAY->MAY`
- Old requirement: `c1f247de966bf0d9`
- New requirement: `55b6323060aa920f`
- Old section: Trace Context > 6. Privacy Considerations > 6.2 Privacy of tracestate field
- New section: Trace Context Level 2 > 6. Privacy Considerations > 6.2 Privacy of tracestate field
- Old locator: `xpath:/body/section[8]/section[2]/p[3]`
- New locator: `xpath:/body/section[8]/section[2]/p[3]`
- Old text: Vendors extremely sensitive to personal information exposure MAY implement selective removal of values corresponding to the unknown keys. Vendors SHOULD NOT mutate the tracestate field, as it defeats the purpose of allowing multiple tracing systems to collaborate.
- New text: Vendors extremely sensitive to personal information exposure MAY implement selective removal of values corresponding to the unknown keys. Vendors SHOULD NOT mutate the tracestate field, as it defeats the purpose of allowing multiple tracing systems to collaborate.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `1479f81abbd1d0aa51e074d83c1e3c604250cecd6777124d208674434e3371e0`
  - `447016b8dd772377a1e5801f5dee9d7699bc46d721f5fdea65ed5c6c78afedd5`
  - `4b62c87256040df0c1db7c228c76c0d2a36ad171d5f638cd8595132535594626`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `ee625872cef2f24bf706be993c7981ad5cfc068ec511c5c81fcea3704c8badbd`

### `MOVED` — `e1e9accde3b5b9e1`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `ea7bbc1e480b9b64`
- New requirement: `50e44d99e9fee51d`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/p[2]`
- New locator: `xpath:/body/section[5]/section[2]/section[4]/p[2]`
- Old text: Vendors MUST follow these rules when parsing headers with an unexpected format:
- New text: Vendors MUST follow these rules when parsing headers with an unexpected format:
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `1b13ad487b9b222c9e16c1b3f42bdd9e30e6f6eecd153532f44b1e21db86edc9`
  - `1d4440e5a889be57db8254c0a4aaf32dd7526dfbca049e3e9d7ede60c6473551`
  - `1da336484936c0f31e0e54d005749792046e4c20ffb316f974322cb026a0130e`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `b9f784b9a3012078e68d8e01203930164f21fc38fbf3c8a78389bf9277258bbf`

### `MOVED` — `a56009e71c484b0d`

- Confidence: `0.93`
- Modality transition: `MAY->MAY`
- Old requirement: `f02dcfce7a1316ec`
- New requirement: `8361cd4ee193258d`
- Old section: Trace Context > 6. Privacy Considerations > 6.1 Privacy of traceparent field
- New section: Trace Context Level 2 > 6. Privacy Considerations > 6.1 Privacy of traceparent field
- Old locator: `xpath:/body/section[8]/section[1]/p[3]`
- New locator: `xpath:/body/section[8]/section[1]/p[3]`
- Old text: Note that these privacy concerns of the traceparent field are theoretical rather than practical. Some services initiating or receiving a request MAY choose to restart a traceparent field to eliminate those risks completely. Vendors SHOULD find a way to minimize the number of distributed trace restarts to promote interoperability of tracing vendors. Instead of restarts, different techniques may be used. For example, services may define trust boundaries of upstream and downstream connections and the level of exposure that any requests may bring. For instance, a vendor might only restart traceparent for authentication requests from or to external services.
- New text: Note that these privacy concerns of the traceparent field are theoretical rather than practical. Some services initiating or receiving a request MAY choose to restart a traceparent field to eliminate those risks completely. Vendors SHOULD find a way to minimize the number of distributed trace restarts to promote interoperability of tracing vendors. Instead of restarts, different techniques may be used. For example, services may define trust boundaries of upstream and downstream connections and the level of exposure that any requests may bring. For instance, a vendor might only restart traceparent for authentication requests from or to external services.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0ae4286b69b78ef89016ac61b1758b34770c9f809df511308501666adc1fb475`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `73a6b47de7426790c570ab03f6872227db332395ab9ea4d424992dd041d53697`
  - `b35a3c613df4e117b312d7abf485d268631a3b6b96f954652cee4b499a7ff472`
  - `e0264269305c5f7d55381af7149e4107602643844644528fd05b008b2cde7a51`

### `MOVED` — `f907b70eac2ab2f3`

- Confidence: `0.93`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `f4b52c63641bbca5`
- New requirement: `78a3f54798374eb6`
- Old section: Trace Context > 1. Conformance
- New section: Trace Context Level 2 > 1. Conformance
- Old locator: `xpath:/body/section[3]/p[2]`
- New locator: `xpath:/body/section[3]/p[2]`
- Old text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- New text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
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
  - `048781f4acf7d8510f51a23a3a480e40d943f9a4c71613381c2daf271c1fb921`
  - `08a32d54884e97b9658284fec6fd5dad2c0f7a099d33f501b1500873ef85d0aa`
  - `142bca48e3eacc9a9415c5e1d63c3383b104e60659b0b3e1198328231731d6b5`
  - `2983f82374cb0a653a8f81255194ab65aa9d4f488404f320ab37462bd806396e`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`

### `MOVED` — `5d50fdf30d66df6c`

- Confidence: `0.93`
- Modality transition: `SHOULD_NOT->SHOULD_NOT`
- Old requirement: `f9456aff59736671`
- New requirement: `1a3242b76dae6f90`
- Old section: Trace Context > 1. Conformance
- New section: Trace Context Level 2 > 1. Conformance
- Old locator: `xpath:/body/section[3]/p[2]`
- New locator: `xpath:/body/section[3]/p[2]`
- Old text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- New text: The key words MAY, MUST, MUST NOT, SHOULD, and SHOULD NOT in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
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
  - `048781f4acf7d8510f51a23a3a480e40d943f9a4c71613381c2daf271c1fb921`
  - `08a32d54884e97b9658284fec6fd5dad2c0f7a099d33f501b1500873ef85d0aa`
  - `142bca48e3eacc9a9415c5e1d63c3383b104e60659b0b3e1198328231731d6b5`
  - `2983f82374cb0a653a8f81255194ab65aa9d4f488404f320ab37462bd806396e`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`

### `MOVED` — `c645c37233101124`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `fff8ae54db31b22f`
- New requirement: `7678e6daa4c78c72`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.4 Mutating the traceparent Field
- New section: Trace Context Level 2 > 3. Trace Context HTTP Request Headers Format > 3.4 Mutating the traceparent Field
- Old locator: `xpath:/body/section[5]/section[4]/ul/li[2]`
- New locator: `xpath:/body/section[5]/section[4]/ul/li[2]`
- Old text: Update sampled: The value of the sampled field reflects the caller's recording behavior: either trace data was dropped or may have been recorded out-of-band. This can be indicated by toggling the flag in both directions. This mutation gives the downstream vendor information about the likelihood that its parent's information was recorded. The parent-id field MUST be set to a new value with the sampled flag update.
- New text: Update sampled: The value of the sampled field reflects the caller's recording behavior: either trace data was dropped or may have been recorded out-of-band. This can be indicated by toggling the flag in both directions. This mutation gives the downstream vendor information about the likelihood that its parent's information was recorded. The parent-id field MUST be set to a new value with the sampled flag update.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `1.0`
  - structural_proximity: `0.45`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `08bee14b13d9d0c191af3f56bbd36d68f2f6d43d442800cd30699c054468263b`
  - `24877dd9849944e68a197e0eca29343332b041c13e4578ed900f8dd57626685d`
  - `6523f0f598b51af3a8b5b1e43c581f9f8f150cfc9b86f194786b9cca51358b4c`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `bcd9f7798afeafb0075424a26c143f5c4a60d1188120ab0b6bbad7af3ce8bd7e`

### `REMOVED` — `15db2799d4f820e9`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `0062f541d5f1c4df`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.4 Mutating the traceparent Field
- Old locator: `xpath:/body/section[5]/section[4]/ul/li[3]`
- Old text: Restart trace: All properties (trace-id, parent-id, trace-flags) are regenerated. This mutation is used in services that are defined as a front gate into secure networks and eliminates a potential denial-of-service attack surface. Vendors SHOULD clean up tracestate collection on traceparent restart. There are rare cases when the original tracestate entries must be preserved after a restart. This typically happens when the trace-id is reverted back at some point of the trace flow, for instance, when it leaves the secure network. However, it SHOULD be an explicit decision, and not the default behavior.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `09446ce1fbea0246088bbdd046e3e44cbf02669960b6d8d9b4e62dba0447c8cc`
  - `93966c352b139a02d334a8638570d6296c1bb2c5068f475a7dde79aa0235822b`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `330d0b57bb6ec2d7`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `14db216fde54e3a4`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.5 tracestate Limits:
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[5]/p[3]`
- Old text: In a situation where tracestate needs to be truncated due to size limitations, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Note that other truncation strategies like safe list entries, blocked list entries, or size-based truncation MAY be used, but are highly discouraged. Those strategies decrease the interoperability of various tracing vendors.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `0061aeb33d51d724c2296beff726298a8311d1d1ceb763cf03ed61c7c416f188`
  - `1429050b414a67c4f13e6b2af8a0186a56d56352619c888e2314b5a7a75e21a2`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `98a39ae9e7027b16`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `1c1a07c6c98bf4f3`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- Old text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either the end of the string or a dash. If all three values were parsed successfully, the vendor should use them.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `a29da8069a7d1da149f91b08d81077795ad94d6099e2d544ec1caa9b0d52daf5`
  - `aa23c8ea35e31aaac0255c5fd6b92ec774c1c1902ea0a5180d1d813a91aa2ed3`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `30224a875afa9e42`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `2cd377d8a377e916`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.1 Header Name
- Old locator: `xpath:/body/section[5]/section[2]/section[1]/p[2]`
- Old text: In order to increase interoperability across multiple protocols and encourage successful integration, by default vendors SHOULD keep the header name lowercase. The header name is a single word without any delimiters, for example, a hyphen (-).
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `07d1dba45cbce3d63db94e19abd1ef10f7a7078140bc561302a9c499113266fd`
  - `9b46f6eabd3b69d943ad384ebc1f413e854f413ba7ce264cf586b5530bd6eff4`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `aafe8bc174e976cd`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `3dac174f538e9498`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[1]`
- Old text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC7230 Section 3.2.2 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC7230. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC7230.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `1e671a1c09d576a42416fb624bf020d55ada4a3192c6af58c9256ed90382599f`
  - `7216f0edf619d7f02aa8f90c954f192a2f501d90d0484da9a6ac7c8521407e37`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `adc09ad6fe945a78`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `44f0034d0140385e`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[1]`
- Old text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC7230 Section 3.2.2 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC7230. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC7230.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `1e671a1c09d576a42416fb624bf020d55ada4a3192c6af58c9256ed90382599f`
  - `7216f0edf619d7f02aa8f90c954f192a2f501d90d0484da9a6ac7c8521407e37`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `83db3bf9cef5166a`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `46381261a853a1b7`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.5 tracestate Limits:
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[5]/p[3]`
- Old text: In a situation where tracestate needs to be truncated due to size limitations, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Note that other truncation strategies like safe list entries, blocked list entries, or size-based truncation MAY be used, but are highly discouraged. Those strategies decrease the interoperability of various tracing vendors.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `0061aeb33d51d724c2296beff726298a8311d1d1ceb763cf03ed61c7c416f188`
  - `1429050b414a67c4f13e6b2af8a0186a56d56352619c888e2314b5a7a75e21a2`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `84d4a53f93081d71`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `466a35e4c33663c4`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.5 tracestate Limits:
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[5]/p[3]`
- Old text: In a situation where tracestate needs to be truncated due to size limitations, the vendor MUST truncate whole entries. Entries larger than 128 characters long SHOULD be removed first. Then entries SHOULD be removed starting from the end of tracestate. Note that other truncation strategies like safe list entries, blocked list entries, or size-based truncation MAY be used, but are highly discouraged. Those strategies decrease the interoperability of various tracing vendors.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `0061aeb33d51d724c2296beff726298a8311d1d1ceb763cf03ed61c7c416f188`
  - `1429050b414a67c4f13e6b2af8a0186a56d56352619c888e2314b5a7a75e21a2`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `da41da4e20028564`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `5b0f7823a7b3ab9a`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/ul[3]/li[2]`
- Old text: If a component needs to make a recording decision - it SHOULD respect the sampled flag value. Security considerations SHOULD be applied to protect from abusive or malicious use of this flag.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `00243228f7821c78951b128d220e3e246c05c45731c8800b271ebade857d743b`
  - `5360dffc8eed34e23424b0de1df02d2774f07a383b6b43928fed038e49fce82f`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `baa441f451b73f3e`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `6756bd7551c5d1ad`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/p[1]`
- Old text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys SHOULD be moved to the beginning (left) of the list.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `a8cbd51eb45d9ee5157232bfb8fd5f2b7e2895ab3368de56ef46f03c2f66b8df`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `ccf1f3e4e71116e174bfd28485e9550d3f874ceed1bab4144b1ec3757f0aaebe`

### `REMOVED` — `e5456d8218a00e1b`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `6adbee76d8747b55`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.5 tracestate Limits:
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[5]/p[2]`
- Old text: There are systems where propagating of 512 characters of tracestate may be expensive. In this case, the maximum size of the propagated tracestate header SHOULD be documented and explained. The cost of propagating tracestate SHOULD be weighted against the value of monitoring scenarios enabled for the end users.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `4b64cf061d4988436ac33d977cfb2e0dac89dd2fe62e7b224773d7a634cd1b6e`
  - `7c2554114180f1689d8a512087130286183837fd102765d9e65441689865d3fa`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `2b8f848b1a8e31b2`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `6f8800e8c368bf1e`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[1]`
- Old text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC7230 Section 3.2.2 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC7230. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC7230.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `1e671a1c09d576a42416fb624bf020d55ada4a3192c6af58c9256ed90382599f`
  - `7216f0edf619d7f02aa8f90c954f192a2f501d90d0484da9a6ac7c8521407e37`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `33c83305ff2a6554`

- Confidence: `0.95`
- Modality transition: `MUST_NOT->∅`
- Old requirement: `7317397054e47a4f`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header
- Old locator: `xpath:/body/section[5]/section[3]/p[2]`
- Old text: If the vendor failed to parse traceparent, it MUST NOT attempt to parse tracestate. Note that the opposite is not true: failure to parse tracestate MUST NOT affect the parsing of traceparent.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `2259c8beb71454304991cee0534c0c5df50148e598cde105c3cc1a65a42f68c5`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `e8e222cc7f0e4b66ec0d8e946c27cc54d6d50766998372492064a2d158dfbfba`

### `REMOVED` — `e4905a19968413c4`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `76fbdff85efa5a5d`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.1 Header Name
- Old locator: `xpath:/body/section[5]/section[2]/section[1]/p[3]`
- Old text: Vendors MUST expect the header name in any case (upper, lower, mixed), and SHOULD send the header name in lowercase.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `92fc168886b1b3999eaa1ef36523983a5f4af124256091314935850fdf20f40e`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `e323c5b7a3feb1c5c77854081c81aeb447a85568aa45c1dff905400836e84622`

### `REMOVED` — `03cd2430fda17e09`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `7b7b11577f38f41a`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/p[1]`
- Old text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys SHOULD be moved to the beginning (left) of the list.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `a8cbd51eb45d9ee5157232bfb8fd5f2b7e2895ab3368de56ef46f03c2f66b8df`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `ccf1f3e4e71116e174bfd28485e9550d3f874ceed1bab4144b1ec3757f0aaebe`

### `REMOVED` — `7eb051a784b9e5b8`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `9b65d6be3e91490c`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.4 Mutating the traceparent Field
- Old locator: `xpath:/body/section[5]/section[4]/ul/li[3]`
- Old text: Restart trace: All properties (trace-id, parent-id, trace-flags) are regenerated. This mutation is used in services that are defined as a front gate into secure networks and eliminates a potential denial-of-service attack surface. Vendors SHOULD clean up tracestate collection on traceparent restart. There are rare cases when the original tracestate entries must be preserved after a restart. This typically happens when the trace-id is reverted back at some point of the trace flow, for instance, when it leaves the secure network. However, it SHOULD be an explicit decision, and not the default behavior.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `09446ce1fbea0246088bbdd046e3e44cbf02669960b6d8d9b4e62dba0447c8cc`
  - `93966c352b139a02d334a8638570d6296c1bb2c5068f475a7dde79aa0235822b`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `91e6c23e95e3ba2e`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `bcca524e4fac70f8`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/p[3]`
- Old text: Vendors MUST expect the header name in any case (upper, lower, mixed), and SHOULD send the header name in lowercase.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `92fc168886b1b3999eaa1ef36523983a5f4af124256091314935850fdf20f40e`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `dfc538765aa1766c9778756c99a61218a5fdf4a4965d582ccd556397fa81e74e`

### `REMOVED` — `c44bda8f625957d2`

- Confidence: `0.95`
- Modality transition: `MUST_NOT->∅`
- Old requirement: `bdb68f7b0e322f35`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header
- Old locator: `xpath:/body/section[5]/section[3]/p[2]`
- Old text: If the vendor failed to parse traceparent, it MUST NOT attempt to parse tracestate. Note that the opposite is not true: failure to parse tracestate MUST NOT affect the parsing of traceparent.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `2259c8beb71454304991cee0534c0c5df50148e598cde105c3cc1a65a42f68c5`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `e8e222cc7f0e4b66ec0d8e946c27cc54d6d50766998372492064a2d158dfbfba`

### `REMOVED` — `52f8edb89cff02b4`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `be8328164cb8cf1b`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.5 Mutating the tracestate Field
- Old locator: `xpath:/body/section[5]/section[5]/p[1]`
- Old text: Vendors receiving a tracestate request header MUST send it to outgoing requests. It MAY mutate the value of this header before passing to outgoing requests. When mutating tracestate, the order of unmodified key/value pairs MUST be preserved. Modified keys SHOULD be moved to the beginning (left) of the list.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `a8cbd51eb45d9ee5157232bfb8fd5f2b7e2895ab3368de56ef46f03c2f66b8df`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `ccf1f3e4e71116e174bfd28485e9550d3f874ceed1bab4144b1ec3757f0aaebe`

### `REMOVED` — `51a37478012091b8`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `c453502dd7dc9725`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- Old text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either the end of the string or a dash. If all three values were parsed successfully, the vendor should use them.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `a29da8069a7d1da149f91b08d81077795ad94d6099e2d544ec1caa9b0d52daf5`
  - `aa23c8ea35e31aaac0255c5fd6b92ec774c1c1902ea0a5180d1d813a91aa2ed3`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `f109142dc4a26ab8`

- Confidence: `0.95`
- Modality transition: `MAY->∅`
- Old requirement: `d85e817c4fedd8d0`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.1 tracestate Header Field Values
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[1]/p[1]`
- Old text: The tracestate field may contain any opaque value in any of the keys. Tracestate MAY be sent or received as multiple header fields. Multiple tracestate header fields MUST be handled as specified by RFC7230 Section 3.2.2 Field Order. The tracestate header SHOULD be sent as a single field when possible, but MAY be split into multiple header fields. When sending tracestate as multiple header fields, it MUST be split according to RFC7230. When receiving multiple tracestate header fields, they MUST be combined into a single header according to RFC7230.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `1e671a1c09d576a42416fb624bf020d55ada4a3192c6af58c9256ed90382599f`
  - `7216f0edf619d7f02aa8f90c954f192a2f501d90d0484da9a6ac7c8521407e37`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `1ce2bdfa129fa4b5`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `ebe5245841c24c20`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name > 3.3.1.5 tracestate Limits:
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/section[5]/p[2]`
- Old text: There are systems where propagating of 512 characters of tracestate may be expensive. In this case, the maximum size of the propagated tracestate header SHOULD be documented and explained. The cost of propagating tracestate SHOULD be weighted against the value of monitoring scenarios enabled for the end users.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `4b64cf061d4988436ac33d977cfb2e0dac89dd2fe62e7b224773d7a634cd1b6e`
  - `7c2554114180f1689d8a512087130286183837fd102765d9e65441689865d3fa`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `bf7dd916bd205bb8`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `f8828f1f2fce1841`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.2 traceparent Header Field Values > 3.2.2.5 trace-flags > 3.2.2.5.1 Sampled flag
- Old locator: `xpath:/body/section[5]/section[2]/section[2]/section[5]/section[1]/ul[3]/li[2]`
- Old text: If a component needs to make a recording decision - it SHOULD respect the sampled flag value. Security considerations SHOULD be applied to protect from abusive or malicious use of this flag.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `00243228f7821c78951b128d220e3e246c05c45731c8800b271ebade857d743b`
  - `5360dffc8eed34e23424b0de1df02d2774f07a383b6b43928fed038e49fce82f`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`

### `REMOVED` — `4c245fb1c9551d12`

- Confidence: `0.95`
- Modality transition: `SHOULD->∅`
- Old requirement: `fa87cc67334e66ce`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.3 Tracestate Header > 3.3.1 Header Name
- Old locator: `xpath:/body/section[5]/section[3]/section[1]/p[2]`
- Old text: In order to increase interoperability across multiple protocols and encourage successful integration, by default you SHOULD keep the header name lowercase. The header name is a single word without any delimiters, for example, a hyphen (-).
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `a4581b713b57a491eb66416852b88e17166351f8371a1e96623afd264d910739`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
  - `b926734c198b2b4652be5b2f16539990bb2fa3a8c02f69b216941e7bff649e48`

### `REMOVED` — `97135d1bf5fb3680`

- Confidence: `0.95`
- Modality transition: `MUST->∅`
- Old requirement: `ff67056f2d69c64d`
- Old section: Trace Context > 3. Trace Context HTTP Headers Format > 3.2 Traceparent Header > 3.2.4 Versioning of traceparent
- Old locator: `xpath:/body/section[5]/section[2]/section[4]/ul/li[3]`
- Old text: If a higher version is detected, the implementation SHOULD try to parse it by trying the following: If the size of the header is shorter than 55 characters, the vendor should not parse the header and should restart the trace. Parse trace-id (from the first dash through the next 32 characters). Vendors MUST check that the 32 characters are hex, and that they are followed by a dash (-). Parse parent-id (from the second dash at the 35th position through the next 16 characters). Vendors MUST check that the 16 characters are hex and followed by a dash. Parse the sampled bit of flags (2 characters from the third dash). Vendors MUST check that the 2 characters are either the end of the string or a dash. If all three values were parsed successfully, the vendor should use them.
- Reasons:
  - No aligned successor requirement; treated as removal.
- Evidence hashes:
  - `a29da8069a7d1da149f91b08d81077795ad94d6099e2d544ec1caa9b0d52daf5`
  - `aa23c8ea35e31aaac0255c5fd6b92ec774c1c1902ea0a5180d1d813a91aa2ed3`
  - `b10f45473a35ad1407552ab2edf9df4280ca19b4d5a9042045844a44b058b528`
