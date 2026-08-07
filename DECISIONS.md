# Design Decisions (M0)

## D008 — Official North Star charter adopted as source of truth

**Decision:** Replace the short M0 north-star stub with the full
`NORMSHIFT_NORTH_STAR` charter under `docs/NORTH_STAR.md`.  
**Why:** Defines end-state Requirement Lineage Graph, milestone gates M0–M6,
trust model, and implementer authority limits.  
**Implication:** After M0 audit, work proceeds only via frozen milestone exits;
LLM may never be classification authority on the correctness path.  
**Status:** Accepted 2026-08-07.

## D001 — Package build backend: hatchling instead of uv_build

**Decision:** Use `hatchling` as the build backend.  
**Why:** Standard packaging layout with `src/normshift` and reliable console
script entry points across environments.  
**Alternative considered:** Keep `uv_build` from `uv init`.  
**Status:** Accepted for M0.

## D002 — Alignment algorithm: greedy multi-signal, not Hungarian

**Decision:** Score all pairs, sort deterministically, greedy match with
ambiguity margin.  
**Why:** Simpler, fully deterministic, sufficient for M0 fixture sizes;
exposes score components per pair.  
**Alternative:** Hungarian algorithm for global optimum.  
**Status:** Accepted for M0; revisit if large-doc recall suffers.

## D003 — One requirement per keyword hit per block

**Decision:** Each normative keyword match in a block yields a requirement.  
**Why:** Preserves multi-modal sentences; stable ordering by match offset.  
**Risk:** Rare double-counting if a sentence uses two keywords intentionally.  
**Status:** Accepted; AMBIGUOUS available when classification is unclear.

## D004 — Informative region detection is structural + class/role

**Decision:** Ignore `pre`/`code`/… tags and elements with example/note/informative
classes or `data-normative=false`.  
**Why:** Deterministic without NLP; covers adversarial case 10.  
**Limitation:** Specs that place normative text only inside custom widgets may
be under-extracted.

## D005 — Report integrity hash excludes `integrity` field

**Decision:** `content_sha256` is SHA-256 of canonical JSON of the report with
the `integrity` key removed.  
**Why:** Avoids self-referential hash; enables tamper detection.

## D006 — Document version from meta/content, never filename alone

**Decision:** Prefer `<meta name="version">`, `data-version`, H1 version tokens;
fallback `sha256:` prefix of content digest.  
**Why:** Mission forbids filename-as-sole version identity.

## D007 — jsonschema retained for optional schema verification

**Decision:** Keep `jsonschema` dependency for `report.schema.json` checks in
`normshift verify`.  
**Why:** Complements Pydantic runtime models with portable JSON Schema artifacts.
