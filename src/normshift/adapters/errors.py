"""Adapter error types (fail closed — never emit success artifacts)."""

from __future__ import annotations


class AdapterError(Exception):
    """Raised when a source adapter cannot produce a valid document load."""

    def __init__(self, message: str, *, adapter_id: str | None = None) -> None:
        self.adapter_id = adapter_id
        super().__init__(message)


class AdapterDetectionError(AdapterError):
    """Raised when family auto-detection fails or is ambiguous."""


class AdapterParseError(AdapterError):
    """Raised when bytes cannot be parsed by the selected adapter."""
