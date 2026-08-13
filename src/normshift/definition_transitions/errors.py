"""Errors for the experimental definition-transition interchange contract."""


class DefinitionTransitionError(ValueError):
    """A caller-supplied transition sidecar fails its strict replay contract."""
