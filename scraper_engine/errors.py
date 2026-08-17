"""
Error hierarchy for the scraper engine.
"""


class ScraperEngineError(Exception):
    """Base exception for all scraper engine errors."""

    pass


class ConfigurationError(ScraperEngineError):
    """Raised when configuration is invalid or missing."""

    pass


class ConfigValidationError(ConfigurationError):
    """Raised when JSON configuration fails schema validation."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []


class HTTPError(ScraperEngineError):
    """Raised when an HTTP request fails."""

    def __init__(self, message: str, status_code: int = None, url: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class ParsingError(ScraperEngineError):
    """Raised when parsing HTML/XML response fails."""

    pass


class ExtractionError(ScraperEngineError):
    """Raised when extracting elements or fields fails."""

    pass


class TransformationError(ScraperEngineError):
    """Raised when applying a value transformation fails."""

    pass


class TemplateError(ScraperEngineError):
    """Raised when variable interpolation or template rendering fails."""

    pass


class WorkflowExecutionError(ScraperEngineError):
    """Raised when workflow step execution fails."""

    pass
