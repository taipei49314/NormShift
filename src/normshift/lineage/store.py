"""SQLite working store + canonical JSONL export for requirement lineage."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from normshift.io_safety import atomic_write_bytes

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nodes (
  node_id TEXT PRIMARY KEY,
  node_type TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS edges (
  edge_id TEXT PRIMARY KEY,
  edge_type TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
"""


class LineageStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def put_node(self, node_id: str, node_type: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO nodes(node_id, node_type, payload_json) VALUES (?,?,?)",
            (node_id, node_type, json.dumps(payload, sort_keys=True, ensure_ascii=False)),
        )
        self.conn.commit()

    def put_edge(self, edge_id: str, edge_type: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO edges(edge_id, edge_type, payload_json) VALUES (?,?,?)",
            (edge_id, edge_type, json.dumps(payload, sort_keys=True, ensure_ascii=False)),
        )
        self.conn.commit()

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?,?)", (key, value)
        )
        self.conn.commit()

    def export_jsonl(self, path: Path) -> bytes:
        """Deterministic JSONL: meta, then nodes sorted, then edges sorted."""
        lines: list[str] = []
        meta_rows = self.conn.execute(
            "SELECT key, value FROM meta ORDER BY key"
        ).fetchall()
        lines.append(
            json.dumps(
                {"record": "meta", "entries": {k: v for k, v in meta_rows}},
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        for node_id, node_type, payload in self.conn.execute(
            "SELECT node_id, node_type, payload_json FROM nodes ORDER BY node_id"
        ):
            obj = {
                "record": "node",
                "node_id": node_id,
                "node_type": node_type,
                "payload": json.loads(payload),
            }
            lines.append(
                json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            )
        for edge_id, edge_type, payload in self.conn.execute(
            "SELECT edge_id, edge_type, payload_json FROM edges ORDER BY edge_id"
        ):
            obj = {
                "record": "edge",
                "edge_id": edge_id,
                "edge_type": edge_type,
                "payload": json.loads(payload),
            }
            lines.append(
                json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            )
        raw = ("\n".join(lines) + "\n").encode("utf-8")
        atomic_write_bytes(Path(path), raw)
        return raw

    def counts(self) -> dict[str, int]:
        n = self.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        e = self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        return {"nodes": int(n), "edges": int(e)}
