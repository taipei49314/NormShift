# NormShift Diff Report

- Tool version: `0.3.1`
- Profile: `rfc2119`
- Schema version: `1.0.0`
- Integrity: `sha256` `2ced18608f7080e490b69f279c0f5f82e5918fda66ba93895279be9553363565`

## Documents

| Side | Path | Version | SHA-256 | Bytes |
|------|------|---------|---------|-------|
| old | `fixtures/synthetic/spec-v1.html` | `1.0.0` | `4757ae7e75bd0f87e06810560dca4889c5032c5b471aa72988fa4c818ba1a0ab` | 1332 |
| new | `fixtures/synthetic/spec-v2.html` | `2.0.0` | `dcbf6fb22c0649ecdb1b2bf0bb4ad2d4e2eca549446115bee10efe6a47fcb1cb` | 2144 |

### Provenance

- **old**: family=`generic_html` adapter=`normshift.adapters.html`@1.0.0 type=`text/html`
  - local_path (portable): `fixtures/synthetic/spec-v1.html`
- **new**: family=`generic_html` adapter=`normshift.adapters.html`@1.0.0 type=`text/html`
  - local_path (portable): `fixtures/synthetic/spec-v2.html`

## Summary

- Old requirements: **9**
- New requirements: **11**
- Changes: **11**

### Classification counts

- `ADDED`: 2
- `EXCEPTION_ADDED`: 1
- `MOVED`: 5
- `POLARITY_FLIP`: 1
- `STRENGTHENED`: 1
- `WEAKENED`: 1

## Changes

### `ADDED` — `6d2ae057a796abd8`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `382f52ffd4f4d1db`
- New section: Synthetic Protocol Spec 2.0.0 > 1 Transmission
- New locator: `id:req-sync|xpath:/body/p[6]`
- New text: Implementers MUST synchronize clocks when a network is available.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `5a869e32e2ab7580da7c1c082fb4f8be64467bd346f60df4aa759d12cec0d0f0`
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `9f1a4f57497186d28caaab84c7ea68f00d3104ad7e3ebbf87bef3d6ebdefec9c`

### `ADDED` — `b7cd79f70fee58d5`

- Confidence: `0.95`
- Modality transition: `∅->MUST`
- New requirement: `8f10558cf9307985`
- New section: Synthetic Protocol Spec 2.0.0 > 1 Transmission
- New locator: `id:req-new|xpath:/body/p[7]`
- New text: Senders MUST include a monotonic sequence number on every datagram.
- Reasons:
  - No aligned prior requirement; treated as addition.
- Evidence hashes:
  - `734373a3f32ffac0af9bf18d865c82aa24cbc0fb601f743bed62add9f23b8727`
  - `7be2c631e75eb8b30fa2ecf1d55fde6cdaef496f578228206fad14c14fc08d75`
  - `c1ee1ddf109285e29f04cca87680655341e1bdc138711ab9067f18e355b7d5d9`

### `EXCEPTION_ADDED` — `be166dd62b3f9559`

- Confidence: `0.88`
- Modality transition: `SHOULD->SHOULD`
- Old requirement: `f2839ab2dd52973f`
- New requirement: `5cf7ca79eae1763a`
- Old section: Synthetic Protocol Spec 1.0.0 > 2 Privacy
- New section: Synthetic Protocol Spec 2.0.0 > 1 Transmission
- Old locator: `id:req-cache|xpath:/body/p[5]`
- New locator: `id:req-cache|xpath:/body/p[5]`
- Old text: User agents SHOULD cache public keys for at most 24 hours.
- New text: User agents SHOULD cache public keys for at most 24 hours unless private mode is active.
- Reasons:
  - Exception introduced: 'unless private mode is active'.
