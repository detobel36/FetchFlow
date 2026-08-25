import httpx
import pytest

from jexflow.errors import HTTPError
from jexflow.http import HTTPRequest, HTTPXClient


def test_httpx_client_success():
    def mock_handler(request: httpx.Request):
        return httpx.Response(200, text="Hello World", request=request)

    transport = httpx.MockTransport(mock_handler)
    raw_client = httpx.Client(transport=transport)
    client = HTTPXClient(client=raw_client)

    req = HTTPRequest(url="https://example.com")
    res = client.send(req)

    assert res.status_code == 200
    assert res.text == "Hello World"
    assert res.is_success is True


def test_httpx_client_error():
    def mock_handler(request: httpx.Request):
        return httpx.Response(404, text="Not Found", request=request)

    transport = httpx.MockTransport(mock_handler)
    raw_client = httpx.Client(transport=transport)
    client = HTTPXClient(client=raw_client)

    req = HTTPRequest(url="https://example.com/404")
    with pytest.raises(HTTPError) as exc_info:
        client.send(req)

    assert exc_info.value.status_code == 404


def test_httpx_client_per_request_timeout():
    passed_timeout = []

    def mock_handler(request: httpx.Request):
        # httpx Request extensions contain timeout if specified
        passed_timeout.append(request.extensions.get("timeout"))
        return httpx.Response(200, text="OK", request=request)

    transport = httpx.MockTransport(mock_handler)
    raw_client = httpx.Client(transport=transport)
    client = HTTPXClient(client=raw_client)

    req = HTTPRequest(url="https://example.com", timeout=5.0)
    res = client.send(req)
    assert res.status_code == 200
    assert len(passed_timeout) == 1
    assert passed_timeout[0] is not None
    assert passed_timeout[0].get("connect") == 5.0
