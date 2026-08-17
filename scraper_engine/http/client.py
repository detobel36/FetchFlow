from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import httpx

from scraper_engine.errors import HTTPError
from scraper_engine.http.models import HTTPRequest, HTTPResponse


class HTTPClient(ABC):
    """Abstract HTTP client interface."""

    @abstractmethod
    def send(self, request: HTTPRequest) -> HTTPResponse:
        """Sends an HTTP request and returns an HTTPResponse."""
        pass

    def close(self) -> None:
        """Closes any underlying connection pools/resources."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class HTTPXClient(HTTPClient):
    """HTTP client implementation using httpx library."""

    def __init__(
        self,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
        client: Optional[httpx.Client] = None
    ):
        self.timeout = timeout
        self.default_headers = headers or {"User-Agent": "Mozilla/5.0 (ScraperEngine/1.0)"}
        self.follow_redirects = follow_redirects
        self._custom_client = client is not None
        self._client = client or httpx.Client(
            timeout=self.timeout,
            headers=self.default_headers,
            follow_redirects=self.follow_redirects
        )

    def send(self, request: HTTPRequest) -> HTTPResponse:
        try:
            kwargs: Dict[str, Any] = {
                "method": request.method,
                "url": request.url,
                "headers": request.headers,
                "content": request.body if isinstance(request.body, (str, bytes)) else None
            }
            if request.params:
                kwargs["params"] = request.params

            res = self._client.request(**kwargs)
            response = HTTPResponse(
                status_code=res.status_code,
                text=res.text,
                headers=dict(res.headers),
                url=str(res.url)
            )
            if not response.is_success:
                raise HTTPError(
                    f"HTTP request to {request.url} failed with status {res.status_code}",
                    status_code=res.status_code,
                    url=str(res.url)
                )
            return response
        except httpx.RequestError as e:
            raise HTTPError(f"HTTP request error for {request.url}: {e}", url=request.url) from e

    def close(self) -> None:
        if not self._custom_client:
            self._client.close()
