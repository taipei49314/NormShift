#!/usr/bin/env python3
"""Expand expedition: live/official imports, extract, pairs, discovery, observatory."""

from __future__ import annotations

import json
import traceback
from pathlib import Path

from normshift.acquire.fetcher import acquire_url, import_local_bytes
from normshift.acquire.store import SnapshotStore
from normshift.extract.extractor import extract_from_source
from normshift.model.types import AdapterName, ChangeClassification, ProfileName
from normshift.observatory.builder import build_observatory
from normshift.pipeline import run_diff
from normshift.source import load_immutable_source

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / ".normshift" / "store"
POLICY = ROOT / "config" / "source-policy.json"
ART = ROOT / "artifacts" / "expedition"
REAL = ART / "real"
SNAP_META = ROOT / "corpus" / "snapshots"


def main() -> None:
    store = SnapshotStore(STORE)
    REAL.mkdir(parents=True, exist_ok=True)
    SNAP_META.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    live_urls: list[tuple[str, str]] = [
        ("https://www.rfc-editor.org/rfc/rfc8259.html", "ietf-rfc-html"),
        ("https://www.rfc-editor.org/rfc/rfc8949.html", "ietf-rfc-html"),
        ("https://www.rfc-editor.org/rfc/rfc9110.html", "ietf-rfc-html"),
        ("https://www.rfc-editor.org/rfc/rfc3986.html", "ietf-rfc-html"),
        ("https://www.w3.org/TR/2021/REC-trace-context-1-20211123/", "w3c-html"),
        ("https://www.w3.org/TR/trace-context-2/", "w3c-html"),
    ]
    acquired: list[dict] = []
    for url, hint in live_urls:
        try:
            man = acquire_url(
                url, store=store, policy_path=POLICY, adapter_hint=hint
            )
            acquired.append(man)
            print(f"ACQ ok {man['byte_length']:7d} {man['snapshot_id']} {url}")
        except Exception as exc:  # noqa: BLE001
            print(f"ACQ fail {url}: {exc}")

    # Always ensure synthetic fixtures present
    fixtures = [
        (
            ROOT / "fixtures/corpus/rfc/sample-v1.html",
            "https://www.rfc-editor.org/rfc/fixture-rfc-v1.html",
            "ietf-rfc-html",
        ),
        (
            ROOT / "fixtures/corpus/rfc/sample-v2.html",
            "https://www.rfc-editor.org/rfc/fixture-rfc-v2.html",
            "ietf-rfc-html",
        ),
        (
            ROOT / "fixtures/corpus/w3c/sample-v1.html",
            "https://www.w3.org/TR/fixture-w3c-v1/",
            "w3c-html",
        ),
        (
            ROOT / "fixtures/corpus/w3c/sample-v2.html",
            "https://www.w3.org/TR/fixture-w3c-v2/",
            "w3c-html",
        ),
        (
            ROOT / "fixtures/corpus/whatwg/sample-v1.html",
            "https://html.spec.whatwg.org/fixture-v1",
            "whatwg-html",
        ),
        (
            ROOT / "fixtures/corpus/whatwg/sample-v2.html",
            "https://html.spec.whatwg.org/fixture-v2",
            "whatwg-html",
        ),
    ]
    for path, url, hint in fixtures:
        if path.is_file():
            try:
                man = import_local_bytes(
                    path,
                    store=store,
                    source_url=url,
                    policy_path=POLICY,
                    adapter_hint=hint,
                    license_note="in-repo redistributable fixture",
                )
                print(f"IMP ok {man['snapshot_id']} {path.name}")
            except Exception as exc:  # noqa: BLE001
                print(f"IMP fail {path}: {exc}")

    # Write hash-only snapshot index (no full official bytes in-repo)
    index: list[dict] = []
    total_req = 0
    by_family: dict[str, int] = {}
    for sid in store.list_manifests():
        man = store.read_manifest(sid)
        meta = {
            "snapshot_id": man["snapshot_id"],
            "source_url": man.get("source_url"),
            "final_url": man.get("final_url"),
            "content_sha256": man["content_sha256"],
            "byte_length": man["byte_length"],
            "adapter_hint": man.get("adapter_hint"),
            "acquisition_mode": man.get("acquisition_mode"),
            "retrieved_at": man.get("retrieved_at"),
            "license_note": man.get("license_note"),
            "label_authority": "AUTO",
            "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        }
        (SNAP_META / f"{sid}.json").write_text(
            json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        index.append(meta)

        # Materialize for processing (local only)
        raw = store.get_bytes(man["content_sha256"])
        html_path = REAL / f"{sid}.html"
        html_path.write_bytes(raw)

        adapter = AdapterName.AUTO
        url = str(man.get("final_url") or man.get("source_url") or "")
        if "rfc-editor" in url or "ietf" in url:
            adapter = AdapterName.RFC
        elif "w3.org" in url:
            adapter = AdapterName.W3C
        elif "whatwg" in url:
            adapter = AdapterName.WHATWG

        profile = (
            ProfileName.WHATWG if adapter == AdapterName.WHATWG else ProfileName.RFC2119
        )
        try:
            src = load_immutable_source(html_path, adapter=adapter)
            doc = extract_from_source(src, profile)
            n = len(doc.requirements)
            total_req += n
            fam = src.family.value
            by_family[fam] = by_family.get(fam, 0) + n
            meta["requirement_count"] = n
            meta["document_version"] = src.document_version
            meta["family"] = fam
            print(f"EXT {n:4d} req  {sid[:28]}  {url[:50]}")
        except Exception as exc:  # noqa: BLE001
            meta["requirement_count"] = 0
            meta["extract_error"] = str(exc)
            print(f"EXT fail {sid}: {exc}")

        (SNAP_META / f"{sid}.json").write_text(
            json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    (SNAP_META / "index.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "snapshots": index,
                "total_requirement_instances": total_req,
                "by_family": by_family,
                "status": "EXPERIMENTAL_NOT_ADJUDICATED",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    # Pair diffs (fixtures + W3C trace-context if both present)
    discovery: list[dict] = []
    pairs = [
        (
            "rfc-fixture",
            ROOT / "fixtures/corpus/rfc/sample-v1.html",
            ROOT / "fixtures/corpus/rfc/sample-v2.html",
            AdapterName.RFC,
            ProfileName.RFC2119,
        ),
        (
            "w3c-fixture",
            ROOT / "fixtures/corpus/w3c/sample-v1.html",
            ROOT / "fixtures/corpus/w3c/sample-v2.html",
            AdapterName.W3C,
            ProfileName.RFC2119,
        ),
        (
            "whatwg-fixture",
            ROOT / "fixtures/corpus/whatwg/sample-v1.html",
            ROOT / "fixtures/corpus/whatwg/sample-v2.html",
            AdapterName.WHATWG,
            ProfileName.WHATWG,
        ),
    ]

    # Locate trace-context snapshots if acquired
    tc1 = tc2 = None
    for sid in store.list_manifests():
        man = store.read_manifest(sid)
        u = str(man.get("final_url") or "")
        if "trace-context-1" in u or "REC-trace-context-1" in u:
            tc1 = REAL / f"{sid}.html"
        if "trace-context-2" in u or u.rstrip("/").endswith("trace-context-2"):
            tc2 = REAL / f"{sid}.html"
    if tc1 and tc2 and tc1.is_file() and tc2.is_file():
        pairs.append(
            ("w3c-trace-context", tc1, tc2, AdapterName.W3C, ProfileName.RFC2119)
        )

    pair_summaries: list[dict] = []
    for pid, old, new, adapter, profile in pairs:
        if not old.is_file() or not new.is_file():
            continue
        out_json = ART / f"{pid}-report.json"
        out_md = ART / f"{pid}-report.md"
        try:
            # Portable refs relative to a common root containing both inputs
            try:
                old.resolve().relative_to(ROOT)
                new.resolve().relative_to(ROOT)
                sroot = ROOT
            except ValueError:
                sroot = old.parent
            report = run_diff(
                old,
                new,
                profile=profile,
                adapter=adapter,
                json_out=out_json,
                markdown_out=out_md,
                source_root=sroot,
            )
            counts: dict[str, int] = {}
            for ch in report.changes:
                k = ch.classification.value
                counts[k] = counts.get(k, 0) + 1
                if ch.classification in {
                    ChangeClassification.STRENGTHENED,
                    ChangeClassification.WEAKENED,
                    ChangeClassification.POLARITY_FLIP,
                    ChangeClassification.ADDED,
                    ChangeClassification.REMOVED,
                    ChangeClassification.AMBIGUOUS,
                    ChangeClassification.CONDITION_ADDED,
                    ChangeClassification.EXCEPTION_ADDED,
                }:
                    discovery.append(
                        {
                            "id": f"{pid}:{ch.change_id[:12]}",
                            "kind": ch.classification.value,
                            "summary": (ch.new_text or ch.old_text or "")[:160],
                            "evidence": str(out_json.relative_to(ROOT)),
                            "snapshot_hashes": [
                                report.old_document.sha256,
                                report.new_document.sha256,
                            ],
                            "confidence": ch.confidence,
                            "label_authority": "AUTO",
                        }
                    )
            pair_summaries.append(
                {
                    "pair_id": pid,
                    "old_reqs": len(report.old_requirements),
                    "new_reqs": len(report.new_requirements),
                    "changes": len(report.changes),
                    "classification_counts": counts,
                    "report": str(out_json.relative_to(ROOT)),
                }
            )
            print(f"PAIR {pid}: {counts}")
        except Exception as exc:  # noqa: BLE001
            print(f"PAIR fail {pid}: {exc}")
            traceback.print_exc()

    # Sort discovery: substantive first
    priority = {
        "POLARITY_FLIP": 0,
        "STRENGTHENED": 1,
        "WEAKENED": 2,
        "REMOVED": 3,
        "ADDED": 4,
        "AMBIGUOUS": 5,
    }
    discovery.sort(key=lambda d: (priority.get(str(d.get("kind")), 9), d.get("id")))

    # Family pages for observatory
    family_html = {
        "family-ietf.html": _family_page("IETF / RFC", "ietf", index),
        "family-w3c.html": _family_page("W3C", "w3c", index),
        "family-whatwg.html": _family_page("WHATWG", "whatwg", index),
        "pairs.html": _pairs_page(pair_summaries),
    }

    site = ART / "site"
    man = build_observatory(
        store=store,
        out_dir=site,
        title="NormShift Real Standards Observatory",
        discovery=discovery[:200],
        extra_pages=family_html,
    )

    summary = {
        "schema_version": "1.0.0",
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "store_snapshots": len(store.list_manifests()),
        "total_requirement_instances": total_req,
        "requirements_by_family": by_family,
        "pairs": pair_summaries,
        "discovery_items": len(discovery),
        "observatory_files": len(man.get("files") or {}),
        "live_acquired": len(acquired),
    }
    (ART / "corpus-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ART / "discovery_queue.jsonl").write_text(
        "\n".join(json.dumps(d, sort_keys=True) for d in discovery) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


def _family_page(title: str, key: str, index: list[dict]) -> str:
    rows = []
    for m in index:
        url = str(m.get("final_url") or m.get("source_url") or "")
        fam = str(m.get("family") or "")
        match = (
            (key == "ietf" and ("rfc-editor" in url or fam == "rfc"))
            or (key == "w3c" and ("w3.org" in url or fam == "w3c"))
            or (key == "whatwg" and ("whatwg" in url or fam == "whatwg"))
        )
        if not match:
            continue
        rows.append(
            f"<tr><td><code>{m.get('snapshot_id')}</code></td>"
            f"<td>{m.get('requirement_count', '?')}</td>"
            f"<td><code>{str(m.get('content_sha256',''))[:16]}…</code></td>"
            f"<td>{url}</td></tr>"
        )
    body = "".join(rows) or "<tr><td colspan=4>(none)</td></tr>"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>
</head><body>
<h1>{title}</h1>
<p><a href="index.html">Home</a> · EXPERIMENTAL_NOT_ADJUDICATED</p>
<table><tr><th>Snapshot</th><th>Reqs</th><th>SHA</th><th>URL</th></tr>
{body}
</table></body></html>
"""


def _pairs_page(pairs: list[dict]) -> str:
    rows = []
    for p in pairs:
        rows.append(
            f"<tr><td>{p.get('pair_id')}</td><td>{p.get('old_reqs')}→{p.get('new_reqs')}</td>"
            f"<td>{p.get('changes')}</td><td><code>{p.get('report')}</code></td></tr>"
        )
    body = "".join(rows) or "<tr><td colspan=4>(none)</td></tr>"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Pairs</title>
</head><body>
<h1>Version pairs</h1>
<p><a href="index.html">Home</a></p>
<table><tr><th>Pair</th><th>Reqs</th><th>Changes</th><th>Report</th></tr>
{body}
</table></body></html>
"""


if __name__ == "__main__":
    main()
