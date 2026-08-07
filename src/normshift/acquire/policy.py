"""Source policy loading and host allowlist checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class PolicyError(ValueError):
    pass


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Minimal YAML subset loader for expedition config (no PyYAML dependency)."""
    # Prefer JSON if the file is actually JSON
    stripped = text.lstrip()
    if stripped.startswith("{"):
        import json

        data = json.loads(text)
        if not isinstance(data, dict):
            raise PolicyError("policy root must be object")
        return data
    # Very small subset: top-level keys, nested one level, lists of scalars
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(0, root)]
    pending_key: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]
        if line.startswith("- "):
            val = line[2:].strip().strip('"').strip("'")
            if pending_key is not None and isinstance(cur, dict):
                lst = cur.setdefault(pending_key, [])
                if not isinstance(lst, list):
                    raise PolicyError(f"expected list for {pending_key}")
                lst.append(_scalar(val))
            elif isinstance(cur, list):
                cur.append(_scalar(val))
            continue
        if ":" in line:
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest == "":
                # nested map or list follows
                if isinstance(cur, dict):
                    nxt: dict[str, Any] = {}
                    cur[key] = nxt
                    stack.append((indent + 2, nxt))
                    pending_key = None
                continue
            if isinstance(cur, dict):
                if rest.startswith("[") and rest.endswith("]"):
                    inner = rest[1:-1].strip()
                    cur[key] = (
                        [_scalar(x.strip()) for x in inner.split(",") if x.strip()]
                        if inner
                        else []
                    )
                else:
                    cur[key] = _scalar(rest)
                pending_key = key if cur[key] == [] else None
                if rest == "[]":
                    cur[key] = []
            continue
    return root


def _scalar(s: str) -> Any:
    if s in {"true", "True"}:
        return True
    if s in {"false", "False"}:
        return False
    if s.isdigit():
        return int(s)
    return s.strip('"').strip("'")


def load_policy(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PolicyError(f"source policy not found: {path}")
    data = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PolicyError("source policy root must be a mapping")
    return data


def allowed_hosts(policy: dict[str, Any]) -> set[str]:
    hosts: set[str] = set()
    domains = policy.get("domains") or {}
    if not isinstance(domains, dict):
        return hosts
    for _family, cfg in domains.items():
        if not isinstance(cfg, dict):
            continue
        for h in cfg.get("hosts") or []:
            hosts.add(str(h).lower())
    return hosts


def assert_url_allowed(url: str, policy: dict[str, Any]) -> None:
    parsed = urlparse(url)
    if policy.get("allow_https_only", True) and parsed.scheme != "https":
        raise PolicyError(f"only https allowed: {url}")
    host = (parsed.hostname or "").lower()
    hosts = allowed_hosts(policy)
    if host not in hosts:
        raise PolicyError(f"host not allowlisted: {host} (url={url})")
