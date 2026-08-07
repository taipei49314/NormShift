"""Static offline observatory site generator."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from normshift.acquire.store import SnapshotStore
from normshift.evidence.hashing import canonical_json_bytes
from normshift.io_safety import atomic_write_text


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_observatory(
    *,
    store: SnapshotStore,
    out_dir: Path,
    title: str = "NormShift Real Standards Observatory",
    discovery: list[dict[str, Any]] | None = None,
    extra_pages: dict[str, str] | None = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    discovery = discovery or []
    pages: dict[str, str] = {}

    snaps = []
    for sid in store.list_manifests():
        man = store.read_manifest(sid)
        snaps.append(man)

    index = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:2rem;max-width:960px;line-height:1.45}}
code,pre{{background:#f4f4f4;padding:.1rem .3rem}}
table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #ccc;padding:.4rem;text-align:left}}
.badge{{display:inline-block;background:#eee;padding:.1rem .4rem;border-radius:4px}}
</style></head><body>
<h1>{title}</h1>
<p class="badge">EXPERIMENTAL_NOT_ADJUDICATED</p>
<p>Local-first observatory over frozen snapshots. Offline build. No remote AI authority.</p>
<ul>
<li><a href="snapshots.html">Source snapshot inventory</a></li>
<li><a href="discovery.html">Discovery queue</a></li>
<li><a href="pairs.html">Version pairs</a> (if generated)</li>
<li><a href="family-ietf.html">IETF family</a> ·
    <a href="family-w3c.html">W3C</a> ·
    <a href="family-whatwg.html">WHATWG</a></li>
<li><a href="limitations.html">Known limitations</a></li>
<li><a href="provenance.html">Provenance and licenses</a></li>
<li><a href="feed.json">Machine-readable feed (JSON)</a></li>
<li><a href="feed.xml">Machine-readable feed (XML)</a></li>
<li><a href="manifest.json">Site manifest</a></li>
</ul>
<h2>Corpus overview</h2>
<p>Snapshots in store: <strong>{len(snaps)}</strong></p>
<p>Discovery items: <strong>{len(discovery)}</strong> (AUTO/PROVISIONAL)</p>
</body></html>
"""
    pages["index.html"] = index

    rows = []
    for m in snaps:
        rows.append(
            f"<tr><td><code>{m.get('snapshot_id')}</code></td>"
            f"<td>{m.get('final_url') or m.get('source_url')}</td>"
            f"<td><code>{m.get('content_sha256','')[:16]}…</code></td>"
            f"<td>{m.get('byte_length')}</td></tr>"
        )
    pages["snapshots.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Snapshots</title></head><body>
<h1>Source snapshot inventory</h1>
<p><a href="index.html">Home</a></p>
<table><tr><th>ID</th><th>URL</th><th>SHA-256</th><th>Bytes</th></tr>
{"".join(rows)}
</table></body></html>
"""

    drows = []
    for i, item in enumerate(discovery):
        drows.append(
            f"<tr><td>{i}</td><td>{item.get('kind')}</td>"
            f"<td>{item.get('summary')}</td>"
            f"<td><code>{item.get('evidence','')}</code></td></tr>"
        )
    pages["discovery.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Discovery</title></head><body>
<h1>Discovery queue</h1>
<p><a href="index.html">Home</a></p>
<p>All items are AUTO/PROVISIONAL — not adjudicated.</p>
<table><tr><th>#</th><th>Kind</th><th>Summary</th><th>Evidence</th></tr>
{"".join(drows) if drows else "<tr><td colspan=4>(empty)</td></tr>"}
</table></body></html>
"""

    pages["limitations.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Limitations</title></head><body>
<h1>Known limitations</h1>
<p><a href="index.html">Home</a></p>
<ul>
<li>M0 deferred audit debt remains open on the R4 baseline.</li>
<li>Labels are AUTO/PROVISIONAL only.</li>
<li>Split/merge candidates are experimental.</li>
<li>No LLM authority; no hosted services.</li>
</ul></body></html>
"""

    pages["provenance.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Provenance</title></head><body>
<h1>Provenance and licenses</h1>
<p><a href="index.html">Home</a></p>
<p>Official standards bytes remain under their respective licenses.
When redistribution is unclear, the store holds content-addressed objects
locally; the repository may only commit acquisition manifests and hashes.</p>
</body></html>
"""

    if extra_pages:
        pages.update(extra_pages)

    feed_items = []
    for item in discovery:
        feed_items.append(
            {
                "id": item.get("id") or _sha_text(json.dumps(item, sort_keys=True))[:16],
                "kind": item.get("kind"),
                "summary": item.get("summary"),
                "evidence": item.get("evidence"),
                "snapshot_hashes": item.get("snapshot_hashes") or [],
                "href": "discovery.html",
                "label_authority": "AUTO",
            }
        )
    feed = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "items": feed_items,
    }
    feed_json = canonical_json_bytes(feed).decode("utf-8")
    pages["feed.json"] = feed_json

    xml_items = []
    for it in feed_items:
        xml_items.append(
            f"<item><id>{it['id']}</id><kind>{it.get('kind')}</kind>"
            f"<summary>{it.get('summary')}</summary>"
            f"<link>{it.get('href')}</link></item>"
        )
    pages["feed.xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<feed>\n'
        + "\n".join(xml_items)
        + "\n</feed>\n"
    )

    file_hashes: dict[str, str] = {}
    for name, content in sorted(pages.items()):
        atomic_write_text(out_dir / name, content)
        file_hashes[name] = _sha_text(content)

    # Page hashes only (exclude self-referential manifest.json hash)
    man_final = {
        "schema_version": "1.0.0",
        "title": title,
        "generated_at": feed["generated_at"],
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "snapshot_count": len(snaps),
        "discovery_count": len(discovery),
        "files": file_hashes,
        "offline": True,
    }
    atomic_write_text(out_dir / "manifest.json", canonical_json_bytes(man_final).decode("utf-8"))
    return man_final


def verify_observatory_manifest(site_dir: Path) -> dict[str, Any]:
    site_dir = Path(site_dir)
    man_path = site_dir / "manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for name, expected in (man.get("files") or {}).items():
        if name == "manifest.json":
            continue  # never self-hash
        p = site_dir / name
        if not p.is_file():
            errors.append(f"missing {name}")
            continue
        # Hash raw file bytes for stability across newline normalizations
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        # files map stores text-sha; recompute consistently
        got_text = _sha_text(p.read_text(encoding="utf-8"))
        if got_text != expected and got != expected:
            errors.append(f"hash mismatch {name}")
    return {"ok": len(errors) == 0, "errors": errors, "file_count": len(man.get("files") or {})}
