#!/usr/bin/env python3
"""Generate GitHub-facing demo stats and showcase markdown (offline-capable)."""

from __future__ import annotations

import json
from pathlib import Path

from normshift.acquire.store import SnapshotStore
from normshift.benchmark.real_runner import run_real_benchmark
from normshift.extract.extractor import extract_from_source
from normshift.model.types import AdapterName, ProfileName
from normshift.pipeline import run_diff
from normshift.source import load_immutable_source

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / ".normshift" / "store"
OUT = ROOT / "docs" / "SHOWCASE.md"
STATS = ROOT / "artifacts" / "expedition" / "github_stats.json"


def main() -> None:
    stats: dict = {
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "tagline": "Evidence-backed semantic diff for technical standards",
    }

    # Fixture gold path
    bench = run_real_benchmark(ROOT)
    stats["benchmark_real"] = bench.to_dict()

    # Store extraction density if available
    store = SnapshotStore(STORE)
    req_total = 0
    by_url: list[dict] = []
    for sid in store.list_manifests():
        man = store.read_manifest(sid)
        url = str(man.get("final_url") or "")
        if "fixture" in url:
            continue
        try:
            raw = store.get_bytes(man["content_sha256"])
        except Exception:
            continue
        tmp = ROOT / "artifacts" / "expedition" / "real" / f"{sid}.html"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(raw)
        adapter = AdapterName.RFC
        if "w3.org" in url:
            adapter = AdapterName.W3C
        elif "whatwg" in url:
            adapter = AdapterName.WHATWG
        try:
            src = load_immutable_source(tmp, adapter=adapter)
            doc = extract_from_source(src, ProfileName.RFC2119)
            n = len(doc.requirements)
            req_total += n
            by_url.append(
                {
                    "url": url,
                    "requirements": n,
                    "sha256": man["content_sha256"][:16],
                    "bytes": man["byte_length"],
                }
            )
            print(f"extract {n:4d}  {url[:70]}")
        except Exception as exc:
            print(f"skip {url[:40]} {exc}")

    by_url.sort(key=lambda x: -int(x["requirements"]))
    stats["live_extractions"] = by_url
    stats["live_requirement_total"] = req_total

    # Killer pair: trace context if present
    tc = [x for x in by_url if "trace-context" in x["url"]]
    stats["trace_context_docs"] = len(tc)

    # Synthetic showcase pair always
    r = run_diff(
        ROOT / "fixtures/corpus/rfc/sample-v1.html",
        ROOT / "fixtures/corpus/rfc/sample-v2.html",
        profile=ProfileName.RFC2119,
        adapter=AdapterName.RFC,
        source_root=ROOT,
    )
    stats["showcase_pair"] = {
        "old": len(r.old_requirements),
        "new": len(r.new_requirements),
        "changes": [
            {
                "class": c.classification.value,
                "confidence": c.confidence,
                "old": (c.old_text or "")[:80],
                "new": (c.new_text or "")[:80],
            }
            for c in r.changes
            if c.classification.value not in {"UNCHANGED", "EDITORIAL"}
        ],
    }

    STATS.parent.mkdir(parents=True, exist_ok=True)
    STATS.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# NormShift Showcase",
        "",
        "> Evidence-backed **semantic diff** for technical standards.",
        "> Deterministic. Offline-replayable. No LLM as authority.",
        "",
        "## Why this matters",
        "",
        "Standards change quietly. A SHOULD becomes a MUST. A condition appears.",
        "An exception vanishes. Teams ship against the wrong obligation.",
        "",
        "NormShift turns two HTML snapshots into an **evidence-linked change report**",
        "you can re-verify from source bytes — without trusting a chat model.",
        "",
        "## Headline numbers (expedition run)",
        "",
        f"- Live official documents processed: **{len(by_url)}**",
        f"- Normative requirement instances extracted: **{req_total}**",
        f"- Provisional real benchmark: **{bench.passed}/{bench.total}**",
        "",
        "### Top extractions",
        "",
        "| Requirements | Document |",
        "|-------------:|----------|",
    ]
    for row in by_url[:8]:
        lines.append(f"| {row['requirements']} | `{row['url']}` |")

    lines += [
        "",
        "## Semantic change example (fixture RFC-like pair)",
        "",
        "```text",
    ]
    for ch in stats["showcase_pair"]["changes"]:
        lines.append(f"{ch['class']}  conf={ch['confidence']}")
        if ch["old"]:
            lines.append(f"  - old: {ch['old']}")
        if ch["new"]:
            lines.append(f"  + new: {ch['new']}")
        lines.append("")
    lines += [
        "```",
        "",
        "## Trust properties",
        "",
        "| Property | Behavior |",
        "|----------|----------|",
        "| Source identity | Content SHA-256 + portable refs |",
        "| Verify | Strict JSON + full pipeline replay |",
        "| Offline | Analysis path needs no network |",
        "| Authority | Explicit AUTO/PROVISIONAL labels only |",
        "| Ambiguity | Surfaced, not silently forced |",
        "",
        "## One-command demo",
        "",
        "```bash",
        "uv sync --frozen --all-extras --dev",
        "uv run normshift diff fixtures/corpus/rfc/sample-v1.html \\",
        "  fixtures/corpus/rfc/sample-v2.html --source-root . --adapter rfc \\",
        "  --json /tmp/ns.json --markdown /tmp/ns.md",
        "uv run normshift verify /tmp/ns.json --source-root .",
        "uv run normshift benchmark --ground-truth benchmark/ground_truth.jsonl",
        "```",
        "",
        "## Expedition mode",
        "",
        "Branch `expedition/real-standards-observatory` adds:",
        "",
        "- HTTPS allowlisted acquisition store",
        "- Multi-version lineage (SQLite + JSONL)",
        "- Static local observatory + discovery feed",
        "",
        "See `docs/EXPEDITION_CHARTER.md` and `artifacts/expedition/EXPEDITION_EVIDENCE.md`.",
        "",
        "---",
        "",
        "*Not production-ready. Not externally audit-passed. Experimental where stated.*",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"wrote {STATS}")
    print(f"live_req_total={req_total} docs={len(by_url)}")


if __name__ == "__main__":
    main()
