from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class HTTPRequest:
    """Represents an outbound HTTP request."""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None


@dataclass
class HTTPResponse:
    """Represents an inbound HTTP response."""
    status_code: int
    text: str
    headers: Dict[str, str] = field(default_factory=dict)
    url: str = ""

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300
