# Tutorial: Price Comparison Across Multiple E-Commerce Stores

This tutorial demonstrates how to perform price comparisons across multiple e-commerce websites (such as **Delhaize** and **Colruyt**) using Jexflow without writing website-specific scraping logic in Python.

By defining the site-specific extraction rules in configuration JSON files (such as `delhaize.json` and `colruyt.json`), you can write a generic Python runner script that executes all steps for each store and aggregates the results for easy comparison.

---

## 1. Overview & Goal

Imagine you want to compare the price of **Coca-Cola** between two Belgian supermarkets:
- **Delhaize**: `https://www.delhaize.be/shop/search?q=coca%20cola%3Arelevance&text=coca%20cola&sort=relevance`
- **Colruyt**: `https://www.colruyt.be/fr/produits?method=user%20typed&o=product%20overview&page=1&searchTerm=coca%20cola&suggestion=none&type=product`

Instead of writing custom BeautifulSoup or Selenium code for each website, you create a JSON configuration for each target site. Your Python application then loads these configurations and processes them generically using the `Scraper` engine.

---

## 2. Configuration Files

The JSON configuration files reside in the `examples/` directory.

### `examples/delhaize.json`
```json
{
  "name": "delhaize_coca_cola_search",
  "version": "1.0",
  "variables": {
    "search_term": "coca cola"
  },
  "steps": [
    {
      "id": "products",
      "request": {
        "method": "GET",
        "url": "https://www.delhaize.be/shop/search?q={{search_term}}%3Arelevance&text={{search_term}}&sort=relevance"
      },
      "extract": {
        "selector": ".product-item, [data-testimonial='product-card']",
        "selector_type": "css"
      },
      "fields": {
        "title": {
          "selector": ".product-title, .product-name, h3",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim"
          ]
        },
        "price": {
          "selector": ".product-price, .price-amount",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim",
            {
              "regex": "([0-9]+[.,][0-9]{2})"
            }
          ]
        }
      }
    }
  ]
}
```

### `examples/colruyt.json`
```json
{
  "name": "colruyt_coca_cola_search",
  "version": "1.0",
  "variables": {
    "search_term": "coca cola"
  },
  "steps": [
    {
      "id": "products",
      "request": {
        "method": "GET",
        "url": "https://www.colruyt.be/fr/produits?method=user%20typed&o=product%20overview&page=1&searchTerm={{search_term}}&suggestion=none&type=product"
      },
      "extract": {
        "selector": ".product-grid__item, .product-card",
        "selector_type": "css"
      },
      "fields": {
        "title": {
          "selector": ".product-card__title, .product-name, h3",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim"
          ]
        },
        "price": {
          "selector": ".product-card__price, .price-value",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim",
            {
              "regex": "([0-9]+[.,][0-9]{2})"
            }
          ]
        }
      }
    }
  ]
}
```

---

## 3. Generic Python Execution Code

Below is a complete Python script showing how to run multiple store configurations dynamically without store-specific logic.

```python
from pathlib import Path
from scraper_engine import Scraper

def compare_prices(config_paths: list[str | Path]) -> dict[str, list[dict]]:
    """Generic price comparison function across multiple stores.

    Args:
        config_paths: List of JSON configuration file paths for stores.

    Returns:
        A dictionary mapping store/configuration name to extracted product items.
    """
    comparison_results = {}

    for config_path in config_paths:
        # Load and execute the configuration generically
        scraper = Scraper(config_path)
        results = scraper.run()

        # Use config name or file stem as key
        store_name = scraper.config.get("name", str(config_path))
        comparison_results[store_name] = results

    return comparison_results

if __name__ == "__main__":
    configs = [
        Path("examples/delhaize.json"),
        Path("examples/colruyt.json"),
    ]

    all_prices = compare_prices(configs)

    for store, items in all_prices.items():
        print(f"\n=== {store} ===")
        for item in items:
            title = item.get("title", "Unknown Product")
            price = item.get("price", "N/A")
            print(f"- {title}: €{price}")
```

---

## 4. Key Takeaways

1. **Separation of Concerns**: HTML parsing rules and request URLs are defined entirely in JSON configurations (`delhaize.json` and `colruyt.json`), while Python code remains generic.
2. **Scalability**: To add a new store (e.g., Carrefour or Albert Heijn), simply create a new JSON configuration file and append it to `config_paths`. No code modifications are needed.
3. **Data Uniformity**: Using transformation pipelines (such as `trim` and `regex`) standardizes output fields (e.g. converting raw price text like `"€ 1.85 / st"` into clean numbers like `"1.85"`).
