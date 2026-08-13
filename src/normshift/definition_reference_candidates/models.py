from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RequirementAnchor(_Strict):
    requirement_id: str = Field(min_length=1)
    document_version: str = Field(min_length=1)
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DefinitionAnchor(_Strict):
    definition_id: str = Field(min_length=1)
    document_version: str = Field(min_length=1)
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_term_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DefinitionReferenceCandidate(_Strict):
    candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    link_id: str = Field(min_length=1)
    method: Literal["LEXICAL_TERM_OCCURRENCE_CANDIDATE"]
    requirement: RequirementAnchor
    definition: DefinitionAnchor


class Integrity(_Strict):
    alg: Literal["sha256"]
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DefinitionReferenceCandidatesDocument(_Strict):
    schema_version: Literal["normshift-definition-reference-candidates/v1"]
    authority_kind: Literal["LINEAGE_GRAPH_REPLAY_ONLY"]
    external_acceptance: Literal[False]
    graph_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    graph_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    graph_schema_version: Literal["1.0.0"]
    graph_tool_version: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    candidates: list[DefinitionReferenceCandidate]
    integrity: Integrity
