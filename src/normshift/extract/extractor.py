"""Extract normative requirements from normalized HTML blocks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from normshift import EXTRACTOR_VERSION
from normshift.extract.historical import bound_current_clause, filter_historical_matches
from normshift.extract.profiles import find_keyword_matches
from normshift.extract.roles import extract_roles
from normshift.model.types import (
    AdapterName,
    ProfileName,
    Requirement,
    RequirementsDocument,
)
from normshift.normalize.html_normalize import NormalizedBlock, normalize_html, normalize_whitespace
from normshift.source import ImmutableSource, load_immutable_source


def stable_requirement_id(
    document_sha256: str,
    source_locator: str,
    modality: str,
    keyword_start: str,
    normalized_text: str,
) -> str:
    payload = "\x1f".join(
        [document_sha256, source_locator, modality, keyword_start, normalized_text]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def fingerprint_requirement(
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
        matches = find_keyword_matches(
            block.text,
            profile,
            protected_spans=block.protected_spans,
        )
        matches = filter_historical_matches(block.text, matches)
        if not matches:
            continue
        for km in matches:
            # Evidence keeps full original_text; roles/fingerprint use current clause only
            # so historical-comment edits do not invent semantic change events.
            clause, km_local = bound_current_clause(block.text, km)
            actor, action, condition, exception = extract_roles(clause, km_local)
            norm_text = normalize_whitespace(clause)
            fp = fingerprint_requirement(
                norm_text,
                km.modality.value,
                actor,
                action,
                condition,
                exception,
            )
            rid = stable_requirement_id(
                document_sha256,
                block.source_locator,
                km.modality.value,
                str(km.start),
                norm_text,
            )
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

    reqs.sort(key=lambda r: (r.structural_index, r.source_locator, r.requirement_id))
    return reqs


def extract_from_source(
    source: ImmutableSource,
    profile: ProfileName,
) -> RequirementsDocument:
    """Extract using an already-loaded immutable source (no re-read)."""
    blocks = normalize_html(source.working_html)
    reqs = requirements_from_blocks(
        blocks,
        document_sha256=source.sha256,
        document_version=source.document_version,
        profile=profile,
    )
    return RequirementsDocument(
        profile=profile,
        document_sha256=source.sha256,
        document_version=source.document_version,
        source_path=source.display_path,
        extractor_version=EXTRACTOR_VERSION,
        requirements=reqs,
        provenance=source.provenance,
        document_family=source.family,
    )


def extract_requirements(
    path: Path,
    profile: ProfileName,
    adapter: AdapterName = AdapterName.AUTO,
    *,
    source: ImmutableSource | None = None,
) -> RequirementsDocument:
    src = source if source is not None else load_immutable_source(path, adapter=adapter)
    return extract_from_source(src, profile)
