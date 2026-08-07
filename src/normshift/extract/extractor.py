"""Extract normative requirements from normalized HTML blocks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from normshift import EXTRACTOR_VERSION
from normshift.extract.profiles import find_keyword_matches
from normshift.extract.roles import extract_roles
from normshift.model.types import (
    ProfileName,
    Requirement,
    RequirementsDocument,
)
from normshift.normalize.html_normalize import NormalizedBlock, normalize_html, normalize_whitespace
from normshift.snapshot import snapshot_document


def _stable_id(*parts: str) -> str:
    payload = "\x1f".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _fingerprint(
    normalized_text: str,
    modality: str,
    actor: str | None,
    action: str | None,
    condition: str | None,
    exception: str | None,
) -> str:
    obj = {
        "normalized_text": normalized_text,
        "modality": modality,
        "actor": actor or "",
        "action": action or "",
        "condition": condition or "",
        "exception": exception or "",
    }
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def requirements_from_blocks(
    blocks: list[NormalizedBlock],
    *,
    document_sha256: str,
    document_version: str,
    profile: ProfileName,
) -> list[Requirement]:
    reqs: list[Requirement] = []
    for block in blocks:
        if block.is_informative:
            continue
        matches = find_keyword_matches(block.text, profile)
        if not matches:
            continue
        # One requirement per keyword hit in the block (stable order).
        for km in matches:
            actor, action, condition, exception = extract_roles(block.text, km)
            norm_text = normalize_whitespace(block.text)
            fp = _fingerprint(
                norm_text,
                km.modality.value,
                actor,
                action,
                condition,
                exception,
            )
            rid = _stable_id(
                document_sha256,
                block.source_locator,
                km.modality.value,
                str(km.start),
                norm_text,
            )
            # Confidence: high for clear keyword + non-empty action.
            confidence = 0.9 if action else 0.75
            if condition or exception:
                confidence = min(1.0, confidence + 0.05)

            reqs.append(
                Requirement(
                    requirement_id=rid,
                    document_sha256=document_sha256,
                    document_version=document_version,
                    section_path=block.section_path,
                    source_locator=block.source_locator,
                    original_text=block.text,
                    normalized_text=norm_text,
                    modality=km.modality,
                    polarity=km.polarity,
                    actor=actor,
                    action=action,
                    condition=condition,
                    exception=exception,
                    confidence=round(confidence, 4),
                    extractor_version=EXTRACTOR_VERSION,
                    fingerprint=fp,
                    structural_index=block.structural_index,
                )
            )

    # Deterministic order: structural index, then locator, then id.
    reqs.sort(key=lambda r: (r.structural_index, r.source_locator, r.requirement_id))
    return reqs


def extract_requirements(
    path: Path,
    profile: ProfileName,
) -> RequirementsDocument:
    snap, raw = snapshot_document(path)
    blocks = normalize_html(raw)
    reqs = requirements_from_blocks(
        blocks,
        document_sha256=snap.sha256,
        document_version=snap.version,
        profile=profile,
    )
    return RequirementsDocument(
        profile=profile,
        document_sha256=snap.sha256,
        document_version=snap.version,
        source_path=snap.path,
        extractor_version=EXTRACTOR_VERSION,
        requirements=reqs,
    )
