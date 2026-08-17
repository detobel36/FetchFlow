from pathlib import Path

import httpx

from scraper_engine import Scraper

CATALOG_HTML = """
<!DOCTYPE html>
<html>
<head><title>Product Catalog</title></head>
<body>
    <div class="product-card">
        <span class="product-id">PROD-001</span>
        <h3 class="title">  Smart TV 4K  </h3>
    </div>
    <div class="product-card">
        <span class="product-id">PROD-002</span>
        <h3 class="title">Wireless Headphones</h3>
    </div>
</body>
</html>
"""

DETAIL_001_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div id="product-detail">
        <span class="price-value"> Price: $499.99 USD </span>
        <span class="sku-code"> tv-4k-001 </span>
    </div>
</body>
</html>
"""

DETAIL_002_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div id="product-detail">
        <span class="price-value"> Price: $89.50 USD </span>
        <span class="sku-code"> hp-wl-002 </span>
    </div>
</body>
</html>
"""


def test_ecommerce_integration():
    example_path = Path(__file__).parent / ".." / "examples" / "ecommerce_scraper.json"

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if url == "https://store.example.com/products":
            return httpx.Response(200, text=CATALOG_HTML, request=request)
        if url == "https://store.example.com/product/PROD-001":
            return httpx.Response(200, text=DETAIL_001_HTML, request=request)
        if url == "https://store.example.com/product/PROD-002":
            return httpx.Response(200, text=DETAIL_002_HTML, request=request)
        return httpx.Response(404, text="Not Found", request=request)

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    from scraper_engine.http import HTTPXClient
    client_wrapper = HTTPXClient(client=http_client)

    scraper = Scraper(config=example_path, http_client=client_wrapper)
    results = scraper.run()

    assert len(results) == 2
    assert results[0] == {
        "id": "PROD-001",
        "title": "Smart TV 4K",
        "price": "499.99",
        "sku": "TV-4K-001",
    }
    assert results[1] == {
        "id": "PROD-002",
        "title": "Wireless Headphones",
        "price": "89.50",
        "sku": "HP-WL-002",
    }
