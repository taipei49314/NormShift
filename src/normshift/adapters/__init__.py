"""Source adapters (M1: local HTML/XML families with provenance)."""

from normshift.adapters.errors import AdapterDetectionError, AdapterError, AdapterParseError
from normshift.adapters.registry import load_document

__all__ = [
    "AdapterDetectionError",
    "AdapterError",
    "AdapterParseError",
    "load_document",
]
