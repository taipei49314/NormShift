"""Immutable content-addressed snapshot store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from normshift.evidence.hashing import canonical_json_bytes
from normshift.io_safety import atomic_write_bytes, atomic_write_text


class SnapshotStoreError(ValueError):
    pass


class SnapshotStore:
    """Layout: store/objects/sha256/<aa>/<hash> and store/manifests/<id>.json"""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.objects = self.root / "objects" / "sha256"
        self.manifests = self.root / "manifests"
        self.exports = self.root / "exports"

    def ensure(self) -> None:
        self.objects.mkdir(parents=True, exist_ok=True)
        self.manifests.mkdir(parents=True, exist_ok=True)
        self.exports.mkdir(parents=True, exist_ok=True)

    def object_path(self, sha256: str) -> Path:
        return self.objects / sha256[:2] / sha256

    def has_object(self, sha256: str) -> bool:
        return self.object_path(sha256).is_file()

    def put_bytes(self, data: bytes, *, sha256: str) -> Path:
        self.ensure()
        path = self.object_path(sha256)
        if path.is_file():
            existing = path.read_bytes()
            if existing != data:
                raise SnapshotStoreError(
                    f"content-address collision or corruption for {sha256}"
                )
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(path, data)
        return path

    def get_bytes(self, sha256: str) -> bytes:
        path = self.object_path(sha256)
        if not path.is_file():
            raise SnapshotStoreError(f"snapshot object missing: {sha256}")
        return path.read_bytes()

    def write_manifest(self, snapshot_id: str, manifest: dict[str, Any]) -> Path:
        self.ensure()
        path = self.manifests / f"{snapshot_id}.json"
        atomic_write_text(
            path,
            canonical_json_bytes(manifest).decode("utf-8"),
        )
        return path

    def read_manifest(self, snapshot_id: str) -> dict[str, Any]:
        path = self.manifests / f"{snapshot_id}.json"
        if not path.is_file():
            raise SnapshotStoreError(f"manifest not found: {snapshot_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SnapshotStoreError("manifest root must be object")
        return data

    def list_manifests(self) -> list[str]:
        if not self.manifests.is_dir():
            return []
        return sorted(p.stem for p in self.manifests.glob("*.json"))

    def verify_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        man = self.read_manifest(snapshot_id)
        sha = str(man["content_sha256"])
        data = self.get_bytes(sha)
        import hashlib

        dig = hashlib.sha256(data).hexdigest()
        ok = dig == sha and len(data) == int(man["byte_length"])
        return {
            "snapshot_id": snapshot_id,
            "ok": ok,
            "content_sha256": sha,
            "computed_sha256": dig,
            "byte_length": len(data),
            "declared_byte_length": man.get("byte_length"),
        }

    def export_snapshot(self, snapshot_id: str, out_dir: Path) -> Path:
        man = self.read_manifest(snapshot_id)
        sha = str(man["content_sha256"])
        data = self.get_bytes(sha)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        raw_name = man.get("filename") or f"{snapshot_id}.bin"
        raw_path = out_dir / Path(str(raw_name)).name
        atomic_write_bytes(raw_path, data)
        atomic_write_text(
            out_dir / "manifest.json",
            canonical_json_bytes(man).decode("utf-8"),
        )
        return out_dir

    def find_by_sha(self, sha256: str) -> list[str]:
        hits: list[str] = []
        for sid in self.list_manifests():
            man = self.read_manifest(sid)
            if man.get("content_sha256") == sha256:
                hits.append(sid)
        return hits

    def find_by_url(self, url: str) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        for sid in self.list_manifests():
            man = self.read_manifest(sid)
            if man.get("source_url") == url or man.get("final_url") == url:
                hits.append(man)
        return hits
