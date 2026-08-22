from pathlib import Path

import httpx

from jexflow import Scraper
from jexflow.http import HTTPXClient

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

DELHAIZE_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="product-item">
        <h3 class="product-title">Coca-Cola Regular 6x33cl</h3>
        <span class="product-price"> 4,99 € </span>
    </div>
    <div class="product-item">
        <h3 class="product-title">Coca-Cola Zero Sugar 1.5L</h3>
        <span class="product-price"> 2,15 € </span>
    </div>
</body>
</html>
"""

COLRUYT_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="product-card">
        <h3 class="product-card__title">Coca-Cola Original Taste 6x33cl</h3>
        <span class="product-card__price"> 4.85 € </span>
    </div>
    <div class="product-card">
        <h3 class="product-card__title">Coca-Cola Zero Sugar 1.5L</h3>
        <span class="product-card__price"> 2.09 € </span>
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


def test_price_comparison_integration():
    delhaize_path = Path(__file__).parent / ".." / "examples" / "delhaize.json"
    colruyt_path = Path(__file__).parent / ".." / "examples" / "colruyt.json"

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "delhaize.be" in url:
            return httpx.Response(200, text=DELHAIZE_HTML, request=request)
        if "colruyt.be" in url:
            return httpx.Response(200, text=COLRUYT_HTML, request=request)
        return httpx.Response(404, text="Not Found", request=request)

    transport = httpx.MockTransport(mock_handler)

    def run_generic_comparison(config_paths: list[Path]) -> dict[str, list[dict]]:
        comparison_results = {}
        for config_path in config_paths:
            client_wrapper = HTTPXClient(client=httpx.Client(transport=transport))
            scraper = Scraper(config=config_path, http_client=client_wrapper)
            results = scraper.run()
            store_name = scraper.config.get("name", str(config_path))
            comparison_results[store_name] = results
        return comparison_results

    all_prices = run_generic_comparison([delhaize_path, colruyt_path])

    assert "delhaize_coca_cola_search" in all_prices
    assert "colruyt_coca_cola_search" in all_prices

    delhaize_items = all_prices["delhaize_coca_cola_search"]
    assert len(delhaize_items) == 2
    assert delhaize_items[0] == {"title": "Coca-Cola Regular 6x33cl", "price": "4,99"}
    assert delhaize_items[1] == {"title": "Coca-Cola Zero Sugar 1.5L", "price": "2,15"}

    colruyt_items = all_prices["colruyt_coca_cola_search"]
    assert len(colruyt_items) == 2
    assert colruyt_items[0] == {"title": "Coca-Cola Original Taste 6x33cl", "price": "4.85"}
    assert colruyt_items[1] == {"title": "Coca-Cola Zero Sugar 1.5L", "price": "2.09"}
