"""Public canonical item identity for blind gold/prediction matching."""

from __future__ import annotations

import hashlib
import unicodedata

from normshift.evidence.hashing import canonical_json_bytes
from normshift.portable_ref import validate_portable_ref

MAX_SOURCE_REF_LENGTH = 768
MAX_LOCATOR_LENGTH = 1024
WINDOWS_RESERVED_STEMS = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


def _validate_text_identity(value: str, *, label: str, maximum: int) -> str:
    if not value or len(value) > maximum:
        raise ValueError(f"{label} length is outside 1..{maximum}")
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError(f"{label} must use NFC Unicode normalization")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError(f"{label} contains a control/format/unassigned character")
    return value


def validate_portable_source_ref(value: str) -> str:
    """Validate a bounded canonical source path used by the scorer boundary."""
    _validate_text_identity(value, label="portable source ref", maximum=MAX_SOURCE_REF_LENGTH)
    validate_portable_ref(value)
    for segment in value.split("/"):
        if segment.endswith((".", " ")):
            raise ValueError("portable source ref has a trailing dot/space alias")
        if any(character in '<>:"|?*' for character in segment):
            raise ValueError("portable source ref contains a Windows-forbidden character")
        if segment.split(".", 1)[0].casefold() in WINDOWS_RESERVED_STEMS:
            raise ValueError("portable source ref contains a Windows reserved device name")
    return value


def validate_portable_locator(value: str) -> str:
    """Validate ``relative/source/ref[#ASCII-fragment]`` without host aliases."""
    _validate_text_identity(value, label="portable locator", maximum=MAX_LOCATOR_LENGTH)
    if value.count("#") > 1:
        raise ValueError("portable locator must contain at most one fragment delimiter")
    source_ref, delimiter, fragment = value.partition("#")
    validate_portable_source_ref(source_ref)
    if delimiter:
        if not fragment:
            raise ValueError("portable locator fragment must be non-empty")
        if any(ord(character) < 0x21 or ord(character) > 0x7E for character in fragment):
            raise ValueError("portable locator fragment must be printable ASCII without spaces")
        if "\\" in fragment or "#" in fragment:
            raise ValueError("portable locator fragment contains a forbidden character")
    return value


def locator_source_ref(value: str) -> str:
    """Return the already-validated source-ref portion of a portable locator."""
    validate_portable_locator(value)
    return value.partition("#")[0]


def acceptance_item_key(
    *,
    task: str,
    evaluation_slot: str,
    source_sha256s: list[str],
    portable_locators: list[str],
) -> str:
    """Derive a label-independent key from immutable evidence identity."""
    if len(source_sha256s) != len(portable_locators) or not source_sha256s:
        raise ValueError("item-key evidence lists must be non-empty and equal length")
    payload = {
        "evaluation_slot": evaluation_slot,
        "evidence": [
            {"portable_locator": locator, "source_sha256": source_sha256}
            for source_sha256, locator in zip(source_sha256s, portable_locators, strict=True)
        ],
        "task": task,
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
