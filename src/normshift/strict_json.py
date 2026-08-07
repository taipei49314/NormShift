"""Strict JSON parsing for evidence boundary (no coercion, no duplicate keys)."""

from __future__ import annotations

import json
from typing import Any


class StrictJSONError(ValueError):
    """Raised when submitted JSON is non-canonical or ambiguous."""


def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise StrictJSONError(f"Duplicate JSON object key: {k!r}")
        out[k] = v
    return out


def _reject_constant(s: str) -> None:
    raise StrictJSONError(f"Non-finite or forbidden JSON constant: {s!r}")


def strict_loads(raw: str | bytes) -> Any:
    """Parse JSON rejecting duplicate keys and NaN/Infinity."""
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs_hook,
            parse_constant=_reject_constant,
        )
    except StrictJSONError:
        raise
    except json.JSONDecodeError as exc:
        raise StrictJSONError(f"Invalid JSON: {exc}") from exc


def deep_require_keys(obj: Any, template: Any, path: str = "$") -> None:
    """Ensure every key present in template is present in obj (field presence)."""
    if isinstance(template, dict):
        if not isinstance(obj, dict):
            raise StrictJSONError(f"{path}: expected object")
        for k, tv in template.items():
            if k not in obj:
                raise StrictJSONError(f"{path}: missing required field {k!r}")
            deep_require_keys(obj[k], tv, f"{path}.{k}")
    elif isinstance(template, list):
        if not isinstance(obj, list):
            raise StrictJSONError(f"{path}: expected array")
        if template:
            for i, item in enumerate(obj):
                deep_require_keys(item, template[0], f"{path}[{i}]")
