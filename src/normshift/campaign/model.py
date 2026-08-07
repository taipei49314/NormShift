"""Strict campaign plan and run-manifest models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SnapshotSpec(_Strict):
    snapshot_key: str
    family: Literal["ietf", "w3c", "whatwg", "html", "synthetic"]
    source_url: str
    adapter: str
    profile: str = "rfc2119"
    acquisition_mode: Literal["https", "import_file", "store_existing"]
    local_import_path: str | None = None
    version_label: str
    redistribution_status: Literal[
        "redistributable", "thin_only", "unknown_fail_closed"
    ]
    license_reference: str
    expected_content_type: str | None = None
    required: bool = True

    @field_validator("local_import_path")
    @classmethod
    def _posix_rel(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if "\\" in v or v.startswith("/") or ".." in v.split("/"):
            raise ValueError(f"illegal path: {v}")
        return v


class PairSpec(_Strict):
    pair_id: str
    old_snapshot_key: str
    new_snapshot_key: str
    relation: str = "version-pair"
    adapter: str
    profile: str = "rfc2119"
    importance_tags: list[str] = Field(default_factory=list)
    review_sampling_policy: str = "default"
    include_bytes_if_redistributable: bool = True


class LineageChainSpec(_Strict):
    chain_id: str
    ordered_snapshot_keys: list[str]
    family: str
    adapter: str
    profile: str = "rfc2119"


class CampaignOutputs(_Strict):
    run_manifest: str = "artifacts/foundry-24h/run-manifest.json"
    capsules_dir: str = "capsules"
    review_dir: str = "artifacts/foundry-24h/review"
    lineage_dir: str = "artifacts/foundry-24h/lineage"
    observatory_dir: str = "artifacts/foundry-24h/observatory"
    metrics: str = "artifacts/foundry-24h/metrics.json"
    dossiers_dir: str = "artifacts/foundry-24h/dossiers"


class AuthorityPolicy(_Strict):
    max_auto_label: str = "AUTO"
    allow_implementer_external_review: bool = False
    synthetic_gold_layer: str = "A"
    real_provisional_layer: str = "B"
    external_reviewed_layer: str = "C"


class CampaignPlan(_Strict):
    schema_version: str = "1.0.0"
    campaign_id: str
    status: str = "EXPERIMENTAL_NOT_ADJUDICATED"
    source_policy: str
    store: str = ".normshift/store"
    snapshots: list[SnapshotSpec]
    pairs: list[PairSpec]
    lineage_chains: list[LineageChainSpec] = Field(default_factory=list)
    outputs: CampaignOutputs = Field(default_factory=CampaignOutputs)
    authority_policy: AuthorityPolicy = Field(default_factory=AuthorityPolicy)
    source_date_epoch: int | None = 1700000000

    def validate_refs(self) -> None:
        keys = [s.snapshot_key for s in self.snapshots]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate snapshot_key")
        keyset = set(keys)
        pair_ids = [p.pair_id for p in self.pairs]
        if len(pair_ids) != len(set(pair_ids)):
            raise ValueError("duplicate pair_id")
        for p in self.pairs:
            if p.old_snapshot_key not in keyset or p.new_snapshot_key not in keyset:
                raise ValueError(f"pair {p.pair_id} unknown snapshot ref")
            if p.old_snapshot_key == p.new_snapshot_key:
                raise ValueError(f"pair {p.pair_id} old==new")
        for c in self.lineage_chains:
            if len(c.ordered_snapshot_keys) < 2:
                raise ValueError(f"lineage {c.chain_id} needs >=2 versions")
            for k in c.ordered_snapshot_keys:
                if k not in keyset:
                    raise ValueError(f"lineage {c.chain_id} unknown key {k}")
        for s in self.snapshots:
            if s.redistribution_status == "redistributable" and not s.license_reference:
                raise ValueError(f"{s.snapshot_key} redistributable needs license_reference")


class CampaignRunManifest(_Strict):
    schema_version: str = "1.0.0"
    campaign_id: str
    campaign_plan_sha256: str
    run_id: str
    mode: Literal["acquire", "offline"]
    source_policy_sha256: str
    code_version: str
    source_date_epoch: int | None = None
    status: str = "EXPERIMENTAL_NOT_ADJUDICATED"
    label_authority: str = "AUTO"
    snapshots: list[dict[str, Any]] = Field(default_factory=list)
    pair_capsule_ids: list[str] = Field(default_factory=list)
    lineage_export_ids: list[str] = Field(default_factory=list)
    review_packet_set_id: str | None = None
    observatory_manifest_id: str | None = None
    artifact_hashes: dict[str, str] = Field(default_factory=dict)
    unresolved_blockers: list[str] = Field(default_factory=list)
    counts: dict[str, Any] = Field(default_factory=dict)
