"""
Importer-specific exceptions.
"""


class ImporterError(Exception):
    """Base exception for importer errors."""
    pass


class ImporterNotFoundError(ImporterError):
    """Raised when an importer is not found."""
    pass


class ImporterConfigurationError(ImporterError):
    """Raised when importer configuration is invalid."""
    pass


class ImporterConnectionError(ImporterError):
    """Raised when importer cannot connect to source."""
    pass


class ImporterValidationError(ImporterError):
    """Raised when content validation fails."""
    pass
