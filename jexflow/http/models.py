from dataclasses import dataclass, field
from typing import Any

HTTP_SUCCESS = 200
HTTP_MULTIPLE_CHOICE = 300

@dataclass
class HTTPRequest:
    """Represents an outbound HTTP request."""

    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    body: Any | None = None
    timeout: float | None = None


@dataclass
class HTTPResponse:
    """Represents an inbound HTTP response."""

    status_code: int
    text: str
    headers: dict[str, str] = field(default_factory=dict)
    url: str = ""

    @property
    def is_success(self) -> bool:
        """Indicate whether the request was successful."""
        return HTTP_SUCCESS <= self.status_code < HTTP_MULTIPLE_CHOICE