- Alignment score components:
  - combined: `0.921`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.7917`
  - modality_match: `1.0`
  - section_similarity: `0.7952`
  - structural_proximity: `1.0`
  - text_similarity: `0.9358`
  - token_similarity: `0.7808`
- Evidence hashes:
  - `5c77b5575f62f94c0620da9d7c53efbe1fe14b0d575eb22812f4762705fad8fc`
  - `8d9c036fb62cc608555765647d1cd4aaf5f1a1ca029c8d05954e54b49e229dca`
  - `b7ab86a71b7fdac275d490cb883501aded1693e2fe5f7e1fa62a9810fa115c50`
  - `ee4818194fbce7a337bb841c6609570ffa260ee468a5e42284a5feac6249271e`
  - `f3320d7b998a31d885e271cec67bb87fe31d90622f16f75b25b0f7db7503cccf`

### `MOVED` — `3e977e49bcff0ec3`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `3ca8070a5df84272`
- New requirement: `d9645ac69218f34d`
- Old section: Synthetic Protocol Spec 1.0.0 > 4 Routing
- New section: Synthetic Protocol Spec 2.0.0 > 4 Routing
- Old locator: `id:req-route-a|xpath:/body/p[8]`
- New locator: `id:req-route-a|xpath:/body/p[10]`
- Old text: Implementers MUST reject unknown critical extensions.
- New text: Implementers MUST reject unknown critical extensions.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9924`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9744`
  - structural_proximity: `0.9`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `dc6d721c2a1174f32306245f395e2917049c29e481bdccec67d776f1938af6ae`
  - `e113ddfaee9d200c4b21b030764af0429011515d397b5ae3d5b1e1a9b8fcc103`
  - `efe34cee3d4d59d7aa6c57231baff8a8e1e8445edbc0e31b57966f1b0d132e27`
  - `f6068d6511abd32b32d60a981a6dcf1c25196e95096eefa58e1499aeca6fec8a`

### `MOVED` — `ea5a887ddc74b725`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `5fe0dffd984f56a5`
- New requirement: `ccc4f80ed800e78c`
- Old section: Synthetic Protocol Spec 1.0.0 > 2 Privacy
- New section: Synthetic Protocol Spec 2.0.0 > 1 Transmission
- Old locator: `id:req-store|xpath:/body/p[4]`
- New locator: `id:req-store|xpath:/body/p[4]`
- Old text: Implementers MUST store credentials in encrypted form.
- New text: Implementers MUST store credentials in encrypted form.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.7952`
  - structural_proximity: `1.0`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `16865a326ea438b6d9317d8459a0db886237c75363df1d70c7db70399a079b92`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `c5f425fd9229fb427f8c9dc33658e1bdbecf8520dff548c128728ec15738986c`
  - `d548652006bb875186f3b4a3b62843e6da95da444f9d0c8abdd1458052e5d372`
  - `e861a18a742bb4fedaba9f1c4a8f3579c1871aec9c19fa7ee69c2ff2c993325b`

### `MOVED` — `9cbe7abe4202209a`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `d79a122f572e2814`
- New requirement: `83f25c48eafd041e`
- Old section: Synthetic Protocol Spec 1.0.0 > 4 Routing
- New section: Synthetic Protocol Spec 2.0.0 > 4 Routing
- Old locator: `id:req-route-b|xpath:/body/p[9]`
- New locator: `id:req-route-b|xpath:/body/p[11]`
- Old text: Implementers MUST accept unknown non-critical extensions.
- New text: Implementers MUST accept unknown non-critical extensions.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9924`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9744`
  - structural_proximity: `0.9`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0f7c7d0f6179e0ff026d6da8810763a0d1f66e32f0a535fce5121cb724055020`
  - `17ae68af48225cd3071edf7257dd6cab8a1f582b848cd7bd40373dd2a6502bf2`
  - `4e4f6a01cca7b24da8248a54db686b2f0777ee42859f874b60df4591a4815575`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `8193efad327750b019c2a8262c97f508c44403127d37fea9109bc91a3d8620cc`

### `MOVED` — `bebd59bc54736471`

- Confidence: `0.93`
- Modality transition: `MUST->MUST`
- Old requirement: `ec1ae09c4bb1fcd1`
- New requirement: `fd263b6b4787bc06`
- Old section: Synthetic Protocol Spec 1.0.0 > 5 Session
- New section: Synthetic Protocol Spec 2.0.0 > 6 Relocated Session
- Old locator: `id:req-session|xpath:/body/p[10]`
- New locator: `id:req-session|xpath:/body/p[12]`
- Old text: User agents MUST open at most one control channel per origin.
- New text: User agents MUST open at most one control channel per origin.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.99`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.9167`
  - structural_proximity: `0.9`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0df1e361d69c55b696d01323617d72de915ae99f5d17653debe7ec6f343e7ac3`
  - `3bd4205feefa96ded6dc7d2984927bf2c5ecaafadb53bf23ed24db4104411e3f`
  - `516b373445a2180f94bfc741a4e87ab09db4ca8470cf0f8a89ecb86443bc619f`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `9103a1df1c69b21d24d14943ae4212b42c581a8224f3ee6f4b8caf45074630eb`

### `MOVED` — `2f51333956c71095`

- Confidence: `0.93`
- Modality transition: `MAY->MAY`
- Old requirement: `febedcd8344d2cce`
- New requirement: `6d9eea7941302da9`
- Old section: Synthetic Protocol Spec 1.0.0 > 3 Examples
- New section: Synthetic Protocol Spec 2.0.0 > 3 Examples
- Old locator: `id:req-mustard|xpath:/body/p[6]`
- New locator: `id:req-mustard|xpath:/body/p[8]`
- Old text: The mustard configuration key MAY be omitted by clients.
- New text: The mustard configuration key MAY be omitted by clients.
- Reasons:
  - Semantically identical requirement relocated across sections → MOVED.
- Alignment score components:
  - combined: `0.9925`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `1.0`
  - modality_match: `1.0`
  - section_similarity: `0.975`
  - structural_proximity: `0.9`
  - text_similarity: `1.0`
  - token_similarity: `1.0`
- Evidence hashes:
  - `0a4a7d429dca6cfad3cfe9495c3f55518da56c481a8e5b67e6ca33e54968db45`
  - `26a636adaf5b81d75fb5cb7bde3a18a851f53f7baab2642a7c218efc6f12964e`
  - `26f2a102e03d0ef2e1f847dfb48554a3fd5bb1f067ec321952936bacd045778f`
  - `6d34a5621bc272a259ed5d4a5ad504f0cb75418592c78da423fefc7e18aaa0c6`
  - `b9d88011b2bf1d0e861436aa9449a249af1777c419981f09cbc4aaa92c72adc3`

