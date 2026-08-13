"""Typed, deliberately narrow DefinitionTransition v1 data models."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class DefinitionTransitionKind(StrEnum):
    DEFINITION_ADDED = "DEFINITION_ADDED"
    DEFINITION_CHANGED = "DEFINITION_CHANGED"
    DEFINITION_REMOVED = "DEFINITION_REMOVED"


class DefinitionAnchor(_StrictModel):
    """One extracted definition as bound by an exact LineageGraph replay."""

    definition_id: str = Field(min_length=1)
    document_version: str = Field(min_length=1)
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_term_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_body_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DefinitionTransition(_StrictModel):
    """One adjacent-version lexical definition transition; no impact inference."""

    transition_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    kind: DefinitionTransitionKind
    lexical_normalized_term: str = Field(min_length=1)
    old_definition: DefinitionAnchor | None
    new_definition: DefinitionAnchor | None

    @model_validator(mode="after")
    def _validate_kind_anchors(self) -> Self:
        if self.kind is DefinitionTransitionKind.DEFINITION_ADDED:
            valid = self.old_definition is None and self.new_definition is not None
        elif self.kind is DefinitionTransitionKind.DEFINITION_REMOVED:
            valid = self.old_definition is not None and self.new_definition is None
        else:
            valid = self.old_definition is not None and self.new_definition is not None
        if not valid:
            raise ValueError("definition transition kind has incompatible old/new anchors")
        return self


class DefinitionTransitionsIntegrity(_StrictModel):
    alg: Literal["sha256"]
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DefinitionTransitionsDocument(_StrictModel):
    """Canonical replay-only transition sidecar, independent of M2 adjudication."""

    schema_version: Literal["normshift-definition-transitions/v1"]
    authority_kind: Literal["LINEAGE_GRAPH_REPLAY_ONLY"]
    external_acceptance: Literal[False]
    graph_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    graph_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    graph_schema_version: Literal["1.0.0"]
    graph_tool_version: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    transitions: list[DefinitionTransition]
    integrity: DefinitionTransitionsIntegrity
