"""M1 real-source acquisition and offline replay contracts."""

from normshift.corpus.acquisition import (
    AcquisitionError,
    CorpusReplayResult,
    acquire_corpus,
    verify_corpus_offline,
)

__all__ = [
    "AcquisitionError",
    "CorpusReplayResult",
    "acquire_corpus",
    "verify_corpus_offline",
]