### `POLARITY_FLIP` — `355c2df40e696c39`

- Confidence: `0.9`
- Modality transition: `MUST->MUST_NOT`
- Old requirement: `84219220e5040601`
- New requirement: `b5e120cbc1add8b2`
- Old section: Synthetic Protocol Spec 1.0.0 > 1 Transmission
- New section: Synthetic Protocol Spec 2.0.0 > 1 Transmission
- Old locator: `id:req-log|xpath:/body/p[3]`
- New locator: `id:req-log|xpath:/body/p[3]`
- Old text: Clients MUST log every authentication failure.
- New text: Clients MUST NOT log every authentication failure.
- Reasons:
  - Polarity/modality flip: MUST -> MUST_NOT.
- Alignment score components:
  - combined: `0.8415`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9574`
  - modality_match: `0.0`
  - section_similarity: `0.9773`
  - structural_proximity: `1.0`
  - text_similarity: `1.0`
  - token_similarity: `0.9583`
- Evidence hashes:
  - `05c7f64fe1b522ab50cff7e183b72fc161ee64e0d11d7f9708b13e003861021a`
  - `3924c5877fa8c9f225817249da8455ccf38a2a67a9897f5028a44af5b5f5b908`
  - `566ff37a15eb4f2a2db705ad4d168edd860e086fa3ac8e3ca5e37bcdb7c0e3dd`
  - `56df0f918f8325563935c7a9aa73f8ad3f437fb74bfb75d5166a068b95d3dbca`
  - `6429c979407d0405eee83691eb3d45c138e39b708c96b6c85ce97da95f96c6c7`

### `STRENGTHENED` — `5db3442a7705f5ce`

- Confidence: `0.92`
- Modality transition: `SHOULD->MUST`
- Old requirement: `e1c817245f92a943`
- New requirement: `0012241f41f632db`
- Old section: Synthetic Protocol Spec 1.0.0 > 1 Transmission
- New section: Synthetic Protocol Spec 2.0.0 > 1 Transmission
- Old locator: `id:req-send|xpath:/body/p[1]`
- New locator: `id:req-send|xpath:/body/p[1]`
- Old text: Implementers SHOULD send an acknowledgment after each frame.
- New text: Implementers MUST send an acknowledgment after each frame.
- Reasons:
  - Obligation strengthened: SHOULD -> MUST.
- Alignment score components:
  - combined: `0.8795`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.931`
  - modality_match: `0.4`
  - section_similarity: `0.9773`
  - structural_proximity: `1.0`
  - text_similarity: `0.955`
  - token_similarity: `0.9322`
- Evidence hashes:
  - `4ca3ac9a42b23757accd88a61087678f97e8a2380cafc312d281a7434a787187`
  - `57a7ada65f65e90a5baf7ca655c133a749537127bc3b7d4538e8ae76aff64215`
  - `832ce89d4d066cc91de351a8b96a7eef60a08f65418e84ddff9a9524a2e63abc`
  - `d451cb7aa263932e29ba457ce350967d54a7640951a1ef53b5b8c93cb486e5f6`
  - `fa06f24d236b4c202533d7a828cfad42ab515b98ef63a83e8b6508d14c909b46`

### `WEAKENED` — `4992727683045912`

- Confidence: `0.92`
- Modality transition: `MUST->SHOULD`
- Old requirement: `6f96e2026ba9c24b`
- New requirement: `baa705772b78c218`
- Old section: Synthetic Protocol Spec 1.0.0 > 1 Transmission
- New section: Synthetic Protocol Spec 2.0.0 > 1 Transmission
- Old locator: `id:req-retry|xpath:/body/p[2]`
- New locator: `id:req-retry|xpath:/body/p[2]`
- Old text: Servers MUST retry failed deliveries up to three times.
- New text: Servers SHOULD retry failed deliveries up to three times.
- Reasons:
  - Obligation weakened: MUST -> SHOULD.
- Alignment score components:
  - combined: `0.878`
  - actor_action_similarity: `1.0`
  - editorial_similarity: `0.9273`
  - modality_match: `0.4`
  - section_similarity: `0.9773`
  - structural_proximity: `1.0`
  - text_similarity: `0.9524`
  - token_similarity: `0.9286`
- Evidence hashes:
  - `15cff6363a7334dac351cf1351ab6031102031486e8142b80709e2180dbff2e0`
  - `25bfadbe275914a9af978a1e7447c05182e942739d3d9fa47cbf36f938e0b842`
  - `98e54b02a65a77ec5a19fe1ac19072827e1efaea88a0c61912c81ac6e37f6054`
  - `c689be42d8ddb0d25d63c2dc16401bdcaf5b6cd80cd83e6537532848239743a9`
  - `e1d107b43d2f38d7eae2a90c21a023c8d409d1fd3f4065057805d1d020d738cc`
