from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any

import httpx

from jexflow.errors import HTTPError
from jexflow.http.models import HTTPRequest, HTTPResponse


class HTTPClient(ABC):
    """Abstract HTTP client interface."""

    @abstractmethod
    def send(self, request: HTTPRequest) -> HTTPResponse:
        """Send an HTTP request and returns an HTTPResponse."""

    def close(self) -> None: # noqa: B027
        """Close any underlying connection pools/resources."""

    def __enter__(self) -> None:
        """Context manager support."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None,
                 exc_tb: TracebackType | None) -> None:
        """Context manager support."""
        self.close()


class HTTPXClient(HTTPClient):
    """HTTP client implementation using httpx library."""

    def __init__(
        self,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = True, # noqa: FBT001,FBT002
        client: httpx.Client | None = None,
    ) -> None:
        """Init.

        Args:
        timeout: The request timeout in seconds.
        headers: A dictionary of default headers.
        follow_redirects: Whether to follow HTTP redirects.
        client: A custom httpx client to use.
        """
        self.timeout = timeout
        self.default_headers = headers or {"User-Agent": "Mozilla/5.0 (ScraperEngine/1.0)"}
        self.follow_redirects = follow_redirects
        self._custom_client = client is not None
        self._client = client or httpx.Client(
            timeout=self.timeout,
            headers=self.default_headers,
            follow_redirects=self.follow_redirects,
        )

    def send(self, request: HTTPRequest) -> HTTPResponse:
        """Send an HTTP request and returns an HTTPResponse."""
        try:
            kwargs: dict[str, Any] = {
                "method": request.method,
                "url": request.url,
                "headers": request.headers,
                "content": request.body if isinstance(request.body, (str, bytes)) else None,
            }
            if request.params:
                kwargs["params"] = request.params

            res = self._client.request(**kwargs)
            response = HTTPResponse(
                status_code=res.status_code,
                text=res.text,
                headers=dict(res.headers),
                url=str(res.url),
            )
            if not response.is_success:
                msg = f"HTTP request to {request.url} failed with status {res.status_code}"
                raise HTTPError(
                    msg,
                    status_code=res.status_code,
                    url=str(res.url),
                )
        except httpx.RequestError as e:
            msg = f"HTTP request error for {request.url}: {e}"
            raise HTTPError(msg, url=request.url) from e
        else:
            return response

    def close(self) -> None:
        """Close any underlying connection pools/resources."""
        if not self._custom_client:
            self._client.close()
