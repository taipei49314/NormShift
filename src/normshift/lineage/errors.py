"""Fail-closed errors for the experimental lineage verification contract."""


class LineageContractError(ValueError):
    """Raised when an externally supplied lineage graph cannot be verified."""
