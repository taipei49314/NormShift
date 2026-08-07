"""Official-source acquisition (network only at acquire time)."""

from normshift.acquire.fetcher import AcquisitionError, acquire_url, load_policy
from normshift.acquire.store import SnapshotStore

__all__ = ["AcquisitionError", "SnapshotStore", "acquire_url", "load_policy"]
