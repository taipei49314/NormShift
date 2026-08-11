# NormShift independent M1 source curation report

Outcome: official replayable **development-source corpus** acquired and independently re-fetched. This is source availability only; M1 and M2 remain `NOT_ADJUDICATED`, blind holdout remains `BLOCKED_EXTERNAL`, and release remains `BLOCKED`.

The governing policy bytes were fetched from merge commit `5a8d5a38c866eac2b8b382fac1af64d63707a73f` and verified as SHA-256 `0265082c85b5e381cf30484774a8cba0d7fb11ab4d5dab8dd5aaa6fd6630f773`.

No NormShift candidate was executed. No prediction, gold, label, score, holdout membership, or per-case output was viewed or created. No repository or GitHub state was changed, and no expedition `AUTO` data was used as evidence.

## Exact source inventory

For every row, requested URL = final URL = frozen canonical snapshot URL, HTTP status = 200, and redirect count = 0. W3C documents additionally declare a mutable HTML `link rel=canonical` of `https://www.w3.org/TR/micropub/`; that value is recorded only as auxiliary metadata and does not replace the dated frozen identity.

| ID / version | Official frozen URL | ETag | Last-Modified | Type / charset | Bytes | Raw SHA-256 |
|---|---|---|---|---|---:|---|
| RFC 2246 / TLS 1.0 | `https://www.rfc-editor.org/rfc/rfc2246.html` | `W/"b589e062b572e18bc21d5ac516864b6a"` | `null` | `text/html`; `null` | 195,469 | `82ef7a3d371e5801b445aea0c639b1fa0851ae542d740a5b238d00e07d6c3cf3` |
| RFC 4346 / TLS 1.1 | `https://www.rfc-editor.org/rfc/rfc4346.html` | `W/"afc836df464679deaeed76c4955ad74a"` | `null` | `text/html`; `null` | 223,410 | `b58c88a5bb51205bf656cf80b5053d9eb32db38847daea95b4402b91da7bba1e` |
| RFC 5246 / TLS 1.2 | `https://www.rfc-editor.org/rfc/rfc5246.html` | `W/"cf76bc12a9a2765242c371817484d5b6"` | `null` | `text/html`; `null` | 268,261 | `a6102891f08ad01933fdce6891c0045432b699c917db12903cfa694372b5e86a` |
| Micropub CR / 2016-10-18 | `https://www.w3.org/TR/2016/CR-micropub-20161018/` | `null` | `Sat, 15 Oct 2016 17:06:25 GMT` | `text/html`; `utf-8` | 163,776 | `8341ae06105a972b8c5e2e60d9924722a174705b7396619caf734c3b7db890f3` |
| Micropub PR / 2017-04-13 | `https://www.w3.org/TR/2017/PR-micropub-20170413/` | `null` | `Thu, 13 Apr 2017 07:59:08 GMT` | `text/html`; `utf-8` | 175,848 | `3edf8e00e5b1068ad83f8a714531d9980acbcee655848f0cc405ba3f8b640597` |
| Micropub REC / 2017-05-23 | `https://www.w3.org/TR/2017/REC-micropub-20170523/` | `null` | `Sun, 21 May 2017 14:54:51 GMT` | `text/html`; `utf-8` | 172,429 | `9eebd4b244e9b0fce61ab6830a79527ff780ebcd225316009451a9c6d902551d` |
| MIME Sniffing RD / 2023-07 (published 2023-07-17) | `https://mimesniff.spec.whatwg.org/review-drafts/2023-07/` | `"64b50be0-239ce"` | `Mon, 17 Jul 2023 09:37:36 GMT` | `text/html`; `utf-8` | 145,870 | `01528914273a059ea6d61035f0b778013b128a3635421da91c3a4199c09cf109` |
| MIME Sniffing RD / 2024-07 (published 2024-07-15) | `https://mimesniff.spec.whatwg.org/review-drafts/2024-07/` | `"66950668-1e4f9"` | `Mon, 15 Jul 2024 11:22:16 GMT` | `text/html`; `utf-8` | 124,153 | `596ec6c40da0dc935e4664d03d6ac9ea55d3d7787d9eee24bb303cc84717218f` |
| MIME Sniffing RD / 2025-01 (published 2025-01-20) | `https://mimesniff.spec.whatwg.org/review-drafts/2025-01/` | `"678e0dad-1b857"` | `Mon, 20 Jan 2025 08:47:41 GMT` | `text/html`; `utf-8` | 112,727 | `b5388f593d4941b61015659e57daca1e7e9eb44508ee04b3854a9b2f2b4e7421` |
| MIME Sniffing RD / 2025-07 (published 2025-07-21) | `https://mimesniff.spec.whatwg.org/review-drafts/2025-07/` | `"687df7ae-1ce2c"` | `Mon, 21 Jul 2025 08:17:50 GMT` | `text/html`; `utf-8` | 118,316 | `db83d3e4a68e6a89361ef10c8113ea569feb05c7782818d9b6223a0b213117b7` |

