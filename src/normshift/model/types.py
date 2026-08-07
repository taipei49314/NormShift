"""Pydantic data models for requirements, changes, and reports."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProfileName(StrEnum):
    RFC2119 = "rfc2119"
    WHATWG = "whatwg"


class DocumentFamily(StrEnum):
    """Source document family handled by M1 adapters."""

    GENERIC_HTML = "generic_html"
    RFC = "rfc"
    W3C = "w3c"
    WHATWG = "whatwg"


class AdapterName(StrEnum):
    AUTO = "auto"
    HTML = "html"
    RFC = "rfc"
    W3C = "w3c"
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
    SPLIT = "SPLIT"
    MERGED = "MERGED"
    AMBIGUOUS = "AMBIGUOUS"


class LineageRelation(StrEnum):
    CONTINUES = "CONTINUES"
    SPLIT_INTO = "SPLIT_INTO"
    MERGED_FROM = "MERGED_FROM"
    SUPERSEDES = "SUPERSEDES"
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    AMBIGUOUS = "AMBIGUOUS"
    DEPENDS_ON = "DEPENDS_ON"
    REFERENCES_DEFINITION = "REFERENCES_DEFINITION"
    DEFINITION_CHANGED = "DEFINITION_CHANGED"


class RequirementInstanceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lineage_id: str
    requirement_id: str
    document_version: str
    document_sha256: str
    section_path: str
    source_locator: str
    modality: Modality
    original_text: str
    normalized_text: str
    actor: str | None = None
    action: str | None = None
    condition: str | None = None
    exception: str | None = None
    fingerprint: str


class LineageNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lineage_id: str
    instances: list[RequirementInstanceRef]
    first_version: str
    last_version: str


class LineageEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge_id: str
    relation: LineageRelation
    from_lineage_id: str | None
    to_lineage_id: str | None
    from_requirement_id: str | None
    to_requirement_id: str | None
    from_version: str
    to_version: str
    change_classification: str | None = None
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    alignment_combined: float | None = None


class AmbiguityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    version_pair: str
    kind: str
    old_requirement_ids: list[str] = Field(default_factory=list)
    new_requirement_ids: list[str] = Field(default_factory=list)
    detail: str
    scores: list[float] = Field(default_factory=list)


class DefinitionRecord(BaseModel):
    """A definition extracted from a document snapshot."""

    model_config = ConfigDict(extra="forbid")

    definition_id: str
    term: str
    body: str
    document_version: str
    document_sha256: str
    source_locator: str
    normalized_body: str


class DependencyLink(BaseModel):
    """Requirement → definition/xref dependency within a version."""

    model_config = ConfigDict(extra="forbid")

    link_id: str
    requirement_id: str
    definition_id: str
    document_version: str
    term: str
    evidence: str


class LineageGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    tool_version: str
    profile: ProfileName
    versions: list[str]
    document_sha256s: list[str]
    nodes: list[LineageNode]
    edges: list[LineageEdge]
    definitions: list[DefinitionRecord] = Field(default_factory=list)
    dependency_links: list[DependencyLink] = Field(default_factory=list)
    ambiguity_queue: list[AmbiguityItem]
    summary: dict[str, Any]
    integrity: dict[str, str]


class Provenance(BaseModel):
    """Immutable source provenance for a document snapshot (M1)."""

    model_config = ConfigDict(extra="forbid")

    document_family: DocumentFamily
    adapter_id: str
    adapter_version: str
    normalization_version: str
    content_type: str
    content_sha256: str
    byte_length: int
    local_path: str
    canonical_source: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    fetch_metadata: dict[str, str] = Field(default_factory=dict)


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
    provenance: Provenance | None = None
    document_family: DocumentFamily | None = None


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
    provenance: Provenance | None = None
    document_family: DocumentFamily | None = None


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
