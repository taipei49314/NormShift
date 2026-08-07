"""Observatory as verified projection of campaign run assets."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from normshift.evidence.hashing import canonical_json_bytes
from normshift.io_safety import atomic_write_text


def _sha_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def project_observatory(
    *,
    out_dir: Path,
    campaign_id: str,
    snapshots: list[dict[str, Any]],
    discovery: list[dict[str, Any]],
    pair_ids: list[str],
    metrics: dict[str, Any],
    packet_count: int,
    source_date_epoch: int | None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pairs").mkdir(exist_ok=True)
    (out_dir / "review").mkdir(exist_ok=True)

    epoch_note = f"source_date_epoch={source_date_epoch}"
    pages: dict[str, str] = {}

    pages["index.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Foundry Observatory</title></head><body>
<h1>Corpus Foundry Observatory</h1>
<p class="badge">EXPERIMENTAL_NOT_ADJUDICATED · AUTO proposals only</p>
<p>Campaign: <code>{campaign_id}</code> · {epoch_note}</p>
<ul>
<li><a href="corpus.html">Corpus</a></li>
<li><a href="snapshots.html">Snapshots</a></li>
<li><a href="pairs.html">Pairs</a></li>
<li><a href="discovery.html">Discovery</a></li>
<li><a href="review/index.html">Review workbench</a></li>
<li><a href="lineage.html">Lineage</a></li>
<li><a href="metrics.html">Metrics</a></li>
<li><a href="limitations.html">Limitations</a></li>
<li><a href="feed.json">feed.json</a></li>
</ul>
<p>Snapshots: {len(snapshots)} · Discovery: {len(discovery)} · Packets: {packet_count}</p>
</body></html>
"""

    pages["corpus.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Corpus</title></head><body>
<h1>Corpus</h1><p><a href="index.html">Home</a></p>
<pre>{canonical_json_bytes(metrics.get("layer_b_real_provisional", {})).decode()}</pre>
</body></html>
"""

    srows = "".join(
        f"<tr><td>{s.get('snapshot_key')}</td><td>{s.get('version_label')}</td>"
        f"<td><code>{str(s.get('content_sha256',''))[:16]}</code></td>"
        f"<td>{s.get('byte_length')}</td></tr>"
        for s in snapshots
    )
    pages["snapshots.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Snapshots</title></head><body>
<h1>Snapshots</h1><p><a href="index.html">Home</a></p>
<table><tr><th>Key</th><th>Version</th><th>SHA</th><th>Bytes</th></tr>
{srows}</table></body></html>
"""

    prows = "".join(
        f'<tr><td><a href="pairs/{pid}.html">{pid}</a></td></tr>' for pid in pair_ids
    )
    pages["pairs.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Pairs</title></head><body>
<h1>Pairs</h1><p><a href="index.html">Home</a></p>
<table>{prows}</table></body></html>
"""
    for pid in pair_ids:
        pages[f"pairs/{pid}.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{pid}</title></head><body>
<h1>Pair {pid}</h1>
<p><a href="../pairs.html">Pairs</a></p>
<ul>
<li>Capsule: <code>capsules/{pid}/capsule.json</code></li>
<li>Report: <code>capsules/{pid}/report/report.json</code></li>
<li>Review packets: campaign review set</li>
<li>Authority: AUTO</li>
<li>Offline replay: see capsule.offline_replay</li>
</ul></body></html>
"""

    drows = "".join(
        f"<tr><td>{d.get('id')}</td><td>{d.get('kind')}</td>"
        f"<td>AUTO</td><td>{d.get('summary')}</td></tr>"
        for d in discovery[:200]
    )
    pages["discovery.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Discovery</title></head><body>
<h1>Discovery ({len(discovery)})</h1>
<p>All items AUTO / UNREVIEWED — not adjudicated.</p>
<table><tr><th>ID</th><th>Class</th><th>Auth</th><th>Summary</th></tr>
{drows}</table></body></html>
"""

    pages["review/index.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Review</title></head><body>
<h1>Review workbench</h1>
<p>Packets: {packet_count} · Decisions: import external ledger only</p>
<ul>
<li><a href="queue.html">Queue</a></li>
<li><a href="conflicts.html">Conflicts</a></li>
<li><a href="instructions.html">Instructions</a></li>
</ul></body></html>
"""
    pages["review/queue.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Queue</title></head><body>
<h1>Review queue</h1>
<p>See artifacts/foundry-24h/review/packets.jsonl</p>
</body></html>
"""
    pages["review/conflicts.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Conflicts</title></head><body>
<h1>Conflicts</h1><p>No external decisions imported.</p></body></html>
"""
    pages["review/instructions.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Instructions</title></head><body>
<h1>Review instructions</h1>
<p>External reviewers append ReviewDecision records. Implementer must not mint EXTERNAL_* authority.</p>
</body></html>
"""
    pages["lineage.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Lineage</title></head><body>
<h1>Lineage candidates</h1>
<p>See artifacts/foundry-24h/lineage/*.candidates.jsonl (AUTO).</p>
</body></html>
"""
    pages["metrics.html"] = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Metrics</title></head><body>
<h1>Metrics</h1>
<p>Layer C: NOT_AVAILABLE (no external review).</p>
<pre>{canonical_json_bytes(metrics).decode()[:4000]}</pre>
</body></html>
"""
    pages["provenance.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Provenance</title></head><body>
<h1>Provenance</h1>
<p>Official bytes may be local-only. Thin capsules declare offline_replay=false.</p>
</body></html>
"""
    pages["limitations.html"] = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Limitations</title></head><body>
<h1>Limitations</h1>
<ul>
<li>AUTO ≠ gold</li>
<li>Deferred M0 audit debt open</li>
<li>Split/merge are candidates only</li>
</ul></body></html>
"""

    feed = {
        "schema_version": "1.0.0",
        "campaign_id": campaign_id,
        "source_date_epoch": source_date_epoch,
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "discovery_count": len(discovery),
        "items": [
            {
                "id": d.get("id"),
                "kind": d.get("kind"),
                "label_authority": "AUTO",
                "href": "discovery.html",
            }
            for d in discovery
        ],
    }
    pages["feed.json"] = canonical_json_bytes(feed).decode("utf-8")
    pages["feed.xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<feed>\n'
        + "\n".join(
            f"<item><id>{d.get('id')}</id><kind>{d.get('kind')}</kind></item>"
            for d in discovery[:100]
        )
        + "\n</feed>\n"
    )

    file_hashes: dict[str, str] = {}
    for name, content in sorted(pages.items()):
        path = out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, content)
        file_hashes[name] = _sha_text(content)

    man = {
        "schema_version": "1.0.0",
        "campaign_id": campaign_id,
        "source_date_epoch": source_date_epoch,
        "status": "EXPERIMENTAL_NOT_ADJUDICATED",
        "snapshot_count": len(snapshots),
        "discovery_count": len(discovery),
        "pair_count": len(pair_ids),
        "packet_count": packet_count,
        "files": file_hashes,
        "offline": True,
    }
    atomic_write_text(
        out_dir / "manifest.json", canonical_json_bytes(man).decode("utf-8")
    )
    return man
