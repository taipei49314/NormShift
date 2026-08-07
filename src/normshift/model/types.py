"""Pydantic data models for requirements, changes, and reports."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProfileName(StrEnum):
    RFC2119 = "rfc2119"
    WHATWG = "whatwg"


class Modality(StrEnum):
    MUST = "MUST"
    MUST_NOT = "MUST_NOT"
    SHOULD = "SHOULD"
    SHOULD_NOT = "SHOULD_NOT"
    MAY = "MAY"


class Polarity(StrEnum):
    AFFIRMATIVE = "AFFIRMATIVE"
    NEGATIVE = "NEGATIVE"


class ChangeClassification(StrEnum):
    UNCHANGED = "UNCHANGED"
    MOVED = "MOVED"
    EDITORIAL = "EDITORIAL"
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    STRENGTHENED = "STRENGTHENED"
    WEAKENED = "WEAKENED"
    POLARITY_FLIP = "POLARITY_FLIP"
    CONDITION_ADDED = "CONDITION_ADDED"
    CONDITION_REMOVED = "CONDITION_REMOVED"
    EXCEPTION_ADDED = "EXCEPTION_ADDED"
    EXCEPTION_REMOVED = "EXCEPTION_REMOVED"
    AMBIGUOUS = "AMBIGUOUS"


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    document_sha256: str
    document_version: str
    section_path: str
    source_locator: str
    original_text: str
    normalized_text: str
    modality: Modality
    polarity: Polarity
    actor: str | None = None
    action: str | None = None
    condition: str | None = None
    exception: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    extractor_version: str
    fingerprint: str
    structural_index: int = 0


class RequirementsDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    profile: ProfileName
    document_sha256: str
    document_version: str
    source_path: str
    extractor_version: str
    requirements: list[Requirement]


class AlignmentScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text_similarity: float
    modality_match: float
    section_similarity: float
    token_similarity: float
    actor_action_similarity: float
    structural_proximity: float
    combined: float
    components: dict[str, float] = Field(default_factory=dict)


class Change(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_id: str
    old_requirement_id: str | None
    new_requirement_id: str | None
    classification: ChangeClassification
    confidence: float = Field(ge=0.0, le=1.0)
    classification_reasons: list[str]
    old_source_locator: str | None = None
    new_source_locator: str | None = None
    old_text: str | None = None
    new_text: str | None = None
    modality_transition: str | None = None
    evidence_hashes: list[str] = Field(default_factory=list)
    alignment_score: AlignmentScore | None = None
    old_section_path: str | None = None
    new_section_path: str | None = None


class DocumentSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str
    version: str
    byte_length: int


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    tool_version: str
    profile: ProfileName
    old_document: DocumentSnapshot
    new_document: DocumentSnapshot
    old_requirements: list[Requirement]
    new_requirements: list[Requirement]
    changes: list[Change]
    summary: dict[str, Any]
    integrity: dict[str, str]
