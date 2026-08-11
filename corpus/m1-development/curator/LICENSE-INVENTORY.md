# NormShift M1 development-source license inventory

Status: `CLEAR_FOR_COMPLETE_UNMODIFIED_PINNED_SNAPSHOT_REDISTRIBUTION_WITH_REQUIRED_NOTICES`

This is a source-curation finding, not legal advice. It applies only to the exact raw SHA-256 values in `SOURCE-INVENTORY.json`; derived excerpts or modified copies require a fresh license review.

## RFC family

Sources: RFC 2246, RFC 4346, and RFC 5246, fetched as complete RFC Editor HTML resources.

- License/basis: document-embedded copyright and distribution notices, BCP 78 where referenced, and the [IETF Trust Legal Provisions 5.0](https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/).
- Supporting interpretation: the [IETF Trust copyright/TLP FAQ](https://trustee.ietf.org/documents/trust-legal-provisions/copyright-policy-and-tlp-faq/) states that unmodified IETF Documents may be published outside the IETF standards process.
- Required handling: distribute the complete snapshot without modification; retain all copyright, authorship, IETF/RFC legends, legal notices, and disclaimers; do not imply endorsement. No patent license is inferred.
- RFC 2246 additionally contains its own explicit copying/distribution grant conditioned on retention of its copyright notice and grant paragraph.

## W3C_TR family

Sources: Micropub Candidate Recommendation 2016-10-18, Proposed Recommendation 2017-04-13, and Recommendation 2017-05-23.

- Each exact document links `https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document`, which redirects to the [W3C Software and Document License, 2015 version](https://www.w3.org/copyright/software-license-2015/).
- License/basis: copying, modification, and distribution are permitted subject to the license notice conditions.
- Required handling for these unmodified snapshots: bundle a user-viewable copy of the full license notice; retain existing W3C copyright, status, original URI, disclaimers, and trademark restrictions; identify that no modification was made.
- Frozen source identity remains each dated `This Version` URL. The documents' observed mutable `link rel=canonical` value (`https://www.w3.org/TR/micropub/`) is auxiliary metadata only.

## WHATWG family

Sources: MIME Sniffing Review Drafts 2023-07, 2024-07, 2025-01, and 2025-07.

- License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
- Basis: every retained Review Draft includes the CC BY 4.0 footer; [WHATWG IPR Policy section 7.1.1](https://whatwg.org/ipr-policy) explicitly applies CC BY 4.0 to Living Standards and Review Drafts. The BSD 3-Clause alternative applies only to portions incorporated into source code, not to this full-document HTML use.
- Required handling: attribute WHATWG and the named copyright holders, name the MIME Sniffing Standard, provide the exact source URL and CC BY 4.0 link, and state that the snapshot is unmodified. No patent conclusion beyond the WHATWG policy is inferred.

## Frozen license evidence

| Evidence | Final URL | SHA-256 | Bytes |
|---|---|---:|---:|
| IETF TLP 5.0 | `https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/` | `9ae8dca17817e331cca993e80261c14ae6b73b0194ecb7a7055645839b67ef67` | 72,616 |
| IETF TLP FAQ | `https://trustee.ietf.org/documents/trust-legal-provisions/copyright-policy-and-tlp-faq/` | `610eaaa046b55b8df39456e6ed7dafd4d3ded19884500f9da8aded02c33151f9` | 76,042 |
| W3C license 2015 | `https://www.w3.org/copyright/software-license-2015/` | `d2f31d95646fcc5f3b6e61b39d44898e6d828d9259e87fa2bc1184452d5803df` | 26,970 |
| WHATWG IPR Policy | `https://whatwg.org/ipr-policy` | `7cc4d98fe3179995010bc00e64ec6b64dd782aae8c6de7dd9c7533b901107227` | 36,038 |
| CC BY 4.0 legal code | `https://creativecommons.org/licenses/by/4.0/legalcode.en` | `6d55b998ed5c54f43426d059a8c549ed58a3321e5463e6a6af1c6b56ab78c333` | 48,970 |

## Fail-closed boundary

These findings do not authorize an undisclosed future holdout source. The independent evaluation owner must repeat this per-document review for every blind source. A missing or generic license, ambiguous ownership, changed bytes, unofficial host, or uncertain version relationship is `BLOCKED_EXTERNAL` under the frozen policy.