Total: 10 actual documents, 1,700,259 raw bytes. The machine-readable inventory records exact retrieval UTC, request/final/canonical values, header evidence paths, adapter/profile proposals, portable refs, per-source license basis, and replay locations.

## M1 versus M2 source claims

| Gate slice | Source-only finding | Acceptance effect |
|---|---|---|
| M1 actual versions | RFC 3, W3C_TR 3, WHATWG 4 distinct raw documents and hashes; each exceeds the policy minimum of 2 | Availability only; no extraction/classification accuracy was evaluated |
| M2 RFC chain | RFC 2246 → RFC 4346 → RFC 5246; each later RFC directly says it obsoletes/revises its predecessor | 3-version source chain available |
| M2 W3C_TR chain | Micropub CR 2016-10-18 → PR 2017-04-13 → REC 2017-05-23; later documents name the immediate prior `Previous Version` and provide change logs | 3-version source chain available |
| M2 WHATWG chain | MIME Sniffing Review Draft 2023-07 → 2024-07 → 2025-01 → 2025-07 | 4-version source chain available |

The WHATWG order was checked against the official `whatwg/mimesniff` review-drafts directory pinned at commit `39aa53511b13953d84fef8d4131d6f61d0ccbde6`. The retained API response is SHA-256 `2b227abf39c7d45f29e87bacba14f2b7ffbba928bfcf568c58a2ee0dea5581ab`. This check caught the otherwise easy mistake of skipping the 2025-01 Review Draft between 2024-07 and 2025-07.

## Integrity and completeness checks

- 10/10 first downloads returned official HTTPS 200 with zero redirects.
- 10/10 second official downloads were byte-identical to the first and matched the frozen SHA-256 values.
- 10/10 files are non-empty and contain zero NUL bytes.
- WHATWG response `Content-Length` values equal retained file lengths exactly.
- W3C documents contain complete doctype/body/closing-html structure, dated `This Version`, status, and change-log material.
- RFC Editor resources are intentionally HTML fragments wrapping the complete paginated RFC text; terminal page markers and full legal sections are present (pages 80, 87, and 104 respectively).
- WHATWG Bikeshed output does not consistently emit a closing `</html>` tag; completeness is instead established by official `Content-Length`, ETag/Last-Modified, expected terminal generated content, and a byte-identical second fetch. It is not treated as truncated.

## License conclusion

The selected development sources have specific, non-generic redistribution bases:

- RFC snapshots: embedded notices plus [IETF TLP 5.0](https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/) and its [FAQ](https://trustee.ietf.org/documents/trust-legal-provisions/copyright-policy-and-tlp-faq/); complete unmodified distribution with all notices retained.
- W3C snapshots: [W3C Software and Document License, 2015 version](https://www.w3.org/copyright/software-license-2015/); full notice and existing document notices/status must accompany the snapshots.
- WHATWG snapshots: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) under [WHATWG IPR Policy §7.1.1](https://whatwg.org/ipr-policy); attribution, exact source, license link, and unmodified status are required.

The exact evidence hashes and handling conditions are in `LICENSE-INVENTORY.md`. This conclusion is conditional on complete, unmodified snapshot distribution with those notices and is not legal advice.

## Blind whole-document split plan

The policy creates a real conflict if only these three family chains exist: M1 requires at least one whole-document holdout in each family, while M2 forbids any lineage chain from crossing dev/holdout. Assigning one document from every current family chain to holdout therefore forces all three current chains wholly into holdout and leaves no real development chain.

The non-leaking resolution is:

1. Treat all 10 acquired sources above as visible development-only sources; none is eligible for future blind holdout.
2. After the candidate is bound by commit/tree/wheel/sdist/source ZIP/bundle hashes, the independent evaluation owner selects and acquires one **different official chain of at least three consecutive versions per family** in a fresh environment.
3. The identities, URLs, raw hashes, split manifest, labels, and per-case outputs of those extra chains stay unavailable to implementation until policy-authorized reveal.
4. Use whole-chain placement only and reject any raw or derived SHA overlap.

Projected minimum split: 10 development + 9 blind holdout = 19 documents; holdout is 47.37% overall. By family it is RFC 3/6 = 50%, W3C_TR 3/6 = 50%, and WHATWG 3/7 = 42.86%, satisfying the ≥40% rule while preserving entire M2 chains.

The actual blind membership is intentionally not created or disclosed here. Until an independent evaluation owner completes and hash-freezes it, the correct status is `BLOCKED_EXTERNAL`, not M1/M2 pass.

## Deliverables

- `SOURCE-INVENTORY.json`: authoritative source-only inventory and split protocol.
- `LICENSE-INVENTORY.md`: license URLs, basis, notice conditions, and frozen evidence hashes.
- `raw/`: first official bytes.
- `http/`: first-response headers.
- `replay/` and `replay-http/`: independent second official fetches and headers.
- `license-evidence/`: frozen official license/policy pages.
- `chain-evidence-whatwg-mimesniff-review-drafts.json`: pinned official WHATWG directory evidence.
- `policy/`: exact frozen preregistration policy bytes and HTTP headers.

All artifacts are isolated in this staging directory; nothing was copied into the repository or published to GitHub.
