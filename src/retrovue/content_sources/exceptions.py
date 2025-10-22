"""
Content source-specific exceptions.
"""


class ContentSourceError(Exception):
    """Base exception for content source errors."""
    pass


class ContentSourceNotFoundError(ContentSourceError):
    """Raised when a content source is not found."""
    pass


class ContentSourceConfigurationError(ContentSourceError):
    """Raised when content source configuration is invalid."""
    pass


class ContentSourceConnectionError(ContentSourceError):
    """Raised when content source cannot connect."""
    pass


class ContentSourceValidationError(ContentSourceError):
    """Raised when content validation fails."""
    pass
