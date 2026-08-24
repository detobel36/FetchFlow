from typing import Any

from jexflow.config import ConfigValidator
from jexflow.http import HTTPClient, HTTPRequest, HTTPResponse
from jexflow.scraper import Scraper


class MockCSRFHTTPClient(HTTPClient):
    """Mock HTTP client for testing CSRF token extraction and submission."""

    def __init__(self) -> None:
        """Init."""
        self.requests_sent: list[HTTPRequest] = []

    def send(self, request: HTTPRequest) -> HTTPResponse:
        """Send request and return mock response."""
        self.requests_sent.append(request)

        if "login" in request.url or "csrf-page" in request.url:
            html_content = """
            <html>
                <head>
                    <meta name="csrf-token" content="csrf_token_val_12345">
                </head>
                <body>
                    <form id="login">
                        <input type="hidden" name="token" value="csrf_token_val_12345">
                    </form>
                </body>
            </html>
            """
            return HTTPResponse(
                status_code=200,
                text=html_content,
                headers={"content-type": "text/html"},
                url=request.url,
            )

        if "api/action" in request.url:
            received_header = request.headers.get("X-CSRF-Token")
            received_param = request.params.get("csrf_token") if request.params else None

            response_json = f"""
            {{
                "status": "success",
                "received_header": "{received_header}",
                "received_param": "{received_param}"
            }}
            """
            return HTTPResponse(
                status_code=200,
                text=response_json,
                headers={"content-type": "application/json"},
                url=request.url,
            )

        return HTTPResponse(
            status_code=200,
            text="<html></html>",
            headers={"content-type": "text/html"},
            url=request.url,
        )


def test_csrf_schema_validation() -> None:
    """Test JSON schema validation for request with csrf_token."""
    config: dict[str, Any] = {
        "name": "csrf_test",
        "steps": [
            {
                "id": "post_with_csrf",
                "request": {
                    "method": "POST",
                    "url": "https://example.com/api/action",
                    "csrf_token": {
                        "url": "https://example.com/csrf-page",
                        "extract": {
                            "selector": "meta[name='csrf-token']",
                        },
                        "type": "attribute",
                        "attribute": "content",
                        "header_name": "X-CSRF-Token",
                        "param_name": "csrf_token",
                    },
                },
            },
        ],
    }
    # Should validate without raising ConfigValidationError
    ConfigValidator.validate(config)


def test_csrf_automated_fetching_and_injection() -> None:
    """Test that engine fetches CSRF token and injects into request headers and params."""
    config: dict[str, Any] = {
        "name": "csrf_automation_test",
        "steps": [
            {
                "id": "post_data",
                "request": {
                    "method": "POST",
                    "url": "https://example.com/api/action",
                    "csrf_token": {
                        "url": "https://example.com/login",
                        "extract": {
                            "selector": "meta[name='csrf-token']",
                        },
                        "type": "attribute",
                        "attribute": "content",
                        "header_name": "X-CSRF-Token",
                        "param_name": "csrf_token",
                    },
                },
                "fields": {
                    "status": {
                        "extract": {
                            "selector": "$.status",
                            "selector_type": "jsonpath",
                        },
                    },
                    "token_header": {
                        "extract": {
                            "selector": "$.received_header",
                            "selector_type": "jsonpath",
                        },
                    },
                    "token_param": {
                        "extract": {
                            "selector": "$.received_param",
                            "selector_type": "jsonpath",
                        },
                    },
                },
            },
        ],
    }

    client = MockCSRFHTTPClient()
    scraper = Scraper(config, http_client=client)
    results = scraper.run()

    # 2 requests sent: 1 for CSRF token retrieval, 1 for main POST request
    expected_token = "csrf_token_val_12345"  # noqa: S105
    assert len(client.requests_sent) == 2
    assert client.requests_sent[0].url == "https://example.com/login"
    assert client.requests_sent[1].url == "https://example.com/api/action"
    assert client.requests_sent[1].headers.get("X-CSRF-Token") == expected_token
    assert client.requests_sent[1].params.get("csrf_token") == expected_token

    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert results[0]["token_header"] == expected_token
    assert results[0]["token_param"] == expected_token
