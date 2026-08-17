import httpx

from scraper_engine import Scraper
from scraper_engine.config.validator import ConfigValidator


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
        if url == "https://example.com/products":
            return httpx.Response(200, text=page1, request=request)
        if "id=101" in url:
            return httpx.Response(200, text=page_detail_101, request=request)
        if "id=102" in url:
            return httpx.Response(200, text=page_detail_102, request=request)
        return httpx.Response(404, text=f"Not Found: {url}", request=request)

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    config = {
        "name": "test_workflow",
        "variables": {
            "base_url": "https://example.com",
        },
        "steps": [
            {
                "id": "products",
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/products",
                },
                "extract": {
                    "selector": ".product",
                    "selector_type": "css",
                },
                "fields": {
                    "id": {
                        "selector": ".id",
                        "type": "text",
                        "transform": ["trim"],
                    },
                    "name": {
                        "selector": ".name",
                        "type": "text",
                        "transform": ["trim"],
                    },
                },
            },
            {
                "id": "details",
                "for_each": {
                    "from": "products",
                    "field": "id",
                },
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/details?id={{id}}",
                },
                "extract": {
                    "selector": ".details",
                    "selector_type": "css",
                },
                "fields": {
                    "price": {
                        "selector": ".price",
                        "type": "text",
                        "transform": ["trim", {"replace": {"from": "$", "to": ""}}],
                    },
                },
            },
        ],
    }

    from scraper_engine.http import HTTPXClient

    client_wrapper = HTTPXClient(client=http_client)
    scraper = Scraper(config=config, http_client=client_wrapper)
    results = scraper.run()

    assert len(results) == 2
    assert results[0] == {"id": "101", "name": "Phone", "price": "599"}
    assert results[1] == {"id": "102", "name": "Laptop", "price": "1299"}


def test_nested_loops_same_page_and_for_each_rest():
    catalog_html = """
    <html>
        <body>
            <div class="products">
                <span class="model">iPhone 15</span>
                <div class="sub-product">
                    <span class="sub-id">ip15-128</span>
                    <span class="memory">128GB</span>
                </div>
                <div class="sub-product">
                    <span class="sub-id">ip15-256</span>
                    <span class="memory">256GB</span>
                </div>
            </div>
            <div class="products">
                <span class="model">Galaxy S24</span>
                <div class="sub-product">
                    <span class="sub-id">s24-256</span>
                    <span class="memory">256GB</span>
                </div>
            </div>
        </body>
    </html>
    """

    res_ip15_128 = '<div class="rest-data"><span class="price">$799</span></div>'
    res_ip15_256 = '<div class="rest-data"><span class="price">$899</span></div>'
    res_s24_256 = '<div class="rest-data"><span class="price">$849</span></div>'

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if url == "https://api.example.com/catalog":
            return httpx.Response(200, text=catalog_html, request=request)
        if "ip15-128" in url:
            return httpx.Response(200, text=res_ip15_128, request=request)
        if "ip15-256" in url:
            return httpx.Response(200, text=res_ip15_256, request=request)
        if "s24-256" in url:
            return httpx.Response(200, text=res_s24_256, request=request)
        return httpx.Response(404, text=f"Not Found: {url}", request=request)

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    config = {
        "name": "nested_loop_scraper",
        "variables": {
            "base_url": "https://api.example.com",
        },
        "steps": [
            {
                "id": "fetch_catalog",
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/catalog",
                },
                "extract": {
                    "selector": ".products",
                    "selector_type": "css",
                },
                "fields": {
                    "model": {
                        "selector": ".model",
                        "type": "text",
                    },
                    "sub_products": {
                        "extract": {
                            "selector": ".sub-product",
                            "selector_type": "css",
                        },
                        "fields": {
                            "sub_id": {
                                "selector": ".sub-id",
                                "type": "text",
                            },
                            "memory": {
                                "selector": ".memory",
                                "type": "text",
                            },
                        },
                    },
                },
            },
            {
                "id": "fetch_sub_product_rest",
                "for_each": {
                    "from": "fetch_catalog",
                    "field": "sub_products",
                },
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/subproduct/{{sub_id}}",
                },
                "extract": {
                    "selector": ".rest-data",
                    "selector_type": "css",
                },
                "fields": {
                    "price": {
                        "selector": ".price",
                        "type": "text",
                    },
                },
            },
        ],
    }

    ConfigValidator.validate(config)

    from scraper_engine.http import HTTPXClient

    client_wrapper = HTTPXClient(client=http_client)
    scraper = Scraper(config=config, http_client=client_wrapper)
    results = scraper.run()

    assert len(results) == 3
    assert results[0]["model"] == "iPhone 15"
    assert results[0]["sub_id"] == "ip15-128"
    assert results[0]["memory"] == "128GB"
    assert results[0]["price"] == "$799"

    assert results[1]["model"] == "iPhone 15"
    assert results[1]["sub_id"] == "ip15-256"
    assert results[1]["memory"] == "256GB"
    assert results[1]["price"] == "$899"

    assert results[2]["model"] == "Galaxy S24"
    assert results[2]["sub_id"] == "s24-256"
    assert results[2]["memory"] == "256GB"
    assert results[2]["price"] == "$849"
