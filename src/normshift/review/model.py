"""Review packet and decision models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReviewPacket(_Strict):
    packet_id: str
    campaign_id: str
    pair_id: str
    capsule_id: str
    change_id: str
    proposed_classification: str
    label_authority: Literal["AUTO"] = "AUTO"
    confidence: float
    old_requirement_id: str | None = None
    new_requirement_id: str | None = None
    old_text: str | None = None
    new_text: str | None = None
    old_locator: str | None = None
    new_locator: str | None = None
    old_context: str | None = None
    new_context: str | None = None
    old_snapshot_sha256: str
    new_snapshot_sha256: str
    alignment_score_components: dict[str, Any] = Field(default_factory=dict)
    classification_reasons: list[str] = Field(default_factory=list)
    alternative_candidates: list[str] = Field(default_factory=list)
    ambiguity_state: str = "none"
    review_questions: list[str] = Field(default_factory=list)
    artifact_references: list[str] = Field(default_factory=list)


class ReviewDecision(_Strict):
    decision_id: str
    packet_id: str
    reviewer_id: str
    reviewer_role: str
    sequence: int
    source_snapshot_hashes: list[str]
    verdict: Literal[
        "ACCEPT_PROPOSAL",
        "RELABEL",
        "REJECT_CHANGE",
        "ABSTAIN",
        "NEEDS_CONTEXT",
        "DUPLICATE",
        "SPLIT",
        "MERGE",
    ]
    selected_classification: str | None = None
    relation_type: str | None = None
    reason: str
    confidence: float | None = None
    needs_more_context: bool = False
    external_evidence_refs: list[str] = Field(default_factory=list)
    label_authority: Literal["TEST_FIXTURE", "EXTERNAL_REVIEW", "EXTERNAL_ADJUDICATION"]
