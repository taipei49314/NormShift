"""HTTPS acquisition from allowlisted official domains."""

from __future__ import annotations

import hashlib
import ssl
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from normshift.acquire.policy import PolicyError, assert_url_allowed, load_policy
from normshift.acquire.store import SnapshotStore

# re-export
__all__ = ["AcquisitionError", "acquire_url", "import_local_bytes", "load_policy"]


class AcquisitionError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def acquire_url(
    url: str,
    *,
    store: SnapshotStore,
    policy_path: Path,
    adapter_hint: str | None = None,
    license_note: str | None = None,
    offline_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Acquire URL into store. If offline_bytes provided, skip network (import)."""
    policy = load_policy(policy_path)
    try:
        assert_url_allowed(url, policy)
    except PolicyError as exc:
        raise AcquisitionError(str(exc)) from exc

    max_bytes = int(policy.get("max_bytes") or 50 * 1024 * 1024)
    redirects: list[str] = []
    final_url = url
    headers_out: dict[str, str] = {}
    status_code = 200

    if offline_bytes is not None:
        raw = offline_bytes
        headers_out = {"content-type": "application/octet-stream"}
    else:
        raw, final_url, redirects, headers_out, status_code = _https_get(
            url, policy=policy, max_bytes=max_bytes
        )

    if not raw:
        raise AcquisitionError("empty body")
    if len(raw) > max_bytes:
        raise AcquisitionError(f"body exceeds max_bytes ({max_bytes})")

    ctype = headers_out.get("content-type", headers_out.get("Content-Type", ""))
    allowed_types = policy.get("allowed_content_types") or []
    if allowed_types and ctype:
        base = ctype.split(";")[0].strip().lower()
        allowed = {str(x).lower() for x in allowed_types}
        if base and base not in allowed and base not in {"application/octet-stream"}:
            raise AcquisitionError(f"unsupported content-type: {ctype}")

    dig = hashlib.sha256(raw).hexdigest()
    store.put_bytes(raw, sha256=dig)

    # same URL different bytes / different URL same bytes
    prior_url = store.find_by_url(url)
    same_url_diff = [
        m
        for m in prior_url
        if m.get("content_sha256") != dig and m.get("source_url") == url
    ]
    same_bytes_diff_url = [
        sid
        for sid in store.find_by_sha(dig)
        if store.read_manifest(sid).get("source_url") not in {url, final_url}
    ]

    snapshot_id = f"snap_{dig[:16]}_{uuid.uuid4().hex[:8]}"
    filename = Path(urlparse(final_url).path).name or f"{snapshot_id}.bin"
    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "snapshot_id": snapshot_id,
        "source_url": url,
        "final_url": final_url,
        "redirects": redirects,
        "status_code": status_code,
        "content_type": ctype,
        "etag": headers_out.get("etag") or headers_out.get("ETag"),
        "last_modified": headers_out.get("last-modified")
        or headers_out.get("Last-Modified"),
        "content_sha256": dig,
        "byte_length": len(raw),
        "retrieved_at": _now_iso(),
        "adapter_hint": adapter_hint,
        "license_note": license_note
        or "See official source; redistribution may be restricted.",
        "filename": filename,
        "acquisition_mode": "offline_import" if offline_bytes is not None else "https",
        "observations": {
            "same_url_different_bytes_prior": [m["snapshot_id"] for m in same_url_diff],
            "same_bytes_different_url_prior": same_bytes_diff_url,
        },
    }
    store.write_manifest(snapshot_id, manifest)
    return manifest


def import_local_bytes(
    path: Path,
    *,
    store: SnapshotStore,
    source_url: str,
    policy_path: Path,
    adapter_hint: str | None = None,
    license_note: str | None = None,
) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    return acquire_url(
        source_url,
        store=store,
        policy_path=policy_path,
        adapter_hint=adapter_hint,
        license_note=license_note,
        offline_bytes=raw,
    )


def _https_get(
    url: str,
    *,
    policy: dict[str, Any],
    max_bytes: int,
) -> tuple[bytes, str, list[str], dict[str, str], int]:
    max_redirects = int(policy.get("max_redirects") or 5)
    current = url
    redirects: list[str] = []
    ctx = ssl.create_default_context()

    for _ in range(max_redirects + 1):
        try:
            assert_url_allowed(current, policy)
        except PolicyError as exc:
            raise AcquisitionError(str(exc)) from exc
        req = Request(
            current,
            headers={"User-Agent": "NormShift-Expedition/0.1 (+local research)"},
            method="GET",
        )
        try:
            with urlopen(req, context=ctx, timeout=60) as resp:  # noqa: S310
                status = getattr(resp, "status", 200) or 200
                headers = {k.lower(): v for k, v in resp.headers.items()}
                # Manual redirect tracking if urllib follows automatically
                final = resp.geturl()
                if final != current:
                    redirects.append(final)
                try:
                    assert_url_allowed(final, policy)
                except PolicyError as exc:
                    raise AcquisitionError(
                        f"redirect outside allowlist: {final}"
                    ) from exc
                chunks: list[bytes] = []
                total = 0
                while True:
                    block = resp.read(64 * 1024)
                    if not block:
                        break
                    total += len(block)
                    if total > max_bytes:
                        raise AcquisitionError("download exceeded max_bytes")
                    chunks.append(block)
                return b"".join(chunks), final, redirects, headers, int(status)
        except HTTPError as exc:
            if exc.code in {301, 302, 303, 307, 308}:
                loc = exc.headers.get("Location")
                if not loc:
                    raise AcquisitionError(f"redirect without Location: {exc.code}") from exc
                redirects.append(loc)
                current = loc
                continue
            if exc.code == 304:
                raise AcquisitionError("304 Not Modified without local cache body") from exc
            raise AcquisitionError(f"HTTP error {exc.code}: {url}") from exc
        except URLError as exc:
            raise AcquisitionError(f"network error: {exc}") from exc

    raise AcquisitionError(f"too many redirects (>{max_redirects})")
