import pytest
import httpx
from scraper_engine import Scraper


def test_workflow_execution():
    page1 = """
    <html>
        <body>
            <div class="product">
                <span class="id">101</span>
                <span class="name">Phone</span>
            </div>
            <div class="product">
                <span class="id">102</span>
                <span class="name">Laptop</span>
            </div>
        </body>
    </html>
    """

    page_detail_101 = """
    <html>
        <body>
            <div class="details">
                <span class="price">$599</span>
            </div>
        </body>
    </html>
    """

    page_detail_102 = """
    <html>
        <body>
            <div class="details">
                <span class="price">$1299</span>
            </div>
        </body>
    </html>
    """

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        print("MOCK RECEIVED URL:", repr(url))
        if url == "https://example.com/products":
            return httpx.Response(200, text=page1, request=request)
        elif "id=101" in url:
            return httpx.Response(200, text=page_detail_101, request=request)
        elif "id=102" in url:
            return httpx.Response(200, text=page_detail_102, request=request)
        return httpx.Response(404, text=f"Not Found: {url}", request=request)

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    config = {
        "name": "test_workflow",
        "variables": {
            "base_url": "https://example.com"
        },
        "steps": [
            {
                "id": "products",
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/products"
                },
                "extract": {
                    "selector": ".product",
                    "selector_type": "css"
                },
                "fields": {
                    "id": {
                        "selector": ".id",
                        "type": "text",
                        "transform": ["trim"]
                    },
                    "name": {
                        "selector": ".name",
                        "type": "text",
                        "transform": ["trim"]
                    }
                }
            },
            {
                "id": "details",
                "for_each": {
                    "from": "products",
                    "field": "id"
                },
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/details?id={{id}}"
                },
                "extract": {
                    "selector": ".details",
                    "selector_type": "css"
                },
                "fields": {
                    "price": {
                        "selector": ".price",
                        "type": "text",
                        "transform": ["trim", {"replace": {"from": "$", "to": ""}}]
                    }
                }
            }
        ]
    }

    from scraper_engine.http import HTTPXClient
    client_wrapper = HTTPXClient(client=http_client)
    scraper = Scraper(config=config, http_client=client_wrapper)
    results = scraper.run()

    assert len(results) == 2
    assert results[0] == {"id": "101", "name": "Phone", "price": "599"}
    assert results[1] == {"id": "102", "name": "Laptop", "price": "1299"}
