"""Error hierarchy for the scraper engine."""


class ScraperEngineError(Exception):
    """Base exception for all scraper engine errors."""



class ConfigurationError(ScraperEngineError):
    """Raised when configuration is invalid or missing."""



class ConfigValidationError(ConfigurationError):
    """Raised when JSON configuration fails schema validation."""

    def __init__(self, message: str, errors: list | None = None) -> None:
        """Init.

        Args:
        message: The error message.
        errors: A list of validation errors.
        """
        super().__init__(message)
        self.errors = errors or []


class HTTPError(ScraperEngineError):
    """Raised when an HTTP request fails."""

    def __init__(self, message: str, status_code: int | None = None, url: str | None = None) -> None:
        """Init.

        Args:
        message: The error message.
        status_code: The HTTP status code.
        url: The URL of the request.
        """
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class ParsingError(ScraperEngineError):
    """Raised when parsing HTML/XML response fails."""



class ExtractionError(ScraperEngineError):
    """Raised when extracting elements or fields fails."""



class TransformationError(ScraperEngineError):
    """Raised when applying a value transformation fails."""



class TemplateError(ScraperEngineError):
    """Raised when variable interpolation or template rendering fails."""



class WorkflowExecutionError(ScraperEngineError):
    """Raised when workflow step execution fails."""

