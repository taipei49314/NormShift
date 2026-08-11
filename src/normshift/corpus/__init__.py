"""M1 real-source acquisition and offline replay contracts."""

from normshift.corpus.acquisition import (
    AcquisitionError,
    CorpusReplayResult,
    acquire_corpus,
    verify_corpus_offline,
)
from normshift.corpus.evidence_inventory import (
    EvidenceInventoryError,
    EvidenceInventoryResult,
    SourceRecipeEvidenceResult,
    verify_evidence_root,
    verify_source_recipe_evidence,
)

__all__ = [
    "AcquisitionError",
    "CorpusReplayResult",
    "EvidenceInventoryError",
    "EvidenceInventoryResult",
    "SourceRecipeEvidenceResult",
    "acquire_corpus",
    "verify_corpus_offline",
    "verify_evidence_root",
    "verify_source_recipe_evidence",
]
